"""[참고 · OpenAI 전용] self_consistency_traced.py 의 OpenAI 판 — N회 샘플링 후 다수결을 gpt-4o-mini 로

원본: 6주차 code/self_consistency_traced.py (5주차 self_consistency.py 에 추적만 켠 사본)

    원본과 다른 점  ★
        모델             ChatOllama(gemma3:4b)  →  ChatOpenAI(gpt-4o-mini)
        MAX_CONCURRENCY  2 (8GB VRAM 보호)      →  5 (GPU 걱정 없음, 레이트리밋만 신경)
        max_tokens       없음                   →  상한을 둔다 (N배 비용 보호)
    프롬프트 · Solution 스키마 · pick() · 다수결은 그대로입니다.

   같은 질문 ──┬──▶ CoT 1 ──▶ 16
               ├──▶ CoT 2 ──▶ 24          batch() 로 한 줄 ★
               ├──▶ CoT 3 ──▶ 16
               ├──▶ CoT 4 ──▶ 16
               └──▶ CoT 5 ──▶ 16
                              │
                        다수결 ▼
                             16          (문제 ①, temperature 0.8 실제 출력, 2026-10-28)

★ LangSmith 기록 — 이 파일의 목적
    batch(5) = trace 5건. 모두 run_name 'self_consistency_openai', 태그 week09-openai 가 붙는다.
    Tags 필터 → 5건을 나란히 → 소수 의견(위 그림의 24) Run 을 열어 reasoning 을 읽는다 ★★

   필요한 조건                      이유
   ───────────────────────────────────────────────────────────────
   temperature > 0  ★               0이면 5번 다 같은 답 → 다수결이 무의미
   답을 정확히 뽑아낼 수 있어야      → 구조화 출력 ★
   답이 갈리는 문제                  너무 쉬우면 5:0으로 끝나 아무것도 안 보인다 ⚠️

⚠️ 큰 모델은 작은 모델보다 '덜 갈린다'.
   gemma3:4b 에서 갈리던 문제도 gpt-4o-mini 는 5:0 으로 끝나는 일이 흔하다.
   만장일치가 나오면 실패가 아니라 관찰 결과다 — 아래 QUESTIONS 의 다른 문제로 바꿔 보거나
   temperature 를 1.0~1.2 로 올려 본다.

준비:
    저장소 맨 위 .env 에  OPENAI_API_KEY=sk-...

실행:
    python self_consistency_openai.py 0        # ★ 먼저 이걸로 — 만장일치가 나온다
    python self_consistency_openai.py          # 그다음 기본값 0.8
    python self_consistency_openai.py 0.8 2    # 두 번째 인자 = 문제 번호 (0·1·2)

    ⚠️ 1회 실행 = 모델 호출 N(=5)번 = 5 traces. 실습 중에는 실행 2~3회 이내로.
"""

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 파일 맨 위. 아래에 있으면 라이브러리가 이미 값을 읽은 뒤다.

import os  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from collections import Counter  # noqa: E402

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.tracers.langchain import wait_for_all_tracers  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402  ← 원본은 langchain_ollama ★
from pydantic import BaseModel, Field  # noqa: E402

MODEL = "gpt-4o-mini"
N = 5
TEMP = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8  # ★ 0이면 다수결이 무의미하다
Q_INDEX = int(sys.argv[2]) if len(sys.argv) > 2 else 0
MAX_CONCURRENCY = 5  # 로컬 GPU 가 없으니 N 개를 한꺼번에 — 429 가 나면 2로 낮춘다
MAX_OUT = 500  # 호출 1번의 답 길이 상한 (토큰) — N배 비용 보호 ⚠️

# 답이 갈리기 쉬운 문제 후보 3개 — 원본과 같다
QUESTIONS = [
    # ① 산술 추론 — 중간에 틀리기 쉬운 다단계 계산
    "한 상자에 사과가 12개씩 들어 있다. 상자 7개를 사서 그중 5개를 이웃에게 나눠 주고, "
    "남은 사과의 3분의 1을 잼으로 만들었다. 잼으로 만들지 않고 남은 사과는 몇 개인가?",
    # ② 논리 퍼즐 — 조건을 순서대로 반영해야 함
    "A는 B보다 나이가 많고, C는 A보다 어리지만 B보다는 많다. "
    "D는 셋 중 누구보다도 어리다. 나이가 많은 순서대로 나열하면?",
    # ③ 비율·속도 — 단위 처리에서 갈리기 쉬움
    "어떤 일을 혼자 하면 갑은 6시간, 을은 12시간이 걸린다. "
    "둘이 함께 2시간 일한 뒤 을이 빠지면, 갑이 혼자 마무리하는 데 몇 시간이 더 걸리는가?",
]
QUESTION = QUESTIONS[Q_INDEX]
PROJECT = os.environ.get("LANGSMITH_PROJECT", "default")
TAGS = ["week09-openai", "self-consistency", MODEL]  # ★ LangSmith 필터용 라벨

