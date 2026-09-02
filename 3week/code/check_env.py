"""[1교시 / 실습 1] .env 로 분리한 API 키가 제대로 로드되는지 확인한다.

핵심 원칙
    - 키는 코드가 아니라 .env 에 둔다
    - 코드에서는 "이름으로만" 참조한다
    - 값 자체는 절대 화면에 출력하지 않는다  ★

실행:
    python check_env.py
"""

import os

from dotenv import load_dotenv

# .env 파일을 읽어 환경변수로 로드한다.
# .env 가 없어도 에러가 나지 않는다 → 아래에서 존재 여부를 직접 확인한다.
load_dotenv()

# 이번 학기에 쓸 키 목록
KEYS = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]


def mask(value: str) -> str:
    """키가 맞는지 눈으로만 확인할 수 있게 가린다.

    화면 공유·스크린샷·터미널 로그로 유출되지 않도록
    앞 4글자 외에는 모두 * 로 덮는다.
    """
    if len(value) <= 4:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 4)


def main() -> None:
    print("=" * 50)
    print("  .env 로드 확인")
    print("=" * 50)

    for name in KEYS:
        value = os.getenv(name)

        # ❌ print(value)          ← 절대 금지. 키 전체가 그대로 노출된다
        # ✅ 존재 여부만 확인한다
        if value:
            print(f"  [O] {name:20s} 로드됨  ({mask(value)}, {len(value)}자)")
        else:
            print(f"  [X] {name:20s} 없음")

    print("-" * 50)
    print("  3주차는 로컬 Ollama만 쓰므로 [X] 여도 정상입니다.")
    print("  키는 4주차 수업 중에 배포합니다.")
    print("=" * 50)

    # 마지막 자가 점검 — .env 가 커밋 대상에서 빠져 있는지
    print()
    print("  다음 명령으로 .env 가 추적되지 않는지 반드시 확인하세요:")
    print("      git status")
    print("      git check-ignore -v .env      # .gitignore:N:.env  이 나오면 정상")


if __name__ == "__main__":
    main()
