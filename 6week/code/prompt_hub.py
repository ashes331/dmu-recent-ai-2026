"""[3교시 / 실습 4] Prompt Hub — 프롬프트를 코드 밖의 '자산' 으로 관리한다.

5주차 1교시에서 "프롬프트는 자산" 이라고 했습니다. 지금은 이렇게 관리합니다.

    prompt = ChatPromptTemplate.from_messages([...])   # ← .py 파일 안에 박혀 있음

Git 으로 버전 관리는 됩니다. 그런데 문제가 남습니다.

    문제                              설명
    ──────────────────────────────────────────────────────────
    프롬프트만 고쳐도 배포해야 함      코드 파일이므로
    개발자가 아니면 못 고침 ★          기획자·도메인 전문가가 손을 못 댐
    여러 프로젝트에서 복사됨           같은 프롬프트가 5군데에 흩어짐
    어떤 버전이 돌고 있는지 불명확     코드를 뒤져야 함

    [코드에 박아둘 때]              [Hub 로 뺄 때]
    프롬프트 수정 → 배포 → 반영      프롬프트 수정 → 저장 → 반영 ★

⚖️ 다만 만능은 아닙니다. 마지막 절에서 대가를 짚습니다.

🔶🔶 이 파일은 이 차시에서 가장 깨지기 쉬운 코드입니다.
     push_prompt / pull_prompt 의 인자 이름과 langchain.hub 쪽 함수(hub.pull)는
     langsmith 버전에 따라 다릅니다.
     ★ 수업 전날 실습실 PC 에서 반드시 1회 실행해 동작하는 형태로 확정하십시오.
       여기서 막히면 이 절이 통째로 멈춥니다.

실행:
    python prompt_hub.py
"""

from dotenv import load_dotenv

load_dotenv()

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from langsmith import Client  # noqa: E402

MODEL = "gemma3:4b"
NAME = "review-analyzer"  # Hub 에 올릴 이름

client = Client()


# ── ① 올릴 프롬프트 (5주차에 만든 것) ──────────────────────────
prompt_v1 = ChatPromptTemplate.from_messages(
    [
        ("system", "너는 고객 리뷰 분석기다."),
        ("human", "다음 리뷰를 분석해라.\n\n{review}"),
    ]
)

# ── ③ 고친 프롬프트 — 같은 이름으로 다시 push 하면 새 버전이 쌓인다 ──
prompt_v2 = ChatPromptTemplate.from_messages(
    [
        # ↓ 이 한 줄이 수정분입니다
        ("system", "너는 고객 리뷰 분석기다. 과장하지 말고 리뷰에 있는 사실만 사용하라."),
        ("human", "다음 리뷰를 분석해라.\n\n{review}"),
    ]
)


def push(obj, label: str) -> str | None:
    """Hub 에 등록한다. 같은 이름이면 새 커밋(버전)이 쌓인다. ★"""
    try:
        url = client.push_prompt(NAME, object=obj)
        print(f"  [O] {label} 등록됨")
        print(f"      {url}")
        return url
    except Exception as e:  # noqa: BLE001
        print(f"  [X] {label} 등록 실패 — {type(e).__name__}: {e}")
        print("      🔶 langsmith 버전에 따라 인자 이름이 다릅니다.")
        print("         client.push_prompt 의 시그니처를 확인하십시오:")
        print("             help(client.push_prompt)")
        return None


def show_commits() -> None:
    """버전 이력을 확인한다 — 웹의 Commits 탭과 같은 내용."""
    try:
        commits = list(client.list_prompt_commits(NAME, limit=5))
    except Exception as e:  # noqa: BLE001
        print(f"  [!] 커밋 목록을 못 읽었습니다 — {type(e).__name__}: {e}")
        print("      웹의 Prompts → 해당 프롬프트 → Commits 탭에서 확인하십시오.")
        return

    print("  버전 이력 (최근 5건) ★")
    for c in commits:
        h = getattr(c, "commit_hash", "?")
        print(f"    · {str(h)[:8]}")


