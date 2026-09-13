# 3주차 실습 코드 — 개발 환경과 LangChain 첫 체인

「최신인공지능」 2026 — 3주차 *개발 환경과 LangChain 첫 체인* (2026년 9월 11일 금)

수업 계획서: [3week/plane/전체플렌.md](../plane/전체플렌.md)

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| **실습 1** | 1교시 | [`.env.example`](.env.example), [`.gitignore`](.gitignore), [`check_env.py`](check_env.py) | 프로젝트 세팅 + `.env` 분리 확인 |
| **실습 2** | 2교시 | [`first_call.py`](first_call.py) | LangChain 첫 호출 (`ChatOllama`) |
| **실습 3** ★ | 2교시 | [`compare_sdk.py`](compare_sdk.py) | `ollama.chat()` vs `ChatOllama` 비교 |
| **실습 4** | 2교시 | [`messages.py`](messages.py) | 메시지 타입 (System / Human / AI) |
| — | 3교시 | [`prompt_template.py`](prompt_template.py) | ChatPromptTemplate 단독 실습 |
| — | 3교시 | [`output_parser.py`](output_parser.py) | StrOutputParser 단독 실습 |
| **실습 5** ★ | 3교시 | [`first_chain.py`](first_chain.py) | **`prompt \| llm \| parser` 체인 조립** |

> `first_chain.py`는 **과제 1의 제출물**입니다. 학생 저장소에서는 `week03/first_chain.py`
> 경로에 두게 합니다.

## 사전 준비

```bash
# 1) 프로젝트 폴더 + 가상환경
mkdir langchain-2026
cd langchain-2026
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate

# 2) 패키지 설치
pip install -r requirements.txt

# 3) Ollama 모델 확인
ollama list          # gemma3:4b 가 보여야 함
# 없으면: ollama pull gemma3:4b
```

## 실행 순서 (수업 진행 순서)

```bash
python check_env.py        # 1교시 — .env 로드 확인
python first_call.py       # 2교시 실습 2
python messages.py         # 2교시 실습 4
python compare_sdk.py      # 2교시 실습 3  ★
python prompt_template.py  # 3교시 1절
python output_parser.py    # 3교시 2절
python first_chain.py      # 3교시 실습 5  ★
```

## 주의

- **PowerShell에서 활성화가 막히면** `이 시스템에서 스크립트를 실행할 수 없으므로...` 오류입니다.
  최초 1회만 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 을 실행하십시오.
- **환경 재생성은 PowerShell 문법으로**: `Remove-Item -Recurse -Force venv`
  (`rmdir /s /q` 는 cmd.exe 전용이라 PowerShell에서는 동작하지 않습니다.)
- 모든 파일은 `MODEL = "gemma3:4b"` 상수를 파일 상단에 두었습니다.
  실습실 모델이 다르면 **이 한 줄만** 고치면 됩니다.
- `.env`는 **절대 커밋하지 않습니다.** `.env.example`만 커밋합니다.
- `compare_sdk.py`는 `ollama` 패키지(공급자 전용 SDK)도 필요합니다.
