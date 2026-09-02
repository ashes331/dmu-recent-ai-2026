"""[2교시 / 실습 2] ★★ "JSON으로 답해줘" vs 스키마 강제 — 실패율을 직접 센다

핵심 질문: "프롬프트를 더 강하게 쓰면 되지 않나요?"  → 숫자로 답한다.

    같은 리뷰 · 같은 모델 · 같은 온도로 각각 N회

    방법 A: "반드시 JSON으로만 답하라"  ──▶ json.loads() + 필드/타입 검사
    방법 B: with_structured_output()    ──▶ 스키마 검증

                      실패 횟수를 센다

★ 판정 기준을 A·B 양쪽에 똑같이 적용하는 것이 중요하다.
  방법 A를 json.loads() 성공 여부로만 재면 A에 유리하게 왜곡된다.
  그래서 A도 파싱 후 같은 Review 스키마로 검증한다.

  무엇을 실패로 세나
    JSON 파싱 자체가 안 됨              ❌
    파싱은 됐는데 필드가 없음            ❌
    파싱은 됐는데 타입이 다름 ("4점")    ❌ ★
    값이 범위를 벗어남 (rating=9)        ❌

⚠️ temperature 를 A·B에 똑같이 적용할 것. 한쪽만 0으로 두면 실험이 성립하지 않는다.
   학생이 "B가 이긴 건 온도를 낮춰서 아니냐" 고 물으면 — 그 질문이 나오면 좋은 수업이다.

🔶 시간 관리: 로컬 4B로 20회 × 2 = 40회면 수 분이 걸린다.
   실행 버튼을 누르게 한 직후에 4-3 해석을 진행하고, 끝난 순서대로 결과를 받는다.
   시간이 빠듯하면 N = 10 으로 낮춰도 경향은 보인다.

실행:
    python ab_failrate.py
    python ab_failrate.py 10        # N 을 바꿔서
"""

import json
import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field, ValidationError

MODEL = "gemma3:4b"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20  # 반복 횟수
TEMP = 0.7  # ★ 0이면 매번 같은 답 → 차이가 안 보인다

REVIEW = "이 무선 이어폰 배터리는 정말 오래갑니다. 다만 케이스가 좀 크네요."


class Review(BaseModel):
    """고객 리뷰 분석 결과."""

    product: str = Field(description="제품명")
    rating: int = Field(description="1~5 정수 별점", ge=1, le=5)
    summary: str = Field(description="30자 이내 요약")


# ══════════════════════════════════════════════════
# 방법 A — 프롬프트로 부탁
# ══════════════════════════════════════════════════
prompt_a = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 리뷰 분석기다. 반드시 JSON으로만 답하라. 설명을 덧붙이지 마라."),
        (
            "human",
            "다음 리뷰를 분석해라. 필드는 product(문자열), "
            "rating(1~5 정수), summary(문자열) 이다.\n\n{review}",
        ),
    ]
)
chain_a = prompt_a | ChatOllama(model=MODEL, temperature=TEMP) | StrOutputParser()


# ══════════════════════════════════════════════════
# 방법 B — 스키마로 강제
# ══════════════════════════════════════════════════
prompt_b = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 리뷰 분석기다."),
        ("human", "다음 리뷰를 분석해라.\n\n{review}"),
    ]
)
chain_b = prompt_b | ChatOllama(model=MODEL, temperature=TEMP).with_structured_output(Review)


def run_a() -> str | None:
    """실패면 사유 문자열, 성공이면 None."""
    text = chain_a.invoke({"review": REVIEW})
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return "JSON 파싱 실패"  # 앞말 · 코드펜스

    if not isinstance(data, dict):
        return "JSON이 객체가 아님"

    try:
        Review(**data)  # ★ B와 같은 잣대로 검증한다
    except ValidationError as e:
        return f"스키마 불일치({e.error_count()}건)"  # 타입 · 필드명 · 범위
    except TypeError:
        return "필드명 불일치"
    return None


def run_b() -> str | None:
    try:
        chain_b.invoke({"review": REVIEW})
    except Exception as e:
        return type(e).__name__
    return None


def main() -> None:
    print(f"모델={MODEL}  temperature={TEMP}  N={N}   (A·B 동일 조건 ★)")
    print("=" * 60)

    summary = []
    for label, fn in [("A  프롬프트로 부탁", run_a), ("B  스키마로 강제", run_b)]:
        fails = []
        print(f"{label} : ", end="", flush=True)
        for i in range(N):
            reason = fn()
            print("." if reason is None else "X", end="", flush=True)
            if reason:
                fails.append((i + 1, reason))
        rate = len(fails) / N * 100
        print(f"\n[{label}]  실패 {len(fails)}/{N}  =  {rate:.0f}%")
        for i, r in fails:
            print(f"    - {i}회차: {r}")
        print("-" * 60)
        summary.append((label, len(fails), rate))

    print()
    print("결과 기록표 — 저장소에 함께 커밋할 것 ★")
    print("  방법                          실패 횟수      실패율")
    print("  " + "─" * 52)
    for label, n_fail, rate in summary:
        print(f"  {label:28s} {n_fail:>3d} / {N}      {rate:>5.0f} %")

    print()
    print("""
읽어낼 것

  관찰                        의미
  ────────────────────────────────────────────────────────────────
  A의 실패율 > B의 실패율      부탁은 확률, 스키마는 계약 ★
  A의 실패 사유가 제각각       앞말·코드펜스·타입·필드명 — 예외 처리를 몇 개나 짜야 하나
  B도 0%가 아닐 수 있음 ⚠️     스키마도 만능은 아니다 (아래)
  B의 실패는 '즉시' 예외       A의 실패는 한참 뒤에 터진다

⚖️ B가 0%가 아니어도 당황하지 말 것 — 오히려 더 좋은 수업 재료다.

  필드 값이 말이 안 됨 (rating=1인데 극찬 리뷰)
      → 스키마는 '형식' 을 보장하지, '내용' 을 보장하지 않는다 ★
  모델이 스키마를 못 지킴
      → 소형 로컬 모델의 한계. with_structured_output(..., method="json_schema") 로 조정

  내용의 진위 검증은 7주차 평가(Evaluation)의 주제다.

📌 결론: "프롬프트를 강하게 쓰는 것으로는 0%에 못 간다.
         형식은 프롬프트가 아니라 타입 시스템이 지켜야 한다."
""")


if __name__ == "__main__":
    main()
