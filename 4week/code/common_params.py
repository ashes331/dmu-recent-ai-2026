"""[3교시 / 1절] 공통 파라미터 4종 — temperature · max_tokens · timeout · max_retries

    앞의 둘은 '모델에게 주는 지시'
    뒤의 둘은 '호출을 어떻게 할 것인가'  ← 네트워크 계층이므로 상용 API에서 중요

관찰 포인트
    1) temperature 0.0 은 같은 질문에 거의 같은 답을 준다
    2) max_tokens 는 '요약해줘'가 아니라 그 지점에서 '자른다'   ★
       문장 중간에서 끊기는 것을 눈으로 확인시킬 것
    3) timeout / max_retries 는 로컬에서는 의미가 약하다 (인터넷을 안 타므로)
       ⚠️ ChatOllama 는 max_tokens · timeout · max_retries 를 에러 없이 무시한다
          (max_tokens 무시는 2교시 bind_params.py ④에서 실측했다)
          → 로컬의 길이 제한은 num_predict (이 파일도 num_predict 로 자른다)

실행:
    python common_params.py
"""

import sys

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

# 한글 윈도우 콘솔(cp949)은 이모지를 출력하지 못해 오류가 납니다.
# 모델이 이모지를 뱉어도 죽지 않도록, 못 찍는 글자는 ? 로 바꿔 출력합니다.
sys.stdout.reconfigure(errors="replace")

load_dotenv()

MODEL = "gemma3:4b"

QUESTION = "파이썬의 장점 3가지를 각각 한 문장으로 알려줘."


def demo_temperature() -> None:
    """같은 질문을 두 번씩 — 값이 낮으면 답이 거의 같다."""
    print("=" * 60)
    print("① temperature - 무작위성")
    print("=" * 60)

    for temp in (0.0, 0.9):
        # num_predict 로 짧게 끊습니다 — 앞부분만 봐도 차이가 드러나고, 수업이 빨라집니다
        llm = ChatOllama(model=MODEL, temperature=temp, num_predict=60)
        print(f"\n── temperature={temp} : 같은 질문을 두 번 ──")
        for i in (1, 2):
            answer = llm.invoke(QUESTION).content.replace("\n", " ")
            print(f"  [{i}회] {answer[:70]}...")

    print()
    print("  0 ~ 0.3 : 분류·추출·요약·JSON 출력 - 일관성이 중요할 때 (5주차 구조화 출력)")
    print("  0.7 ~ 1.0 : 아이디어 생성·창작")


def demo_max_tokens() -> None:
    """생성 길이 제한 — 잘린다는 것을 보여준다."""
    print()
    print("=" * 60)
    print("② 최대 생성 길이 - Ollama: num_predict / OpenAI: max_tokens  [이름이 다름]")
    print("=" * 60)

    llm = ChatOllama(model=MODEL, temperature=0.2, num_predict=40)
    print(llm.invoke(QUESTION).content)
    print()
    print("  [주의] '40토큰으로 요약해줘'가 아닙니다. 40토큰에서 잘립니다.")
    print("     문장 중간에서 끊기죠? 길이를 조절하려면 프롬프트로도 함께 요청해야 합니다.")
    print("     비용 상한을 거는 안전장치로 이해하는 것이 정확합니다.")


def demo_timeout_and_retries() -> None:
    """네트워크 계층 파라미터 — 코드만 보여주고 넘어간다."""
    print()
    print("=" * 60)
    print("③ timeout / ④ max_retries - 호출을 어떻게 할 것인가")
    print("=" * 60)
    print(
        """
    ChatOpenAI(model="...", timeout=30)      # 30초 안에 응답 없으면 포기
    ChatOpenAI(model="...", max_retries=2)   # 일시적 오류면 2번까지 다시 건다

    [주의] 둘 다 상용 API(ChatOpenAI)용입니다. ChatOllama 에 넣으면 에러 없이 무시됩니다.

        호출
          ├─ 성공 ─────────────────────▶ 끝
          └─ 실패 ─▶ max_retries 만큼 재시도
                        ├─ 성공 ────────▶ 끝
                        └─ 계속 실패 ─▶ 폴백(다른 모델)   ★ 실습 3

    [주의] 재시도가 듣는 것은 '일시적' 오류뿐입니다.
       잘못된 키·없는 모델명은 몇 번을 걸어도 실패합니다. → 그때 필요한 것이 폴백.

    [추가] 재시도 간격 - 지수 백오프(Exponential Backoff)
       바로 다시 걸지 않고, 실패할 때마다 기다리는 시간을 2배로 늘립니다.
       0.5초 → 1초 → 2초 → 4초 → 8초(상한)   (실제로는 0.75~1.0배로 조금씩 흔듦 = 지터)
       max_retries 만 쓰면 openai 라이브러리가 이미 해 줍니다. 직접 짤 필요 없음.
    """
    )


def main() -> None:
    demo_temperature()
    demo_max_tokens()
    demo_timeout_and_retries()


if __name__ == "__main__":
    main()
