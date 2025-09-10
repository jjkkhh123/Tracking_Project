from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

login_bp = Blueprint('login_bp', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='haihai',
        password='0122',
        database='tagpj'
    )

# -------------------------------
# 로그인
# -------------------------------
@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form.get('userid')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM users WHERE username = %s", (userid,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            # ✅ 세션에 로그인 정보 저장
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # ✅ 전역에도 role 저장 (스트리밍 루프에서 접근할 수 있게)
            current_app.config['CURRENT_ROLE'] = user['role']

            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")

    return render_template('login.html')

# -------------------------------
# 로그아웃
# -------------------------------
@login_bp.route('/logout')
def logout():
    # ✅ 세션 초기화
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)

    # ✅ 전역 role도 기본값으로 리셋
    current_app.config['CURRENT_ROLE'] = 'user'

    return redirect(url_for('login_bp.login'))

# -------------------------------
# 회원가입
# -------------------------------
@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        user_type = request.form.get('user_type')  # 'user' 또는 '장애인'

        if password != confirm:
            return render_template('login.html',
                                   register_error="비밀번호가 일치하지 않습니다.",
                                   open_modal=True)

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return render_template('login.html',
                                       register_error="이미 존재하는 아이디입니다.",
                                       open_modal=True)

            hashed_pw = generate_password_hash(password)

            # ✅ role도 함께 저장
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_pw, user_type)
            )
        conn.commit()
        conn.close()

        return redirect(url_for('login_bp.login'))

    return redirect(url_for('login_bp.login'))
