"""[2교시 / 실습 2] ★★ 같은 문서를 3가지로 잘라, 같은 질문에 무엇이 검색되는지 비교한다

  ★ 이 교시가 10주차의 핵심입니다.
    학생들은 보통 "임베딩 모델이 좋으면 검색이 잘 되겠지" 라고 생각합니다.
    실제로는 **어떻게 잘랐는가가 검색 품질의 상한을 결정합니다.**

    A 고정 크기   단순·빠름            ⚠️ 문장·단어 중간에서 끊긴다
    B 재귀적      큰 경계부터 시도      ★ 실무 기본값
    C 구조 기반   섹션 통째로 유지      ★★ 메타데이터가 자동 생성된다

  📌 결론 문장
     **"검색 품질의 상한은 임베딩 모델이 아니라 분할이 정합니다."**
     같은 임베딩 모델, 같은 질문인데 결과가 달랐습니다. 바꾼 것은 자르는 방법뿐입니다.

  이 파일은 3절(메타데이터 설계)의 build_chunks_with_metadata() 도 제공합니다.
  embed.py 가 이것을 가져다 씁니다. ★

실행:
    python split_compare.py            # 1단계: 어디서 끊겼는지 눈으로 본다 (무료·즉시) ★
    python split_compare.py --search   # 2단계: 세 인덱스에 같은 질문을 던진다 (임베딩 필요)
    python split_compare.py --meta     # 3절: 메타데이터를 심은 청크를 확인한다 ★
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

HERE = Path(__file__).parent
DOC_PATH = HERE / os.getenv("WEEK10_DOC", "data/학칙.md")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# 🔶 사전 확인 필수: 이 질문으로 세 인덱스의 결과가 실제로 갈리는지 미리 돌려 보십시오. ★
QUESTION = os.getenv("WEEK10_QUESTION", "일반휴학은 통산 최대 몇 학기까지 할 수 있나요?")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ★ 한국어 구분자를 추가했습니다.
#   기본 separators 는 영어 기준(". ")이라 한국어 문장 끝("다. ")을 못 잡습니다.
KO_SEPARATORS = ["\n\n", "\n", "다. ", ". ", " ", ""]

HEADERS = [("#", "장"), ("##", "조")]


def load_raw() -> str:
    return TextLoader(str(DOC_PATH), encoding="utf-8").load()[0].page_content


# ── A. 고정 크기 ────────────────────────────────────────────
def split_a(raw: str) -> list[str]:
    """500자에서 기계적으로 끊는다. ⚠️ 이 방식의 실패가 오늘 실습의 출발점."""
    return CharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=0, separator=""
    ).split_text(raw)


# ── B. 재귀적 ──────────────────────────────────────────────
def split_b(raw: str) -> list[str]:
    """가능한 한 큰 경계를 지키면서 500자를 맞춘다. ★ 실무 기본값

       ① "\\n\\n"(문단)으로 나눠본다  → 500자 이하가 되면 채택
       ② 안 되면 "\\n"(줄)로
       ③ 안 되면 "다. "·". "(문장)으로
       ④ 그래도 안 되면 " "(단어) → 마지막엔 글자 단위
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=KO_SEPARATORS
    ).split_text(raw)


# ── C. 구조 기반 ───────────────────────────────────────────
def split_c(raw: str) -> list[Document]:
    """섹션(조)이 통째로 유지되고, ★★ metadata 가 자동으로 붙는다."""
    return MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS).split_text(raw)


