"""[2교시 / 실습 2] ★★ 검색 전략 3종 — MMR · MultiQuery · 하이브리드

  ★ 배포 스켈레톤입니다. 25분에 3종을 처음부터 짜는 것은 불가능합니다.
    특히 **하이브리드는 BM25 인덱스를 따로 만들고 묶어야 해서 무겁습니다.**
    조립은 되어 있으니 **파라미터를 바꿔가며 실험**하십시오. ★

  기본 유사도 검색의 두 한계

     ① 중복       비슷한 것만 잔뜩 온다        → MMR
                  "휴학 규정 알려줘" 에 제12조 이야기만 5개.
                  군휴학·질병휴학은 하나도 안 나온다 ⚠️

     ② 표현 의존  말을 바꾸면 못 찾는다        → MultiQuery
                  "휴학 절차" ✅ / "학교 좀 쉬고 싶은데" ❌
                  구어체 질문과 규정 문어체 사이의 거리가 멉니다.
                  사용자는 규정 용어를 모른 채 질문합니다. **그게 정상입니다.**

     (+) 벡터의 약점  고유명사·숫자·코드      → 하이브리드(BM25)
                  "제12조" 로 검색하면 엉뚱한 조문이 나옵니다.
                  의미로 뭉개기 때문입니다. **옛날 방식이 더 잘합니다.**

  📌 결론: **"좋은 전략 하나" 가 아니라 "내 질문 유형에 맞는 것"** 입니다.
     그리고 어느 것이 나은지는 **내 데이터로 재봐야 압니다** → 7주차 평가 → 과제 4 ★

실행:
    python retriever_strategies.py                 # 4종(기본·MMR·MQ·하이브리드) 전체 비교표 ★★
    python retriever_strategies.py --mmr           # MMR 만 — lambda_mult 를 바꿔가며 ★
    python retriever_strategies.py --multiquery    # MultiQuery 만 — 재작성된 질문을 본다 ★★
    python retriever_strategies.py --hybrid        # 하이브리드만 — weights 를 바꿔가며 ★
"""

import logging
import re
import sys

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from questions import QUESTIONS
from rag_common import clip, get_llm, load_chunks, load_store, pad

K = 3


# ── ① 기본 ─────────────────────────────────────────────────
def make_basic(store):
    return store.as_retriever(search_kwargs={"k": K})


# ── ② MMR — 유사도와 다양성의 균형 ★ ─────────────────────────
def make_mmr(store, lambda_mult: float = 0.5, fetch_k: int = 20):
    """기본 : 유사도 상위 k개를 그냥 뽑는다
       MMR  : "질문과 가까우면서 + 이미 뽑은 것과는 다른" 것을 순서대로 뽑는다 ★

       fetch_k       1차로 넓게 가져올 개수 (클수록 다양성 여지↑)
       lambda_mult   0 = 다양성 최대 / 1 = 유사도 최대  ★ 저울
    """
    return store.as_retriever(
        search_type="mmr",  # ★ 한 줄
        search_kwargs={"k": K, "fetch_k": fetch_k, "lambda_mult": lambda_mult},
    )


# ── ③ MultiQuery — 질문을 여러 형태로 다시 쓴다 ★ ─────────────
def make_multiquery(store, llm=None, verbose: bool = False):
    """원 질문을 LLM 이 재작성 → 각각 검색 → 합집합(중복 제거)

       "학교 좀 쉬고 싶은데"
            ① "휴학 신청 절차는 무엇인가?"
            ② "휴학 요건과 기간은?"
            ③ "학업을 중단하려면 어떻게 하나?"

       ⚖️ 대가: **LLM 호출이 추가**됩니다. 지연·비용이 늘어납니다.
          7주차의 3축(정확도·토큰·지연)으로 재봐야 채택 여부를 알 수 있습니다. ★
    """
    from langchain.retrievers.multi_query import MultiQueryRetriever

    if verbose:
        # ★★ 재작성된 질문을 반드시 화면에 보여주십시오.
        #    "모델이 내 질문을 이렇게 바꿔서 검색했구나" 를 보는 순간 이 전략이 이해됩니다.
        logging.basicConfig()
        logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)

    return MultiQueryRetriever.from_llm(
        retriever=store.as_retriever(search_kwargs={"k": K}),
        llm=llm or get_llm(),  # ★ 질문 재작성용 LLM
    )


