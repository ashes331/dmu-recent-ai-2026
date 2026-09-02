"""[3교시 / 1절] ChatPromptTemplate — 프롬프트를 부품으로

f-string 으로 충분해 보이는데 무엇이 문제인가?

    topic = "파이썬"
    prompt = f"{level}에게 {topic}의 장점 3가지를 설명하세요."

    - 재사용 불가        : 다른 파일에서 쓰려면 복사해야 함
    - 변수 누락 미검출   : level 을 안 넘기면 NameError 가 런타임에 터짐
    - 버전 관리 불가     : 무엇이 바뀌었는지 추적 어려움
    - 체인에 못 끼움 ★  : f-string 은 문자열일 뿐, 부품이 아님

핵심: 프롬프트를 "문자열이 아니라 객체"로 다뤄야 파이프에 끼울 수 있다.

실행:
    python prompt_template.py
"""

from langchain_core.prompts import ChatPromptTemplate


def main() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 프로그래밍 강사입니다. {level} 눈높이로 설명하세요."),
            ("human", "{topic}의 장점 3가지를 각각 한 문장으로 알려줘."),
        ]
    )

    # ── 1. 값을 채워서 실제 메시지 생성 ────────────
    messages = prompt.invoke({"level": "초보자", "topic": "파이썬"})
    print("── prompt.invoke() 결과 ──────────────────")
    print(messages)
    print()

    # 결과가 메시지 리스트다.
    # 2교시(messages.py)에서 손으로 만들던 것이 자동 생성됐다.
    for m in messages.to_messages():
        print(f"  {type(m).__name__:15s} {m.content}")
    print()

    # ★ 중요한 관찰
    #   prompt.invoke() 와 llm.invoke() 가 "같은 이름"이다.
    #   우연이 아니라 설계다. first_chain.py 에서 그 이유가 드러난다.

    # ── 2. 템플릿은 무엇이 필요한지 스스로 안다 ────
    print("필요한 변수:", prompt.input_variables)  # ['level', 'topic']
    print()

    # ── 3. 변수를 빠뜨리면? ────────────────────────
    print("── topic 을 빠뜨리고 호출해 보면 ─────────")
    try:
        prompt.invoke({"level": "초보자"})
    except KeyError as e:
        # 에러 메시지가 길어서 첫 줄만 보여준다
        first_line = str(e).strip('"').split("\\n")[0]
        print(f"  KeyError: {first_line}")
        print("  → 무엇이 빠졌는지 이름까지 알려준다. 명확한 에러로 즉시 발견.")

    # f-string 이라면 NameError 가 나거나,
    # 더 나쁘게는 엉뚱한 변수가 들어가 "조용히 잘못 동작"한다.

    # ── 4. 같은 템플릿을 값만 바꿔 재사용 ──────────
    print()
    print("── 같은 템플릿, 다른 값 ──────────────────")
    for values in [
        {"level": "초보자", "topic": "파이썬"},
        {"level": "실무자", "topic": "Git"},
    ]:
        human = prompt.invoke(values).to_messages()[1]
        print(f"  {values} → {human.content}")


if __name__ == "__main__":
    main()
