"""[2교시 / 2절] ★★ LLM-as-a-Judge — 모델에게 채점을 맡긴다, 그리고 그 판정자를 검증한다

  규칙으로 안 되는 과제가 있습니다 — 요약 품질, 답변의 적절성, "같은 뜻인가".
  그럴 때 채점을 모델에게 맡깁니다.

  ★ 그런데 핵심 질문이 남습니다.
        "채점자가 모델이라면, **그 모델은 믿을 수 있습니까?**"

     같은 답안을 두 판정자에게 채점시켜 봅니다.

       예제  학생 답            로컬 4B 판정   상용 판정   사람(정답)
       ─────────────────────────────────────────────────────────────
        1    "긍정입니다"        ✅ 정답        ✅ 정답      ✅
        2    "긍정이 아닙니다"   ✅ 정답 ⚠️     ❌ 오답      ❌
        3    "약간 좋은 편"      ❌ 오답        ✅ 정답      ✅
                         │
                         ▼
     ⚠️ 판정자가 22% 틀린다면, 그 판정으로 잰 A/B 결과는 얼마나 믿을 수 있나?

  ★★ 이 절의 결론: **평가 결과를 믿으려면 평가자를 먼저 믿을 수 있어야 합니다.**
     실무 절차 — 예제 10개 정도를 사람이 직접 채점해 두고 판정자와 대조합니다.
     일치율이 낮으면 판정 프롬프트를 고치거나 판정자 모델을 바꿉니다.
     **판정자도 평가 대상입니다.**

  ⚠️ 판정 기준은 **이분 판정(예/아니오)** 으로 설계하십시오.
     5점 척도는 로컬 모델에서 점수가 흔들립니다 (같은 답에 3점, 4점을 오갑니다).

  🔶 상용 API 는 본 차시 배정 4순위입니다. **판정자에만**, **소규모 데이터셋에만** 쓰십시오.
     OPENAI_API_KEY 가 없으면 로컬 판정자만 돌아갑니다 (그래도 수업은 성립합니다).

실행:
    python llm_judge.py           # 로컬 판정자 (+ 키가 있으면 상용까지 비교) ★
    python llm_judge.py local     # 로컬만
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

LOCAL_MODEL = "gemma3:4b"
OPENAI_MODEL = "gpt-4o-mini"  # 🔶 예산·정책에 맞춰 확정


class Judgement(BaseModel):
    """채점 결과 — ★ bool 로 강제해야 셀 수 있다 (5주차 구조화 출력)."""

    is_correct: bool = Field(description="정답과 같은 뜻이면 true, 아니면 false")
    reason: str = Field(description="그렇게 판단한 이유 한 문장")


judge_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 채점자다. 표현이 달라도 '같은 뜻'이면 정답으로 판정하라. "
            "부정 표현('아니다', '~가 아닙니다')이 붙어 뜻이 뒤집혔다면 오답이다. "
            "반드시 true 또는 false 하나로 판정한다.",
        ),
        (
            "human",
            "질문: {question}\n정답: {reference}\n학생 답: {answer}\n\n"
            "학생 답이 정답과 같은 뜻인가?",
        ),
    ]
)


# ── 사람이 미리 채점해 둔 정답표 (Gold) ★★ ───────────────────
#    판정자를 검증하려면 '판정자보다 먼저 믿을 수 있는 기준' 이 있어야 합니다.
#    (질문, 기대 정답, 학생 답, 사람 판정)
GOLD = [
    ("배송이 하루 만에 왔어요", "긍정", "긍정", True),
    ("배송이 하루 만에 왔어요", "긍정", "긍정입니다", True),
    ("배송이 하루 만에 왔어요", "긍정", "이 리뷰는 긍정적입니다", True),
    ("배송이 하루 만에 왔어요", "긍정", "긍정이 아닙니다", False),  # ★ 부정문 함정
    ("나쁘지 않네요", "긍정", "약간 좋은 편", True),  # ★ 규칙 기반이 못 잡는 것
    ("나쁘지 않네요", "긍정", "중립", False),
    ("화면에 흠집이 있네요", "부정", "부정적", True),
    ("화면에 흠집이 있네요", "부정", "positive", False),  # ★ 언어가 달라도 뜻으로
    ("그냥 평범합니다", "중립", "보통입니다", True),
    ("그냥 평범합니다", "중립", "긍정", False),
]


def build_local():
    llm = ChatOllama(model=LOCAL_MODEL, temperature=0)
    return f"로컬 {LOCAL_MODEL}", judge_prompt | llm.with_structured_output(Judgement)


def build_openai():
    """🔶 상용 판정자. 키가 없으면 None 을 돌려 조용히 건너뛴다."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("[i] langchain-openai 가 없습니다 → pip install langchain-openai")
        return None
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    return f"상용 {OPENAI_MODEL}", judge_prompt | llm.with_structured_output(Judgement)