# ── ④ 하이브리드 — 키워드 + 벡터 ★ ───────────────────────────
def make_hybrid(store, chunks, weights=(0.4, 0.6)):
    """BM25(키워드) + 벡터(의미) 를 가중 합산한다.

       BM25   "제12조" 같은 정확한 토큰에 강함. 의미는 모름
       벡터   "쉬고 싶은데" 같은 의역에 강함. 고유명사는 약함

       ★ weights 를 [0.2,0.8] / [0.5,0.5] / [0.8,0.2] 로 바꿔 보게 하십시오.
         **고유명사 질문**과 **구어체 질문**에서 최적값이 서로 다릅니다.
         → "하나의 정답 가중치는 없다" 가 이 실습의 결론입니다.
    """
    from langchain_community.retrievers import BM25Retriever

    try:
        from langchain.retrievers import EnsembleRetriever  # 🔶 임포트 경로 사전 확인
    except ImportError:  # 버전에 따라 위치가 다릅니다
        from langchain_community.retrievers import EnsembleRetriever

    # ── ① BM25 인덱스는 따로 만든다 (문서 텍스트가 필요) ★ ──
    bm25 = BM25Retriever.from_documents(chunks)  # 10주차 청크
    bm25.k = K

    # ── ② 벡터 검색기 ──────────────────────────────────────
    vec = store.as_retriever(search_kwargs={"k": K})

    # ── ③ 묶는다 — 가중치가 핵심 ★ ──────────────────────────
    return EnsembleRetriever(retrievers=[bm25, vec], weights=list(weights))


# ── 공통 표시 ───────────────────────────────────────────────
def articles_of(docs) -> list[str]:
    """어느 조가 검색됐는가 — 비교의 단위를 '조' 로 잡으면 표가 읽힙니다 ★"""
    return [d.metadata.get("article", "?") or "?" for d in docs]


def hit(docs, expected: str) -> str:
    """상위 결과에 정답 근거 조가 포함되었는가 (○/×) — 기록 방식을 단순화합니다 ★

    expected 예: "제12조" / "제12~15조" / "— (문서에 없음)"
    """
    if expected.startswith("—"):
        return "—"  # 문서에 없는 내용 — 애초에 맞힐 대상이 아닙니다

    nums = [int(n) for n in re.findall(r"\d+", expected)]
    if len(nums) == 2 and "~" in expected:  # 범위 표기
        nums = list(range(nums[0], nums[1] + 1))

    got = " ".join(articles_of(docs))
    return "○" if any(f"제{n}조" in got for n in nums) else "×"


def compare_all() -> None:
    store = load_store()
    chunks = load_chunks(store)

    strategies = {
        "기본": make_basic(store),
        "MMR": make_mmr(store),
        "MultiQuery": make_multiquery(store),
        "하이브리드": make_hybrid(store, chunks),
    }

    print(f"\n질문 {len(QUESTIONS)}개 × 전략 {len(strategies)}종")
    print("⏱ MultiQuery 는 질문마다 LLM 호출이 추가되어 느립니다. 먼저 걸어 두십시오. ★\n")

    print("  " + pad("질문", 46) + pad("유형", 14)
          + "".join(pad(n, 13, ">") for n in strategies))
    print("  " + "─" * 112)

    for q, kind, expected in QUESTIONS:
        cells = []
        for retr in strategies.values():
            try:
                cells.append(hit(retr.invoke(q), expected))
            except Exception as e:
                cells.append(f"!{type(e).__name__[:6]}")
        print("  " + pad(clip(q, 44), 46) + pad(kind, 14)
              + "".join(pad(c, 13, ">") for c in cells))

    print("""
  ○ = 상위 결과에 정답 근거 조가 포함됨 / × = 없음 / — = 문서에 없는 내용

예상되는 결론 ★

  | 질문 유형              | 잘 듣는 전략   | 이유                          |
  | 구어체·의역            | **MultiQuery** | 질문을 문서 표현으로 다시 씀    |
  | 고유명사·조문번호·코드  | **하이브리드** | BM25 가 정확 토큰을 잡음       |
  | 넓은 질문              | **MMR**        | 서로 다른 조항을 고루 가져옴    |
  | 표준적 질문            | **기본으로 충분** ★ | 전략을 쓸 이유가 없음      |

📌 **"좋은 전략 하나" 가 아니라 "내 질문 유형에 맞는 것"** 입니다.
   그리고 어느 것이 나은지는 **내 데이터로 재봐야 압니다** → 과제 4 ★

⚠️ 결과가 전략별로 안 갈리면: 문서가 작아서일 수 있습니다.
   질문을 더 까다롭게(구어체·조문번호) 바꾸거나 K 를 줄여 보십시오. 🔶
""")


