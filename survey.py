from flask import Blueprint, render_template, request, jsonify, redirect, session
import sqlite3, datetime, json, openai

survey_bp = Blueprint("survey", __name__)

def init_db():
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS survey_results (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT NOT NULL,
        user_id     TEXT NOT NULL,

        -- 감정별 선택 여부 (yes/no 단계)
        anger       INTEGER NOT NULL,
        depress     INTEGER NOT NULL,
        anxiety     INTEGER NOT NULL,
        lonely      INTEGER NOT NULL,
        fatigue     INTEGER NOT NULL,
        sadness     INTEGER NOT NULL,
        joy         INTEGER NOT NULL,
        happy       INTEGER NOT NULL,
        calm        INTEGER NOT NULL,
        satisfy     INTEGER NOT NULL,

        -- 부정 감정 3점 척도
        anger1      INTEGER, anger2 INTEGER,
        depress1    INTEGER, depress2 INTEGER,
        anxiety1    INTEGER, anxiety2 INTEGER,
        lonely1     INTEGER, lonely2 INTEGER,
        fatigue1    INTEGER, fatigue2 INTEGER,
        sad1        INTEGER, sad2 INTEGER,

        -- 부정 주관식
        share1      TEXT,
        share2      TEXT,

        -- 긍정 감정 3점 척도
        joy1        INTEGER, joy2 INTEGER,
        happy1      INTEGER, happy2 INTEGER,
        calm1       INTEGER, calm2 INTEGER,
        satisfy1    INTEGER,
        satisfy2    TEXT,  -- 주관식

        -- 긍정 주관식
        posShare1   TEXT,
        posShare2   TEXT,
        posShare3   TEXT
        );
    """)
    conn.commit()
    conn.close()

init_db()

@survey_bp.route("/survey")
def survey():
    if "userid" not in session:
        return redirect("/")
    return render_template("survey.html")


@survey_bp.route("/submit", methods=["POST"])
def submit():
    if "userid" not in session:
        return jsonify({"error": "로그인하지 않았습니다."}), 401

    data = request.get_json()
    user_id = session["userid"]

    # 한글 키 → DB 컬럼명 매핑
    mapping = {
        "anger": "분노",
        "depress": "우울",
        "anxiety": "불안",
        "lonely": "외로움",
        "fatigue": "무기력",
        "sadness": "슬픔",
        "joy": "기쁨",
        "happy": "행복",
        "calm": "평온",
        "satisfy": "만족감"
    }

    # 저장할 컬럼·값 리스트 준비
    columns = ["timestamp", "user_id"]
    values  = [datetime.datetime.now().isoformat(), user_id]

    # 1단계 감정 체크
    for col, json_key in mapping.items():
        val = data.get(json_key, "0")
        try:
            values.append(int(val))
        except:
            values.append(0)
        columns.append(col)

    # 2단계 부정 감정 심화
    neg_keys = [
        *["anger"+str(i) for i in range(1,3)],
        *["depress"+str(i) for i in range(1,3)],
        *["anxiety"+str(i) for i in range(1,3)],
        *["lonely"+str(i) for i in range(1,3)],
        *["fatigue"+str(i) for i in range(1,3)],
        *["sad"+str(i) for i in range(1,3)]
    ]
    for key in neg_keys:
        columns.append(key)
        values.append(data.get(key, None))

    # 부정 감정 주관식
    for i in range(1,3):
        key = f"share{i}"
        columns.append(key)
        values.append(data.get(key, ""))

    # 긍정 감정 척도 + 만족감 주관식
    pos_keys = [
        "joy1", "joy2",
        "happy1", "happy2",
        "calm1", "calm2",
        "satisfy1"
    ]
    for key in pos_keys:
        columns.append(key)
        values.append(data.get(key, None))

    # 만족감 주관식
    columns.append("satisfy2")
    values.append(data.get("satisfy2", ""))

    # 긍정 주관식
    for i in range(1, 4):
        key = f"posShare{i}"
        columns.append(key)
        values.append(data.get(key, ""))


    # DB 저장
    try:
        conn = sqlite3.connect("emotion.db")
        cursor = conn.cursor()
        sql = f"""
            INSERT INTO survey_results ({','.join(columns)})
            VALUES ({','.join('?' for _ in values)})
        """
        cursor.execute(sql, values)
        conn.commit()
        return jsonify({"message": "DB 저장 완료!"})
    except Exception as e:
        print("DB 저장 오류:", e)
        return jsonify({"error": "DB 저장 실패"}), 500
    finally:
        conn.close()


@survey_bp.route("/analyze_latest", methods=["GET"])
def analyze_latest():
    conn = sqlite3.connect("emotion.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM survey_results ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"message": "분석할 데이터가 없습니다."}), 404

    # row는 dict처럼 접근 가능
    anger_scores = [row[f"anger{i}"] for i in range(1, 4)]
    avg_anger = round(sum(anger_scores) / len(anger_scores), 2)
    return jsonify({"분노 평균": avg_anger})




@survey_bp.route("/debug_db")
def debug_db():
    conn = sqlite3.connect("emotion.db")
    conn.row_factory = sqlite3.Row  # 각 row를 딕셔너리처럼 다룰 수 있게
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM survey_results ORDER BY id DESC LIMIT 3")
    rows = cursor.fetchall()
    conn.close()

    result = [dict(row) for row in rows]  # JSON으로 직렬화 가능하도록 변환
    return jsonify(result)

