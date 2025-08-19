import cv2
import numpy as np
import base64
import time
import mediapipe as mp
import sys
import threading
import socket
from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
from functools import wraps
from deepface import DeepFace
from scipy.spatial.distance import cosine
from PIL import ImageFont, ImageDraw, Image
from ultralytics import YOLO
from login import login_bp
from database import get_db_connection, load_known_faces, save_face_to_db, known_faces

# ✅ mediapipe 객체는 메모리 효율 및 동시성 문제를 줄이기 위해 매번 생성하도록 구조 변경 (→ 아래 함수 내부로 이동)

app = Flask(__name__)
app.secret_key = "your_secret_key"
model = YOLO("best.pt")  # 기존 yolov8n.pt → best.pt
app.register_blueprint(login_bp)

pending_faces = {}
active_tags = {}
last_frame = None

SIMILARITY_THRESHOLD = 0.7
REQUIRED_SECONDS = 3
TAG_CACHE_SECONDS = 5


def align_face_with_mediapipe(image):
    h, w = image.shape[:2]
    try:
        with mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as face_mesh:
            results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    except Exception as e:
        print("[❌] mediapipe 처리 실패:", e)
        return image

    if not results.multi_face_landmarks:
        print("[!] 얼굴 미검출: mediapipe 결과 없음")
        return image

    try:
        landmarks = results.multi_face_landmarks[0].landmark

        # 눈 중심 계산
        left_eye = np.mean([(landmarks[33].x, landmarks[33].y), (landmarks[133].x, landmarks[133].y)], axis=0)
        right_eye = np.mean([(landmarks[362].x, landmarks[362].y), (landmarks[263].x, landmarks[263].y)], axis=0)

        # 이미지 좌표로 변환
        left_eye = np.array([left_eye[0] * w, left_eye[1] * h])
        right_eye = np.array([right_eye[0] * w, right_eye[1] * h])

        delta = right_eye - left_eye
        angle = np.degrees(np.arctan2(delta[1], delta[0]))
        center = tuple(int(x) for x in np.mean([left_eye, right_eye], axis=0))

        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        aligned = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR)

        return aligned
    except Exception as e:
        print("[❌] align_face_with_mediapipe 예외 발생:", e)
        return image


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_bp.login'))  # ✅ 정확한 blueprint 명시
        return f(*args, **kwargs)
    return decorated_function


def get_face_embedding(face_img):
    try:
        aligned = align_face_with_mediapipe(face_img)
        embedding = DeepFace.represent(aligned, model_name='Facenet', enforce_detection=False)[0]['embedding']
        return embedding
    except Exception as e:
        print("[!] get_face_embedding 실패:", e)
        return None


def find_matching_tag(embedding):
    for face in known_faces:
        similarity = 1 - cosine(embedding, face['embedding'])
        if similarity > SIMILARITY_THRESHOLD:
            return face['tag'], face.get('category', '기타')
    return None, None


