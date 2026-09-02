"""[2교시 / 실습 2] ★★ CoT vs Self-Consistency — 같은 데이터셋에 걸어 3축으로 비교한다

  선수과목에서 "CoT 가 낫다" 의 근거는 **논문 인용** 이었습니다.
  그런데 그 논문의 과제와 내 과제는 다릅니다. 모델도 다릅니다.
  **내 과제에서도 CoT 가 나은지는 재봐야 압니다.** — 그걸 오늘 잽니다.

     같은 데이터셋 (1교시에 만든 16건)
          │
          ├──▶ 실험 A : CoT              — 단계적으로 생각한 뒤 1회 답변
          │
          └──▶ 실험 B : Self-Consistency — CoT 를 N회 샘플링 후 다수결 (5주차 실습 4)
                                              │
                                              ▼
                          비교축 3개:  정확도 · 토큰 · 지연시간   ★★

  ⚠️ 정확도만 보면 안 됩니다. Self-Consistency 는 호출이 N배입니다.
     정확도가 조금 오른 대가로 비용과 시간이 몇 배가 됩니다.
     **"그래서 쓸 것인가"** 를 판단하는 것이 오늘의 목표입니다.

  ⏱ 실행에 시간이 걸립니다. 예제 16개 × (1회 + 5회) = 96회 호출입니다.
     ★ 먼저 실행을 걸어 두고, 도는 동안 3-3의 해석 틀을 설명하십시오.

  🔶 evaluate() 의 시그니처는 langsmith 버전에 따라 다릅니다.
     수업 전날 반드시 python check_eval_api.py 로 확인하십시오.
     여기서 막히면 25분 실습이 통째로 멈춥니다 — 이 교시 최대의 위험 지점입니다. ★

실행:
    python ab_experiment.py            # 실험 A, B 둘 다
    python ab_experiment.py cot        # A 만
    python ab_experiment.py sc         # B 만
"""

import sys
import time
from collections import Counter
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

N = 5  # Self-Consistency 샘플 수 ⚠️ traces 가 N배로 늘어난다
TEMP_SC = 0.8  # ★ 0 이면 5번 다 같은 답 → 다수결이 무의미
MAX_CONCURRENCY = 1  # ⚠️ 8GB VRAM 실습실 보호. 여유가 있으면 2 🔶
BATCH_CONCURRENCY = 2  # batch 내부 동시 실행 수


class Result(BaseModel):
    """분류 결과 — reasoning 을 먼저 쓰게 해야 CoT 가 된다. ★

    ⚠️ label 을 그냥 str 로 두면 안 됩니다. 실제로 확인된 것: ★★
          label: str = Field(description="긍정/부정/중립 중 하나만")
          → gemma3:4b 가 'mixed_sentiment' 라고 답합니다.

       description 은 **부탁**입니다. Literal 은 **계약**입니다.
       Literal 로 두면 스키마에 enum 이 박혀 세 값 외에는 나올 수 없습니다.
       (5주차 "'JSON으로 답해줘' vs with_structured_output()" — 같은 구분입니다) ★
    """

    reasoning: str = Field(description="단계별 판단 근거")
    label: Literal["긍정", "부정", "중립"] = Field(description="세 가지 중 하나")


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "리뷰의 감정을 분류한다. 단계적으로 생각한 뒤 라벨을 정하라."),
        ("human", "{review}"),
    ]
)

# ── 실험 A : CoT 1회 ──────────────────────────────────────────
chain_cot = metrics.build_chain(prompt, ChatOllama(model=MODEL, temperature=0), Result)
meter_cot = metrics.Meter("cot")

# ── 실험 B : Self-Consistency (N회 다수결) ★ ──────────────────
chain_sc = metrics.build_chain(prompt, ChatOllama(model=MODEL, temperature=TEMP_SC), Result)
meter_sc = metrics.Meter("self-consistency")


def target_cot(inputs: dict) -> dict:
    t0 = time.perf_counter()
    failed = False
    try:
        parsed, tin, tout = metrics.split(chain_cot.invoke({"review": inputs["review"]}))
        label = metrics.label_of(parsed)
        failed = not label
        usages = [(tin, tout)]
    except Exception as e:  # noqa: BLE001 — 빈 입력 등에서 깨질 수 있다. 오답으로 센다 ★
        print(f"  [!] cot 실패: {e.__class__.__name__}")
        label, usages, failed = "", [(None, None)], True

    elapsed = time.perf_counter() - t0
    meter_cot.record(elapsed, usages, failed=failed)
    # ★ 토큰·지연을 출력에 함께 실어 두면 웹 비교 화면에서도 보입니다.
    return {"label": label, "latency_s": round(elapsed, 2), "llm_calls": 1}


