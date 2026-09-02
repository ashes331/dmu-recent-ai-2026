# 파일: embed_02_search_compare.py
# 2주차 3교시 실습 3 ★ ― 키워드 검색 vs 의미 검색
#
# 이번 교시의 핵심 실습. RAG 가 왜 필요한지를 한 번에 보여준다.
#
# 실행 환경: Colab 권장
#   !pip install -q sentence-transformers

import numpy as np
from sentence_transformers import SentenceTransformer

# 한국어 임베딩 모델. 선택 근거는 embed_01_similarity.py 주석 참고.
MODEL_NAME = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

# 학과 안내 문서라고 가정한 5개 문장
DOCS = [
    "본 학과의 이수 요건은 총 130학점이다.",
    "전공필수 과목은 반드시 수강해야 하며 재수강이 제한된다.",
    "학생 식당은 평일 오전 11시부터 오후 2시까지 운영한다.",
    "도서관은 시험 기간에 24시간 개방한다.",
    "캡스톤디자인은 4학년 1학기에 이수하는 것을 권장한다.",
]

QUERY = "졸업하려면 몇 학점 들어야 해?"


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def keyword_search(query, docs):
    """방법 A ― Ctrl+F 방식. 질문을 띄어쓰기로 잘라 그대로 들어 있는지만 본다."""
    print("=" * 55)
    print("[A] 키워드 검색")
    print("=" * 55)

    keywords = query.replace("?", "").split()   # ['졸업하려면', '몇', '학점', '들어야', '해']
    print(f"  검색어: {keywords}")
    print()

    counts = []
    for i, doc in enumerate(docs):
        hits = [kw for kw in keywords if kw in doc]
        counts.append(len(hits))
        print(f"  문서{i}: 일치 {len(hits)}개 {hits}")

    # 최고 점수를 받은 문서가 여럿이면 키워드 검색은 순위를 매길 수 없다.
    best = max(counts)
    tied = [i for i, c in enumerate(counts) if c == best]
    print()
    print(f"  → 최고 일치 {best}개, 해당 문서 {tied}")
    if len(tied) > 1:
        print("     동점이라 순위를 매길 수 없다. 어느 쪽이 답인지 고를 방법이 없다.")
    return counts


def semantic_search(query, docs, model):
    """방법 B ― 임베딩으로 바꿔 각도를 비교한다."""
    print()
    print("=" * 55)
    print("[B] 의미 검색")
    print("=" * 55)

    q_vec = model.encode(query)
    d_vecs = model.encode(docs)

    scores = [(i, float(cosine(q_vec, v))) for i, v in enumerate(d_vecs)]
    scores.sort(key=lambda x: x[1], reverse=True)

    for rank, (i, score) in enumerate(scores, 1):
        mark = " ★" if rank == 1 else ""
        print(f"  {rank}위  유사도 {score:.4f}  문서{i}: {docs[i]}{mark}")

    return scores


def main():
    print()
    model = SentenceTransformer(MODEL_NAME)
    print(f"질문: {QUERY}")
    print()

    counts = keyword_search(QUERY, DOCS)
    scores = semantic_search(QUERY, DOCS, model)

    top_idx, top_score = scores[0]
    second_idx, second_score = scores[1]
    print()
    print("-" * 55)
    print("  관찰 포인트")
    print("-" * 55)
    print("  1) 키워드 검색이 정답을 골라낼 수 있는가")
    print(f"     정답 문서0 = {counts[0]}개, 무관한 문서1 = {counts[1]}개 → 동점이다.")
    print("     게다가 문서1이 걸린 이유는 '수강해야'에 '해'가 들어 있어서다.")
    print("     의미와 아무 상관없는 우연한 일치다. 순위를 매길 근거가 없다.")
    print(f"  2) 의미 검색 1위는 문서{top_idx} ({top_score:.4f}) "
          f"{'← 정답. 겹치는 단어에 기대지 않는다' if top_idx == 0 else '← 오답!'}")
    print(f"  3) 2위 문서{second_idx} ({second_score:.4f}) 가 올라온 이유 :")
    print("     '수강·과목'이 졸업 요건과 의미적으로 가깝기 때문")
    print()
    print("  이것이 RAG 의 첫 단계다.")
    print("  10~11주차에서 수천 개 문서로 확대하고, 더 똑똑한 검색 전략을 배운다.")
    print()

    # ── 확장 질문 (시간이 남으면) ─────────────────────────────
    # 질문을 바꾸면 1위가 바뀐다. 의미로 찾고 있다는 또 하나의 증거.
    print("=" * 55)
    print("[확장] 질문을 바꿔 보면")
    print("=" * 55)
    for q in ["밥 언제 먹을 수 있어?", "시험 기간에 공부할 데 없을까?"]:
        q_vec = model.encode(q)
        d_vecs = model.encode(DOCS)
        best = max(range(len(DOCS)), key=lambda i: cosine(q_vec, d_vecs[i]))
        print(f"  \"{q}\"")
        print(f"     → 1위: 문서{best}  {DOCS[best]}")
    print()
    print("  키워드 검색이 더 유리한 경우는 없을까?")
    print("    → 정확한 고유명사·코드·모델명 검색. 이것이 11주차 하이브리드 검색의 동기다.")
    print()


if __name__ == "__main__":
    main()
