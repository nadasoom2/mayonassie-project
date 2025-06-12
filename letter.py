from flask import Blueprint, request, render_template, session, jsonify, redirect
import sqlite3
from datetime import datetime

letter_bp = Blueprint("letter", __name__)

def get_db_connection():
    conn = sqlite3.connect("emotion.db")
    conn.row_factory = sqlite3.Row
    return conn

# 편지쓰기 페이지 렌더링
@letter_bp.route("/letterwriting")
def letter_form():
    if "userid" not in session:
        return redirect("/")
    return render_template("letterwriting.html")

# 편지 전송 API
@letter_bp.route("/letter/send", methods=["POST"])
def send_letter():
    if "userid" not in session:
        return jsonify({"error": "로그인이 필요합니다"}), 401

    data = request.get_json()
    emotion = data.get("emotion")
    title = data.get("title")
    content = data.get("content")
    userid = session["userid"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_blocked, last_sent_date FROM users WHERE userid = ?", (userid,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return jsonify({"success": False, "message": "유저 정보를 찾을 수 없습니다."})

    if user["is_blocked"]:
        conn.close()
        return jsonify({"success": False, "message": "신고 누적으로 인해 편지 작성이 제한되었습니다."})

    cur.execute(
        "INSERT INTO letters (emotion, title, content, userid, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (emotion, title, content, userid)
    )
    conn.commit()

    today_str = datetime.now().strftime("%Y-%m-%d")
    last_sent_date = user["last_sent_date"]
    first_time_today = (last_sent_date != today_str)

    if first_time_today:
        cur.execute("UPDATE users SET last_sent_date = ? WHERE userid = ?", (today_str, userid))
        conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "편지 저장 완료",
        "first_time_today": first_time_today
    })

# 랜덤 편지 1개 가져오기
@letter_bp.route("/letter/random", methods=["POST"])
def random_letter():
    if "userid" not in session:
        return jsonify({"error": "로그인이 필요합니다"}), 401

    userid = session["userid"]
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT coins, last_sent_date FROM users WHERE userid = ?", (userid,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "유저 정보를 찾을 수 없습니다"}), 404

    coins = user["coins"]
    last_sent_date = user["last_sent_date"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_first_today = (last_sent_date != today_str)

    paid = request.args.get("paid") == "true"

    if not is_first_today and paid and coins <= 0:
        conn.close()
        return jsonify({"error": "코인이 부족합니다"}), 403

    cur.execute(
        "SELECT id, userid, emotion, title, content FROM letters WHERE userid != ? ORDER BY RANDOM() LIMIT 1",
        (userid,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "받을 수 있는 편지가 없습니다"}), 404
    
    cur.execute(
        "INSERT OR IGNORE INTO received_letters (userid, letter_id) VALUES (?, ?)",
        (userid, row["id"])
    )


    if paid:
        cur.execute("UPDATE users SET coins = coins - 1 WHERE userid = ?", (userid,))

    if is_first_today:
        cur.execute("UPDATE users SET last_sent_date = ? WHERE userid = ?", (today_str, userid))

    conn.commit()
    conn.close()

    return jsonify({
        "id": row["id"],
        "userid": row["userid"],
        "emotion": row["emotion"],
        "title": row["title"],
        "content": row["content"]
    })

# 편지 ID로 편지 내용 조회
@letter_bp.route("/letter")
def get_letter():
    letter_id = request.args.get("id")
    if not letter_id:
        return jsonify({"error": "편지 ID가 없습니다"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT userid, emotion, title, content FROM letters WHERE id = ?", (letter_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return jsonify({
            "sender_userid": row["userid"],
            "emotion": row["emotion"],
            "title": row["title"],
            "content": row["content"]
        })
    else:
        return jsonify({"error": "편지를 찾을 수 없습니다"}), 404

# 편지 신고
@letter_bp.route("/letter/report", methods=["POST"])
def report_letter():
    if "userid" not in session:
        return jsonify({"error": "로그인이 필요합니다"}), 401

    data = request.get_json()
    letter_id = data.get("id")

    if not letter_id:
        return jsonify({"error": "편지 ID가 필요합니다"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT userid, reports FROM letters WHERE id = ?", (letter_id,))
    letter = cur.fetchone()

    if not letter:
        conn.close()
        return jsonify({"error": "존재하지 않는 편지입니다"}), 404

    author_id = letter["userid"]
    current_reports = letter["reports"] if letter["reports"] else 0

    cur.execute("UPDATE letters SET reports = ? WHERE id = ?", (current_reports + 1, letter_id))

    if current_reports + 1 >= 3:
        cur.execute("UPDATE users SET is_blocked = 1 WHERE userid = ?", (author_id,))

    conn.commit()
    conn.close()

    return jsonify({"message": "편지가 신고되었습니다."})


@letter_bp.route("/letter/received")
def received_letters():
    if "userid" not in session:
        return jsonify({"error": "로그인이 필요합니다"}), 401
    userid = session["userid"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT l.id, l.title, l.userid as sender_userid "
        "FROM letters l "
        "JOIN received_letters r ON l.id = r.letter_id "
        "WHERE r.userid = ? "
        "ORDER BY r.received_at DESC",
        (userid,)
    )
    letters = cur.fetchall()
    conn.close()
    letter_list = [{"id": l["id"], "title": l["title"], "sender_userid": l["sender_userid"]} for l in letters]
    return jsonify(letter_list)
