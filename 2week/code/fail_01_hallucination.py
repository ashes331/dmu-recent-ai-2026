# 파일: fail_01_hallucination.py
# 2주차 2교시 실습 1 ― 실패 ① "모르는 것을 지어낸다"
#
# 실행 (PowerShell):
#   ollama serve            # 이미 떠 있으면 생략
#   ollama pull gemma3:4b
#   python fail_01_hallucination.py
#
# 이 스크립트는 LangChain 을 쓰지 않는다. 선행 과목에서 쓰던 ollama 패키지 그대로다.
# "맨손으로 해보니 안 되더라"를 먼저 겪는 것이 목적이다.

import os

import ollama

MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

# 모델이 학습했을 리 없는, 우리 학과의 구체적 사실을 묻는다
QUESTION = "동양미래대학교 인공지능소프트웨어학과의 졸업 이수 학점과 필수 교과목을 알려줘."

# 같은 질문을 두 번 던진다. 답이 달라지면 "근거가 없다"는 증거가 된다.
RUNS = 2


def ask(question):
    """단일 호출 ― 이전 대화도, 외부 문서도 붙이지 않는다."""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
    )
    return response["message"]["content"]


def main():
    print()
    print("=" * 62)
    print("  실패 ①  모르는 것을 지어낸다")
    print("=" * 62)
    print(f"  모델 : {MODEL}")
    print(f"  질문 : {QUESTION}")
    print()

    answers = []
    for i in range(1, RUNS + 1):
        print("-" * 62)
        print(f"  [{i}회차 응답]")
        print("-" * 62)
        answer = ask(QUESTION)
        print(answer.strip())
        print()
        answers.append(answer.strip())

    print("=" * 62)
    print("  관찰 포인트")
    print("=" * 62)
    print("  1) 모델이 '모른다'고 했는가?   → 대부분 숫자와 과목명을 지어냅니다")
    print("  2) 답변에 확신이 담겨 있는가?  → 틀린 답을 자신 있게 말하는 것이 더 위험합니다")
    same = "같음" if answers[0] == answers[-1] else "다름  ← 근거가 없다는 증거!"
    print(f"  3) 1회차와 {RUNS}회차 답변이 같은가?  → {same}")
    print()
    print("  진단 : 모델은 사실을 저장한 적이 없다. 확률 계산기일 뿐이다.")
    print("  필요 : 우리 문서를 찾아서 근거로 주는 장치  →  RAG (10~11주차)")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 실습실에서 가장 흔한 실패는 서버 미기동과 모델 미설치 두 가지다.
        print()
        print(f"[실행 실패] {type(e).__name__}: {e}")
        print()
        print("  확인할 것")
        print("    1) Ollama 서버가 떠 있는가        :  ollama serve")
        print(f"    2) 모델이 받아져 있는가            :  ollama pull {MODEL}")
        print("    3) 파이썬 패키지가 깔려 있는가     :  pip install ollama")
        print()
