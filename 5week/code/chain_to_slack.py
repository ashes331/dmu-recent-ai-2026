"""[4교시 / 실습 6] 체인의 마지막 한 칸 — 결과를 슬랙으로 배달한다

새 개념은 없다. 3교시에서 배운 RunnableLambda 를 한 번 더 쓸 뿐이다.

    chain = prompt | llm | parser | RunnableLambda(to_slack)
                                    └───────┬────────┘
                                   평범한 파이썬 함수를 체인의 부품으로

★ 오늘의 요지
  슬랙 전송은 특별한 기능이 아니라 '그냥 함수 하나' 다.
  Runnable 규약(.invoke)을 만족하는 것은 무엇이든 | 로 이을 수 있다 — 3교시 §1-1.

⚠️ 부수효과(side effect) 단계의 규칙 : 받은 값을 그대로 return 한다
  return 을 빼면 None 이 흘러가 뒤에 이은 단계가 전부 깨진다.
  전송은 '곁다리로 하는 일' 이고, 체인의 본류는 계속 흘러야 한다.

실행:
    python chain_to_slack.py            # ① 가벼운 1단 체인 → 슬랙  (권장: 먼저 이것부터)
    python chain_to_slack.py full       # ② 3교시 분해 체인 → 슬랙  (LLM 5~6회, 수 분 소요)

전제:
    실습 5(send_slack_message.py)가 이미 성공해야 한다.
    슬랙 설정(①~④)이 안 끝났으면 이 파일도 똑같이 실패한다.
"""

import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama

from send_slack_message import send  # ← 실습 5 의 함수를 그대로 재사용 ★

MODEL = "gemma3:4b"
TEMP = 0


# ── 부수효과 부품 — 흘러온 값을 슬랙으로 보내고, 그대로 돌려준다 ★ ──
def to_slack(answer: str) -> str:
    send(f"*분석 결과가 나왔습니다*\n\n{answer}")
    return answer  # ⚠️ 이 줄을 지우면 뒤 단계가 None 을 받는다


notify = RunnableLambda(to_slack)  # 이 한 칸을 어느 체인 끝에든 붙일 수 있다


# ── ① 가벼운 체인 — 슬랙 연결만 확인한다 (LLM 1회) ──────────────
def run_simple() -> None:
    llm = ChatOllama(model=MODEL, temperature=TEMP)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "너는 요약 조교다. 세 문장 이내로 답하라."),
            ("human", "{topic} 에 대해 핵심만 정리해라."),
        ]
    )

    chain = prompt | llm | StrOutputParser() | notify  # ← 끝에 한 칸 추가

    print("=" * 60)
    print("[① 가벼운 체인] prompt | llm | parser | notify")
    print("=" * 60)

    answer = chain.invoke({"topic": "LCEL 파이프 연산자가 하는 일"})

    print("-" * 60)
    print("[체인이 돌려준 값]  ← to_slack 이 return 했기 때문에 살아 있다 ★")
    print(answer)


# ── ② 3교시 분해 체인에 붙인다 (LLM 5~6회) ──────────────────────
def run_full() -> None:
    # 임포트가 무거우므로 이 함수 안에서 불러온다
    from least_to_most import PROBLEM, chain  # 실습 3 의 결과물

    notified = chain | notify  # ← 체인 끝에 한 칸 추가. 이게 전부다 ★

    print("=" * 60)
    print("[② 분해 체인] least_to_most.chain | notify")
    print("원 문제:", PROBLEM)
    print("=" * 60)

    answer = notified.invoke({"problem": PROBLEM})

    print("=" * 60)
    print("[최종 답]")
    print(answer)
    print("=" * 60)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "simple"

    if mode == "full":
        run_full()
    else:
        run_simple()

    print("""
관찰 — 무엇을 볼 것인가

  관찰 항목                      짚어줄 말
  ────────────────────────────────────────────────────────────────
  터미널과 슬랙에 같은 내용      출력(output)과 전달(delivery)은 다른 문제다 ★
  체인 코드가 한 칸만 늘었다     Runnable 규약 하나로 무엇이든 이어붙는다 (3교시 §1-1)
  to_slack 이 값을 return       부수효과 단계는 받은 값을 그대로 흘려보낸다 ⚠️
  full 모드는 한참 걸린다        분해 1 + 하위 3~4 + 종합 1 = 5~6회 호출
  전송이 체인 안에서 일어난다    실패하면 체인 전체가 멈춘다 → 아래 '한 걸음 더'

💡 한 걸음 더
   · to_slack 의 return 을 지우고 뒤에 단계를 하나 더 이어 보라. 어떻게 깨지는가?
   · 슬랙 전송이 실패해도 체인은 계속 돌게 하려면? (to_slack 안에서 try/except 로 감싼다)
     — "알림 실패 때문에 분석 결과까지 잃을 것인가" 가 판단 기준이다
   · 중간 단계에도 notify 를 끼워 넣어 보라: prompt | llm | notify | parser
   · 실패했을 때만 슬랙으로 보내는 버전을 만들어 보라 (에러 알림 봇)

📌 다음 주(6주차 LangSmith)에는 이 호출들이 트리로 펼쳐집니다.
   to_slack 도 트리의 한 노드로 보입니다.
""")


if __name__ == "__main__":
    main()
