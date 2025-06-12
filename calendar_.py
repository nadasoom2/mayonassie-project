from flask import Blueprint, request, session, jsonify
import sqlite3

calendar_bp = Blueprint("calendar", __name__, url_prefix="/calendar")

@calendar_bp.route("/calendar-data")
def calendar_data():
    if "userid" not in session:
        return jsonify({"error": "로그인 필요"}), 401

    date = request.args.get("date")
    user_id = session["userid"]

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()

    # ✅ 여기서 memo → share1 으로 바꿈
    cursor.execute("SELECT share1 FROM survey_results WHERE user_id=? AND DATE(timestamp)=?", (user_id, date))
    survey = cursor.fetchone()

    cursor.execute("SELECT content FROM diary WHERE user_id=? AND date=?", (user_id, date))
    diary = cursor.fetchone()

    conn.close()

    return jsonify({
        "memo": survey[0] if survey else None,
        "diary": diary[0] if diary else None
    })



@calendar_bp.route("/calendar-diary-range")
def calendar_diary_range():
    if "userid" not in session:
        return jsonify([])
    
    start = request.args.get("start")
    end = request.args.get("end")
    user_id = session["userid"]

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM diary WHERE user_id=? AND date BETWEEN ? AND ?", (user_id, start, end))
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{"date": row[0]} for row in rows])
