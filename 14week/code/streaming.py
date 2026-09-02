"""[2교시 / 실습 2] 에이전트의 진행 상황을 사용자에게 흘려보낸다

  에이전트는 오래 걸립니다.

     [4주차 단일 호출]   질문 ─── 5초 ───▶ 답변
     [14주차 에이전트]   질문 ─── 40초 ────────────────────▶ 답변  ⚠️
                              그동안 화면은 아무것도 없다 → 사용자는 **껐다고 판단**합니다

  두 종류의 스트리밍 ★★

     | 종류        | 무엇이 흐르나      | 사용자가 보는 것                    |
     | 토큰 단위    | 글자              | "휴학은 통산 6개..." (글자가 흘러나옴) — 4주차 |
     | **상태 단위** ★| **노드 실행 결과** | "검색 중... 계산 중... 정리 중..." ★★ |

     ★★ **상태 단위가 에이전트의 핵심입니다.**
        토큰 단위만으로는 **도구를 실행하는 동안 여전히 침묵**합니다(생성이 아니므로).
        **"지금 무엇을 하고 있는가"** 를 보여주는 것이 상태 단위입니다.

     | stream_mode | 나오는 것                    | 쓰임              |
     | "values"    | **전체 상태** 스냅샷          | 디버깅 (13주차)    |
     | "updates" ★ | **어느 노드가 무엇을 바꿨는지** | **진행 표시** ★★  |
     | "messages"  | LLM **토큰**                 | 답변 글자 흘리기    |

     🔶 모드 이름과 지원 여부는 버전에 따라 다릅니다. **사전 확인** 후 배포하십시오.

  📌 결론: **총 시간은 못 줄입니다. 사용자가 기다릴 수 있게 만드는 것**이 목표입니다.
     4주차 결론 그대로 — *"스트리밍은 성능 최적화가 아니라 사용자 경험 개선"*.

실행:
    python streaming.py            # 상태 단위 + 토큰 단위
    python streaming.py --updates  # 상태 단위만 (진행 표시) ★★
    python streaming.py --tokens   # 토큰 단위만 (writer 노드로 한정)
"""

import sys
import time

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

from supervisor import CONFIG, INPUTS, QUESTION, graph  # ★ 1교시 그래프를 그대로 재사용

# ★ 노드 이름을 **사용자 말로 번역**합니다 — UX 의 실체
#   "researcher" 가 아니라 "문서를 찾는 중"
LABELS = {
    "supervisor": "담당자 배정 중",
    "researcher": "문서를 찾는 중",
    "calculator": "계산하는 중",
    "writer": "답변을 정리하는 중",
}


def stream_updates() -> float:
    """① 상태 단위 — 진행 표시 ★★"""
    print("── 상태 단위 (stream_mode='updates') ★★ ─────────")
    t0 = time.perf_counter()
    for chunk in graph.stream(INPUTS, CONFIG, stream_mode="updates"):
        for node in chunk:
            label = LABELS.get(node, node)
            print(f"  ▸ [{time.perf_counter() - t0:5.1f}s] {label}...")
    total = time.perf_counter() - t0
    print(f"  ▸ [{total:5.1f}s] 완료")
    return total


def stream_tokens() -> None:
    """② 토큰 단위 — 답변 글자 흘리기

    ★ writer 노드의 토큰만 흘립니다.
      중간 노드의 출력까지 흘리면 화면이 지저분해집니다.
    """
    print("\n── 토큰 단위 (stream_mode='messages') ────────────")
    print("--- 최종 답변 ---")
    try:
        for msg, meta in graph.stream(INPUTS, CONFIG, stream_mode="messages"):
            if meta.get("langgraph_node") == "writer":  # ★ 작성 노드의 토큰만
                print(msg.content, end="", flush=True)
        print()
    except Exception as e:  # 🔶 모드 지원 여부가 버전마다 다릅니다
        print(f"\n🔶 messages 모드에서 오류 ({type(e).__name__}: {str(e)[:60]})")
        print("   버전에 따라 지원이 다릅니다. 상태 단위만으로도 이 절은 성립합니다. ★")


def main() -> None:
    print(f"Q: {QUESTION}\n")

    if "--tokens" in sys.argv:
        stream_tokens()
        return

    total = stream_updates()

    if "--updates" not in sys.argv:
        stream_tokens()

    print(f"""
관찰 포인트 ★

  첫 진행 표시가 **1~2초 만에** 뜸        "40초 침묵이 사라졌습니다" ★
  총 소요 시간은 **그대로** ({total:.1f}s)   4주차 결론 그대로 — **체감만 개선** ★
  노드 이름을 **사용자 말로 번역**         "researcher" 가 아니라 "문서를 찾는 중"
                                          — **UX 의 실체** ★
  토큰 스트리밍을 **writer 로 한정**       중간 노드까지 흘리면 화면이 지저분해짐

📌 **총 시간은 못 줄입니다. 사용자가 기다릴 수 있게 만드는 것**이 목표입니다.

💡 비동기(astream) 는 **여러 사용자 요청을 동시에** 처리할 때 필요합니다.
   ⚠️ 본 교과목에서는 직접 구현하지 않습니다 — `langgraph dev` 가 내부에서 처리합니다.

       async for chunk in graph.astream(inputs, stream_mode="updates"):
           print(chunk)
""")


if __name__ == "__main__":
    main()
