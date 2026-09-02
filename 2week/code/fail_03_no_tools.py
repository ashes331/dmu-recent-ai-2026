# 파일: fail_03_no_tools.py
# 2주차 2교시 실습 1 ― 실패 ③ "지금 무슨 일이 일어나는지 모른다"
#
# 실행:  python fail_03_no_tools.py
#
# 두 가지를 한 번에 묻는다.
#   · 오늘 날씨      → 학습 시점 이후를 모르므로 모르거나 지어낸다
#   · 큰 수의 곱셈   → 계산기가 아니라 확률 예측이므로 자주 틀린다

import os

import ollama

MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

QUESTION = "지금 서울 날씨 알려줘. 그리고 137 * 892는?"

# 채점용 정답. 모델이 이 숫자를 맞히는지 눈으로만 확인하지 말고 코드로 확인한다.
A, B = 137, 892
ANSWER = A * B      # 122204


def main():
    print()
    print("=" * 62)
    print("  실패 ③  바깥 세상과 연결되어 있지 않다")
    print("=" * 62)
    print(f"  모델 : {MODEL}")
    print(f"  질문 : {QUESTION}")
    print()

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": QUESTION}],
    )
    content = response["message"]["content"].strip()

    print("-" * 62)
    print("  [응답]")
    print("-" * 62)
    print(content)
    print()

    # 숫자에 쉼표가 섞여 나오는 경우가 있어 제거한 뒤 찾는다.
    flat = content.replace(",", "")
    got_it = str(ANSWER) in flat

    print("=" * 62)
    print("  관찰 포인트")
    print("=" * 62)
    print("  날씨 : 실시간 정보다. 모델에는 접근 수단이 없다.")
    print("         → '모른다'고 하면 그나마 정직한 것이고, 지어내면 위험하다.")
    print(f"  곱셈 : {A} * {B} = {ANSWER}")
    print(f"         모델이 맞혔는가 :  {'예' if got_it else '아니오  ← 확률 예측이라 자릿수가 크면 자주 틀립니다'}")
    print()
    print("  진단 : 모델은 검색도 계산도 하지 않는다. 다음 토큰을 고를 뿐이다.")
    print("  필요 : 도구를 붙이고, 모델이 스스로 고르게 하는 장치  →  Tool Calling (9주차)")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print(f"[실행 실패] {type(e).__name__}: {e}")
        print()
        print("  확인할 것")
        print("    1) Ollama 서버가 떠 있는가        :  ollama serve")
        print(f"    2) 모델이 받아져 있는가            :  ollama pull {MODEL}")
        print("    3) 파이썬 패키지가 깔려 있는가     :  pip install ollama")
        print()
