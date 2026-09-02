# 파일: temperature_demo.py
# 보완A_LLM작동원리 5-2 실습 4 ― temperature 바꿔보기
#
# 실행 환경: Google Colab 권장 ("셀 3")
#
# ※ Colab 에서는 셀 1(next_token.py)에서 만든 tok·model 을 그대로 씁니다.
#   이 파일은 단독 실행도 되도록 모델을 직접 불러옵니다.
#   (셀 1을 이미 실행했다면 아래 두 줄은 건너뛰어도 됩니다)

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
model.eval()

inputs = tok("The capital of France is", return_tensors="pt")

for t in [0.1, 0.7, 1.5]:
    torch.manual_seed(42)                    # 결과 재현을 위해 시드 고정
    out = model.generate(
        **inputs,
        max_new_tokens=20,
        do_sample=True,                      # 뽑기 방식 사용
        temperature=t,
        top_p=0.9,
        pad_token_id=tok.eos_token_id,
    )
    print(f"[temperature={t}]")
    print("  ", tok.decode(out[0], skip_special_tokens=True))
    print()

print("관찰 포인트")
print("  · 0.1 ― 같은 표현을 반복한다. 안전하지만 단조롭다")
print("  · 0.7 ― 'Paris'는 나오지만 엉뚱한 내용이 붙는다")
print("  · 1.5 ― 문장은 그럴듯한데 내용이 완전히 사실무근이다")
print()
print("  세 경우 모두 문법적으로는 완벽하다.")
print("  모델은 '말이 되게' 만들 뿐, '사실인지'는 전혀 검증하지 않는다.")
print()
print("  응용 과제: temperature 를 0.3 / 1.0 / 2.0 으로, top_p 를 0.5 / 1.0 으로")
print("            바꿔 보세요. 어떤 조합이 번역·요약에 맞고,")
print("            어떤 조합이 브레인스토밍에 맞을까요?")
print()
