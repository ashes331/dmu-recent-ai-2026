"""[3교시 / 실습 3] ★★ Reflection 루프 — 생성 → 자기 평가 → 재작성

              ┌──────────────────────────┐
              ▼                          │
   START ─▶ [generate] ─▶ [evaluate] ────┤ "revise"
                              │
                              └─────────▶ END   "end"

  ★ LCEL 로는 아예 못 쓰던 것이 여기서는 딕셔너리 한 줄입니다.
    파이프(|)는 방향이 하나뿐이라 **되돌아가는 화살표를 쓸 문법이 없습니다.**

  ⚠️⚠️ 종료 조건은 두 겹으로 겁니다.

     ① 논리적 종료   상태에 attempts 를 두고 N회 넘으면 END    우리가 설계 ★
     ② 안전망        recursion_limit                        프레임워크의 강제 차단

     recursion_limit 만 믿으면 안 됩니다. 그건 **에러를 내며 멈추는** 장치입니다.
     **정상 종료는 ①로 설계해야** 합니다. ②는 버그가 있을 때를 대비한 것입니다.

  ★ attempts 는 **체인에는 둘 자리가 없던 값**입니다.
    1교시 2-2 ③에서 말한 "상태가 필요하다" 가 여기서 실체가 됩니다.

  ★★ 5주차 Self-Consistency 와 대비

     |          | Self-Consistency (5주) | **Reflection (오늘)**    |
     | 구조     | **병렬**               | **순환** ★               |
     | 방식     | 여러 개를 뽑아 **투표**  | 하나를 **반복해서 다듬음** |
     | 구현     | batch()                | **그래프 엣지**           |
     | 적합     | 답이 하나로 정해진 문제  | **정답이 없는** 문제 ★    |
     | 비용     | N배 (한 번에)           | 반복 횟수만큼 (점증)      |

     **"기법이 실행 구조를 요구한다" 의 결정적 예시입니다.**
     다수결은 병렬이 없으면 못 하고, Reflection 은 순환이 없으면 못 합니다.

  ⚠️ 로컬 모델 주의
     반복 1회 = LLM 호출 2회 (생성 + 평가)
     반복 3회 = 6회 호출 × 30명 = 180회   ⚠️ 실습실 GPU 부하
     → 반복 상한 2~3회 · recursion_limit 8~10 · **이분 판정(예/아니오)**

실행:
    python reflection.py
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
MAX_ATTEMPTS = int(os.getenv("WEEK12_MAX_ATTEMPTS", "3"))  # ① 논리적 종료 ★
RECURSION_LIMIT = int(os.getenv("WEEK12_RECURSION_LIMIT", "10"))  # ② 안전망 ★

llm = ChatOllama(model=MODEL, temperature=0.3)

# 🔶 교수 사전 준비: **1회차 답변이 눈에 띄게 부실한 과제**를 고르십시오.
#    처음부터 잘 나오면 루프가 1회에 끝나 **의미가 사라집니다.** ★
#    요구사항을 조금 까다롭게 걸면 잘 갈립니다.
TOPIC = "고등학생에게 벡터 데이터베이스 설명하기"
REQUIREMENT = "정확히 3문장으로, 일상에서 볼 수 있는 구체적 예시를 하나 이상 포함해"

# 호출 수를 세어 '비용' 을 숫자로 보여줍니다 ★
CALLS = {"n": 0}


class State(TypedDict):
    topic: str
    draft: str
    critique: str
    passed: bool
    attempts: int


# ── ① 생성 노드 — 지적 사항이 있으면 반영한다 ★ ───────────────
def generate(state: State) -> dict:
    if state.get("critique") and state["critique"] != "OK":
        p = ChatPromptTemplate.from_template(
            "주제: {topic}\n\n이전 초안:\n{draft}\n\n"
            "지적 사항:\n{critique}\n\n지적 사항을 반영해 다시 작성하라. "
            "요구사항: {req}")
        text = (p | llm | StrOutputParser()).invoke({
            "topic": state["topic"], "draft": state["draft"],
            "critique": state["critique"], "req": REQUIREMENT})
    else:
        p = ChatPromptTemplate.from_template("주제 '{topic}'에 대해 {req} 소개 글을 써라.")
        text = (p | llm | StrOutputParser()).invoke(
            {"topic": state["topic"], "req": REQUIREMENT})

    CALLS["n"] += 1
    n = state.get("attempts", 0) + 1
    print(f"\n  [생성 {n}회차] {text.strip()[:70]}...")
    return {"draft": text.strip(), "attempts": n}


# ── ② 자기 평가 노드 — 이분 판정 ★ ───────────────────────────
class Critique(BaseModel):
    """초안 평가 결과."""

    passed: bool = Field(description="요구사항을 충족하면 true")
    critique: str = Field(description="부족한 점 한두 문장. 충족하면 'OK'")


def evaluate(state: State) -> dict:
    """★ 이분 판정으로 설계하는 이유: 7주차 LLM 판정자에서 배운 것과 같습니다.
    "충족하는가? 예/아니오" 가 소형 모델에서 5점 척도보다 훨씬 안정적입니다.
    """
    p = ChatPromptTemplate.from_template(
        "다음 글이 '{req} 소개하는지' 평가하라.\n\n주제: {topic}\n글:\n{draft}")
    try:
        r = (p | llm.with_structured_output(Critique)).invoke(
            {"topic": state["topic"], "draft": state["draft"], "req": REQUIREMENT})
        passed, critique = r.passed, r.critique
    except Exception as e:  # 🔶 구조화 출력 실패 시 — 루프를 멈추지 않게 처리
        print(f"  [평가] ⚠️ 실패 ({type(e).__name__}) → 통과로 처리하고 종료합니다")
        passed, critique = True, "OK (평가 실패)"

    CALLS["n"] += 1
    print(f"  [평가 {state['attempts']}회차] {'통과' if passed else '보완'} — {critique[:60]}")
    print(f"  (LLM 호출 누계: {CALLS['n']}회)")
    return {"passed": passed, "critique": critique}


# ── ③ 종료 판단 ★★ ─────────────────────────────────────────
def should_continue(state: State) -> Literal["revise", "end"]:
    if state["passed"]:
        return "end"  # 품질 충족
    if state["attempts"] >= MAX_ATTEMPTS:
        print(f"  ⚠️ {MAX_ATTEMPTS}회 도달 — 종료")
        return "end"  # ★ 횟수 상한 (① 논리적 종료)
    return "revise"


# ── ④ 조립 — 여기서 순환이 생긴다 ★ ──────────────────────────
builder = StateGraph(State)
builder.add_node("generate", generate)
builder.add_node("evaluate", evaluate)

builder.add_edge(START, "generate")
builder.add_edge("generate", "evaluate")
builder.add_conditional_edges(
    "evaluate", should_continue,
    {"revise": "generate", "end": END},  # ★ "generate" 로 되돌아간다 = 순환
)

graph = builder.compile()


def main() -> None:
    print(f"모델: {MODEL} / 반복 상한 {MAX_ATTEMPTS} / recursion_limit {RECURSION_LIMIT}")
    print(f"요구사항: {REQUIREMENT}")

    out = graph.invoke(
        {"topic": TOPIC, "attempts": 0, "critique": ""},
        config={"recursion_limit": RECURSION_LIMIT},  # ★ ② 안전망
    )

    print("\n" + "=" * 60)
    print(f"총 {out['attempts']}회 시도 / 통과 여부: {out['passed']} / "
          f"LLM 호출 {CALLS['n']}회")
    print("-" * 60)
    print(out["draft"])
    print("=" * 60)

    print("""
