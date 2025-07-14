from flask import Blueprint, render_template, request, redirect, url_for, session
import mysql.connector

login_bp = Blueprint('login_bp', __name__)

def get_db_connection():
    return mysql.connector.connect( #heidsql의 user이름과 비밀번호 그리고 가져올 데이터베이스 입력
        host='localhost',
        user='haihai',
        password='0122',
        database='tagpj'
    )

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form.get('userid')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        #SQL 질의어
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (userid, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")

    return render_template('login.html')

@login_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login_bp.login'))

@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            return render_template('login.html', register_error="비밀번호가 일치하지 않습니다.", open_modal=True)

        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return render_template('login.html', register_error="이미 존재하는 아이디입니다.", open_modal=True)
            
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login_bp.login'))
    return redirect(url_for('login_bp.login'))
