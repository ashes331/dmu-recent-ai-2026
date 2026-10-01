#!/usr/bin/env bash
# ============================================================================
#  최신인공지능 2026 — 실습실 PC 초기 셋팅 (PC 초기화 후 복구용) · Git Bash 판
#  setup_env.bat 과 같은 일을 Git Bash 에서 합니다.
#
#  하는 일
#    1) 프로젝트를 만들 «상위 폴더» 를 입력받아 이동 (미리 정해 두지 않고 매번 묻습니다)
#    2) 만들 폴더 이름을 입력받아 생성
#       + .gitignore 생성 (venv/ · .env 가 git 에 올라가지 않게 · 이미 있으면 그대로)
#    3) python -m venv venv 생성 → 활성화
#    4) 2~4주차 패키지 설치 (4주차 langchain-openai 포함)
#    5) Git 설정 — git init · 이름 · 메일 · 저장소 주소를 입력받아 --local 로 지정
#    6) 나머지(VS Code·pull/push·.env·Ollama)는 Git Bash 명령어만 화면에 안내
#
#  실행 : VS Code 터미널을 Git Bash 로 열고  bash setup_env.sh
#         (터미널 창 오른쪽 + 옆 ∨ → Git Bash)
#         (Git 설치 때 기본 설정이면 탐색기에서 더블클릭해도 Git Bash 창으로 실행됩니다)
#  ※ 이 파일은 UTF-8 + LF 로 저장해야 합니다. (CRLF 로 저장하면 $'\r': command not found)
# ============================================================================

# ── 설치할 패키지 (2~4주차) ────────────────────────────────────────────────
#  2주차 실습 1 (로컬 Ollama)  : ollama, numpy
#  3주차 1~3교시 (첫 체인)      : langchain, langchain-core, langchain-ollama, python-dotenv
#  4주차 2교시 (모델 교체)      : langchain-openai  ★ 이 셋팅 시점에 이미 쓰므로 함께 설치
#  ※ 버전은 교수 PC에서 3주차 실습을 검증한 버전으로 고정 (2026/requirements.txt 와 동일)
#  🔶 langchain-openai==1.6.2 는 위 고정 버전들과 함께 풀리는 것을 확인한 값(2026-09-21, pip dry-run).
#     수업 전날 교수 PC에서 4주차 2교시 실습으로 한 번 검증할 것
#  ※ sentence-transformers·matplotlib 은 2주차 Colab 전용이라 설치하지 않음 (PyTorch 대용량)
#  ※ langchain-anthropic 은 설치하지 않음 (4주차 code/requirements.txt 참조)
PACKAGES=(langchain==1.4.0 langchain-core==1.6.2 langchain-ollama==1.1.0 python-dotenv==1.2.3 ollama==0.6.2 numpy langchain-openai==1.6.2)
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

# ── [1/5] 작업 위치 입력 ───────────────────────────────────────────────────
echo "[1/5] 작업 위치"
echo "  프로젝트 폴더를 만들 «상위 폴더» 를 입력하세요."
echo "  탐색기 주소창의 경로를 복사해 붙여 넣어도 됩니다 (예: D:\\dl026)."
while :; do
    ask HOME_DIR "  상위 폴더 경로 (Enter = 지금 폴더 $(cygpath -w "$PWD")): "
    HOME_DIR="${HOME_DIR//\"/}"        # 탐색기 «경로로 복사» 에 붙는 따옴표 제거
    [ -z "$HOME_DIR" ] && HOME_DIR="$PWD"
    # D:\dl026 → /d/dl026 — cygpath -u 는 TEMP 아래를 /tmp, Git 설치 폴더를 / 로 바꿔 보여 줘서 드라이브 문자로 직접 만든다
    HOME_DIR="$(cygpath -m "$HOME_DIR")"
    if [[ "$HOME_DIR" == [A-Za-z]:* ]]; then
        DRIVE="${HOME_DIR:0:1}"
        HOME_DIR="/${DRIVE,,}${HOME_DIR:2}"
    fi
    [ "$HOME_DIR" != "/" ] && HOME_DIR="${HOME_DIR%/}"
    [ -d "$HOME_DIR" ] && break
    # 없는 폴더면 만들지 물어본다 — 오타 하나로 스크립트가 죽지 않게
    echo "  [!] 없는 폴더입니다: $(cygpath -w "$HOME_DIR")"
    ask ANS "  이 폴더를 만들까요? (Enter = 만들기 / n = 경로 다시 입력): "
    if [[ "$ANS" == [nN] ]]; then echo; continue; fi
    if mkdir -p "$HOME_DIR" 2>/dev/null; then
        echo "  [OK] 폴더를 만들었습니다."
        break
    fi
    echo "  [X] 폴더를 만들지 못했습니다 — 다른 경로를 입력하세요."
    echo
done
cd "$HOME_DIR" 2>/dev/null || fail "폴더로 이동할 수 없습니다: $HOME_DIR"
echo "  위치: $(cygpath -w "$PWD")"
echo

# ── [2/5] 폴더 이름 입력 → 생성 ────────────────────────────────────────────
while :; do
    echo "[2/5] 프로젝트 폴더"
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
            echo '      상위 폴더를 짧은 경로(예: D:\dl026)로 입력하거나, 폴더 이름을 짧게 하세요.'
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
#  이미 있으면(되살린 저장소 등) 건드리지 않는다. 안내 [4-A] 는 pull 전에 이 파일을 .bak 으로 옮기게 한다 —
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

# ── [3/5] venv 생성 → 활성화 ───────────────────────────────────────────────
echo "[3/5] 가상환경"
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

