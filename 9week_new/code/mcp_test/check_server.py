"""[9주차 2교시 · 보충] ① LLM 없이 MCP 서버를 직접 불러 본다

   모델을 붙이기 전에 서버가 제대로 도는지부터 확인합니다.

   check_server.py ──① 도구 목록 주세요──▶ mcp_server.py
                   ◀── 이름 · 설명 · 인자 스키마 ──
                   ──② add(2, 3) 실행해 주세요──▶
                   ◀── 5 ──

  ★ docstring 이 '설명'으로, 타입 힌트가 'JSON 스키마'로 바뀌어 전달됩니다.
     2교시 show_what_model_sees() 에서 본 것과 같은 모양입니다.

실행:
    python check_server.py
"""

import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from fastmcp import Client

# ★ Path 로 넘깁니다. 문자열 "mcp_server.py" 는 FastMCP 5 에서 막힐 예정입니다(경고가 뜸).
#   __file__ 옆의 파일을 가리키므로 어느 폴더에서 실행해도 찾습니다.
SERVER = Path(__file__).with_name("mcp_server.py")


async def main() -> None:
    async with Client(SERVER) as client:  # 서버를 자식 프로세스로 띄우고 연결
        print("── ① 도구 목록 ──")
        for t in await client.list_tools():
            print(f"{t.name}\n   설명: {t.description}\n   스키마: {t.input_schema}")

        print("\n── ② 실행 요청: add(a=2, b=3) ──")
        r = await client.call_tool("add", {"a": 2, "b": 3})
        print("결과:", r.data)


if __name__ == "__main__":
    asyncio.run(main())
