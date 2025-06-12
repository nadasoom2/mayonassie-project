from flask import Blueprint, request, render_template, session, jsonify, redirect
import sqlite3
from datetime import datetime

# ✅ url_prefix 추가

diary_bp = Blueprint("diary", __name__, url_prefix="/diary")


@diary_bp.route("/")
def diary_page():
    if "userid" not in session:
        return redirect("/")
    return render_template("diary.html")

@diary_bp.route("/save", methods=["POST"])
def save_diary():
    if "userid" not in session:
        return jsonify({"error": "로그인이 필요합니다"}), 401
    
    data = request.get_json()
    content = data.get("content")
    user_id = session["userid"]

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO diary (user_id, date, time, content)
        VALUES (?, ?, ?, ?)
    """, (user_id, date, time, content))
    conn.commit()
    conn.close()

    return jsonify({"message": f"{date} {time} 일기 저장 완료!"})


@diary_bp.route("/list")
def diary_list():
    user_id = session["userid"]
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, time, content FROM diary WHERE user_id=? ORDER BY date DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {"id": r[0], "date": r[1], "time": r[2], "content": r[3]}
        for r in rows
    ])



@diary_bp.route("/get", methods=["GET"])
def get_diary():
    user_id = session["userid"]
    date = request.args.get("date")
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM diary WHERE user_id=? AND date=?", (user_id, date))
    row = cursor.fetchone()
    conn.close()
    return jsonify({"content": row[0] if row else ""})

@diary_bp.route("/delete", methods=["POST"])
def delete_diary():
    data = request.get_json()
    diary_id = data.get("id")
    user_id = session["userid"]

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diary WHERE id=? AND user_id=?", (diary_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "일기 삭제 완료"})
