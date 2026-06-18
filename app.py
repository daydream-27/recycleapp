import os
import re
import base64
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
KAKAO_MAP_KEY = os.environ.get("KAKAO_MAP_KEY")

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("[OK] OpenAI 연결됨")
else:
    client = None
    print("[경고] OPENAI_API_KEY 없음")


def analyze_image(image_base64, mime_type="image/jpeg"):
    if not client:
        return "API 키가 없어요. 관리자에게 문의하세요."

    prompt = """너는 대한민국 환경부 분리배출 가이드 전문가야.
사용자가 올린 사진을 분석해서 아래 형식으로 알려줘.

1. **재질 분류**: (예: 플라스틱 PET, 종이, 유리, 캔 등)
2. **분리배출 방법**: 구체적으로 어떻게 버려야 하는지
3. **세척 필요 여부**: 씻어야 하는지 여부
4. **라벨/뚜껑 처리**: 제거해야 하는지 여부
5. **주의사항**: 특별히 주의할 점

만약 재활용이 불가능하면 '일반 쓰레기'로 명확히 분류해줘.
한국어로 친절하고 간결하게 답해줘."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }],
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[오류]: {e}")
        return f"분석 중 오류가 발생했어요: {str(e)}"


def analyze_text(text):
    if not client:
        return "API 키가 없어요. 관리자에게 문의하세요."

    prompt = f"""너는 대한민국 환경부 분리배출 가이드 전문가야.
사용자가 "{text}"을(를) 어떻게 버려야 하는지 아래 형식으로 알려줘.

1. **재질 분류**: (예: 플라스틱 PET, 종이, 유리, 캔 등)
2. **분리배출 방법**: 구체적으로 어떻게 버려야 하는지
3. **세척 필요 여부**: 씻어야 하는지 여부
4. **라벨/뚜껑 처리**: 제거해야 하는지 여부
5. **주의사항**: 특별히 주의할 점

만약 재활용이 불가능하면 '일반 쓰레기'로 명확히 분류해줘.
한국어로 친절하고 간결하게 답해줘."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[오류]: {e}")
        return f"분석 중 오류가 발생했어요: {str(e)}"


@app.route("/")
def index():
    return render_template("index.html", kakao_key=KAKAO_MAP_KEY)


@app.route("/analyze", methods=["POST"])
def analyze():
    # 이미지 분석
    if "image" in request.files:
        image_file = request.files["image"]
        mime_type = image_file.mimetype or "image/jpeg"
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        result = analyze_image(image_data, mime_type)
        return jsonify({"success": True, "result": result})

    # 텍스트 분석
    text = request.form.get("text", "").strip()
    if text:
        result = analyze_text(text)
        return jsonify({"success": True, "result": result})

    return jsonify({"success": False, "result": "이미지나 텍스트를 입력해주세요."})


if __name__ == "__main__":
    app.run(debug=True)
