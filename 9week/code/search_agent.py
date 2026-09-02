"""[2교시 / 실습 2] ★ 웹 검색 도구 + 모델별 도구 선택 정확도 비교

  ⚠️⚠️ 운영 안내를 먼저 읽으십시오.

     강의실 전체가 같은 공인 IP 를 씁니다.
     30명이 동시에 검색 = 레이트리밋 차단 = 실습 전체 정지 ⚠️

     [운영] 3~4개 조로 나누어 조별 3~4분 시차 실행 ★
            대기 조는 그동안 3-3 의 description 개선 작업을 먼저 수행
     [최후] .env 에  WEEK09_SEARCH=fake  → 가짜 검색 도구로 대체

  ★ 이 실습이 재는 것: "모델이 도구를 제대로 고르는가"

     도구를 준 모델이 아무 질문에나 검색을 때리는 것도 '실패'입니다.
     그래서 QUESTIONS 에 **도구를 쓰지 말아야 할 질문**을 반드시 넣었습니다.
     (11주차 "안녕하세요에도 벡터 검색이 도는" 낭비 문제와 같은 구조입니다 ★)

  ⚖️ 7주차와의 연결
     아래 표가 곧 작은 데이터셋이고, picked == expected 가 곧 규칙 기반 평가자입니다.
     도구 선택 정확도도 '측정 대상' 입니다.

실행:
    python search_agent.py           # 로컬 (+ 키가 있으면 상용까지 비교)
    python search_agent.py --names   # 도구 이름만 확인 (검색 호출 없음 · 무료) ★
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

TOOL_MODEL = os.getenv("TOOL_MODEL", "gemma3:4b")  # 🔶 tool_support_check.py 로 확정
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DELAY = float(os.getenv("WEEK09_SEARCH_DELAY", "3"))  # ★ 레이트리밋 완화


# ── 검색 도구 — 차단되면 가짜 도구로 갈아끼운다 🔶 ─────────────
def load_search_tool():
    """실제 검색 도구를 만든다. 실패하면 가짜 도구로 대체한다. ★

    ⚠️ 검색 도구의 패키지·클래스명은 버전에 따라 이동한 이력이 있습니다.
       수업 전날 1회 실행해 배포 코드를 확정하십시오. 🔶
    """
    if os.getenv("WEEK09_SEARCH", "duckduckgo").lower() == "fake":
        from fake_search import web_search

        print("🔶 가짜 검색 도구를 씁니다 (.env 의 WEEK09_SEARCH=fake)\n")
        return web_search

    try:
        from langchain_community.tools import DuckDuckGoSearchRun

        return DuckDuckGoSearchRun()  # 도구 객체 — API 키 불필요
    except Exception as e:
        from fake_search import web_search

        print(f"⚠️ 검색 도구를 만들지 못했습니다 ({type(e).__name__}). 가짜 도구로 진행합니다.\n")
        return web_search


@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다. 정확한 곱셈이 필요할 때 사용한다."""
    return a * b


search = load_search_tool()
TOOLS = [search, multiply]

# ⚠️ 기대값은 '도구의 실제 이름'이어야 한다 ★★
#    검색 도구의 name 은 클래스가 정한 값(예: "duckduckgo_search")이지 "search" 가 아닙니다.
#    문자열을 직접 적으면 항상 불일치로 나와 측정이 통째로 무의미해집니다.
SEARCH = search.name
MULT = multiply.name

QUESTIONS = [
    ("2026년 노벨물리학상 수상자는?", SEARCH),  # 검색이 맞다
    ("357 곱하기 4891은?", MULT),  # 계산이 맞다
    ("대한민국의 수도는?", "none"),  # ★ 도구 불필요
    ("파이썬에서 리스트와 튜플의 차이는?", "none"),  # ★ 도구 불필요
]


