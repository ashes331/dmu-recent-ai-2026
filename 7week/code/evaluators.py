"""[2교시 / 1절] 규칙 기반 평가자 — 코드로 채점 기준을 고정한다

  기대 정답이 "긍정" 인데 모델이 이렇게 답했습니다. 맞습니까?

     ① "긍정"                   → ✅ 명백히 맞음
     ② "긍정입니다"             → ???
     ③ "  긍정  "               → ???  (공백)
     ④ "이 리뷰는 긍정적입니다"  → ???
     ⑤ "약간 긍정"              → ???
     ⑥ "positive"              → ???

  ⚠️ 채점 기준을 먼저 정하지 않으면 매번 다른 점수가 나옵니다.

  ┌ 평가자 ──┬ 잡아내는 것 ─────┬ 놓치는 것 ───────────────────────┐
  │ 정확 일치 │ 형식까지 완벽한가 │ "긍정입니다" 를 오답 처리 ⚠️      │
  │ 포함      │ 군더더기 허용     │ "긍정이 아닙니다" 를 정답 처리 ⚠️★│
  │ 정규식    │ 형식 준수 여부    │ 내용의 옳고 그름은 못 봄          │
  └──────────┴──────────────────┴──────────────────────────────────┘

★ 이 절의 결론 한 문장: **평가자도 검증 대상입니다.**
  평가자 자체에 버그가 있으면 그 위에서 잰 측정 결과 전체가 무의미해집니다.

🔶 버전 주의: langsmith 의 평가자 시그니처는 두 가지가 있습니다.
      신형: def f(outputs: dict, reference_outputs: dict)     ← 이 파일의 기본형
      구형: def f(run, example)
   구형 환경이면 아래 as_legacy() 로 감싸서 넘기십시오.
   어느 쪽인지는 python check_eval_api.py 가 알려 줍니다. ★

실행:
    python evaluators.py        # LLM 호출 없음 · 비용 0원 · 즉시 실행 ★
"""

import re

from metrics import pad  # 표시 폭(한글=2)을 맞춰 표를 그리는 잡일 함수

VALID = r"(긍정|부정|중립)"


# ── ① 정확 일치 — 가장 엄격 ───────────────────────────────────
def exact_match(outputs: dict, reference_outputs: dict) -> bool:
    """모델 출력이 정답과 정확히 같은가."""
    return str(outputs.get("label", "")).strip() == str(reference_outputs.get("label", "")).strip()


# ── ② 포함 — 앞뒤 군더더기를 허용 ★ ───────────────────────────
def contains(outputs: dict, reference_outputs: dict) -> bool:
    """정답 문자열이 출력 안에 들어 있는가.  ⚠️ 함정이 있다 — 아래 시연 참고."""
    return str(reference_outputs.get("label", "")).strip() in str(outputs.get("label", ""))


# ── ③ 정규식 — 형식을 검사 ────────────────────────────────────
def is_valid_label(outputs: dict, reference_outputs: dict) -> bool:
    """세 라벨 중 하나만 나왔는가 (형식 준수 여부. 정답 여부와 무관) ★"""
    return bool(re.fullmatch(VALID, str(outputs.get("label", "")).strip()))


# ── 참고: 실무에서 흔히 쓰는 절충안 ───────────────────────────
def normalized_match(outputs: dict, reference_outputs: dict) -> bool:
    """군더더기는 허용하되 부정 표현은 걸러낸다 — contains 의 함정을 막은 형태.

    ★ 완벽한 규칙은 없습니다. '어디까지 봐줄 것인가' 를 정하는 것이 채점 기준입니다.
    """
    got = str(outputs.get("label", "")).strip()
    want = str(reference_outputs.get("label", "")).strip()
    found = re.findall(VALID, got)
    if len(found) != 1 or found[0] != want:
        return False
    # ⚠️ 한국어 활용형 주의 — "아니" 는 "아닙니다" 의 부분 문자열이 아닙니다.
    #    (아/닙/니/다) 이므로 "아닙" 을 따로 넣어야 잡힙니다. 규칙을 정교하게
    #    짜기 어렵다는 것이 바로 이런 것입니다. ★
    return not re.search(r"(아니|아닙|아님|아냐|않|없|말고|반대)", got)


ALL = [exact_match, contains, is_valid_label, normalized_match]


# ── 🔶 구형 시그니처용 어댑터 ─────────────────────────────────
def as_legacy(fn):
    """(outputs, reference_outputs) 평가자를 구형 (run, example) 형태로 감싼다."""

    def wrapper(run, example):
        score = bool(fn(run.outputs or {}, example.outputs or {}))
        return {"key": fn.__name__, "score": score}

    wrapper.__name__ = fn.__name__
    return wrapper


def _load_evaluate():
    """🔶 evaluate 의 import 경로도 버전에 따라 다릅니다."""
    try:
        from langsmith import evaluate
    except ImportError:  # 구버전
        from langsmith.evaluation import evaluate
    return evaluate


