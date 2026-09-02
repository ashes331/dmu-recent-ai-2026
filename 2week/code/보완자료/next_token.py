# 파일: next_token.py
# 보완A_LLM작동원리 4-2 실습 3 ★★ ― 다음 토큰 확률 Top-5 출력
#
# 실행 환경: Google Colab 권장 (torch·transformers 기설치)
#   Colab 에서는 이 파일 내용을 "셀 1" 에 붙여 넣습니다.
#
# 로컬 실행:  pip install torch transformers
#   ⏱️ 최초 1회 GPT-2 모델(약 500MB) 다운로드에 1~2분 걸립니다.
#
# "LLM 은 확률로 다음 토큰을 고른다"는 말을 화면에 숫자로 띄우는 것이 목적이다.

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# 모델과 토크나이저 불러오기 (최초 1회만 다운로드)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
model.eval()          # 추론 모드 (학습이 아님)


def top_k_next(prompt, k=5):
    """prompt 다음에 올 토큰의 확률 상위 k개를 출력한다."""
    inputs = tok(prompt, return_tensors="pt")     # ① 문자열 → 토큰 ID

    with torch.no_grad():                          # 기울기 계산 끄기 (추론만)
        logits = model(**inputs).logits            # ② 모델 통과 → 점수(logit)

    # logits shape: (배치, 토큰 개수, 어휘 크기)
    # 마지막 토큰 위치의 점수만 필요하다 → [0, -1, :]
    last = logits[0, -1, :]

    probs = torch.softmax(last, dim=-1)            # ③ 점수 → 확률 (합이 1)
    top = torch.topk(probs, k)                     # ④ 상위 k개

    print(f"입력: {prompt}")
    print("-" * 40)
    for rank, (p, idx) in enumerate(zip(top.values, top.indices), 1):
        word = tok.decode(idx)
        bar = "█" * int(p.item() * 100)
        print(f"{rank}위  {word!r:<14} {p.item()*100:6.2f}%  {bar}")
    print()


if __name__ == "__main__":
    top_k_next("Water boils at 100 degrees")

    print("관찰 포인트 ★")
    print("  · 1위가 100% 가 아니다. 확실한 답도 확률로 표현된다")
    print("  · ' F' 와 ' Fahrenheit', ' C' 와 ' Celsius' 가 각각 따로 잡힌다")
    print("    → 같은 의미라도 토큰이 다르면 확률이 나뉜다")
    print("  · 정답 후보들에 확률이 흩어져 있으므로")
    print("    뽑기 방식에 따라 답이 달라진다 (실습 4: temperature_demo.py)")
    print()
