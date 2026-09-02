"""🔶 [교수용 · 수업 전날 필수] evaluate() / create_examples() 시그니처 사전 확인

  ⚠️ 이 차시 최대의 위험 지점입니다.

     langsmith 는 버전 변화가 빠르고, 아래 두 가지가 버전마다 다릅니다.

       ① create_examples() 의 인자 형태
            inputs=/outputs= 리스트   vs   examples=[{...}] dict 리스트
       ② 평가자 함수의 시그니처
            (outputs, reference_outputs)   vs   (run, example)

     여기서 막히면 2교시 25분 실습이 통째로 멈춥니다.
     **수업 전날 실습실 PC 에서 반드시 1회 실행**해 동작하는 형태를 확정하십시오. ★

  이 스크립트가 하는 일
     · 설치된 버전 출력
     · evaluate 의 import 경로 확인
     · create_examples 가 받는 인자 확인
     · **LLM 없이** 더미 target 으로 evaluate() 를 1회 실제 실행 (traces 2건 소모)
     · 끝나면 임시 데이터셋을 지운다

실행:
    python check_eval_api.py            # 확인 후 임시 데이터셋 삭제
    python check_eval_api.py --keep     # 임시 데이터셋을 남겨 웹에서 확인
"""

import inspect
import sys

from dotenv import load_dotenv

load_dotenv()  # ★ 반드시 맨 위

TEMP_DATASET = "week07-apicheck-tmp"


def section(title: str) -> None:
    print("\n" + "─" * 70)
    print(f"  {title}")
    print("─" * 70)


def show_versions() -> None:
    section("① 설치된 버전")
    try:
        from importlib.metadata import version
    except ImportError:
        print("  (importlib.metadata 없음)")
        return
    for pkg in ("langsmith", "langchain", "langchain-core", "langchain-ollama", "langchain-openai"):
        try:
            print(f"  {pkg:<20} {version(pkg)}")
        except Exception:  # noqa: BLE001
            print(f"  {pkg:<20} (미설치)")


def check_env() -> bool:
    section("② 환경변수")
    import os

    ok = True
    pairs = [
        ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"),
        ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"),
        ("LANGSMITH_PROJECT", "LANGCHAIN_PROJECT"),
    ]
    for new, old in pairs:
        value = os.getenv(new) or os.getenv(old)
        name = new if os.getenv(new) else (old if os.getenv(old) else new)
        if not value:
            print(f"  [X] {new} (또는 {old}) 가 비어 있습니다")
            if "API_KEY" in new:
                ok = False
            continue
        shown = value if "KEY" not in new else value[:8] + "..." + f"({len(value)}자)"
        print(f"  [O] {name} = {shown}")
        if "KEY" in new and value != value.strip():
            print("      ⚠️ 키 앞뒤에 공백이 있습니다. .env 에서 따옴표 없이 붙여넣으십시오.")
            ok = False
    return ok


def check_import():
    section("③ evaluate 의 import 경로")
    try:
        from langsmith import evaluate

        print("  [O] from langsmith import evaluate          ← 신형")
        return evaluate
    except ImportError:
        pass
    try:
        from langsmith.evaluation import evaluate

        print("  [O] from langsmith.evaluation import evaluate  ← 구형 🔶")
        print("      → 배포 코드의 import 를 이쪽으로 확정하십시오.")
        return evaluate
    except ImportError as e:
        print(f"  [X] evaluate 를 찾을 수 없습니다: {e}")
        return None


def check_create_examples(client) -> None:
    section("④ create_examples() 가 받는 인자")
    try:
        params = list(inspect.signature(client.create_examples).parameters)
        print(f"  {params}")
        if "examples" in params:
            print("  [O] 현재 형태 (examples=[{...}] dict 리스트) 사용 가능 ★")
        if "inputs" in params and "outputs" in params:
            print("  [O] 레거시 형태 (inputs=/outputs=) 가 명시적 인자로 남아 있습니다 — 구버전")
        elif "kwargs" in params:
            print("  [i] 레거시 형태는 **kwargs 로만 받습니다 (0.3.11 이후) 🔶")
            print("      → 강의안의 inputs=/outputs= 코드는 '옛 방식' 입니다. 아직 동작합니다.")
        if "examples" not in params and "inputs" not in params:
            print("  [!] 둘 다 아닙니다 🔶 make_dataset.py 를 손봐야 합니다.")
    except (TypeError, ValueError) as e:
        print(f"  [i] 시그니처를 읽지 못했습니다 ({e}) — 실제 실행으로 확인하십시오.")


