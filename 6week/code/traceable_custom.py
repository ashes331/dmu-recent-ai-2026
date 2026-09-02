"""[3교시 / 실습 3] ★ @traceable — LangChain 밖의 내 함수도 트리에 올린다.

2교시에서 본 트리에는 LangChain 부품만 있었습니다. 내 코드는 안 보였습니다.

    raw    = open("review.txt").read()      # ← 트리에 안 나옴
    text   = preprocess(raw)                # ← 트리에 안 나옴  ★
    result = chain.invoke({"review": text}) # ← 이것만 나옴
    save(result)                            # ← 트리에 안 나옴

  핵심 질문: 전처리에서 텍스트를 잘못 잘라 먹었다면, 추적 화면으로 알 수 있습니까?

    상황                                    추적에 보이는가
    ────────────────────────────────────────────────────────
    체인이 이상한 답을 냄                   ✅
    체인에 들어간 입력이 이미 망가져 있었음  ❌ 안 보임 ★
    전처리가 5초 걸림                       ❌ 안 보임

⚠️ 이게 실무에서 가장 흔한 오진입니다.
   "모델이 이상하다" 고 몇 시간을 보고, 알고 보면 전처리에서 문서 절반이
   날아가 있던 경우입니다. 10주차 RAG 실습에서 반드시 겪게 됩니다.

실행:
    python traceable_custom.py          # 정상 (500자로 자름)
    python traceable_custom.py 50       # ★ 50자로 잘라 '전처리 버그' 를 만들어 본다
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from langsmith import traceable  # ★ langchain 이 아니라 langsmith  # noqa: E402

MODEL = "gemma3:4b"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 500  # ★ 50 으로 바꿔 보게 한다

# ── 체인 (5주차 방식 그대로) ────────────────────────────────────
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 고객 리뷰 분석기다. 장점과 단점을 각각 한 줄로 정리한다."),
        ("human", "다음 리뷰를 분석해라.\n\n{review}"),
    ]
)
chain = prompt | ChatOllama(model=MODEL, temperature=0) | StrOutputParser()


# ── @traceable — 데코레이터 한 줄 ★ ─────────────────────────────
@traceable(name="리뷰 전처리", run_type="tool")
def preprocess(raw: str) -> str:
    """공백·개행을 정리하고 정해진 길이로 자른다."""
    return raw.replace("\n", " ").strip()[:LIMIT]


@traceable(name="결과 후처리", run_type="tool")
def postprocess(text: str) -> dict:
    return {"length": len(text), "text": text}


@traceable(name="리뷰 분석 파이프라인")  # ★★ 전체를 감싼다
def run_pipeline(raw: str) -> dict:
    text = preprocess(raw)                     # ← 자식 Run ①
    result = chain.invoke({"review": text})    # ← 자식 Run ② (체인 트리 전체)
    return postprocess(result)                 # ← 자식 Run ③


# ★ run_pipeline 으로 전체를 감싼 것이 요령입니다.
#   감싸지 않으면 전처리·체인·후처리가 각각 별개의 Trace 로 흩어집니다.
#   하나로 묶어야 "이 요청 1건에서 무슨 일이 있었나" 로 읽힙니다.
#
#   인자          하는 일
#   ─────────────────────────────────────────────────────────
#   name=         트리에 표시될 이름 (없으면 함수 이름)
#   run_type=     Run 종류 — "tool" · "chain" · "retriever" 등
#   (인자·반환값)  자동으로 Input / Output 에 기록됨 ★
#
# ⚠️ 함수의 인자와 반환값이 그대로 기록됩니다.
#    개인정보가 인자로 들어가면 그대로 외부로 전송됩니다.
#    (1교시 2-5 의 보안 주의가 여기에도 적용됩니다)


RAW = """  이 무선 이어폰 배터리는
정말 오래갑니다. 한 번 충전하면 사흘은 쓰네요.
음질도 이 가격대에서는 훌륭한 편입니다.
다만 케이스가 좀 크네요. 주머니에 넣으면 불룩합니다.
그리고 통화 품질은 기대 이하였습니다. 상대방이 잘 안 들린다고 합니다.  """


def main() -> None:
    print("=" * 66)
    print(f"  @traceable 실습 — 전처리 길이 제한 LIMIT = {LIMIT}자")
    print("=" * 66)

    out = run_pipeline(RAW)

    print(f"  원문 길이     : {len(RAW)}자")
    print(f"  전처리 후 길이 : {min(len(RAW.replace(chr(10), ' ').strip()), LIMIT)}자")
    print("-" * 66)
    print(out["text"])
    print("=" * 66)

    if LIMIT < 100:
        print("""
⚠️ 방금 무슨 일이 일어났습니까?

   체인의 출력이 엉뚱해졌습니다. 리뷰의 뒷부분(케이스·통화 품질)이
   아예 모델에 가지 않았기 때문입니다.

   ★ 그런데 그 원인이 추적 화면의 '리뷰 전처리' Run 의 Output 에
     그대로 보입니다. 50자짜리 잘린 문자열이 실물로 찍혀 있습니다.

   "모델이 이상한 게 아니었다."
   이 장면을 한 번 겪으면 이 절이 완성됩니다. ★
""")

    print("""
추적 화면에서 이렇게 보입니다 ★

  Run: 리뷰 분석 파이프라인            ← @traceable (내 함수)
   ├─ Run: 리뷰 전처리                 ← @traceable  ★ 새로 보임
   ├─ Run: RunnableSequence            ← LangChain 체인 (2교시에 본 것)
   │    ├─ Run: ChatPromptTemplate
   │    └─ Run: ChatOllama
   └─ Run: 결과 후처리                 ← @traceable  ★ 새로 보임

무엇을 관찰할 것인가

  관찰 항목                짚어줄 말
  ──────────────────────────────────────────────────────────────
  내 함수가 트리에 나타남   "이제 전처리 버그도 여기서 잡습니다"
  전처리 Run 의 Output      잘린 결과가 실물로 보인다 ★
  파이프라인이 하나의 Trace  감싸지 않았으면 3개로 흩어졌을 것

💡 한 걸음 더:  python traceable_custom.py 50   로 다시 돌려 보십시오.

다음 단계 →  python tags_metadata.py
""")


if __name__ == "__main__":
    main()
