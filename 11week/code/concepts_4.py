"""[2교시 / 3절] 개념 4종 — 어떤 문제를 푸는가 (실습하지 않습니다)

  🎯 여기서는 구현하지 않습니다. **"어떤 상황에 무엇을 쓰는가"** 만 잡습니다.
     시험도 그 수준으로 출제합니다.

  ⚠️ 7종을 모두 실습하면 어느 것도 제대로 끝나지 않습니다.
     3종(MMR·MultiQuery·하이브리드)만 손으로 만들고, 4종은 개념으로 정리합니다.

  이 파일은 **읽는 자료**입니다. 코드는 참고용으로 붙여 두었을 뿐,
  --run 을 붙이지 않는 한 아무것도 호출하지 않습니다. ★

실행:
    python concepts_4.py              # 4종 설명 + 7종 한눈에 표 (호출 없음 · 무료) ★
    python concepts_4.py --run parent # 🔶 교수 시연용 — Parent Document 만 실제로
"""

import sys

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")


# ── 3-1. Contextual Compression ─────────────────────────────
COMPRESSION = """
── ① Contextual Compression — 가져온 것에서 관련 부분만 ──────────

   검색 결과: 2,000자 청크
        │   그중 답과 관련된 것은 3문장뿐
        ▼
   LLM 이 관련 부분만 뽑아낸다 → 200자
        ▼
   프롬프트가 짧아진다 → 비용↓ · 노이즈↓ · Lost in the Middle 완화 ★

   푸는 문제 : 긴 문서에 관련 없는 내용이 섞임
   대가      : **LLM 호출 추가 (문서 수만큼!)** ⚠️

   # 개념 코드 (실습하지 않음)
   from langchain.retrievers import ContextualCompressionRetriever
   from langchain.retrievers.document_compressors import LLMChainExtractor

   compressor = LLMChainExtractor.from_llm(llm)
   retriever_cc = ContextualCompressionRetriever(
       base_compressor=compressor, base_retriever=vec)
"""

# ── 3-2. Parent Document ★★ ─────────────────────────────────
PARENT = """
── ② Parent Document — 작게 검색하고 크게 답한다 ★★ ──────────────

   ★ 10주차 청크 딜레마의 정면 해법입니다.

   [10주차의 딜레마]
     작게 자르면 → 검색은 정확한데 문맥이 없다
     크게 자르면 → 문맥은 있는데 검색이 부정확하다
                        │
                        ▼
   [Parent Document]
     자식 청크(작게)로 검색한다        ← 검색 정확도 ✅
     부모 청크(크게)를 반환한다        ← 문맥 확보 ✅  ★

   부모: 제12조 전체 (2,000자)
     ├ 자식1: "일반휴학은 학기 단위로 신청하며..." (300자)  ← 이걸로 검색
     ├ 자식2: "통산 6개 학기를 초과할 수 없다"     (300자)
     └ 자식3: "군 복무 휴학은 별도로 산정한다"     (300자)
                    │  자식2가 검색되면
                    ▼
              부모(제12조 전체)를 프롬프트에 넣는다 ★

   푸는 문제 : **작게 자르면 문맥 소실 / 크게 자르면 노이즈** ★★
   대가      : 저장 구조가 복잡해짐 (부모-자식 두 벌 관리)

   ★★ 10주차 2교시 1-5 에서 예고한 그것입니다.
      기말 서술형 후보 ③("200자로 하니 문맥이 없고 2000자로 하니 엉뚱한 게 섞인다")
      의 **정답**입니다.
"""

# ── 3-3. Self-Query ─────────────────────────────────────────
SELF_QUERY = """
── ③ Self-Query — 자연어에서 필터를 자동 추출 ────────────────────

   사용자: "작년 학사 규정에서 휴학 조건 알려줘"
        │
        │  LLM 이 분해한다  ★
        ▼
   검색어  : "휴학 조건"
   필터    : {"year": 2025, "category": "학사"}      ← 1교시 필터 검색으로 ★
        ▼
   메타데이터 필터 + 유사도 검색을 함께 수행

   푸는 문제 : 사용자가 **필터 문법을 모른다**
   대가      : 메타데이터 스키마 정의 필요 / **파싱 실패 가능** ⚠️

   ★ 10주차 메타데이터 설계가 여기서도 회수됩니다.
     year·category 를 안 심었으면 **Self-Query 도 못 씁니다.**
   ⚠️ 파싱 실패 가능성 → **5주차 구조화 출력(with_structured_output)** 으로 안정화 ★
"""

