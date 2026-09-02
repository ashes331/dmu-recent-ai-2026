"""[1교시 / 확인 B] VRAM 요구량 어림 계산기

1교시 2-3에서 손으로 계산한 것을 코드로 옮긴 것입니다.
⚠️ 손계산을 대신하려고 만든 게 아닙니다. 손으로 먼저 계산하고,
   그 다음 이 스크립트로 답을 맞춰 보는 용도입니다.

계산식
    필요 VRAM = ① 가중치 + ② KV 캐시 + ③ 실행 오버헤드

    ① 가중치(GB) = 파라미터 수(B) × 실효 비트수 ÷ 8
                    Q4_K_M 의 실효 비트는 4가 아니라 약 4.5    ★
    ② KV 캐시     = 파라미터 1B · 컨텍스트 1K 당 대략 16MB
    ③ 오버헤드    = CUDA 컨텍스트·런타임으로 0.5 ~ 1GB

⚠️ 전부 어림값입니다. 모델 구조(GQA 여부, 비전 인코더 유무)에 따라 달라집니다.
   정확한 값이 목적이 아니라 "올라가는가 / 아슬아슬한가 / 안 되는가" 를
   3초 안에 가르는 것이 목적입니다.

실행:
    python vram_calc.py                    # 슬라이드의 4B·8B·12B 표를 출력
    python vram_calc.py 4.3 4096           # 내 화면의 값으로 계산 (ollama show)
"""

import sys

# 실습실 PC 기준
VRAM_GB = 8.0

# Q4_K_M 의 실효 비트수. 레이어별로 비트를 다르게 배분하므로 4가 아니다  ★
EFFECTIVE_BITS = 4.5

# 파라미터 1B · 컨텍스트 1K 당 KV 캐시 (GB) — 어림값 (약 12~13MB)
KV_GB_PER_B_PER_K = 0.0125

# CUDA 컨텍스트 등 실행 오버헤드 (GB)
OVERHEAD_GB = 0.7


def estimate(params_b: float, ctx_tokens: int, bits: float = EFFECTIVE_BITS) -> dict:
    """파라미터 수(B)와 컨텍스트 길이(토큰)로 필요 VRAM을 어림한다."""
    weights = params_b * bits / 8  # ① 가중치
    kv = params_b * (ctx_tokens / 1024) * KV_GB_PER_B_PER_K  # ② KV 캐시
    total = weights + kv + OVERHEAD_GB  # ③ 오버헤드 포함
    return {"weights": weights, "kv": kv, "overhead": OVERHEAD_GB, "total": total}


def verdict(total_gb: float) -> str:
    """8GB에서 어떻게 되는가 — 세 갈래로만 가른다."""
    if total_gb <= VRAM_GB * 0.8:
        return "[가능] 여유 있음"
    if total_gb <= VRAM_GB * 1.1:
        # 어림값이므로 VRAM 근처(±10%)는 '경계'로 본다.
        # 에러가 아니라 '느려지는' 구간이라 이게 더 위험하다  ★
        return "[경계] 넘치기 쉬움 - 일부 레이어가 CPU로 밀릴 수 있음"
    return "[초과] CPU 분산으로 수 배 느려짐"


def print_row(label: str, params_b: float, ctx: int) -> None:
    r = estimate(params_b, ctx)
    print(
        f"  {label:<6} "
        f"가중치 {r['weights']:>5.1f}GB  "
        f"KV {r['kv']:>4.1f}GB  "
        f"오버헤드 {r['overhead']:>4.1f}GB  "
        f"= 합계 {r['total']:>5.1f}GB   {verdict(r['total'])}"
    )


def main() -> None:
    print(f"기준: VRAM {VRAM_GB:.0f}GB / 양자화 Q4_K_M(실효 {EFFECTIVE_BITS}비트)")
    print()

    if len(sys.argv) >= 2:
        # 내 화면의 값으로 계산한다 — ollama show 로 조회한 그 숫자  ★
        params_b = float(sys.argv[1])
        ctx = int(sys.argv[2]) if len(sys.argv) >= 3 else 4096
        print(f"── 입력값: 파라미터 {params_b}B / 컨텍스트 {ctx} ──")
        print_row(f"{params_b}B", params_b, ctx)
        print()
        print("※ ollama ps 의 SIZE 열과 비교해 보세요. (1교시 2-4)")
        return

    # ── 슬라이드의 세 가지 예제 (컨텍스트 4K 기준) ──
    print("── 컨텍스트 4K 기준 ──────────────────────────────────────────")
    for label, params_b in [("4B", 4.0), ("8B", 8.0), ("12B", 12.0)]:
        print_row(label, params_b, 4096)

    print()
    print("── 같은 모델, 컨텍스트만 8K 로 늘리면 (num_ctx 의 대가) ★ ────")
    for label, params_b in [("4B", 4.0), ("8B", 8.0), ("12B", 12.0)]:
        print_row(label, params_b, 8192)

    print()
    print("[정리] 12B는 '되긴 하는데 느린' 구간입니다.")
    print("   인터넷 가이드가 권하는 모델이라도, 판단은 내 하드웨어 기준으로.")
    print()
    print("※ 내 모델로 계산하려면:  python vram_calc.py <파라미터수> <컨텍스트>")
    print("   예)  ollama show gemma3:4b  →  python vram_calc.py 4.3 8192")


if __name__ == "__main__":
    main()
