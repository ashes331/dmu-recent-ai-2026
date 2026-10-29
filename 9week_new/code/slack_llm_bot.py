"""[9주차 3교시 / 실습 2] ★★ 슬랙에서 묻고, 내 PC의 LLM 이 답한다

    @내앱이름 LCEL 이 뭐야?            → Ollama (기본, 무료)
    @내앱이름 openai LCEL 이 뭐야?     → OpenAI
    @내앱이름 비교 LCEL 이 뭐야?       → 둘 다 — 속도와 답을 나란히 본다

  전체 흐름

    슬랙 사용자 ── @멘션 ──▶ 슬랙 서버 ══ WebSocket (xapp) ══▶ 내 PC  slack_llm_bot.py
                                                                    │
                                                    ┌───────────────┴───────────────┐
                                                    ▼                               ▼
                                          Ollama  localhost:11434         OpenAI API (인터넷)
                                                    └───────────────┬───────────────┘
    슬랙 스레드 ◀── chat_postMessage / chat_update (xoxb) ──────────┘

★ 오늘의 요지 네 가지
  1) 먼저 "⏳ 생각 중" 을 달고, 답이 오면 그 메시지를 chat_update 로 고친다.
     LLM 은 수 초~수십 초 걸린다. 아무 반응이 없으면 사람은 다시 부른다.
  2) 실패해도 봇은 죽지 않는다. 5주차 send() 는 raise 했지만,
     봇은 '켜 두고 여러 사람이 쓰는 프로그램' 이다. 한 사람의 실패는 그 사람에게만 알린다.
  3) 슬랙 질문 1건 = LangSmith trace 1건. tags 로 week09-slack · ollama/openai 가 붙는다 (1교시).
  4) 슬랙 메시지는 '남이 쓴 입력' 이다 (2교시). 이 봇에는 도구가 없어서 주입이 '이상한 답' 에 머문다.
     도구를 붙이는 순간 2교시의 방어 4종(구분자·입력 검증·권한 최소화·사람 승인)이 필요해진다.

⚠️ 봇을 켜 두면 워크스페이스의 누구나 내 OpenAI 키로 질문할 수 있다 — 비용은 내 몫.
   .env 의 SLACK_ALLOWED_USERS 에 내 멤버 ID 를 적으면 openai 는 나만 쓴다.
   수업이 끝나면 Ctrl+C 로 봇을 끈다.

전제:
    실습 1(socket_hello.py) 에서 pong 이 와야 한다.
    python llm_backends.py 로 두 모델이 터미널에서 먼저 답해야 한다.

실행:
    python slack_llm_bot.py        # 끝낼 때는 Ctrl+C
"""

from dotenv import load_dotenv

load_dotenv()  # ★ 맨 위 — LANGSMITH_* 를 먼저 읽힌다

import os  # noqa: E402
import re  # noqa: E402

from slack_bolt import App  # noqa: E402
from slack_bolt.adapter.socket_mode import SocketModeHandler  # noqa: E402
from slack_sdk.errors import SlackApiError  # noqa: E402

from llm_backends import BACKENDS, ask, model_name  # noqa: E402  ← 실습 2 준비 파일 재사용 ★

DEFAULT_BACKEND = "ollama"  # 앞에 아무것도 안 붙이면 무료인 쪽으로
COMPARE_WORDS = ("비교", "vs")

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
# 쉼표로 여러 명 — 비워 두면 누구나 openai 를 쓸 수 있다
ALLOWED = {u.strip() for u in os.environ.get("SLACK_ALLOWED_USERS", "").split(",") if u.strip()}

if not BOT_TOKEN.startswith("xoxb-"):
    raise SystemExit("SLACK_BOT_TOKEN 은 xoxb- 로 시작해야 합니다.")
if not APP_TOKEN.startswith("xapp-"):
    raise SystemExit("SLACK_APP_TOKEN 은 xapp- 로 시작해야 합니다.")

app = App(token=BOT_TOKEN)

