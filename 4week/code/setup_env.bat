@echo off
setlocal
rem --- ASCII only above this line: non-ASCII bytes before chcp can break cmd parsing ---
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do set "_OLDCP=%%a"
if defined _OLDCP set "_OLDCP=%_OLDCP: =%"
"%SystemRoot%\System32\chcp.com" 65001 >nul

rem ============================================================================
rem  최신인공지능 2026 — 실습실 PC 초기 셋팅 (PC 초기화 후 복구용)
rem
rem  하는 일
rem    1) 프로젝트를 만들 «상위 폴더» 를 입력받아 이동 (미리 정해 두지 않고 매번 묻습니다)
rem    2) 만들 폴더 이름을 입력받아 생성
rem       + .gitignore 생성 (venv/ · .env 가 git 에 올라가지 않게 · 이미 있으면 그대로)
rem    3) python -m venv venv 생성 → 활성화
rem    4) 2~4주차 패키지 설치 (4주차 langchain-openai 포함)
rem    5) Git 설정 — git init · 이름 · 메일 · 저장소 주소를 입력받아 --local 로 지정
rem    6) 나머지(VS Code·pull/push·.env·Ollama)는 명령어만 화면에 안내
rem
rem  실행 : 탐색기에서 더블클릭  또는  터미널에서  .\setup_env.bat
rem  ※ .bat 이라 PowerShell 실행 정책(Set-ExecutionPolicy)과 무관하게 실행됩니다.
rem  ※ 이 파일은 UTF-8 + CRLF 로 저장해야 합니다. (LF 로 저장하면 goto 가 깨짐)
rem ============================================================================

rem ── 설치할 패키지 (2~4주차) ────────────────────────────────────────────────
rem  2주차 실습 1 (로컬 Ollama)  : ollama, numpy
rem  3주차 1~3교시 (첫 체인)      : langchain, langchain-core, langchain-ollama, python-dotenv
rem  4주차 2교시 (모델 교체)      : langchain-openai  ★ 이 셋팅 시점에 이미 쓰므로 함께 설치
rem  ※ 버전은 교수 PC에서 3주차 실습을 검증한 버전으로 고정 (2026/requirements.txt 와 동일)
rem  🔶 langchain-openai==1.6.2 는 위 고정 버전들과 함께 풀리는 것을 확인한 값(2026-09-21, 실제 설치 확인).
rem     수업 전날 교수 PC에서 4주차 2교시 실습으로 한 번 검증할 것
rem  ※ sentence-transformers·matplotlib 은 2주차 Colab 전용이라 설치하지 않음 (PyTorch 대용량)
rem  ※ langchain-anthropic 은 설치하지 않음 (4주차 code/requirements.txt 참조)
set "PACKAGES=langchain==1.4.0 langchain-core==1.6.2 langchain-ollama==1.1.0 python-dotenv==1.2.3 ollama==0.6.2 numpy langchain-openai==1.6.2"
set "DEFAULT_NAME=langchain-2026"
set "RC=1"

