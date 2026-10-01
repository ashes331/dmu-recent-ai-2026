## VSCODE 터미널 실행 git bash 실행

## setup_env.sh를 다운로드 하여 바탕화면 > 최신인공지능 폴더에 복사합니다.
white@DESKTOP-HODBN6P MINGW64 ~/Desktop/강의/동양/최신인공지능
$ cp 2026/4week/code/setup_env.sh ./

## setup_env.sh 실행
white@DESKTOP-HODBN6P MINGW64 ~/Desktop/강의/동양/최신인공지능
$ bash setup_env.sh 
============================================================
 최신인공지능 — 실습실 PC 초기 셋팅 (Git Bash)
============================================================

[0] 사전 점검
  [OK] Python 3.13.7  (python)
  [OK] git
  [OK] ollama
  [OK] gemma3:4b
  [OK] VS Code
  ※ [X] 가 있으면 조교/교수에게 알려 주세요.

[1/5] 작업 위치
  프로젝트 폴더를 만들 «상위 폴더» 를 입력하세요.
  탐색기 주소창의 경로를 복사해 붙여 넣어도 됩니다 (예: D:\dl026).
  상위 폴더 경로 (Enter = 지금 폴더 C:\Users\white\Desktop\강의\동양\최신인공지능): 
  위치: C:\Users\white\Desktop\강의\동양\최신인공지능

[2/5] 프로젝트 폴더
  만들 폴더 이름 (Enter = langchain-2026): 2026
  만들 위치: C:\Users\white\Desktop\강의\동양\최신인공지능\2026
  이 위치로 진행할까요? (Enter = 진행 / n = 이름 다시 입력): 
  [i] 이미 있는 폴더입니다 — 그대로 사용합니다.
  [i] .gitignore 가 이미 있습니다 — 그대로 둡니다.

[3/5] 가상환경
  [!] 이미 venv 가 있습니다: C:\Users\white\Desktop\강의\동양\최신인공지능\2026\venv
  지우고 새로 만들까요? (y = 새로 만들기 / Enter = 그대로 사용): y
  기존 venv 삭제 중...
  python -m venv venv  (10~30초)
  [OK] 활성화됨: C:\Users\white\Desktop\강의\동양\최신인공지능\2026\venv\Scripts\python.exe

[4/5] 패키지 설치 (2~4주차)
  pip install langchain==1.4.0 langchain-core==1.6.2 langchain-ollama==1.1.0 python-dotenv==1.2.3 ollama==0.6.2 numpy langchain-openai==1.6.2

Collecting langchain==1.4.0
  Using cached langchain-1.4.0-py3-none-any.whl.metadata (6.2 kB)
Collecting langchain-core==1.6.2
  Using cached langchain_core-1.6.2-py3-none-any.whl.metadata (4.8 kB)
Collecting langchain-ollama==1.1.0
  Using cached langchain_ollama-1.1.0-py3-none-any.whl.metadata (3.0 kB)
Collecting python-dotenv==1.2.3