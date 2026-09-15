#!/usr/bin/env bash
# ============================================================================
#  최신인공지능 2026 — 실습실 PC 초기 셋팅 (PC 초기화 후 복구용) · Git Bash 판
#  setup_env.bat 과 같은 일을 Git Bash 에서 합니다.
#
#  하는 일
#    1) 환경변수 dl026_HOME_DIR 위치로 이동
#    2) 만들 폴더 이름을 입력받아 생성
#       + .gitignore 생성 (venv/ · .env 가 git 에 올라가지 않게 · 이미 있으면 그대로)
#    3) python -m venv venv 생성 → 활성화
#    4) 2~3주차에 pip install 했던 패키지 설치
#    5) 나머지(VS Code·Git·.env·Ollama)는 Git Bash 명령어만 화면에 안내
#
#  실행 : Git Bash 에서  bash setup_env.sh
#         (Git 설치 때 기본 설정이면 탐색기에서 더블클릭해도 Git Bash 창으로 실행됩니다)
#  ※ 이 파일은 UTF-8 + LF 로 저장해야 합니다. (CRLF 로 저장하면 $'\r': command not found)
# ============================================================================

# ── 설치할 패키지 (2~3주차) ────────────────────────────────────────────────
#  2주차 실습 1 (로컬 Ollama)  : ollama, numpy
#  3주차 1~3교시 (첫 체인)      : langchain, langchain-core, langchain-ollama, python-dotenv
#  ※ 버전은 교수 PC에서 3주차 실습을 검증한 버전으로 고정 (2026/requirements.txt 와 동일)
#  ※ sentence-transformers·matplotlib 은 2주차 Colab 전용이라 설치하지 않음 (PyTorch 대용량)
PACKAGES=(langchain==1.4.0 langchain-core==1.6.2 langchain-ollama==1.1.0 python-dotenv==1.2.3 ollama==0.6.2 numpy)
DEFAULT_NAME="langchain-2026"

# Git Bash 창에서는 파이썬 출력 인코딩이 cp949 로 잡혀 한글이 깨질 수 있음
export PYTHONIOENCODING=utf-8

finish() {  # 더블클릭 실행이면 창이 바로 닫히므로 결과를 읽을 시간을 준다
    echo
    read -r -p "Enter 를 누르면 끝납니다... " _ || true
    exit "$1"
}

fail() {  # fail "메시지" ["다음 줄" ...]
    printf '  [X] %s\n' "$1"
    shift
    for line in "$@"; do printf '      %s\n' "$line"; done
    finish 1
}

ask() {  # ask 변수이름 "질문" — 입력이 끊기면(EOF) 같은 질문을 무한 반복하지 않고 중단
    local _ans
    if ! IFS= read -r -p "$2" _ans; then
        echo
        fail "입력이 끊겨 중단합니다."
    fi
    _ans="${_ans%$'\r'}"
    printf -v "$1" '%s' "$_ans"
}

pip_fail() {
    echo
    echo "  [X] 패키지 설치에 실패했습니다."
    echo '      - 네트워크 오류라면: 스크립트를 다시 실행하고 venv 는 "그대로 사용"(Enter)을 고르세요.'
    echo '      - "너무 깁니다" / "No such file or directory" 라면: 경로가 너무 긴 것입니다. 짧은 위치에 새로 만드세요.'
    echo "      또는 활성화된 터미널에서 직접:"
    echo "      pip install ${PACKAGES[*]}"
    finish 1
}

echo "============================================================"
echo " 최신인공지능 — 실습실 PC 초기 셋팅 (Git Bash)"
echo "============================================================"
echo

# ── [0] 사전 점검 ───────────────────────────────────────────────────────────
echo "[0] 사전 점검"
if python -c "import sys" >/dev/null 2>&1; then
    PY=(python)
elif py -3 -c "import sys" >/dev/null 2>&1; then
    PY=(py -3)