def run_evaluate(target, *, data, evaluators, experiment_prefix, metadata=None, max_concurrency=1):
    """evaluate() 를 부른다. 평가자 시그니처가 안 맞으면 구형으로 한 번 더 시도한다. 🔶

    ⚠️ 이 차시 최대의 위험 지점입니다. 여기서 막히면 25분 실습이 통째로 멈춥니다.
       수업 전날 check_eval_api.py 로 반드시 확인하십시오. ★
    """
    evaluate = _load_evaluate()
    kwargs = dict(
        data=data,
        experiment_prefix=experiment_prefix,
        metadata=metadata or {},
        max_concurrency=max_concurrency,  # ⚠️ 8GB VRAM 실습실 보호 — 1~2 로 제한
    )
    try:
        return evaluate(target, evaluators=evaluators, **kwargs)
    except TypeError as e:
        print(f"[!] 신형 평가자 시그니처 실패 ({e}) → 구형 (run, example) 으로 재시도 🔶")
        return evaluate(target, evaluators=[as_legacy(f) for f in evaluators], **kwargs)


def accuracy_of(results, key: str = "exact_match"):
    """실험 결과에서 평균 점수를 뽑는다. 🔶 못 뽑으면 None (웹에서 읽으면 된다)."""
    try:
        scores = []
        for row in results:
            evs = (row.get("evaluation_results") or {}).get("results") or []
            for e in evs:
                if getattr(e, "key", None) == key and getattr(e, "score", None) is not None:
                    scores.append(float(e.score))
        return sum(scores) / len(scores) if scores else None
    except Exception:  # noqa: BLE001 — 버전 차이는 치명적이지 않다. 웹에서 보면 된다.
        return None


# ── 시연 — 평가자를 평가한다 ★★ ──────────────────────────────
#   (모델 출력, 기대 정답, 사람이 보기에 맞는가)
CASES = [
    ("긍정", "긍정", True),
    ("긍정입니다", "긍정", True),
    ("  긍정  ", "긍정", True),
    ("이 리뷰는 긍정적입니다", "긍정", True),
    ("positive", "긍정", True),
    ("긍정이 아닙니다", "긍정", False),  # ★★ contains 의 함정
    ("부정", "긍정", False),
    ("애매하지만 굳이 고르면 긍정", "긍정", True),
    ("", "중립", False),  # 빈 출력 (호출 실패)
]


def main() -> None:
    print("=" * 78)
    print("  규칙 기반 평가자 3종 — 같은 답안을 서로 다르게 채점한다")
    print("=" * 78)
    header = ["모델 출력", "정답", "사람", "정확일치", "포함", "정규식", "정규화"]
    widths = [32, 6, 6, 10, 8, 8, 8]
    print("".join(pad(h, w) for h, w in zip(header, widths)))
    print("-" * 78)

    wrong = {fn.__name__: 0 for fn in ALL}
    for got, want, human in CASES:
        o, r = {"label": got}, {"label": want}
        marks = []
        for fn in ALL:
            v = fn(o, r)
            if v != human:
                wrong[fn.__name__] += 1
            marks.append("O" if v else "X")
        cells = [f'"{got}"', want, "O" if human else "X", *marks]
        print("".join(pad(c, w) for c, w in zip(cells, widths)))

    print("-" * 78)
    n = len(CASES)
    for fn in ALL:
        w = wrong[fn.__name__]
        print(f"  {fn.__name__:<18} 사람 판정과 불일치 {w}/{n}건")
    print("=" * 78)
    print("""
읽어낼 것 ★★

  ① "긍정입니다" 를 exact_match 는 오답으로 셉니다.
     모델은 맞혔는데 평가자가 틀렸다고 셉니다 → 정확도가 실제보다 낮게 나옵니다.

  ② "긍정이 아닙니다" 를 contains 는 정답으로 셉니다.  ⚠️★
     "긍정이 아닙니다" 안에 "긍정" 이 들어 있기 때문입니다.
     모델은 틀렸는데 평가자가 맞았다고 셉니다 → 정확도가 실제보다 높게 나옵니다.

  ③ is_valid_label 은 형식만 봅니다. "부정" 도 형식은 통과합니다.
     형식 검사와 정답 검사는 다른 축입니다 (5주차: 스키마는 형식을 보장하지만
     내용은 보장하지 않는다 — 그 구분이 여기서도 그대로입니다) ★

  → **평가자 자체에 버그가 있으면 측정 결과 전체가 무의미합니다.**
    평가자도 이렇게 몇 건을 손으로 채점해 대조해야 합니다.

✅ 규칙 기반의 장점            ⚠️ 한계
  비용 0원 (LLM 호출 없음)       표현이 조금만 달라도 오답 처리
  즉시 채점                      의미가 같은지는 판단 못 함 ★
  항상 같은 결과 (재현 가능)     요약·번역·생성형 과제에 적용 불가
  기준이 코드로 남아 검토 가능   규칙을 정교하게 짜기 어렵다

📌 규칙 기반으로 되는 일은 규칙 기반으로 하십시오.
   분류·추출처럼 답이 정해진 과제에 LLM 판정자를 쓸 이유가 없습니다. 돈과 시간만 더 듭니다.

다음 단계 →  python llm_judge.py       (규칙으로 안 되는 과제는?)
""")


if __name__ == "__main__":
    main()
