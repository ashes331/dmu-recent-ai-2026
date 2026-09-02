"""[2교시 / 실습 2] thread_id 로 대화를 이어간다 — 1주차 ✗ ② 를 지우는 자리

  지금은 매번 처음부터입니다.

     graph.invoke({"messages": [HumanMessage("357 곱하기 4891은?")]})
     # → "1746087입니다"
     graph.invoke({"messages": [HumanMessage("거기에 2를 더하면?")]})
     # → "무엇에 2를 더하나요?"   ⚠️ 앞 대화를 모른다

  ⚠️ 1교시의 add_messages 는 **"한 번의 invoke 안에서"** 메시지를 쌓습니다.
     invoke 가 끝나면 **상태가 사라집니다.**

  해결은 두 가지가 **함께** 있어야 합니다 ★

     | 체크포인터  | 상태를 **저장하는 장치** (어디에 저장할지) |
     | thread_id  | **어느 대화인지** 식별 — 카카오톡의 채팅방 하나 ★ |

  ★ 이 실습의 핵심은 3번 호출입니다.
    "메모리가 있다" 가 아니라 **"thread 단위로 있다"** 는 것.
    실제 서비스에서 **사용자마다 다른 thread_id** 를 주는 이유입니다.
    안 그러면 **남의 대화가 섞입니다** ⚠️ (개인정보 사고)

  | 구분 | 무엇                     | 저장소                  | 본 실습 |
  | 단기 | **한 대화(thread) 안**    | MemorySaver(프로세스)   | ✅ 오늘 |
  | 장기 | **대화를 넘어서** 남는 정보 | SQLite·DB 등 영속 저장소 | 개념만 |

  ⚠️ MemorySaver 는 **프로세스가 끝나면 사라집니다.** 실습에는 충분하지만
     미니 프로젝트에서 "재시작해도 기억" 이 필요하면 영속 저장소가 필요합니다. 🔶

실행:
    python memory_agent.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from react_agent import builder  # ★ 1교시 그래프를 그대로 재사용

RECURSION_LIMIT = int(os.getenv("WEEK13_RECURSION_LIMIT", "10"))

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)  # ★ 이 한 줄


def ask(text: str, thread: str) -> None:
    out = graph.invoke(
        {"messages": [HumanMessage(text)]},
        config={"configurable": {"thread_id": thread},  # ★ 대화 식별자
                "recursion_limit": RECURSION_LIMIT},
    )
    print(f"[{thread}] Q: {text}")
    print(f"[{thread}] A: {out['messages'][-1].content.strip()[:100]}\n")


def main() -> None:
    print("체크포인터: MemorySaver (프로세스 메모리 — 재시작하면 사라집니다 ⚠️)\n")

    # ── 대화 A ─────────────────────────────────────────────
    ask("357 곱하기 4891은?", "chat-A")
    ask("거기에 2를 더하면?", "chat-A")  # ★ 이어진다

    # ── 대화 B — 다른 thread ★ ──────────────────────────────
    ask("거기에 2를 더하면?", "chat-B")  # ⚠️ "무엇에?" — 기억이 없다

    # ── 저장된 상태 들여다보기 ──────────────────────────────
    print("── 저장된 상태 ──────────────────────────────────")
    for thread in ("chat-A", "chat-B"):
        state = graph.get_state({"configurable": {"thread_id": thread}})
        print(f"  [{thread}] 메시지 수: {len(state.values['messages'])}  "
              f"다음 노드: {state.next}")  # ★ 4절 HITL 에서 다시 봅니다

    print("""
결과 확인표 — 학생이 채웁니다 ★

  | 호출                      | thread     | 앞 대화를 아는가 |
  | 1. "357 곱하기 4891은?"    | chat-A     | —              |
  | 2. "거기에 2를 더하면?"     | chat-A     | ✅ 안다         |
  | 3. "거기에 2를 더하면?"     | **chat-B** | ❌ **모른다** ★ |

★ **3번이 이 실습의 핵심입니다.**
  "메모리가 있다" 가 아니라 **"thread 단위로 있다"** 는 것.
  실제 서비스에서 사용자마다 다른 thread_id 를 주는 이유입니다.
  ⚠️ 안 그러면 **남의 대화가 섞입니다** (개인정보 사고)

💡 대화가 길어지면?
   매 호출에 전체 이력이 프롬프트로 들어가 **토큰이 계속 늘어납니다.**
   실무에서는 **오래된 메시지를 요약하거나 잘라냅니다.**
   (11주차 Lost in the Middle 과 같은 이유 — **길다고 좋은 게 아닙니다** ★)

🔶 영속 저장소를 쓰면 프로그램을 재시작해도 대화가 남습니다.
   # from langgraph.checkpoint.sqlite import SqliteSaver
   미니 프로젝트에서 "재시작해도 기억" 이 필요하면 이쪽을 검토하십시오.
""")


if __name__ == "__main__":
    main()