USAGE = (
    "이렇게 불러 주세요 🙂\n"
    "• `@봇 질문` — Ollama (기본)\n"
    "• `@봇 openai 질문` — OpenAI\n"
    "• `@봇 비교 질문` — 둘 다"
)


# ── 1. 메시지 → (어느 모델들, 질문) ──────────────────────────────
def parse(text: str) -> tuple[list[str], str]:
    text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()  # 앞의 <@U07ABCDEF> 를 떼어 낸다
    first, _, rest = text.partition(" ")
    key = first.lower()
    if key in BACKENDS:
        return [key], rest.strip()
    if key in COMPARE_WORDS:
        return list(BACKENDS), rest.strip()
    return [DEFAULT_BACKEND], text


def to_mrkdwn(answer: str) -> str:
    """LLM 은 **굵게** 로 쓰고, 슬랙은 *굵게* 로 읽는다."""
    return answer.strip().replace("**", "*")


# ── 2. 답하기 — 자리부터 잡고, 답이 오면 고친다 ★ ────────────────
def answer(event: dict, client) -> None:
    channel = event["channel"]
    thread = event.get("thread_ts") or event["ts"]
    user = event.get("user", "")
    backends, question = parse(event.get("text", ""))
    print(f"받음 ← user={user} {backends} {question!r}")

    if not question:
        client.chat_postMessage(channel=channel, thread_ts=thread, text=USAGE)
        return

    for backend in backends:
        if backend == "openai" and ALLOWED and user not in ALLOWED:
            client.chat_postMessage(
                channel=channel, thread_ts=thread,
                text="🔒 openai 는 이 봇 주인만 쓸 수 있습니다. 앞에 아무것도 붙이지 않으면 Ollama 가 답합니다.",
            )
            continue

        # ① 자리 잡기 — 사람은 반응이 없으면 다시 부른다
        holder = client.chat_postMessage(
            channel=channel, thread_ts=thread,
            text=f"⏳ {backend} ({model_name(backend)}) 가 생각 중입니다…",
        )

        # ② 모델 호출 — 실패해도 봇은 계속 산다 ★
        try:
            ans, sec = ask(backend, question, {"slack_user": user, "slack_channel": channel})
            text = f"{to_mrkdwn(ans)}\n\n_— {backend} · {model_name(backend)} · {sec:.1f}초_"
            print(f"  답함 → {backend} {sec:.1f}초")
        except Exception as e:
            text = f"⚠️ {backend} 실패 — `{type(e).__name__}: {str(e)[:200]}`"
            print(f"  실패 → {backend} {type(e).__name__}: {e}")

        # ③ 자리를 답으로 바꾼다 (chat:write 하나로 된다)
        client.chat_update(channel=channel, ts=holder["ts"], text=text)


# ── 3. 이벤트 연결 ──────────────────────────────────────────────
@app.event("app_mention")
def on_mention(event, client):
    answer(event, client)


@app.event("message")
def on_dm(event, client):
    # (선택) 봇에게 1:1 DM 으로 물을 때 — message.im 이벤트를 구독해야 온다
    # subtype 이 있는 것(수정·삭제·봇 메시지)은 건너뛴다
    if event.get("channel_type") == "im" and not event.get("subtype"):
        answer(event, client)


if __name__ == "__main__":
    print("=" * 60)
    print(f"기본 모델 : {DEFAULT_BACKEND} ({model_name(DEFAULT_BACKEND)})")
    print(f"openai 허용 : {', '.join(sorted(ALLOWED)) if ALLOWED else '누구나 ⚠️ 비용 주의'}")
    print("슬랙에서 @내앱이름 질문 / openai 질문 / 비교 질문.  끝낼 때는 Ctrl+C")
    print("=" * 60)
    try:
        SocketModeHandler(app, APP_TOKEN).start()
    except SlackApiError as e:
        raise SystemExit(f"앱 토큰으로 연결하지 못했습니다: {e.response['error']}  → 실습 1 socket_hello.py 부터 다시")
