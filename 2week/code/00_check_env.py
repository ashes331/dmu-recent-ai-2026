# 파일: 00_check_env.py
# 2주차 ― 수업 전 실습실 PC 점검
#
# 실행:  python 00_check_env.py
#
# 확인 항목
#   · 파이썬 / 가상환경
#   · ollama 패키지, Ollama 서버 기동 여부
#   · 실습 1용 대화 모델 (gemma3:4b)
#   · 실습 2·3·4 대비책용 임베딩 모델 (nomic-embed-text)
#   · sentence-transformers / numpy / matplotlib
#
# 빠진 것이 있으면 조치 명령까지 함께 알려준다.

import importlib.util
import os
import sys
import unicodedata

CHAT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

LINE = "-" * 62
todo = []          # 조치가 필요한 항목을 모은다


def dwidth(s):
    """터미널에서 실제로 차지하는 폭. 한글은 두 칸으로 센다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def row(label, ok, detail, fix=None):
    """한 줄 출력하고, 조치가 필요하면(fix 가 있으면) 목록에 쌓아 둔다.

    [OK] 정상   [!!] 조치 필요   [--] 없어도 되는 항목
    """
    mark = "OK" if ok else ("!!" if fix else "--")
    pad = " " * max(1, 32 - dwidth(label))
    print(f"  [{mark}] {label}{pad}{detail}")
    if not ok and fix:
        todo.append((label, fix))


def has_module(name):
    return importlib.util.find_spec(name) is not None


def check_python():
    print(LINE)
    print("  1. 파이썬")
    print(LINE)
    v = sys.version_info
    row("버전", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}",
        "Python 3.10 이상을 쓰십시오")
    in_venv = sys.prefix != sys.base_prefix
    row("가상환경", True, "예" if in_venv else "아니오 (전역 환경)")
    row("실행 파일", True, sys.executable)
    print()


def check_ollama():
    print(LINE)
    print("  2. Ollama  (실습 1 ― 2교시)")
    print(LINE)

    if not has_module("ollama"):
        row("ollama 패키지", False, "없음", "pip install ollama")
        print()
        return

    row("ollama 패키지", True, "설치됨")

    import ollama
    try:
        names = [m.get("model") or m.get("name") for m in ollama.list()["models"]]
    except Exception as e:
        row("서버 연결", False, f"실패 ({type(e).__name__})", "ollama serve")
        print()
        return

    row("서버 연결", True, f"정상 ― 모델 {len(names)}개")

    chat_ok = any(n and n.startswith(CHAT_MODEL.split(":")[0]) for n in names)
    row(f"대화 모델 {CHAT_MODEL}", CHAT_MODEL in names,
        "있음" if CHAT_MODEL in names else ("유사 모델만 있음" if chat_ok else "없음"),
        f"ollama pull {CHAT_MODEL}")

    row(f"임베딩 모델 {EMBED_MODEL}", any(n and n.startswith(EMBED_MODEL) for n in names),
        "있음" if any(n and n.startswith(EMBED_MODEL) for n in names) else "없음",
        f"ollama pull {EMBED_MODEL}   # Colab 이 막힐 때의 대비책")
    print()


def check_embedding_packages():
    print(LINE)
    print("  3. 임베딩 실습 패키지  (실습 2·3·4 ― 3교시)")
    print(LINE)

    row("numpy", has_module("numpy"), "설치됨" if has_module("numpy") else "없음",
        "pip install numpy")

    st = has_module("sentence_transformers")
    row("sentence-transformers", st, "설치됨" if st else "없음 (Colab 사용 시 정상)",
        None)   # 실습실 PC에는 일부러 안 깐다. 조치 목록에 넣지 않는다.

    mpl = has_module("matplotlib")
    row("matplotlib", mpl, "설치됨" if mpl else "없음 → 실습 4는 표 출력으로 대체",
        None)
    print()
    if not st:
        print("  ※ sentence-transformers 미설치는 문제가 아니다.")
        print("    2주차 방침상 실습 2·3·4 는 Colab 에서 진행한다.")
        print("    Colab 이 막히면 embed_local_ollama.py 로 대체한다.")
        print()


def main():
    print()
    print("=" * 62)
    print("  2주차 실습 환경 점검  (00_check_env.py)")
    print("=" * 62)
    print()

    check_python()
    check_ollama()
    check_embedding_packages()

    print("=" * 62)
    if todo:
        print("  조치가 필요한 항목")
        print("=" * 62)
        for label, fix in todo:
            print(f"  · {label}")
            print(f"      {fix}")
    else:
        print("  모두 정상입니다. 실습을 진행할 수 있습니다.")
    print("=" * 62)
    print()
    print("  ★ 코드로는 확인할 수 없는 것 ― 반드시 사람이 직접 확인할 것")
    print("     실습실 PC 에서 Colab 에 접속해 셀 1개를 실행해 볼 것")
    print("     (도메인 접속이 아니라 로그인 / 런타임 연결 / pip 설치가 되는지)")
    print()


if __name__ == "__main__":
    main()
