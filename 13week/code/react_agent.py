"""[1교시 / 실습 1] ★★ ReAct 에이전트 — 9주차 도구를 그대로, 순환은 그래프가 돌린다

                    ┌──────────────────────────────┐
                    ▼                              │
   START ──▶ ┌────────────┐  도구 필요?  ┌──────────────┐
             │   agent    │─────예──────▶│  ToolNode    │──┘
             │ (모델 호출) │              │ (도구 실행)   │
             └─────┬──────┘              └──────────────┘
                   │ 아니오
                   ▼
                  END

  ★★ 9주차에 우리가 **손으로** 하던 ③단계를 ToolNode 가 대신합니다.
     그리고 **몇 번 돌지는 모델이 정합니다.** 그게 **에이전트**입니다.

     |            | 9주차              | **13주차**              |
     | 도구 실행   | **우리 코드**       | **ToolNode**            |
     | 반복       | 한 바퀴 (수동)      | **모델이 정하는 만큼** ★  |
     | 종료 판단   | 없음               | **조건부 엣지**          |
     | 상태       | messages 를 손으로  | **State + add_messages** ★|

  ⚠️ **바뀌지 않은 것이 하나 있습니다.**
     도구를 **실행하는 주체는 여전히 우리 쪽 코드**입니다.
     ToolNode 는 우리가 그래프에 넣은 노드입니다. **모델이 실행하는 게 아닙니다.**
     → 그래서 **2교시 HITL 로 그 자리를 멈출 수 있습니다.** ★

  ⚠️ 소형 모델의 실패 3종 ★
     무한 루프          같은 도구를 계속 부른다 ⚠️   → recursion_limit 8~10
     도구를 한 번도 안 씀 도구가 있는데 지어낸다      → 도구 2~3개, description 개선
     조기 종료          결과를 받고도 답을 안 만듦   → **시스템 프롬프트에 종료 조건 명시** ★

실행:
    python react_agent.py              # ReAct 에이전트 한 바퀴 ★★
    python react_agent.py --broken     # ⚠️ 리듀서를 빼면? → 무한 루프 시연 ★★
"""

import os
import sys
from typing import Annotated, TypedDict

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

TOOL_MODEL = os.getenv("TOOL_MODEL", "gemma3:4b")  # 🔶 9주차에서 확정한 모델
RECURSION_LIMIT = int(os.getenv("WEEK13_RECURSION_LIMIT", "10"))


# ── ① 도구 — 9주차 과제 3의 것을 그대로 ★ ────────────────────
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


TOOLS = [multiply, get_time]

# ★ 조기 종료·무한 루프를 막는 두 문장. 소형 모델에는 이 두 줄이 큽니다.
SYSTEM = SystemMessage(
    "너는 도구를 사용하는 조수다. 도구가 필요하면 호출하고, "
    "도구 결과를 받으면 반드시 최종 답변을 작성하라. "  # ★ 조기 종료 방지
    "같은 도구를 같은 인자로 두 번 이상 호출하지 마라.")  # ★ 무한 루프 방지


# ── ② 상태 — 리듀서가 핵심 ★★ ───────────────────────────────
class State(TypedDict):
    messages: Annotated[list, add_messages]  # ★ 없으면 대화가 매번 지워진다


class BrokenState(TypedDict):
    """⚠️ 리듀서를 일부러 뺀 것. --broken 시연용 ★★"""

    messages: list  # ← Annotated 제거


def build_agent(tools=None, state_cls=State, model: str | None = None):
    """agent ↔ ToolNode 순환 그래프의 builder 를 만든다.

    ★ 2교시(memory_agent.py)와 3교시가 이 함수를 그대로 가져다 씁니다.
    """
    tools = tools if tools is not None else TOOLS
    llm = ChatOllama(model=model or TOOL_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # ── ③ agent 노드 ────────────────────────────────────────
    def agent(state) -> dict:
        return {"messages": [llm_with_tools.invoke([SYSTEM] + list(state["messages"]))]}

    # ── ④ 조립 ★ ───────────────────────────────────────────
    builder = StateGraph(state_cls)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))  # ★ 도구 실행을 대신해 준다

    builder.add_edge(START, "agent")
    # ★ tools_condition 은 LangGraph 가 제공하는 라우팅 함수입니다.
    #   "마지막 메시지에 tool_calls 가 있으면 'tools', 없으면 END"
    #   — 12주차에 손으로 짠 그 함수입니다.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")  # ★ 되돌아간다 = 순환

    return builder


