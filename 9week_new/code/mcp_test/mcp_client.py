"""[9주차 2교시 · 보충] ② MCP 서버의 도구를 LangChain 모델에 붙인다

   ① MCPAdapter 가 서버를 띄우고 도구 목록을 받아 LangChain 도구로 바꾼다
            │
            ▼
   ② bind_tools(tools)                        ← 2교시와 같음
            │
            ▼
   ③ 모델이 판단 → tool_calls 반환            ← 실행은 안 한다, '요청'만 ★
            │
            ▼
   ④ 도구 실행 → 요청이 MCP 서버로 전달 → ToolMessage
            │
            ▼
   ⑤ ToolMessage 를 붙여 다시 호출 → 최종 답변

  ★★ 2교시 tool_flow.py 와 비교하십시오
        모델 쪽 흐름(②~⑤)은 한 글자도 안 바뀝니다.
        바뀐 것은 ① — 도구를 '내 파일'에서 가져오느냐, 'MCP 서버'에 물어보느냐 뿐입니다.

  ⚠️ 남의 MCP 서버를 꽂으면 그 서버의 설명·결과가 그대로 모델에 들어갑니다.
     편의성과 보안은 반대 방향 → 2교시 §3 간접 주입

실행:
    python mcp_client.py         # 질문과 최종 답변만
    python mcp_client.py -v      # 도구 목록 · tool_calls · ToolMessage 까지 자세히
"""

import asyncio
import os
import sys
import warnings
from pathlib import Path

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
#    2교시 tool_flow.py 와 같은 llama3.2:3b — 없으면: ollama pull llama3.2:3b
TOOL_MODEL = os.getenv("TOOL_MODEL", "llama3.2:3b")

# ★ Path 로 넘깁니다. MCPAdapter 는 문자열을 http(s) 주소로만 받습니다
#   (문자열 하나로 아무 스크립트나 실행되는 것을 막는 보안 설계).
SERVER = Path(__file__).with_name("mcp_server.py")

QUESTION = "'나는 오늘 MCP를 배웠다' 는 몇 단어야? word_count 도구를 써."


async def main(verbose: bool) -> None:
    async with MCPAdapter(SERVER) as adapter:
        # ① MCP 도구 → LangChain 도구
        tools = await adapter.list_tools()
        by_name = {t.name: t for t in tools}
        if verbose:
            print("── ① 서버가 알려준 도구 ──")
            for t in tools:
                print(f"{t.name}: {t.description}  인자={t.args}")
            print()

        # ② 2교시와 같음
        llm = ChatOllama(model=TOOL_MODEL, temperature=0).bind_tools(tools)

        print("질문:", QUESTION)
        messages = [HumanMessage(QUESTION)]
        ai = await llm.ainvoke(messages)
        messages.append(ai)

        # ③ 모델은 요청만 한다
        if verbose:
            print("\n── ③ tool_calls ──")
            print(ai.tool_calls)
        if not ai.tool_calls:
            print("\n⚠️ 모델이 도구를 부르지 않았습니다 — 그대로 답했습니다:")
            print(ai.content)
            return

        # ④ 실행은 MCP 서버에서 — call 전체를 넘기면 ToolMessage 가 돌아온다(2교시 12장)
        for call in ai.tool_calls:
            tool_msg = await by_name[call["name"]].ainvoke(call)
            if verbose:
                print(f"\n── ④ ToolMessage ({call['name']}) ──")
                print(tool_msg.content)
            messages.append(tool_msg)

        # ⑤ 결과를 보고 최종 답변
        final = await llm.ainvoke(messages)
        print("\n답변:", final.content)


if __name__ == "__main__":
    print(f"모델: {TOOL_MODEL}\n")
    asyncio.run(main(verbose="-v" in sys.argv))
