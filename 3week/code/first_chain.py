"""[3교시 / 실습 5] ★ 첫 번째 체인 — prompt | llm | parser

이 파일이 과제 1의 제출물입니다.  (저장소 경로: week03/first_chain.py)

       입력 dict
          │
          ▼
      ┌─────────┐  messages   ┌──────┐  AIMessage  ┌────────┐   str
      │ prompt  │ ──────────▶ │ llm  │ ──────────▶ │ parser │ ─────▶ 출력
      └─────────┘             └──────┘             └────────┘
          └─────────────────── chain ───────────────────┘

이 짧은 한 줄이 5주차 LCEL, 10~11주차 RAG 체인, 12주차 그래프의 기본형입니다.

실행:
    python first_chain.py
"""

import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# Windows 콘솔(cp949)은 모델이 뱉는 한자·이모지에서 UnicodeEncodeError 를 낸다.
# 출력 인코딩을 UTF-8 로 바꿔 둔다.
sys.stdout.reconfigure(encoding="utf-8")

MODEL = "gemma3:4b"

# ── 부품 3개 ──────────────────────────────────────
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "당신은 프로그래밍 강사입니다. {level} 눈높이로 설명하세요."),
        ("human", "{topic}의 장점 3가지를 각각 한 문장으로 알려줘."),
    ]
)
llm = ChatOllama(model=MODEL)
parser = StrOutputParser()


def step_by_step() -> None:
    """방법 A — 하나씩 손으로 넘기기.

    동작은 한다. 하지만 중간 변수가 3개 필요하고,
    부품이 늘어날수록 코드가 계속 길어진다.
    """
    print("── 방법 A: 손으로 하나씩 ─────────────────")

    messages = prompt.invoke({"level": "초보자", "topic": "파이썬"})
    ai_msg = llm.invoke(messages)
    text = parser.invoke(ai_msg)

    print(text.strip())


def with_pipe() -> None:
    """방법 B — 파이프로 연결하기.  ★

    | 는 파이썬의 __or__ 연산자를 LangChain 이 재정의한 것이다.
    유닉스 파이프(cat file | grep x | wc -l)와 같은 발상.

    이 구조에 이름이 있다 — LCEL (LangChain Expression Language).
    5주차에서 본격적으로 다룬다.
    """
    print("── 방법 B: 파이프로 한 줄 ────────────────")

    chain = prompt | llm | parser  # ← 세 줄이 한 줄로

    text = chain.invoke({"level": "초보자", "topic": "파이썬"})
    print(text.strip())

    # 체인 자체도 .invoke() 를 가진다 → 다른 체인의 부품이 될 수 있다
    print()
    print("체인의 타입:", type(chain))  # RunnableSequence


def batch_demo() -> None:
    """batch() — 여러 입력을 한 번에 실행.

    5주차 Self-Consistency(같은 질문을 여러 번 돌려 다수결)의 기반이 된다.
    """
    print("── batch(): 여러 입력을 한 번에 ──────────")

    chain = prompt | llm | parser
    results = chain.batch(
        [
            {"level": "초보자", "topic": "파이썬"},
            {"level": "실무자", "topic": "Git"},
        ]
    )

    for r in results:
        print(r.strip()[:60], "...")
        print("-" * 40)


def stream_demo() -> None:
    """stream() — 토큰 단위로 흘려보내기.

    답이 다 나올 때까지 기다리지 않고 글자가 흘러나온다.
    ChatGPT 의 그 느낌. 4주차에서 자세히 다룬다.
    """
    print("── stream(): 토큰 단위 출력 ──────────────")

    chain = prompt | llm | parser

    for chunk in chain.stream({"level": "초보자", "topic": "파이썬"}):
        print(chunk, end="", flush=True)
    print()


def main() -> None:
    step_by_step()
    print("\n" + "=" * 50 + "\n")

    with_pipe()
    print("\n" + "=" * 50 + "\n")

    batch_demo()
    print("\n" + "=" * 50 + "\n")

    stream_demo()

    print()
    print("=" * 50)
    print("""
정리

  실행 방식 3종
      invoke()   하나 실행            기본
      batch()    여러 개 병렬 실행     5주차 Self-Consistency
      stream()   토큰 단위 스트리밍    4주차

  10주차 RAG 에서는 앞에 부품이 하나 더 붙는다:
      retriever | prompt | llm | parser
""")
    print("=" * 50)


if __name__ == "__main__":
    main()
