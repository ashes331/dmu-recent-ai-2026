"""[9주차 3교시 / 실습 1] ★ Socket Mode — 슬랙이 내 PC에 말을 건다

5주차 4교시는 '보내기' 만 했다.  내 PC ──▶ 슬랙  (chat_postMessage)
오늘은 '받기' 를 더한다.          내 PC ◀── 슬랙  (누가 봇을 @멘션하면)

  슬랙이 내 PC에 말을 거는 방법은 두 가지다.

    HTTP 방식      슬랙이 내 PC 주소로 요청을 보낸다
                   → 인터넷에서 보이는 공인 주소가 필요 (학교·집 공유기 뒤에선 안 됨)
    Socket Mode ★  내 PC가 먼저 슬랙에 연결(WebSocket)을 열어 두고 기다린다
                   → 밖으로 나가는 연결이라 공인 주소도, 포트 개방도 필요 없다

  그래서 토큰이 두 개다.
    SLACK_BOT_TOKEN (xoxb-)  보내는 선 — 5주차에 받은 것.  chat:write
    SLACK_APP_TOKEN (xapp-)  받는 선   — 오늘 받는 것.     connections:write

이 파일은 LLM 없이 "연결" 만 확인한다. 여기서 pong 이 와야 실습 2로 간다 ★

─────────────────────────────────────────────────────────────
사전 준비 (5주차에 만든 앱에 네 가지를 더한다 — api.slack.com/apps → 내 앱)
  (5주차 앱이 없으면 README «앱이 없을 때 — 매니페스트로 한 번에» 부터)

  ① Socket Mode 켜기     Settings → Socket Mode → Enable Socket Mode 켜기
                          → 토큰 이름(예: socket) 입력 → Generate
                          → xapp-... 복사 → .env 의 SLACK_APP_TOKEN
                          (scope 는 connections:write 가 자동으로 붙는다)
  ② 이벤트 구독          Features → Event Subscriptions → Enable Events 켜기
                          → Subscribe to bot events → Add Bot User Event
                          → app_mention  → Save Changes
                          (app_mentions:read 스코프가 자동으로 추가된다)
  ③ 재설치 ★            노란 배너 "reinstall your app" → 다시 설치 → 허용
                          ⚠️ 스코프가 늘었으므로 재설치 전까지는 이벤트가 안 온다
  ④ 채널에 봇이 있는지   5주차에 /invite 한 채널이면 그대로 된다
                          (봇이 없는 채널의 멘션은 봇에게 전달되지 않는다)

실행:
    python socket_hello.py
    → "Bolt app is running!" 이 보이면 슬랙에서   @내앱이름 안녕
      (macOS·Linux 에서는 앞에 ⚡️ 가 붙는다. Windows 는 글자만 나온다)
    → 스레드에 "pong 🏓" 이 달리면 성공.  끝낼 때는 Ctrl+C
"""

import os
import re

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

# ⚠️ 두 토큰을 바꿔 넣는 실수가 가장 흔하다 — 앞머리로 먼저 거른다
if not BOT_TOKEN.startswith("xoxb-"):
    raise SystemExit("SLACK_BOT_TOKEN 은 xoxb- 로 시작해야 합니다. (OAuth & Permissions → Bot User OAuth Token)")
if not APP_TOKEN.startswith("xapp-"):
    raise SystemExit("SLACK_APP_TOKEN 은 xapp- 로 시작해야 합니다. (Basic Information → App-Level Tokens)")

app = App(token=BOT_TOKEN)  # 만들 때 auth.test 로 xoxb 토큰을 한 번 확인한다


# ── 누군가 봇을 @멘션하면 이 함수가 불린다 ★ ─────────────────────
@app.event("app_mention")
def on_mention(event, say):
    #  event["text"] 는  "<@U07ABCDEF> 안녕"  처럼 멘션 표시가 앞에 붙어서 온다
    text = re.sub(r"<@[A-Z0-9]+>\s*", "", event["text"]).strip()
    print(f"받음 ← user={event['user']} channel={event['channel']} text={text!r}")

    say(
        text=f"pong 🏓  (받은 말: {text or '(없음)'})",
        thread_ts=event.get("thread_ts") or event["ts"],  # 원글의 스레드에 단다 (5주차 thread_ts)
    )


if __name__ == "__main__":
    print("=" * 60)
    print(f"봇 토큰 : {BOT_TOKEN[:9]}...{BOT_TOKEN[-4:]}   ← 앞뒤만 찍는다 ⚠️")
    print(f"앱 토큰 : {APP_TOKEN[:9]}...{APP_TOKEN[-4:]}")
    print("슬랙에서 @내앱이름 을 불러 보세요.  끝낼 때는 Ctrl+C")
    print("=" * 60)
    try:
        SocketModeHandler(app, APP_TOKEN).start()  # ★ 여기서 멈춰서 계속 기다린다
    except SlackApiError as e:  # 받는 선(xapp)을 여는 단계의 실패
        raise SystemExit(
            f"앱 토큰으로 연결하지 못했습니다: {e.response['error']}\n"
            "  invalid_auth → xapp 토큰 오타·폐기.  Basic Information → App-Level Tokens 에서 다시 복사\n"
            "  Socket Mode 를 켜지 않았다면 → Settings → Socket Mode → Enable"
        )
