"""[2교시 / 실습 1] ★ with_structured_output() — 부탁을 계약으로

ask_json.py 에서는 프롬프트로 '부탁' 했다. 여기서는 스키마로 '강제' 한다.
결과가 문자열이 아니라 Review 객체로 온다.

    [3주차~4주차]  prompt | llm | StrOutputParser()            → str
    [5주차 오늘]   prompt | llm.with_structured_output(Review) → Review 객체 ★
                                    ▲
                             parser 자리가 스키마로 '승격' 되었다

★ 4주차에는 model 자리를 갈아끼웠다. 오늘은 parser 자리를 갈아끼운다.
  체인의 나머지는 그대로다 — 이것이 Runnable 규약의 이득이다.

⚠️ with_structured_output() 을 쓰면 파서를 따로 붙이지 않는다.
   뒤에 | StrOutputParser() 를 또 붙이면 객체가 다시 문자열로 뭉개진다.

실행:
    python structured.py
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

MODEL = "gemma3:4b"
TEMP = 0  # ★ 구조화 출력은 낮게 (Self-Consistency 는 반대로 높게 — 3교시)

REVIEW = "이 무선 이어폰 배터리는 정말 오래갑니다. 소리도 깨끗해요. 다만 케이스가 좀 크네요."


# ── ① 계약서를 쓴다 ────────────────────────────────
class Review(BaseModel):
    """고객 리뷰에서 뽑아낸 분석 결과."""  # ← 이 docstring 도 모델에게 전달된다 ★

    product: str = Field(description="리뷰 대상 제품명")
    rating: int = Field(description="1~5 사이 정수 별점", ge=1, le=5)
    summary: str = Field(description="30자 이내 한 줄 요약")
    pros: list[str] = Field(description="장점 목록", default_factory=list)
    cons: list[str] = Field(description="단점 목록", default_factory=list)


# ★★ Field(description=...) 은 주석이 아니다.
#    LangChain 이 이 스키마를 JSON Schema 로 변환해 모델에게 실제로 보낸다.
#    즉 description 을 잘 쓰는 것이 곧 프롬프트 엔지니어링이다.
#    1교시의 "명확·구체" 원칙이 여기로 옮겨온 것.


def demo_validation() -> None:
    """검증이 '언제' 일어나는지 먼저 본다 (2-2절)."""
    from pydantic import ValidationError

    print("── Pydantic 검증은 이 자리에서 터진다 ──────")
    cases = [
        ("정상", dict(product="이어폰", rating=4, summary="배터리 우수")),
        ("타입 틀림", dict(product="이어폰", rating="4점", summary="...")),
        ("범위 초과", dict(product="이어폰", rating=9, summary="...")),
        ("필드 누락", dict(product="이어폰")),
    ]
    for label, kwargs in cases:
        try:
            Review(**kwargs)
            print(f"  {label:10s} ✅ 통과")
        except ValidationError as e:
            print(f"  {label:10s} ❌ ValidationError ({e.error_count()}건)")

    print()
    print("  📌 실패가 뒤로 미뤄지지 않고 '여기서' 터진다.")
    print("     1교시의 '한참 뒤에 터지는 조용한 실패' 가 호출 직후로 앞당겨졌다.")


def main() -> None:
    demo_validation()
    print()
    print("=" * 60)
    print()

    # ── ② 프롬프트에서 형식 지시를 뺀다 ★ ────────────
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "너는 고객 리뷰 분석기다."),  # "JSON으로 답하라" 가 사라졌다 ★
            ("human", "다음 리뷰를 분석해라.\n\n{review}"),
        ]
    )

    # ── ③ 모델에 스키마를 물린다 ─────────────────────
    llm = ChatOllama(model=MODEL, temperature=TEMP)
    chain = prompt | llm.with_structured_output(Review)

    # 🔶 방식이 잘 안 맞으면 명시적으로 지정한다 (3-3절 참고)
    #    chain = prompt | llm.with_structured_output(Review, method="json_schema")

    result = chain.invoke({"review": REVIEW})

    print("── 결과 ────────────────────────────────────")
    print("  type      :", type(result))  # <class '__main__.Review'>  ← 문자열이 아니다 ★
    print("  product   :", result.product)
    print("  rating    :", result.rating, "★")
    print("  summary   :", result.summary)
    print("  pros      :", result.pros)
    print("  cons      :", result.cons)
    print()
    print("  rating + 1:", result.rating + 1, " ← int 라서 바로 계산된다 ★")
    print("  model_dump:", result.model_dump())  # dict 로 변환 (저장·전송용)

    print()
    print("=" * 60)
    print("""
관찰 — 무엇이 달라졌나

  관찰 항목                       짚어줄 말
  ────────────────────────────────────────────────────────────────
  프롬프트에서 형식 지시가 사라짐  형식은 이제 프롬프트가 아니라 스키마의 일이다 ★
  반환값이 문자열이 아님           result["rating"] 이 아니라 result.rating
  rating 이 int                    바로 계산·정렬·평균에 쓸 수 있다
  파서를 안 붙였음                 with_structured_output 이 파서 역할까지 한다
  편집기 자동완성                  result. 을 치면 필드가 뜬다

💡 한 걸음 더: Field(description=...) 을 일부러 지우고 다시 돌려 보라.
   품질이 떨어지는 것이 보이면 "description 이 곧 프롬프트" 가 몸으로 전달된다.

⚠️ 스키마를 붙였다고 모델이 실수를 안 하게 되는 것은 아니다.
   실수를 '즉시·확실히 잡아낸다' 는 것이 이득이다. → ab_failrate.py 에서 숫자로 확인
""")
    print("=" * 60)


if __name__ == "__main__":
    main()