def demo_mmr() -> None:
    """★ lambda_mult 를 0.2 / 0.5 / 0.9 로 바꿔가며 돌려보게 하십시오."""
    store = load_store()
    q = "휴학 관련 규정을 전반적으로 알려주세요"  # 넓은 질문 ★
    print(f"질문: {q}\n")

    print("  [기본]      ", articles_of(make_basic(store).invoke(q)))
    for lm in (0.9, 0.5, 0.2):
        docs = make_mmr(store, lambda_mult=lm).invoke(q)
        print(f"  [MMR λ={lm}] ", articles_of(docs))

    print("""
  ★ λ=0.9 면 기본 검색과 거의 같고, λ=0.2 면 관련성이 떨어지는 것까지 섞입니다.
  ⚖️ **"공짜가 아니다"** — 다양성을 얻으려면 **최상위 유사도를 일부 내줍니다.**

  ⚠️ 기본 검색의 한계 ①(중복)이 보입니까?
     기본은 제12조 이야기만 몰려 오고, MMR 은 제13·14·15조가 섞여 옵니다.
     사용자는 **넓게** 알고 싶은데 검색은 **좁게** 가져오는 것이 문제였습니다.
""")


def demo_multiquery() -> None:
    """★★ 재작성된 질문을 반드시 화면에 보여주십시오."""
    store = load_store()
    retr = make_multiquery(store, verbose=True)  # ★ INFO 로그로 재작성 질문이 찍힙니다

    q = "학교 좀 쉬고 싶은데 어떻게 해야 하나요?"  # 구어체 ★
    print(f"질문: {q}")
    print("(아래 INFO 로그가 '모델이 만든 재작성 질문' 입니다 ★★)\n")

    docs = retr.invoke(q)
    print("\n  검색된 조:", articles_of(docs))
    print("  [기본 검색과 비교]", articles_of(make_basic(store).invoke(q)))

    print("""
  ★★ "모델이 내 질문을 이렇게 바꿔서 검색했구나" 를 보는 순간 이 전략이 이해됩니다.
     LangSmith 추적에서도 **LLM Run 이 하나 더 늘어난 것**이 보입니다.

  ⚖️ 대가: LLM 호출이 추가됩니다. 지연·비용이 늘어납니다.
     7주차의 3축으로 재봐야 채택 여부를 알 수 있습니다. ★

  💡 13주차 예고: MultiQuery 는 **항상** 여러 질문을 만듭니다.
     Agentic RAG 는 **실패했을 때만** 재작성합니다. 같은 문제, 다른 해법입니다. ★
""")


def demo_hybrid() -> None:
    """★ weights 를 바꿔가며 — 질문 유형마다 최적값이 다릅니다."""
    store = load_store()
    chunks = load_chunks(store)

    cases = [
        ("제12조 내용이 뭔가요?", "고유명사 ★"),
        ("학교 좀 쉬고 싶은데 어떻게 해야 하나요?", "구어체 ★"),
    ]

    for q, kind in cases:
        print(f"\n질문 [{kind}]: {q}")
        print("  [기본 벡터]        ", articles_of(make_basic(store).invoke(q)))
        for w in [(0.2, 0.8), (0.5, 0.5), (0.8, 0.2)]:
            docs = make_hybrid(store, chunks, weights=w).invoke(q)
            print(f"  [BM25 {w[0]} / 벡터 {w[1]}] ", articles_of(docs))

    print("""
  ★ 고유명사 질문과 구어체 질문에서 **최적 가중치가 서로 다릅니다.**
    → "하나의 정답 가중치는 없다" 가 이 실습의 결론입니다.

  💡 rank_bm25 는 순수 파이썬 CPU 라이브러리라 VRAM 을 쓰지 않습니다.
     8GB 예산에 영향이 없습니다.
""")


def main() -> None:
    if "--mmr" in sys.argv:
        demo_mmr()
    elif "--multiquery" in sys.argv:
        demo_multiquery()
    elif "--hybrid" in sys.argv:
        demo_hybrid()
    else:
        compare_all()


if __name__ == "__main__":
    main()
