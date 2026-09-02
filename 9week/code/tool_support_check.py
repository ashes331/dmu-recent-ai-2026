"""[사전 확인] 🔶 교수용 — 이 모델이 도구 호출을 지원하는가 ★★

  ⚠️ 이 차시 최대의 위험 지점입니다.
     모든 모델이 도구 호출을 지원하지는 않습니다.
     지원하지 않는 모델에 bind_tools() 를 하면
       · tool_calls 가 늘 비어 있거나
       · 오류가 납니다
     → 2교시 실습 1(20분)이 통째로 성립하지 않습니다.

  ★ 학기 시작 전 / 늦어도 수업 전날, 실습실 PC 에서 1회 실행하십시오.
    통과한 모델 이름을 .env 의 TOOL_MODEL 에 적어 배포하면 됩니다.

  (실습환경_사전설치_목록.md 2-2절의 그 스크립트를 실행 가능한 형태로 옮긴 것입니다)

실행:
    python tool_support_check.py                  # .env 의 TOOL_MODEL + 후보들
    python tool_support_check.py qwen3:8b llama3.1:8b   # 후보를 직접 지정
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# 🔶 실습실에 pull 되어 있는 후보를 적으십시오. (ollama list 로 확인)
CANDIDATES = [
    os.getenv("TOOL_MODEL", "gemma3:4b"),
    "gemma3:4b",
]


@tool
def add(a: int, b: int) -> int:
    """두 정수를 더한다. 정확한 덧셈이 필요할 때 사용한다."""
    return a + b


def check(name: str) -> bool:
    """bind_tools 후 tool_calls 가 실제로 채워지는가. ★ 이것이 유일한 판정 기준."""
    try:
        llm = ChatOllama(model=name, temperature=0).bind_tools([add])
        msg = llm.invoke("17 더하기 25는?")
    except Exception as e:  # 모델 미설치·미지원 등
        print(f"  [{name:24s}] ❌ 오류 — {type(e).__name__}: {str(e)[:70]}")
        return False

    calls = getattr(msg, "tool_calls", None) or []
    if calls:
        print(f"  [{name:24s}] ✅ 지원  tool_calls={calls}")
        return True

    # ★ 여기가 가장 흔한 실패 모습입니다 — 오류 없이 '그냥 답해 버립니다'
    print(f"  [{name:24s}] ❌ 미지원  content={msg.content[:50]!r}")
    return False


def main() -> None:
    names = sys.argv[1:] or CANDIDATES
    seen, targets = set(), []
    for n in names:  # 중복 제거 (순서 유지)
        if n not in seen:
            seen.add(n)
            targets.append(n)

    print("도구 호출 지원 여부 확인 — 판정 기준은 'tool_calls 가 채워지는가' 하나입니다 ★")
    print("─" * 72)

    passed = [n for n in targets if check(n)]

    print("─" * 72)
    if passed:
        print(f"""
✅ 사용 가능한 모델: {', '.join(passed)}

   .env 에 아래 한 줄을 넣어 배포하십시오.
       TOOL_MODEL={passed[0]}
""")
    else:
        print("""
⚠️⚠️ 도구 호출을 지원하는 로컬 모델이 없습니다.

   대응 순서 ★
     ① ollama list 로 다른 후보를 확인하고 이 스크립트에 인자로 넘겨 재확인
            python tool_support_check.py <후보1> <후보2>
     ② 지원 모델을 pull  (⚠️ 30명 동시 다운로드 금지 — 사전에 관리자 배포)
     ③ 본 차시는 상용 API 배정 1순위입니다.
        로컬이 안 되면 .env 에 OPENAI_API_KEY 를 넣고 상용으로 진행하십시오.
""")


if __name__ == "__main__":
    main()
