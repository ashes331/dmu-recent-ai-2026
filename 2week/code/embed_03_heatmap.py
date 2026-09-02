# 파일: embed_03_heatmap.py
# 2주차 3교시 실습 4 ― 유사도 행렬 히트맵
#
# 실행 환경: Colab 권장
#   !pip install -q sentence-transformers
#
# 한글 폰트가 깨지면 라벨을 번호로 대체한다. 실습 목적(블록 구조 확인)에는 지장이 없다.

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from sentence_transformers import SentenceTransformer

# 한국어 임베딩 모델. 선택 근거는 embed_01_similarity.py 주석 참고.
MODEL_NAME = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"

TEXTS = [
    "졸업 이수 학점",
    "학위 취득 요건",
    "전공필수 과목",
    "학생 식당 운영 시간",
    "점심 메뉴 안내",
]

# 이 순서대로 찾아보고 있는 것을 쓴다. 하나도 없으면 라벨을 번호로 대체한다.
KOREAN_FONTS = ["Malgun Gothic", "AppleGothic", "NanumGothic", "NanumBarunGothic"]


def setup_korean_font():
    """설치된 한글 폰트를 찾아 지정한다. 찾으면 True."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in KOREAN_FONTS:
        if name in installed:
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False    # 마이너스 기호 깨짐 방지
            return True
    return False


def print_matrix(sim, texts):
    """matplotlib 를 못 쓰거나 폰트가 없을 때를 대비한 표 출력."""
    print()
    print("      " + "".join(f"{i:>7}" for i in range(len(texts))))
    for i in range(len(texts)):
        row = "".join(f"{sim[i, j]:>7.2f}" for j in range(len(texts)))
        print(f"  {i}  {row}   {texts[i]}")
    print()


def main():
    model = SentenceTransformer(MODEL_NAME)

    # normalize_embeddings=True 로 벡터 길이를 1로 맞추면 내적 = 코사인 유사도
    vecs = model.encode(TEXTS, normalize_embeddings=True)
    sim = vecs @ vecs.T                              # 5x5 유사도 행렬

    print_matrix(sim, TEXTS)

    print("-" * 58)
    print("  관찰 포인트")
    print("-" * 58)
    print("  1) 대각선이 전부 1.00 ― 자기 자신과의 유사도")
    print("  2) 블록 구조가 보이는가")
    print(f"       학사 관련 (0,1,2) : 0-1 = {sim[0, 1]:.2f}")
    print(f"       식당 관련 (3,4)   : 3-4 = {sim[3, 4]:.2f}")
    print(f"       두 블록 사이      : 0-3 = {sim[0, 3]:.2f}   ← 확연히 낮다")
    print("     → 주제별로 자동으로 묶인다 = 의미 공간이 잘 만들어졌다")
    print("  3) 정규화 후 내적을 쓴 이유 : 코사인 유사도와 같아져 계산이 단순해진다")
    print()

    has_korean = setup_korean_font()
    labels = ([f"{i}: {t}" for i, t in enumerate(TEXTS)] if has_korean
              else [f"text {i}" for i in range(len(TEXTS))])
    if not has_korean:
        print("  ※ 한글 폰트를 찾지 못해 y축 라벨을 번호로 대체했다.")
        print("    Colab 에서 한글이 필요하면 아래를 실행한 뒤 런타임을 재시작한다.")
        print("      !apt-get -qq install fonts-nanum")
        print()

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(sim, cmap="YlOrRd", vmin=0, vmax=1)

    ax.set_xticks(range(len(TEXTS)))
    ax.set_yticks(range(len(TEXTS)))
    ax.set_xticklabels(range(len(TEXTS)))
    ax.set_yticklabels(labels)

    for i in range(len(TEXTS)):
        for j in range(len(TEXTS)):
            ax.text(j, i, f"{sim[i, j]:.2f}", ha="center", va="center", fontsize=9)

    plt.colorbar(im)
    plt.title("Sentence Similarity Matrix")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
