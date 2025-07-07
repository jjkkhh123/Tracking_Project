# database.py
import pymysql
import json
import numpy as np
import mysql.connector

# 얼굴 태그 데이터를 캐시해 둘 리스트
known_faces = []

# DB 연결 함수
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='haihai',
        password='0122',
        database='tagpj'
    )



# 얼굴 데이터 불러오기 (서버 시작 시 호출)
def load_known_faces():
    global known_faces
    known_faces = []
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT tag, category, embedding FROM known_faces")
        rows = cur.fetchall()
        for row in rows:
            known_faces.append({
                'tag': row['tag'],
                'category': row['category'],
                'embedding': np.array(json.loads(row['embedding']))
            })
    conn.close()
    print(f"[DB] {len(known_faces)}개의 태그를 불러왔습니다.")

# 얼굴 데이터 저장

def save_face_to_db(tag, category, embedding, user_id=1):
    embedding_json = json.dumps(embedding.tolist())
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO known_faces (user_id, tag, category, embedding) VALUES (%s, %s, %s, %s)",
            (user_id, tag, category, embedding_json)
        )
    conn.commit()
    conn.close()
    print(f"[DB] 태그 '{tag}' 저장 완료.")
