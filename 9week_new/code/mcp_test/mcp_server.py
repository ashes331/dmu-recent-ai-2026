"""[9주차 2교시 · 보충] MCP 서버 — 도구를 '내놓는' 쪽 (FastMCP)

   2교시의 @tool 과 거의 같습니다. 바뀐 것은 두 가지뿐입니다.
       @tool            →  @mcp.tool
       (파일 안에서 사용) →  mcp.run()  으로 바깥에 내놓는다

   docstring  → 도구 설명    (모델이 도구를 고르는 근거 ★)
   타입 힌트   → 인자 스키마  (빼면 모델이 인자를 못 채웁니다)

  ⚠️ 이 파일은 직접 실행하지 않습니다.
     check_server.py / mcp_client.py 가 자식 프로세스로 띄우고, 끝나면 종료합니다.
     (python mcp_server.py 로 띄우면 입력을 기다리며 멈춰 있을 뿐입니다)

  ⚠️ 이 파일에서는 print() 를 쓰지 않습니다.
     stdio 전송은 표준출력 자체가 클라이언트와의 통로라서, print 가 섞이면 통신이 깨집니다.
"""

from fastmcp import FastMCP

mcp = FastMCP("week9")  # 서버 이름


@mcp.tool  # ← 이 한 줄로 MCP 도구가 된다 ★
def word_count(text: str) -> int:
    """문장의 단어 수를 센다."""
    return len(text.split())


@mcp.tool
def add(a: int, b: int) -> int:
    """두 정수를 더한다."""
    return a + b


if __name__ == "__main__":
    mcp.run(show_banner=False)  # stdio 로 요청을 기다린다 (show_banner=False: 시작 로고 끄기)