def pull_and_run() -> None:
    """④ 불러오기 — 불러온 것은 '평범한 ChatPromptTemplate 객체' 다. ★"""
    try:
        loaded = client.pull_prompt(NAME)  # 최신 버전
        # loaded = client.pull_prompt(f"{NAME}:<커밋해시>")   # 특정 버전 고정 ★
    except Exception as e:  # noqa: BLE001
        print(f"  [X] 불러오기 실패 — {type(e).__name__}: {e}")
        print("      🔶 소유자 접두사가 필요할 수 있습니다: '<내계정>/review-analyzer'")
        return

    print(f"  [O] 불러온 객체 타입: {type(loaded).__name__}")

    # ★ 관찰 포인트: | 로 이어붙이는 방식이 하나도 안 바뀝니다.
    #   5주차에서 배운 Runnable 규약 덕분입니다.
    chain = loaded | ChatOllama(model=MODEL, temperature=0) | StrOutputParser()
    out = chain.invoke({"review": "배터리가 오래갑니다. 다만 케이스가 큽니다."})
    print("  실행 결과:", out.replace("\n", " ")[:80], "...")


def main() -> None:
    print("=" * 66)
    print("  실습 4 — Prompt Hub")
    print("=" * 66)

    print("\n[② 등록]")
    push(prompt_v1, "v1")

    print("\n[③ 고쳐서 다시 등록 → 새 버전이 생긴다]")
    push(prompt_v2, "v2")

    print()
    show_commits()

    print("\n[④ 불러와서 그대로 체인에 끼운다]")
    pull_and_run()

    print()
    print("=" * 66)
    print("""
웹에서 확인 — Prompts 메뉴

  화면에서 볼 것        의미
  ──────────────────────────────────────────
  프롬프트 본문         등록된 실물
  Commits (버전 이력) ★  고칠 때마다 쌓인다
  공개/비공개 설정      기본은 비공개
  Playground            웹에서 바로 시험 실행 ★

버전을 고정하는 법

  방식                      언제 쓰나
  ──────────────────────────────────────────────────────
  최신 버전 ("이름")        개발 중 — 항상 최신을 따라감
  버전 고정 ("이름:커밋") ★  운영 중 — 남이 고쳐도 내 서비스는 안 흔들림

  ⚠️ 운영 서비스는 반드시 버전을 고정해야 합니다.
     최신을 따라가게 두면 누군가 프롬프트를 고친 순간 내 서비스 동작이 바뀝니다.
     배포한 적도 없는데요. — requirements.txt 의 버전 고정과 같은 이유입니다.

⚖️ 대가도 있습니다

  얻는 것                     잃는 것
  ────────────────────────────────────────────────────────────
  코드 배포 없이 수정         외부 서비스 의존 — 장애 시 못 가져옴 ⚠️
  비개발자도 수정 가능        아무나 고치면 아무도 모르게 동작이 바뀜
  버전 이력·롤백              코드 저장소와 이력이 두 군데로 갈림
  웹에서 바로 시험            오프라인 실행 불가 ★

  ★ 4주차에서 "로컬 모델의 장점 = 오프라인 가능" 이라고 적었습니다.
    그런데 프롬프트를 Hub 에서 가져오면 인터넷이 없으면 안 돕니다.
    로컬 모델을 쓰는 의미가 반쯤 사라집니다.
    실무 절충안: 시작할 때 한 번 pull 해서 로컬에 캐시해 두고 씁니다.

📌 본 교과목 방침: 미니 프로젝트에 Prompt Hub 는 필수가 아닙니다.
   "이런 방식이 있고, 무엇을 주고받는지" 를 아는 것까지가 오늘의 목표입니다.
""")
    print("=" * 66)


if __name__ == "__main__":
    main()
