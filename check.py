from flask import Blueprint, request, jsonify, session
import datetime
import sqlite3

check_bp = Blueprint("check", __name__)

# 연속 출석 계산 함수
def calculate_streak(dates: list) -> int:
    if not dates:
        return 0

    # 날짜 문자열을 date 객체로 변환 후 정렬
    dates = sorted([datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in dates])
    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        diff = (dates[i] - dates[i - 1]).days
        if diff == 1:
            streak += 1
        elif diff > 1:
            break
    return streak

@check_bp.route("/check_attendance", methods=["POST"])
def check_attendance():
    """
    출석 처리 및 5일 연속 출석 시 1코인 지급
    """
    if "userid" not in session:
        return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401

    user_id = session["userid"]
    today = str(datetime.date.today())

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()

    # 오늘 날짜 출석 시도
    cursor.execute("""
        INSERT OR IGNORE INTO attendance (user_id, date, checked)
        VALUES (?, ?, 1)
    """, (user_id, today))

    # 새로 삽입된 경우만 출석 처리 (중복 방지)
    if cursor.rowcount > 0:
        # 출석 날짜 리스트 조회
        cursor.execute("SELECT date FROM attendance WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        date_list = [r[0] for r in rows]

        # streak 계산
        streak = calculate_streak(date_list)

        # 연속 출석이 5일이면 보상 지급
        if streak > 0 and streak % 5 == 0:
            cursor.execute("""
                UPDATE users
                SET coins = coins + 1
                WHERE userid = ?
            """, (user_id,))
            conn.commit()

    # 현재 보유 코인 수 확인
    cursor.execute("SELECT coins FROM users WHERE userid = ?", (user_id,))
    coins_row = cursor.fetchone()
    new_coins = coins_row[0] if coins_row else 0

    conn.commit()
    conn.close()

    return jsonify({"success": True, "date": today, "coins": new_coins})


@check_bp.route("/check_attendance_dates", methods=["GET"])
def get_attendance_dates():
    """
    유저가 출석한 날짜 리스트와 현재 보유 coins 반환
    """
    if "userid" not in session:
        return jsonify([])

    user_id = session["userid"]
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()

    cursor.execute("SELECT date FROM attendance WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    cursor.execute("SELECT coins FROM users WHERE userid = ?", (user_id,))
    coins_row = cursor.fetchone()
    current_coins = coins_row[0] if coins_row else 0

    conn.close()

    return jsonify({
        "dates": [row[0] for row in rows],
        "coins": current_coins
    })
