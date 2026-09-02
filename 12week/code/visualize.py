"""[3교시 / 실습 4] 그래프 시각화 + 실행 경로 확인

  ★ 되돌아가는 화살표가 그림에 보입니다. 이 그림을 **LCEL 로는 그릴 수 없었습니다.**
    1교시의 *"체인은 파이프, 그래프는 회로도"* 를 여기서 회수하십시오.

        +-----------+
        | __start__ |
        +-----------+
              *
              v
        +----------+
        | generate |◄────┐
        +----------+     │
              *          │ revise ★
              v          │
        +----------+     │
        | evaluate |─────┘
        +----------+
              *
              v
         +---------+
         | __end__ |
         +---------+

  ⚠️ 강의안 정정 ★
     강의안은 draw_ascii() 를 "의존성이 가장 가볍다" 고 소개하지만,
     실제로는 **grandalf 패키지가 필요합니다** (없으면 ImportError).
     추가 설치 없이 되는 것은 **draw_mermaid()** 쪽입니다. 🔶
     이 파일은 ASCII 를 먼저 시도하고, 안 되면 Mermaid 로 넘어갑니다.

  ★ 과제 5 의 "시각화 이미지" 는 **ASCII 캡처나 Mermaid 텍스트도 인정**합니다.

실행:
    python visualize.py                 # reflection 그래프 (순환이 보입니다) ★
    python visualize.py branch          # branch_graph 그래프 (분기가 보입니다)
    python visualize.py reflection --png  # 🔶 PNG 저장 시도
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent

GRAPHS = {
    "reflection": ("reflection", "순환 — 되돌아가는 화살표를 확인하십시오 ★"),
    "branch": ("branch_graph", "분기 — 세 갈래로 나뉘는 것을 확인하십시오"),
    "first": ("first_graph", "직렬 — 분기도 순환도 없습니다 (체인이 더 낫습니다 ⚖️)"),
}


def load_graph(key: str):
    import importlib

    module_name, _ = GRAPHS[key]
    return importlib.import_module(module_name).graph


def draw_ascii(graph) -> bool:
    """ASCII — 🔶 grandalf 가 필요합니다."""
    try:
        print(graph.get_graph().draw_ascii())
        return True
    except ImportError:
        print("""🔶 draw_ascii() 에는 grandalf 가 필요합니다.
     pip install grandalf
   (설치가 안 되면 아래 Mermaid 로 충분합니다 — 과제 5에서도 인정됩니다) ★
""")
        return False


def draw_mermaid(graph) -> str:
    """Mermaid 텍스트 — 추가 설치 없이 됩니다. 문서·README 에 붙이기 좋습니다 ★"""
    text = graph.get_graph().draw_mermaid()
    print(text)
    return text


def draw_png(graph, out: Path) -> None:
    """🔶 PNG 렌더링에는 외부 의존성이 필요할 수 있습니다."""
    try:
        out.write_bytes(graph.get_graph().draw_mermaid_png())
        print(f"✅ 저장: {out}")
    except Exception as e:
        print(f"""🔶 PNG 렌더링 실패 ({type(e).__name__}: {str(e)[:60]})
   외부 렌더링 서비스·의존성이 필요합니다. **ASCII / Mermaid 로 충분합니다.** ★
   과제 5 의 '시각화 이미지' 는 ASCII 캡처나 Mermaid 텍스트도 인정합니다.
""")


def main() -> None:
    key = next((a for a in sys.argv[1:] if a in GRAPHS), "reflection")
    _, note = GRAPHS[key]

    print(f"── {key} 그래프 — {note}\n")
    graph = load_graph(key)

    print("── ① ASCII ─────────────────────────────────────")
    draw_ascii(graph)

    print("\n── ② Mermaid (README 에 그대로 붙이십시오) ★ ────")
    text = draw_mermaid(graph)

    mmd = HERE / f"{key}.mmd"
    mmd.write_text(text, encoding="utf-8")
    print(f"\n✅ 저장: {mmd}   ← 과제 5 제출물로 인정됩니다 ★")

    if "--png" in sys.argv:
        print("\n── ③ PNG 🔶 ────────────────────────────────")
        draw_png(graph, HERE / f"{key}.png")

    print("""
── LangSmith 에서 실행 경로 보기 ★ ────────────────────────

   Trace
    ├ Run: generate    (1회차)
    ├ Run: evaluate    (1회차)
    ├ Run: generate    (2회차)   ★ 같은 노드가 다시 나온다 = 순환의 증거
    ├ Run: evaluate    (2회차)
    └ Run: generate    (3회차)

  | 확인할 것              | 왜                                |
  | **같은 노드가 여러 번** | **순환이 실제로 돌았다는 증거** ★    |
  | 회차별 critique 내용    | 무엇을 지적했고 반영됐는지          |
  | **총 지연·토큰**        | 반복의 **비용**을 숫자로 (6주차)    |
  | 어느 분기를 탔는가      | 조건부 엣지의 판단 결과            |

📌 6주차에 배운 화면이 그래프에서도 그대로 쓰입니다.
   그때 "9주차 이후 실행 경로가 복잡해지므로 관측 도구를 먼저 익힌다" 고 한 이유가 이것입니다. ★
""")


if __name__ == "__main__":
    main()