else
    fail "Python 을 찾을 수 없습니다." \
         "- 터미널에서 python -V 를 쳐 보세요." \
         "- Microsoft Store 가 열리면: 설정 → 앱 → 앱 실행 별칭 → python 끄기" \
         "- Python 이 설치되어 있지 않다면 조교/교수에게 알려 주세요."
fi
if ! "${PY[@]}" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "  [X] Python 3.10 이상이 필요합니다."
    "${PY[@]}" -V
    finish 1
fi
echo "  [OK] $("${PY[@]}" -V 2>&1)  (${PY[*]})"

if command -v git >/dev/null 2>&1; then echo "  [OK] git"
else echo "  [X]  git 없음 — 안내 [4] Git 단계에서 막힙니다"; fi
if command -v ollama >/dev/null 2>&1; then echo "  [OK] ollama"
else echo "  [X]  ollama 없음 — 로컬 모델 실습 불가"; fi
if ollama list 2>/dev/null | grep -qi "gemma3:4b"; then echo "  [OK] gemma3:4b"
else echo "  [--] gemma3:4b 확인 안 됨 (Ollama 서버가 꺼져 있거나 모델 없음)"; fi
if command -v code >/dev/null 2>&1; then echo "  [OK] VS Code"
else echo "  [--] code 명령 없음 — VS Code 를 직접 열어 폴더를 여세요"; fi
echo "  ※ [X] 가 있으면 조교/교수에게 알려 주세요."
echo

# ── [1/4] dl026_HOME_DIR 로 이동 ───────────────────────────────────────────
echo "[1/4] 작업 위치 확인"
HOME_DIR="${dl026_HOME_DIR:-}"
if [ -z "$HOME_DIR" ]; then
    echo "  [!] 환경변수 dl026_HOME_DIR 이 설정되어 있지 않습니다."
    echo "      실습실 PC라면 조교/교수에게 알려 주세요."
    ask HOME_DIR "  상위 폴더 경로 (Enter = 지금 폴더 $(pwd)): "
    [ -z "$HOME_DIR" ] && HOME_DIR="$(pwd)"
fi
HOME_DIR="${HOME_DIR//\"/}"            # 탐색기 «경로로 복사» 에 붙는 따옴표 제거
# D:\dl026 → /d/dl026 — cygpath -u 는 TEMP 아래를 /tmp, Git 설치 폴더를 / 로 바꿔 보여 줘서 드라이브 문자로 직접 만든다
HOME_DIR="$(cygpath -m "$HOME_DIR")"
if [[ "$HOME_DIR" == [A-Za-z]:* ]]; then
    DRIVE="${HOME_DIR:0:1}"
    HOME_DIR="/${DRIVE,,}${HOME_DIR:2}"
fi
[ "$HOME_DIR" != "/" ] && HOME_DIR="${HOME_DIR%/}"
cd "$HOME_DIR" 2>/dev/null || fail "폴더로 이동할 수 없습니다: $HOME_DIR"
echo "  위치: $(cygpath -w "$PWD")"
echo

# ── [2/4] 폴더 이름 입력 → 생성 ────────────────────────────────────────────
while :; do
    echo "[2/4] 프로젝트 폴더"
    ask PROJ "  만들 폴더 이름 (Enter = $DEFAULT_NAME): "
    [ -z "$PROJ" ] && PROJ="$DEFAULT_NAME"
    # 한글·공백은 이후 명령을 번거롭게 하므로 영문만 허용 (bash [A-Za-z] 는 로캘에 따라 달라져 파이썬으로 검사)
    if ! PROJ="$PROJ" "${PY[@]}" -c "import os, re, sys; sys.exit(0 if re.fullmatch(r'[A-Za-z0-9._-]+', os.environ['PROJ']) else 1)"; then
        echo "  [X] 폴더 이름은 영문·숫자·-·_·. 만 쓸 수 있습니다. (공백·한글 불가)"
        echo
        continue
    fi
    PROJ_DIR="$HOME_DIR/$PROJ"
    PROJ_WIN="$(cygpath -w "$PROJ_DIR")"
    echo "  만들 위치: $PROJ_WIN"
    # 경로가 길면 langsmith 설치 중 Windows 260자 제한에 걸림 (venv 안 경로만 약 110자)
    # MSYS_NO_PATHCONV: Git Bash 가 /v 를 경로(C:/Program Files/Git/v)로 바꾸지 않게
    if ! MSYS_NO_PATHCONV=1 reg query 'HKLM\SYSTEM\CurrentControlSet\Control\FileSystem' /v LongPathsEnabled 2>/dev/null | grep -q "0x1"; then
        if ! PROJ_WIN="$PROJ_WIN" "${PY[@]}" -c "import os, sys; sys.exit(1 if len(os.environ['PROJ_WIN']) > 120 else 0)"; then
            echo '  [!] 경로가 너무 깁니다 (120자 초과). 패키지 설치가 "No such file or directory" 로 실패할 수 있습니다.'
            echo '      dl026_HOME_DIR 을 짧은 경로(예: D:\dl026)로 쓰거나, 폴더 이름을 짧게 하세요.'
        fi
    fi
    ask ANS "  이 위치로 진행할까요? (Enter = 진행 / n = 이름 다시 입력): "
    if [[ "$ANS" == [nN] ]]; then echo; continue; fi
    break
