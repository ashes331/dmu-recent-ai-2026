"""[1교시 / 실습 1] ★★ Supervisor 패턴 — 역할이 다른 에이전트를 관리자가 배분한다

  왜 하나로는 안 되는가

     도구 2~3개   →  잘 고른다 ✅
     도구 5개     →  가끔 헷갈린다
     도구 10개    →  ⚠️ 못 고른다        ← 9주차에서 이미 확인한 현상

     엉뚱한 도구 선택   설명문 10개를 다 읽고 비교하기 어려움
     도구를 아예 안 씀  선택지가 많아 판단을 회피
     **프롬프트 충돌** ★ "간결히 답하라" + "근거를 상세히 인용하라" + … 지시가 부딪힘

     ⚠️ 9주차의 대응은 "도구 수를 2~3개로 제한" 이었습니다.
        그런데 **정말 10개가 필요한 서비스**라면? — 제한이 답이 될 수 없습니다.

  사람은 어떻게 하는가 → **역할별로 나누고, 관리자가 일을 배분한다** ★

                    ┌──────────────┐
        질문 ──────▶│  Supervisor  │◀──────┐
                    └──────┬───────┘       │ 결과를 보고 다음 담당자 결정
              ┌────────────┼────────────┐  │
              ▼            ▼            ▼  │
       ┌───────────┐ ┌──────────┐ ┌─────────┴─┐
       │ 검색 에이전트│ │계산 에이전트│ │작성 에이전트│
       │ (도구 1개)  │ │ (도구 1개) │ │ (도구 0개) │
       └───────────┘ └──────────┘ └───────────┘

  ★ **구조적으로는 12주차 조건부 엣지 + 순환입니다.**
    Supervisor 가 라우팅 노드이고, 워커가 끝나면 다시 Supervisor 로 돌아옵니다.
    **새 개념이 아니라 조합입니다.**

  ★ 개별 에이전트는 **9주차 원칙(도구 2~3개)을 그대로 지킵니다.**
    각자 적은 도구 + 짧고 명확한 지시. 전체로는 3개를 씁니다.

  ⚠️⚠️ 비용은 **곱으로** 늘어납니다.
       Supervisor 판단 1회 + 워커 실행 → 다시 Supervisor …
       에이전트 3개 × 순환 = 단일 에이전트의 몇 배 호출 ⚠️
       → 로컬 모델 기준 에이전트 2~3개, recursion_limit 은 낮게.
       → 30명 동시 실행 시 GPU 부하를 고려해 **순차 실행을 유도**하십시오. ★

  ⚖️ **멀티 에이전트는 정확도를 비용으로 삽니다.**
     **도구가 3개면 단일 에이전트가 낫습니다.** 나누는 것은 **역할이 정말 갈릴 때**입니다. ★

실행:
    python supervisor.py
"""

import os
import sys
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

TOOL_MODEL = os.getenv("TOOL_MODEL", "gemma3:4b")  # 🔶 9주차에서 확정한 모델
MAX_STEPS = int(os.getenv("WEEK14_MAX_STEPS", "6"))  # ★ 종료 안전장치
RECURSION_LIMIT = int(os.getenv("WEEK14_RECURSION_LIMIT", "15"))

llm = ChatOllama(model=TOOL_MODEL, temperature=0)


