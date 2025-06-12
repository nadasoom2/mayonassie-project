from dotenv import load_dotenv
load_dotenv()

import sqlite3
from flask import Flask
from flask_cors import CORS

from auth import auth_bp
from survey import survey_bp
from chat import chat_bp
from diary import diary_bp
from letter import letter_bp
from calendar_ import calendar_bp
from check import check_bp
from autodiary import autodiary_bp
from buy import buy_bp
from payment import payment_bp
from main import main_bp

app = Flask(__name__)
CORS(app)
app.secret_key = "your_secret_key"

# Blueprint 등록
app.register_blueprint(auth_bp)
app.register_blueprint(survey_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(diary_bp)
app.register_blueprint(letter_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(check_bp)
app.register_blueprint(autodiary_bp)
app.register_blueprint(buy_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(main_bp)


# ---------- DB 초기화 ----------
def init_user_db():
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            phone    TEXT    NOT NULL UNIQUE,
            userid   TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            coins    INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# attendance 테이블이 없다면 생성 (출석 체크용)
def init_attendance_db():
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  TEXT    NOT NULL,
            date     TEXT    NOT NULL,
            checked  INTEGER NOT NULL DEFAULT 1,
            UNIQUE(user_id, date)
        )
    """)
    conn.commit()
    conn.close()

# diary 테이블이 없다면 생성 (일기 저장용)
def init_diary_db():
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  TEXT    NOT NULL,
            date     TEXT    NOT NULL,
            time     TEXT    NOT NULL,
            content  TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# letters 테이블이 없다면 생성 (편지 저장용)
def init_letter_db():
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS letters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            emotion     TEXT    NOT NULL,
            title       TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# survey_results 등 나머지 테이블은 survey.py 등에서 init_db() 호출로 생성됨

# 각종 테이블 초기화 호출
init_user_db()
init_attendance_db()
init_diary_db()
init_letter_db()

if __name__ == "__main__":
    app.run(debug=True)
