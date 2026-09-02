"""[3교시 / 2절] 무료 한도 계산 — 예제 수 × 실험 수 × 샘플링 배수

  소모량 ≒ 예제 수 × 실험 수 × (샘플링 배수) + 판정자 호출

  ⚠️ 주의해야 할 조합
       Self-Consistency(N=5) × 예제 100개 × 실험 5회 = 2,500 traces
       한 번에 한도의 절반을 씁니다. **N 과 예제 수는 곱해집니다.** ★

  한도 관리 3원칙
    ① 데이터셋을 작게      10~20개. 늘리는 건 언제든 가능
    ② 샘플링 배수를 조심   batch(N) 은 traces 가 N배 ★
    ③ 디버깅 중에는 끄기   LANGSMITH_TRACING=false

  💡 초과하면? 429 로 거부될 뿐 **과금되지 않습니다**(하드 캡).
     다만 그 시점부터 기록이 안 남으므로, 과제 마감 직전에 소진되면 곤란합니다.
     ⚠️⚠️ 개인 신용카드를 등록하면 그 안전장치가 풀립니다. 절대 등록하지 마십시오.

실행:
    python quota_calc.py                    # 오늘 수업 소모량
    python quota_calc.py 100 5 5            # 예제 100 · 실험 5회 · 샘플링 5배 ⚠️
"""

import sys

from metrics import pad  # 표시 폭(한글=2)을 맞춰 표를 그리는 잡일 함수

FREE_MONTHLY = 5_000  # 무료 Developer 플랜: 월 5,000 traces

# (이름, 예제 수, 샘플링 배수, 설명)
TODAY = [
    ("실습 2  A (CoT)", 16, 1, "예제당 1회"),
    ("실습 2  B (Self-Consistency)", 16, 5, "예제당 5회 ⚠️"),
    ("실습 3  C (CoT-v2)", 16, 1, "같은 데이터셋 재평가"),
    ("2교시 판정자 시연", 10, 1, "llm_judge.py — 로컬"),
]

LATER = [
    ("보충 Zero-shot", 16, 1, "수업 후 · 무배점"),
    ("보충 Few-shot", 16, 1, "수업 후 · 무배점"),
    ("보충 Step-Back", 16, 2, "상위 질문 1회 + 원 질문 1회 ★"),
]


def table(title: str, rows) -> int:
    def line(name, n, mult, traces, note=""):
        return (
            "  " + pad(name, 34) + pad(n, 6, ">") + pad(mult, 6, ">") + pad(traces, 10, ">")
            + ("   " + note if note else "")
        )

    print(f"\n  {title}")
    print("  " + "─" * 62)
    print(line("항목", "예제", "배수", "traces"))
    print("  " + "─" * 62)
    total = 0
    for name, n, mult, note in rows:
        traces = n * mult
        total += traces
        print(line(name, n, mult, traces, note))
    print("  " + "─" * 62)
    print(line("소계", "", "", total))
    return total


def main() -> None:
    args = sys.argv[1:]

    if len(args) >= 2:
        n = int(args[0])
        runs = int(args[1])
        mult = int(args[2]) if len(args) > 2 else 1
        traces = n * runs * mult
        print("=" * 66)
        print(f"  예제 {n}개 × 실험 {runs}회 × 샘플링 {mult}배 = {traces:,} traces")
        print(f"  무료 한도 {FREE_MONTHLY:,} 대비 {traces / FREE_MONTHLY * 100:.1f}%")
        print("=" * 66)
        if traces > FREE_MONTHLY:
            print("  ⚠️ 한도 초과입니다. 429 로 거부되며 기록이 남지 않습니다.")
        elif traces > FREE_MONTHLY * 0.2:
            print("  ⚠️ 한 번에 한도의 20% 이상을 씁니다. 예제 수나 N 을 줄이십시오. ★")
        else:
            print("  ✅ 여유 있습니다.")
        return

    print("=" * 66)
    print("  무료 한도 소모량 계산 — 학생 1인 기준")
    print("=" * 66)
    today = table("오늘 수업", TODAY)
    later = table("수업 후 보충 실습 (무배점)", LATER)

    print("\n  " + "=" * 62)
    for name, value in [
        ("무료 한도 (월)", FREE_MONTHLY),
        ("오늘 수업", today),
        ("보충 실습", later),
        ("합계", today + later),
    ]:
        print("  " + pad(name, 40) + pad(f"{value:,}", 10, ">"))
    left = FREE_MONTHLY - today - later
    print("  " + pad("남는 여유", 40) + pad(f"{left:,}", 10, ">") + "   ✅ 충분")
    print("  " + "=" * 62)
    print(f"""
⚠️ 주의해야 할 조합 — 직접 계산해 보십시오

    python quota_calc.py 100 5 5      → 예제 100 × 실험 5 × N=5

한도 관리 3원칙
  ① 데이터셋을 작게       10~20개. 늘리는 건 언제든 가능
  ② 샘플링 배수를 조심    batch(N) 은 traces 가 N배 ★
  ③ 디버깅 중에는 끄기    .env 에서  LANGSMITH_TRACING=false

⚠️ 추적 보존은 14일입니다 (6주차). 오늘 만든 실험 결과도 2주 뒤 사라집니다.
   **캡처를 지금 저장**하십시오. 중간고사 대비 자료로 쓸 것입니다. ★
""")


if __name__ == "__main__":
    main()
