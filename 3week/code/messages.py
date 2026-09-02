"""[2교시 / 실습 4] 메시지 타입 — System / Human / AI

선행 과목에서는 {"role": "system", "content": ...} 딕셔너리를 썼습니다.
LangChain 은 이를 "타입이 있는 객체"로 다룹니다.

    SystemMessage  ← {"role": "system"}       AI의 역할·규칙 설정
    HumanMessage   ← {"role": "user"}         사용자 입력
    AIMessage      ← {"role": "assistant"}    AI의 응답

딕셔너리 대비 장점
    오타("sytem")가 나면 실행 전에 잡히고, 에디터가 자동완성해 준다.

실행:
    python messages.py
"""

import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

# Windows 콘솔(cp949)은 모델이 뱉는 한자·이모지에서 UnicodeEncodeError 를 낸다.
# 출력 인코딩을 UTF-8 로 바꿔 둔다.
sys.stdout.reconfigure(encoding="utf-8")

MODEL = "gemma3:4b"


def main() -> None:
    llm = ChatOllama(model=MODEL)

    # ── 1턴 ────────────────────────────────────────
    messages = [
        SystemMessage(content="당신은 친절한 파이썬 튜터입니다. 초보자 눈높이로 답하세요."),
        HumanMessage(content="리스트와 튜플의 차이가 뭐야?"),
    ]

    response = llm.invoke(messages)
    print("[1턴] 리스트와 튜플의 차이가 뭐야?")
    print(response.content)
    print("=" * 50)

    # ── 2턴: 대화 이력 이어가기 ────────────────────
    # 모델의 답(AIMessage)을 그대로 리스트에 넣고, 다음 질문을 덧붙인다.
    messages.append(response)  # AIMessage 를 변환 없이 append
    messages.append(HumanMessage(content="그럼 언제 튜플을 써?"))

    response2 = llm.invoke(messages)
    print("[2턴] 그럼 언제 튜플을 써?")
    print(response2.content)
    print("=" * 50)

    # 지금 대화 이력이 몇 개인지 확인
    messages.append(response2)
    print(f"누적 메시지 {len(messages)}개")
    for i, m in enumerate(messages, start=1):
        kind = type(m).__name__
        preview = m.content.replace("\n", " ")[:30]
        print(f"  {i}. {kind:15s} {preview}...")

    # ⚠️ 여기서 멈춰서 생각해 볼 것
    #    "2주차의 ② 기억 못 한다" 가 해결됐나?
    #    → 아니다. 여전히 우리가 손으로 리스트를 관리하고 있다.
    #      매 호출마다 전체 이력을 다시 보낸다(= 토큰을 다시 낸다).
    #      진짜 해결은 13주차 체크포인터에서 이뤄진다.
    #
    #    아래 두 줄은 AIMessage 를 직접 만들어 이력에 끼워 넣는 예시다.
    #    (이력을 파일에서 복원할 때 이렇게 쓴다)
    restored = [
        SystemMessage(content="당신은 친절한 파이썬 튜터입니다."),
        HumanMessage(content="리스트와 튜플의 차이가 뭐야?"),
        AIMessage(content="리스트는 수정 가능하고, 튜플은 수정 불가능합니다."),
    ]
    print()
    print(f"손으로 복원한 이력: {len(restored)}개")


if __name__ == "__main__":
    main()
