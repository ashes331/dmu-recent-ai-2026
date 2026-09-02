"""[2교시 / 실습 2] ★★ 조건부 엣지 — 질문 유형을 분류해 서로 다른 경로로 보낸다

                    ┌─────────────┐
      START ───────▶│  classify   │
                    └──────┬──────┘
                           │  ★ 라우팅 함수가 '문자열' 을 돌려준다
              ┌────────────┼────────────┐
       "math" │      "rag" │    "chat"  │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ calc     │ │ search   │ │ chat     │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             └────────────┼────────────┘
                          ▼
                         END

  ★ 라우팅 함수는 노드가 아닙니다.
    상태를 **읽기만** 하고 **다음 목적지 이름**을 돌려줍니다.
    여기서 LLM 을 부르지 마십시오 — 분류는 앞 노드(classify)가 이미 했습니다.

  ★ Literal 타입으로 분류 결과를 제한한 것에 주목하십시오.
    5주차 구조화 출력이 여기서 값을 합니다 —
    모델이 "수학문제" 같은 엉뚱한 문자열을 돌려주면
    **라우팅 딕셔너리에 없어서 그래프가 죽습니다.** 스키마가 그걸 막습니다. ★

  📌 **과제 5가 정확히 이 실습의 확장입니다.** 오늘 코드를 잘 남겨 두십시오.
     그리고 **미니 프로젝트의 골격**으로 쓰십시오 (13주차 중간 점검에서 확인합니다). ★

실행:
    python branch_graph.py
"""

import os
import sys
from typing import Literal, TypedDict

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

MODEL = os.getenv("MODEL", "gemma3:4b")
llm = ChatOllama(model=MODEL, temperature=0)

ROUTES = ("math", "rag", "chat")


class State(TypedDict):
    question: str
    category: str
    answer: str


# ── 분류 노드 — 5주차 구조화 출력을 쓴다 ★ ───────────────────
class Category(BaseModel):
    """질문 유형."""

    category: Literal["math", "rag", "chat"] = Field(
        description="계산이 필요하면 math, 문서 검색이 필요하면 rag, 그 외 잡담은 chat")


def classify(state: State) -> dict:
    p = ChatPromptTemplate.from_template("질문을 분류하라: {q}")
    try:
        r = (p | llm.with_structured_output(Category)).invoke({"q": state["question"]})
        category = r.category
    except Exception as e:  # 🔶 소형 모델은 구조화 출력에서도 흔들립니다
        print(f"  [분류] ⚠️ 실패 ({type(e).__name__}) → 기본 경로로 보냅니다")
        category = "chat"
    print(f"  [분류] {category}")
    return {"category": category}


# ── 경로별 노드 ─────────────────────────────────────────────
def calc(state: State) -> dict:
    p = ChatPromptTemplate.from_template("계산 문제다. 단계적으로 풀어라: {q}")
    return {"answer": (p | llm | StrOutputParser()).invoke({"q": state["question"]})}


def search(state: State) -> dict:
    # 🔶 11주차 retriever 를 붙이면 그대로 RAG 경로가 됩니다 ★
    #    from rag_common import load_store
    #    docs = load_store().as_retriever(search_kwargs={"k": 3}).invoke(state["question"])
    return {"answer": "[검색 경로] 문서를 찾아 답합니다 — 11주차 retriever 연결 지점"}


def chat(state: State) -> dict:
    p = ChatPromptTemplate.from_template("친근하게 한두 문장으로 답하라: {q}")
    return {"answer": (p | llm | StrOutputParser()).invoke({"q": state["question"]})}


# ── 라우팅 ★ ────────────────────────────────────────────────
def route(state: State) -> str:
    """다음에 갈 노드의 '이름' 을 문자열로 돌려준다. ★

    ⚠️ 분류가 틀리면 경로 전체가 틀립니다.
       소형 모델의 분류 실패에 대비해 **기본 경로(fallback)** 를 두는 것이 안전합니다.
    """
    return state["category"] if state["category"] in ROUTES else "chat"


builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("calc", calc)
builder.add_node("search", search)
builder.add_node("chat", chat)

builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify",  # 이 노드 다음에
    route,  # 이 함수로 판단해서
    {"math": "calc", "rag": "search", "chat": "chat"},  # 이 노드로 간다
)
for n in ("calc", "search", "chat"):
    builder.add_edge(n, END)

graph = builder.compile()


def main() -> None:
    print(f"모델: {MODEL}\n")

    # ── 서로 다른 경로를 타는 입력 3개 ★ ────────────────────
    for q in ["357 곱하기 4891은?",
              "우리 학교 휴학 규정 알려줘",
              "오늘 기분이 좀 별로야"]:
        print(f"\nQ: {q}")
        out = graph.invoke({"question": q})
        print(f"   경로: {out['category']}")
        print("A:", out["answer"].strip()[:100].replace("\n", " "))

    print("""

관찰과 확장 ★

  입력에 따라 **다른 노드가 실행됨**        분기가 실제로 동작 ★
  실행되지 않은 경로는 **비용 0**           11주차의 "인사에도 검색이 도는" 낭비 해결의 실마리 ★
  라우팅 함수가 문자열을 반환               노드가 아니라 **판단**이다

  ⚠️ 분류가 틀리면 경로 전체가 틀립니다.
     route() 에 기본 경로(fallback)를 넣어 두었습니다 —
     모델이 이상한 값을 내도 그래프가 죽지 않습니다. ★

  💡 13주차 연결: search 노드에 **11주차 retriever** 를 꽂으면
     그대로 **Agentic RAG 의 뼈대**가 됩니다.
     "검색이 필요한지 스스로 판단" 이 이것입니다. ★

  📌 **과제 5 = 이 실습의 확장.** 그리고 **미니 프로젝트의 골격**으로 쓰십시오.
     ⚠️ 별도로 만들면 남은 2주에 완주가 어렵습니다.
""")


if __name__ == "__main__":
    main()
