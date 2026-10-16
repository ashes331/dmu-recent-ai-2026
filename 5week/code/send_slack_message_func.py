"""send_slack_message.py 를 다른 파일에서 import 해서 쓰는 모듈 판

사용법:
    from send_slack_message_func import send_slack_message

    ts = send_slack_message("분석이 끝났습니다")                 # 기본 채널로 전송
    send_slack_message("스레드 댓글", thread_ts=ts)               # 위 메시지의 스레드로
    send_slack_message("다른 채널로", channel="#다른-채널")        # 채널 지정

send_slack_message.py 와 다른 점
  · import 하는 순간에는 아무 일도 하지 않는다 (토큰 검사·접속은 처음 보낼 때 한다)
  · 토큰이 없으면 프로그램을 끝내지(SystemExit) 않고 RuntimeError 를 낸다
    → 부르는 쪽에서 try/except 로 잡을 수 있다
  · 채널을 인자로 바꿀 수 있다 (안 주면 .env 의 SLACK_CHANNEL, 없으면 #수업-출력물)

사전 준비(앱 생성·chat:write·토큰·/invite)는 send_slack_message.py 와 같다.

실행(동작 확인용):
    python send_slack_message_func.py "보낼 내용"
"""

import os
import sys

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()  # .env 를 환경변수로 읽어들인다

DEFAULT_CHANNEL = "#수업-출력물"

# ── 에러 대응표 ★ ───────────────────────────────────────────────
#    대부분 코드 문제가 아니라 사전 준비 ①~④ 중 하나를 건너뛴 문제다.
HINTS = {
    "not_in_channel": "  → ④단계 누락. 슬랙 채널에서  /invite @앱이름  을 실행하세요.",
    "missing_scope": "  → ②단계 누락, 또는 스코프를 추가하고 '재설치' 를 안 했습니다.\n"
                     "     chat:write 추가 후 반드시 Install 을 다시 누르세요.\n"
                     "     (이미 발급된 토큰에는 추가한 권한이 들어 있지 않습니다)",
    "channel_not_found": "  → 채널명 오타이거나 비공개 채널입니다.\n"
                         "     '#' 을 포함했는지 확인하거나, 채널 ID(C01ABCD...)를 쓰세요.",
    "invalid_auth": "  → 토큰이 틀렸거나 재발급되었습니다.\n"
                    "     .env 의 앞뒤 따옴표·공백이 흔한 범인입니다.",
    "token_revoked": "  → 토큰이 폐기되었습니다. 앱을 다시 설치해 새 토큰을 받으세요.",
    "ratelimited": "  → 너무 빠르게 반복 호출했습니다. 반복문에 time.sleep(1) 을 넣으세요.",
}

_client: WebClient | None = None  # 처음 보낼 때 한 번만 만들고 재사용한다


def _get_client() -> WebClient:
    """WebClient 를 처음 필요할 때 만든다. 토큰이 없으면 RuntimeError."""
    global _client
    if _client is None:
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError(
                "SLACK_BOT_TOKEN 이 없습니다.\n"
                "  1) .env.example 을 복사해 .env 로 만든다\n"
                "  2) SLACK_BOT_TOKEN=xoxb-... 를 채운다\n"
                "  3) 따옴표와 앞뒤 공백을 넣지 않는다  ← invalid_auth 의 흔한 범인"
            )
        _client = WebClient(token=token)
    return _client


# ── 이 함수 하나를 import 해서 쓴다 ★ ────────────────────────────
def send_slack_message(
    text: str,
    channel: str | None = None,
    thread_ts: str | None = None,
) -> str:
    """슬랙 채널에 text 를 보내고, 보낸 메시지의 타임스탬프(ts)를 돌려준다.

    channel   : 안 주면 .env 의 SLACK_CHANNEL, 그것도 없으면 #수업-출력물
    thread_ts : 주면 그 메시지의 '스레드 댓글' 로 달린다

    실패하면 원인 안내를 출력한 뒤 SlackApiError 를 그대로 raise 한다.
    (체인 안에서 쓸 때 실패가 조용히 묻히면 안 되므로)
    """
    channel = channel or os.environ.get("SLACK_CHANNEL", DEFAULT_CHANNEL)
    try:
        res = _get_client().chat_postMessage(  # ★ 핵심 한 줄
            channel=channel,
            text=text,
            thread_ts=thread_ts,
        )
        print(f"전송 성공 → {channel} (ts={res['ts']})")
        return res["ts"]

    except SlackApiError as e:
        code = e.response["error"]
        print(f"전송 실패: {code}")
        print(HINTS.get(code, "  → api.slack.com/methods/chat.postMessage 의 Errors 표를 확인하세요."))
        raise


if __name__ == "__main__":
    # 직접 실행했을 때만 도는 동작 확인 코드 — import 할 때는 실행되지 않는다
    message = sys.argv[1] if len(sys.argv) > 1 else "send_slack_message_func 동작 확인 메시지입니다."
    try:
        send_slack_message(message)
    except (RuntimeError, SlackApiError) as e:
        if isinstance(e, RuntimeError):
            print(e)
        raise SystemExit(1)
