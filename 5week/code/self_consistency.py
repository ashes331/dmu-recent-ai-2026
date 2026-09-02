"""[3교시 / 실습 4] ★ Self-Consistency — N회 샘플링 후 다수결

   같은 질문 ──┬──▶ CoT 1 ──▶ 17
               ├──▶ CoT 2 ──▶ 17          batch() 로 한 줄 ★
               ├──▶ CoT 3 ──▶ 23
               ├──▶ CoT 4 ──▶ 17
               └──▶ CoT 5 ──▶ 17
                              │
                        다수결 ▼
                             17

   필요한 조건                      이유
   ───────────────────────────────────────────────────────────────
   temperature > 0  ★               0이면 5번 다 같은 답 → 다수결이 무의미
   답을 정확히 뽑아낼 수 있어야      문장에서 눈으로 찾으면 셀 수 없다
                                     → 구조화 출력(2교시) ★
   답이 갈리는 문제                  너무 쉬우면 5:0으로 끝나 아무것도 안 보인다 ⚠️

★ batch() 에 '같은 입력을 N개' 넣는 것이 이 실습의 요령이다.
    [{"question": Q}] * N   ← 이 한 줄이 Self-Consistency 의 구현이다.

🔶 사전 준비 필수: 답이 갈려야 의미가 있다.
   아래 QUESTIONS 후보를 미리 5회씩 돌려 보고, 표가 갈리는 것을 골라 배포할 것.
   전원 만장일치면 이 절이 밋밋해진다.

실행:
    python self_consistency.py 0        # ★ 먼저 이걸로 — 만장일치가 나온다
    python self_consistency.py          # 그다음 기본값 0.8
"""

import sys
from collections import Counter

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

MODEL = "gemma3:4b"
N = 5  # ⚠️ 로컬 GPU 여력을 고려해 5 정도로 제한
TEMP = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8  # ★ 0이면 다수결이 무의미하다
MAX_CONCURRENCY = 2  # ⚠️ 8GB VRAM 실습실 보호 — 2~3으로 제한 🔶

# 🔶 답이 갈리는 문제 후보 — 수업 전에 각각 5회씩 돌려 보고 하나를 고를 것
QUESTIONS = [
    # ① 산술 추론 — 중간에 미끄러지기 쉬운 다단계 계산
    "한 상자에 사과가 12개씩 들어 있다. 상자 7개를 사서 그중 5개를 이웃에게 나눠 주고, "
    "남은 사과의 3분의 1을 잼으로 만들었다. 잼으로 만들지 않고 남은 사과는 몇 개인가?",
    # ② 논리 퍼즐 — 조건을 순서대로 반영해야 함
    "A는 B보다 나이가 많고, C는 A보다 어리지만 B보다는 많다. "
    "D는 셋 중 누구보다도 어리다. 나이가 많은 순서대로 나열하면?",
    # ③ 비율·속도 — 단위 처리에서 갈리기 쉬움
    "어떤 일을 혼자 하면 갑은 6시간, 을은 12시간이 걸린다. "
    "둘이 함께 2시간 일한 뒤 을이 빠지면, 갑이 혼자 마무리하는 데 몇 시간이 더 걸리는가?",
]
QUESTION = QUESTIONS[0]


class Solution(BaseModel):
    """단계별 추론과 최종 답."""

    reasoning: str = Field(description="단계별 풀이 과정")
    answer: str = Field(description="최종 답만. 숫자면 단위 없이 숫자만")


# ★ answer 를 '단위 없이 숫자만' 으로 강제하는 것이 중요하다.
#   "17개" / "17 개" / "답은 17" 이 섞이면 Counter 가 다른 답으로 센다.


cot_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 문제 해결가다. 단계적으로 생각한 뒤 최종 답을 낸다."),
        ("human", "{question}"),
    ]
)

cot = cot_prompt | ChatOllama(model=MODEL, temperature=TEMP).with_structured_output(Solution)


def main() -> None:
    print("=" * 60)
    print(f"모델={MODEL}  temperature={TEMP}  N={N}")
    print("문제:", QUESTION)
    print("=" * 60)

    # ── ① 같은 입력을 N개 만들어 batch 로 넘긴다 ★ ──────────────
    results = cot.batch(
        [{"question": QUESTION}] * N,
        config={"max_concurrency": MAX_CONCURRENCY},  # 로컬 GPU 보호 ★
    )

    # ── ② 답만 뽑아 센다 ──────────────────────────────────────
    results = [r for r in results if r is not None]
    answers = [r.answer.strip() for r in results]

    for i, r in enumerate(results, 1):
        print(f"[{i}] 답={r.answer.strip():>10s}   근거={r.reasoning[:60]}...")

    votes = Counter(answers)
    final, count = votes.most_common(1)[0]

    print("=" * 60)
    print("표 분포 :", dict(votes))
    print(f"최종 답 : {final}   ({count}/{N} 표, {count / N * 100:.0f}%)")
    print(f"1회만 실행했다면 나왔을 답 : {answers[0]}   ← 운에 맡긴 결과")
    print("=" * 60)

    if len(votes) == 1:
        print("\n⚠️ 만장일치다. temperature 가 0이거나 문제가 너무 쉽다.")
        print("   '5번 돌렸는데 5표가 다 같습니다. 이게 다수결입니까?'")
        print("   → python self_consistency.py 0.8 로 다시 돌려 보라.")

    print("""
읽어낼 것

  관찰                    의미
  ────────────────────────────────────────────────────────────────
  temp=0 → 만장일치        샘플이 서로 달라야 다수결이 성립한다 ★
  소수 의견이 존재         CoT 1회 실행은 그 소수 의견을 뽑을 수도 있었다
  총 소요 시간             정확도를 N배의 비용으로 산 것 ⚠️
  표가 3:2로 갈릴 때       N을 늘려야 하는 신호 — 다만 비용도 함께 늘어난다

⚖️ 한계

  해결하는 것                    해결하지 못하는 것
  ────────────────────────────────────────────────────────────────
  추론 도중의 우연한 실수        모델이 '일관되게' 틀리는 경우 (만장일치 오답) ⚠️
  1회 실행의 운                  비용이 N배 — 모든 호출에 적용할 수 없다

  "다수결은 자주 틀리는 것을 걸러낼 뿐, 항상 틀리는 것은 못 걸러낸다."
  그건 7주차 평가(Evaluation)로 잡는다.

📌 적용 기준: "틀리면 비용이 큰 소수의 판단" 에만 쓴다.
   요약·번역에는 다수결을 쓰지 않는다 — 셀 수 있는 답이 없기 때문이다. ★
""")


if __name__ == "__main__":
    main()