# ── 3-4. Re-ranking ─────────────────────────────────────────
RERANK = """
── ④ Re-ranking — 넓게 가져와 다시 줄 세운다 (교수 시연) ★ ────────

   1차 : 벡터 검색으로 20건을 '넓게' 가져온다   (빠르지만 정확도는 보통)
        ▼
   2차 : 재정렬 모델이 질문-문서 쌍을 하나씩 정밀 채점 → 상위 5건 ★
        ▼
   상위권 정확도가 크게 올라간다

   푸는 문제 : **1차 검색 상위권의 정확도가 낮음**
   대가      : 모델 추가 → **지연 증가 / VRAM 추가** ⚠️

   ⚠️⚠️ 학생 PC 에는 설치하지 않습니다.
        생성 LLM(8B Q4) 5.0GB + 임베딩 0.3GB + KV 캐시 1.0GB ≒ 6.3GB
        + 재정렬 모델 1.1~2.2GB  →  **8GB 초과 위험** ⚠️
        → **교수 PC 에서 시연만** 하십시오.

   🔶 시연 준비: 같은 질문에 대해 **재정렬 전/후 상위 5건의 순위가 실제로 바뀌는 화면**
      을 확보하십시오. 순위가 안 바뀌면 시연의 의미가 없습니다.
      **1차 검색을 20건으로 넓게 잡으면 잘 갈립니다.** ★

   ⚠️ 과제 4 에서 Re-ranking 은 선택지에서 **제외**됩니다(시연 대상이므로).
"""

TABLE = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3-5. 7종 한눈에 — 시험 대비 표 ★★

  | 전략                    | 다루는 방식 | 푸는 문제                          | 대가              |
  |-------------------------|-----------|-----------------------------------|------------------|
  | **MMR**                 | 실습      | 검색 결과가 **서로 중복됨**          | 최상위 유사도 희생  |
  | **MultiQuery**          | 실습      | **질문 표현이 문서와 다름**          | LLM 호출 추가      |
  | **하이브리드**           | 실습      | **고유명사·코드·숫자**를 벡터가 놓침  | 가중치 튜닝 필요    |
  | Contextual Compression  | 개념      | 긴 문서에 관련 없는 내용이 섞임       | LLM 호출 추가      |
  | **Parent Document** ★★  | 개념      | **작게=문맥소실 / 크게=노이즈**      | 저장 구조 복잡      |
  | Self-Query              | 개념      | 사용자가 **필터를 직접 못 씀**       | 스키마 정의·파싱실패 |
  | Re-ranking              | 개념+시연 | **1차 상위권 정확도가 낮음**         | 모델 추가(지연·VRAM)|

📌 이 표를 그대로 외우게 하지 말고, **"문제 → 전략"** 으로 답하게 연습시키십시오.
   기말 서술형이 정확히 그 형태로 나옵니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def run_parent() -> None:
    """🔶 교수 시연용 — Parent Document 를 실제로 한 번 보여줍니다.

    ⚠️ 학생 실습 대상이 아닙니다. 25분에 넣으면 3종 실습이 끝나지 않습니다.
    """
    from langchain.retrievers import ParentDocumentRetriever
    from langchain.storage import InMemoryStore
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from rag_common import KO_SEPARATORS, get_emb, load_chunks

    try:
        from langchain_chroma import Chroma
    except ImportError:
        print("🔶 langchain-chroma 가 필요합니다: pip install langchain-chroma chromadb")
        return

    docs = load_chunks()
    for d in docs:  # ⚠️ Chroma 는 metadata 의 None 을 거부합니다 🔶
        d.metadata = {k: v for k, v in d.metadata.items() if v is not None}

    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=0, separators=KO_SEPARATORS)
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=150, chunk_overlap=0, separators=KO_SEPARATORS)  # ★ 작게 검색

    retriever = ParentDocumentRetriever(
        vectorstore=Chroma(collection_name="week11_parent",
                           embedding_function=get_emb()),
        docstore=InMemoryStore(),
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    retriever.add_documents(docs)

    q = "일반휴학은 통산 최대 몇 학기까지 가능한가?"
    print(f"질문: {q}\n")

    print("── 자식 청크로 검색한 결과 (작다 — 정확하다) ─────────")
    for d in retriever.vectorstore.similarity_search(q, k=2):
        print(f"  ({len(d.page_content):3d}자) {d.page_content[:70]}")

    print("\n── 실제로 반환되는 것: 부모 청크 (크다 — 문맥이 있다) ★")
    for d in retriever.invoke(q):
        print(f"  ({len(d.page_content):3d}자) {d.page_content[:110]}...")

    print("""
  ★★ "작게 검색하고 크게 답한다."
     검색은 150자 자식으로 정확하게, 답변은 800자 부모로 문맥을 갖춰서.
     10주차의 딜레마를 **양쪽 다 취하는** 방식입니다.
""")


def main() -> None:
    if "--run" in sys.argv:
        target = sys.argv[sys.argv.index("--run") + 1]
        if target == "parent":
            run_parent()
            return
        print(f"🔶 '--run {target}' 은 준비되어 있지 않습니다. (parent 만 지원)")
        return

    print(COMPRESSION)
    print(PARENT)
    print(SELF_QUERY)
    print(RERANK)
    print(TABLE)
    print("  🔶 교수 시연: python concepts_4.py --run parent\n")


if __name__ == "__main__":
    main()
