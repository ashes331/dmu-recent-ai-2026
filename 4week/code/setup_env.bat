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
rem    1) 환경변수 dl026_HOME_DIR 위치로 이동
rem    2) 만들 폴더 이름을 입력받아 생성
rem    3) python -m venv venv 생성 → 활성화
rem    4) 2~3주차에 pip install 했던 패키지 설치
rem    5) 나머지(VS Code·Git·.env·Ollama)는 명령어만 화면에 안내
rem
rem  실행 : 탐색기에서 더블클릭  또는  터미널에서  .\setup_env.bat
rem  ※ .bat 이라 PowerShell 실행 정책(Set-ExecutionPolicy)과 무관하게 실행됩니다.
rem  ※ 이 파일은 UTF-8 + CRLF 로 저장해야 합니다. (LF 로 저장하면 goto 가 깨짐)
rem ============================================================================

rem ── 설치할 패키지 (2~3주차) ────────────────────────────────────────────────
rem  2주차 실습 1 (로컬 Ollama)  : ollama, numpy
rem  3주차 1~3교시 (첫 체인)      : langchain, langchain-core, langchain-ollama, python-dotenv
rem  ※ 버전은 교수 PC에서 3주차 실습을 검증한 버전으로 고정 (2026/requirements.txt 와 동일)
rem  ※ sentence-transformers·matplotlib 은 2주차 Colab 전용이라 설치하지 않음 (PyTorch 대용량)
set "PACKAGES=langchain==1.4.0 langchain-core==1.6.2 langchain-ollama==1.1.0 python-dotenv==1.2.3 ollama==0.6.2 numpy"
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

rem ── [1/4] dl026_HOME_DIR 로 이동 ───────────────────────────────────────────
echo [1/4] 작업 위치 확인
set "HOME_DIR=%dl026_HOME_DIR%"
if defined HOME_DIR goto :check_home
echo   [!] 환경변수 dl026_HOME_DIR 이 설정되어 있지 않습니다.
echo       실습실 PC라면 조교/교수에게 알려 주세요.
set /p "HOME_DIR=  상위 폴더 경로 (Enter = 지금 폴더 %CD%): "
if not defined HOME_DIR set "HOME_DIR=%CD%"

:check_home
set "HOME_DIR=%HOME_DIR:"=%"
if "%HOME_DIR:~-1%"=="\" set "HOME_DIR=%HOME_DIR:~0,-1%"
if not exist "%HOME_DIR%\" goto :bad_home
cd /d "%HOME_DIR%" || goto :bad_home
echo   위치: %CD%
echo(

rem ── [2/4] 폴더 이름 입력 → 생성 ────────────────────────────────────────────
:ask_name
echo [2/4] 프로젝트 폴더
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
echo       dl026_HOME_DIR 을 짧은 경로(예: D:\dl026)로 쓰거나, 폴더 이름을 짧게 하세요.
:path_ok
set "ANS="
set /p "ANS=  이 위치로 진행할까요? (Enter = 진행 / n = 이름 다시 입력): "
if /i "%ANS%"=="n" goto :ask_name

if exist "%PROJ_DIR%\" echo   [i] 이미 있는 폴더입니다 — 그대로 사용합니다.
if not exist "%PROJ_DIR%\" mkdir "%PROJ_DIR%"
cd /d "%PROJ_DIR%" || goto :bad_home
echo(

rem ── [3/4] venv 생성 → 활성화 ───────────────────────────────────────────────
echo [3/4] 가상환경
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

rem ── [4/4] 2~3주차 패키지 설치 ──────────────────────────────────────────────
echo [4/4] 패키지 설치 (2~3주차)
echo   pip install %PACKAGES%
echo(
python -m pip install %PACKAGES%
if errorlevel 1 goto :fail_pip
echo(
echo   설치 확인:
python -c "from importlib.metadata import version as v; [print(f'    {p:18s} {v(p)}') for p in ['langchain', 'langchain-core', 'langchain-ollama', 'python-dotenv', 'ollama', 'numpy']]"
if errorlevel 1 goto :fail_pip
set "RC=0"

rem ── 이후 안내 (명령어만 출력) ────────────────────────────────────────────────
echo(
echo ============================================================
echo  설치 완료 — 아래 명령은 직접 실행하세요
echo ============================================================
echo  ※ 스크립트 안에서 켠 가상환경은 스크립트가 끝나면 꺼집니다.
echo    VS Code 터미널(PowerShell)에서 아래 순서대로 다시 켜 주세요.
echo(
echo [1] VS Code 로 프로젝트 폴더 열기
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
echo [3] VS Code 인터프리터 지정
echo     Ctrl+Shift+P → Python: Select Interpreter → .\venv\Scripts\python.exe
echo(
echo     (공용 PC 대비) 설정을 폴더 안에 심기 — 한 줄씩 실행
echo     New-Item -ItemType Directory -Force .vscode ^| Out-Null
echo     '{ "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe" }' ^| Out-File .vscode\settings.json -Encoding ascii
echo(
echo [4] Git — 공용 PC 이므로 신원은 --local 로
echo     git config --global init.defaultBranch main
echo     git init
echo     git config --local user.name  "본인이름"
echo     git config --local user.email "본인메일@example.com"
echo(
echo   [4-A] GitHub 에 3주차 저장소가 이미 있는 경우 ★ 대부분 여기
echo     git remote add origin https://github.com/^<본인계정^>/langchain-2026.git
echo     git pull origin main
echo     git branch -u origin/main
echo     git status                ← venv/ 가 목록에 보이면 안 됩니다
echo(
echo   [4-B] 저장소가 없는 경우 (처음부터)
echo     VS Code 탐색기 → 새 파일 → .gitignore
echo       내용: venv/  __pycache__/  *.pyc  .env  .vscode/  .idea/   (한 줄에 하나씩)
echo     pip freeze ^> requirements.txt
echo     git add .
echo     git status                ← venv/ 와 .env 가 없어야 합니다
echo     git commit -m "chore: 프로젝트 초기 세팅"
echo     git remote add origin https://github.com/^<본인계정^>/langchain-2026.git
echo     git push -u origin main
echo(
echo [5] .env 준비 — 키는 4주차 수업 중 배포
echo     Copy-Item .env.example .env
echo     git status                ← .env 가 목록에 보이면 안 됩니다 ★
echo(
echo [6] 4주차 패키지 — 수업 안내에 따라
echo     pip install langchain-openai
echo(
echo [7] Ollama 모델 확인 — pull 은 수업 중 금지 ★
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