def run_judge(name, judge) -> list:
    """GOLD 전체를 채점시키고 (판정, 사람판정, 이유) 목록을 돌려준다."""
    print(f"\n▶ 판정자: {name}  — 예제 {len(GOLD)}건 채점 중...")
    rows = []
    for question, reference, answer, human in GOLD:
        try:
            j = judge.invoke({"question": question, "reference": reference, "answer": answer})
            rows.append((answer, reference, bool(j.is_correct), human, j.reason))
        except Exception as e:  # noqa: BLE001
            print(f"  [!] 실패: {e.__class__.__name__} — 오답 처리")
            rows.append((answer, reference, False, human, "(판정 실패)"))
    return rows


def report(name, rows) -> float:
    agree = sum(1 for _, _, verdict, human, _ in rows if verdict == human)
    rate = agree / len(rows)
    print(f"\n  [{name}] 사람 채점과의 일치율 : {agree}/{len(rows)} = {rate * 100:.0f}%")
    for answer, reference, verdict, human, reason in rows:
        mark = "  " if verdict == human else "⚠️"
        print(
            f"   {mark} 정답 {reference:<3} / 학생답 {answer:<22}"
            f" 판정 {'O' if verdict else 'X'}  사람 {'O' if human else 'X'}   {reason[:34]}"
        )
    return rate


def main() -> None:
    only_local = "local" in sys.argv[1:]

    print("=" * 78)
    print("  LLM-as-a-Judge — 판정자를 검증한다 ★★")
    print("=" * 78)
    print("""
왜 bool 로 강제하는가 (5주차 with_structured_output) ★
    판정 결과가 "네 맞는 것 같습니다" 같은 문장으로 오면 **집계를 할 수 없습니다.**
    is_correct: bool 로 강제해야 셀 수 있습니다.
""")

    judges = [build_local()]
    if not only_local:
        commercial = build_openai()
        if commercial:
            judges.append(commercial)
        else:
            print("[i] OPENAI_API_KEY 가 없어 상용 판정자는 건너뜁니다.")
            print("    (로컬 판정자만으로도 '판정자도 틀린다' 는 확인됩니다) 🔶")

    rates = {}
    for name, judge in judges:
        rates[name] = report(name, run_judge(name, judge))

    print("\n" + "=" * 78)
    for name, rate in rates.items():
        print(f"  {name:<22} 일치율 {rate * 100:5.0f}%")
    if len(rates) == 2:
        (n1, r1), (n2, r2) = rates.items()
        print(f"\n  ⚠️ 같은 답안인데 판정이 다릅니다. 차이 {abs(r1 - r2) * 100:.0f}%p")
        print(f"     {n1} 로 잰 A/B 결과와 {n2} 로 잰 A/B 결과는 **다른 숫자**가 됩니다.")
    print("=" * 78)
    print("""
무엇을 언제 쓰나 (2교시 2-3)

  과제                   권장 평가자        이유
  ────────────────────────────────────────────────────────────────────
  분류 (긍정/부정)       규칙 기반          답이 정해져 있다. 판정자를 쓸 이유가 없음
  추출 (날짜·금액)       규칙 기반 (+정규식) 형식 검증까지 가능
  형식 준수 여부         규칙 기반          5주차 파싱 실패율과 같은 발상
  요약 품질              LLM 판정자         규칙으로 표현 불가
  "같은 뜻인가"          LLM 판정자         의미 비교가 필요
  비용·시간이 빠듯할 때  규칙 기반 ★       판정자는 예제 수만큼 호출이 추가된다

💡 둘을 함께 쓰는 것이 실무 표준입니다.
   규칙 기반으로 **형식**을 보고, LLM 판정자로 **내용**을 봅니다.
   (5주차 "스키마는 형식을 보장하지만 내용은 보장하지 않는다" — 그 구분입니다) ★

⚠️ 오늘 실습 2·3 의 과제는 '분류' 입니다. 그래서 채점은 **규칙 기반(exact_match)** 을 씁니다.
   판정자는 "이런 게 있고, 이런 위험이 있다" 를 보기 위해 여기서만 돌립니다. ★

다음 단계 →  python ab_experiment.py
""")


if __name__ == "__main__":
    main()
