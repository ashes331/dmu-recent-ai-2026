"""[3교시 / 실습 3] ★ Lost in the Middle — 정답 문서의 '위치' 를 바꿔가며 본다

  핵심 질문: 관련 문서를 10개 넣으면 3개보다 잘 답합니까?

     프롬프트에 문서 10개를 넣었을 때, 모델이 실제로 반영하는 정도

     위치:   1    2    3    4    5    6    7    8    9   10
     반영:  ███  ██▓  ██   █▓   █    █    █▓   ██   ██▓  ███
            높음                 낮음 ⚠️                   높음
            └── 앞 ──┘      └─ 중간 ─┘        └── 뒤 ──┘

  ★ 정답이 5번째에 있으면 모델이 못 보고 지나갑니다.
    검색은 성공했는데 **답이 틀립니다.** 그리고 원인을 찾기가 매우 어렵습니다 —
    "문서는 제대로 가져왔는데 왜 틀리지?"

  ★ 실험 요령: **검색을 쓰지 않고 문서 순서를 직접 조작합니다.**
    검색에 맡기면 순서가 매번 달라져 실험이 성립하지 않습니다.

  ⚠️ 진단 순서가 하나 늘었습니다 (1교시 2-3 의 확장)
     ① 검색 결과에 답이 있는가?     → 없으면 **검색 문제**
     ② 있는데 틀렸다면 → **몇 번째에 있었는가?** ★ ← 오늘 추가
     ③ 그래도 아니면 → 프롬프트·모델 문제

  📌 결론 문장
     ***"검색이 정답을 가져왔다" 와 "모델이 그것을 봤다" 는 다른 이야기입니다.***

실행:
    python lost_in_middle.py             # 위치 실험 + 개수 실험
    python lost_in_middle.py --repeat 3  # ⚠️ 결과가 흔들릴 때 반복 측정 ★
"""

import sys

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from questions import LIM_ANSWER_DOC, LIM_ANSWER_KEY, LIM_QUESTION
from rag_common import get_llm

PROMPT = ChatPromptTemplate.from_messages([
    ("system", "아래 <context> 안의 문서들만 근거로 답하라. 없으면 '모름'이라고 답하라."),
    ("human", "<context>\n{context}\n</context>\n\n질문: {question}"),
])

# 관련 없는(그러나 **그럴듯한**) 방해 문서 ★
#   ⚠️ 방해 문서가 엉성하면 실험이 안 갈립니다.
#      같은 규정집의 '다른 조문' 이어야 모델이 실제로 헷갈립니다. 🔶
DISTRACTORS = [
    "제16조(복학) ① 휴학 기간이 만료된 학생은 그 다음 학기에 복학하여야 한다.",
    "제17조(조기 복학) ① 휴학 사유가 소멸한 학생은 기간 만료 전이라도 복학을 신청할 수 있다.",
    "제20조(제적) ① 정해진 기간에 등록을 완료하지 아니한 자는 제적한다.",
    "제21조(재입학) ① 제적된 자는 3년 이내에 1회에 한하여 재입학을 신청할 수 있다.",
    "제25조(재학 연한) ② 재학 연한은 수업 연한의 2배를 초과할 수 없다.",
    "제26조(학점 이수) ② 한 학기에 신청할 수 있는 학점은 21학점을 초과할 수 없다.",
    "제27조(계절 수업) ① 계절 수업 학점은 매 계절 6학점을 초과할 수 없다.",
    "제30조(성적 평가) ② 수업 시간의 4분의 1을 초과하여 결석하면 F 학점을 부여한다.",
    "제31조(재수강) ② 재수강한 교과목의 성적은 A0를 초과하여 부여할 수 없다.",
    "제35조(졸업 요건) ① 졸업에 필요한 학점은 120학점 이상으로 한다.",
    "제36조(학위 수여) ① 졸업이 인정된 자에게는 전문학사 학위를 수여한다.",
    "제13조(군 복무 휴학) ③ 입영 통지서 사본을 첨부하여 휴학원을 제출한다.",
]


