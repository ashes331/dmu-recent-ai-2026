# 파일: attention_viz.py
# 보완B_Attention과Transformer 4장 실습 5 ★ ― Attention 가중치 시각화
#
# 실행 환경: Google Colab 권장
#   Colab 에서는 아래 세 부분을 각각 "셀 4 / 셀 5 / 셀 6" 으로 나눠 붙여 넣습니다.
#   로컬에서는 이 파일 하나를 그대로 실행하면 셋이 순서대로 돕니다.
#
# 로컬 실행:  pip install torch transformers matplotlib
#
# 확인할 것: "The animal didn't cross the street because it was too tired"
#   여기서 it 은 animal 인가 street 인가? 사람은 바로 안다. 모델도 그럴까?

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

LAYER, HEAD = 4, 3          # 144개(12층 × 12헤드) 중 '대명사 해석'을 담당하는 헤드


# ─────────────────────────────────────────────────────────
# 셀 4 ― Attention 꺼내기
# ─────────────────────────────────────────────────────────
tok = GPT2Tokenizer.from_pretrained("gpt2")

# ★ 중요: attention 값을 꺼내려면 attn_implementation="eager" 로 불러와야 한다
#   (기본값은 빠른 구현을 쓰는데, 그 경우 attention 값이 None 으로 나온다)
model = GPT2LMHeadModel.from_pretrained("gpt2", attn_implementation="eager")
model.eval()

sentence = "The animal didn't cross the street because it was too tired"
inputs = tok(sentence, return_tensors="pt")
tokens = [tok.decode(i) for i in inputs["input_ids"][0]]

with torch.no_grad():
    out = model(**inputs, output_attentions=True)   # ★ attention 반환 옵션

print("층(layer) 수 :", len(out.attentions))
print("shape (배치, 헤드, 보는쪽, 보이는쪽):", tuple(out.attentions[0].shape))
print("토큰:", tokens)
print()


# ─────────────────────────────────────────────────────────
# 셀 5 ― 'it' 이 무엇을 보는지 확인  ★★ 이 실습의 핵심
# ─────────────────────────────────────────────────────────
att = out.attentions[LAYER][0, HEAD].numpy()

it_index = [i for i, t in enumerate(tokens) if t.strip() == "it"][0]
row = att[it_index]

print(f"'it' 가 가장 많이 본 토큰 Top-5  (layer {LAYER}, head {HEAD})")
for rank, j in enumerate(row.argsort()[::-1][:5], 1):
    bar = "█" * int(row[j] * 40)
    print(f"  {rank}. {tokens[j]!r:<12} {row[j]:.3f}  {bar}")
print()

print("핵심 메시지 ★★")
print("  아무도 'it 은 animal 을 가리킨다'고 가르쳐 준 적이 없다.")
print("  모델이 다음 단어를 맞히는 훈련만으로 문법을 스스로 익힌 것이다.")
print()


# ─────────────────────────────────────────────────────────
# 셀 6 ― 히트맵으로 전체 보기
# ─────────────────────────────────────────────────────────
# [주의] 한글 폰트: matplotlib 기본 폰트에는 한글이 없어 축 이름을 한글로 쓰면
#   네모(□□□)로 깨진다. 그래서 축 이름을 영어로 쓴다.
try:
    import matplotlib.pyplot as plt
except ImportError:
    # 로컬에 matplotlib 이 없어도 위의 핵심 결과(셀 5)는 이미 나왔다.
    # 히트맵 대신 행렬을 표로 출력하고 끝낸다.
    print("[matplotlib 없음] 히트맵 대신 표로 출력합니다.  pip install matplotlib")
    print()
    print("        " + "".join(f"{t.strip()[:6]:>8}" for t in tokens))
    for i, t in enumerate(tokens):
        print(f"  {t.strip()[:6]:>6} " + "".join(f"{att[i, j]:>8.2f}" for j in range(len(tokens))))
    print()
    print("  행 = Query(보는 쪽), 열 = Key(보이는 쪽). 값이 클수록 많이 본다.")
    raise SystemExit(0)

fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(att, cmap="Blues")

ax.set_xticks(range(len(tokens)))
ax.set_yticks(range(len(tokens)))
ax.set_xticklabels(tokens, rotation=90)
ax.set_yticklabels(tokens)
ax.set_xlabel("Key  (seen)")
ax.set_ylabel("Query  (seeing)")
ax.set_title(f"GPT-2 Self-Attention  (layer {LAYER}, head {HEAD})")

fig.colorbar(im)
plt.tight_layout()
plt.show()
