# 파일: next_token_ko.py
# 보완A_LLM작동원리 4-3 실습 3 ― 한국어 모델로도 해보기
#
# 실행 환경: Google Colab 권장 ("셀 2")
# 로컬 실행:  pip install torch transformers
#
# 이 실습의 목적은 "모델이 사실을 아는 게 아니라 비슷한 자리에 자주 등장한 단어를
# 고를 뿐"이라는 것을 확인하는 데 있다. 환각의 정체가 여기서 드러난다.

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "skt/kogpt2-base-v2"                     # 한국어 GPT-2
tok_ko = AutoTokenizer.from_pretrained(MODEL)
model_ko = AutoModelForCausalLM.from_pretrained(MODEL)
model_ko.eval()


def top_k_ko(prompt, k=5):
    inputs = tok_ko(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model_ko(**inputs).logits[0, -1, :]
    probs = torch.softmax(logits, dim=-1)
    top = torch.topk(probs, k)
    print(f"[{prompt}]")
    for rank, (p, idx) in enumerate(zip(top.values, top.indices), 1):
        print(f"   {rank}위 {tok_ko.decode(idx)!r:<10} {p.item()*100:6.2f}%")
    print()


if __name__ == "__main__":
    top_k_ko("대한민국의 수도는")
    top_k_ko("오늘 날씨가 너무")

    print("핵심 질문 ★")
    print("  사람은 '대한민국의 수도는' 다음에 거의 100% '서울'이라고 답한다.")
    print("  그런데 모델은 서울에도 몇 % 밖에 주지 않고, '평양'이 바로 뒤를 따른다.")
    print()
    print("  왜 그런가")
    print("    ① 작고 오래된 모델이다 (약 1.25억 파라미터)")
    print("    ② 확률이 5만여 개 토큰에 얇게 퍼져 있다")
    print("    ③ '평양'이 상위권이라는 게 중요하다 ― 모델은 사실을 아는 게 아니라")
    print("       비슷한 자리에 자주 등장한 단어를 고르고 있을 뿐이다")
    print()
    print("  이것이 환각(Hallucination)의 정체다.")
    print()
