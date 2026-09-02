"""[2교시 / 1절] MessagesPlaceholder 와 partial() — 빈자리를 설계한다

1교시에서 프롬프트를 고정 부분과 가변 부분으로 나눴다.
그런데 '개수를 모르는 것' 이 하나 있다 — 대화 이력이다.

    1턴째:  system + human
    2턴째:  system + human + ai + human
    3턴째:  system + human + ai + human + ai + human
                     └──────── 늘어난다 ────────┘

    {question}                        문자열 하나를 받는 자리
    MessagesPlaceholder("history")    메시지 '여러 개' 가 들어갈 자리  ★

★ 오늘은 자리를 비워 두는 것까지만 한다.
  이 자리를 누가 채워 주느냐 = 메모리 → 11주차(대화형 RAG) · 13주차(에이전트)
  지금은 빈 리스트 [] 를 넣어도 정상 동작한다.

실행:
    python placeholder_partial.py
"""

from datetime import date

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# ══════════════════════════════════════════════════
# 1-1. 아직 모르는 것을 위한 자리 — MessagesPlaceholder
# ══════════════════════════════════════════════════
def demo_placeholder() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 친절한 상담원입니다."),
            MessagesPlaceholder("history"),  # ← 메시지 '여러 개' 가 들어갈 자리 ★
            ("human", "{question}"),
        ]
    )

    print("── 이력이 있을 때 ──────────────────────────")
    messages = prompt.invoke(
        {
            "history": [  # ← 리스트를 넘긴다
                HumanMessage("환불 규정이 어떻게 되나요?"),
                AIMessage("구매 후 7일 이내 가능합니다."),
            ],
            "question": "영수증이 없어도 되나요?",
        }
    )
    for m in messages.to_messages():
        print(f"  {type(m).__name__:15s} {m.content}")

    print()
    print("── 이력이 아직 없을 때 (빈 리스트) ─────────")
    empty = prompt.invoke({"history": [], "question": "영업시간이 어떻게 되나요?"})
    for m in empty.to_messages():
        print(f"  {type(m).__name__:15s} {m.content}")

    print()
    print("  자리                            받는 것")
    print("  ─────────────────────────────────────────────────────")
    print("  {question}                      문자열 하나")
    print("  MessagesPlaceholder('history')  메시지 리스트  ★")


# ══════════════════════════════════════════════════
# 1-2. partial() — 일부만 먼저 채워 두기
# ══════════════════════════════════════════════════
def demo_partial() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 {role} 전문가입니다. {audience} 눈높이로 답하세요."),
            ("human", "{question}"),
        ]
    )

    print("── partial 없이 — 매번 3개를 다 넘겨야 한다 ─")
    print("  ", prompt.input_variables)
    prompt.invoke({"role": "파이썬", "audience": "초보자", "question": "리스트란?"})
    prompt.invoke({"role": "파이썬", "audience": "초보자", "question": "튜플이란?"})
    #               └──────────── 매번 반복 ────────────┘

    print()
    print("── partial 로 미리 고정 ★ ─────────────────")
    py_tutor = prompt.partial(role="파이썬", audience="초보자")
    print("  ", py_tutor.input_variables)  # ['question'] ← 이제 하나만 넘기면 된다

    for q in ("리스트란?", "튜플이란?"):
        system = py_tutor.invoke({"question": q}).to_messages()[0]
        print(f"   {q:10s} → system: {system.content}")

    # ── 쓰임새 ① 역할 특화 템플릿 파생 ─────────────
    print()
    print("── 하나의 템플릿에서 여러 파생본 ──────────")
    for name, role in [("py_tutor", "파이썬"), ("db_tutor", "데이터베이스"), ("net_tutor", "네트워크")]:
        derived = prompt.partial(role=role, audience="초보자")
        print(f"   {name:10s} {derived.invoke({'question': '...'}).to_messages()[0].content}")

    # ── 쓰임새 ② 호출 시점에 계산되는 값 ★ ─────────
    print()
    print("── 값이 아니라 '함수' 를 넘긴다 ★ ─────────")
    dated_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 {role} 전문가입니다. 오늘은 {today} 입니다."),
            ("human", "{question}"),
        ]
    )

    # ⚠️ partial(today=date.today()) 처럼 '값' 을 넘기면
    #    프로그램이 켜진 순간의 날짜로 굳는다. 서버가 며칠 떠 있으면 날짜가 안 바뀐다.
    frozen = dated_prompt.partial(role="파이썬", today=date.today().isoformat())

    # ✅ '함수' 를 넘기면 매 호출마다 계산된다.
    live = dated_prompt.partial(role="파이썬", today=lambda: date.today().isoformat())

    for label, p in [("굳음 (값)", frozen), ("살아있음 (함수) ★", live)]:
        print(f"   {label:20s} {p.invoke({'question': '...'}).to_messages()[0].content}")

    print()
    print("  📌 partial 이라는 이름은 functools.partial 과 같은 발상이다.")
    print("     인자 일부를 미리 묶어 새 함수를 만드는 것 — 여기서는 새 '프롬프트' 를 만든다.")


def main() -> None:
    demo_placeholder()
    print()
    print("=" * 60)
    print()
    demo_partial()


if __name__ == "__main__":
    main()
