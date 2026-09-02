"""[3교시 / 실습 3] 회귀 방지 — 프롬프트를 고치고, 같은 데이터셋으로 다시 잰다

  1교시에서 말한 문제 ③ 을 실제로 만들어 봅니다.

     [실험 A] CoT                  정확도 78%
          │
          │  "프롬프트에 '중립은 웬만하면 쓰지 마라' 를 추가하면
          │   애매한 케이스가 긍정/부정으로 잘 갈리지 않을까?"
          ▼
     [실험 C] CoT + 프롬프트 수정   정확도 ??%

  ⚠️ 바뀐 것은 system 한 줄뿐입니다. ★
     그런데 그 한 줄이 **안 본 케이스**를 망가뜨릴 수 있습니다.

  확인해야 할 것                    왜
  ──────────────────────────────────────────────────────
  전체 정확도가 올랐는가             개선 여부
  **어떤 예제가 새로 틀렸는가** ★★  회귀 — 이게 진짜 목적
  어떤 예제가 새로 맞았는가          개선의 실체

  ★ metadata 에 "무엇을 바꿨는지" 를 반드시 남기십시오.
    실험이 10개쯤 쌓이면 'cot-v2' 라는 이름만으로는 뭘 바꿨는지 아무도 기억 못 합니다.
    (6주차 "설정값을 함께 기록해야 재현이 된다" 와 같은 이야기)

실행:
    python regression.py
    python regression.py --diff       # ★ v1 과 v2 를 예제별로 대조해 회귀를 찾는다
"""

import sys
import time
from typing import Literal

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import metrics  # noqa: E402
from evaluators import accuracy_of, exact_match, run_evaluate  # noqa: E402

MODEL = "gemma3:4b"
DATASET_NAME = "week07-review-sentiment"
EXPERIMENT_PREFIX = "cot-v2"
CHANGE = "중립 억제 문장 추가"  # ★ 무엇을 바꿨는지
MAX_CONCURRENCY = 1


class Result(BaseModel):
    """★ ab_experiment.py 와 **완전히 같은 스키마**여야 합니다.
    비교하려면 바뀐 것이 프롬프트 한 줄뿐이어야 합니다.
    """

    reasoning: str = Field(description="단계별 판단 근거")
    label: Literal["긍정", "부정", "중립"] = Field(description="세 가지 중 하나")


# ── ⚠️ 바뀐 것은 system 한 줄뿐입니다 ★ ────────────────────────
prompt_v2 = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "리뷰의 감정을 분류한다. 단계적으로 생각한 뒤 라벨을 정하라. "
            "중립은 정말 판단이 불가능할 때만 쓴다.",  # ← 추가한 문장
        ),
        ("human", "{review}"),
    ]
)

chain_v2 = metrics.build_chain(prompt_v2, ChatOllama(model=MODEL, temperature=0), Result)
meter = metrics.Meter(EXPERIMENT_PREFIX)


def target_v2(inputs: dict) -> dict:
    t0 = time.perf_counter()
    try:
        parsed, tin, tout = metrics.split(chain_v2.invoke({"review": inputs["review"]}))
        label = metrics.label_of(parsed)
        usages, failed = [(tin, tout)], not label
    except Exception as e:  # noqa: BLE001
        print(f"  [!] 실패: {e.__class__.__name__}")
        label, usages, failed = "", [(None, None)], True

    elapsed = time.perf_counter() - t0
    meter.record(elapsed, usages, failed=failed)
    return {"label": label, "latency_s": round(elapsed, 2), "llm_calls": 1}


