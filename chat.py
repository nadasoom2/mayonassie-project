# gpt 대화, 감정 분석 결과 출력

from flask import Blueprint, request, session, jsonify, render_template, redirect
from gpt_utils import analyze_emotions_with_gpt
import sqlite3, random, openai

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat")
def chat_page():
    if "userid" not in session:
        return redirect("/")

    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM survey_results WHERE user_id=? ORDER BY id DESC LIMIT 1", (session["userid"],))
    row = cursor.fetchone()
    column_names = [description[0] for description in cursor.description]
    conn.close()

    if row:
        session["emotion_summary"] = analyze_emotions_with_gpt(row, column_names)

    return render_template("chat.html")


@chat_bp.route("/chat_api", methods=["POST", "GET"])
def chat_api():
    if request.method == "GET":
        # 최근 설문 데이터에서 GPT 요약 불러오기
        conn = sqlite3.connect("emotion.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM survey_results ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        column_names = [desc[0] for desc in cursor.description]

        conn.close()

        if not row:
            return jsonify({ "reply": "❌ 최근 설문 데이터가 없습니다." })

        # GPT 분석 함수로 감정 요약 생성
        emotion_summary = analyze_emotions_with_gpt(row, column_names)

        if not emotion_summary:
            return jsonify({ "reply": "❌ 감정 분석 결과 생성 실패" })

        # 따뜻한 질문 후보 리스트
        question_candidates = [
            "오늘 하루는 좀 어땠어요?",
            "요즘 어떤 순간이 제일 힘들었어요?",
            "혼자 있는 시간은 괜찮았나요?",
            "누군가에게 털어놓고 싶은 이야기 있었나요?",
            "요즘 가장 많이 떠오르는 감정은 뭐였나요?",
            "자고 나면 좀 괜찮아지던가요?",
            "마음이 지쳐 있을 때 어떤 생각이 들었나요?",
            "기억에 남는 순간이 있었나요?"
        ]

        import random
        chosen_questions = random.sample(question_candidates, 2)
        joined_questions = " ".join(chosen_questions)

        # 최종 첫 메시지
        first_message = f"{emotion_summary} {joined_questions}"
        return jsonify({ "reply": first_message })



    # POST 방식일 경우 (유저가 채팅창에서 전송했을 때)
    data = request.get_json()
    user_input = data.get("message", "")

    emotion_context = session.get("emotion_summary", "사용자의 감정 상태는 확인되지 않았습니다.")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
        당신은 감정 케어 AI입니다. 사용자의 최근 감정 상태는 다음과 같습니다:

        "{emotion_context}"

        너는 이 감정 상태를 항상 기억하면서, 사용자의 질문에 반응할 때 반드시 이 상태를 고려해.
        그리고 그에 맞춰 대화를 부드럽고 따뜻하게 이끌어야 해.
        너는 사용자의 감정 상태를 고려해서, 친구처럼 반말로 다정하게 이야기해줘. 예: '많이 힘들었구나. 오늘 어땠어?' 처럼 말야.


        - 항상 짧고 가독성 좋은 문장으로 말해. 2~3줄 이내로.
        - 한 번에 질문은 하나만 던져. (두 개 이상 질문하지 마.)
        - 사용자의 감정에 공감하듯, 따뜻하고 부드러운 친구처럼 말해.
        - 사용자의 마음을 진심으로 궁금해하는 태도를 살짝 보여줘.
        - 위로 받는 기분이 들도록, 무겁지 않게 다정하게 표현해.
        - 가벼운 말에도 감정을 떠올리게 유도하되, 평가하거나 분석하진 마.
        - 사용자가 말한 감정을 그대로 되돌려주듯, 짧게 재진술해 줘.
        예: “지금 많이 지치셨군요. 그럼, 최근에 그런 감정을 자주 느끼셨나요?”
        - 적절한 순간에 한 문장 정도의 위로 문구를 섞어줘.
        예: “그 마음, 충분히 이해돼요. 혹시 지금 조금 가벼워진 기분이 드시나요?”
        - 평범한 일상 언어로, 사용자에게 ‘괜찮다’는 메시지를 전해 줘.
        예: “괜찮아요, 천천히 이야기해주셔도 돼요.”
        - 답변 끝에 너무 길지 않게, 한 번 더 살짝 물어봐.
        예: “그동안 이런 기분을 공유해본 적이 있으신가요?”
        - 사용자가 스스로 생각을 정리할 수 있도록, 열린형 질문을 한 가지만 던져줘.
        예: “지금 이 순간, 어떤 작은 변화가 있을 것 같으세요?”
        - 절대 평가하거나 해결책만 제시하지 말고, 공감과 이해에 집중해.
        예: “듣고 있자니 많이 힘드셨을 것 같아요.”

        너의 말은 **짧고, 부드럽고, 눈치 있게**.  
        무조건 공감하려 하지 말고, **살짝 마음을 건드리는 질문**을 해줘.
        """
                },
                
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=300
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({ "reply": reply })
    except Exception as e:
        return jsonify({ "reply": f"❌ 오류 발생: {str(e)}" }), 500
    
# --------result
@chat_bp.route("/result")
def result():
    if "userid" not in session:
        return redirect("/")
    return render_template("result.html")

# /gpt_summary 라우트
@chat_bp.route("/gpt_summary")
def gpt_summary():
    user_id = session.get("userid")
    if not user_id:
        return jsonify({"error": "로그인 필요"}), 401
    
    conn = sqlite3.connect("emotion.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM survey_results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    column_names = [desc[0] for desc in cursor.description]
    conn.close()

    if not row:
        return jsonify({ "summary": "❌ 분석할 데이터가 없습니다." }), 404

    # 감정별 점수 계산
    emotion_map = {
        "분노": ["anger1", "anger2", "anger3"],
        "우울": ["depress1", "depress2", "depress3"],
        "불안": ["anxiety1", "anxiety2", "anxiety3"],
        "외로움": ["lonely1", "lonely2", "lonely3"],
        "무기력": ["fatigue1", "fatigue2", "fatigue3"],
        "슬픔": ["sad1", "sad2", "sad3"],
        "기쁨": ["joy1", "joy2", "joy3"],
        "행복": ["happy1", "happy2", "happy3"],
        "평온": ["calm1", "calm2"],  # calm3은 주관식
        "만족감": ["satisfy1", "satisfy2"]  # satisfy3은 주관식
    }


    row_dict = dict(zip(column_names, row))
    scores = {}
    for emotion, keys in emotion_map.items():
        vals = [row_dict.get(k) for k in keys if k in row_dict and isinstance(row_dict[k], int)]
        avg = round(sum(vals)/len(vals), 2) if vals else 0
        scores[emotion] = avg

    # GPT 분석 문장
    from gpt_utils import analyze_emotions_with_gpt
    gpt_result = analyze_emotions_with_gpt(row, column_names)

    return jsonify({
        "summary": gpt_result or "❌ GPT 분석 실패",
        "scores": scores
    })

@chat_bp.route("/save_chat_temp", methods=["POST"])
def save_chat_temp():
    session["chat_history"] = request.get_json().get("history", [])
    return jsonify({"message": "저장 완료"})

