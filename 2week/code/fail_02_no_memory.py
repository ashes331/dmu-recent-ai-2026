# 파일: fail_02_no_memory.py
# 2주차 2교시 실습 1 ― 실패 ② "어제 한 얘기를 기억 못 한다"
#
# 실행:  python fail_02_no_memory.py
#
# 작년 Streamlit 챗봇에서 대화가 이어졌던 것은 모델이 기억해서가 아니라
# session_state 에 메시지를 쌓아 "매번 전체 이력을 다시 보냈기" 때문이다.
# 그 사실을 두 방식의 비교로 확인한다.

import os

import ollama

MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

TELL = "내 이름은 이재숙이야. 기억해줘."
ASK = "내 이름이 뭐라고 했지?"


def chat(messages):
    """messages 를 통째로 보내고 답변 문자열만 돌려준다."""
    response = ollama.chat(model=MODEL, messages=messages)
    return response["message"]["content"].strip()


def demo_without_history():
    """호출마다 messages 를 새로 만든다 = 이력이 끊긴다."""
    print("=" * 62)
    print("  [A] 이력을 안 보낸 경우 ― 매 호출이 독립적")
    print("=" * 62)

    r1 = chat([{"role": "user", "content": TELL}])
    print(f"  1차 질문 : {TELL}")
    print(f"  1차 응답 : {r1}")
    print()

    # 새 대화다. 앞의 내용이 전혀 들어 있지 않다.
    r2 = chat([{"role": "user", "content": ASK}])
    print(f"  2차 질문 : {ASK}")
    print(f"  2차 응답 : {r2}")
    print()
    return r2


def demo_with_history():
    """앞의 질문·답변을 messages 에 쌓아서 다시 보낸다 = 이력이 이어진다."""
    print("=" * 62)
    print("  [B] 이력을 직접 쌓아 보낸 경우")
    print("=" * 62)

    history = [{"role": "user", "content": TELL}]
    r1 = chat(history)
    history.append({"role": "assistant", "content": r1})   # 답변도 쌓아야 한다
    history.append({"role": "user", "content": ASK})

    r2 = chat(history)
    print(f"  보낸 메시지 수 : {len(history)}개")
    print(f"  2차 질문 : {ASK}")
    print(f"  2차 응답 : {r2}")
    print()
    return r2


def main():
    print()
    print(f"모델 : {MODEL}")
    print()

    a2 = demo_without_history()
    b2 = demo_with_history()

    print("=" * 62)
    print("  관찰 포인트")
    print("=" * 62)
    print(f"  [A] 이름을 알고 있는가 :  {'예' if '이재숙' in a2 else '아니오  ← 모릅니다'}")
    print(f"  [B] 이름을 알고 있는가 :  {'예  ← 우리가 보내줬으니까' if '이재숙' in b2 else '아니오'}")
    print()
    print("  왜 그런가 : ollama.chat() 은 매 호출이 완전히 독립적이다.")
    print("              [B]가 기억하는 것처럼 보인 것은 우리가 이력을 다시 보냈기 때문이다.")
    print()
    print("  그럼 계속 쌓으면 되지 않나?")
    print("    → 컨텍스트 윈도우 한계에 부딪히고, 토큰 비용이 계속 늘어난다.")
    print("  필요 : 대화 상태를 저장·관리하는 장치  →  메모리 / LangGraph (13주차)")
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
