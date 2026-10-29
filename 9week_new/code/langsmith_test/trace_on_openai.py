"""[참고 · OpenAI 전용] trace_on.py 의 OpenAI 판 — Least-to-Most 체인을 gpt-4o-mini 로 추적한다

원본: 6주차 code/trace_on.py (5주차 least_to_most.py 에 추적만 켠 사본)

    원본과 다른 점은 '모델 한 줄' 입니다.  ★
        ChatOllama(model="gemma3:4b")   →   ChatOpenAI(model="gpt-4o-mini")
    체인(분해기 → 풀이기 → 종합기)은 한 글자도 고치지 않았습니다.
    LangChain 은 모델을 갈아 끼워도 체인이 그대로 돈다 — 6주차 4교시 llm_backends.py 와 같은 이야기입니다.

    추적은 여전히 .env 의 LANGSMITH_* 3줄이 켭니다.
    더한 것은 '찾기 쉽게' 하는 config 한 줄뿐입니다 — run_name · tags · metadata (1교시 «태그와 메타데이터»).
        LangSmith 에서  Tags = week09-openai  로 필터하면 이 파일의 실행만 보입니다. ★

   Ollama 판과 비교해 볼 것
   ─────────────────────────────────────────────────────────────
   속도        로컬 4B 는 수십 초, gpt-4o-mini 는 대개 몇 초 ★
   토큰 수     LangSmith 에서 Run 마다 입력·출력 토큰이 찍힌다
               (로컬 모델은 비어 있는 경우가 있었다 — 6주차 README «토큰 수가 안 보임»)
   비용        1회 실행 = 모델 호출 5~6번. 몇 원 수준이지만 '내 키' 로 나간다 ⚠️

준비:
    저장소 맨 위 .env 에  OPENAI_API_KEY=sk-...   (4주차에 넣은 것)
    pip install langchain-openai   (requirements.txt 에 있음)

실행:
    python trace_on_openai.py

실행 후:
    smith.langchain.com → Projects → .env 의 LANGSMITH_PROJECT
    → Tags 필터  week09-openai  → 'least_to_most_openai' 한 줄 ★
    → 트리를 펼쳐 ChatOpenAI Run 의 토큰 수 · 지연을 Ollama 판과 비교해 본다
"""

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 파일 맨 위. 아래에 있으면 라이브러리가 이미 값을 읽은 뒤다.

import os  # noqa: E402
from typing import List  # noqa: E402

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.runnables import RunnableLambda, RunnablePassthrough  # noqa: E402
from langchain_core.tracers.langchain import wait_for_all_tracers  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402  ← 원본은 langchain_ollama ★
from pydantic import BaseModel, Field  # noqa: E402

MODEL = "gpt-4o-mini"  # 4·5·6주차와 같은 OpenAI 모델
TEMP = 0  # ★ 분해·풀이는 낮은 온도
MAX_OUT = 600  # 호출 1번의 답 길이 상한 (토큰) — 비용 상한 ⚠️

PROBLEM = (
    "한 카페가 오후 시간대 매출만 계속 줄고 있다. "
    "원인을 진단하고 개선안을 우선순위와 함께 제시하라."
)

PROJECT = os.environ.get("LANGSMITH_PROJECT", "default")
TAGS = ["week09-openai", "least-to-most", MODEL]  # ★ LangSmith 필터용 라벨

# ⚠️ 설정 오류는 호출 전에 잡는다 — 이 파일의 목적은 'LangSmith 에 기록을 남기는 것' 이다
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("OPENAI_API_KEY 가 .env 에 없습니다. 저장소 맨 위 .env 를 확인하세요.")
if os.environ.get("LANGSMITH_TRACING", "").lower() != "true" or not os.environ.get("LANGSMITH_API_KEY"):
    raise SystemExit("추적이 꺼져 있습니다. .env 에 LANGSMITH_TRACING=true 와 LANGSMITH_API_KEY 를 넣으세요.")

llm = ChatOpenAI(model=MODEL, temperature=TEMP, max_tokens=MAX_OUT, timeout=60)  # ★ 바뀐 한 줄


# ↓↓↓ 여기부터는 원본 trace_on.py(= 5주차 least_to_most.py) 그대로입니다 ↓↓↓

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

# ↑↑↑ 여기까지 원본 그대로 ↑↑↑


def main() -> None:
    print("=" * 60)
    print(f"모델={MODEL}  temperature={TEMP}  LangSmith 프로젝트={PROJECT}  태그={TAGS[0]}")
    print("원 문제:", PROBLEM)
    print("=" * 60)

    answer = chain.invoke(  # ← 1회 = 1 trace ★
        {"problem": PROBLEM},
        config={
            "run_name": "least_to_most_openai",  # 목록에 보이는 이름
            "tags": TAGS,
            "metadata": {"model": MODEL, "temperature": TEMP, "source": "6주차 trace_on.py"},
        },
    )
    wait_for_all_tracers()  # ★ 프로그램이 끝나기 전에 기록 전송을 마친다

    print("=" * 60)
    print("[최종 답]")
    print(answer)
    print("=" * 60)
    print("""
이제 브라우저로 갑니다 ★

    smith.langchain.com  →  좌측 Projects  →  .env 의 LANGSMITH_PROJECT
        └ Tags 필터 week09-openai → 'least_to_most_openai' 를 열고 트리를 펼친다
          ChatOpenAI Run 마다  토큰 수(입력/출력) · 지연  이 찍혀 있다 ★

   Ollama 판(6주차 trace_on.py)과 나란히 보면
     ① 트리 모양은 같다     — 체인이 같으니까
     ② 지연·토큰은 다르다   — 모델만 바뀌었으니까

목록에 아무것도 없다면

  증상                        원인                       조치
  ─────────────────────────────────────────────────────────────────
  목록이 비어 있음            LANGSMITH_TRACING≠true     .env 확인
  401 / invalid_api_key       OPENAI_API_KEY 오타·폐기   키 앞뒤 공백·따옴표 제거
  429 / insufficient_quota    OpenAI 잔액·한도 소진      platform.openai.com 에서 확인
  .env 를 고쳤는데 안 바뀜 ★  셸에 옛 값이 남아 있음      터미널을 새로 열고 재실행
""")


if __name__ == "__main__":
    main()