def draw_korean_text(frame, text, x, y, font_size=30):
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font_path = "static/fonts/malgun.ttf"
    font = ImageFont.truetype(font_path, font_size)
    draw.text((x, y), text, font=font, fill=(255, 255, 0))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def generate_frames():
    global last_frame
    cap = cv2.VideoCapture(0)

    fps_limit = 10        # ✅ 최대 FPS 제한 (초당 10프레임)
    prev_time = 0

    yolo_interval = 0.3   # ✅ YOLO 실행 주기 (0.3초마다 한 번)
    last_yolo_time = 0
    last_boxes = []       # ✅ 마지막 YOLO 결과 저장

    while True:
        success, frame = cap.read()
        if not success:
            break

        current_time = time.time()

        # 1️⃣ FPS 제한 (10fps 이상으로는 처리 안 함)
        if current_time - prev_time < 1.0 / fps_limit:
            continue
        prev_time = current_time

        # 마지막 프레임 보관 (OCR에서 사용)
        last_frame = frame.copy()

        # 2️⃣ YOLO 실행 주기 제한
        if current_time - last_yolo_time > yolo_interval:
            results = model(frame, classes=[48])  # 사람 탐지
            last_boxes = results[0].boxes
            last_yolo_time = current_time

        # 3️⃣ YOLO 결과 적용 (직전 결과도 재사용)
        for box in last_boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w, h = x2 - x1, y2 - y1
            person_crop = frame[y1:y2, x1:x2]

            # 얼굴 영역 추출
            cx1, cy1 = int(w * 0.2), int(h * 0.1)
            cx2, cy2 = int(w * 0.8), int(h * 0.6)
            face_region = person_crop[cy1:cy2, cx1:cx2]

            if face_region.size == 0:
                continue

            embedding = get_face_embedding(face_region)
            if embedding is None:
                continue

            temp_id = str(hash(tuple(np.round(embedding[:4], 2))))[:6]

            # ✅ 기존 로직 유지 (active_tags / DB 검색 / pending_faces 등록)

            # 1. 캐시 확인
            if temp_id in active_tags:
                tag, last_seen = active_tags[temp_id]
                if current_time - last_seen < TAG_CACHE_SECONDS:
                    category = next((f['category'] for f in known_faces if f['tag'] == tag), '기타')
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    frame = draw_korean_text(frame, f"{category}:{tag}", x1, y1 - 30)
                    active_tags[temp_id] = (tag, current_time)
                    continue
                else:
                    del active_tags[temp_id]

            # 2. DB 검색
            tag, category = find_matching_tag(embedding)
            if tag:
                active_tags[temp_id] = (tag, current_time)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                frame = draw_korean_text(frame, f"{category}:{tag}", x1, y1 - 30)
                continue

            # 3. 중복 대기 확인
            already_pending = any(
                1 - cosine(embedding, pf['embedding']) > SIMILARITY_THRESHOLD
                for pf in pending_faces.values()
            )
            if already_pending:
                continue

            # 4. 신규 대기 등록
            if temp_id not in pending_faces:
                face_img = face_region.copy()
                success, face_jpg = cv2.imencode('.jpg', face_img)
                face_b64 = base64.b64encode(face_jpg).decode('utf-8') if success else ''
                pending_faces[temp_id] = {
                    'embedding': embedding,
                    'start_time': current_time,
                    'image': face_b64
                }

        # 최종 프레임 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/ocr_capture', methods=['POST'])
@login_required
def ocr_capture():
    from OCR_Paddle_module import extract_text_from_image
    global last_frame
    if last_frame is None:
        return jsonify({'success': False, 'message': '아직 프레임이 확보되지 않았습니다.'})
    try:
        text = extract_text_from_image(last_frame)
        return jsonify({'success': True, 'text': text})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/speak_text', methods=['POST'])
@login_required
def speak_text():
    from gtts import gTTS
    import pygame
    import io

    data = request.get_json()
    text = data.get('text', '')

    try:
        tts = gTTS(text=text, lang='ko')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login_bp.login'))  # ✅ blueprint명 반영


@app.route('/')
@login_required
def index():
    global pending_faces
    pending_faces.clear()   
    user_id = session['user_id']
    load_known_faces(user_id)
    return render_template('index.html')




@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_pending_tags')
@login_required
def get_pending_tags():
    return jsonify([
        {
            'face_id': face_id,
            'image': info.get('image', '')
        }
        for face_id, info in pending_faces.items()
    ])


@app.route('/submit_tag', methods=['POST'])
@login_required
def submit_tag():
    data = request.get_json()
    face_id = data['face_id']
    tag = data['tag']
    category = data.get('category', '기타')

    if face_id in pending_faces:
        embedding = np.array(pending_faces[face_id]['embedding'])
        user_id = session['user_id']   # ✅ 현재 로그인 사용자 ID
        save_face_to_db(tag, category, embedding, user_id)
        known_faces.append({
            'tag': tag,
            'category': category,
            'embedding': embedding
        })
        del pending_faces[face_id]
        return 'success'
    return 'fail'



if __name__ == '__main__':

    # ✅ Flask 실행 직후 접속 URL을 출력 (조금 지연해서)
    def show_access_url():
        print("\n🌐 접속 주소:")
        print(" - http://127.0.0.1:5000  (로컬)")
        
        ip = socket.gethostbyname(socket.gethostname())
        print(f" - http://{ip}:5000    (외부접속)")

    threading.Timer(2.0, show_access_url).start()  # 2초 후 실행

    app.run(host='0.0.0.0', port=5000)
