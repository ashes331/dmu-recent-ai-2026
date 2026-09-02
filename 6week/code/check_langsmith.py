"""[1교시 / 실습 1] ★ .env 에 넣은 LangSmith 설정이 실제로 로드되는지 확인한다.

3주차 check_env.py 의 6주차 판입니다. 원칙은 그대로입니다.

    - 키는 코드가 아니라 .env 에 둔다
    - 코드에서는 "이름으로만" 참조한다
    - 값 자체는 절대 화면에 출력하지 않는다  ★  (오늘은 캡처를 제출합니다!)

⚠️ 이 파일을 먼저 돌리게 하십시오.
   trace_on.py 를 돌렸는데 목록이 비어 있으면 원인이 셋 중 하나인데,
   그 셋을 여기서 미리 갈라 줍니다.

실행:
    python check_langsmith.py
"""

import os

from dotenv import load_dotenv

# ★ 반드시 파일 맨 위. 아래에 있으면 라이브러리가 이미 값을 읽은 뒤라 안 먹습니다.
load_dotenv()

# 현재 권장 이름 / 예전 이름 — 둘 다 확인해 준다 🔶
NEW_NAMES = ["LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"]
OLD_NAMES = ["LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"]

TRUTHY = {"true", "1", "yes", "on"}


def mask(value: str) -> str:
    """키가 맞는지 눈으로만 확인할 수 있게 가린다.

    오늘은 추적 화면을 캡처해 제출합니다.
    터미널 캡처에 키가 통째로 찍히는 사고가 실제로 납니다. ★
    """
    if len(value) <= 8:
        return "*" * len(value)
    return value[:8] + "*" * (len(value) - 8)


def show(names: list[str], label: str) -> dict[str, str]:
    print(f"  [{label}]")
    found: dict[str, str] = {}
    for name in names:
        value = os.getenv(name)
        if not value:
            print(f"    [X] {name:22s} 없음")
            continue

        found[name] = value
        if "API_KEY" in name:
            # ❌ print(value)  ← 절대 금지
            print(f"    [O] {name:22s} 로드됨  ({mask(value)}, {len(value)}자)")
        else:
            print(f"    [O] {name:22s} = {value}")
    print()
    return found


def diagnose(found: dict[str, str]) -> None:
    """자주 나오는 실수 세 가지를 여기서 잡는다. ★"""
    print("-" * 64)
    print("  점검")
    print("-" * 64)

    tracing = found.get("LANGSMITH_TRACING") or found.get("LANGCHAIN_TRACING_V2") or ""
    key = found.get("LANGSMITH_API_KEY") or found.get("LANGCHAIN_API_KEY") or ""
    project = found.get("LANGSMITH_PROJECT") or found.get("LANGCHAIN_PROJECT") or ""

    # ① 스위치
    if tracing.strip().lower() in TRUTHY:
        print("    [O] 추적 스위치가 켜져 있습니다.")
    else:
        print(f"    [X] 추적이 꺼져 있습니다 (값: {tracing!r})")
        print("        → .env 에 LANGSMITH_TRACING=true  (소문자 true 권장)")

    # ② 키 — 가장 흔한 사고가 따옴표·공백입니다
    if not key:
        print("    [X] API 키가 없습니다. Settings → API Keys 에서 발급하십시오.")
    else:
        if key != key.strip():
            print("    [X] 키 앞뒤에 공백이 있습니다 ⚠️  → .env 에서 지우십시오.")
        elif key[0] in "\"'" or key[-1] in "\"'":
            print("    [X] 키가 따옴표로 감싸여 있습니다 ⚠️  → 따옴표 없이 붙여넣습니다.")
        elif not key.startswith("lsv2_"):
            print(f"    [!] 키가 lsv2_ 로 시작하지 않습니다 (현재: {key[:5]}...)")
            print("        형식이 바뀌었을 수 있습니다. 발급 화면을 다시 확인하십시오. 🔶")
        else:
            print("    [O] 키 형식이 정상으로 보입니다.")

    # ③ 프로젝트
    if project:
        print(f"    [O] 기록은 '{project}' 프로젝트로 들어갑니다.")
    else:
        print("    [!] LANGSMITH_PROJECT 가 없습니다 → 'default' 로 들어갑니다.")
        print("        주차별로 나눠 두지 않으면 나중에 구분이 안 됩니다.")


def ping() -> None:
    """실제로 인증까지 되는지 확인한다 (선택)."""
    print()
    print("-" * 64)
    print("  서버 확인")
    print("-" * 64)
    try:
        from langsmith import Client

        client = Client()
        # 프로젝트를 1건만 읽어 본다 — 인증이 되면 예외가 안 난다
        list(client.list_projects(limit=1))
        print("    [O] 인증 성공 — 내 계정으로 연결되었습니다 ★")
    except ImportError:
        print("    [X] langsmith 패키지가 없습니다 → pip install -r requirements.txt")
    except Exception as e:  # noqa: BLE001
        print(f"    [X] 연결/인증 실패 — {type(e).__name__}: {e}")
        print("        · 401/403 → 키가 잘못됨")
        print("        · 시간 초과 → net_check.py 로 네트워크부터 확인")


def main() -> None:
    print("=" * 64)
    print("  6주차 실습 1 — LangSmith 연동 확인")
    print("=" * 64)

    found = show(NEW_NAMES, "현재 권장 이름")
    old = show(OLD_NAMES, "예전 이름 (있어도 대개 동작합니다)")
    found.update(old)

    diagnose(found)
    ping()

    print()
    print("=" * 64)
    print("""
전부 [O] 라면 다음으로 넘어갑니다.

    python trace_on.py

⚠️ .env 를 고쳤는데 값이 안 바뀌면 → 터미널을 새로 열고 다시 실행하십시오.
   load_dotenv() 는 이미 셸에 있는 환경변수를 기본적으로 덮어쓰지 않습니다. ★

⚠️ 마지막으로 한 번 더:
       git check-ignore -v .env
   출력이 나와야 안전합니다. 오늘 키가 하나 더 늘었습니다.
""")
    print("=" * 64)


if __name__ == "__main__":
    main()
