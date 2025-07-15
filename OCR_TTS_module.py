# ocr_tts_module.py 내용 내장화 및 main.py 통합
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
import pytesseract
import pyttsx3

# OCR + TTS 관련 초기화
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 1.0)

def extract_text_from_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang='kor+eng')
    return text.strip()

def speak_text(text):
    if text:
        print(f"[🔊 읽기] {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()

app = Flask(__name__)
app.secret_key = "your_secret_key"
model = YOLO("yolov8n.pt")
app.register_blueprint(login_bp)

pending_faces = {}
active_tags = {}
SIMILARITY_THRESHOLD = 0.7
REQUIRED_SECONDS = 3
TAG_CACHE_SECONDS = 5

# 로그인 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# OCR 캡처 라우터
@app.route('/ocr_capture', methods=['POST'])
@login_required
def ocr_capture():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return jsonify({'success': False, 'message': '웹캡 캡처 실패'})
    text = extract_text_from_image(frame)
    return jsonify({'success': True, 'text': text})

# TTS 실행 라우터
@app.route('/speak_text', methods=['POST'])
@login_required
def speak_text_route():
    data = request.get_json()
    text = data.get('text', '')
    speak_text(text)
    return jsonify({'success': True})