def show_diff() -> None:
    """★ v1(cot) 과 v2(cot-v2) 를 예제별로 대조해 **회귀**를 찾는다.

    🔶 실험 결과를 코드로 읽는 API 는 버전차가 있습니다. 실패하면 웹에서 보십시오
       (Datasets & Testing → 데이터셋 → 두 실험을 선택 → 예제별 비교 화면).
    """
    from langsmith import Client

    client = Client()

    projects = list(client.list_projects(reference_dataset_name=DATASET_NAME))

    def latest(match):
        found = [p for p in projects if match(p.name)]
        return max(found, key=lambda p: p.start_time) if found else None

    # ⚠️ "cot-" 은 "cot-v2-..." 도 잡습니다. v2 를 명시적으로 제외합니다.
    v1 = latest(lambda n: n.startswith("cot-") and not n.startswith(EXPERIMENT_PREFIX))
    v2 = latest(lambda n: n.startswith(EXPERIMENT_PREFIX))

    if not v1 or not v2:
        print("[!] 비교할 실험을 찾지 못했습니다. ab_experiment.py 를 먼저 돌리십시오.")
        print("    (또는 웹 비교 화면에서 직접 보십시오 — 그게 원래 방식입니다) ★")
        return

    def review_of(payload: dict) -> str:
        """루트 Run 의 입력에서 review 를 꺼낸다. 🔶 감싸는 형태가 버전마다 다르다."""
        payload = payload or {}
        if "review" in payload:
            return str(payload["review"])
        inner = payload.get("inputs")
        return str(inner.get("review", "")) if isinstance(inner, dict) else str(payload)

    def collect(project):
        return {
            review_of(r.inputs): (r.outputs or {}).get("label", "")
            for r in client.list_runs(project_name=project.name, is_root=True)
        }

    def refs():
        return {
            (e.inputs or {}).get("review", ""): (e.outputs or {}).get("label", "")
            for e in client.list_examples(dataset_name=DATASET_NAME)
        }

    a, b, gold = collect(v1), collect(v2), refs()

    print("=" * 78)
    print(f"  예제별 대조 :  {v1.name}  vs  {v2.name}")
    print("=" * 78)
    print(f"  {'예제':<28}{'정답':<6}{'v1':<8}{'v2':<8}판정")
    print("-" * 78)

    tally = {"유지": 0, "개선": 0, "회귀": 0, "둘다오답": 0}
    for review, want in gold.items():
        if review not in a or review not in b:
            continue
        ok1, ok2 = a[review].strip() == want, b[review].strip() == want
        verdict = (
            "유지 " if ok1 and ok2 else "개선 ★" if ok2 else "회귀 ⚠️★★" if ok1 else "둘다오답"
        )
        tally["유지" if ok1 and ok2 else "개선" if ok2 else "회귀" if ok1 else "둘다오답"] += 1
        shown = (review or "(빈 입력)")[:26]
        print(f"  {shown:<28}{want:<6}{a[review][:6]:<8}{b[review][:6]:<8}{verdict}")

    print("-" * 78)
    print(f"  유지 {tally['유지']} / 개선 {tally['개선']} / ⚠️ 회귀 {tally['회귀']} / 둘다오답 {tally['둘다오답']}")
    print("=" * 78)


def main() -> None:
    if "--diff" in sys.argv:
        show_diff()
        return

    print("=" * 72)
    print("  실습 3 — 회귀 방지 재평가")
    print(f"  바꾼 것: {CHANGE}   (system 한 줄)")
    print("=" * 72)

    results = run_evaluate(
        target_v2,
        data=DATASET_NAME,  # ★ 같은 데이터셋 — 이게 핵심
        evaluators=[exact_match],
        experiment_prefix=EXPERIMENT_PREFIX,
        metadata={  # ★ 무엇을 바꿨는지 기록
            "variant": "cot",
            "version": "v2",
            "change": CHANGE,
            "model": MODEL,
            "temperature": 0,
        },
        max_concurrency=MAX_CONCURRENCY,
    )

    acc = accuracy_of(results)
    print(
        f"\n[{EXPERIMENT_PREFIX}] 완료 — {meter.examples}건 / {meter.seconds:.1f}초 / "
        f"토큰 {meter.tokens_text} / 정확도 "
        f"{f'{acc * 100:.1f}%' if acc is not None else '웹에서 확인'}"
    )
    print("=" * 72)
    print("""
비교 화면에서 회귀 찾기 (3교시 1-3) ★★

    예제        v1      v2      판정
    ────────────────────────────────────────
    #1 배송..    ✅      ✅      유지
    #3 나쁘지..  ❌      ✅      개선 ★
    #7 그냥..    ✅      ❌      회귀 ⚠️★★   ← 이걸 찾는 게 목적
    #9 가격은..  ❌      ✅      개선
    ────────────────────────────────────────
    전체        78%  →  84%

⚠️⚠️ 전체 정확도만 보면 #7 을 놓칩니다. 78% → 84% 면 "성공" 으로 보입니다.
     그런데 **원래 잘 되던 케이스 하나가 망가졌습니다.**
     그 케이스가 서비스에서 가장 흔한 입력이라면?
     **전체 수치는 올랐는데 사용자 만족은 떨어집니다.**

  결과                        조치
  ──────────────────────────────────────────────────────────────
  개선만 있고 회귀 없음        채택
  개선 > 회귀, 회귀가 사소함   채택 + 회귀 케이스를 데이터셋에 명시
  개선 < 회귀                  되돌린다
  회귀 케이스가 중요한 입력 ★  수치가 올라도 재검토

📌 이것이 "회귀 테스트" 입니다. 코드를 고칠 때마다 테스트를 돌리는 것과 정확히 같습니다.
   차이는 테스트가 통과/실패가 아니라 **'점수'** 라는 것뿐입니다.

💡 실무 루틴
   프롬프트 수정 → 같은 데이터셋 재평가 → 회귀 확인 → 새 실패는 데이터셋에 추가 → 반복
   데이터셋은 **쓸수록 강해집니다.**

지금 확인 →  웹 비교 화면  (또는  python regression.py --diff)
다음 단계 →  python quota_calc.py
""")


if __name__ == "__main__":
    main()
