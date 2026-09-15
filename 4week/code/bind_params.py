"""[2교시 / 2절] .bind() 와 공급자별 이름 — 틀려 보고, 조용히 무시되는 것을 실측한다

생성자에 설정을 주는 방법(방법 A)은 1교시 my_bot.py 에서 이미 해 봤습니다.
    ChatOllama(model="py-tutor", num_predict=20)   ← 코드에서 주면 코드가 이긴다
오늘은 두 가지를 새로 봅니다.
    B) .bind() 로 덧붙이기 — 모델 객체 하나로 설정만 다른 체인을 파생시킬 때  ★
       (같은 방식이 9주차 도구 호출 bind_tools 에서 다시 나옵니다)
    ★ 공급자를 바꾸면 이름이 달라지고, 어떤 이름은 에러 없이 무시됩니다

⚠️ 함정 — 같은 .bind() 인데 공급자마다 받는 모양이 반대입니다  ★★
    공급자 = 모델을 실제로 돌려 주는 쪽. 오늘은 Ollama(로컬 서버) · OpenAI(상용 API) 둘.
    .bind() 는 값을 각 회사 라이브러리에 그대로 넘깁니다.

    Ollama (ChatOllama) — ollama 의 Client.chat() 이 받음. temperature 는 options={...} 안쪽
        base.bind(temperature=0.9)              → TypeError 로 죽습니다
        base.bind(options={"temperature": 0.9}) → 이렇게 써야 합니다

    OpenAI (ChatOpenAI) — openai 의 chat.completions.create() 가 받음. temperature 는 맨 바깥 인자
        base.bind(temperature=0.9)              → 그대로 됩니다
        base.bind(options={"temperature": 0.9}) → 반대로 TypeError 로 죽습니다

이 파일이 보여 주는 것
    ② .bind(options={...})       — Ollama 에서 되는 형태 (틀려 보기: 표시한 줄을 고쳐 실행)
    ③ OpenAI 에 options=          — 반대로 TypeError        (키가 있을 때만)
    ④ ChatOllama(max_tokens=10)   — 에러 없이 무시된다 / num_predict=10 은 잘린다  ★★
    ⑤ ChatOpenAI(num_predict=300) — 경고 후 model_kwargs 로 옮겨져 요청에 실린다 (키가 있을 때만)
    ⑥ 이름 확인                    — 그 클래스가 아는 이름인가 (model_fields)

실행:
    python bind_params.py
"""

import os
import sys
import warnings

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# 한글 윈도우 콘솔(cp949)은 이모지를 출력하지 못해 오류가 납니다.
# 모델이 이모지를 뱉어도 죽지 않도록, 못 찍는 글자는 ? 로 바꿔 출력합니다.
sys.stdout.reconfigure(errors="replace")

load_dotenv()  # .env 에서 OPENAI_API_KEY 를 읽는다

# 실습실 모델이 다르면 이 한 줄만 고친다
MODEL = "gemma3:4b"

# 🔶 상용 모델명은 수업 전날 공식 문서에서 확인해 확정할 것
OPENAI_MODEL = "gpt-4o-mini"

QUESTION = "파이썬의 장점 3가지를 각각 한 문장으로 알려줘."


def title(text: str) -> None:
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)


def demo_bind() -> None:
    title("② .bind() - 모델 객체는 하나, 설정만 덧붙인다")
    base = ChatOllama(model=MODEL)

    # ⚠️ ChatOllama 에서는 options={...} 로 감싸야 합니다.  ★★
    #    틀려 보기: 아래 줄을  short = base.bind(temperature=0.9)  로 고쳐 실행해 보세요.
    #    → .bind() 줄이 아니라 invoke 할 때 TypeError 가 납니다.
    #
    # ⚠️ options 는 '덧붙이기'가 아니라 '통째 교체'입니다.
    #    생성자에서 준 num_predict · num_ctx 를 유지하려면 여기 같이 적어야 합니다.
    short = base.bind(options={"temperature": 0.2, "num_predict": 60})

    answer = short.invoke(QUESTION).content.replace("\n", " ")
    print(f"  {answer[:90]}...")


