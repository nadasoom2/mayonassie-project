import os
from flask import Blueprint, request, jsonify, render_template, session
from datetime import datetime
from gpt_utils import analyze_emotions_with_gpt, extract_emotion_scores
import sqlite3
import openai

# Blueprint 객체 생성
autodiary_bp = Blueprint('autodiary', __name__, template_folder='templates')

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

@autodiary_bp.route("/api/has_survey", methods=["GET"])
def has_survey():
    return jsonify({"hasSurvey": True})

@autodiary_bp.route("/generate_autodiary", methods=["POST"])
def generate_autodiary():
    if "userid" not in session:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    data = request.get_json()
    conversation = data.get("conversation", "")
    user_id = session["userid"]

    answers = session.get("chat_history", [])  # user/ai 메시지 리스트
    session.pop("chat_history", None)  # 다 쓰고 지워도 됨


    # 최근 설문 데이터 가져오기
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM survey_results WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    col_names = [desc[0] for desc in cursor.description]
    conn.close()

    # 감정 점수 계산
    scores = extract_emotion_scores(row, col_names)
    score_text = "\n".join([f"{k}: {v}" for k, v in scores.items()])

    prompt = f"""
    아래는 사용자가 AI에게 들려준 오늘 하루의 이야기들이야:

    {conversation.strip()}

    참고로 이 사용자는 오늘 감정 설문을 통해 다음과 같은 감정을 느꼈다고 해:
    {score_text}

    이 모든 내용을 바탕으로 오늘 하루를 돌아보며 쓰는 감성적인 일기를 작성해줘.

    [작성 규칙]
    - 첫 줄은 사용자와 대화했던 내용을 바탕으로 제목을 짧은 문장으로 만들어준다
    - 모든 문장은 \"‘~다’ 종결어미”로 끝나되, 중간에 쉼표나 연결어(“그러나”, “그래서”, “그리고”)를 사용해 부드럽게 이어준다.
    - 분량은 5~7문장 이상, 상황 → 감정 → 깨달음 및 다짐 흐름이 자연스럽게 이어지도록 한다.
    - 전체 글은 문단을 나누어 작성해줘. 상황, 감정, 깨달음이 자연스럽게 이어지도록 문단마다 줄바꿈을 넣어줘.
    - 글머리는 1~2줄, 중간은 자세하게, 마지막은 여운 있게 마무리해줘.
    - 감정, 상황, 여운이 자연스럽게 흐르도록
    - 사용자의 말투/표현도 잘 살려줘
    - 감정 점수나 설문 질문을 직접 인용하지 말고, 내가 실제로 느낀 듯한 말투로 녹여서 쓴다.
    - 너무 직접적인 해결책 대신, “오늘 내가 이러이러했구나” 하는 내면의 성찰을 중심으로 적는다.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500
        )
        diary = response.choices[0].message.content.strip()
        return jsonify({"diary": diary})
    except Exception as e:
        return jsonify({"diary": "일기 생성 실패", "error": str(e)}), 500

@autodiary_bp.route('/autodiary')
def autodiary_page():
    # chat_history가 있으면 대화 기반 일기 (chat에서 넘어온 경우)
    if "chat_history" in session:
        return render_template('autodiary.html', mode="chat")
    else:
        return render_template('autodiary.html', mode="survey")


@autodiary_bp.route("/autodiary_complete", methods=["POST"])
def autodiary_complete():
    if "userid" not in session:
        return "로그인 필요", 401

    data = request.get_json()
    content = data.get("content", "")
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

    return jsonify({"message": "자동일기 저장 완료!"})

@autodiary_bp.route('/next_question', methods=['POST'])
def next_question():
    data = request.get_json()
    answer = data.get("previousAnswer", "")
    conversation = data.get("conversation", "")

    full_text = conversation.strip() + "\n사용자: " + answer

    prompt = f"""
    아래는 지금까지 사용자가 AI에게 이야기한 전체 내용이야:

    {full_text}

     이 내용을 바탕으로, **따뜻하고 다정한 말투**로 다음 질문을 하나만 이어줘.

    조건:
    - 말투는 반말이지만 너무 건조하지 않고 다정하게
    - 질문은 하나만. 부드럽게 이어지는 말투로
    - 앞에서 이미 나온 질문과 겹치지 않게
    - 지금 이야기한 내용에서 연관된 감정, 상황, 기억 등을 더 알아보는 방향이면 좋아
    - 충분히 이야기를 나눴다고 판단되면, "모든 정보가 수집됐어!" 라고 대답해
    - 너무 빠르게 종료하지말고, 사용자의 감정이나 흐름이 자연스럽게 마무리 되는 시점까지 이끌어줘
    - 사용자가 여러 개의 에피소드를 말하고 싶어 할 수도 있으니, 다른 일이 있다면 자연스럽게 꺼내볼 수 있도록 유도해줘
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        reply = response.choices[0].message.content.strip()

        if "모든 정보가 수집되었습니다" in reply:
            return jsonify({"done": True})
        else:
            return jsonify({"done": False, "question": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
