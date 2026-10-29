"""[9주차 2교시 · 보충] 띄워 둔 MCP 서버에 '주소로' 접속한다

   mcp_client.py 와 한 줄만 다릅니다.
       MCPAdapter(Path("mcp_server.py"))           ← 서버를 내가 띄운다 (stdio)
       MCPAdapter("http://127.0.0.1:8011/mcp")     ← 이미 떠 있는 서버에 접속 (HTTP) ★

   그 아래 흐름(bind_tools → tool_calls → ToolMessage → 최종 답변)은 그대로입니다.

  ⚠️ 먼저 다른 터미널에서 python http_server.py 를 켜 두십시오.
     안 켜면 연결 오류가 납니다.

실행:
    python http_client.py                  # 기본 질문 (word_count)
    python http_client.py "2 더하기 3은?"   # 질문을 바꿔서 — add 도 불러 보기
    python http_client.py -v               # 도구 목록 · tool_calls · ToolMessage 까지 자세히
"""

import asyncio
import os
import sys
import warnings

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 다른 import 보다 위 (LangSmith 환경변수를 먼저 읽혀야 함)

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core._api import LangChainBetaWarning

# langchain.mcp 는 베타라 import 할 때마다 경고가 뜹니다 — 오류가 아니므로 숨깁니다.
warnings.filterwarnings("ignore", category=LangChainBetaWarning)

from langchain.mcp import MCPAdapter
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# ⚠️ 도구 호출을 지원하는 모델이어야 합니다. gemma3:4b 는 지원하지 않습니다.
TOOL_MODEL = os.getenv("TOOL_MODEL", "llama3.2:3b")

MCP_PORT = int(os.getenv("MCP_PORT", "8011"))  # http_server.py 와 같은 값이어야 한다
SERVER_URL = f"http://127.0.0.1:{MCP_PORT}/mcp"

DEFAULT_QUESTION = "'나는 오늘 MCP를 배웠다' 는 몇 단어야? word_count 도구를 써."


async def main(question: str, verbose: bool) -> None:
    try:
        async with MCPAdapter(SERVER_URL) as adapter:  # ★ 주소로 접속 — 서버를 띄우지 않는다
            tools = await adapter.list_tools()
            by_name = {t.name: t for t in tools}
            if verbose:
                print("── 서버가 알려준 도구 ──")
                for t in tools:
                    print(f"{t.name}: {t.description}  인자={t.args}")
                print()

            llm = ChatOllama(model=TOOL_MODEL, temperature=0).bind_tools(tools)

            print("질문:", question)
            messages = [HumanMessage(question)]
            ai = await llm.ainvoke(messages)
            messages.append(ai)

            if verbose:
                print("\n── tool_calls ──")
                print(ai.tool_calls)
            if not ai.tool_calls:
                print("\n⚠️ 모델이 도구를 부르지 않았습니다 — 그대로 답했습니다:")
                print(ai.content)
                return

            for call in ai.tool_calls:
                tool_msg = await by_name[call["name"]].ainvoke(call)  # 실행은 떠 있는 서버에서
                if verbose:
                    print(f"\n── ToolMessage ({call['name']}) ──")
                    print(tool_msg.content)
                messages.append(tool_msg)

            final = await llm.ainvoke(messages)
            print("\n답변:", final.content)
    except Exception as e:
        # 서버를 안 켰을 때 — 긴 오류 추적 대신 할 일을 알려 준다
        if "connect" in f"{type(e).__name__} {e}".lower():
            print(f"\n⚠️ {SERVER_URL} 에 연결할 수 없습니다.")
            print("   다른 터미널에서 python http_server.py 를 먼저 켜 두십시오.")
            print("   (켜 두었다면 양쪽 MCP_PORT 가 같은지 확인)")
            return
        raise


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "-v"]
    print(f"모델: {TOOL_MODEL}   서버: {SERVER_URL}\n")
    asyncio.run(main(args[0] if args else DEFAULT_QUESTION, verbose="-v" in sys.argv))
