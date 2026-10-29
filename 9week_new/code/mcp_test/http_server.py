"""[9주차 2교시 · 보충] MCP 서버를 HTTP 로 '띄워 두는' 방식

   mcp_server.py 와 도구는 똑같습니다(그대로 import). 바뀐 것은 실행 방법뿐입니다.

       stdio (mcp_server.py)                 HTTP (이 파일)
       ─────────────────────                 ───────────────────────────────
       클라이언트가 자식 프로세스로 띄움      내가 터미널에서 먼저 띄워 둠
       클라이언트가 끝나면 같이 종료          Ctrl+C 로 끌 때까지 계속 켜져 있음
       print() 쓰면 통신이 깨짐              print() 써도 됨 (통로가 HTTP)
       한 번에 클라이언트 하나               여러 클라이언트가 여러 번 접속

  ★ 터미널을 두 개 띄우십시오.
       터미널 1: python http_server.py     ← 켜 둔다
       터미널 2: python http_client.py     ← 실행할 때마다 터미널 1 에 POST /mcp 로그가 찍힌다

  ⚠️ host="127.0.0.1" — 내 PC 에서만 접속됩니다.
     "0.0.0.0" 으로 바꾸면 실습실의 다른 PC 도 내 도구를 실행할 수 있습니다.
     편의성과 보안은 반대 방향 → 2교시 §3

실행:
    python http_server.py        # 끌 때: Ctrl+C
    (포트를 바꾸려면 루트 .env 에 MCP_PORT=... — http_client.py 도 같은 값을 읽습니다)
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from mcp_server import mcp  # ★ 도구 정의는 mcp_server.py 의 것을 그대로 쓴다

MCP_PORT = int(os.getenv("MCP_PORT", "8011"))

if __name__ == "__main__":
    print(f"MCP 서버 시작: http://127.0.0.1:{MCP_PORT}/mcp   (끄기: Ctrl+C)")
    print("도구: word_count, add\n")
    mcp.run(transport="http", host="127.0.0.1", port=MCP_PORT, show_banner=False)
