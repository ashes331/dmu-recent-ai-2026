"""[2교시 / 1절] MessagesPlaceholder 와 partial() — 빈자리를 설계한다

1교시에서 프롬프트를 고정 부분과 가변 부분으로 나눴다.
그런데 '개수를 모르는 것' 이 하나 있다 — 대화 이력이다.

    1턴째:  system + human
    2턴째:  system + human + ai + human
    3턴째:  system + human + ai + human + ai + human
                     └──────── 늘어난다 ────────┘

    {question}                        문자열 하나를 받는 자리
    MessagesPlaceholder("history")    메시지 '여러 개' 가 들어갈 자리  ★

★ 오늘은 자리만 만든다 — 채우는 것은 메모리의 몫.
  지난 대화를 저장했다가 이 자리에 자동으로 넣어 주는 장치 = 메모리 → 11주차(대화형 RAG) · 13주차(에이전트)
  지금은 빈 리스트 [] 를 넣어도 정상 동작한다.

실행:
    python placeholder_partial.py
"""

from datetime import date, datetime

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

    # '값' 을 넘기면 partial 을 부른 순간 한 번 계산되어 고정된다 — 바뀌지 않는 값에 쓴다.
    fixed = dated_prompt.partial(role="파이썬", today=date.today().isoformat())

    # ★ '함수' 를 넘기면 invoke 할 때마다 새로 계산된다 — 시간을 동적으로 채울 수 있다.
    #    서버를 며칠 켜 두어도 날짜가 저절로 넘어간다.
    live = dated_prompt.partial(role="파이썬", today=lambda: date.today().isoformat())

    # 응용 — 현재 시각까지 동적으로
    clock = dated_prompt.partial(role="파이썬", today=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    for label, p in [("고정 (값)", fixed), ("동적 (함수) ★", live), ("동적 (시각까지)", clock)]:
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