def build(pos: int, n_docs: int = 10) -> str:
    """정답 문서를 pos 번째(1-based)에 끼워 넣는다."""
    docs = DISTRACTORS[: n_docs - 1].copy()
    docs.insert(pos - 1, LIM_ANSWER_DOC)
    return "\n\n".join(f"[문서 {i}] {d}" for i, d in enumerate(docs, 1))


def judge(answer: str) -> bool:
    """정답 판정 — 숫자가 들어 있는가 (단순하게 갑니다)"""
    return LIM_ANSWER_KEY in answer


def run_positions(chain, repeat: int) -> None:
    print("── 실험 ① 정답의 '위치' 를 바꾼다 (문서 10개 고정) ★ ──\n")
    print(f"  질문: {LIM_QUESTION}")
    print(f"  정답: {LIM_ANSWER_DOC}\n")

    for pos in (1, 5, 10):
        oks, last = 0, ""
        for _ in range(repeat):
            last = chain.invoke({"context": build(pos), "question": LIM_QUESTION})
            oks += judge(last)
        tag = " ← 중간 ★" if pos == 5 else ""
        rate = f"{oks}/{repeat}" if repeat > 1 else ("✅" if oks else "❌")
        print(f"  정답 위치 {pos:2d}번  →  {rate}  {last.strip()[:60]}{tag}")


def run_counts(chain, repeat: int) -> None:
    print("\n── 실험 ② 문서 '개수' 를 줄인다 (정답은 항상 중간) ★ ──\n")
    for k in (10, 5, 3):
        oks, last = 0, ""
        for _ in range(repeat):
            last = chain.invoke(
                {"context": build(max(1, k // 2), n_docs=k), "question": LIM_QUESTION}
            )
            oks += judge(last)
        rate = f"{oks}/{repeat}" if repeat > 1 else ("✅" if oks else "❌")
        print(f"  k={k:2d}  →  {rate}  {last.strip()[:60]}")


def main() -> None:
    repeat = 1
    if "--repeat" in sys.argv:
        repeat = int(sys.argv[sys.argv.index("--repeat") + 1])

    chain = PROMPT | get_llm() | StrOutputParser()

    run_positions(chain, repeat)
    run_counts(chain, repeat)

    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
결과 기록과 해석 ★

  | 정답 위치     | 답변 | 정답 여부 |     | 문서 개수 | 정답 여부 |
  | 1번 (앞)      |     |          |     | k=10     |          |
  | **5번 (중간)** ★ |  |          |     | k=5      |          |
  | 10번 (뒤)     |     |          |     | k=3      |          |

읽어낼 것

  1번·10번은 맞고 **5번은 틀림**   → **Lost in the Middle 확인** ★★
  k 를 줄이니 맞음                 → **적게 넣는 것이 답일 때가 있다**
  위치만 바꿨는데 답이 달라짐       → **검색 품질이 같아도 배치가 결과를 바꾼다** ★

대응 3가지 ★

  개수를 줄인다              k=10 → 3~5              가장 간단하고 효과적 ★
  재정렬해서 양끝에 배치      중요한 것을 1번과 마지막   2교시 Re-ranking
  압축한다                   관련 부분만 추출          2교시 Contextual Compression

⚖️ "많이 가져올수록 좋다" 는 직관이 틀립니다.
   k 를 늘리는 것은 **재현율(놓치지 않기)** 을 올리지만
   **정밀도(반영되기)** 를 떨어뜨립니다. **또 트레이드오프입니다.**

🔶 안 갈리면
   ① 문서 수를 늘리고 (10 → 15~20)
   ② 방해 문서를 **더 그럴듯하게** (같은 규정집의 다른 조문)
   ③ --repeat 3 으로 반복 측정 — LLM 은 비결정적입니다 (6주차 1교시) ★
   **차이가 안 나면 이 절이 통째로 의미를 잃습니다.** 수업 전날 반드시 확인하십시오.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
