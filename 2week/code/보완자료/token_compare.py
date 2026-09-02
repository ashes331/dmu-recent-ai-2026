# 파일: token_compare.py
# 보완A_LLM작동원리 3-3 실습 2 ― 모델마다 토크나이저가 다르다 ★
#
# 실행:
#   pip install tiktoken
#   python token_compare.py

import tiktoken

text_ko = "안녕하세요, 저는 인공지능을 공부하는 학생입니다."
text_en = "Hello, I am a student studying artificial intelligence."

counts = {}
for model in ["gpt-4", "gpt-4o"]:
    enc = tiktoken.encoding_for_model(model)
    n_ko, n_en = len(enc.encode(text_ko)), len(enc.encode(text_en))
    counts[model] = n_ko
    print(f"{model:<8} ({enc.name:<12}) "
          f"한국어 {n_ko:>3}토큰 / 영어 {n_en:>3}토큰")

# 한국어 토큰 효율이 얼마나 개선됐는지 숫자로 보여준다
old, new = counts["gpt-4"], counts["gpt-4o"]
print()
print(f"  한국어 토큰 {old} → {new}  ({(old - new) / old * 100:.0f}% 감소)")
print("  토크나이저가 개선되면서 한국어 사용 비용이 거의 절반이 되었다.")
print()
print("  응용 과제: 본인이 자주 쓰는 프롬프트를 넣어 두 모델의 토큰 수를 비교해 보세요.")
print("            하루 100번 호출하면 한 달에 얼마나 차이 날까요?")
print()
