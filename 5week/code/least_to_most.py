"""[3교시 / 실습 3] ★★ Least-to-Most — 나누고 · 순서대로 풀고 · 합친다

❌ 한 번에:
   "이 제품 리뷰 50건을 읽고, 반복되는 불만을 찾고, 그 불만의 원인을 추정하고,
    개선 우선순위를 정해서 보고서를 써라."
   → 앞의 지시를 하다가 뒤를 잊는다 / 근거 없이 결론부터 쓴다 / 중간을 검증할 수 없다

✅ 나눠서 (Least-to-Most):
   ① 반복되는 불만은 무엇인가?          ← 쉽다. 사실 추출
        │  (①의 답을 근거로)
   ② 각 불만의 원인은?                  ← ①이 있어야 답할 수 있다
        │  (①②의 답을 근거로)
   ③ 개선 우선순위는?                   ← ①②가 있어야 답할 수 있다
        ▼
   ④ 종합 보고서

   얻는 것 : 정확도(앞 결과가 근거) / 검증 가능성(어디서 틀렸는지 보임) / 재사용
⚠️ 대가도 있다 : 호출이 1회 → N+2회. 시간과 비용이 배로 든다.
   "나눌수록 좋다" 가 아니라 "한 번에 안 되는 문제만 나눈다".

★ 이 파일이 6주차 LangSmith 실습의 대상이다.
  단계가 여러 개여서 LangSmith 추적 화면이 풍성하게 나온다. 반드시 커밋할 것.

실행:
    python least_to_most.py           # 로컬 Ollama (gemma3:4b)
    python least_to_most.py openai    # (추가) OpenAI gpt-4o-mini — .env 에 OPENAI_API_KEY 필요
"""

import os
import sys
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

load_dotenv()  # (추가) .env 에서 OPENAI_API_KEY 를 읽는다

MODEL = "gemma3:4b"
OPENAI_MODEL = "gpt-4o-mini"  # (추가) python least_to_most.py openai 로 실행할 때
TEMP = 0  # ★ 분해·풀이는 낮은 온도 (Self-Consistency 는 반대)

PROBLEM = (
    "한 카페가 오후 시간대 매출만 계속 줄고 있다. "
    "원인을 진단하고 개선안을 우선순위와 함께 제시하라."
)


# (추가) 모델 고르기 — 바뀌는 것은 llm 한 줄뿐이고, 아래 체인은 그대로다 ★
def build_llm():
    if len(sys.argv) > 1 and sys.argv[1] == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            sys.exit("[중단] OPENAI_API_KEY 가 없습니다. .env 에 키를 넣고 다시 실행하세요.")
        from langchain_openai import ChatOpenAI  # 키가 있을 때만 불러온다

        print(f"[모델] OpenAI {OPENAI_MODEL}")
        return ChatOpenAI(model=OPENAI_MODEL, temperature=TEMP)
    print(f"[모델] 로컬 {MODEL}")
    return ChatOllama(model=MODEL, temperature=TEMP)


llm = build_llm()


# ── ① 분해기 — 하위 질문 목록을 '구조화 출력' 으로 받는다 ★ ─────
class SubQuestions(BaseModel):
    """원 문제를 풀기 위해 순서대로 답해야 할 하위 질문들."""

    # (추가) min_length·max_length — 없으면 작은 모델이 빈 목록 [] 을 돌려준다
    #        (빈 목록도 스키마상 '맞는 답' 이라서). 개수를 스키마로 강제한다 ★
    questions: List[str] = Field(
        description="쉬운 것부터 어려운 순서로 3~4개", min_length=3, max_length=4
    )


decompose_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 문제를 잘게 나누는 조교다. 문제를 직접 풀지 마라."),
        ("human", "다음 문제를 풀기 위해 순서대로 답해야 할 하위 질문으로 나눠라.\n\n{problem}"),
    ]
)
decomposer = decompose_prompt | llm.with_structured_output(SubQuestions)

