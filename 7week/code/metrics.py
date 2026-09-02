"""[2·3교시 공용] 3축 측정 헬퍼 — 정확도 · 토큰 · 지연시간

  ⚠️ 정확도만 보면 안 됩니다 (2교시 3-1).

      정확도  78% → 86%   (+8%p)
      토큰    3배
      지연    2.5배
      비용    5배
        │
        ▼
      "정확도가 올랐다" 는 채택의 근거가 아닙니다.
      **"무엇을 얼마에 샀는가"** 를 봐야 합니다. ★★

★ 구조화 출력을 쓰면 토큰이 사라지는 문제
    with_structured_output(Result) 의 반환값은 Pydantic 객체입니다.
    편하지만 원본 AIMessage 가 없어져 usage_metadata(토큰) 를 볼 수 없습니다.

    → include_raw=True 를 주면 이렇게 돌아옵니다:
         {"raw": AIMessage, "parsed": Result | None, "parsing_error": ...}
      원본이 함께 오므로 토큰을 셀 수 있습니다. ★

    🔶 실습실에서 include_raw 가 말썽이면 .env 에 아래 한 줄을 넣으십시오.
         WEEK07_INCLUDE_RAW=false
       (토큰은 "측정 불가" 로 처리되고 정확도·지연은 그대로 측정됩니다.
        6주차에서 gemma3 의 토큰 수가 안 잡히던 것과 같은 대비책입니다)

이 파일은 단독 실행용이 아닙니다. ab_experiment.py / regression.py 가 가져다 씁니다.
"""

from __future__ import annotations

import os
import threading
import time
import unicodedata
from dataclasses import dataclass, field

INCLUDE_RAW = os.getenv("WEEK07_INCLUDE_RAW", "true").strip().lower() != "false"


# ── 표를 그리기 위한 잡일 ──────────────────────────────────────
#    한글·★ 는 폭이 2인데 len() 은 1로 셉니다. 그대로 f"{s:<20}" 하면 표가 어긋납니다.
def width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))


def pad(s: str, n: int, align: str = "<") -> str:
    """표시 폭 기준으로 채운다. align: '<' 왼쪽 / '>' 오른쪽."""
    s = str(s)
    fill = " " * max(0, n - width(s))
    return s + fill if align == "<" else fill + s


def build_chain(prompt, llm, schema):
    """prompt | llm.with_structured_output(schema)  — 토큰을 보려면 include_raw=True ★"""
    if INCLUDE_RAW:
        return prompt | llm.with_structured_output(schema, include_raw=True)
    return prompt | llm.with_structured_output(schema)


def split(result):
    """invoke/batch 반환값을 (parsed, input_tokens, output_tokens) 으로 쪼갠다."""
    if isinstance(result, dict) and ("parsed" in result or "raw" in result):
        parsed = result.get("parsed")
        usage = getattr(result.get("raw"), "usage_metadata", None) or {}
        return parsed, usage.get("input_tokens"), usage.get("output_tokens")
    return result, None, None


def label_of(parsed, default: str = "") -> str:
    """parsed 에서 label 을 안전하게 꺼낸다. 실패분은 빈 문자열 = 오답 처리."""
    value = getattr(parsed, "label", None)
    return str(value).strip() if value else default


@dataclass
class Meter:
    """실험 하나의 3축 누적기. evaluate() 가 예제를 병렬로 돌리므로 잠금이 필요하다."""

    name: str
    examples: int = 0  # 예제 수 (= traces 계산의 기준)
    llm_calls: int = 0  # 실제 LLM 호출 수 (Self-Consistency 는 예제당 N회) ★
    failures: int = 0  # 예외·파싱 실패 (오답으로 센다)
    seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    unmeasured: int = 0  # 토큰이 안 잡힌 호출 수 🔶
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, seconds: float, usages, *, failed: bool = False) -> None:
        with self._lock:
            self.examples += 1
            self.seconds += seconds
            self.llm_calls += len(usages)
            if failed:
                self.failures += 1
            for tin, tout in usages:
                if tin is None and tout is None:
                    self.unmeasured += 1
                else:
                    self.input_tokens += tin or 0
                    self.output_tokens += tout or 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def tokens_text(self) -> str:
        if self.total_tokens == 0 and self.unmeasured:
            return "측정 불가"
        suffix = f" (미측정 {self.unmeasured}건)" if self.unmeasured else ""
        return f"{self.total_tokens:,}{suffix}"

    @property
    def avg_seconds(self) -> float:
        return self.seconds / self.examples if self.examples else 0.0


def _ratio(b: float, a: float) -> str:
    """b 가 a 의 몇 배인가."""
    if not a:
        return "—"
    return f"{b / a:.1f}배"


def comparison_table(meters, accuracy=None) -> str:
    """3축 비교표를 그린다. accuracy 는 {실험이름: 0.0~1.0} — 웹에서 읽어 넣어도 된다."""
    accuracy = accuracy or {}
    a, b = meters[0], meters[1]
    acc_a, acc_b = accuracy.get(a.name), accuracy.get(b.name)

    def pct(v):
        return f"{v * 100:.1f} %" if v is not None else "웹에서 확인"

    diff = (
        f"{(acc_b - acc_a) * 100:+.1f}%p" if acc_a is not None and acc_b is not None else "—"
    )

    def row(axis, va, vb, delta=""):
        return "  " + pad(axis, 20) + pad(va, 18, ">") + pad(vb, 22, ">") + pad(delta, 12, ">")

    lines = [
        "",
        "  3축 비교표 ★★  — RESULTS.md 에 그대로 옮겨 적으십시오",
        "  " + "─" * 72,
        row("비교축", "A. " + a.name, "B. " + b.name, "차이"),
        "  " + "─" * 72,
        row("정확도", pct(acc_a), pct(acc_b), diff),
        row("총 토큰", a.tokens_text, b.tokens_text, _ratio(b.total_tokens, a.total_tokens)),
        row(
            "총 소요 시간",
            f"{a.seconds:.1f}초",
            f"{b.seconds:.1f}초",
            _ratio(b.seconds, a.seconds),
        ),
        row(
            "예제당 평균 지연",
            f"{a.avg_seconds:.1f}초",
            f"{b.avg_seconds:.1f}초",
            _ratio(b.avg_seconds, a.avg_seconds),
        ),
        row("LLM 호출 수", a.llm_calls, b.llm_calls, _ratio(b.llm_calls, a.llm_calls)),
        row("traces 소모", a.llm_calls, b.llm_calls, _ratio(b.llm_calls, a.llm_calls)),
        row("실패(오답 처리)", a.failures, b.failures),
        "  " + "─" * 72,
    ]
    return "\n".join(lines)