done

if [ -d "$PROJ_DIR" ]; then
    echo "  [i] 이미 있는 폴더입니다 — 그대로 사용합니다."
else
    mkdir -p "$PROJ_DIR" || fail "폴더를 만들 수 없습니다: $PROJ_WIN"
fi
cd "$PROJ_DIR" || fail "폴더로 이동할 수 없습니다: $PROJ_WIN"

# .gitignore — venv/ · .env 가 git 에 올라가지 않게 (3주차 과제 1 견본 code/.gitignore 와 같은 내용)
#  이미 있으면(되살린 저장소 등) 건드리지 않는다. 안내 [4-A] 는 pull 전에 이 파일을 지우게 한다 —
#  추적되지 않은 .gitignore 가 있으면 내용이 같아도 git pull 이 멈추기 때문
if [ -e .gitignore ]; then
    echo "  [i] .gitignore 가 이미 있습니다 — 그대로 둡니다."
elif cat > .gitignore <<'EOF'
# 가상환경
venv/
__pycache__/
*.pyc

# 환경변수 — 절대 커밋 금지 ★
.env

# 에디터
.vscode/
.idea/
EOF
then
    echo "  [OK] .gitignore 생성 — venv/ · .env 가 git 에 올라가지 않게"
else
    echo "  [!] .gitignore 를 만들지 못했습니다 — 안내 [4-B] 전에 직접 만드세요."
fi
echo

# ── [3/4] venv 생성 → 활성화 ───────────────────────────────────────────────
echo "[3/4] 가상환경"
create_venv() {
    echo "  python -m venv venv  (10~30초)"
    "${PY[@]}" -m venv venv || fail "가상환경을 만들지 못했습니다." \
        "venv 폴더를 쓰는 프로그램(VS Code 터미널 등)을 모두 닫고 다시 실행하세요."
}
if [ -f venv/Scripts/python.exe ]; then
    echo "  [!] 이미 venv 가 있습니다: $PROJ_WIN\\venv"
    ask ANS "  지우고 새로 만들까요? (y = 새로 만들기 / Enter = 그대로 사용): "
    if [[ "$ANS" == [yY] ]]; then
        echo "  기존 venv 삭제 중..."
        rm -rf venv
        [ -d venv ] && fail "가상환경을 지우지 못했습니다." \
            "venv 폴더를 쓰는 프로그램(VS Code 터미널 등)을 모두 닫고 다시 실행하세요."
        create_venv
    fi
else
    create_venv
fi

# Windows 에서 만든 venv 에도 bash 용 activate 가 있다 (Scripts/activate)
# shellcheck disable=SC1091
source venv/Scripts/activate
# 활성화 확인 — sys.prefix 가 base 와 다르면 venv 안
if ! python -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null; then
    # 옛 Python 의 activate 는 Git Bash 경로 변환이 없어 PATH 가 안 바뀔 수 있음 → 직접 앞에 붙인다
    export VIRTUAL_ENV="$PROJ_DIR/venv"
    export PATH="$VIRTUAL_ENV/Scripts:$PATH"
    hash -r
    python -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null \
        || fail "가상환경 활성화에 실패했습니다." \
                '스크립트를 다시 실행해 "지우고 새로 만들까요?" 에서 y 를 선택하세요.'