builder = build_agent()
graph = builder.compile()


def run(g, question: str) -> None:
    """단계별로 찍어 봅니다 — 순환이 실제로 도는 것이 보입니다 ★"""
    for chunk in g.stream(
        {"messages": [HumanMessage(question)]},
        config={"recursion_limit": RECURSION_LIMIT},  # ★ 안전망
        stream_mode="values",
    ):
        chunk["messages"][-1].pretty_print()


def demo_broken() -> None:
    """⚠️ 리듀서를 빼면 무한 루프가 됩니다 ★★

    도구 결과(ToolMessage)가 messages 를 **덮어써서** 사라집니다.
    모델은 결과를 못 보므로 **같은 도구를 계속 요청**합니다.
    → recursion_limit 이 걸려 있어 안전하게 멈춥니다.
    """
    from langgraph.errors import GraphRecursionError

    print("""⚠️ 리듀서를 뺀 State 로 돌립니다 (실패 시연) ★★

    class BrokenState(TypedDict):
        messages: list          # ← Annotated[list, add_messages] 제거

  도구 결과가 messages 를 덮어써서 사라집니다.
  모델은 결과를 못 보므로 같은 도구를 계속 요청합니다.
""")
    g = build_agent(state_cls=BrokenState).compile()
    try:
        run(g, "357 곱하기 4891은?")
        print("\n🔶 이번에는 루프에 빠지지 않았습니다. 모델·온도에 따라 갈립니다.")
        print("   그래도 messages 가 쌓이지 않는 것은 위 출력에서 확인할 수 있습니다. ★")
    except GraphRecursionError:
        print(f"""
✅ GraphRecursionError — recursion_limit({RECURSION_LIMIT}) 에서 멈췄습니다.

  ★★ 12주차에서 배운 리듀서가 **왜 필요한지**가
     여기서 **무한 루프라는 형태로** 드러납니다.
     recursion_limit 이 걸려 있어 안전했습니다 — **안전망의 존재 이유**입니다. ⚠️
""")


def main() -> None:
    print(f"모델: {TOOL_MODEL} / recursion_limit {RECURSION_LIMIT}\n")

    if "--broken" in sys.argv:
        demo_broken()
        return

    run(graph, "357 곱하기 4891은? 그리고 지금 몇 시야?")

    print("""
관찰 포인트 ★★

  agent 노드가 **두 번** 실행됨        **순환이 돌았다** (12주차 시각화와 같은 증거) ★
  ToolNode 가 **자동으로** 실행         "9주차에 손으로 짠 for 문이 사라졌습니다" ★★
  messages 가 쌓임                     **리듀서 add_messages 덕분**
  도구가 필요 없는 질문                 한 바퀴에 END 로 감 — **낭비 없음**

  ⚠️ 실패도 함께 관찰시키십시오: python react_agent.py --broken  ★★

  💡 사전 구축 에이전트: create_react_agent(llm, TOOLS) 한 줄로도 같은 그래프가 됩니다.
     **다만 오늘은 직접 조립합니다** — 안이 보여야 고칠 수 있기 때문입니다.
     (3주차에 ollama.chat() 을 먼저 보고 ChatOllama 로 간 것과 같은 순서 ★)

  ⚠️ 바뀌지 않은 것: 도구를 **실행하는 주체는 여전히 우리 쪽(그래프)** 입니다.
     → 그래서 2교시 HITL 로 그 자리를 멈출 수 있습니다. ★
""")


if __name__ == "__main__":
    main()
