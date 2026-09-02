# 파일: embed_local_ollama.py
# 2주차 3교시 ― Colab 이 막혔을 때의 대비책
#
# 실습 2(유사도)와 실습 3(키워드 vs 의미 검색)을 로컬 Ollama 임베딩으로 그대로 진행한다.
# sentence-transformers / PyTorch 설치가 필요 없다.
#
# 준비:
#   ollama pull nomic-embed-text      # 10주차에도 쓰는 모델이라 어차피 필요하다
#   pip install ollama numpy
#
# 실행:
#   python embed_local_ollama.py
#
# ※ 임베딩 모델이 달라지면 유사도의 절대값도 달라진다. 대소 관계만 보면 된다.
#   문서와 질문은 반드시 "같은 모델"로 변환해야 한다는 원칙은 여기서도 그대로다.
#
# [경고] 반드시 수업 전에 한 번 실행해 볼 것 (2026-08-21 실측)
#   nomic-embed-text 는 영어 중심 모델이라 한국어에서 유사도 순위가 뒤집힌다.
#   실측: 질문 vs 졸업요건 0.73  <  질문 vs 학식메뉴 0.83   ← 역전
#         실습 3의 1위도 오답(문서1), 실습 4의 블록 구조도 나타나지 않음
#   즉 이 대비책은 "실행은 되지만 강의안의 결론을 보여주지는 못한다".
#
#   아래 self_check() 가 실행 첫머리에서 이를 자동 진단한다.
#   경고가 뜨면 수업에서는 결과를 그대로 보여주는 대신
#     · Colab(KR-SBERT) 결과 캡처를 띄우거나
#     · 이 실패 자체를 "한국어 지원이 모델 선택 기준인 이유"의 사례로 쓰는 것을 권한다.
#   더 나은 한국어 임베딩 모델을 로컬에 두려면 bge-m3(약 1.2GB) 검토가 필요하다.

import os

import numpy as np
import ollama

EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

SENTENCES = [
    "졸업하려면 몇 학점 들어야 해?",
    "본 학과의 이수 요건은 총 130학점이다.",
    "오늘 학식 메뉴가 뭐야?",
]

DOCS = [
    "본 학과의 이수 요건은 총 130학점이다.",
    "전공필수 과목은 반드시 수강해야 하며 재수강이 제한된다.",
    "학생 식당은 평일 오전 11시부터 오후 2시까지 운영한다.",
    "도서관은 시험 기간에 24시간 개방한다.",
    "캡스톤디자인은 4학년 1학기에 이수하는 것을 권장한다.",
]

QUERY = "졸업하려면 몇 학점 들어야 해?"

HEAT_TEXTS = [
    "졸업 이수 학점",
    "학위 취득 요건",
    "전공필수 과목",
    "학생 식당 운영 시간",
    "점심 메뉴 안내",
]


def encode(texts):
    """문장 목록을 (N, D) 배열로 바꾼다. SentenceTransformer.encode 와 같은 역할."""
    if isinstance(texts, str):
        texts = [texts]
    result = ollama.embed(model=EMBED_MODEL, input=texts)
    return np.array(result["embeddings"], dtype=np.float32)


def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def self_check():
    """이 모델이 강의안의 결론을 재현할 수 있는지 먼저 진단한다.

    실습 2의 대소 관계(졸업요건 > 학식)가 성립하지 않으면 경고를 띄운다.
    """
    v = encode(SENTENCES)
    s_doc = cosine(v[0], v[1])
    s_food = cosine(v[0], v[2])
    if s_doc > s_food:
        return True

    print("!" * 58)
    print("  경고 ― 이 임베딩 모델은 한국어 순위를 제대로 내지 못합니다")
    print("!" * 58)
    print(f"  질문 vs 졸업요건 {s_doc:.4f}  <  질문 vs 학식메뉴 {s_food:.4f}   ← 역전")
    print()
    print("  '의미가 가까우면 유사도가 높다'는 강의안의 결론이 이 모델로는 안 나옵니다.")
    print(f"  현재 모델 : {EMBED_MODEL}")
    print()
    print("  수업에서의 대처")
    print("    · Colab(KR-SBERT) 결과 캡처를 대신 띄운다, 또는")
    print("    · 이 실패 자체를 '한국어 지원이 모델 선택 기준인 이유'의 사례로 쓴다")
    print()
    print("  아래 출력은 참고용으로 그대로 진행합니다.")
    print("!" * 58)
    print()
    return False