# ── [4/5] 2~4주차 패키지 설치 ──────────────────────────────────────────────
echo "[4/5] 패키지 설치 (2~4주차)"
echo "  pip install ${PACKAGES[*]}"
echo
python -m pip install "${PACKAGES[@]}" || pip_fail
echo
echo "  설치 확인:"
python -c "from importlib.metadata import version as v; [print(f'    {p:18s} {v(p)}') for p in ['langchain', 'langchain-core', 'langchain-ollama', 'langchain-openai', 'python-dotenv', 'ollama', 'numpy']]" || pip_fail

# ── [5/5] Git 설정 ─────────────────────────────────────────────────────────
#  공용 PC 이므로 신원은 --local (이 폴더 안에서만). --global 은 다음 사람에게 남는다.
#  pull/push 는 계정 인증이 필요해 자동으로 하지 않고 아래 안내로 넘긴다.
echo
echo "[5/5] Git 설정"
if ! command -v git >/dev/null 2>&1; then
    echo "  [X] git 이 없어 건너뜁니다 — 조교/교수에게 알려 주세요."
else
    if [ -d .git ]; then
        echo "  [i] 이미 git 저장소입니다 — git init 은 건너뜁니다."
    elif git init -b main -q 2>/dev/null || git init -q; then
        echo "  [OK] git init"
    else
        echo "  [!] git init 에 실패했습니다 — 아래 안내 [4] 를 직접 실행하세요."
    fi

    if [ -d .git ]; then
        # 이미 넣어 둔 값이 있으면 Enter 로 그대로 쓴다
        GIT_NAME="$(git config --local --get user.name 2>/dev/null || true)"
        GIT_MAIL="$(git config --local --get user.email 2>/dev/null || true)"
        GIT_URL="$(git config --local --get remote.origin.url 2>/dev/null || true)"

        while :; do
            ask ANS "  이름 (git user.name${GIT_NAME:+ · Enter = $GIT_NAME}): "
            [ -z "$ANS" ] && ANS="$GIT_NAME"
            if [ -n "$ANS" ]; then GIT_NAME="$ANS"; break; fi
            echo "  [!] 이름을 입력하세요."
        done
        while :; do
            ask ANS "  메일 (git user.email${GIT_MAIL:+ · Enter = $GIT_MAIL}): "
            [ -z "$ANS" ] && ANS="$GIT_MAIL"
            case "$ANS" in
                ?*@?*.?*) GIT_MAIL="$ANS"; break ;;
                "")       echo "  [!] 메일을 입력하세요." ;;
                *)        echo "  [!] 메일 모양이 아닙니다 (예: hong@example.com)" ;;
            esac
        done
        git config --local user.name  "$GIT_NAME"
        git config --local user.email "$GIT_MAIL"

        echo "  GitHub 저장소 주소 — 3주차에 만든 저장소가 있으면 그 주소를 붙여 넣으세요."
        echo "    예: https://github.com/<본인계정>/langchain-2026.git"
        ask ANS "  저장소 주소 (Enter = 나중에${GIT_URL:+ · Enter = $GIT_URL}): "
        [ -z "$ANS" ] && ANS="$GIT_URL"
        ANS="${ANS//\"/}"                 # 붙여 넣을 때 따옴표가 같이 와도 지운다
        if [ -n "$ANS" ]; then
            if [ -n "$GIT_URL" ]; then git remote set-url origin "$ANS"; else git remote add origin "$ANS"; fi
            GIT_URL="$(git config --local --get remote.origin.url 2>/dev/null || true)"
        fi

        echo "  [확인] user.name  = $(git config --local --get user.name)"
        echo "         user.email = $(git config --local --get user.email)"
        echo "         origin     = ${GIT_URL:-(아직 없음 — 안내 [4] 참조)}"
    fi
fi

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
echo "    ※ 이미 VS Code 를 열어 두고 그 터미널에서 실행했다면 → 건너뛰세요 (스킵)"
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

[4] Git — init · user.name · user.email · origin 은 [5/5] 에서 끝났습니다
    git config --local --list   ← 방금 넣은 값을 확인만 하세요
    ※ 저장소 주소를 나중에 넣으려면
    git remote add origin https://github.com/<본인계정>/langchain-2026.git

  [4-A] GitHub 에 3주차 저장소가 이미 있는 경우 ★ 대부분 여기
    mv .gitignore .gitignore.bak   ← 지우지 말고 옮겨 둡니다 (그냥 두면 pull 이 멈춥니다)
    git pull origin main
      성공하면 →  rm .gitignore.bak
      실패하면 →  mv .gitignore.bak .gitignore   ★ 반드시 되돌리고 나서 다시 시도
                  (되돌리지 않으면 .env 와 venv/ 를 막아 줄 파일이 없습니다)
    git branch -u origin/main
    git status                ← venv/ 와 .env 가 보이면 안 됩니다
                              ★ 보이면 commit 하지 말고 손 드세요

  [4-B] 저장소가 없는 경우 (처음부터)
    cat .gitignore            ← 스크립트가 만들어 둔 것 — venv/ · .env 가 있는지 확인
    pip freeze > requirements.txt
    git add .
    git status                ← venv/ 와 .env 가 없어야 합니다
                              ★ 보이면 commit 하지 말고 손 드세요
    git commit -m "chore: 프로젝트 초기 세팅"
    git push -u origin main   ← origin 은 [5/5] 에서 넣었습니다

[5] .env 준비 — 키는 4주차 수업 중 배포
    cp .env.example .env
    git status                ← .env 가 목록에 보이면 안 됩니다 ★

[6] Ollama 모델 확인 — pull 은 수업 중 금지 ★
    ollama list               ← gemma3:4b 가 보여야 합니다
EOF
finish 0
