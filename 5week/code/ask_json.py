"""[1교시 / 1-5] 확인 A — "JSON으로 답해줘" 는 정말 JSON으로 오는가

프롬프트로 형식을 '부탁'했을 때 무엇이 오는지 눈으로 본다.
10번 돌리면 아래 다섯 가지가 섞여 나온다.

    ① {"product": "무선 이어폰", "rating": 4, "summary": "..."}   ✅
    ② 물론이죠! 분석 결과는 다음과 같습니다: {...}                 ❌ 앞말
    ③ ```json ... ```                                             ❌ 코드펜스
    ④ {"product": "...", "rating": "4점", ...}                     ❌ 타입 틀림
    ⑤ {"제품": "...", ...}                                         ❌ 필드명 틀림

⚠️ ②③은 json.loads() 에서 즉시 터진다 — 바로 안다.
   ④⑤는 파싱이 '성공'한다. 그리고 한참 뒤 data["rating"] + 1 같은 줄에서 터진다.
   → 조용한 실패. 원인 추적이 어렵다.

★ temperature 가 0이 아니다. 0이면 10번 다 같은 답이 나와 흔들림이 안 보인다.

🔶 이 시연은 "실패가 나와야" 의미가 있다. 수업 전 실습실 PC에서 10~20회 돌려
   실패가 실제로 섞이는지 확인할 것. 너무 잘 나오면 REVIEW 를 애매하게 만들거나
   요구 필드를 4~5개로 늘린다.

실행:
    python ask_json.py
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

MODEL = "gemma3:4b"
TEMP = 0.7  # ★ 0이 아님 — 형식이 흔들리는 장면을 봐야 한다
N = 10

REVIEW = "이 무선 이어폰 배터리는 정말 오래갑니다. 다만 케이스가 좀 크네요."


def main() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "너는 리뷰 분석기다. 반드시 JSON으로만 답하라. 설명을 덧붙이지 마라."),
            ("human", "다음 리뷰를 분석해라. 필드는 product, rating(1~5 정수), summary 다.\n\n{review}"),
        ]
    )
    llm = ChatOllama(model=MODEL, temperature=TEMP)

    chain = prompt | llm | StrOutputParser()

    for i in range(N):
        print(f"--- {i + 1}회 " + "-" * 45)
        print(chain.invoke({"review": REVIEW})[:200])

    print()
    print("=" * 60)
    print("""
관찰 — 무엇이 섞여 나왔는가

  유형                        예                              언제 터지나
  ────────────────────────────────────────────────────────────────────
  ① 정상                      {"product": ..., "rating": 4}   —
  ② 앞말 붙임                 물론이죠! {...}                  json.loads() 즉시
  ③ 코드펜스                  ```json ... ```                  json.loads() 즉시
  ④ 타입 틀림  ⚠️             "rating": "4점"                  한참 뒤 ★
  ⑤ 필드명 틀림 ⚠️            "제품": ...                      한참 뒤 ★

프롬프트를 더 강하게 쓰면(반드시·절대·오직 JSON만) 실패율은 조금 줄어든다.
그러나 0이 되지는 않는다. 부탁은 부탁이기 때문이다.

  📌 부탁은 확률이고, 스키마는 계약이다.
     → 2교시 structured.py / ab_failrate.py 에서 숫자로 확인한다.
""")
    print("=" * 60)


if __name__ == "__main__":
    main()
