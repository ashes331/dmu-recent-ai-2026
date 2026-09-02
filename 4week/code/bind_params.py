"""[2교시 / 1절] ChatOllama 에 파라미터 붙이기

지난주에는 ChatOllama(model=...) 만 썼습니다. 오늘은 여기에 설정을 붙입니다.

붙이는 방법은 두 가지
    A) 생성자에 지정  — 그 객체 전체에 적용
    B) .bind() 로 덧붙이기 — 모델 객체 하나로 설정만 다른 체인을 파생시킬 때  ★
       (같은 방식이 9주차 도구 호출 bind_tools 에서 다시 나옵니다)

⚠️ 함정 — ChatOllama 의 .bind() 는 이름이 다릅니다  ★★
    base.bind(temperature=0.9)              → TypeError 로 죽습니다
    base.bind(options={"temperature": 0.9}) → 이렇게 써야 합니다

    ChatOpenAI 는 base.bind(temperature=0.9) 가 그대로 됩니다.
    같은 .bind() 인데 공급자마다 받는 형태가 다른 것 — 오늘 1-3절의 주제가
    파라미터 이름뿐 아니라 .bind() 에서도 똑같이 나타납니다.

관찰 포인트
    temperature 0.0 과 0.9 의 답이 얼마나 다른가 — 같은 프롬프트, 같은 모델인데도.

실행:
    python bind_params.py
"""

import sys

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# 한글 윈도우 콘솔(cp949)은 이모지를 출력하지 못해 오류가 납니다.
# 모델이 이모지를 뱉어도 죽지 않도록, 못 찍는 글자는 ? 로 바꿔 출력합니다.
sys.stdout.reconfigure(errors="replace")

# 실습실 모델이 다르면 이 한 줄만 고친다
MODEL = "gemma3:4b"

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "당신은 프로그래밍 강사입니다. {level} 눈높이로 설명하세요."),
        ("human", "{topic}의 장점 3가지를 각각 한 문장으로 알려줘."),
    ]
)
parser = StrOutputParser()
INPUTS = {"level": "초보자", "topic": "파이썬"}


def main() -> None:
    # ── 방법 A: 생성자에 지정 ─────────────────────────────
    llm = ChatOllama(
        model=MODEL,
        temperature=0.2,  # 1교시에서 본 그 파라미터
        num_predict=300,  # 최대 생성 토큰 수
        num_ctx=4096,     # 컨텍스트 창 크기  ← VRAM에 영향 ★ (1교시 계산)
    )
    print("=" * 60)
    print("[방법 A] 생성자에 지정 - temperature=0.2")
    print("=" * 60)
    print((prompt | llm | parser).invoke(INPUTS))

    # ── 방법 B: .bind() 로 나중에 덧붙이기 ────────────────
    #    모델 객체는 하나. 설정만 다른 체인을 두 개 파생시킨다.
    #
    #    ⚠️ ChatOllama 에서는 options={...} 로 감싸야 합니다.  ★★
    #       base.bind(temperature=0.9) 로 쓰면 TypeError 로 죽습니다.
    #       (bind 로 준 값이 Ollama 클라이언트에 그대로 전달되기 때문)
    #       ChatOpenAI 는 base.bind(temperature=0.9) 가 그대로 됩니다.
    #
    #    ⚠️ options 는 '덧붙이기'가 아니라 '통째 교체'입니다.
    #       생성자에서 준 num_predict·num_ctx 를 유지하려면 여기 같이 적어야 합니다.
    base = ChatOllama(model=MODEL)
    creative = base.bind(options={"temperature": 0.9, "num_predict": 300})
    strict = base.bind(options={"temperature": 0.0, "num_predict": 300})

    for label, bound in [("창의적 temperature=0.9", creative), ("엄격 temperature=0.0", strict)]:
        print()
        print("=" * 60)
        print(f"[방법 B] .bind() - {label}")
        print("=" * 60)
        print((prompt | bound | parser).invoke(INPUTS))

    # ── ⚠️ 여기서 짚을 것 ────────────────────────────────
    # num_predict 는 Ollama 고유 이름입니다.
    # 2교시 실습 1에서 ChatOpenAI 로 바꿔 끼울 때 이 이름은 먹지 않습니다.
    #   Ollama: num_predict   /   OpenAI: max_tokens
    # temperature 만 공통입니다. → 그래서 실습 1에서는 공통 파라미터만 씁니다.
    print()
    print("[주의] num_predict 는 Ollama 고유 이름, OpenAI 는 max_tokens 입니다.")
    print("       .bind() 도 마찬가지입니다 - Ollama 는 options={...} 로 감싸야 하고,")
    print("       OpenAI 는 bind(temperature=0.9) 가 그대로 됩니다.")
    print("       LangChain이 '모든 것'을 통일해 주지는 않습니다. (3교시 1절에서 정리)")


if __name__ == "__main__":
    main()
