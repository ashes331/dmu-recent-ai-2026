"""[1교시 / 실습 1] ★★ 코드 수정 0줄 — 5주차 체인을 그대로 실행한다.

이 파일에는 추적 코드가 한 줄도 없습니다.
LangSmith 를 import 하지도 않았고, 콜백을 붙이지도 않았습니다.

    바뀐 것은 .env 에 넣은 환경변수 3줄뿐입니다.  ★
        LANGSMITH_TRACING=true
        LANGSMITH_API_KEY=lsv2_pt_...
        LANGSMITH_PROJECT=week06-tracing

    아래 체인 정의는 5주차 least_to_most.py 를 그대로 옮긴 것입니다.
    ⚠️ 단 하나 다른 점: load_dotenv() 두 줄이 맨 위에 추가되었습니다.
       5주차 파일에는 .env 가 필요 없었기 때문입니다.
       학생 저장소에서는 week05/least_to_most.py 상단에 이 두 줄만 넣고
       그대로 돌려도 됩니다 — 그게 더 좋은 시연입니다. ★

   ① 비결정성    → 실행되는 모든 것이 자동으로 '기록' 된다
   ② 다단계      → 중첩 실행이 '트리' 로 펼쳐진다
   ③ 숨은 프롬프트 → 모델에 실제로 간 '최종 문자열' 이 보인다

실행:
    python trace_on.py

실행 후:
    smith.langchain.com → Projects → week06-tracing → 방금 실행이 목록에 있다 ★
    (트리를 펼쳐 보는 것은 2교시입니다. 여기서는 "기록됐다" 까지만!)
"""

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 파일 맨 위. 아래에 있으면 라이브러리가 이미 값을 읽은 뒤다.

# ↓↓↓ 여기부터는 5주차 least_to_most.py 그대로입니다 — 한 글자도 고치지 않았습니다 ↓↓↓

from typing import List  # noqa: E402

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.runnables import RunnableLambda, RunnablePassthrough  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

MODEL = "gemma3:4b"
TEMP = 0  # ★ 분해·풀이는 낮은 온도

PROBLEM = (
    "한 카페가 오후 시간대 매출만 계속 줄고 있다. "
    "원인을 진단하고 개선안을 우선순위와 함께 제시하라."
)

llm = ChatOllama(model=MODEL, temperature=TEMP)


# ── ① 분해기 ────────────────────────────────────────────────────
class SubQuestions(BaseModel):
    """원 문제를 풀기 위해 순서대로 답해야 할 하위 질문들."""

    questions: List[str] = Field(description="쉬운 것부터 어려운 순서로 3~4개")


decompose_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 문제를 잘게 쪼개는 조교다. 문제를 직접 풀지 마라."),
        ("human", "다음 문제를 풀기 위해 순서대로 답해야 할 하위 질문으로 나눠라.\n\n{problem}"),
    ]
)
decomposer = decompose_prompt | llm.with_structured_output(SubQuestions)


# ── ② 풀이기 ────────────────────────────────────────────────────
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

# ★★ 2교시에서 이 prompt 의 Run 을 열어 봅니다.
#    코드에는 "{solved}" 라고만 적혀 있지만, 세 번째 하위 질문을 풀 때
#    모델이 실제로 받은 것은 1,000자가 넘는 실물 문자열입니다.
#    그게 1교시에서 말한 '숨은 프롬프트' 이고, 오늘 해결할 문제입니다.


# ── ③ 순서대로 푸는 반복문 ──────────────────────────────────────
def solve_in_order(data: dict) -> dict:
    problem = data["problem"]
    solved: List[str] = []

    for i, q in enumerate(data["subs"].questions, 1):
        answer = solver.invoke(
            {
                "problem": problem,
                "solved": "\n\n".join(solved) or "(아직 없음)",  # ← 누적된다 ★
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


# ── ⑤ 전부 파이프로 잇는다 ──────────────────────────────────────
chain = (
    RunnablePassthrough.assign(subs=decomposer)
    | RunnableLambda(solve_in_order)
    | final_prompt
    | llm
    | StrOutputParser()
)

# ↑↑↑ 여기까지 5주차 그대로 ↑↑↑


def main() -> None:
    print("=" * 60)
    print("원 문제:", PROBLEM)
    print("=" * 60)

    answer = chain.invoke({"problem": PROBLEM})  # ← 1회 = 1 trace ★

    print("=" * 60)
    print("[최종 답]")
    print(answer)
    print("=" * 60)
    print("""
이제 브라우저로 갑니다 ★

    smith.langchain.com  →  좌측 Projects  →  week06-tracing
        └ 방금 실행이 목록에 한 줄로 찍혀 있습니다.

🎯 오늘 1교시의 목표는 이 장면 하나입니다.
   "내가 아무것도 안 했는데 다 기록돼 있다."
   코드는 5주차 그대로이고, 추가한 것은 환경변수 3줄뿐입니다.

   ⚠️ 트리를 펼쳐 보는 것은 2교시입니다. 여기서는 "기록됐다" 까지만!

목록에 아무것도 없다면

  증상                        원인                       조치
  ─────────────────────────────────────────────────────────────────
  목록이 비어 있음            LANGSMITH_TRACING≠true     python check_langsmith.py
  인증 오류                   키 앞뒤 공백·따옴표        .env 에서 따옴표 제거
  .env 를 고쳤는데 안 바뀜 ★  셸에 옛 값이 남아 있음      터미널을 새로 열고 재실행
  접속 자체가 안 됨           프록시·백신                python net_check.py
""")


if __name__ == "__main__":
    main()
