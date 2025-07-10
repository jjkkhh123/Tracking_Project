# Tracking_Project
만약 ValueError: You have tensorflow 2.19.0 and this requires tf-keras package. Please run pip install tf-keras or downgrade your tensorflow. 와 같은 오류가 뜬다면 아래의 코드를 통해 해결
```
pip install tf-keras
```

sql 연동을 위해 설치
```
pip install pymysql
pip install mysql-connector-python
```

```
pip uninstall deepface
pip install insightface
```

# 실시간 얼굴 태깅 시스템

실시간 웹캠 영상을 기반으로 사람을 인식하고 얼굴 임베딩을 통해 기존에 등록된 태그와 유사도를 비교하여 자동 분류하거나, 미등록된 경우 사용자로부터 태그를 입력받아 저장하는 시스템입니다.

## 📌 주요 기능

- YOLOv8n 모델을 활용한 사람 탐지
- DeepFace(Facenet) 기반 얼굴 임베딩 및 유사도 계산
- 실시간 영상 스트리밍 (Flask + OpenCV)
- 태깅이 필요한 얼굴에 대해 사용자 입력 폼 제공
- 태그 등록 및 분류 기능
- 로그인 및 회원가입 (세션 기반)
- 반응형 웹 UI (PC 및 모바일 지원)

---

## 🛠️ 사용 기술 및 모델

| 기능 | 사용 기술 / 라이브러리 / 모델 |
|------|------------------------------|
| 웹 서버 | Python Flask |
| 실시간 영상 스트리밍 | OpenCV |
| 사람 인식 | YOLOv8n (Ultralytics) |
| 얼굴 임베딩 | DeepFace (`Facenet` 모델 사용) |
| 벡터 유사도 측정 | Cosine Similarity (`scipy`) |
| DB | MariaDB / MySQL (pymysql, mysql-connector-python) |
| 웹 UI | HTML / CSS / JavaScript |
| 사용자 인증 | 세션 기반 로그인 |
| 한글 텍스트 렌더링 | PIL + Malgun.ttf 폰트 사용 |

---

## 📂 프로젝트 구조
```
📁 TrackingProject/
├── main.py # 실시간 처리 및 라우팅
├── login.py # 로그인/회원가입 기능
├── database.py # DB 연결 및 태그 저장/불러오기
├── yolov8n.pt # YOLOv8n 모델 가중치
├── static/
│ ├── styles.css # CSS 스타일링
│ ├── main.js # 태깅 대기 인터페이스 로직
│ ├── register_modal.js # 회원가입 모달 제어
│ └── fonts/
│ └── malgun.ttf # 한글 폰트
├── templates/
│ ├── index.html # 메인 태깅 화면
│ ├── login.html # 로그인 페이지 (+회원가입 모달)
│ └── register.html # 독립 회원가입 페이지
```

---

## ⚙️ 기술 흐름
[카메라 입력]
→ YOLOv8n으로 사람 탐지
→ 얼굴 영역 crop
→ DeepFace로 얼굴 임베딩
→ 기존 태그와 cosine similarity 비교
→ 일치: 태그 + 분류 표시
→ 불일치: 사용자 입력 요청


---

## 🧠 기술 설명

- **YOLOv8n**: 초경량 객체 탐지 모델로, `classes=[0]`을 지정해 사람만 탐지.
- **DeepFace(Facenet)**: 얼굴 이미지를 고차원 임베딩 벡터로 변환해 개별 비교 없이 벡터 간 유사도로 얼굴 식별 가능.
- **Cosine Similarity**: 기존 벡터들과의 코사인 유사도를 통해 같은 인물인지 판단 (`유사도 > 0.7`일 경우 일치 처리).
- **세션 관리**: Flask의 `session`으로 로그인 유저 상태 유지.
- **Pending Face 캐시**: 동일 얼굴 중복 요청 방지를 위해 일정 시간 동안 태깅 요청 캐시 처리.

---

## 🧪 실행 방법

```bash
# 필요한 라이브러리 설치
pip install -r requirements.txt

```

# 서버 실행
```
python main.py
```
📸 스크린샷



