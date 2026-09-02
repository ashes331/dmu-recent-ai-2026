# 파일: embed_01_similarity.py
# 2주차 3교시 실습 2 ― 문장 임베딩과 코사인 유사도
#
# 실행 환경: Colab 권장
#   !pip install -q sentence-transformers
#
# 로컬에서 돌리려면:  pip install sentence-transformers numpy
#   ※ PyTorch 가 함께 깔린다. 실습실 PC에는 설치하지 않는 것이 2주차 방침이다.

import numpy as np
from sentence_transformers import SentenceTransformer

# 한국어 임베딩 모델 (최초 1회 다운로드 약 1~2분, 768차원)
#
# ※ 모델 선택 근거 ― 2026-08-21 실측
#   paraphrase-multilingual-MiniLM-L12-v2 (다국어 384차원) 는 한국어 성능이 떨어져
#   실습 3에서 오답(캡스톤디자인)을 1위로 올린다. 한국어 전용 모델로 교체했다.
#   이것이 곧 1-4절 "한국어 지원" 이 모델 선택 기준인 이유의 실제 사례다.
MODEL_NAME = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

SENTENCES = [
    "졸업하려면 몇 학점 들어야 해?",        # 0  질문
    "본 학과의 이수 요건은 총 130학점이다.",  # 1  정답 문서
    "오늘 학식 메뉴가 뭐야?",               # 2  무관한 문장
]


def cosine(a, b):
    """두 벡터 사이 각도의 코사인. 1에 가까울수록 의미가 유사하다."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def main():
    model = SentenceTransformer(MODEL_NAME)
    vectors = model.encode(SENTENCES)

    print()
    print("벡터 shape:", vectors.shape)          # (3, 768) ― 문장 3개, 각 768차원
    print("0번 벡터 앞 5개:", np.round(vectors[0][:5], 4))
    print()

    s_doc = cosine(vectors[0], vectors[1])
    s_food = cosine(vectors[0], vectors[2])

    print("질문 vs 졸업요건 :", round(float(s_doc), 4))
    print("질문 vs 학식메뉴 :", round(float(s_food), 4))
    print()

    print("-" * 58)
    print("  관찰 포인트")
    print("-" * 58)
    print(f"  1) shape 가 (3, {vectors.shape[1]})  ― 세 문장의 길이가 모두 다른데도")
    print("     → 문장 길이와 무관하게 항상 같은 개수의 숫자로 고정된다")
    print(f"  2) 졸업요건({s_doc:.4f}) > 학식({s_food:.4f}) 인가 : "
          f"{'예  ← 단어가 아니라 의미로 비교되고 있다' if s_doc > s_food else '아니오'}")
    print("  3) 벡터 값 자체는 사람 눈에 무의미하다. 비교용 좌표일 뿐이다.")
    print()
    print("  ※ 정확한 수치는 모델·버전에 따라 달라진다. 대소 관계만 보면 된다.")
    print()


if __name__ == "__main__":
    main()
