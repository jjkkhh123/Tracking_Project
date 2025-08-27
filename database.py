import mysql.connector
import numpy as np

# 전역 얼굴 정보 리스트
known_faces = []  # [{'tag': str, 'category': str, 'embedding': np.ndarray}]


def get_db_connection():
    """MySQL DB 연결"""
    try:
        return mysql.connector.connect(
            host='localhost',
            user='haihai',
            password='0122',
            database='tagpj'
        )
    except mysql.connector.Error as e:
        print(f"[❌] DB 연결 오류: {e}")
        raise


def save_face_to_db(tag, category, embedding, user_id):
    """얼굴 태그와 임베딩 데이터를 DB에 저장"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:  # 💡 기존 cursor 닫기 생략 방지 위해 with문 사용
            # 💡 임베딩 저장 시 float64 타입으로 고정 (재사용 시 일관성 보장)
            embedding = np.asarray(embedding, dtype=np.float64)
            embedding_str = ','.join(map(str, embedding))

            cur.execute(
                "INSERT INTO known_faces (tag, category, embedding, user_id) VALUES (%s, %s, %s, %s)",
                (tag, category, embedding_str, user_id)
            )
        conn.commit()
    except mysql.connector.Error as e:
        print(f"[❌] DB 저장 오류: {e}")
    finally:
        conn.close()  # 💡 connection만 따로 close (cursor는 with문으로 처리됨)

def load_known_faces(user_id):
    """
    DB에서 특정 user_id의 임베딩 데이터를 불러와 known_faces 리스트에 로딩
    """
    global known_faces
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM known_faces WHERE user_id = %s", (user_id,))
            rows = cur.fetchall()
    except mysql.connector.Error as e:
        print(f"[❌] DB 조회 오류: {e}")
        rows = []
    finally:
        conn.close()

    known_faces.clear()

    for row in rows:
        try:
            embedding_array = np.fromstring(row['embedding'], sep=',', dtype=np.float64)

            known_faces.append({
                'tag': row['tag'],
                'category': row['category'],
                'embedding': embedding_array
            })
        except Exception as e:
            print(f"[!] 임베딩 변환 실패 (tag: {row.get('tag')}): {e}")

    print(f"[DB] ✅ {len(known_faces)}개의 태그를 불러왔습니다. (user_id={user_id})")