def target_sc(inputs: dict) -> dict:
    """★ 같은 입력을 N개 만들어 batch 로 넘긴다 — 이 한 줄이 Self-Consistency 의 구현이다."""
    t0 = time.perf_counter()
    rs = chain_sc.batch(
        [{"review": inputs["review"]}] * N,
        config={"max_concurrency": BATCH_CONCURRENCY},
        return_exceptions=True,  # ★ 일부가 실패해도 멈추지 않는다
    )

    labels, usages = [], []
    for r in rs:
        if isinstance(r, Exception):
            usages.append((None, None))
            continue
        parsed, tin, tout = metrics.split(r)
        usages.append((tin, tout))
        label = metrics.label_of(parsed)
        if label:
            labels.append(label)

    elapsed = time.perf_counter() - t0
    votes = Counter(labels)
    final = votes.most_common(1)[0][0] if labels else ""  # 전부 실패 → 오답 처리
    meter_sc.record(elapsed, usages, failed=not labels)

    return {
        "label": final,
        "votes": dict(votes),  # ★ 표 분포가 웹에 남는다 — 3:2 로 갈렸는지 볼 수 있다
        "latency_s": round(elapsed, 2),
        "llm_calls": N,
    }


EXPERIMENTS = {
    "cot": (target_cot, meter_cot, {"variant": "cot", "n": 1, "temperature": 0}),
    "sc": (target_sc, meter_sc, {"variant": "self-consistency", "n": N, "temperature": TEMP_SC}),
}


def main() -> None:
    picked = [a for a in sys.argv[1:] if a in EXPERIMENTS] or ["cot", "sc"]

    print("=" * 72)
    print("  실습 2 — 기법 A/B 실측 (CoT vs Self-Consistency)")
    print(f"  모델={MODEL}  데이터셋={DATASET_NAME}  N={N}  temp(SC)={TEMP_SC}")
    print("=" * 72)

    accuracy = {}
    for key in picked:
        target, meter, meta = EXPERIMENTS[key]
        meta = dict(meta, model=MODEL, dataset=DATASET_NAME)  # ★ 설정값을 함께 기록해야 재현이 된다
        print(f"\n▶ 실험 [{meter.name}] 시작 — 오래 걸립니다. 기다리는 동안 3-3 을 읽으십시오.")

        results = run_evaluate(
            target,
            data=DATASET_NAME,
            evaluators=[exact_match],
            experiment_prefix=meter.name,  # ★ 실험 구분 (6주차 태그의 연장)
            metadata=meta,
            max_concurrency=MAX_CONCURRENCY,
        )

        acc = accuracy_of(results)
        if acc is not None:
            accuracy[meter.name] = acc
        print(
            f"  [{meter.name}] 완료 — {meter.examples}건 / "
            f"{meter.seconds:.1f}초 / LLM 호출 {meter.llm_calls}회 / "
            f"정확도 {f'{acc * 100:.1f}%' if acc is not None else '웹에서 확인'}"
        )

    if len(picked) == 2:
        print(metrics.comparison_table([meter_cot, meter_sc], accuracy))

    print("=" * 72)
    print(f"""
결과 읽기 — 웹에서 나란히 봅니다 (2교시 3-3) ★★

    Datasets & Testing → {DATASET_NAME} → 실험 목록에서 두 실험을 **선택**
      → 예제별 비교 화면이 나옵니다. 어느 예제에서 갈렸는지 그 자리에서 보입니다.

해석 연습 — 이 표를 보고 무엇을 결정합니까? ★

    가정:  정확도 78% → 86% (+8%p) / 토큰 3배 / 지연 2.5배 / 비용 5배

      상황                    판단     근거
      ─────────────────────────────────────────────────────────────
      의료·법률 판단 보조     채택     틀리면 피해가 크다. 비용은 부차적
      실시간 채팅 응답        기각     지연 2.5배는 사용자가 못 기다린다 ★
      하루 100만 건 배치      기각     비용 5배가 감당 불가
      하루 100건 내부 도구    채택     비용 절대액이 작다

    📌 **"정확도가 올랐다" 는 채택의 근거가 아닙니다.
       "무엇을 얼마에 샀는가" 를 봐야 합니다.** ★★
       4주차 모델 비교표의 "공짜는 없다" 와 같은 구조입니다.
       그때는 모델 선택, 오늘은 **기법 선택** 입니다.

⚠️ 두 실험의 정확도가 똑같이 나온다면
   데이터셋이 너무 쉬운 것입니다. 둘 다 100%면 비교가 안 됩니다.
   examples.py 에 **엣지 케이스를 더 넣으십시오.** 실패가 나와야 측정이 됩니다. ★

다음 단계 →  RESULTS.md 를 채운다  →  python regression.py
""")


if __name__ == "__main__":
    main()
