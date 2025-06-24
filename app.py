
import cv2
import time
import numpy as np
from flask import Flask, render_template, Response, request, jsonify
from ultralytics import YOLO
from deepface import DeepFace
from scipy.spatial.distance import cosine

app = Flask(__name__)

model = YOLO("yolov8n.pt")

known_faces = []  # [{'embedding': [...], 'tag': '이진수'}]
pending_faces = {}  # {face_id: {'embedding': [...], 'start_time': float}}
active_tags = {}  # {temp_id: tag}

SIMILARITY_THRESHOLD = 0.7
REQUIRED_SECONDS = 3
TAG_CACHE_SECONDS = 5  # 얼마나 태그를 유지할지 (초)

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
            return face['tag']
    return None

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

            # hash로 임시 ID 만들기 (active_tags 캐시에 사용)
            temp_id = str(hash(tuple(np.round(embedding[:4], 2))))[:6]

            # 캐시된 태그 있으면 바로 사용 (유지 시간 초과 시 삭제)
            if temp_id in active_tags:
                tag, last_seen = active_tags[temp_id]
                if current_time - last_seen < TAG_CACHE_SECONDS:
                    # 최신 태그 표시
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, tag, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (255, 255, 0), 2)
                    # 마지막 본 시간 업데이트
                    active_tags[temp_id] = (tag, current_time)
                    continue
                else:
                    del active_tags[temp_id]

            # known_faces에서 새로 태그 찾기
            tag = find_matching_tag(embedding)
            if tag:
                # 캐시에 등록하고 표시
                active_tags[temp_id] = (tag, current_time)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, tag, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (255, 255, 0), 2)
                continue

            # pending_faces 중복 방지
            duplicate_pending = False
            for pf in pending_faces.values():
                similarity = 1 - cosine(embedding, pf['embedding'])
                if similarity > SIMILARITY_THRESHOLD:
                    duplicate_pending = True
                    break
            if duplicate_pending:
                continue

            # 새로운 사람 등록
            if temp_id not in pending_faces:
                pending_faces[temp_id] = {'embedding': embedding, 'start_time': current_time}
            else:
                duration = current_time - pending_faces[temp_id]['start_time']
                if duration >= REQUIRED_SECONDS:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 100, 255), 2)
                    cv2.putText(frame, f"태그 대기중...", (x1, y2 + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_pending_tags')
def get_pending_tags():
    return jsonify(list(pending_faces.keys()))

@app.route('/submit_tag', methods=['POST'])
def submit_tag():
    data = request.get_json()
    face_id = data['face_id']
    tag = data['tag']
    if face_id in pending_faces:
        known_faces.append({
            'embedding': pending_faces[face_id]['embedding'],
            'tag': tag
        })
        del pending_faces[face_id]
        return 'success'
    return 'fail'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