fi
echo "  [OK] 활성화됨: $(python -c "import sys; print(sys.executable)")"
echo

# ── [4/4] 2~3주차 패키지 설치 ──────────────────────────────────────────────
echo "[4/4] 패키지 설치 (2~3주차)"
echo "  pip install ${PACKAGES[*]}"
echo
python -m pip install "${PACKAGES[@]}" || pip_fail
echo
echo "  설치 확인:"
python -c "from importlib.metadata import version as v; [print(f'    {p:18s} {v(p)}') for p in ['langchain', 'langchain-core', 'langchain-ollama', 'python-dotenv', 'ollama', 'numpy']]" || pip_fail

# ── 이후 안내 (명령어만 출력) ────────────────────────────────────────────────
echo
echo "============================================================"
echo " 설치 완료 — 아래 명령은 직접 실행하세요"
echo "============================================================"
echo " ※ 스크립트 안에서 켠 가상환경은 스크립트가 끝나면 꺼집니다."
echo "   VS Code 터미널을 Git Bash 로 열고(터미널 창 오른쪽 + 옆 ∨ → Git Bash)"
echo "   아래 순서대로 다시 켜 주세요."
echo
echo "[1] VS Code 로 프로젝트 폴더 열기"
echo "    code \"$PROJ_DIR\""
echo
echo "[2] 가상환경 활성화 — 프롬프트 위 줄에 (venv) 가 붙어야 정상"
echo "    cd \"$PROJ_DIR\""
cat <<'EOF'
    source venv/Scripts/activate
    which python              ← .../venv/Scripts/python 인지 확인

    ※ which python 이 venv 가 아니면 (옛 Python)
    export PATH="$PWD/venv/Scripts:$PATH"

    ※ PowerShell 이라면 — Git Bash 로 만든 이 venv 도 그대로 켜집니다
    venv\Scripts\Activate.ps1

[3] VS Code 인터프리터 지정
    Ctrl+Shift+P → Python: Select Interpreter → ./venv/Scripts/python.exe

    (공용 PC 대비) 설정을 폴더 안에 심기 — 한 줄씩 실행
    mkdir -p .vscode
    echo '{ "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe" }' > .vscode/settings.json

[4] Git — 공용 PC 이므로 신원은 --local 로
    git config --global init.defaultBranch main
    git init
    git config --local user.name  "본인이름"
    git config --local user.email "본인메일@example.com"

  [4-A] GitHub 에 3주차 저장소가 이미 있는 경우 ★ 대부분 여기
    git remote add origin https://github.com/<본인계정>/langchain-2026.git
    rm .gitignore             ← 스크립트가 만든 것 — 지우지 않으면 pull 이 멈춥니다
    git pull origin main
    git branch -u origin/main
    git status                ← venv/ 가 목록에 보이면 안 됩니다

  [4-B] 저장소가 없는 경우 (처음부터)
    cat .gitignore            ← 스크립트가 만들어 둔 것 — venv/ · .env 가 있는지 확인
    pip freeze > requirements.txt
    git add .
    git status                ← venv/ 와 .env 가 없어야 합니다
    git commit -m "chore: 프로젝트 초기 세팅"
    git remote add origin https://github.com/<본인계정>/langchain-2026.git
    git push -u origin main

[5] .env 준비 — 키는 4주차 수업 중 배포
    cp .env.example .env
    git status                ← .env 가 목록에 보이면 안 됩니다 ★

[6] 4주차 패키지 — 수업 안내에 따라
    pip install langchain-openai

[7] Ollama 모델 확인 — pull 은 수업 중 금지 ★
    ollama list               ← gemma3:4b 가 보여야 합니다
EOF
finish 0
