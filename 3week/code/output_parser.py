"""[3교시 / 2절] StrOutputParser — 출력을 다듬는 부품

2교시에서 매번 이렇게 썼습니다.

    response = llm.invoke(...)
    text = response.content      # ← 항상 이 한 줄이 붙는다

체인으로 연결하려면 이 변환도 "부품"이어야 합니다.

    파서                 역할                        다루는 주차
    ────────────────────────────────────────────────────────────
    StrOutputParser      AIMessage → 순수 문자열      3주차 (지금)
    JSON / Pydantic 파서 텍스트 → 구조화된 객체       5주차

실행:
    python output_parser.py
"""

import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

# Windows 콘솔(cp949)은 모델이 뱉는 한자·이모지에서 UnicodeEncodeError 를 낸다.
# 출력 인코딩을 UTF-8 로 바꿔 둔다.
sys.stdout.reconfigure(encoding="utf-8")

MODEL = "gemma3:4b"


def main() -> None:
    llm = ChatOllama(model=MODEL)
    parser = StrOutputParser()

    # 1) 모델 호출 → AIMessage
    response = llm.invoke("파이썬을 한 문장으로 소개해줘.")
    print("모델 반환 타입:", type(response))  # AIMessage

    # 2) 파서에 넣으면 → str
    result = parser.invoke(response)
    print("파서 반환 타입:", type(result))  # <class 'str'>
    print()
    print("결과:", result.strip())

    print()
    print("=" * 60)
    print("""
세 부품의 공통점

    ChatPromptTemplate   .invoke(dict)        → messages
    ChatOllama           .invoke(messages)    → AIMessage
    StrOutputParser      .invoke(AIMessage)   → str

발견: 셋 다 .invoke() 를 가지고 있고,
      앞 부품의 출력이 그대로 뒤 부품의 입력이다.

      → 그렇다면 이어 붙일 수 있지 않을까?   (first_chain.py 로)
""")
    print("=" * 60)


if __name__ == "__main__":
    main()
