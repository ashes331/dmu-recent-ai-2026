# 파일: token_demo.py
# 보완A_LLM작동원리 3-2 실습 2 ― 토큰화하고 되돌리기
#
# 대상: 「빅데이터분석프로젝트」 6주차 미이수자 (보완 자료)
#
# 실행:
#   pip install tiktoken
#   python token_demo.py

import tiktoken

# GPT-4o 계열이 사용하는 인코딩
enc = tiktoken.get_encoding("o200k_base")

text_ko = "안녕하세요, 저는 인공지능을 공부하는 학생입니다."
text_en = "Hello, I am a student studying artificial intelligence."

for name, text in [("한국어", text_ko), ("영어", text_en)]:
    ids = enc.encode(text)                       # 문자열 → 토큰 ID 목록
    pieces = [enc.decode([i]) for i in ids]      # 토큰 ID 하나씩 → 문자열 조각
    print(f"[{name}] 글자 수: {len(text)}  /  토큰 수: {len(ids)}")
    print(f"  토큰 ID : {ids}")
    print(f"  토큰 조각: {pieces}")
    print()

# 무손실 확인 ― 인코딩했다 디코딩하면 원문이 그대로 돌아온다
print("-" * 58)
print("  무손실 확인")
print("-" * 58)
for name, text in [("한국어", text_ko), ("영어", text_en)]:
    restored = enc.decode(enc.encode(text))
    print(f"  [{name}] 원문 복원 : {'성공' if restored == text else '실패'}")
print()

print("  관찰 포인트")
print("    · '안' + '녕하세요' ― 한 단어가 2조각으로 쪼개진다")
print("    · '인' + '공지' + '능' ― '인공지능'은 3조각이다")
print("    · 영어는 ' student' 처럼 앞 공백까지 한 토큰이다")
print("    · 글자 수는 한국어가 더 적은데 토큰 수는 더 많다")
print()
