"""[참고 · OpenAI 전용] prompt_hub.py 의 OpenAI 판 — 프롬프트를 코드 밖의 '자산' 으로 관리한다

원본: 6주차 code/prompt_hub.py (실습 4)

    원본과 다른 점  ★
        체인 실행 모델   ChatOllama(gemma3:4b)  →  ChatOpenAI(gpt-4o-mini)
        Hub 이름         review-analyzer         →  review-analyzer-openai  (6주차 기록과 섞이지 않게)
        ⑤ 버전 고정      주석으로만 소개         →  v1 커밋 해시로 실제로 불러와 최신(v2)과 비교 ★
    push · 커밋 목록 · pull 은 원본과 같습니다.

  Prompt Hub 는 어디에 쌓이나 ★
    smith.langchain.com → 좌측 Prompts   (추적 기록의 Projects 와 다른 메뉴)
    LANGSMITH_API_KEY 의 워크스페이스에 쌓입니다 — LANGSMITH_PROJECT 와는 관계없습니다.
    같은 이름으로 다시 push 하면 '새 커밋(버전)' 이 쌓입니다. 기본은 비공개입니다.

  [코드에 박아둘 때]              [Hub 로 뺄 때]
  프롬프트 수정 → 배포 → 반영      프롬프트 수정 → 저장 → 반영 ★

⚠️ push_prompt / pull_prompt 의 인자 이름은 langsmith 버전에 따라 다릅니다.
   에러가 나면 메시지를 그대로 캡처해 질문하세요. (자료 제작 PC: langsmith 0.13.0 에서 확인)

준비:
    저장소 맨 위 .env 에  OPENAI_API_KEY · LANGSMITH_API_KEY
    (LANGSMITH_TRACING=true 면 ④·⑤ 의 체인 실행도 Projects 에 trace 로 남습니다 — 태그 week09-openai)

실행:
    python prompt_hub_openai.py
    ⚠️ 실행할 때마다 v1 · v2 커밋이 2개씩 더 쌓입니다. 1~2회면 충분합니다.
"""

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 파일 맨 위

import os  # noqa: E402

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.tracers.langchain import wait_for_all_tracers  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402  ← 원본은 langchain_ollama ★
from langsmith import Client  # noqa: E402

MODEL = "gpt-4o-mini"
MAX_OUT = 300  # 호출 1번의 답 길이 상한 (토큰) — 비용 상한 ⚠️
NAME = "review-analyzer-openai"  # Hub 에 올릴 이름 — 6주차 review-analyzer 와 따로 쌓인다
REVIEW = "배터리가 오래갑니다. 다만 케이스가 큽니다. 인생 최고의 제품!"  # 과장 문구를 일부러 넣었다
TAGS = ["week09-openai", "prompt-hub", MODEL]

# ⚠️ 설정 오류는 호출 전에 잡는다
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("OPENAI_API_KEY 가 .env 에 없습니다. 저장소 맨 위 .env 를 확인하세요.")
if not os.environ.get("LANGSMITH_API_KEY"):
    raise SystemExit("LANGSMITH_API_KEY 가 .env 에 없습니다. Prompt Hub 도 LangSmith 키로 접속합니다.")

client = Client()
llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=MAX_OUT, timeout=60)  # ★ 바뀐 한 줄


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
        print("      ⚠️ 'Nothing to commit' 이면 직전 버전과 내용이 같다는 뜻입니다.")
        print("         그 밖의 에러는 langsmith 버전 차이일 수 있습니다:  help(client.push_prompt)")
        return None


def show_commits() -> list[str]:
    """버전 이력을 확인한다 — 웹의 Commits 탭과 같은 내용. 최신이 맨 위."""
    try:
        commits = list(client.list_prompt_commits(NAME, limit=5))
    except Exception as e:  # noqa: BLE001
        print(f"  [!] 커밋 목록을 못 읽었습니다 — {type(e).__name__}: {e}")
        print("      웹의 Prompts → 해당 프롬프트 → Commits 탭에서 확인하세요.")
        return []

    hashes = [str(getattr(c, "commit_hash", "?")) for c in commits]
    print("  버전 이력 (최근 5건, 위가 최신) ★")
    for h in hashes:
        print(f"    · {h[:8]}")
    return hashes


