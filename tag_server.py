from flask import Flask, request, jsonify
app = Flask(__name__)

pending_tags = {}  # {face_id: embedding}
known_faces = {}   # {face_id: {'embedding': ..., 'tag': ...}}

@app.route('/get_pending_tags')
def get_pending_tags():
    return jsonify(list(pending_tags.keys()))

@app.route('/submit_tag', methods=['POST'])
def submit_tag():
    data = request.get_json()
    face_id = data['face_id']
    tag = data['tag']
    if face_id in pending_tags:
        known_faces[face_id] = {'embedding': pending_tags[face_id], 'tag': tag}
        del pending_tags[face_id]
        return 'success'
    return 'fail'

# 실시간 인식 코드에서 이걸 통해 pending_tags 업데이트
def register_new_face(face_id, embedding):
    pending_tags[face_id] = embedding

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 모든 네트워크에서 접속 허용
