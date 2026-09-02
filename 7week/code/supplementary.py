"""[2교시 / 3-4] 보충 실습 — Zero-shot · Few-shot · Step-Back (실행은 수업 후 · 무배점)

  수업 중에는 실험군 2개(CoT / Self-Consistency)만 돌립니다.
  25분 안에 4~5개를 돌리면 **어느 것도 제대로 끝나지 않습니다.**
  나머지는 여기서 **설계만** 함께 잡고, 실행·집계는 각자 수행합니다.

  실험군      프롬프트                    예상되는 특징
  ─────────────────────────────────────────────────────────────
  Zero-shot   지시만                      가장 싸고 빠름. 기준선(baseline)
  Few-shot    예시 3~5개 첨부             형식 준수↑, 입력 토큰↑
  Step-Back ★ 한 발 물러선 질문을 먼저    선수과목 미학습 기법

★ Step-Back Prompting — 오늘 처음 보는 기법

     원 질문: "2023년 A사 B제품 출시일에 경쟁사는 무엇을 했나?"
          │
          │  ① 한 발 물러선 질문을 먼저 만든다
          │     → "A사 B제품은 언제 출시되었나?"
          │  ② 그 답(일반적·상위 사실)을 근거로
          │  ③ 원 질문에 답한다
          ▼
     구체적 질문에 바로 답하면 틀리기 쉬운 문제를, 상위 사실부터 확보해 푼다

  ★ 구조적으로는 5주차 Least-to-Most 의 사촌입니다 — 둘 다 **직렬 분해**.
    차이는 "쉬운 것부터 순서대로"(Least-to-Most) vs
           "한 단계 추상화된 질문 먼저"(Step-Back).

  ⚠️ Step-Back 은 중간고사에 출제하지 않습니다 (수행 여부가 학생마다 다르므로).
     결과는 개인 LangSmith 프로젝트에 남겨 **시험 대비 자료**로 쓰십시오.

  ⚠️ Step-Back 은 예제당 LLM 호출이 **2회**입니다. traces 도 2배입니다.

실행:
    python supplementary.py                    # 세 실험군 모두 (수업 후에)
    python supplementary.py zeroshot
    python supplementary.py fewshot
    python supplementary.py stepback
"""

import sys
import time
from typing import Literal

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import metrics  # noqa: E402
from evaluators import accuracy_of, exact_match, run_evaluate  # noqa: E402

MODEL = "gemma3:4b"
DATASET_NAME = "week07-review-sentiment"
MAX_CONCURRENCY = 1


class Label(BaseModel):
    """Zero-shot·Few-shot 은 근거를 요구하지 않는다 — 그래서 출력 토큰이 적다. ★

    ★ label 은 Literal 로 못 박습니다. str + description 은 '부탁' 이라
      실제로 'mixed_sentiment' 같은 값이 나옵니다 (ab_experiment.py 주석 참고).
    """

    label: Literal["긍정", "부정", "중립"] = Field(description="세 가지 중 하나")


llm = ChatOllama(model=MODEL, temperature=0)

# ── ① Zero-shot — 지시만. 기준선(baseline) ────────────────────
zeroshot_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "리뷰의 감정을 긍정/부정/중립 중 하나로 분류한다."),
        ("human", "{review}"),
    ]
)

# ── ② Few-shot — 예시를 붙인다 (5주차 few_shot.py) ────────────
#     ⚠️ 데이터셋에 들어 있는 예제를 예시로 쓰면 안 됩니다 — 답을 알려주고 채점하는 꼴 ★★
FEWSHOT_EXAMPLES = [
    ("포장이 꼼꼼해서 좋았습니다", "긍정"),
    ("설명과 다른 물건이 왔어요", "부정"),
    ("어제 수령했습니다", "중립"),
    ("싸지는 않지만 만족합니다", "긍정"),
]

fewshot_prompt = ChatPromptTemplate.from_messages(
    [("system", "리뷰의 감정을 긍정/부정/중립 중 하나로 분류한다.")]
    + [m for review, label in FEWSHOT_EXAMPLES for m in (("human", review), ("ai", label))]
    + [("human", "{review}")]
)

# ── ③ Step-Back — 상위 질문을 먼저 ★ ─────────────────────────
stepback_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 리뷰 분석가다. 감정 라벨은 아직 정하지 마라. "
            "이 리뷰가 무엇에 대해(배송·품질·가격·서비스 등) 어떤 태도를 보이는지 "
            "한 발 물러서서 두 문장으로만 정리하라.",
        ),
        ("human", "{review}"),
    ]
)

final_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "아래 분석을 근거로 리뷰의 감정을 긍정/부정/중립 중 하나로 분류한다. "
            "장점과 단점이 함께 있으면 마지막 절의 인상을 따른다.",
        ),
        ("human", "리뷰: {review}\n\n분석: {analysis}\n\n라벨은?"),
    ]
)

