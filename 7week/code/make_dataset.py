"""[1교시 / 실습 1] ★ 평가용 데이터셋을 만든다 — LangSmith Datasets

  6주차: 계기판을 달았다   — 무슨 일이 있었나 (관측)
  7주차: 눈금을 만든다     — 얼마나 좋은가   (측정) ★

      ① 데이터셋  : 고정된 문제집 (입력 + 기대 출력)   ← 오늘 이 파일
      ② 평가자    : 채점 기준                          → evaluators.py
      ③ 실험      : 기법을 바꿔가며 같은 문제집을 푼다  → ab_experiment.py
      ④ 비교      : 어느 쪽이 나은가 — 숫자로           → RESULTS.md

  데이터셋 만드는 방법은 두 가지입니다.
      ① 수동 작성        — 이 파일 (examples.py 배포본 + 학생 추가분)
      ② 추적 로그 수집 ★ — 웹에서 6주차 Run 을 골라 "Add to Dataset"
                            (코드가 아니라 화면에서 합니다. 2-3절)

🔶 버전 주의: create_examples() 의 인자 형태가 langsmith 버전에 따라 다릅니다.
   · 현재 형태 : examples=[{"inputs": ..., "outputs": ...}]
   · 레거시    : inputs=[...], outputs=[...]   ← 강의안에 적힌 형태 (0.3.11 부터 옛 방식)
   이 파일은 **현재 형태를 먼저** 쓰고, 안 되면 레거시로 재시도합니다.
   그래도 막히면 python check_eval_api.py 로 먼저 확인하십시오. ★

실행:
    python make_dataset.py            # 만들기 (이미 있으면 부족한 예제만 채움)
    python make_dataset.py --reset    # ⚠️ 기존 데이터셋을 지우고 새로 만든다
"""

import sys

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위. 아래에 있으면 라이브러리가 이미 값을 읽은 뒤다.

from langsmith import Client  # noqa: E402

import examples as ex  # noqa: E402

DATASET_NAME = "week07-review-sentiment"
DESCRIPTION = "리뷰 감정 분류 — 대표 + 엣지 케이스. 7주차 기법 A/B 실측용"


def get_or_create(client: Client, reset: bool):
    """데이터셋을 가져오거나 만든다. 수업 중 재실행을 견디게 하는 것이 목적. ★"""
    found = list(client.list_datasets(dataset_name=DATASET_NAME))

    if found and reset:
        print(f"⚠️  --reset : 기존 '{DATASET_NAME}' 을 삭제합니다.")
        client.delete_dataset(dataset_id=found[0].id)
        found = []

    if found:
        print(f"[i] 이미 있는 데이터셋을 재사용합니다 — {DATASET_NAME}")
        return found[0], False

    dataset = client.create_dataset(dataset_name=DATASET_NAME, description=DESCRIPTION)
    print(f"[+] 데이터셋 생성 — {DATASET_NAME}")
    return dataset, True


def add_examples(client: Client, dataset_id, pairs) -> int:
    """예제를 추가한다. 🔶 두 가지 인자 형태를 모두 시도한다.

    ★ 확인된 사실 (langsmith 0.4.37 기준)
        · 현재 형태 : examples=[{"inputs": ..., "outputs": ...}]   ← 먼저 시도
        · 레거시    : inputs=[...], outputs=[...]                  ← 강의안에 적힌 형태
      레거시는 0.3.11 부터 '옛 방식'이 되었지만 아직 받아 줍니다.
      **버전이 올라가면 먼저 끊기는 쪽은 레거시**이므로 현재 형태를 기본으로 둡니다.
    """
    if not pairs:
        return 0

    # ── 형태 B : examples=[{...}] dict 리스트 (현재 권장 형태) ★
    try:
        client.create_examples(
            dataset_id=dataset_id,
            examples=[{"inputs": i, "outputs": o} for i, o in pairs],
        )
        return len(pairs)
    except (TypeError, ValueError) as e:
        print(f"[!] 현재 형태 실패 ({e.__class__.__name__}) → 레거시 형태로 재시도 🔶")

    # ── 형태 A : inputs=/outputs= 리스트 (강의안·구버전)
    client.create_examples(
        inputs=[i for i, _ in pairs],
        outputs=[o for _, o in pairs],
        dataset_id=dataset_id,
    )
    return len(pairs)


def main() -> None:
    reset = "--reset" in sys.argv

    print("=" * 72)
    print("  실습 1 — 평가용 데이터셋 구성")
    print("=" * 72)
    print(ex.summary())
    print()

    client = Client()
    dataset, created = get_or_create(client, reset)

    # ── 이미 들어 있는 입력은 건너뛴다 (중복 등록 방지) ★ ──────────
    existing = {
        (e.inputs or {}).get("review") for e in client.list_examples(dataset_id=dataset.id)
    }
    if existing and not created:
        print(f"[i] 기존 예제 {len(existing)}건 — 없는 것만 추가합니다.")

    todo = [(i, o) for i, o, _, _ in ex.EXAMPLES if i["review"] not in existing]
    added = add_examples(client, dataset.id, todo)

    total = len(list(client.list_examples(dataset_id=dataset.id)))
    print()
    print(f"[✓] {added}건 등록  →  '{DATASET_NAME}' 총 {total}건")
    print("=" * 72)
    print(f"""
웹에서 확인합니다

    smith.langchain.com → Datasets & Testing → {DATASET_NAME}
      · 예제를 **화면에서 직접 추가·수정**할 수 있습니다 (비개발자 협업 시 유용)
      · Input / Reference Output 두 칸이 곧 '문제와 정답' 입니다

★★ 방법 ② — 추적 로그에서 수집 (여기서부터는 화면 작업입니다)

    Projects → week06-tracing → Runs 목록
        ① 이상한 답이 나온 Run 을 찾는다
        ② "Add to Dataset" 으로 이 데이터셋에 추가            ★
        ③ 기대 출력(정답)을 손으로 채운다

    수동 작성 : 내가 상상한 케이스        빠르지만 내가 아는 것에 편향된다
    로그 수집 : 실제로 일어난 케이스 ★   내가 예상 못 한 입력이 들어 있다

    📌 실무에서는 ② 가 본체입니다. 실패한 입력을 계속 담아
       다시는 그 실패가 재발하지 않게 합니다 — 이것이 회귀 테스트입니다 (3교시).

📌 학생 활동: examples.py 아래쪽에 **내 엣지 케이스 2~3개**를 추가하고
   이 파일을 다시 실행하십시오. (이미 등록된 것은 건너뜁니다)

다음 단계 →  python evaluators.py
""")


if __name__ == "__main__":
    main()