def practice_2():
    print("=" * 58)
    print("  실습 2 ― 임베딩과 코사인 유사도")
    print("=" * 58)

    vectors = encode(SENTENCES)
    print("  벡터 shape:", vectors.shape)
    print("  0번 벡터 앞 5개:", np.round(vectors[0][:5], 4))
    print()

    s_doc = cosine(vectors[0], vectors[1])
    s_food = cosine(vectors[0], vectors[2])
    print(f"  질문 vs 졸업요건 : {s_doc:.4f}")
    print(f"  질문 vs 학식메뉴 : {s_food:.4f}")
    print(f"  → 졸업요건이 더 높은가 : {'예' if s_doc > s_food else '아니오'}")
    print()


def practice_3():
    print("=" * 58)
    print("  실습 3 ― 키워드 검색 vs 의미 검색")
    print("=" * 58)
    print(f"  질문: {QUERY}")
    print()

    keywords = QUERY.replace("?", "").split()
    print("  [A] 키워드 검색")
    total = 0
    for i, doc in enumerate(DOCS):
        hits = [kw for kw in keywords if kw in doc]
        total += len(hits)
        print(f"      문서{i}: 일치 {len(hits)}개 {hits}")
    print(f"      → 전체 일치 {total}개")
    print()

    print("  [B] 의미 검색")
    q_vec = encode(QUERY)[0]
    d_vecs = encode(DOCS)
    scores = sorted(
        ((i, cosine(q_vec, v)) for i, v in enumerate(d_vecs)),
        key=lambda x: x[1],
        reverse=True,
    )
    for rank, (i, score) in enumerate(scores, 1):
        mark = " ★" if rank == 1 else ""
        print(f"      {rank}위  유사도 {score:.4f}  문서{i}: {DOCS[i]}{mark}")
    print()


def practice_4():
    """matplotlib 이 없어도 되도록 유사도 행렬을 표로 출력한다."""
    print("=" * 58)
    print("  실습 4 ― 유사도 행렬 (표 출력)")
    print("=" * 58)

    vecs = encode(HEAT_TEXTS)
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)   # 정규화 → 내적 = 코사인
    sim = vecs @ vecs.T

    print("      " + "".join(f"{i:>7}" for i in range(len(HEAT_TEXTS))))
    for i in range(len(HEAT_TEXTS)):
        row = "".join(f"{sim[i, j]:>7.2f}" for j in range(len(HEAT_TEXTS)))
        print(f"  {i}  {row}   {HEAT_TEXTS[i]}")
    print()
    print(f"  학사 블록 0-1 = {sim[0, 1]:.2f}   식당 블록 3-4 = {sim[3, 4]:.2f}"
          f"   블록 사이 0-3 = {sim[0, 3]:.2f}")
    print("  → 주제별로 묶이는 블록 구조가 보이면 성공이다.")
    print()


def main():
    print()
    print(f"임베딩 모델 : {EMBED_MODEL}  (로컬 Ollama)")
    print()
    self_check()
    practice_2()
    practice_3()
    practice_4()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print(f"[실행 실패] {type(e).__name__}: {e}")
        print()
        print("  확인할 것")
        print("    1) Ollama 서버가 떠 있는가     :  ollama serve")
        print(f"    2) 임베딩 모델이 있는가         :  ollama pull {EMBED_MODEL}")
        print("    3) 패키지가 깔려 있는가        :  pip install ollama numpy")
        print()