chain_zeroshot = metrics.build_chain(zeroshot_prompt, llm, Label)
chain_fewshot = metrics.build_chain(fewshot_prompt, llm, Label)
chain_stepback_1 = stepback_prompt | llm | StrOutputParser()  # ① 상위 질문
chain_stepback_2 = metrics.build_chain(final_prompt, llm, Label)  # ③ 원 질문


def _simple_target(chain, meter):
    def target(inputs: dict) -> dict:
        t0 = time.perf_counter()
        try:
            parsed, tin, tout = metrics.split(chain.invoke({"review": inputs["review"]}))
            label, usages = metrics.label_of(parsed), [(tin, tout)]
        except Exception as e:  # noqa: BLE001
            print(f"  [!] 실패: {e.__class__.__name__}")
            label, usages = "", [(None, None)]
        elapsed = time.perf_counter() - t0
        meter.record(elapsed, usages, failed=not label)
        return {"label": label, "latency_s": round(elapsed, 2), "llm_calls": 1}

    return target


meters = {
    "zeroshot": metrics.Meter("zeroshot"),
    "fewshot": metrics.Meter("fewshot"),
    "stepback": metrics.Meter("stepback"),
}


def target_stepback(inputs: dict) -> dict:
    """★ 예제당 LLM 호출 2회 — ① 상위 분석 → ② 그 답을 근거로 라벨."""
    meter = meters["stepback"]
    t0 = time.perf_counter()
    try:
        analysis = chain_stepback_1.invoke({"review": inputs["review"]})
        parsed, tin, tout = metrics.split(
            chain_stepback_2.invoke({"review": inputs["review"], "analysis": analysis})
        )
        label = metrics.label_of(parsed)
        usages = [(None, None), (tin, tout)]  # ① 은 StrOutputParser 라 토큰이 안 잡힌다 🔶
    except Exception as e:  # noqa: BLE001
        print(f"  [!] 실패: {e.__class__.__name__}")
        analysis, label, usages = "", "", [(None, None), (None, None)]

    elapsed = time.perf_counter() - t0
    meter.record(elapsed, usages, failed=not label)
    return {
        "label": label,
        "analysis": analysis[:200],  # ★ 중간 산출물을 남겨 두면 웹에서 근거를 볼 수 있다
        "latency_s": round(elapsed, 2),
        "llm_calls": 2,
    }


VARIANTS = {
    "zeroshot": (
        lambda: _simple_target(chain_zeroshot, meters["zeroshot"]),
        {"variant": "zeroshot", "n": 1, "note": "기준선"},
    ),
    "fewshot": (
        lambda: _simple_target(chain_fewshot, meters["fewshot"]),
        {"variant": "fewshot", "n": 1, "shots": len(FEWSHOT_EXAMPLES)},
    ),
    "stepback": (
        lambda: target_stepback,
        {"variant": "stepback", "n": 1, "llm_calls_per_example": 2},
    ),
}


def main() -> None:
    picked = [a for a in sys.argv[1:] if a in VARIANTS] or list(VARIANTS)

    print("=" * 72)
    print("  보충 실습 — 수업 후에 각자 실행합니다 (무배점)")
    print(f"  실험군: {', '.join(picked)}   데이터셋: {DATASET_NAME}")
    print("=" * 72)

    for key in picked:
        make_target, meta = VARIANTS[key]
        meter = meters[key]
        print(f"\n▶ 실험 [{key}] 시작")
        results = run_evaluate(
            make_target(),
            data=DATASET_NAME,
            evaluators=[exact_match],
            experiment_prefix=key,
            metadata=dict(meta, model=MODEL, supplementary=True),
            max_concurrency=MAX_CONCURRENCY,
        )
        acc = accuracy_of(results)
        print(
            f"  [{key}] {meter.examples}건 / {meter.seconds:.1f}초 / "
            f"토큰 {meter.tokens_text} / 정확도 "
            f"{f'{acc * 100:.1f}%' if acc is not None else '웹에서 확인'}"
        )

    print("\n" + "=" * 72)
    print("""
정리할 것 — RESULTS.md 의 보충 실습 표에 채우십시오

  실험군            정확도   토큰    지연    호출/예제
  ──────────────────────────────────────────────────────
  zeroshot          ___%     ___     ___초   1        ← 기준선
  fewshot           ___%     ___     ___초   1
  CoT               ___%     ___     ___초   1
  Self-Consistency  ___%     ___     ___초   5
  Step-Back ★       ___%     ___     ___초   2

★ 물어야 할 것
  · Few-shot 은 입력 토큰이 얼마나 늘었는가? 그만큼 값을 했는가?
  · Step-Back 은 CoT 보다 나은가? 호출이 2배인데도?
  · **"정확도가 올랐다" 가 아니라 "무엇을 얼마에 샀는가"** — 매번 같은 질문입니다. ★★

⚠️ Few-shot 예시에 **데이터셋 예제를 쓰지 마십시오.** 답을 알려주고 채점하는 꼴이 됩니다.
   (시험 문제를 미리 보여주고 시험을 치는 것과 같습니다) ★★
""")


if __name__ == "__main__":
    main()
