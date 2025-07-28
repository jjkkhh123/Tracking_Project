# 👤 실시간 얼굴 태깅 시스템 (YOLOv8 + DeepFace)

Python Flask 기반의 웹 애플리케이션으로, 실시간 영상 속 인물을 YOLOv8로 탐지하고, DeepFace를 통해 얼굴 임베딩 후 기존 사용자와 비교하여 자동 분류하거나, 미등록된 인물에 대해 태그를 입력받아 저장하는 시스템입니다.

---

## 📌 목차

- [1. 주요 기능](#1-주요-기능)
- [2. 사용 기술](#2-사용-기술)
- [3. 프로젝트 구조](#3-프로젝트-구조)
- [4. 시스템 처리 흐름](#4-시스템-처리-흐름)
- [5. 실행 방법](#5-실행-방법)
- [6. 데이터베이스 설정](#6-데이터베이스-설정)
- [7. 테스트 계정](#7-테스트-계정)
- [8. 시스템 구조도](#8-시스템-구조도)
- [9. 라이선스](#10-라이선스)

---

## 1. 주요 기능

- ✅ YOLOv8 커스텀 모델을 이용한 사람 검출 (`best.pt`)
- ✅ Mediapipe로 얼굴 정렬 → 정확도 향상
- ✅ DeepFace (Facenet) 기반 얼굴 임베딩
- ✅ Cosine Similarity로 기존 인물과 유사도 비교
- ✅ 미인식 인물에 대해 태그 및 카테고리 수동 입력
- ✅ 실시간 영상 스트리밍 (OpenCV + Flask)
- ✅ PaddleOCR로 텍스트 추출 + gTTS 음성 출력
- ✅ MariaDB/MySQL로 태그 및 사용자 정보 저장
- ✅ PC 및 모바일 브라우저 대응 UI
- ✅ 세션 기반 로그인 / 회원가입 시스템

---

## 2. 사용 기술

| 기능               | 기술 스택 |
|--------------------|------------|
| 웹 프레임워크       | Flask |
| 영상 처리           | OpenCV |
| 객체 인식           | YOLOv8 (Ultralytics, `best.pt`) |
| 얼굴 임베딩         | DeepFace (Facenet) + Mediapipe 정렬 |
| OCR + 음성 출력     | PaddleOCR + gTTS |
| DB 및 인증          | MySQL / MariaDB, 세션 기반 |
| 클라이언트 UI       | HTML, CSS, JavaScript |
| 폰트 렌더링         | PIL + Malgun.ttf |

---

## 3. 프로젝트 구조

<pre><code>
📁 TrackingProject/
├── main.py                  # Flask 앱 실행 + 영상 처리
├── login.py                 # 로그인, 회원가입 처리
├── database.py              # DB 연결 및 임베딩 처리
├── OCR_Paddle_module.py     # OCR 추출 함수
├── yolov8n.pt               # 기본 YOLOv8n 모델 (백업용)
├── best.pt                  # 커스텀 학습된 사람 탐지 모델
├── requirements.txt         # Python 의존성
├── templates/
│   ├── index.html           # 메인 태깅 화면
│   └── register.html        # 회원가입 화면
├── static/
│   ├── styles.css           # 스타일
│   ├── main.js              # 태깅 폼 처리 및 OCR 실행
│   ├── register_modal.js    # 회원가입 모달 제어
│   └── fonts/
│       └── malgun.ttf       # 한글 폰트
</code></pre>

---

## 4. 시스템 처리 흐름
![images](https://github.com/jjkkhh123/Tracking_Project/blob/main/images/%EC%8B%9C%EC%8A%A4%ED%85%9C%20%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98%20%EB%8B%A4%EC%9D%B4%EC%96%B4%EA%B7%B8%EB%9E%A8.jpg)
1. 카메라 영상 → YOLOv8로 사람 탐지  
2. 얼굴 영역 crop → Mediapipe로 정렬  
3. DeepFace(Facenet)으로 얼굴 임베딩 추출  
4. 기존 사용자와 코사인 유사도 비교  
   - 유사도 > 0.7 → 태그 자동 표시  
   - 일치 없음 → 태그 입력 폼 생성  
5. 입력된 태그 및 카테고리는 DB에 저장  
6. 글자 추출 버튼 → OCR → TTS로 음성 출력 가능

---

## 5. 실행 방법

### 1. Python 환경 설정

```bash
python -m venv venv
source venv/bin/activate  # 윈도우: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. YOLOv8 모델 준비
- `best.pt` 파일을 프로젝트 루트에 위치시킵니다.
- (이미 포함됨)

### 3. 실행

```bash
python main.py
```

실행 후 콘솔에 아래와 같은 접속 주소가 표시됩니다:

```
🌐 접속 주소:
 - http://127.0.0.1:5000  (로컬)
 - http://192.168.X.X:5000  (모바일 접근 가능)
```

---

## 6. 데이터베이스 설정

```sql
CREATE DATABASE tagpj;
USE tagpj;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    password VARCHAR(255)
);

CREATE TABLE known_faces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag VARCHAR(255),
    category VARCHAR(255),
    embedding TEXT,
    user_id INT
);
```

---

## 7. 테스트 계정

| 아이디 | 비밀번호 |
|--------|----------|
| test1  | 1234     |

> `users` 테이블에 직접 추가하거나 `/register` 통해 생성하세요.

---

## 8. 시스템 구조도

> 아래 링크에서 확인하세요:  
📎 Boardmix 스타일 시스템 흐름도 (이미지 제공 예정)


---

## 9. 라이선스

MIT License
