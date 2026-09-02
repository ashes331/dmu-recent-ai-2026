"""[3교시 / 1-3] ★★ 태그·메타데이터 — 실험을 구분한다.

  핵심 질문: 프롬프트를 고쳐 다시 돌렸습니다. 목록에 실행이 20개 쌓여 있습니다.
             어느 게 고치기 전이고 어느 게 고친 후입니까?

     Traces 목록
     ├─ 14:32:10   ...    ← ???
     ├─ 14:33:02   ...    ← ???
     ├─ 14:35:41   ...    ← ???
          시각 말고는 구분할 방법이 없다 ⚠️

  해결: 실행할 때 꼬리표를 붙인다.

              태그(tags)              메타데이터(metadata)
    ─────────────────────────────────────────────────────────────
    형태      문자열 리스트           키-값 dict
    쓰임      목록에서 빠르게 필터    조건 검색·비교, 값 자체를 봄
    예        ["exp-A", "night-run"]  {"temperature": 0.8, "k": 5}

★★ 왜 지금 이걸 배우는가
   다음 주 7주차의 주제가 "바꾼 게 정말 좋아졌는가" 입니다.
   비교하려면 비교 대상이 구분되어 있어야 합니다.
   태그 없이 100개를 쌓아두면 다음 주에 비교할 수가 없습니다.

   "실험은 하는 것보다 구분해 두는 것이 중요합니다.
    라벨 없는 시험관 100개는 실험이 아닙니다."

실행:
    python tags_metadata.py
"""

from dotenv import load_dotenv

load_dotenv()

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

MODEL = "gemma3:4b"

REVIEW = (
    "이 무선 이어폰 배터리는 정말 오래갑니다. 다만 케이스가 좀 크고, "
    "통화 품질은 기대 이하였습니다."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 고객 리뷰 분석기다. 장점과 단점을 각각 한 줄로 정리한다."),
        ("human", "다음 리뷰를 분석해라.\n\n{review}"),
    ]
)


def build(temperature: float):
    return prompt | ChatOllama(model=MODEL, temperature=temperature) | StrOutputParser()


# ── 방법 A: 호출할 때 config 로 붙인다 ──────────────────────────
def method_a() -> None:
    chain = build(0.0)
    result = chain.invoke(
        {"review": REVIEW},
        config={
            "tags": ["exp-A", "temp-0.0"],          # ★ 필터용 짧은 라벨
            "metadata": {                            # ★ 검색·비교용 키-값
                "variant": "A",
                "model": MODEL,
                "temperature": 0.0,
                "note": "프롬프트 수정 전",
            },
        },
    )
    print("[방법 A — config 로 붙이기]")
    print(" ", result.replace("\n", " ")[:80], "...")
    print()


# ── 방법 B: 체인에 미리 붙여 두고 파생한다 ★ ────────────────────
#    같은 체인에서 라벨만 다른 변형을 만들어 두는 방식입니다.
def method_b() -> None:
    print("[방법 B — with_config 로 파생해 A/B 를 나란히 만든다] ★")

    for variant, temp in [("A", 0.0), ("B", 0.8)]:
        c = build(temp).with_config(
            tags=[f"exp-{variant}", f"temp-{temp}"],
            metadata={
                "variant": variant,
                "model": MODEL,
                "temperature": temp,   # ★ 설정값을 함께 기록해야 '재현' 이 된다
                "run_by": "week06-practice",
            },
        )
        out = c.invoke({"review": REVIEW})
        print(f"  exp-{variant} (temp={temp}) → {out.replace(chr(10), ' ')[:70]} ...")
    print()


def main() -> None:
    print("=" * 66)
    print("  태그·메타데이터로 실험 구분하기")
    print("=" * 66)

    method_a()
    method_b()

    print("=" * 66)
    print("""
이제 웹에서 확인합니다 ★

    smith.langchain.com → week06-tracing → 필터에  exp-A  를 입력
        └ exp-A 로 태그된 실행만 남습니다.
          exp-B 로 바꾸면 다른 쪽만 남습니다.

    Run 하나를 열어 Metadata 를 보면 temperature·model 이 그대로 있습니다.
    ★ 설정값을 함께 기록해 두지 않으면, 나중에 "이건 몇 도로 돌린 거지?" 를
      알 방법이 없습니다. 재현이 안 되는 실험은 실험이 아닙니다.

무엇을 관찰할 것인가

  관찰                        의미
  ──────────────────────────────────────────────────────────────
  태그로 필터가 됨            "이게 다음 주 A/B 비교의 전제입니다" ★★
  메타데이터에 숫자를 넣음    temperature·k 같은 설정값을 함께 기록
  A 와 B 의 출력이 다름       temp 0.0 vs 0.8 — 5주차에서 본 그 차이

⚠️ 태그는 '짧은 라벨', 메타데이터는 '값' 입니다.
   태그에 temperature 값을 통째로 넣지 마십시오. 필터가 지저분해집니다.

다음 단계 →  python prompt_hub.py
""")
    print("=" * 66)


if __name__ == "__main__":
    main()
