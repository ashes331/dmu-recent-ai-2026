"""[2교시 / 실습 3] ★ ollama.chat() vs ChatOllama — 같은 일을 두 방식으로

이번 주차의 핵심 실습입니다.
    방식 A — 작년 방식   : 공급자 전용 SDK (ollama)
    방식 B — 이번 학기   : LangChain (ChatOllama)

결과는 같습니다. 코드는 다릅니다.
    → 무엇이 좋아졌나?  그리고 무엇이 감춰졌나?  (균형 있게 판단할 것)

필요 패키지:
    pip install ollama langchain-ollama

실행:
    python compare_sdk.py
"""

import sys

# Windows 콘솔(cp949)은 모델이 뱉는 한자·이모지에서 UnicodeEncodeError 를 낸다.
# 출력 인코딩을 UTF-8 로 바꿔 둔다.
sys.stdout.reconfigure(encoding="utf-8")

MODEL = "gemma3:4b"
SYSTEM = "당신은 한 문장으로만 답하는 비서입니다."
QUESTION = "대한민국의 수도는?"


# ══════════════════════════════════════════════════
# 방식 A — 작년 방식 : 공급자 전용 SDK
# ══════════════════════════════════════════════════
def call_with_sdk() -> None:
    import ollama

    resp = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": QUESTION},
        ],
    )

    print("[A] ollama.chat()")
    print("   결과:", resp["message"]["content"].strip())
    print("   타입:", type(resp))
    # 결과를 꺼내려면 응답 구조를 외워야 한다:  resp["message"]["content"]
    # 키 이름을 틀리면 실행 후에야 KeyError 로 알게 된다.
    #
    # 🔶 수업 중 주의: 최신 ollama 패키지는 순수 dict 가 아니라
    #    ollama._types.ChatResponse 객체를 돌려준다(딕셔너리처럼 [] 접근은 그대로 됨).
    #    강의안 비교표의 "반환 타입: dict" 는 예전 버전 기준이므로,
    #    화면에 찍히는 타입이 다르면 이 점을 설명해 줄 것.
    #    → 핵심 논지는 그대로다: "공급자마다 응답 구조가 제각각이고,
    #      그 구조를 외워야 한다"


# ══════════════════════════════════════════════════
# 방식 B — 이번 학기 방식 : LangChain
# ══════════════════════════════════════════════════
def call_with_langchain() -> None:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_ollama import ChatOllama

    llm = ChatOllama(model=MODEL)
    resp = llm.invoke(
        [
            SystemMessage(content=SYSTEM),
            HumanMessage(content=QUESTION),
        ]
    )

    print("[B] ChatOllama.invoke()")
    print("   결과:", resp.content.strip())
    print("   타입:", type(resp))
    # 결과 접근은 항상 .content — 공급자가 바뀌어도 동일하다.


def main() -> None:
    call_with_sdk()
    print()
    call_with_langchain()

    print()
    print("=" * 60)
    print("""
관찰 — 무엇이 같고 무엇이 다른가

  항목          A: ollama.chat()              B: ChatOllama
  ─────────────────────────────────────────────────────────────
  결과 텍스트   같음                           같음
  결과 접근     resp["message"]["content"]     resp.content
  반환 타입     dict / ChatResponse *          AIMessage
                (* 패키지 버전에 따라 다름)
  메시지 표현   딕셔너리                       타입 객체
  오타 검출     실행 후 KeyError               에디터가 미리 잡음

여기까지는 큰 차이가 없어 보인다. 오히려 A 가 짧다.
진짜 차이는 아래 질문에서 드러난다 →  compare_sdk.py 하단 주석 참고
""")
    print("=" * 60)


# ══════════════════════════════════════════════════
# 4-2. 결정적 질문 — "OpenAI 로 바꾸려면?"  ★
# ══════════════════════════════════════════════════
#
# 방식 A — 전부 다시 쓴다
#
#     import ollama
#     resp = ollama.chat(model="gemma3:4b", messages=[...])
#     text = resp["message"]["content"]
#
#     # ↓ OpenAI 로 바꾸면 — 라이브러리·함수·응답 구조가 전부 다름
#     from openai import OpenAI
#     client = OpenAI()
#     resp = client.chat.completions.create(model="gpt-...", messages=[...])
#     text = resp.choices[0].message.content     # 접근 경로도 다르다!
#
# 방식 B — 한 줄이다
#
#     llm = ChatOllama(model="gemma3:4b")
#     # ↓ 이 줄만 바꾼다
#     llm = ChatOpenAI(model="gpt-...")
#
#     # 아래는 그대로
#     resp = llm.invoke([SystemMessage(...), HumanMessage(...)])
#     text = resp.content
#
#   → 4주차에서 로컬 Ollama ↔ OpenAI 2종 교체를 직접 해본다.
#
# ══════════════════════════════════════════════════
# 4-3. 균형 — 무엇이 감춰지는가  ⚖️
# ══════════════════════════════════════════════════
#
#   얻는 것                 대가
#   ─────────────────────────────────────────────────────────
#   모델 교체가 한 줄        실제 HTTP 요청이 어떻게 나가는지 안 보인다
#   공통 인터페이스          공급자 고유 기능은 못 쓰거나 우회해야 함
#   검증된 부품              버전 변화가 빨라 따라가야 한다
#   생태계·자료              간단한 작업엔 과한 의존성
#
#   상황                              A(전용 SDK)   B(LangChain)
#   ─────────────────────────────────────────────────────────
#   모델 하나만 쓰는 간단한 스크립트    ✅ 충분        과함
#   모델을 바꿔가며 비교해야 함         힘듦          ✅
#   RAG·에이전트처럼 부품이 많음        매우 힘듦      ✅
#   공급자 최신 기능을 바로 써야 함     ✅            지원 대기
#
#   결론: LangChain 이 모든 문제를 푸는 만능 도구는 아니다.
#         다만 이번 학기에 만들 것 — 검색·도구·상태가 얽힌 애플리케이션 — 에서는
#         직접 짜는 비용이 훨씬 크다. 그래서 쓴다.

if __name__ == "__main__":
    main()