print("**** decomposer : ",decomposer)
# ⚠️ 분해 결과가 엉망일 때 고칠 곳은 코드가 아니라 SubQuestions 의 description 이다.
#    (2교시에서 말한 "description 이 곧 프롬프트")


# ── ② 풀이기 — 하위 질문 하나를 푼다 ────────────────────────────
solve_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 문제 해결 조교다. 앞서 푼 결과를 근거로 이번 질문에만 짧게 답하라."),
        (
            "human",
            "원 문제: {problem}\n\n지금까지 푼 것:\n{solved}\n\n이번 질문: {question}",
        ),
    ]
)
solver = solve_prompt | llm | StrOutputParser()


# ── ③ 순서대로 푸는 반복문을 '부품' 으로 만든다 ★ ───────────────
def solve_in_order(data: dict) -> dict:
    problem = data["problem"]
    solved: List[str] = []

    for i, q in enumerate(data["subs"].questions, 1):
        answer = solver.invoke(
            {
                "problem": problem,
                "solved": "\n\n".join(solved) or "(아직 없음)",  # ← 앞 결과를 넘긴다 ★
                "question": q,
            }
        )
        solved.append(f"Q{i}. {q}\nA{i}. {answer}")
        print("─" * 60)
        print(solved[-1])

    return {"problem": problem, "solved": "\n\n".join(solved)}


# ── ④ 종합기 ────────────────────────────────────────────────────
final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 최종 답변자다. 하위 풀이만을 근거로 답하라."),
        ("human", "원 문제: {problem}\n\n하위 풀이:\n{solved}\n\n최종 답을 정리해라."),
    ]
)


# ── ⑤ 전부 파이프로 잇는다 ★★ ──────────────────────────────────
chain = (
    RunnablePassthrough.assign(subs=decomposer)  # {"problem"} → {"problem", "subs"}
    | RunnableLambda(solve_in_order)  # → {"problem", "solved"}
    | final_prompt
    | llm
    | StrOutputParser()
)

#  {"problem"}
#       │
#       ├─ assign(subs=decomposer) ──▶ {"problem", "subs"}      ← 원본 보존 ★
#       │
#       ├─ RunnableLambda(solve_in_order) ──▶ {"problem", "solved"}
#       │        └ 내부에서 solver 를 하위 질문 수만큼 invoke (순차)
#       │
#       └─ final_prompt | llm | parser ──▶ 최종 답(str)


def main() -> None:
    print("=" * 60)
    print("원 문제:", PROBLEM)
    print("=" * 60)

    answer = chain.invoke({"problem": PROBLEM})

    print("=" * 60)
    print("[최종 답]")
    print(answer)
    print("=" * 60)
    print("""
관찰 — 무엇을 볼 것인가

  관찰 항목                    짚어줄 말
  ────────────────────────────────────────────────────────────────
  하위 질문이 매번 조금씩 다름  분해도 모델이 하는 일 — 완전히 고정되지 않는다
  solved 가 누적됨              앞 답이 뒤 질문의 '근거' 로 들어가는 것이 핵심 ★
  중간 출력이 화면에 보임       어디서 틀렸는지 추적 가능
                                → 다음 주 LangSmith 가 이걸 자동으로 해 준다
  호출 횟수                     분해 1 + 하위 3~4 + 종합 1 = 5~6회 ⚠️
  assign 이 없으면              problem 이 사라져 뒷단계가 깨진다 (일부러 지워 보여도 좋다)

💡 한 걸음 더: 같은 문제를 '한 번에' 묻는 단일 프롬프트와 나란히 실행해 비교하라.
   "나눈 쪽이 근거가 있다" 가 눈으로 보이면 이 절이 완성된다.

📌 이 체인이 6주차 LangSmith 실습의 대상이다. 반드시 커밋할 것.
""")


if __name__ == "__main__":
    main()
