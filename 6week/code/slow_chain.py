"""[2교시 / 3절] ★ 병목이 '눈에 띄게' 설계된 예시 체인 — 교수 시연용

교수 준비물의 "한 단계가 유독 느린 예시 체인 1건" 이 이 파일입니다.
세 단계 중 ② 만 일부러 길게 쓰게 해 두었습니다. 추적 화면에서
② 가 압도적으로 오래 걸린 것이 한눈에 보여야 합니다.

   Run: 진단 파이프라인            (부모 — 항상 1등이다. 병목이 아니다 ⚠️)
    ├─ ① 요약      짧게       ~2초
    ├─ ② 상세 분석  아주 길게  ~12초   ★ 여기가 진짜 병목
    └─ ③ 한 줄 결론 짧게       ~2초

★★ 부모 Run 의 함정

    전체 시간 = 자기 + 자식 전부
    자기 시간 = 전체 시간 − 자식들의 시간   ← 병목은 이것이 큰 Run ★

    "부장님이 제일 오래 걸렸다고 하면 안 되죠. 팀 전체 시간이니까요.
     누가 실제로 오래 잡고 있었는지를 봐야 합니다."

진단 4단계
    ① 트리를 펼친다
    ② 잎(자식이 없는 Run)만 본다   ← 여기서 자기 시간 = 전체 시간 ★
    ③ 가장 큰 것을 고른다
    ④ 그 Run 의 입력·출력·토큰을 열어 '왜 오래 걸렸는지' 추정한다

실행:
    python slow_chain.py           # 1회 실행
    python slow_chain.py 2         # 2회 실행 — 워밍업 효과를 비교한다 ★
"""

import sys
import time

from dotenv import load_dotenv

load_dotenv()

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.runnables import RunnableLambda  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

MODEL = "gemma3:4b"

TOPIC = "한 카페의 오후 시간대 매출 감소"

llm = ChatOllama(model=MODEL, temperature=0)


def step(system: str, human: str):
    return ChatPromptTemplate.from_messages([("system", system), ("human", human)]) | llm | StrOutputParser()


# ── ① 짧게 ──────────────────────────────────────────────────────
summarize = step(
    "너는 요약 담당이다. 반드시 두 문장 이내로만 답한다.",
    "다음 상황을 요약해라: {topic}",
)

# ── ② 일부러 길게 ★ — 출력 토큰이 많으면 느려진다 ──────────────
analyze = step(
    "너는 분석 담당이다. 아주 상세하게, 최소 900자 이상으로 답한다. "
    "가능한 모든 원인을 빠짐없이 나열하고 각각을 길게 설명한다.",
    "다음 요약을 근거로 원인을 낱낱이 분석해라:\n{summary}",
)

# ── ③ 짧게 ──────────────────────────────────────────────────────
conclude = step(
    "너는 결론 담당이다. 반드시 한 문장으로만 답한다.",
    "다음 분석의 결론을 한 문장으로:\n{analysis}",
)


# ── 로컬에서도 단계별 시간을 재 둔다 ────────────────────────────
#    추적 화면의 값과 대조시키기 위한 것입니다.
#    (4주차에서 VRAM 계산값과 ollama ps 실측을 대조한 것과 같은 방식)
TIMES: dict[str, float] = {}


def timed(name: str, runnable):
    """단계 하나를 감싸 실행 시간을 재고, 트리에 표시될 이름도 지정한다."""

    def _run(data: dict) -> str:
        t0 = time.perf_counter()
        out = runnable.invoke(data)
        TIMES[name] = time.perf_counter() - t0
        return out

    return RunnableLambda(_run).with_config(run_name=name)


step1 = timed("① 요약", summarize)
step2 = timed("② 상세 분석", analyze)
step3 = timed("③ 한 줄 결론", conclude)


def pipeline(data: dict) -> dict:
    """세 단계를 순서대로 돈다 — 이 함수가 '부모 Run' 이 된다."""
    summary = step1.invoke({"topic": data["topic"]})
    analysis = step2.invoke({"summary": summary})
    verdict = step3.invoke({"analysis": analysis})
    return {"summary": summary, "analysis": analysis, "verdict": verdict}


chain = RunnableLambda(pipeline).with_config(run_name="진단 파이프라인")


def report(total: float) -> None:
    child = sum(TIMES.values())
    self_time = total - child

    print()
    print("  단계            시간(초)    비율     비고")
    print("  " + "─" * 62)
    print(f"  진단 파이프라인 {total:8.2f}   {100:5.1f}%   ← 부모. 항상 1등이다 (병목 아님) ⚠️")
    for name, sec in TIMES.items():
        mark = "  ★ 병목" if sec == max(TIMES.values()) else ""
        print(f"    {name:12s} {sec:8.2f}   {sec / total * 100:5.1f}%{mark}")
    print(f"    (부모 자기시간){self_time:8.2f}   {self_time / total * 100:5.1f}%   ← 부모가 '실제로' 쓴 시간 ★")
    print("  " + "─" * 62)


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    for i in range(1, runs + 1):
        TIMES.clear()
        print("=" * 66)
        print(f"  실행 {i}/{runs} — 주제: {TOPIC}")
        print("=" * 66)

        t0 = time.perf_counter()
        result = chain.invoke({"topic": TOPIC})
        total = time.perf_counter() - t0

        print(f"  [결론] {result['verdict']}")
        report(total)
        print()

    print("=" * 66)
    print("""
추적 화면에서 확인할 것 ★

  관찰                              읽는 법
  ──────────────────────────────────────────────────────────────────
  '진단 파이프라인' 이 제일 김      자식 전부를 감쌌으니 당연하다. 병목 아님 ⚠️
  ② 상세 분석 이 제일 김            잎 Run 중 1등 = 진짜 병목 ★
  ② 의 출력 토큰이 크다             느린 원인 = '답을 길게 쓰고 있음'
                                     → 처방: max_tokens · 프롬프트로 길이 제한

느린 원인 세 가지와 처방

  관찰                    원인                처방                     배운 곳
  ──────────────────────────────────────────────────────────────────────────
  출력 토큰이 많다        답이 길다           max_tokens / 길이 제한   4주차 3교시
  입력 토큰이 많다        누적된 컨텍스트     앞 결과를 요약해 넘김    5주차 3교시
  토큰은 적은데 느리다 ★  모델 로딩·CPU 분산  ollama ps 의 PROCESSOR   4주차 1교시 ★★

⚠️ 첫 실행이 유독 느렸다면 그건 모델 문제가 아니라 '워밍업' 입니다.
   python slow_chain.py 2  로 두 번 실행해 1회차와 2회차를 비교하십시오.
   추적 화면에서도 두 Trace 를 나란히 놓고 보게 하십시오. ★

⚠️ 지연 ≠ 비용. 토큰으로 정렬하면 1등이 달라질 수 있습니다.
   "어디를 고칠 것인가" 는 "무엇을 개선하려는가" 에 따라 답이 달라집니다.
""")
    print("=" * 66)


if __name__ == "__main__":
    main()