def demo_openai_options(has_key: bool) -> None:
    title("③ OpenAI 에 Ollama 형태(options=)로 주면 - 반대로 TypeError")
    if not has_key:
        print("  [건너뜀] OPENAI_API_KEY 가 없습니다.")
        print("           (ChatOpenAI 는 키가 없으면 객체를 만들 때부터 막힙니다)")
        return

    try:
        ChatOpenAI(model=OPENAI_MODEL).bind(options={"temperature": 0.9}).invoke("hi")
    except TypeError as e:
        print(f"  TypeError: {e}")
        print("  → 요청을 보내기 전에 파이썬에서 막힙니다. 비용은 0원입니다.")


def demo_silent_ignore() -> None:
    title("④ 조용히 무시되는 이름 - ChatOllama 에 OpenAI 이름(max_tokens)을 주면")
    cases = [
        ("max_tokens=10  (OpenAI 이름)", ChatOllama(model=MODEL, max_tokens=10)),
        ("num_predict=10 (Ollama 이름)", ChatOllama(model=MODEL, num_predict=10)),
    ]
    for label, llm in cases:
        msg = llm.invoke(QUESTION)
        out = (msg.usage_metadata or {}).get("output_tokens")
        reason = msg.response_metadata.get("done_reason")
        print(f"  {label} → 출력 {out} 토큰 · done_reason={reason}")

    print("  → 두 줄 모두 에러가 없었습니다. 10에서 잘린 것(length)은 num_predict 쪽뿐입니다.")
    print("    에러가 나면 다행이고, 조용히 무시되면 위험합니다.")


def demo_openai_name_warning(has_key: bool) -> None:
    title("⑤ OpenAI 에 Ollama 이름(num_predict)을 주면 - 경고 후 요청에 그대로 실린다")
    if not has_key:
        print("  [건너뜀] OPENAI_API_KEY 가 없습니다.")
        return

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        llm = ChatOpenAI(model=OPENAI_MODEL, num_predict=300)  # 만들기만 — 호출하지 않는다

    for w in caught:
        print(f"  [경고] {' '.join(str(w.message).split())}")
    print(f"  model_kwargs = {llm.model_kwargs}  ← 이 값이 요청 본문에 그대로 실립니다")
    print("  → 조용히 무시되지는 않지만 OpenAI 가 모르는 이름입니다. OpenAI 이름은 max_tokens")


def demo_fields() -> None:
    title("⑥ 이름 확인 - 그 클래스가 아는 이름인가 (model_fields)")
    for cls in (ChatOllama, ChatOpenAI):
        for name in ("num_predict", "max_tokens"):
            known = "있음" if name in cls.model_fields else "없음"
            print(f"  {cls.__name__:<11} '{name}' : {known}")


def main() -> None:
    has_key = bool(os.getenv("OPENAI_API_KEY"))

    print("[방법 A · 1교시 복습] 생성자에 지정 - ChatOllama(model=..., temperature=0.2, num_predict=300)")
    print("                     1교시 my_bot.py 에서 해 봤으므로 여기서는 호출하지 않습니다.")

    demo_bind()
    demo_openai_options(has_key)
    demo_silent_ignore()
    demo_openai_name_warning(has_key)
    demo_fields()

    print()
    print("[정리] temperature 는 공통, 최대 길이는 Ollama num_predict / OpenAI max_tokens.")
    print("       .bind() 도 공급자마다 받는 모양이 반대입니다.")
    print("       LangChain 이 '모든 것'을 통일해 주지는 않습니다.")
    print("       3교시 1절은 이 표에 timeout · max_retries 두 줄만 더합니다.")


if __name__ == "__main__":
    main()