def run(prompt, label: str) -> None:
    """불러온 프롬프트를 체인에 끼워 실행한다."""
    # ★ 관찰 포인트: | 로 이어붙이는 방식이 하나도 안 바뀝니다 — 모델이 OpenAI 로 바뀌어도.
    chain = prompt | llm | StrOutputParser()
    out = chain.invoke(
        {"review": REVIEW},
        config={"run_name": f"prompt_hub_openai_{label}", "tags": TAGS, "metadata": {"prompt": NAME, "version": label}},
    )
    print(f"  [{label}] {out.replace(chr(10), ' ')[:110]} ...")


def pull_and_run(hashes: list[str]) -> None:
    """④ 최신 버전 불러오기  ⑤ 버전 고정으로 불러오기 — 불러온 것은 '평범한 ChatPromptTemplate' 다. ★"""
    try:
        latest = client.pull_prompt(NAME)  # 최신 버전 (= v2)
    except Exception as e:  # noqa: BLE001
        print(f"  [X] 불러오기 실패 — {type(e).__name__}: {e}")
        return
    print(f"  [O] 불러온 객체 타입: {type(latest).__name__}")
    run(latest, "최신")

    if len(hashes) < 2:
        print("  [!] 커밋이 2개 미만이라 버전 고정 비교를 건너뜁니다.")
        return
    v1_hash = hashes[1]  # 바로 앞 커밋 = 이번 실행의 v1
    print(f"\n[⑤ 버전 고정 — '{NAME}:{v1_hash[:8]}' 로 v1 을 불러온다 ★]")
    pinned = client.pull_prompt(f"{NAME}:{v1_hash}")
    print("  system 문장:", pinned.messages[0].prompt.template)
    run(pinned, "v1 고정")


def main() -> None:
    print("=" * 66)
    print(f"  Prompt Hub — OpenAI 판   모델={MODEL}   Hub 이름={NAME}")
    print("=" * 66)

    print("\n[② 등록]")
    push(prompt_v1, "v1")

    print("\n[③ 고쳐서 다시 등록 → 새 버전이 생긴다]")
    push(prompt_v2, "v2")

    print()
    hashes = show_commits()

    print("\n[④ 최신 버전을 불러와서 그대로 체인에 끼운다]")
    pull_and_run(hashes)
    wait_for_all_tracers()  # 추적이 켜져 있으면 기록 전송을 마친다

    print()
    print("=" * 66)
    print(f"""
웹에서 확인 — 좌측 Prompts 메뉴 → {NAME}

  화면에서 볼 것        의미
  ──────────────────────────────────────────
  프롬프트 본문         등록된 실물
  Commits (버전 이력) ★  고칠 때마다 쌓인다 — 위 해시와 같다
  공개/비공개 설정      기본은 비공개
  Playground            웹에서 바로 시험 실행 ★

  (추적이 켜져 있으면) Projects → 내 프로젝트 → Tags = week09-openai
      → prompt_hub_openai_최신 · prompt_hub_openai_v1 고정 두 줄

⑤ 에서 볼 것 ★
  [최신]   은 "과장하지 말고" 가 들어간 v2
  [v1 고정] 은 그 한 줄이 없는 v1 — 누가 Hub 에서 v2 로 고쳐도 이 줄은 안 바뀐다 ★
  답의 차이는 크지 않을 수 있습니다 (자료 제작 PC: 둘 다 "인생 최고" 를 리뷰어의 표현으로 인용, v1 이 더 길게 항목화).
  볼 것은 답의 품질이 아니라 "system 문장이 고정된 버전에서 온다" 는 사실입니다.

  💡 커밋 해시는 '내용' 으로 정해집니다 — 6주차 review-analyzer 와 같은 v1 · v2 를 올리면
     이름이 달라도 해시가 같습니다 (1ced05a8 · 387f0f8c). 내용이 같으면 같은 버전입니다.

  ⚠️ 운영 서비스는 반드시 버전을 고정해야 합니다.
     최신을 따라가게 두면 누군가 프롬프트를 고친 순간 내 서비스 동작이 바뀝니다.
     배포한 적도 없는데요. — requirements.txt 의 버전 고정과 같은 이유입니다.

⚖️ 대가 (원본과 같다)
  외부 서비스 의존 · 오프라인 실행 불가 · 아무도 모르게 동작이 바뀜 · 이력이 두 군데로 갈림
  📌 미니 프로젝트에 Prompt Hub 는 필수가 아닙니다.
""")
    print("=" * 66)


if __name__ == "__main__":
    main()
