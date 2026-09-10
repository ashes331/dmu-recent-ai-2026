# 4주차 실습 코드 — Model I/O (1) 로컬 LLM과 상용 LLM을 하나의 인터페이스로

2026년 9월 18일 (금) / 최신인공지능 4주차

> **"코드 한 줄만 바꿉니다. 나머지는 그대로입니다."**
> 3주차에 만든 체인에서 **모델 자리만** 교체합니다.

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| 확인 B | 1교시 | [`vram_calc.py`](vram_calc.py) | VRAM 요구량 어림 계산 (손계산 검산용) |
| — | 2교시 | [`bind_params.py`](bind_params.py) | `ChatOllama` 파라미터 지정 / `.bind()` |
| **실습 1** ★★ | 2교시 | [`swap_models.py`](swap_models.py) | **동일 체인에서 모델 2종 교체·측정** |
| **실습 2** ★ | 2교시 | [`비교표_양식.md`](비교표_양식.md) | 6항목 비교표 작성 (저장소 커밋) |
| — | 3교시 | [`common_params.py`](common_params.py) | `temperature`·`max_tokens`·`timeout`·`max_retries` |
| **실습 3** | 3교시 | [`fallback.py`](fallback.py) | 상용 실패 → 로컬 대체 (`with_fallbacks`) |
| **실습 4** ★ | 3교시 | [`streaming.py`](streaming.py) | 첫 토큰 지연 측정 → **비교표 완성** |

> 학생 저장소에서는 `week04/` 경로에 두게 합니다.
> 1교시에는 **번호 붙은 실습이 없습니다** — `ollama list`·`show`·`ps` 는 터미널에서 직접 칩니다.

## 사전 준비

```bash
# 1) 3주차 저장소(과제 1)를 clone 하고 가상환경 활성화
#    Windows
venv\Scripts\activate

# 2) 4주차 패키지 설치 — langchain-openai 가 추가됩니다
pip install -r requirements.txt

# 3) .env 준비  ★
copy .env.example .env        # Windows  (macOS/Linux: cp)
#    → .env 의 OPENAI_API_KEY= 뒤에 수업 중 배포되는 공용 키를 넣습니다

# 4) ⚠️ 실습 시작 전 반드시 확인 — .env 가 여기 보이면 안 됩니다
git status

# 5) 모델 확인 (pull 은 수업 중 금지 ★ — 사전 설치되어 있습니다)
ollama list          # gemma3:4b 가 보여야 함
```

## 실행 순서 (수업 진행 순서)

```bash
# ── 1교시 ── 터미널에서 직접
ollama show gemma3:4b        # 파라미터 수 · 컨텍스트 길이 · 양자화 조회 ★
python vram_calc.py          # 손계산과 맞춰 본다
python vram_calc.py 4.3 8192 # 내 화면의 값으로 계산
ollama run gemma3:4b "안녕"  # 메모리에 올리고
ollama ps                    # SIZE 와 PROCESSOR 열 확인 ★
ollama stop gemma3:4b        # 2교시 전 VRAM 확보

# ── 2교시 ──
python bind_params.py        # 1절
python swap_models.py        # 실습 1  ★★
#                            → 결과를 비교표_양식.md 에 옮겨 적기 (실습 2)

# ── 3교시 ──
python common_params.py      # 1절
python fallback.py           # 실습 3
python streaming.py          # 실습 4  ★ → 비교표의 '첫 토큰까지' 칸 완성
```

## 주의

- **`ollama pull` 은 수업 중 절대 실행 금지.** 30명이 동시에 수 GB를 받으면
  실습실 네트워크가 마비됩니다. 필요한 모델은 사전 pull 완료 상태입니다.
- 모든 파일 상단에 `LOCAL_MODEL = "gemma3:4b"` 상수를 두었습니다.
  실습실 모델이 다르면 **이 한 줄만** 고치면 됩니다.
- 🔶 **상용 모델명은 자주 바뀝니다.** 각 파일의 `OPENAI_MODEL` 값을
  **수업 전날 공식 문서에서 확인**해 확정하고 배포하십시오.
- 🔶 `usage_metadata` 는 공급자·버전에 따라 비어 있을 수 있습니다.
  학기 전에 2종 모두 찍어보고, 안 나오는 항목은 비교표에서 **"측정 불가"** 로 처리하도록
  미리 정해 두십시오.
- **`.env` 는 절대 커밋하지 않습니다.** `.env.example` 만 커밋합니다.

## ⚠️ Claude(Anthropic)는 제외입니다

`ChatAnthropic` 은 **Anthropic API 키**가 필요하며, 학생이 가진
**Claude Code 구독 계정으로는 호출할 수 없습니다.**
교체 실습은 **로컬 ↔ OpenAI 2종**으로 진행하며, `langchain-anthropic` 도 설치하지 않습니다.

## 상용 키를 못 쓰게 된 경우 (자동 대체)

`swap_models.py` 와 `streaming.py` 는 `OPENAI_API_KEY` 가 없으면
**로컬 2종 비교**(`gemma3:1b` vs `gemma3:4b`)로 자동 전환됩니다. 코드 구조는 그대로입니다.

| 실습 | 대체 방식 |
|---|---|
| 실습 1 | 로컬 2종 비교 (자동) |
| 실습 2 | 비교표의 **'비용' → '메모리 점유'**(`ollama ps` 의 SIZE)로 치환 |
| 실습 3 | `fallback.py` 의 `primary` 를 `ChatOllama(model="없는모델")` 로 바꿔 로컬→로컬 폴백 |
| 실습 4 | 변경 없음 (로컬에서도 스트리밍 동작) |

## 오늘 산출물 확인

- [ ] `swap_models.py` — 모델 2종 교체 실행
- [ ] `fallback.py` — 폴백 동작 확인
- [ ] `streaming.py` — 첫 토큰 지연 측정
- [ ] **비교표 (6항목 완성본)** ★ — 저장소에 커밋

> 📌 비교표는 정규 과제가 아니지만 버리지 마십시오.
> **10주차 미니 프로젝트 명세**에서 *"왜 이 모델을 골랐는가"* 의 근거로 그대로 씁니다.
