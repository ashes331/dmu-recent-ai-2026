"""[1교시 / 2-5] ★ 끄는 법 — 반드시 시연하십시오.

⚠️⚠️ 추적을 켜면 프롬프트와 응답이 외부 서비스로 전송됩니다.

    넣어도 되는 것          절대 넣으면 안 되는 것
    ────────────────────────────────────────────────────
    수업용 예제 문장        주민번호·연락처 등 개인정보
    공개 문서               회사 기밀·미공개 자료
    직접 만든 테스트 데이터  실제 고객 데이터

  짚어줄 말: "4주차에 배운 보안 기준을 기억하십니까? 로컬 모델을 쓰면
             데이터가 안 나간다고 했었죠. 추적을 켜면 그 이점이 사라집니다."

📌 미니 프로젝트에서 민감한 데이터를 다루는 학생은 '끌 줄' 알아야 합니다.

이 파일은 같은 질문을 3번 던집니다.
그런데 LangSmith 목록에는 2건만 찍혀야 정상입니다. ★

실행:
    python trace_off.py
"""

from dotenv import load_dotenv

load_dotenv()

import os  # noqa: E402

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

MODEL = "gemma3:4b"

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 한 문장으로만 답하는 조교다."),
        ("human", "{question}"),
    ]
)
chain = prompt | ChatOllama(model=MODEL, temperature=0) | StrOutputParser()

Q = "LangSmith 는 무엇을 하는 도구인가?"


def main() -> None:
    print("=" * 64)
    print("  추적 끄는 법 — 세 가지 층위")
    print("=" * 64)
    print(f"  현재 LANGSMITH_TRACING = {os.getenv('LANGSMITH_TRACING')!r}")
    print()

    # ── ① 그냥 실행 — 기록된다 ──────────────────────────────────
    print("[1] 기본 실행 — 이건 기록됩니다")
    print("   ", chain.invoke({"question": Q}))
    print()

    # ── ② 구간만 끈다 ★ ────────────────────────────────────────
    #     민감한 데이터를 다루는 그 구간만 감싸면 됩니다.
    print("[2] tracing_context(enabled=False) 로 감싼 실행 — 기록되지 않습니다 ★")
    try:
        from langsmith import tracing_context

        with tracing_context(enabled=False):
            print("   ", chain.invoke({"question": Q + " (이 실행은 기록되지 않아야 한다)"}))
    except ImportError:
        # 🔶 langsmith 버전에 따라 위치가 다릅니다. 수업 전날 확인하십시오.
        from langsmith.run_helpers import tracing_context  # type: ignore[no-redef]

        with tracing_context(enabled=False):
            print("   ", chain.invoke({"question": Q + " (이 실행은 기록되지 않아야 한다)"}))
    print()

    # ── ③ 다시 켜진다 ──────────────────────────────────────────
    print("[3] with 블록을 나오면 원래대로 — 이건 다시 기록됩니다")
    print("   ", chain.invoke({"question": Q}))

    print()
    print("=" * 64)
    print("""
확인 ★

    smith.langchain.com → week06-tracing 프로젝트를 새로고침합니다.
    방금 3번 호출했는데 목록에는 2건만 늘어나 있어야 합니다.
    [2] 번이 빠진 것입니다.

세 가지 끄는 방법

  범위        방법                                    언제 쓰나
  ──────────────────────────────────────────────────────────────────────
  전체        .env 의 LANGSMITH_TRACING=false          대량 실행 · 한도 절약
              (터미널을 새로 열어야 반영됩니다 ★)
  구간        with tracing_context(enabled=False):     민감 데이터 구간만
  프로젝트    LANGSMITH_PROJECT 를 바꿔 격리           섞이는 것만 막고 싶을 때

⚠️ 강의안에 적힌  chain.invoke(x, config={"callbacks": []})  는
   버전에 따라 '기대대로 꺼지지 않습니다'. 환경변수로 추적이 켜져 있으면
   프레임워크가 추적기를 다시 붙이기 때문입니다.
   → 확실히 끄려면 위의 tracing_context 나 환경변수를 쓰십시오. ★
   🔶 수업 전날 실습실 버전에서 한 번 확인해 어느 쪽을 가르칠지 확정하십시오.

💡 실무 습관: 개발할 때 켜고, 대량 실행할 때 끕니다.
""")
    print("=" * 64)


if __name__ == "__main__":
    main()
