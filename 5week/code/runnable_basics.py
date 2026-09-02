"""[3교시 / 1절] LCEL과 Runnable — 파이프가 실제로 하는 일

3주차부터 계속 써 온 한 줄:

    chain = prompt | llm | parser

이 문법에 이름이 있다 — LCEL (LangChain Expression Language).
그리고 이 | 로 이어붙일 수 있는 것들의 공통 규약이 Runnable 이다.

    .invoke(입력)          하나 실행
    .batch([입력들])       여러 개 병렬 실행     ★ 실습 4
    .stream(입력)          토큰 단위로 흘려보냄  (4주차)
    .ainvoke / .abatch / .astream   각각의 비동기판

★ 이 메서드들을 가진 것은 전부 | 로 이을 수 있다.
  프롬프트도, 모델도, 파서도, 체인 자체도, 심지어 평범한 파이썬 함수도.

  4주차에서 ChatOllama ↔ ChatOpenAI 를 갈아끼울 수 있었던 이유,
  2교시에서 parser 자리를 스키마로 바꿀 수 있었던 이유가 전부 이 규약 하나다.

실행:
    python runnable_basics.py
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_ollama import ChatOllama

MODEL = "gemma3:4b"

llm = ChatOllama(model=MODEL, temperature=0)


# ══════════════════════════════════════════════════
# 1-2. 이어붙이면 그것도 Runnable
# ══════════════════════════════════════════════════
def demo_chain_is_runnable() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "너는 한 문장으로만 답하는 비서다."),
            ("human", "{topic} 을 한 문장으로 요약해줘."),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    print("── 체인의 타입 ─────────────────────────────")
    print("  ", type(chain))  # RunnableSequence
    print("  체인도 .invoke 를 가지므로, 다른 체인의 부품이 된다 ★")

    #    prompt ──▶ llm ──▶ parser
    #    └──────── chain ────────┘     ← 이 덩어리 자체가 다시 하나의 부품
    #
    # 📌 이 성질이 실습 3(least_to_most.py)의 전부다.
    #    큰 체인을 만든다는 것은 작은 체인을 부품으로 쓰는 것이다.

    print()
    print("  invoke :", chain.invoke({"topic": "LCEL"})[:80])


# ══════════════════════════════════════════════════
# 1-3-① RunnableLambda — 평범한 함수를 부품으로
# ══════════════════════════════════════════════════
def demo_runnable_lambda() -> None:
    prompt = ChatPromptTemplate.from_template("{topic} 의 장점을 3가지 알려줘.")

    def shorten(text: str) -> str:
        return text[:100] + " ..."

    chain = prompt | llm | StrOutputParser() | RunnableLambda(shorten)

    print("── RunnableLambda — 함수도 부품이다 ────────")
    print("  ", chain.invoke({"topic": "LangChain"}))
    print()
    print("  ⚠️ 함수는 인자를 하나만 받아야 한다. 여러 값을 넘기려면 dict 하나로 묶는다.")
    print("     실습 3에서 이 방식으로 '반복문' 을 체인 안에 넣는다.")


# ══════════════════════════════════════════════════
# 1-3-② RunnablePassthrough.assign — 입력을 보존하며 항목 추가 ★★
# ══════════════════════════════════════════════════
def demo_assign() -> None:
    keyword_chain = (
        ChatPromptTemplate.from_template("{text} 에서 핵심 키워드 3개만 쉼표로 나열해라.")
        | llm
        | StrOutputParser()
    )

    print("── assign 없이 — 원본이 사라진다 ───────────")
    lost = keyword_chain.invoke({"text": "LCEL 은 Runnable 을 파이프로 잇는 문법이다."})
    print("  ", repr(lost)[:90])
    print("   ↑ 원래 입력 text 가 어디에도 없다. 뒷단계에서 또 써야 하는데 이미 없다.")

    print()
    print("── assign 으로 — 원본을 보존하며 옆에 붙인다 ★")
    step = RunnablePassthrough.assign(keywords=keyword_chain)
    kept = step.invoke({"text": "LCEL 은 Runnable 을 파이프로 잇는 문법이다."})
    for k, v in kept.items():
        print(f"   {k:10s} {str(v)[:60]}")

    #  입력  {"text": "..."}
    #    ▼
    #  출력  {"text": "...", "keywords": <결과>}     ← 원본이 살아 있다 ★
    #
    # ★ 10주차 RAG 에서 다시 나온다. 실습 3에서 바로 쓴다.


# ══════════════════════════════════════════════════
# 1-3-③ RunnableParallel — 두 갈래를 동시에
# ══════════════════════════════════════════════════
def demo_parallel() -> None:
    summary_chain = (
        ChatPromptTemplate.from_template("{text} 를 한 문장으로 요약해라.") | llm | StrOutputParser()
    )
    keyword_chain = (
        ChatPromptTemplate.from_template("{text} 에서 키워드 3개만 쉼표로 나열해라.")
        | llm
        | StrOutputParser()
    )

    both = RunnableParallel(summary=summary_chain, keywords=keyword_chain)
    # dict 리터럴로 써도 같다 (LCEL이 자동 변환)
    #   both = {"summary": summary_chain, "keywords": keyword_chain}

    print("── RunnableParallel — 다른 체인들을 동시에 ─")
    result = both.invoke({"text": "Least-to-Most 는 큰 문제를 하위 질문으로 쪼개 순서대로 푼다."})
    for k, v in result.items():
        print(f"   {k:10s} {str(v)[:70]}")

    print()
    print("  💡 batch() 와 다르다.")
    print("     RunnableParallel = '다른 체인들' 을 같은 입력으로 동시에")
    print("     batch()          = '같은 체인' 에 다른 입력들을 동시에   ← 실습 4는 이쪽 ★")


def main() -> None:
    for fn in (demo_chain_is_runnable, demo_runnable_lambda, demo_assign, demo_parallel):
        fn()
        print()
        print("=" * 60)
        print()

    print("""
실행 방식 3종과 이번 주차의 대응 ★

  메서드      무엇을 하나                      오늘 어디에
  ────────────────────────────────────────────────────────────────
  invoke()    하나 실행                        실습 3 (분해 체인)
  batch()     같은 체인, 여러 입력을 병렬 ★    실습 4 (Self-Consistency)
  stream()    토큰 단위 출력                   4주차에서 완료

⚠️ batch() 는 "빨리 실행" 이 아니라 "동시에 실행" 이다.
   로컬 GPU는 동시 처리 여력이 적어 실제로는 거의 순차 실행될 수 있다.
   상용 API 에서는 네트워크 왕복이 겹쳐져 차이가 크게 난다.
""")


if __name__ == "__main__":
    main()