def show_names() -> None:
    """★ 학생이 직접 실행하게 하십시오. 검색 호출이 없어 무료·즉시입니다."""
    print("── 도구 이름 확인 ★ ─────────────────────────────────")
    for t in TOOLS:
        print(f"  name        : {t.name}")
        print(f"  description : {t.description[:80]}")
        print()
    print(f"""  ★ @tool 로 만든 도구는 '함수 이름' 이 name 이지만,
    클래스로 제공되는 도구는 '클래스가 정한 이름' 을 씁니다.
        검색 도구의 실제 이름 = {SEARCH!r}
        곱셈 도구의 실제 이름 = {MULT!r}

    2교시 1-1 의 "모델이 보는 것은 이름·독스트링·타입힌트" 를
    여기서 확인하는 자리입니다.
""")


def check(llm, label: str) -> int:
    """같은 도구·같은 질문을 주고 '무엇을 골랐는가'만 본다. ★"""
    bound = llm.bind_tools(TOOLS)
    hit = 0

    print(f"\n[{label}]")
    for q, expected in QUESTIONS:
        try:
            msg = bound.invoke([HumanMessage(q)])
            picked = msg.tool_calls[0]["name"] if msg.tool_calls else "none"
        except Exception as e:  # 미지원 모델·네트워크 등
            picked = f"오류({type(e).__name__})"

        ok = picked == expected
        hit += ok
        print(f"  [{'✅' if ok else '❌'}] {q[:24]:24s} 기대={expected:20s} 선택={picked}")
        time.sleep(DELAY)  # ★ 레이트리밋 완화

    print(f"  → [{label}] 도구 선택 정확도 {hit}/{len(QUESTIONS)}")
    return hit


def commercial_llm():
    """🔶 상용 API — 본 차시는 배정 1순위. 키가 없으면 None."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    except Exception as e:
        print(f"🔶 상용 모델을 만들지 못했습니다: {type(e).__name__}")
        return None


def main() -> None:
    if "--names" in sys.argv:
        show_names()
        return

    show_names()

    check(ChatOllama(model=TOOL_MODEL, temperature=0), f"로컬 {TOOL_MODEL}")

    llm_paid = commercial_llm()
    if llm_paid is not None:
        check(llm_paid, f"상용 {OPENAI_MODEL}")
    else:
        print("""
🔶 OPENAI_API_KEY 가 없어 상용 비교는 건너뜁니다.
   로컬만으로도 실습은 성립합니다. 대신 '로컬 소형 vs 로컬 중형' 으로 대체하십시오.
   (.env 의 TOOL_MODEL 을 바꿔가며 두 번 돌리면 됩니다)
""")

    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
결과 기록표 — 학생이 채웁니다

  | 질문           | 기대 도구 | 로컬 모델 | 상용 모델 |
  | 노벨상 수상자   | search   |          |          |
  | 357 × 4891     | multiply |          |          |
  | 대한민국 수도   | none ★   |          |          |
  | 리스트 vs 튜플  | none ★   |          |          |
  | 정확도         |          | ___ / 4  | ___ / 4  |

소형 모델의 전형적 실패 3종 ★

  엉뚱한 도구 선택   "수도는?" 에 multiply 호출     설명문을 제대로 못 읽음
  도구를 아예 안 씀  검색이 필요한데 지어낸다 ⚠️     도구가 있다는 걸 잊음
  불필요한 남발      상식 질문에도 검색             "도구가 있으니 써야 한다"

대응 2가지 ★

  ① 도구 수를 줄인다 (2~3개)
       도구가 10개면 소형 모델은 고르지 못합니다
       → 14주차 멀티 에이전트가 이 문제를 '역할 분담' 으로 풉니다 ★

  ② description 을 고친다
       "날씨 함수"                                ❌
       "도시 이름을 받아 현재 날씨를 조회한다.
        실시간 기상 정보가 필요할 때만 사용한다."   ✅  ← '언제 쓰는지' 를 넣는다

📌 대기 조 활동: multiply 의 독스트링을 고쳐 다시 돌려보십시오.
   설명문 한 줄로 선택 정확도가 바뀌는 것을 직접 보면
   "독스트링이 곧 프롬프트" 가 확실히 남습니다. ★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