def check_evaluate(evaluate, client, keep: bool) -> None:
    section("⑤ evaluate() 실제 실행 — LLM 없이 더미 target 으로")

    # ── 임시 데이터셋 (예제 2건) ─────────────────────────────
    for existing in client.list_datasets(dataset_name=TEMP_DATASET):
        client.delete_dataset(dataset_id=existing.id)

    dataset = client.create_dataset(dataset_name=TEMP_DATASET, description="API 확인용 임시")
    pairs = [({"review": "좋아요"}, {"label": "긍정"}), ({"review": "별로"}, {"label": "부정"})]
    try:
        client.create_examples(
            dataset_id=dataset.id,
            examples=[{"inputs": i, "outputs": o} for i, o in pairs],
        )
        print("  [O] create_examples 현재 형태(examples=)로 등록 성공 ★")
    except (TypeError, ValueError):
        client.create_examples(
            inputs=[i for i, _ in pairs], outputs=[o for _, o in pairs], dataset_id=dataset.id
        )
        print("  [O] create_examples 레거시 형태(inputs=/outputs=)로 등록 성공 🔶")

    def target(inputs: dict) -> dict:
        """LLM 을 부르지 않는다. 첫 글자로 대충 답한다 — API 형태만 확인하면 된다."""
        return {"label": "긍정" if "좋" in inputs["review"] else "부정"}

    # ── 신형 평가자 ─────────────────────────────────────────
    def new_style(outputs: dict, reference_outputs: dict) -> bool:
        return outputs["label"] == reference_outputs["label"]

    # ── 구형 평가자 ─────────────────────────────────────────
    def old_style(run, example):
        got = (run.outputs or {}).get("label")
        want = (example.outputs or {}).get("label")
        return {"key": "exact_match", "score": got == want}

    style = None
    try:
        results = evaluate(
            target,
            data=TEMP_DATASET,
            evaluators=[new_style],
            experiment_prefix="apicheck-new",
            max_concurrency=1,
        )
        list(results)  # 실제로 끝까지 돌려 본다
        style = "신형 (outputs, reference_outputs)"
        print("  [O] 신형 평가자 시그니처 동작 ★  — 배포 코드 그대로 쓰면 됩니다")
    except Exception as e:  # noqa: BLE001
        print(f"  [X] 신형 실패: {e.__class__.__name__}: {e}")
        try:
            results = evaluate(
                target,
                data=TEMP_DATASET,
                evaluators=[old_style],
                experiment_prefix="apicheck-old",
                max_concurrency=1,
            )
            list(results)
            style = "구형 (run, example)"
            print("  [O] 구형 평가자 시그니처 동작 🔶")
            print("      → evaluators.py 의 as_legacy() 로 감싸서 넘기면 됩니다.")
        except Exception as e2:  # noqa: BLE001
            print(f"  [X] 구형도 실패: {e2.__class__.__name__}: {e2}")

    # ── 정리 ────────────────────────────────────────────────
    if keep:
        print(f"\n  [i] --keep : 임시 데이터셋 '{TEMP_DATASET}' 을 남겨 둡니다.")
    else:
        for existing in client.list_datasets(dataset_name=TEMP_DATASET):
            client.delete_dataset(dataset_id=existing.id)
        print(f"\n  [i] 임시 데이터셋 '{TEMP_DATASET}' 삭제 완료")

    section("결론")
    if style:
        print(f"  ✅ 이 PC 에서 동작하는 평가자 시그니처 : {style}")
        print("     이 형태로 배포 코드를 확정하십시오. ★")
    else:
        print("  ⚠️ 어느 쪽도 동작하지 않습니다. langsmith 버전을 고정하고 다시 확인하십시오.")
        print("     예)  pip install \"langsmith==<동작하는 버전>\"")


def main() -> None:
    keep = "--keep" in sys.argv

    print("=" * 70)
    print("  🔶 교수용 사전 점검 — evaluate() / create_examples() 시그니처")
    print("=" * 70)

    show_versions()
    if not check_env():
        print("\n⚠️ 환경변수부터 고치십시오. .env 를 확인하고 **터미널을 새로 열어** 재실행합니다.")
        return

    evaluate = check_import()
    if evaluate is None:
        return

    from langsmith import Client

    client = Client()
    check_create_examples(client)
    check_evaluate(evaluate, client, keep)

    print("\n" + "=" * 70)
    print("""
확인이 끝났으면

    python examples.py          # 데이터셋 배포본 점검 (LLM 없음)
    python evaluators.py        # 규칙 기반 평가자 시연 (LLM 없음)
    python make_dataset.py      # 실습 1
    python ab_experiment.py     # 실습 2 ★★  ← 결과가 실제로 갈리는지 확인할 것

⚠️ 두 기법의 결과가 갈리지 않으면 실습의 의미가 사라집니다.
   전날 1회 돌려 보고, 둘 다 100% 가 나오면 examples.py 에 엣지 케이스를 더 넣으십시오. ★
""")


if __name__ == "__main__":
    main()
