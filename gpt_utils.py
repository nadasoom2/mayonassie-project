# gpt 감정 분석

import openai  # 상단 import에 추가
import os

# GPT API 키는 환경 변수 또는 직접 문자열로 설정 가능

openai.api_key = os.getenv("OPENAI_API_KEY")

# GPT 분석 함수
# GPT 분석 함수 (None 반환 포함)
def extract_emotion_scores(row, col_names):
    emotion_map = {
        "분노": ["anger1", "anger2", "anger3"],
        "우울": ["depress1", "depress2", "depress3"],
        "불안": ["anxiety1", "anxiety2", "anxiety3"],
        "외로움": ["lonely1", "lonely2", "lonely3"],
        "무기력": ["fatigue1", "fatigue2", "fatigue3"],
        "슬픔": ["sad1", "sad2", "sad3"],
        "기쁨": ["joy1", "joy2", "joy3"],
        "행복": ["happy1", "happy2", "happy3"],
        "평온": ["calm1", "calm2"],
        "만족감": ["satisfy1", "satisfy2"]
    }
    row_dict = dict(zip(col_names, row))
    scores = {}
    for emotion, keys in emotion_map.items():
        vals = [row_dict.get(k) for k in keys if isinstance(row_dict.get(k), int)]
        scores[emotion] = round(sum(vals)/len(vals), 2) if vals else 0
    return scores

def analyze_emotions_with_gpt(survey_row, column_names):
    row_dict = dict(zip(column_names, survey_row))

    # 주관식 텍스트 필드 목록
    text_fields = [
        "share1", "share2", "share3",   # 부정 감정 나눔
        "posShare1", "posShare2", "posShare3",  # 긍정 감정 나눔
        "calm3", "satisfy3"             # 평온/만족 주관식
    ]

    # 유효한 주관식만 추출
    memo_combined = "\n".join(
        f"- {row_dict[field].strip()}" 
        for field in text_fields 
        if field in row_dict and row_dict[field] and str(row_dict[field]).strip() != ""
    )

    # 감정 점수 필드 기준
    emotion_map = {
        "분노": ["anger1", "anger2", "anger3"],
        "우울": ["depress1", "depress2", "depress3"],
        "불안": ["anxiety1", "anxiety2", "anxiety3"],
        "외로움": ["lonely1", "lonely2", "lonely3"],
        "무기력": ["fatigue1", "fatigue2", "fatigue3"],
        "슬픔": ["sad1", "sad2", "sad3"],
        "기쁨": ["joy1", "joy2", "joy3"],
        "행복": ["happy1", "happy2", "happy3"],
        "평온": ["calm1", "calm2"],
        "만족감": ["satisfy1", "satisfy2"]
    }

    emotion_scores = {}
    for 감정, 키들 in emotion_map.items():
        점수들 = [row_dict.get(k) for k in 키들 if isinstance(row_dict.get(k), int)]
        평균 = round(sum(점수들) / len(점수들), 2) if 점수들 else 0
        emotion_scores[감정] = 평균

    # 주관식 감정 내용
    memo_fields = ["share1", "share2", "share3", "posShare1", "posShare2", "posShare3", "calm3", "satisfy3"]
    memo_combined = "\n".join(f"- {row_dict.get(m, '')}" for m in memo_fields if row_dict.get(m, "").strip())

    # 프롬프트 생성
    prompt = (
        "다음은 사용자의 감정 설문 점수입니다.\n\n"
        + "\n".join([f"{감정}: {점수}" for 감정, 점수 in emotion_scores.items()])
        + f"\n\n사용자가 추가로 남긴 감정 공유 내용:\n{memo_combined if memo_combined else '(없음)'}\n\n"
        + "정보를 바탕으로 이 사용자의 감정 상태를 따뜻하고 직관적으로 요약해줘. "
          "진단이 아니라 사용자 입장에서 공감할 수 있는 말투로, ~합니다 말투는 금지야. "
          "‘당신의 감정 상태는...’ 같은 문장은 쓰지 말고, 바로 감정 묘사로 시작해. "
          "복합적인 감정이 섞여 있어도 자연스럽게 연결해줘. "
          "공유한 주관식 감정 내용이 있다면 그것을 중심으로 감정 흐름을 설명해줘. "
          "글 길이는 2~3문장 이내로, 너무 길지 않게 작성해줘."
    )

    # GPT 호출
    try:
        import openai
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        import traceback
        print("❌ GPT 분석 중 예외 발생:", str(e))
        traceback.print_exc()
        return None

