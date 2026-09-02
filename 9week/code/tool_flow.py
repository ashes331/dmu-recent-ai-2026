"""[2교시 / 실습 1] ★★ 도구 호출의 한 바퀴를 손으로 완성한다

   ① 질문
       "357 곱하기 4891은?"
            │
            ▼
   ② 모델이 판단 → tool_calls 반환          ← content 는 비어 있다 ★
       {'name':'multiply', 'args':{'a':357,'b':4891}, 'id':'call_abc'}
            │
            ▼
   ③ ★ 우리 코드가 함수를 실행한다 ★         ← 모델이 하는 게 아니다!
       multiply.invoke({'a':357,'b':4891})  →  1746087
            │
            ▼
   ④ 결과를 ToolMessage 로 되돌린다
       ToolMessage(content='1746087', tool_call_id='call_abc')
            │
            ▼
   ⑤ 모델이 최종 답변 생성
       "357 곱하기 4891은 1746087입니다."

  ★★ 오늘의 핵심 문장
        모델은 도구를 '실행'하지 않습니다. '요청'할 뿐입니다.
        실행은 우리 코드가 합니다.

     실행 주체가 우리이기 때문에 우리가 막을 수 있습니다 → 3교시 보안
     그리고 우리가 안 막으면 아무도 안 막습니다.

  ⚠️ 이 한 바퀴를 손으로 돌리는 것이 오늘의 방식입니다.
     도구가 또 필요하면? 우리가 또 돌려야 합니다.
     → 13주차에서 그래프가 자동으로 돌립니다(ReAct). 오늘의 수고를 기억하십시오. ★

실행:
    python tool_flow.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 다른 import 보다 위 (LangSmith 환경변수를 먼저 읽혀야 함)

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# 🔶 도구 호출을 지원하는 모델이어야 합니다. python tool_support_check.py 로 확정.
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemma3:4b")


# ── ① 도구 정의 — 독스트링이 곧 설명문 ★★ ─────────────────────
@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다. 정확한 곱셈이 필요할 때 사용한다."""
    return a * b


@tool
def get_time(timezone: str = "Asia/Seoul") -> str:
    """지정한 시간대의 현재 시각을 문자열로 반환한다."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S")


TOOLS = {t.name: t for t in [multiply, get_time]}


def show_what_model_sees() -> None:
    """1-1절 — 모델에게 전달되는 것은 무엇인가. ★★

    | 코드 요소       | 모델에게 전달되는 것              |
    | 함수 이름       | 도구 이름                         |
    | ★★ 독스트링    | 도구 설명(언제 쓰는 도구인지)      |
    | 타입 힌트       | 인자 스키마 (이름·타입)           |
    | 함수 본문       | ❌ 전달되지 않음 — 모델은 모른다  |
    """
    print("── 모델이 보는 것 (함수 본문은 안 보인다) ★★ ──────────")
    for t in TOOLS.values():
        print(f"  name        : {t.name}")
        print(f"  description : {t.description}")
        print(f"  args        : {t.args}")
        print()

    print("""  ★★ 독스트링이 곧 프롬프트입니다.
        5주차 Field(description=...) 과 같은 발상입니다.

          \"\"\"도시 이름을 받아 현재 날씨를 조회한다.\"\"\"   ✅ 언제 쓰는지 명확
          \"\"\"날씨 함수.\"\"\"                             ❌ 모델이 못 고릅니다
""")


def one_round(question: str) -> None:
    """②~⑤ — 한 바퀴를 손으로 돌린다."""
    llm = ChatOllama(model=TOOL_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(list(TOOLS.values()))  # ★ 이 한 줄 (4주차 .bind() 계열)

    messages = [HumanMessage(question)]

    # ── ② 1차 호출 — 여기가 오늘의 결정적 장면 ★★ ─────────────
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    print(f"질문      : {question}")
    print("content   :", repr(ai_msg.content), "  ← 비어 있다! ★")
    print("tool_calls:", ai_msg.tool_calls)

    if not ai_msg.tool_calls:
        # 🔶 모델이 도구 호출을 지원하지 않거나, 도구가 필요 없다고 판단한 경우
        print(f"""
⚠️ tool_calls 가 비어 있습니다. 둘 중 하나입니다.
   ① 모델이 "도구가 필요 없다"고 판단했다 → 정상 (상식 질문이면 오히려 맞습니다)
   ② '{TOOL_MODEL}' 이 도구 호출을 지원하지 않는다 ⚠️
      → python tool_support_check.py 로 확인하고 .env 의 TOOL_MODEL 을 고치십시오.
""")
        print("모델의 답 :", ai_msg.content[:120])
        return

    # ── ③④ ★ 우리가 실행하고 ToolMessage 로 되돌린다 ★ ────────
    print("\n── ③ 실행 주체는 우리 코드입니다 (아래 로그는 우리가 찍은 것) ★★ ──")
    for call in ai_msg.tool_calls:
        tool_obj = TOOLS[call["name"]]

        # 두 형태의 차이를 반드시 짚을 것 ★
        #   invoke(call["args"]) → 그냥 '결과값'          (파이썬 값)
        #   invoke(call)         → 'ToolMessage'          (tool_call_id 자동 기입)
        raw_result = tool_obj.invoke(call["args"])
        tool_msg = tool_obj.invoke(call)

        print(f"  실행 {call['name']}({call['args']}) → {raw_result}")
        print(f"    args 만 넘기면 : {raw_result!r}          ← 파이썬 값")
        print(f"    call 을 넘기면 : {type(tool_msg).__name__}"
              f"(content={tool_msg.content!r}, tool_call_id={tool_msg.tool_call_id!r})")

        messages.append(tool_msg)  # ★ tool_call_id 로 요청-결과의 짝을 맞춘다

    # ── ⑤ 다시 모델에게 — 이번엔 최종 답이 나온다 ──────────────
    final = llm_with_tools.invoke(messages)
    print("\n최종 답변 :", final.content.strip())
    print(f"messages 길이: {len(messages) + 1}  ← 대화 이력이 쌓인다 (5주차 MessagesPlaceholder 의 자리)")


def main() -> None:
    print(f"모델: {TOOL_MODEL}\n")

    show_what_model_sees()
    print("=" * 60, "\n")

    # 질문 하나에 도구 두 개를 요청할 수 있다 ★
    one_round("357 곱하기 4891은? 그리고 지금 몇 시야?")

    print("\n" + "=" * 60)
    print("""
관찰 포인트 ★

  1차 응답의 content 가 빈 문자열
        → "모델이 답을 안 했습니다. 도구를 달라고 한 겁니다"
  tool_calls 가 2개
        → 질문 하나에 도구 두 개를 요청할 수 있다
  함수 실행 로그
        → 우리 코드가 찍은 로그. 실행 주체가 우리임을 확인 ★★
  최종 답변의 계산이 정확
        → 1교시에서 틀렸던 계산이 맞게 나온다
          (LLM 은 계산기가 아니라 '다음 토큰 예측기' 였습니다)

  ⚠️ 도구가 또 필요하면 우리가 또 돌려야 합니다.
     → 13주차 ToolNode 가 이 for 문을 대신합니다. ★
""")
    print("=" * 60)


if __name__ == "__main__":
    main()