def compare_shapes(raw: str) -> dict:
    """먼저 눈으로 봅니다 — 어디서 끊겼는가 ★"""
    a, b = split_a(raw), split_b(raw)
    c_docs = split_c(raw)
    c = [d.page_content for d in c_docs]

    for name, chunks in [("A 고정", a), ("B 재귀", b), ("C 구조", c)]:
        lens = [len(x) for x in chunks]
        print("=" * 60)
        print(f"[{name}] {len(chunks)}개  평균 {sum(lens) // len(lens)}자  "
              f"최소 {min(lens)}  최대 {max(lens)}")
        print("--- 첫 청크 끝부분 80자 (어디서 끊겼는지 보기) ★ ---")
        print("..." + chunks[0][-80:].replace("\n", " "))

    print("=" * 60)
    print("""
  [A 고정] ...신청하며 통산            ← ⚠️ 숫자 바로 앞에서 끊겼다
  [B 재귀] ...초과할 수 없다.          ← ✅ 문장 끝
  [C 구조] (제12조 전체가 한 청크)      ← ✅ 조 단위

  ⚠️ A 에서 무슨 일이 일어났는지 보십시오.
     "일반휴학은 학기 단위로 신청하며 통산" 에서 끊긴 청크가 만들어졌습니다.
     이 청크는 질문("일반휴학은 통산 몇 학기?")과 매우 비슷해서 **검색은 1위로 잘 됩니다.**
     그런데 **몇 학기인지가 그 안에 없습니다.** ★★

     → 검색은 성공했는데 답을 못 만듭니다. 그리고 모델은 그럴듯하게 지어냅니다.
""")

    # C 의 metadata 가 자동 생성되는 것을 보여준다 ★★
    print("  ★★ C 는 metadata 가 자동으로 붙습니다 — 3절의 근거입니다")
    for d in c_docs[3:5]:
        print(f"    {d.metadata}")
    print()

    return {"A 고정": a, "B 재귀": b, "C 구조": c}


def compare_search(groups: dict) -> None:
    """세 인덱스에 같은 질문을 던져 무엇이 나오는지 본다 ★★"""
    from langchain_community.vectorstores import FAISS
    from langchain_ollama import OllamaEmbeddings

    emb = OllamaEmbeddings(model=EMBED_MODEL)

    print(f"\n질문: {QUESTION}\n")
    for name, chunks in groups.items():
        store = FAISS.from_texts(chunks, emb)
        hits = store.similarity_search(QUESTION, k=2)
        print("=" * 60)
        print(f"[{name}]")
        for i, d in enumerate(hits, 1):
            text = d.page_content.replace("\n", " ")
            # ★ 답(숫자)이 이 청크 안에 실제로 들어 있는가 — 이것이 판정 기준
            has_answer = "6개 학기" in d.page_content
            mark = "✅ 답 포함" if has_answer else "❌ 답 없음"
            print(f"  {i}. [{mark}] {text[:110]}...")

    print("=" * 60)
    print("""
학생이 채울 표

  | 분할   | 청크 수 | 평균 길이 | 검색 1위 청크에 **답이 들어 있는가** |
  | A 고정 |        |          |                                    |
  | B 재귀 |        |          |                                    |
  | C 구조 |        |          |                                    |

무엇을 읽어낼 것인가 ★

  A 에서 답이 잘린 청크가 1위   검색은 성공했는데 **답을 못 만든다** ★★
  B 는 문장이 온전함            같은 크기인데 **쓸 수 있는 청크**가 된다
  C 는 조 단위로 완결           규정·매뉴얼처럼 구조가 있는 문서에 최적
  C 의 청크 길이 편차가 큼       긴 섹션은 다시 잘라야 함 (2단 구성)

📌 **"검색 품질의 상한은 임베딩 모델이 아니라 분할이 정합니다."**

🔶 결과가 안 갈리면: chunk_size 를 더 작게 잡거나, 경계에 걸치는 질문으로 바꾸십시오.
   갈리지 않으면 이 실습의 의미가 사라집니다. ★
""")