학생이 채울 표 ★

  | 회차 | 초안 요약 | 평가 | 호출 수 누계 |
  |  1   |          |     |      2      |
  |  2   |          |     |      4      |
  |  3   |          |     |      6      |

읽어낼 것 ★★

  2회차가 1회차보다 나아짐        **Reflection 이 작동** ★
  3회차는 별로 안 나아짐          **수확 체감** — 반복을 늘려도 한계가 있다 ★★
  호출이 회차당 2회씩 증가         **비용은 선형 증가** ⚠️
  자기 평가가 계속 "보완"          ⚠️ 평가 노드가 너무 엄격 — 종료가 안 됨
  1회차에 바로 "통과"              ⚠️ 평가 노드가 너무 관대 — 루프가 무의미

⚖️ **자기 평가의 딜레마를 반드시 짚으십시오.**
   **같은 모델이 쓰고 같은 모델이 채점합니다.**
   모델이 못 보는 결함은 **평가에서도 못 봅니다.**
   → 7주차 "판정자를 믿을 수 있는가" 와 정확히 같은 문제입니다. ★★
   실무에서는 **평가에 더 강한 모델**을 쓰거나 **규칙 기반 검사**를 섞습니다.

📌 결론 문장
   ***"반복하면 좋아집니다. 다만 무한히 좋아지지는 않고, 비용은 확실히 늘어납니다."***

🔶 1회차에 바로 통과해 버리면 REQUIREMENT 를 더 까다롭게 바꾸십시오.
   루프가 1회에 끝나면 이 실습의 의미가 사라집니다. ★
""")


if __name__ == "__main__":
    main()