# ── 도구: 역할별로 '적게' 준다 ★ ─────────────────────────────
@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다. 정확한 곱셈이 필요할 때 사용한다."""
    return a * b


@tool
def search_docs(query: str) -> str:
    """사내·학내 문서에서 관련 내용을 찾는다. 규정·학칙 확인이 필요할 때 사용한다."""
    # 🔶 11주차 retriever 를 연결하면 실제 검색이 됩니다 ★
    #    from rag_common import load_store
    #    docs = load_store().as_retriever(search_kwargs={"k": 3}).invoke(query)
    #    return "\n".join(d.page_content for d in docs)
    return f"[검색결과] '{query}' 관련 규정: 일반휴학은 통산 6개 학기까지."


class State(TypedDict):
    messages: Annotated[list, add_messages]
    next: str
    steps: int


WORKERS = ("researcher", "calculator", "writer")


# ── ① Supervisor — 다음 담당자를 고른다 ★★ ───────────────────
class Route(BaseModel):
    """다음 담당자."""

    next: Literal["researcher", "calculator", "writer", "FINISH"] = Field(
        description="문서 조회가 필요하면 researcher, 계산이면 calculator, "
                    "최종 정리가 필요하면 writer, 모두 끝났으면 FINISH")


def supervisor(state: State) -> dict:
    sys_msg = SystemMessage(
        "너는 팀 관리자다. 지금까지의 대화를 보고 다음에 일할 담당자를 고르라. "
        "이미 필요한 정보가 모였고 정리도 끝났으면 FINISH 를 고르라.")
    step = state.get("steps", 0) + 1
    try:
        nxt = llm.with_structured_output(Route).invoke(
            [sys_msg] + list(state["messages"])).next
    except Exception as e:  # 🔶 소형 모델 대비 — 헤매면 정리하고 끝냅니다
        print(f"  [Supervisor {step}] ⚠️ 판단 실패 ({type(e).__name__}) → writer")
        nxt = "writer"
    print(f"  [Supervisor {step}] → {nxt}")
    return {"next": nxt, "steps": step}


def route(state: State) -> str:
    # ★ 종료 조건 두 겹: Supervisor 의 FINISH + 단계 상한
    if state["next"] == "FINISH" or state["steps"] >= MAX_STEPS:
        return "FINISH"
    return state["next"] if state["next"] in WORKERS else "FINISH"


# ── ② 워커 — 각자 도구 1~2개만 ★ ─────────────────────────────
def make_worker(name: str, tools: list, instruction: str):
    """🔶 워커 내부는 간이 구현입니다 (내부 순환 1회).

    정식으로는 각 워커를 **서브그래프**(13주차 ReAct 그래프)로 만들어 노드에 넣습니다.
    **수업 시간(18분) 제약상 단순화**한 것임을 학생에게 밝히십시오. ★

        research_graph = research_builder.compile()      # 그 자체로 완결된 에이전트
        main_builder.add_node("research", research_graph)  # ★ 노드로 넣는다
        # compile() 결과가 Runnable 이므로 노드가 될 수 있습니다
        # — 5주차 "체인도 부품이다" 가 그래프에서도 성립합니다 ★
    """
    bound = llm.bind_tools(tools) if tools else llm
    registry = {t.name: t for t in tools}

    def worker(state: State) -> dict:
        history = [SystemMessage(instruction)] + list(state["messages"])
        msg = bound.invoke(history)
        produced = [msg]

        # 도구 호출이 있으면 여기서 처리하고, 결과를 넣어 한 번 더 부른다
        calls = getattr(msg, "tool_calls", None) or []
        for call in calls:
            obj = registry.get(call["name"])
            if obj is None:
                continue
            produced.append(obj.invoke(call))  # ← 실행 주체는 여전히 우리 코드 ★

        if len(produced) > 1:
            produced.append(bound.invoke(history + produced))

        text = (produced[-1].content or "").strip()
        print(f"  [{name}] {text[:70]}")

        # ★ 관리자가 읽을 수 있게 '누가 무엇을 했는지' 를 남깁니다.
        #   워커의 원본 메시지를 그대로 쌓으면 tool_calls 짝이 어긋날 수 있습니다. 🔶
        return {"messages": [AIMessage(content=f"[{name}] {text}", name=name)]}

    return worker


builder = StateGraph(State)
builder.add_node("supervisor", supervisor)
builder.add_node("researcher",
                 make_worker("researcher", [search_docs],
                             "너는 문서 조사 담당이다. 검색 도구로 사실만 확인해 보고하라."))
builder.add_node("calculator",
                 make_worker("calculator", [multiply],
                             "너는 계산 담당이다. 계산 도구로 정확히 계산해 보고하라."))
builder.add_node("writer",
                 make_worker("writer", [],
                             "너는 작성 담당이다. 앞의 결과를 종합해 최종 답변을 작성하라."))

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route, {
    "researcher": "researcher", "calculator": "calculator",
    "writer": "writer", "FINISH": END,
})
for w in WORKERS:
    builder.add_edge(w, "supervisor")  # ★ 끝나면 관리자에게 복귀 = 순환

graph = builder.compile()

QUESTION = "휴학 최대 학기 수를 확인하고, 그 값에 6을 곱한 결과를 알려줘."
INPUTS = {"messages": [HumanMessage(QUESTION)], "steps": 0}
CONFIG = {"recursion_limit": RECURSION_LIMIT}


def main() -> None:
    print(f"모델: {TOOL_MODEL} / MAX_STEPS {MAX_STEPS} / recursion_limit {RECURSION_LIMIT}")
    print(f"\nQ: {QUESTION}\n")

    out = graph.invoke(INPUTS, CONFIG)

    print("\n" + "=" * 60)
    print("최종:", out["messages"][-1].content.strip()[:250])
    print(f"\nSupervisor 판단 횟수: {out['steps']}회 / 누적 메시지 {len(out['messages'])}개")
    print("=" * 60)

    print("""
관찰 ★★  — 질문 하나에 두 담당자가 필요하도록 설계했습니다

   [Supervisor 1] → researcher      (휴학 최대 학기 수를 조회)
   [researcher] 일반휴학은 통산 6개 학기까지
   [Supervisor 2] → calculator      (6 × 6 계산)
   [calculator] 36
   [Supervisor 3] → writer          (종합)
   [writer] 휴학 최대 학기 수는 6이며, 6을 곱하면 36입니다.
   [Supervisor 4] → FINISH

  | 관찰                    | 짚어줄 말                                    |
  | Supervisor 가 **여러 번** | 배분 → 실행 → **결과를 보고 다시 판단** ★      |
  | 각 워커의 도구가 1개뿐    | "9주차 원칙을 각자 지키면서 전체는 3개를 씁니다" ★★ |
  | **호출 횟수**            | 단일 에이전트보다 확실히 많다 ⚠️              |
  | Supervisor 가 헤매면     | 소형 모델의 한계 → **MAX_STEPS 로 방어**      |

📌 **LangSmith 추적을 꼭 열어 보게 하십시오.**
   **Run 개수와 총 토큰**이 13주차 단일 에이전트보다 얼마나 늘었는지 **숫자로** 확인.
   🔶 교수는 **비교 캡처**를 미리 준비해 두면 좋습니다. ★

⚖️ **결론: 멀티 에이전트는 정확도를 비용으로 삽니다.**
   7주차의 판단 틀(정확도 vs 토큰 vs 지연)이 여기서도 그대로 적용됩니다.
   **도구가 3개면 단일 에이전트가 낫습니다.** 나누는 것은 **역할이 정말 갈릴 때**입니다. ★
""")


if __name__ == "__main__":
    main()