# ── 3절. 메타데이터 설계 ★★ ─────────────────────────────────
def build_chunks_with_metadata(raw: str | None = None) -> list[Document]:
    """분할 단계에서 메타데이터를 심는다. ★★ 이 절이 11주차 전부를 좌우합니다.

       [10주차 — 지금]                  [11주차 — 나중]
       청크에 metadata 를 심는다   →    · 필터 검색  "2026년 개정본에서만"
         source / page / 장 / 조         · Self-Query "3장에서만 찾아줘"
         year / category                 · ★ 출처 표기 "[학칙 3장 12조]"
                                           │
       ⚠️ 안 심으면?                →     └ 만들 수 없습니다. 정보가 없으니까 ★★

    ★ 실무의 2단 구성을 씁니다: C(구조)로 크게 나눈 뒤 → 긴 섹션만 B(재귀)로 다시.
      · 구조로 나누면 장·조 metadata 가 공짜로 생깁니다
      · 재귀로 다듬으면 청크 길이 편차가 잡힙니다
    """
    raw = raw if raw is not None else load_raw()

    sections = split_c(raw)  # 장·조 metadata 가 붙은 섹션들
    sub = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=KO_SEPARATORS
    )

    chunks: list[Document] = []
    for sec in sections:
        for piece in sub.split_text(sec.page_content):
            chunks.append(
                Document(
                    page_content=piece,
                    metadata={
                        # ── 출처 표기용 ★ (11주차 3교시 Citation) ────────
                        "source": DOC_PATH.name,
                        "chapter": sec.metadata.get("장", ""),
                        "article": sec.metadata.get("조", ""),
                        # ⚠️ page 는 PDF Loader 라야 붙습니다. .md 에는 아예 없습니다.
                        #    "나중에 복원할 수 없는 것" 의 대표 사례입니다 ★
                        #    → 11주차 citation.py 에서 p.? 로 표시됩니다.
                        #    ⚠️ 값이 없다고 None 을 넣지 마십시오. 일부 벡터 저장소
                        #       (Chroma 등)는 metadata 에 None 을 거부합니다. 🔶
                        #       "없는 키" 로 두는 편이 안전합니다.
                        # ── 필터 검색용 ★ (11주차 1교시) ────────────────
                        # ⚠️ 타입을 맞추십시오. 2026(숫자)과 "2026"(문자)은
                        #    범위 필터에서 다르게 동작합니다.
                        "year": 2026,
                        "category": "학사",
                        "doc_type": "규정",
                        # ── 운영·디버깅용 ────────────────────────────────
                        "chunk_id": len(chunks),
                        # ★ 어떻게 잘랐는지 기록해 두면 7주차 방식으로
                        #   분할 전략을 A/B 비교할 수 있습니다.
                        "splitter": f"markdown→recursive-{CHUNK_SIZE}-{CHUNK_OVERLAP}",
                    },
                )
            )
    return chunks


def show_metadata() -> None:
    chunks = build_chunks_with_metadata()
    print(f"메타데이터를 심은 청크 {len(chunks)}개\n")
    for d in chunks[:3]:
        print("─" * 60)
        print(d.metadata)
        print(d.page_content[:90].replace("\n", " "), "...")

    print("─" * 60)
    print("""
설계 원칙 3가지 ★

  나중에 복원할 수 없는 것을 우선   페이지 번호·섹션 제목은 자르고 나면 사라진다 ★
  필터로 쓸 값은 타입을 맞춘다      year: 2026(숫자) vs "2026"(문자) — 범위 필터가 달라짐
  본문에 이미 있는 것은 안 넣는다    중복은 저장 비용만 늘림

⚠️ 과하게도, 부족하게도 넣지 마십시오. 기준은 하나입니다 —
   ***"11주차에 이걸로 무엇을 하고 싶은가?"***

📌 학생 활동: "내 미니 프로젝트 문서에는 어떤 메타데이터가 필요할까?" 를
   CONTEXT.md 에 한 줄이라도 적게 하십시오. ★
""")


def main() -> None:
    raw = load_raw()
    print(f"문서: {DOC_PATH}  ({len(raw)}자)\n")

    if "--meta" in sys.argv:
        show_metadata()
        return

    groups = compare_shapes(raw)

    if "--search" in sys.argv:
        compare_search(groups)
    else:
        print("  다음: python split_compare.py --search   # 세 인덱스에 같은 질문 ★")
        print("        python split_compare.py --meta     # 3절 메타데이터 설계 ★★")


if __name__ == "__main__":
    main()
