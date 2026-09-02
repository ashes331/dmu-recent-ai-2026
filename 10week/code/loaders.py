"""[1교시 / 실습 1] 문서 형식별 Loader 4종을 돌려보고 결과를 비교한다

  Loader = 무엇이든 읽어서 Document 객체 리스트로 만든다.

      Document(
          page_content="문서의 본문 텍스트...",
          metadata={"source": "학칙.pdf", "page": 7},      # ★ 이게 오늘의 복선
      )

  ★ metadata 를 지금 기억해 두십시오.
    2교시 3절(메타데이터 설계)과 11주차(필터 검색·출처 표기)의 근거가 됩니다.

  Loader 별 '단위' 가 다릅니다 ★

      Text  →  1개 (파일 전체)          자동 metadata: source
      PDF   →  페이지 수만큼 ★          자동 metadata: source, page ★
      CSV   →  행 수만큼 ★              자동 metadata: source, row
      Web   →  1개                      자동 metadata: source, title

  📌 핵심 메시지: **"쓰레기를 넣으면 쓰레기가 나옵니다."**
     파이프라인 6단계 중 ①에서 망가진 것은 ⑥에서 절대 복구되지 않습니다.

  🔶 임포트 경로 주의: Loader 클래스의 위치(langchain_community.document_loaders)는
     버전에 따라 이동한 이력이 있습니다. 수업 전날 1회 실행해 확정하십시오.

실행:
    python loaders.py            # 로컬 파일 3종 (Web 은 건너뜀 · 네트워크 없음)
    python loaders.py --web      # Web Loader 까지 (⚠️ 30명 동시 호출 주의)
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

# WebBaseLoader 는 User-Agent 가 없으면 경고를 냅니다. 미리 채워 둡니다.
import os

os.environ.setdefault("USER_AGENT", "dongyang-ai-class/2026 (교육용 실습)")

from langchain_community.document_loaders import CSVLoader, TextLoader, WebBaseLoader

DATA = Path(__file__).parent / "data"

# 🔶 교수 준비: 실제 학칙 PDF 를 data/학칙.pdf 로 두십시오. ★
#    ⚠️ '표가 깨지는 페이지' 와 '머리말이 섞이는 페이지' 는 진짜 PDF 라야 보입니다.
#       합성 PDF 로는 이 절의 교육 효과가 나오지 않습니다.
PDF_PATH = DATA / "학칙.pdf"

# 🔶 학교 공지 등 실제로 접근 가능한 주소로 바꾸십시오.
WEB_URL = "https://example.com/notice"


def show(name: str, docs) -> None:
    print("=" * 60)
    if not docs:
        print(f"[{name}]  건너뜀")
        return
    print(f"[{name}]  Document 개수: {len(docs)}")
    print("metadata:", docs[0].metadata)  # ★ 무엇이 '자동으로' 붙는가
    print("본문 앞 200자:")
    print(docs[0].page_content[:200].strip())
    print()


def load_text():
    """① 텍스트 — 파일 전체가 Document 1개. 구조 정보가 전혀 없다."""
    return TextLoader(str(DATA / "규정.txt"), encoding="utf-8").load()


def load_pdf():
    """② PDF — 페이지 단위로 쪼개진다. metadata 에 page 가 붙는다 ★"""
    if not PDF_PATH.exists():
        print("=" * 60)
        print(f"""[PDF]  건너뜀 — {PDF_PATH} 가 없습니다. 🔶

  ⚠️ 이 절의 핵심(파싱 난점)은 **진짜 PDF** 라야 보입니다.
     교수 준비물: 실제 학칙 PDF 를 data/학칙.pdf 로 두십시오.

     ┌─────────────────────────────────┐
     │  동양미래대학교 학칙        - 7 -│  ← 머리말·페이지 번호가 본문에 섞인다
     ├─────────────────────────────────┤
     │  제3장 휴학                      │
     │  ┌──────┬──────┬──────┐         │
     │  │ 구분  │ 기간  │ 비고  │        │  ← 표가 한 줄 텍스트로 뭉개진다 ⚠️
     │  └──────┴──────┴──────┘         │
     │  ① 일반휴학은 ...                │  ← 단이 나뉘면 순서가 뒤섞인다
     └─────────────────────────────────┘
""")
        return []

    try:
        from langchain_community.document_loaders import PyPDFLoader
    except ImportError:
        print("[PDF]  건너뜀 — pip install pypdf 가 필요합니다. 🔶")
        return []

    return PyPDFLoader(str(PDF_PATH)).load()


def load_csv():
    """③ CSV — 행 단위로 Document 가 만들어진다. 열 이름이 본문에 섞인다 ★"""
    return CSVLoader(str(DATA / "faq.csv"), encoding="utf-8").load()


def load_web():
    """④ 웹 — 메뉴·광고·푸터가 본문에 섞인다 ⚠️

    ⚠️ 30명이 같은 주소를 동시에 때리면 차단될 수 있습니다. 조별 순차 실행. ★
    """
    try:
        return WebBaseLoader(WEB_URL).load()
    except Exception as e:
        print(f"[Web]  건너뜀 — {type(e).__name__}: {str(e)[:60]} 🔶")
        return []


def main() -> None:
    show("Text", load_text())
    show("PDF", load_pdf())
    show("CSV", load_csv())

    if "--web" in sys.argv:
        show("Web", load_web())
    else:
        print("=" * 60)
        print("[Web]  건너뜀 — 켜려면: python loaders.py --web  (⚠️ 조별 순차 실행)\n")

    print("=" * 60)
    print("""
파싱 난점 — 무엇을 관찰할 것인가 ★

  | Loader | Document 개수  | 자동 metadata      | 난점                       |
  | Text   | 1개 (파일 전체) | source             | 구조 정보가 전혀 없음        |
  | PDF    | 페이지 수만큼   | source, page ★     | 머리말·표·다단·스캔본 ⚠️    |
  | CSV    | 행 수만큼       | source, row        | 열 이름이 본문에 섞임        |
  | Web    | 1개            | source, title      | 메뉴·광고·푸터가 섞임 ⚠️     |

  ⚠️ PDF 가 가장 까다롭습니다

    머리말·페이지 번호   모든 청크에 잡음이 섞임      → 전처리로 제거 (정규식)
    표                   행·열 관계가 사라짐          → 표 특화 파서 / 수동 정리
    다단 레이아웃        읽는 순서가 뒤바뀜           → 레이아웃 인식 파서
    스캔 PDF (이미지)    텍스트가 아예 없음 ⚠️        → OCR (본 과목 범위 밖)

  📌 "쓰레기를 넣으면 쓰레기가 나옵니다."
     RAG 프로젝트 시간의 상당 부분이 ① Load 와 ② Split 에 들어갑니다.

  💡 9주차 연결: WebBaseLoader 로 가져온 페이지에 주입 문장이 있다면?
     그대로 청크가 되어 벡터 저장소에 들어갑니다. 한 번 들어가면 계속 검색됩니다 ⚠️
     → "가져온 텍스트는 데이터다. 지시가 아니다." ★
""")


if __name__ == "__main__":
    main()
