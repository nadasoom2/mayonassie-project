import sqlite3
from flask import Blueprint, render_template, session

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def main():
    """
    메인 페이지: 로그인된 사용자의 coins를 조회하여 화면에 전달.
    """
    user_id = session.get("userid")  # 로그인 시 session["userid"]에 아이디(문자열)를 저장
    coins = 0

    if user_id:
        conn = sqlite3.connect("emotion.db")
        cursor = conn.cursor()
        # coins 컬럼을 userid 기준으로 조회
        cursor.execute("SELECT coins FROM users WHERE userid = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            coins = result[0]

    # 템플릿으로 coins와 userid를 넘겨줌
    return render_template("main.html", coins=coins, userid=user_id)
