"""[2교시 / 실습 2] LangChain 첫 호출 — ChatOllama

작년에는 ollama.chat() 을 직접 불렀습니다.
이번에는 LangChain 규격으로 감싼 ChatOllama 를 씁니다.

관찰 포인트
    1) 반환 타입이 문자열이 아니라 AIMessage "객체"다
    2) 텍스트는 .content 안에 있다
    3) invoke() 는 LangChain 모든 부품이 공유하는 실행 메서드다  ★

실행:
    python first_call.py
"""

import sys

from langchain_ollama import ChatOllama

# Windows 콘솔(cp949)은 모델이 뱉는 한자·이모지에서 UnicodeEncodeError 를 낸다.
# 출력 인코딩을 UTF-8 로 바꿔 둔다.
sys.stdout.reconfigure(encoding="utf-8")

# 실습실 모델이 다르면 이 한 줄만 고친다
MODEL = "gemma3:4b"


def main() -> None:
    # 1) 모델 객체 생성
    #    temperature: 0에 가까울수록 일관된 답, 1에 가까울수록 다양한 답
    llm = ChatOllama(model=MODEL, temperature=0.7)

    # 2) 호출 — 문자열을 그대로 넘길 수도 있다
    response = llm.invoke("파이썬의 장점 3가지를 각각 한 문장으로 알려줘.")

    # 3) 결과 확인
    print("반환 타입:", type(response))
    #    → <class 'langchain_core.messages.ai.AIMessage'>
    #      문자열이 아니라 객체로 돌아온다는 점에 주목
    print()
    print("── 응답 내용 ──────────────────────────────")
    print(response.content)  # 실제 텍스트는 .content 안에 있다
    print("──────────────────────────────────────────")

    # ── 응답 객체 들여다보기 ──────────────────────
    # 왜 객체로 돌려주나?
    #   텍스트만 주면 토큰 사용량·모델명·종료 이유를 알 수 없다.
    #   6주차 LangSmith 에서 이 메타데이터가 비용·성능 분석의 원천이 된다.
    print()
    print("메타데이터:", response.response_metadata)
    print("사용 토큰 :", response.usage_metadata)


if __name__ == "__main__":
    main()


