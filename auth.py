from flask import Blueprint, request, session, render_template, redirect, flash
import sqlite3

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def home():
    return render_template("login.html")

@auth_bp.route("/home")
def home_dashboard():
    if "userid" not in session:
        return redirect("/")

    user_id = session.get("userid")
    coins = 0

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE userid = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        coins = result[0]

    return render_template("main.html", coins=coins, userid=user_id)


@auth_bp.route("/signup")
def go_register():
    return render_template("signup.html")

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        userid = request.form["userid"]
        password = request.form["password"]
        phone = request.form["phone"]
    except Exception as e:
        return f"❌ 폼에서 값 추출 실패: {e}"

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (userid, password, phone) VALUES (?, ?, ?)",
                       (userid, password, phone))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        flash("❌ 이미 존재하는 아이디 또는 전화번호입니다.")
        return redirect("/signup")
    except Exception as e:
        conn.close()
        return f"❌ DB 저장 중 오류 발생: {e}"

    conn.close()
    flash("✅ 회원가입이 완료되었습니다! 로그인해주세요.")
    return redirect("/")


@auth_bp.route("/login", methods=["POST"])
def login():
    phone = request.form["phone"]
    password = request.form["password"]

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        session["userid"] = user[2]  # 예: "taei123"
        return redirect("/home")
    else:
        flash("❌ 전화번호 또는 비밀번호가 올바르지 않습니다.")
        return redirect("/")
