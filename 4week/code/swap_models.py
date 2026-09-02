"""[2교시 / 실습 1] ★★ 같은 체인에 모델만 갈아끼우고 측정한다

    chain = prompt | llm | parser
                      ▲
                      │
               여기만 바꾼다
        ┌─────────────┴─────────────┐
    ChatOllama(로컬)          ChatOpenAI(상용)

    prompt 그대로 · parser 그대로 · invoke 그대로     ← 오늘의 핵심 ★

관찰 포인트
    1) 바뀐 코드는 아래 models 딕셔너리의 '한 줄' 뿐이다        ★
    2) 두 모델이 교체 가능한 이유 = 같은 Runnable 규약(invoke)을 따르기 때문
    3) 총 소요 시간은 재지만 '첫 토큰까지'는 invoke 로 잴 수 없다
       → 3교시 실습 4(streaming.py)에서 채운다                 ★

⚠️ ChatAnthropic 은 쓰지 않습니다.
   Anthropic API 키가 필요하며, Claude Code 구독 계정으로는 호출할 수 없습니다.

실행:
    python swap_models.py
"""

import os
import sys
import time

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# 한글 윈도우 콘솔(cp949)은 이모지를 출력하지 못해 오류가 납니다.
# 모델이 이모지를 뱉어도 죽지 않도록, 못 찍는 글자는 ? 로 바꿔 출력합니다.
sys.stdout.reconfigure(errors="replace")

load_dotenv()  # 3주차에 만든 .env 에서 키를 읽는다  ★

# 실습실 모델이 다르면 이 한 줄만 고친다
LOCAL_MODEL = "gemma3:4b"
LOCAL_SMALL = "gemma3:1b"  # 상용 키를 못 쓸 때의 대체 비교용

# 🔶 상용 모델명은 자주 바뀝니다. 수업 전날 공식 문서에서 확인해 확정할 것 ★
OPENAI_MODEL = "gpt-4o-mini"

# ── 프롬프트와 파서는 한 번만 만든다. 끝까지 바뀌지 않는다 ──
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "당신은 프로그래밍 강사입니다. {level} 눈높이로 설명하세요."),
        ("human", "{topic}의 장점 3가지를 각각 한 문장으로 알려줘."),
    ]
)
parser = StrOutputParser()
INPUTS = {"level": "초보자", "topic": "파이썬"}


def build_models() -> dict:
    """바뀌는 것은 이 목록뿐입니다."""
    if os.getenv("OPENAI_API_KEY"):
        return {
            f"로컬 {LOCAL_MODEL}": ChatOllama(model=LOCAL_MODEL, temperature=0.2),
            f"OpenAI {OPENAI_MODEL}": ChatOpenAI(model=OPENAI_MODEL, temperature=0.2),
        }

    # ── 대체안: 상용 키가 없으면 로컬 2종으로 비교한다 ──
    #    코드 구조는 완전히 같습니다. 비교표의 '비용' 칸을
    #    'ollama ps 의 SIZE(메모리 점유)' 로 바꿔서 채우면 됩니다.  ★
    print("[주의] OPENAI_API_KEY 가 없습니다 → 로컬 2종 비교로 진행합니다.")
    print("   (.env 에 키를 넣으면 자동으로 로컬 ↔ OpenAI 비교가 됩니다)")
    print()
    return {
        f"소형 {LOCAL_SMALL}": ChatOllama(model=LOCAL_SMALL, temperature=0.2),
        f"중형 {LOCAL_MODEL}": ChatOllama(model=LOCAL_MODEL, temperature=0.2),
    }


def run_one(name: str, llm) -> dict:
    """한 모델을 돌리고 측정값을 돌려준다."""
    # 💡 파서를 빼면 AIMessage 객체가 그대로 온다 → 토큰 사용량을 볼 수 있다  ★
    #    StrOutputParser 는 문자열만 남기고 메타데이터를 버립니다.
    #    (호출을 두 번 하지 않으려고 여기서는 파서를 마지막에 따로 적용합니다.
    #     parser.invoke(msg) 가 곧 체인 끝의 parser 가 하던 일입니다.)
    chain_meta = prompt | llm

    t0 = time.perf_counter()
    msg = chain_meta.invoke(INPUTS)
    elapsed = time.perf_counter() - t0

    text = parser.invoke(msg)
    usage = msg.usage_metadata or {}  # 🔶 공급자·버전에 따라 비어 있을 수 있음

    print("=" * 60)
    print(f"[{name}]  총 소요 {elapsed:.2f}초")
    print("=" * 60)
    print(text)
    print()
    print("  usage_metadata:", usage or "(측정 불가)")

    return {
        "name": name,
        "elapsed": elapsed,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
    }


def print_summary(rows: list) -> None:
    """비교표(실습 2)에 그대로 옮겨 적을 수 있게 정리해서 보여준다."""
    print()
    print("=" * 60)
    print("측정 요약 - 실습 2 비교표에 옮겨 적으세요")
    print("=" * 60)
    print(f"  {'모델':<24} {'총 소요':>8} {'입력':>8} {'출력':>8} {'첫 토큰':>10}")
    for r in rows:
        i = r["input_tokens"] if r["input_tokens"] is not None else "측정불가"
        o = r["output_tokens"] if r["output_tokens"] is not None else "측정불가"
        print(f"  {r['name']:<24} {r['elapsed']:>7.2f}초 {i:>8} {o:>8} {'(3교시)':>10}")

    print()
    print("[대기] '첫 토큰까지' 칸은 invoke 로는 잴 수 없습니다.")
    print("       3교시 실습 4(streaming.py)에서 채웁니다.  ★")
    print()
    print("[비용] (입력 토큰 × 입력 단가) + (출력 토큰 × 출력 단가)")
    print("       단가는 외우지 마세요. 외울 것은 계산 구조 - 출력이 대체로 더 비쌉니다.")


def main() -> None:
    rows = [run_one(name, llm) for name, llm in build_models().items()]
    print_summary(rows)

    # ── ⚠️ '상용이 항상 좋다'로 끝내지 말 것 ────────────────
    # 이 프롬프트처럼 단순한 작업은 로컬 4B로 충분한 경우가 많습니다.
    # 작업 난이도에 따라 답이 달라진다는 것이 요점입니다.
    # 시간이 남으면 INPUTS 를 다단계 추론이 필요한 어려운 질문으로 바꿔
    # 한 번 더 돌려 차이를 보십시오.


if __name__ == "__main__":
    main()
