"""[1교시 / 실습 0-③] 내가 만든 챗봇을 LangChain 코드에서 부르기

§3에서 Modelfile 로 py-tutor 를 만들었습니다.
    ollama create py-tutor -f Modelfile

이 모델도 ChatOllama(model="py-tutor") 로 그대로 부를 수 있습니다.
그런데 코드에서 설정을 주면, Modelfile 에 구워 둔 설정은 어떻게 될까요?  ★

확인 방법 — 답의 '내용'이 아니라 '토큰 수'를 봅니다
    답의 내용은 매번 달라 증거가 되지 못합니다.
    Modelfile 의 SYSTEM 이 붙으면 입력 토큰이 늘어나고,
    안 붙으면 원본 모델(gemma3:4b)과 입력 토큰 수가 같아집니다.

관찰 포인트
    ① 그냥 부르기               → SYSTEM · PARAMETER · MESSAGE 가 모두 붙는다
    ② 코드에서 system 을 주기   → Modelfile 의 SYSTEM 은 빠진다 (교체)  ★★
                                  ※ MESSAGE 예시 대화는 그대로 남는다
    ③ 코드에서 num_predict 주기 → PARAMETER 값(400)을 덮어쓴다

실행:
    ollama create py-tutor -f Modelfile     # 먼저 한 번
    python my_bot.py
"""

import sys

from langchain_ollama import ChatOllama

# 한글 윈도우 콘솔(cp949)은 이모지를 출력하지 못해 오류가 납니다.
# 모델이 이모지를 뱉어도 죽지 않도록, 못 찍는 글자는 ? 로 바꿔 출력합니다.
sys.stdout.reconfigure(errors="replace")

# 실습실 모델이 다르면 이 두 줄만 고친다 (BASE 는 Modelfile 의 FROM 과 같아야 함)
BASE_MODEL = "gemma3:4b"
BOT_MODEL = "py-tutor"

QUESTION = "리스트가 뭐야?"
CODE_SYSTEM = "당신은 친절한 비서입니다."


def ask(model: str, messages: list, **params):
    """모델을 한 번 부르고 (답, 입력 토큰, 출력 토큰) 을 돌려준다."""
    reply = ChatOllama(model=model, **params).invoke(messages)
    usage = reply.usage_metadata or {}
    return reply.content, usage.get("input_tokens"), usage.get("output_tokens")


def main() -> None:
    only_q = [("human", QUESTION)]
    with_sys = [("system", CODE_SYSTEM), ("human", QUESTION)]

    # ── ① 그냥 부르기 ─────────────────────────────────────
    #    원본은 토큰 수만 재면 되므로 num_predict=1 로 빨리 끝낸다
    _, base_in, _ = ask(BASE_MODEL, only_q, num_predict=1)
    answer, bot_in, bot_out = ask(BOT_MODEL, only_q)
    print("=" * 60)
    print(f"[1] 그냥 부르기 - '{QUESTION}'")
    print("=" * 60)
    print(answer)
    print("-" * 60)
    print(f"  입력 토큰  {BASE_MODEL:<10} {base_in:>4}")
    print(f"  입력 토큰  {BOT_MODEL:<10} {bot_in:>4}   <- SYSTEM + MESSAGE 가 붙어 늘어남")
    print(f"  출력 토큰  {BOT_MODEL:<10} {bot_out:>4}   (Modelfile num_predict 400 이내)")

    # ── ② 코드에서 system 을 주면 ─────────────────────────
    _, base_sys_in, _ = ask(BASE_MODEL, with_sys, num_predict=1)
    _, bot_sys_in, _ = ask(BOT_MODEL, with_sys, num_predict=1)
    print()
    print("=" * 60)
    print(f"[2] 코드에서 system 을 주면 - '{CODE_SYSTEM}'")
    print("=" * 60)
    print(f"  입력 토큰  {BASE_MODEL:<10} {base_sys_in:>4}")
    print(f"  입력 토큰  {BOT_MODEL:<10} {bot_sys_in:>4}")
    print(f"  차이 {bot_sys_in - base_sys_in} 토큰 = MESSAGE 예시 대화만 남은 몫")
    print("  -> Modelfile 의 SYSTEM 은 빠지고, 코드의 system 으로 '교체'되었습니다  ★★")

    # ── ③ 코드에서 num_predict 를 주면 ─────────────────────
    answer, _, cut_out = ask(BOT_MODEL, only_q, num_predict=20)
    print()
    print("=" * 60)
    print("[3] 코드에서 num_predict=20 을 주면 (Modelfile 에는 400)")
    print("=" * 60)
    print(answer)
    print("-" * 60)
    print(f"  출력 토큰 {cut_out}  -> 코드의 값이 Modelfile PARAMETER 를 덮어씀")

    print()
    print("[정리] Modelfile 은 '기본값'입니다. 코드에서 주면 코드가 이깁니다.")
    print("       그리고 2교시에서 ChatOpenAI 로 바꾸면 py-tutor 의 설정은 따라가지 않습니다.")
    print("       -> 모델을 갈아끼울 코드라면, 설정은 코드 쪽에 둡니다.")


if __name__ == "__main__":
    main()
