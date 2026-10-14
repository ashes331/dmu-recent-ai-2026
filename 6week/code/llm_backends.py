"""[4교시 / 실습 8 준비] OpenAI 와 Ollama — 같은 체인, 모델만 갈아 끼운다

슬랙을 붙이기 전에 **LLM 쪽만 따로** 확인하는 파일이다.
봇이 답을 안 할 때 "슬랙이 문제인가, 모델이 문제인가" 를 가르는 기준점이 된다 ★

    prompt | llm | StrOutputParser()
             └┬┘
       ChatOllama  (내 PC, 무료, 첫 호출이 느림)
       ChatOpenAI  (클라우드, 유료, 키 필요)

  4주차 swap_models.py 에서 본 그대로다 — 체인의 나머지는 한 글자도 안 바뀐다.

★ 6주차와의 연결
  .env 에 LANGSMITH_TRACING=true 가 있으면 슬랙 질문 1건이 LangSmith trace 1건이 된다.
  ask() 에 붙이는 tags · metadata 는 3교시 tags_metadata.py 와 같은 방식이다.

실행:
    python llm_backends.py                          # 두 모델에 같은 질문 (기본)
    python llm_backends.py ollama "LCEL 이 뭐야?"    # 하나만
    python llm_backends.py openai "LCEL 이 뭐야?"
"""

from dotenv import load_dotenv

load_dotenv()  # ★ 맨 위 — LANGSMITH_* 를 라이브러리보다 먼저 읽힌다 (1교시)

import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

MODEL = "gemma3:4b"            # Ollama — 실습실 모델이 다르면 이 한 줄만
OPENAI_MODEL = "gpt-4o-mini"   # OpenAI — 4·5주차와 같은 모델
MAX_OUT = 400                  # 답 길이 상한 (토큰) — 슬랙 한 화면 + OpenAI 비용 상한

BACKENDS = ("ollama", "openai")

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 대학 수업 슬랙 채널의 조교 봇이다. 한국어로 다섯 문장 이내로 답한다. "
            "모르면 모른다고 말한다.",
        ),
        ("human", "{question}"),
    ]
)


def build_llm(backend: str):
    """backend 이름으로 채팅 모델을 만든다. 임포트는 쓸 때만 한다."""
    if backend == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=MODEL, temperature=0.3, num_predict=MAX_OUT)

    if backend == "openai":
        # ⚠️ 키가 없으면 여기서 멈춘다 — 설정 오류는 호출 전에 잡는다 (5주차 실습 5와 같은 원칙)
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY 가 .env 에 없습니다.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=OPENAI_MODEL, temperature=0.3, max_tokens=MAX_OUT, timeout=60)

    raise ValueError(f"모르는 backend: {backend!r}  (가능: {', '.join(BACKENDS)})")


def model_name(backend: str) -> str:
    return MODEL if backend == "ollama" else OPENAI_MODEL


def ask(backend: str, question: str, meta: dict | None = None) -> tuple[str, float]:
    """질문 하나를 backend 로 보내고 (답, 걸린 초) 를 돌려준다."""
    chain = prompt | build_llm(backend) | StrOutputParser()

    start = time.perf_counter()
    answer = chain.invoke(
        {"question": question},
        config={
            "run_name": f"slack-answer ({backend})",   # LangSmith 목록에 보일 이름
            "tags": ["week06-slack", backend],          # ★ 3교시 — 필터용 라벨
            "metadata": {"model": model_name(backend), **(meta or {})},
        },
    )
    return answer, time.perf_counter() - start


def main() -> None:
    args = sys.argv[1:]
    backends = BACKENDS
    if args and args[0] in BACKENDS:
        backends = (args.pop(0),)
    question = " ".join(args) or "LangSmith 추적이 디버깅에 왜 도움이 되는지 설명해 줘."

    print("=" * 60)
    print("질문 :", question)
    print("=" * 60)

    for backend in backends:
        try:
            answer, sec = ask(backend, question, {"source": "terminal"})
        except Exception as e:  # 한쪽이 실패해도 다른 쪽은 확인한다
            print(f"\n[{backend}] 실패 — {type(e).__name__}: {e}")
            print("  → ollama: 'ollama serve' 가 떠 있나?  openai: .env 의 OPENAI_API_KEY 는?")
            continue
        print(f"\n[{backend} · {model_name(backend)} · {sec:.1f}초]")
        print(answer.strip())

    print("""
관찰 — 무엇을 볼 것인가

  관찰 항목                        의미
  ────────────────────────────────────────────────────────────────
  ollama 첫 실행이 유난히 느리다    모델을 메모리에 올리는 시간 (2교시 워밍업) ★
  두 번째 실행부터 빨라진다         이미 올라가 있다 — 봇은 켜 둔 채로 쓰는 프로그램
  openai 는 키가 없으면 멈춘다      설정 오류는 호출 전에 잡는다
  체인 코드는 하나다               모델만 바뀐다 (4주차 swap_models.py)

💡 여기서 두 모델이 다 답하면, 봇이 답을 안 할 때 범인은 슬랙 쪽이다.
""")


if __name__ == "__main__":
    main()
