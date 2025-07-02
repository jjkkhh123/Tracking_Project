import cv2
import time
import json
import os
import numpy as np
import base64

from flask import Flask, render_template, Response, request, jsonify
from ultralytics import YOLO
from deepface import DeepFace
from scipy.spatial.distance import cosine

app = Flask(__name__)

model = YOLO("yolov8n.pt")

known_faces = []       # [{'embedding': np.array([...]), 'tag': '이름', 'category': '분류'}]
pending_faces = {}     # {face_id: {'embedding': [...], 'start_time': float, 'image': base64}}
active_tags = {}       # {temp_id: (tag, last_seen_time)}

SIMILARITY_THRESHOLD = 0.7
REQUIRED_SECONDS = 3
TAG_CACHE_SECONDS = 5
SAVE_FILE = "known_faces.json"

# ------------------------ 태그 저장 / 불러오기 ------------------------

def load_known_faces():
    global known_faces
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                known_faces = [
                    {
                        'embedding': np.array(face['embedding']),
                        'tag': face['tag'],
                        'category': face.get('category', '기타')
                    }
                    for face in data
                ]
            print(f"[✔] {len(known_faces)}개의 태그 데이터를 로드했습니다.")
        except Exception as e:
            print(f"[!] 태그 불러오기 실패: {e}")

def save_known_faces():
    try:
        data = [
            {
                'embedding': face['embedding'].tolist(),
                'tag': face['tag'],
                'category': face.get('category', '기타')
            }
            for face in known_faces
        ]
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("[💾] 태그 데이터 저장 완료.")
    except Exception as e:
        print(f"[!] 태그 저장 실패: {e}")

# ------------------------ 임베딩 및 매칭 ------------------------

def get_face_embedding(face_img):
    try:
        embedding = DeepFace.represent(face_img, model_name='Facenet', enforce_detection=False)[0]['embedding']
        return embedding
    except Exception as e:
        print(f"[!] 임베딩 실패: {e}")
        return None

def find_matching_tag(embedding):
    for face in known_faces:
        similarity = 1 - cosine(embedding, face['embedding'])
        if similarity > SIMILARITY_THRESHOLD:
            return face['tag'], face.get('category', '기타')
    return None, None

# ------------------------ 영상 스트리밍 ------------------------

def generate_frames():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        current_time = time.time()
        results = model(frame, classes=[0])
        boxes = results[0].boxes

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w, h = x2 - x1, y2 - y1
            person_crop = frame[y1:y2, x1:x2]

            cx1, cy1 = int(w * 0.2), int(h * 0.1)
            cx2, cy2 = int(w * 0.8), int(h * 0.6)
            face_region = person_crop[cy1:cy2, cx1:cx2]

            if face_region.size == 0:
                continue

            embedding = get_face_embedding(face_region)
            if embedding is None:
                continue

            temp_id = str(hash(tuple(np.round(embedding[:4], 2))))[:6]

            # 캐시된 태그가 있으면 사용
            if temp_id in active_tags:
                tag, last_seen = active_tags[temp_id]
                if current_time - last_seen < TAG_CACHE_SECONDS:
                    category = next((f['category'] for f in known_faces if f['tag'] == tag), '기타')
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{category}:{tag}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (255, 255, 0), 2)
                    active_tags[temp_id] = (tag, current_time)
                    continue
                else:
                    del active_tags[temp_id]

            # 새로운 매칭 시도
            tag, category = find_matching_tag(embedding)
            if tag:
                active_tags[temp_id] = (tag, current_time)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{category}:{tag}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (255, 255, 0), 2)
                continue

            # 중복 pending 방지
            if any(1 - cosine(embedding, pf['embedding']) > SIMILARITY_THRESHOLD for pf in pending_faces.values()):
                continue

            # 대기 등록 및 미리보기 생성
            if temp_id not in pending_faces:
                face_img = face_region.copy()
                success, face_jpg = cv2.imencode('.jpg', face_img)
                if success:
                    face_b64 = base64.b64encode(face_jpg).decode('utf-8')
                else:
                    face_b64 = ''
                pending_faces[temp_id] = {
                    'embedding': embedding,
                    'start_time': current_time,
                    'image': face_b64
                }

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ------------------------ Flask 라우터 ------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_pending_tags')
def get_pending_tags():
    data = [
        {
            'face_id': face_id,
            'image': info.get('image', '')
        }
        for face_id, info in pending_faces.items()
    ]
    return jsonify(data)

@app.route('/submit_tag', methods=['POST'])
def submit_tag():
    data = request.get_json()
    face_id = data['face_id']
    tag = data['tag']
    category = data.get('category', '기타')

    if face_id in pending_faces:
        known_faces.append({
            'embedding': pending_faces[face_id]['embedding'],
            'tag': tag,
            'category': category
        })
        del pending_faces[face_id]
        save_known_faces()
        return 'success'
    return 'fail'

# ------------------------ 서버 실행 ------------------------

if __name__ == '__main__':
    load_known_faces()
    app.run(host='0.0.0.0', port=5000)