# ⚠️ 설정 오류는 호출 전에 잡는다 — 이 파일의 목적은 'LangSmith 에 기록을 남기는 것' 이다
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("OPENAI_API_KEY 가 .env 에 없습니다. 저장소 맨 위 .env 를 확인하세요.")
if os.environ.get("LANGSMITH_TRACING", "").lower() != "true" or not os.environ.get("LANGSMITH_API_KEY"):
    raise SystemExit("추적이 꺼져 있습니다. .env 에 LANGSMITH_TRACING=true 와 LANGSMITH_API_KEY 를 넣으세요.")


class Solution(BaseModel):
    """단계별 추론과 최종 답."""

    reasoning: str = Field(description="단계별 풀이 과정")
    answer: str = Field(description="최종 답만. 숫자면 단위 없이 숫자 하나만 (예: 53). 풀이는 쓰지 않는다")


# ★ answer 를 '단위 없이 숫자만' 으로 강제하는 것이 중요하다.
#   "16개" / "16 개" / "답은 16" 이 섞이면 Counter 가 다른 답으로 센다.
#   gpt-4o-mini 는 스키마를 잘 지키는 편이지만, pick() 은 그대로 둔다 — 같은 코드로 두 모델을 비교하려고.


def pick(text: str) -> str:
    """answer 칸에서 셀 수 있는 답만 뽑는다 — 숫자가 있으면 마지막 숫자."""
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    return nums[-1] if nums else " ".join(text.split())[:30]


def one_line(text: str, width: int) -> str:
    """줄바꿈을 없애고 width 글자로 자른다 — 결과 화면을 한 줄로 유지."""
    text = " ".join(text.split())
    return text if len(text) <= width else text[:width] + "..."


cot_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 문제 해결가다. 단계적으로 생각한 뒤 최종 답을 낸다."),
        ("human", "{question}"),
    ]
)

llm = ChatOpenAI(model=MODEL, temperature=TEMP, max_tokens=MAX_OUT, timeout=60)  # ★ 바뀐 한 줄
cot = cot_prompt | llm.with_structured_output(Solution)


def main() -> None:
    print("=" * 60)
    print(f"모델={MODEL}  temperature={TEMP}  N={N}  LangSmith 프로젝트={PROJECT}  태그={TAGS[0]}")
    print("문제:", QUESTION)
    print("=" * 60)

    # ── ① 같은 입력을 N개 만들어 batch 로 넘긴다 ★ ──────────────
    t0 = time.perf_counter()
    results = cot.batch(
        [{"question": QUESTION}] * N,
        config={
            "max_concurrency": MAX_CONCURRENCY,
            "run_name": "self_consistency_openai",  # N건 모두 같은 이름 ★
            "tags": TAGS,
            "metadata": {"model": MODEL, "temperature": TEMP, "question_index": Q_INDEX, "n": N},
        },
    )
    elapsed = time.perf_counter() - t0
    wait_for_all_tracers()  # ★ 프로그램이 끝나기 전에 기록 전송을 마친다

    # ── ② 답만 뽑아 센다 ──────────────────────────────────────
    results = [r for r in results if r is not None]
    answers = [pick(r.answer) for r in results]

    for i, (r, a) in enumerate(zip(results, answers), 1):
        print(f"[{i}] 답={a:>6s}   원문={one_line(r.answer, 20):<23s}  근거={one_line(r.reasoning, 30)}")

    votes = Counter(answers)
    final, count = votes.most_common(1)[0]

    print("=" * 60)
    print("표 분포 :", dict(votes))
    print(f"최종 답 : {final}   ({count}/{N} 표, {count / N * 100:.0f}%)")
    print(f"1회만 실행했다면 나왔을 답 : {answers[0]}   ← 운에 맡긴 결과")
    print(f"걸린 시간 : {elapsed:.1f}초  (N={N}개를 동시에 {MAX_CONCURRENCY}개씩)")
    print("=" * 60)

    if len(votes) == 1:
        print("\n⚠️ 만장일치다. temperature 가 0이거나, 이 모델에게 문제가 쉽다.")
        print("   큰 모델일수록 잘 갈리지 않는다 — 그것도 관찰 결과다.")
        print("   → python self_consistency_openai.py 0.8 1   (다른 문제)")
        print("   → python self_consistency_openai.py 1.2     (온도를 올려서)")

    print(f"""
LangSmith 에서 확인 ★
    Projects → {PROJECT} → Tags 필터 week09-openai
    → 'self_consistency_openai' 가 {N}건 — 같은 입력, 다른 출력
    → 표가 갈렸다면 소수 의견 Run 을 열어 reasoning 을 읽는다""")

    print("""
읽어낼 것

  관찰                    의미
  ────────────────────────────────────────────────────────────────
  temp=0 → 만장일치        샘플이 서로 달라야 다수결이 성립한다 ★
  gemma 보다 덜 갈린다     모델이 강할수록 다수결로 얻는 이득이 줄어든다
  걸린 시간                동시 실행이라 N배는 아니지만, 비용(토큰)은 정확히 N배 ⚠️
  표가 3:2로 갈릴 때       N을 늘려야 하는 신호 — 다만 비용도 함께 늘어난다

⚖️ 한계 (원본과 같다)

  "다수결은 자주 틀리는 것을 걸러낼 뿐, 항상 틀리는 것은 못 걸러낸다."
  📌 적용 기준: "틀리면 비용이 큰 소수의 판단" 에만 쓴다.
""")


if __name__ == "__main__":
    main()
