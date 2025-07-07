from flask import Blueprint, render_template, request, redirect, url_for, session
import mysql.connector

login_bp = Blueprint('login_bp', __name__)

def get_db_connection():
    return mysql.connector.connect(
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
