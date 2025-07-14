from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
from functools import wraps
import cv2
import numpy as np
import base64
import time
from deepface import DeepFace
from scipy.spatial.distance import cosine
from PIL import ImageFont, ImageDraw, Image
from ultralytics import YOLO
from login import login_bp
from database import get_db_connection, load_known_faces, save_face_to_db, known_faces

app = Flask(__name__)
app.secret_key = "your_secret_key"
model = YOLO("yolov8n.pt")
app.register_blueprint(login_bp)

pending_faces = {}
active_tags = {}

SIMILARITY_THRESHOLD = 0.7
REQUIRED_SECONDS = 3
TAG_CACHE_SECONDS = 5


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_face_embedding(face_img):
    try:
        embedding = DeepFace.represent(face_img, model_name='Facenet', enforce_detection=False)[0]['embedding']
        return embedding
    except:
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

            tag, category = find_matching_tag(embedding)
            if tag:
                active_tags[temp_id] = (tag, current_time)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                frame = draw_korean_text(frame, f"{category}:{tag}", x1, y1 - 30)
                continue

            is_pending_match = any(
                1 - cosine(embedding, pf['embedding']) > 0.85
                for pf in pending_faces.values()
            )
            if is_pending_match:
                print(f"[⏩] 유사 얼굴 대기 중: {temp_id}")
                continue

            if temp_id not in pending_faces:
                face_img = face_region.copy()
                success, face_jpg = cv2.imencode('.jpg', face_img)

                if not success:
                    print(f"[⚠] 이미지 인코딩 실패 → 등록 생략: {temp_id}")
                    continue

                face_b64 = base64.b64encode(face_jpg).decode('utf-8')
                pending_faces[temp_id] = {
                    'embedding': embedding,
                    'start_time': current_time,
                    'image': face_b64
                }
                print(f"[🆕] 등록 대기 추가: {temp_id}")

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_pending_tags')
@login_required
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
@login_required
def submit_tag():
    data = request.get_json()
    face_id = data['face_id']
    tag = data['tag']
    category = data.get('category', '기타')

    if face_id in pending_faces:
        embedding = np.array(pending_faces[face_id]['embedding'])
        save_face_to_db(tag, category, embedding, user_id=1)
        known_faces.append({
            'tag': tag,
            'category': category,
            'embedding': embedding
        })
        del pending_faces[face_id]
        return 'success'
    return 'fail'


if __name__ == '__main__':
    load_known_faces()
    app.run(host='0.0.0.0', port=5000)
