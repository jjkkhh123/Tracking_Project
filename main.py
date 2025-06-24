import cv2
import time
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace
from scipy.spatial.distance import cosine

# YOLO 모델 로드 (가장 가벼운 yolov8n)
model = YOLO("yolov8n.pt")

# 임베딩 저장소 및 시간 측정용 딕셔너리
known_faces = []  # [{'embedding': [...], 'tag': '이진수'}]
new_face_timers = {}  # {face_id: start_time}

# 설정
SIMILARITY_THRESHOLD = 0.7
REQUIRED_SECONDS = 3

def get_face_embedding(face_img):
    try:
        # 임베딩 추출 (FaceNet은 CPU에서도 비교적 빠름)
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

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO 사람 감지
    results = model(frame, classes=[0])
    boxes = results[0].boxes

    current_time = time.time()

    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        w, h = x2 - x1, y2 - y1
        person_crop = frame[y1:y2, x1:x2]

        # 얼굴로 추정되는 부분만 추출 (중앙 60% 크롭)
        cx1 = int(w * 0.2)
        cy1 = int(h * 0.1)
        cx2 = int(w * 0.8)
        cy2 = int(h * 0.6)
        face_region = person_crop[cy1:cy2, cx1:cx2]

        if face_region.size == 0:
            continue

        embedding = get_face_embedding(face_region)
        if embedding is None:
            continue

        tag = find_matching_tag(embedding)

        if tag:
            # 기존 태그된 사람이라면 박스에 태그 표시
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, tag, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, (255, 255, 0), 2)
        else:
            # 새로운 사람 → 임시 ID는 임베딩 첫 4자리
            temp_id = str(hash(tuple(np.round(embedding[:4], 2))))[:6]

            if temp_id not in new_face_timers:
                new_face_timers[temp_id] = current_time
            else:
                duration = current_time - new_face_timers[temp_id]
                if duration >= REQUIRED_SECONDS:
                    user_tag = input(f"이 사람에게 부여할 태그를 입력하세요: ")
                    known_faces.append({'embedding': embedding, 'tag': user_tag})
                    del new_face_timers[temp_id]
                    print(f"[✔] '{user_tag}' 태그 등록 완료!")

            # 아직 태그 안 된 새 사람 표시
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 100, 255), 2)
            cv2.putText(frame, f"태그 대기중...", (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 100, 255), 2)

    cv2.imshow("Face Tag Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