echo ============================================================
echo  최신인공지능 — 실습실 PC 초기 셋팅
echo ============================================================
echo(

rem ── [0] 사전 점검 ───────────────────────────────────────────────────────────
echo [0] 사전 점검
set "PY="
python -c "import sys" >nul 2>&1 && set "PY=python"
if not defined PY py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
if not defined PY goto :no_python
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto :old_python
for /f "delims=" %%v in ('%PY% -V 2^>^&1') do set "PYV=%%v"
echo   [OK] %PYV%  (%PY%)

set "S=[X]  git 없음 — 안내 [4] Git 단계에서 막힙니다"
where git >nul 2>&1 && set "S=[OK] git"
echo   %S%
set "S=[X]  ollama 없음 — 로컬 모델 실습 불가"
where ollama >nul 2>&1 && set "S=[OK] ollama"
echo   %S%
set "S=[--] gemma3:4b 확인 안 됨 (Ollama 서버가 꺼져 있거나 모델 없음)"
ollama list 2>nul | findstr /i /c:"gemma3:4b" >nul && set "S=[OK] gemma3:4b"
echo   %S%
set "S=[--] code 명령 없음 — VS Code 를 직접 열어 폴더를 여세요"
where code >nul 2>&1 && set "S=[OK] VS Code"
echo   %S%
echo   ※ [X] 가 있으면 조교/교수에게 알려 주세요.
echo(

rem ── [1/5] 작업 위치 입력 ───────────────────────────────────────────────────
echo [1/5] 작업 위치
echo   프로젝트 폴더를 만들 «상위 폴더» 를 입력하세요.
echo   탐색기 주소창의 경로를 복사해 붙여 넣어도 됩니다 (예: D:\dl026).

:ask_home
set "HOME_DIR="
set /p "HOME_DIR=  상위 폴더 경로 (Enter = 지금 폴더 %CD%): "
if not defined HOME_DIR set "HOME_DIR=%CD%"
set "HOME_DIR=%HOME_DIR:"=%"
if "%HOME_DIR:~-1%"=="\" set "HOME_DIR=%HOME_DIR:~0,-1%"
if exist "%HOME_DIR%\" goto :home_ok
rem 없는 폴더면 만들지 물어본다 — 오타 하나로 스크립트가 죽지 않게
echo   [!] 없는 폴더입니다: %HOME_DIR%
set "ANS="
set /p "ANS=  이 폴더를 만들까요? (Enter = 만들기 / n = 경로 다시 입력): "
if /i "%ANS%"=="n" goto :ask_home
mkdir "%HOME_DIR%" 2>nul
if exist "%HOME_DIR%\" goto :home_made
echo   [X] 폴더를 만들지 못했습니다 — 다른 경로를 입력하세요.
goto :ask_home
:home_made
echo   [OK] 폴더를 만들었습니다.
:home_ok
cd /d "%HOME_DIR%" || goto :bad_home
echo   위치: %CD%
echo(

rem ── [2/5] 폴더 이름 입력 → 생성 ────────────────────────────────────────────
:ask_name
echo [2/5] 프로젝트 폴더
set "PROJ="
set /p "PROJ=  만들 폴더 이름 (Enter = %DEFAULT_NAME%): "
if not defined PROJ set "PROJ=%DEFAULT_NAME%"
rem 한글 입력은 cmd(UTF-8)에서 깨지고 공백은 이후 명령을 번거롭게 하므로 영문만 허용
%PY% -c "import os, re, sys; sys.exit(0 if re.fullmatch(r'[A-Za-z0-9._-]+', os.environ['PROJ']) else 1)"
if errorlevel 1 goto :bad_name
set "PROJ_DIR=%HOME_DIR%\%PROJ%"
echo   만들 위치: %PROJ_DIR%
rem 경로가 길면 langsmith 설치 중 Windows 260자 제한에 걸림 (venv 안 경로만 약 110자)
set "LONGPATH=0"
reg query "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2>nul | findstr /c:"0x1" >nul && set "LONGPATH=1"
if "%LONGPATH%"=="1" goto :path_ok
%PY% -c "import os, sys; sys.exit(1 if len(os.environ['PROJ_DIR']) > 120 else 0)"
if not errorlevel 1 goto :path_ok
echo   [!] 경로가 너무 깁니다 (120자 초과). 패키지 설치가 "No such file or directory" 로 실패할 수 있습니다.
echo       상위 폴더를 짧은 경로(예: D:\dl026)로 입력하거나, 폴더 이름을 짧게 하세요.
:path_ok
set "ANS="
set /p "ANS=  이 위치로 진행할까요? (Enter = 진행 / n = 이름 다시 입력): "
if /i "%ANS%"=="n" goto :ask_name

if exist "%PROJ_DIR%\" echo   [i] 이미 있는 폴더입니다 — 그대로 사용합니다.
if not exist "%PROJ_DIR%\" mkdir "%PROJ_DIR%"
cd /d "%PROJ_DIR%" || goto :bad_home

rem .gitignore — venv/ · .env 가 git 에 올라가지 않게 (3주차 과제 1 견본 code/.gitignore 와 같은 내용)
rem  이미 있으면(되살린 저장소 등) 건드리지 않는다. 안내 [4-A] 는 pull 전에 이 파일을 .bak 으로 옮기게 한다 —
rem  추적되지 않은 .gitignore 가 있으면 내용이 같아도 git pull 이 멈추기 때문
rem  ※ 괄호 블록 ( … ) 로 한 번에 쓰면 한글 때문에 뒤의 goto 가 레이블을 못 찾는다 — 한 줄씩 >> 로 쓴다
if exist ".gitignore" goto :gitignore_exists
> ".gitignore" echo # 가상환경
>>".gitignore" echo venv/
>>".gitignore" echo __pycache__/
>>".gitignore" echo *.pyc
>>".gitignore" echo(
>>".gitignore" echo # 환경변수 — 절대 커밋 금지 ★
>>".gitignore" echo .env
>>".gitignore" echo(
>>".gitignore" echo # 에디터
>>".gitignore" echo .vscode/
>>".gitignore" echo .idea/
if not exist ".gitignore" goto :gitignore_fail
echo   [OK] .gitignore 생성 — venv/ · .env 가 git 에 올라가지 않게
goto :gitignore_done
:gitignore_exists
echo   [i] .gitignore 가 이미 있습니다 — 그대로 둡니다.
goto :gitignore_done
:gitignore_fail
echo   [!] .gitignore 를 만들지 못했습니다 — 안내 [4-B] 전에 직접 만드세요.
:gitignore_done
echo(

rem ── [3/5] venv 생성 → 활성화 ───────────────────────────────────────────────
echo [3/5] 가상환경
if exist "venv\Scripts\python.exe" goto :venv_exists

:create_venv
echo   python -m venv venv  (10~30초)
%PY% -m venv venv
if errorlevel 1 goto :fail_venv
goto :activate

:venv_exists
echo   [!] 이미 venv 가 있습니다: %PROJ_DIR%\venv
set "ANS="
set /p "ANS=  지우고 새로 만들까요? (y = 새로 만들기 / Enter = 그대로 사용): "
if /i not "%ANS%"=="y" goto :activate
echo   기존 venv 삭제 중...
rmdir /s /q venv
if exist "venv\" goto :fail_venv
goto :create_venv

:activate
call "venv\Scripts\activate.bat"
rem 활성화 확인 — sys.prefix 가 base 와 다르면 venv 안
python -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)"
if errorlevel 1 goto :fail_activate
for /f "delims=" %%p in ('where python') do (
    set "VENV_PY=%%p"
    goto :activated
)
:activated
echo   [OK] 활성화됨: %VENV_PY%
echo(

rem ── [4/5] 2~4주차 패키지 설치 ──────────────────────────────────────────────
echo [4/5] 패키지 설치 (2~4주차)
echo   pip install %PACKAGES%
echo(
python -m pip install %PACKAGES%
if errorlevel 1 goto :fail_pip
echo(
echo   설치 확인:
python -c "from importlib.metadata import version as v; [print(f'    {p:18s} {v(p)}') for p in ['langchain', 'langchain-core', 'langchain-ollama', 'langchain-openai', 'python-dotenv', 'ollama', 'numpy']]"
if errorlevel 1 goto :fail_pip
set "RC=0"

rem ── [5/5] Git 설정 ─────────────────────────────────────────────────────────
rem  공용 PC 이므로 신원은 --local (이 폴더 안에서만). --global 은 다음 사람에게 남는다.
rem  pull/push 는 계정 인증이 필요해 자동으로 하지 않고 아래 안내로 넘긴다.
rem  ※ 괄호 블록 ( … ) 안에 한글을 두면 뒤의 goto 가 레이블을 못 찾는다 — 한 줄씩 쓴다
echo(
echo [5/5] Git 설정
where git >nul 2>&1
if errorlevel 1 goto :git_none
if exist ".git\" goto :git_have
git init -b main -q 2>nul
if not exist ".git\" git init -q
if not exist ".git\" goto :git_initfail
echo   [OK] git init
goto :git_ready

:git_have
echo   [i] 이미 git 저장소입니다 — git init 은 건너뜁니다.
goto :git_ready

:git_none
echo   [X] git 이 없어 건너뜁니다 — 조교/교수에게 알려 주세요.
goto :git_done

:git_initfail
echo   [!] git init 에 실패했습니다 — 아래 안내 [4] 를 직접 실행하세요.
goto :git_done

:git_ready
rem 이미 넣어 둔 값이 있으면 Enter 로 그대로 쓴다
set "GIT_NAME="
for /f "delims=" %%v in ('git config --local --get user.name 2^>nul') do set "GIT_NAME=%%v"
set "GIT_MAIL="
for /f "delims=" %%v in ('git config --local --get user.email 2^>nul') do set "GIT_MAIL=%%v"
set "GIT_URL="
for /f "delims=" %%v in ('git config --local --get remote.origin.url 2^>nul') do set "GIT_URL=%%v"

rem set /p 는 입력이 끊기면(EOF) 빈 값을 그대로 돌려줘 무한 반복이 된다 — 횟수로 끊는다
set /a GIT_TRY=0
:ask_git_name
set /a GIT_TRY+=1
if %GIT_TRY% GTR 5 goto :git_input_dead
set "ANS="
if defined GIT_NAME set /p "ANS=  이름 (git user.name · Enter = %GIT_NAME%): "
if not defined GIT_NAME set /p "ANS=  이름 (git user.name): "
if not defined ANS set "ANS=%GIT_NAME%"
if defined ANS goto :git_name_ok
echo   [!] 이름을 입력하세요.
goto :ask_git_name
:git_name_ok
set "GIT_NAME=%ANS%"

set /a GIT_TRY=0
:ask_git_mail
set /a GIT_TRY+=1
if %GIT_TRY% GTR 5 goto :git_input_dead
set "ANS="
if defined GIT_MAIL set /p "ANS=  메일 (git user.email · Enter = %GIT_MAIL%): "
if not defined GIT_MAIL set /p "ANS=  메일 (git user.email): "
if not defined ANS set "ANS=%GIT_MAIL%"
if defined ANS goto :git_mail_check
echo   [!] 메일을 입력하세요.
goto :ask_git_mail
:git_mail_check
echo %ANS%| findstr /r /c:"^..*@..*\...*$" >nul
if not errorlevel 1 goto :git_mail_ok
echo   [!] 메일 모양이 아닙니다 - 예: hong@example.com
goto :ask_git_mail
:git_mail_ok
set "GIT_MAIL=%ANS%"

git config --local user.name  "%GIT_NAME%"
git config --local user.email "%GIT_MAIL%"

echo   GitHub 저장소 주소 — 3주차에 만든 저장소가 있으면 그 주소를 붙여 넣으세요.
echo     예: https://github.com/^<본인계정^>/langchain-2026.git
set "ANS="
if defined GIT_URL set /p "ANS=  저장소 주소 (Enter = %GIT_URL%): "
if not defined GIT_URL set /p "ANS=  저장소 주소 (Enter = 나중에): "
if not defined ANS set "ANS=%GIT_URL%"
if not defined ANS goto :git_show
set "ANS=%ANS:"=%"
if defined GIT_URL git remote set-url origin "%ANS%"
if not defined GIT_URL git remote add origin "%ANS%"
set "GIT_URL="
for /f "delims=" %%v in ('git config --local --get remote.origin.url 2^>nul') do set "GIT_URL=%%v"

:git_show
rem 화면에 찍는 값은 git 에 실제로 들어간 값이어야 한다 (cmd 는 한글 입력이 깨질 수 있다)
set "GIT_NAME="
for /f "delims=" %%v in ('git config --local --get user.name 2^>nul') do set "GIT_NAME=%%v"
set "GIT_MAIL="
for /f "delims=" %%v in ('git config --local --get user.email 2^>nul') do set "GIT_MAIL=%%v"
echo   [확인] user.name  = %GIT_NAME%
echo          user.email = %GIT_MAIL%
if defined GIT_URL echo          origin     = %GIT_URL%
if not defined GIT_URL echo          origin     = (아직 없음 - 안내 [4] 참조)
echo   ※ 이름이 깨져 보이면 - cmd 는 한글 입력이 깨질 수 있습니다. 아래를 직접 치세요.
echo      git config --local user.name "본인이름"
goto :git_done

:git_input_dead
echo   [X] 입력이 끊겨 Git 설정을 건너뜁니다 - 아래 안내 [4] 를 직접 실행하세요.

:git_done

rem ── 이후 안내 (명령어만 출력) ────────────────────────────────────────────────
echo(
echo ============================================================
echo  설치 완료 — 아래 명령은 직접 실행하세요
echo ============================================================
echo  ※ 스크립트 안에서 켠 가상환경은 스크립트가 끝나면 꺼집니다.
echo    VS Code 터미널(PowerShell)에서 아래 순서대로 다시 켜 주세요.
echo(
echo [1] VS Code 로 프로젝트 폴더 열기
echo     ※ 이미 VS Code 를 열어 두고 그 터미널에서 실행했다면 - 건너뛰세요 [스킵]
echo     code "%PROJ_DIR%"
echo(
echo [2] 가상환경 활성화 — 프롬프트 앞에 (venv) 가 붙어야 정상
echo     cd "%PROJ_DIR%"
echo     venv\Scripts\Activate.ps1
echo     where.exe python          ← 첫 줄이 ...\venv\Scripts\python.exe 인지 확인
echo(
echo     ※ "이 시스템에서 스크립트를 실행할 수 없으므로..." 가 나오면 (최초 1회)
echo     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
echo(
echo     ※ Git Bash 라면 위 명령 대신 — 이 venv 를 그대로 켤 수 있습니다
echo     source venv/Scripts/activate
echo     which python              ← .../venv/Scripts/python 인지 확인
echo     (venv 가 아니면)  export PATH="$PWD/venv/Scripts:$PATH"
echo(
echo [3] VS Code 인터프리터 지정
echo     Ctrl+Shift+P → Python: Select Interpreter → .\venv\Scripts\python.exe
echo(
echo     (공용 PC 대비) 설정을 폴더 안에 심기 — 한 줄씩 실행
echo     New-Item -ItemType Directory -Force .vscode ^| Out-Null
echo     '{ "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe" }' ^| Out-File .vscode\settings.json -Encoding ascii
echo(
echo [4] Git — init · user.name · user.email · origin 은 [5/5] 에서 끝났습니다
echo     git config --local --list   ← 방금 넣은 값을 확인만 하세요
echo     ※ 저장소 주소를 나중에 넣으려면
echo     git remote add origin https://github.com/^<본인계정^>/langchain-2026.git
echo(
echo   [4-A] GitHub 에 3주차 저장소가 이미 있는 경우 ★ 대부분 여기
echo     Rename-Item .gitignore .gitignore.bak   ← 지우지 말고 이름만 바꿉니다
echo     git pull origin main
echo       성공하면 →  Remove-Item .gitignore.bak
echo       실패하면 →  Rename-Item .gitignore.bak .gitignore   ★ 되돌리고 나서 다시 시도
echo                   되돌리지 않으면 .env 와 venv/ 를 막아 줄 파일이 없습니다
echo     git branch -u origin/main
echo     git status                ← venv/ 와 .env 가 보이면 안 됩니다
echo                               ★ 보이면 commit 하지 말고 손 드세요
echo(
echo   [4-B] 저장소가 없는 경우 (처음부터)
echo     Get-Content .gitignore    ← 스크립트가 만들어 둔 것 — venv/ · .env 가 있는지 확인
echo     pip freeze ^> requirements.txt
echo     git add .
echo     git status                ← venv/ 와 .env 가 없어야 합니다
echo                               ★ 보이면 commit 하지 말고 손 드세요
echo     git commit -m "chore: 프로젝트 초기 세팅"
echo     git push -u origin main   ← origin 은 [5/5] 에서 넣었습니다
echo(
echo [5] .env 준비 — 키는 4주차 수업 중 배포
echo     Copy-Item .env.example .env
echo     git status                ← .env 가 목록에 보이면 안 됩니다 ★
echo(
echo [6] Ollama 모델 확인 — pull 은 수업 중 금지 ★
echo     ollama list               ← gemma3:4b 가 보여야 합니다
echo(
goto :end

rem ── 오류 처리 ───────────────────────────────────────────────────────────────
:no_python
echo   [X] Python 을 찾을 수 없습니다.
echo       - 터미널에서 python -V 를 쳐 보세요.
echo       - Microsoft Store 가 열리면: 설정 → 앱 → 앱 실행 별칭 → python 끄기
echo       - Python 이 설치되어 있지 않다면 조교/교수에게 알려 주세요.
goto :end

:old_python
echo   [X] Python 3.10 이상이 필요합니다.
%PY% -V
goto :end

:bad_home
echo   [X] 폴더로 이동할 수 없습니다: %HOME_DIR%
goto :end

:bad_name
echo   [X] 폴더 이름은 영문·숫자·-·_·. 만 쓸 수 있습니다. (공백·한글 불가)
echo(
goto :ask_name

:fail_venv
echo   [X] 가상환경을 만들지 못했습니다.
echo       venv 폴더를 쓰는 프로그램(VS Code 터미널 등)을 모두 닫고 다시 실행하세요.
goto :end

:fail_activate
echo   [X] 가상환경 활성화에 실패했습니다.
echo       스크립트를 다시 실행해 "지우고 새로 만들까요?" 에서 y 를 선택하세요.
goto :end

:fail_pip
echo(
echo   [X] 패키지 설치에 실패했습니다.
echo       - 네트워크 오류라면: 스크립트를 다시 실행하고 venv 는 "그대로 사용"(Enter)을 고르세요.
echo       - "너무 깁니다" / "No such file or directory" 라면: 경로가 너무 긴 것입니다. 짧은 위치에 새로 만드세요.
echo       또는 활성화된 터미널에서 직접:
echo       pip install %PACKAGES%
goto :end

:end
echo(
pause
if defined _OLDCP "%SystemRoot%\System32\chcp.com" %_OLDCP% >nul
endlocal & exit /b %RC%
