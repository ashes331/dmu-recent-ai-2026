# 6주차 실습 코드 — LangSmith (1) 추적과 디버깅

2026년 10월 7일 (수) — 추석 보강일 / 최신인공지능 6주차
※ 진도 맞바꿈 적용 — 10/2(금)에 5주차 진도, **10/7(수)** 에 6주차 진도

> **"`print()`로 디버깅해 보셨죠? LLM 앱에서는 그게 왜 안 통하는지 봅니다."**

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| **실습 1** ★ | 1교시 2절 | [`check_langsmith.py`](check_langsmith.py) | `.env` 연동 확인 · 흔한 실수 3종 자동 진단 — **가장 먼저** 실행 |
| **실습 1** ★★ | 1교시 2-4 | [`trace_on.py`](trace_on.py) | **코드 수정 0줄** — 5주차 체인을 그대로 실행해 목록에 찍히는지 본다 |
| — | 1교시 2-5 | [`trace_off.py`](trace_off.py) | **끄는 법** ⚠️ 보안 — 같은 질문 3번 중 **2건만** 기록되면 정상 |
| **실습 2** ★★ | 2교시 | [`RESULTS.md`](RESULTS.md) | **코드 없음** — 브라우저에서 추적 트리를 읽고 이 기록표를 채운다 (= 과제 2의 뼈대) |
| 시연 | 2교시 3절 | [`slow_chain.py`](slow_chain.py) | 병목이 눈에 띄게 만든 체인 · **부모 Run의 함정** ★ (직접 돌려 봐도 됩니다) |
| 시연 | 2교시 2-3 | [`self_consistency_traced.py`](self_consistency_traced.py) | **(추가)** 5주차 `self_consistency.py` + 맨 위 `load_dotenv()` 두 줄 — `batch()` 의 추적 모양 |
| **실습 3** ★ | 3교시 1-2 | [`traceable_custom.py`](traceable_custom.py) | **`@traceable`** — 내 함수를 트리에 올린다 |
| **실습 3** ★★ | 3교시 1-3 | [`tags_metadata.py`](tags_metadata.py) | **태그·메타데이터로 실험 구분** (7주차 A/B의 전제) |
| **실습 4** | 3교시 2절 | [`prompt_hub.py`](prompt_hub.py) | Prompt Hub 등록 · 버전 갱신 · 불러오기 |
| **실습 7** ★ | 4교시 3절 | [`socket_hello.py`](socket_hello.py) | **(추가)** Socket Mode 연결 확인 — 멘션하면 `pong` |
| 준비 | 4교시 4절 | [`llm_backends.py`](llm_backends.py) | **(추가)** OpenAI · Ollama 를 슬랙 없이 먼저 확인 |
| **실습 8** ★★ | 4교시 4절 | [`slack_llm_bot.py`](slack_llm_bot.py) | **(추가)** 슬랙에서 묻고 **내 PC의 LLM 이 답한다** |
| 점검 | — | [`net_check.py`](net_check.py) | LangSmith 서버에 **접속 자체가 안 될 때** 확인 |
| 견본 | — | [`.env.example`](.env.example) | 오늘 추가되는 환경변수 견본 |

> 저장소에서는 `week06/` 경로에 두고 작업합니다.
> 2교시에는 5주차 `week05/` 의 `self_consistency.py` · `ab_failrate.py` 도 다시 씁니다 — 아래 «실행 순서» 참고.

## 사전 준비

```bash
# 5주차까지 쓰던 가상환경을 그대로 사용합니다
# Windows
venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt     # 1~3교시는 새로 설치할 것이 사실상 없습니다

ollama list                         # gemma3:4b 가 보여야 함
```

**`.env` 는 저장소 맨 위 폴더에 있는 그 파일 하나**를 계속 씁니다. `week06/` 안에 새로 만들지 마세요.
[`.env.example`](.env.example) 의 `LANGSMITH_` 세 줄을 그 `.env` 에 옮겨 적고, `LANGSMITH_API_KEY` 를 채웁니다.

```bash
# 저장소 맨 위 폴더에서
git check-ignore -v .env            # ★ 출력이 나와야 안전합니다
```

⚠️ **`.env` 는 절대 커밋하지 않습니다.** 3주차 과제 1의 채점 항목이었고, **오늘 키가 하나 더 늘었습니다.**

⚠️⚠️ **개인 신용카드를 절대 등록하지 마세요.**
무료 Developer 플랜은 **카드 없이 가입되고**, 한도를 넘으면 **429로 거부될 뿐 과금되지 않습니다**(하드 캡).
카드를 등록하면 그 안전장치가 풀립니다.

### (추가) 4교시 슬랙 봇 준비

```bash
pip install slack_bolt langchain-openai     # requirements.txt 에도 추가되어 있습니다
```

5주차 4교시에 만든 슬랙 앱에 **네 가지**를 더합니다 (`PPT/4교시_Slack_Socket_Mode_LLM_봇.html` 5~9장).

| # | 어디서 | 무엇을 |
|---|---|---|
| ① | Settings → **Socket Mode** | Enable → 토큰 이름 입력 → Generate → `xapp-...` 를 `.env` 의 `SLACK_APP_TOKEN` 에 |
| ② | Features → **Event Subscriptions** | Enable Events → Subscribe to bot events → **`app_mention`** → Save Changes |
| ③ | 화면 위 노란 배너 | **재설치(reinstall)** → 허용 — 스코프가 늘었으므로 필수 ★ |
| ④ | 슬랙 채널 | 5주차에 `/invite` 한 채널이면 그대로. 아니면 `/invite @내앱이름` |

> ⚠️ 4교시는 **로컬 전용**입니다. Colab 노트북에는 없습니다 — 봇은 **켜 둔 채 기다리는 프로그램**이고,
> Ollama 도 **내 PC**에서 돌기 때문입니다.

## 실행 순서 (수업 진행 순서)

```bash
# ── 1교시 : 연동 — 코드 수정 0줄을 확인하는 것이 목표 ★
python check_langsmith.py      # 실습 1 — .env 가 제대로 로드됐나 (먼저!)
python trace_on.py             # 실습 1 ★★ — 목록에 찍히는 것까지만
python trace_off.py            # 2-5절 — 끄는 법 ⚠️

# ── 2교시 : 화면 읽기 (브라우저) ★★ — RESULTS.md 를 열어 놓고 채웁니다
python slow_chain.py 2         # 병목 + 워밍업 비교 ★
python ../week05/ab_failrate.py        # 실패한 Run 필터링 (§2-2)
python self_consistency_traced.py     # batch() 의 추적 모양 (§2-3, N=5 · 2회 이내 ⚠️) — (추가) 5주차 사본, 두 줄 이미 넣음

# ── 3교시 : 범위 넓히기 + 버전 관리
python traceable_custom.py     # 실습 3 ★
python traceable_custom.py 50  #   ★ 50자로 잘라 '전처리 버그'를 일부러 만들어 본다
python tags_metadata.py        # 실습 3 ★★ — 태그·메타데이터
python prompt_hub.py           # 실습 4

# ── (추가) 4교시 : 슬랙 Socket Mode 봇 — 로컬 전용
python socket_hello.py         # 실습 7 ★ — "Bolt app is running!" 후 슬랙에서 @내앱이름 안녕 → pong
python llm_backends.py         #   슬랙 없이 두 모델 먼저 확인 (봇이 침묵할 때 범인 가르기)
python slack_llm_bot.py        # 실습 8 ★★ — @내앱이름 질문 / openai 질문 / 비교 질문
                               #   끝낼 때는 Ctrl+C ⚠️ 켜 두면 누구나 내 OpenAI 키를 씁니다
```

> ⚠️ **5주차 파일은 그대로 돌리면 추적되지 않습니다.** `self_consistency.py` · `ab_failrate.py` 에는
> `load_dotenv()` 가 없어서 `.env` 의 `LANGSMITH_TRACING=true` 를 읽지 못합니다.
> (추가) `self_consistency.py` 는 두 줄을 넣은 사본 `self_consistency_traced.py` 를 이 폴더에 두었습니다. `ab_failrate.py` 는
> 파일의 **맨 위**에 아래 두 줄을 넣고 실행하세요. `trace_on.py` 가 5주차 체인에 더한 것도 이 두 줄뿐입니다.
>
> ```python
> from dotenv import load_dotenv
> load_dotenv()
> ```

## 오늘 추가되는 환경변수 3개 ★

| 변수 | 하는 일 | 안 넣으면 |
|---|---|---|
| **`LANGSMITH_TRACING`** | 추적 켜기/끄기 스위치 ★ | 추적 안 됨 |
| **`LANGSMITH_API_KEY`** | 내 계정으로 보내기 | 인증 실패 |
| `LANGSMITH_PROJECT` | 기록을 담을 프로젝트 이름 | `default` 로 들어감 |

> **프로젝트 이름은 `.env` 를 고치지 말고 실행할 때 바꿉니다** — `LANGSMITH_PROJECT=week07-eval python trace_on.py` (Git Bash).
> `load_dotenv()` 는 이미 있는 환경변수를 덮어쓰지 않기 때문입니다. 코드 · 호출 단위로 바꾸는 법은 1교시 §2-3 «(추가) 프로젝트 이름 바꾸는 법».

> 예전 이름은 `LANGCHAIN_TRACING_V2` · `LANGCHAIN_API_KEY` · `LANGCHAIN_PROJECT` 입니다.
> 인터넷 예제에서 이 이름을 보면 같은 것입니다. `check_langsmith.py` 가 두 이름을 모두 확인해 줍니다.

## ⚠️ 안 될 때의 점검 순서

| 증상 | 원인 | 조치 |
|---|---|---|
| 목록에 아무것도 없음 | `LANGSMITH_TRACING` 이 `true` 가 아님 | `python check_langsmith.py` |
| 목록에 아무것도 없음 (5주차 파일) | 파일에 `load_dotenv()` 가 없음 | 위 «실행 순서» 의 두 줄을 **맨 위**에 ★ |
| 인증 오류 | 키 앞뒤 공백·따옴표 | `.env` 에서 따옴표 없이 붙여넣기 |
| **`.env` 를 고쳤는데 안 바뀜** ★ | 셸에 기존 환경변수가 남아 있음 | **터미널을 새로 열고** 재실행 |
| `load_dotenv()` 가 아래쪽에 있음 | 라이브러리가 이미 값을 읽은 뒤 | **파일 맨 위**로 올린다 ★ |
| 접속 자체가 안 됨 | 프록시·백신 | `python net_check.py` |
| 토큰 수가 안 보임 | 모델 공급자·버전에 따라 비어 있음 | 기록표에 **"측정 불가"** 로 적는다 (4주차 `usage_metadata` 와 같은 이슈) |
| `prompt_hub.py` 에서 인자 오류 | `langsmith` 버전마다 함수 인자 이름이 다름 | 에러 메시지를 그대로 캡처해 질문 |

## 주의

- 모든 파일 상단에 `MODEL = "gemma3:4b"` 상수를 두었습니다.
  실습실 모델이 다르면 **이 한 줄만** 고치면 됩니다.
- `load_dotenv()` 는 **반드시 파일 맨 위**에 둡니다. 아래에 있으면 안 먹습니다. ★
  (그래서 이 폴더의 파일들은 `import` 순서가 일반적인 관례와 다릅니다 — 의도된 것입니다)
- `trace_on.py` 는 5주차 `least_to_most.py` 를 옮긴 것입니다.
  **다른 점은 맨 위의 `load_dotenv()` 두 줄뿐**입니다.
  내 `week05/least_to_most.py` 맨 위에 그 두 줄만 넣고 돌려도 똑같이 추적됩니다. ★
- 추적을 켜면 **프롬프트와 응답이 외부 서비스로 전송**됩니다.
  개인정보 · 기밀 · 실제 고객 데이터는 넣지 마세요. 그런 데이터를 다룰 때는 `trace_off.py` 의 방법으로 끕니다. ⚠️
- `batch(N)` 은 **N traces** 를 소모합니다. 실습 중에는 **N=5, 실행 2회 이내**로 하세요. ⚠️

## ⚠️ 무료 플랜 제약 네 가지

| 제약 | 실제로 무슨 일이 | 우리의 대응 |
|---|---|---|
| **카드 등록 불필요 (하드 캡)** | 한도 초과 시 429 거부, **과금 없음** | ⚠️ **개인 카드 절대 등록 금지** ★ |
| **1 seat** | 워크스페이스에 남을 초대 불가 | 과제는 **공유 링크 + 캡처**로 제출 |
| **추적 보존 14일** ★ | 오늘 추적은 **10/21경 소멸** | **캡처 필수**, 링크는 보조 ★★ |
| **월 5,000 traces** | 반복 실습 시 소모 | `batch(N)` 반복 자제 |

```
   chain.invoke() 1회             =  1 trace
   Least-to-Most 1회 (LLM 5~6회)  =  1 trace     ← 안에서 몇 번 부르든 1건
   batch(5) 1회                   =  5 traces ⚠️
```

## 📌 과제 2

| # | 제출물 |
|---|--------|
| 1 | 추적이 적용된 체인 코드 (`week06/` 커밋) |
| 2 | 분석 보고서 — **병목 구간 / 토큰 사용량 / 개선 아이디어** |
| 3 | ★ **추적 화면 캡처 (필수)** — 트리가 펼쳐진 화면 |
| 4 | 공개 공유(Share) 링크 (선택) |

> [`RESULTS.md`](RESULTS.md) 를 채우면 **보고서의 절반이 이미 완성**됩니다.
> ⚠️ **부모 Run 을 병목으로 적지 마세요** — 병목은 **잎 Run** 입니다. ★
> **마감**: 수업에서 공지합니다. 추적은 14일 뒤 사라지므로 **캡처를 미리미리 저장**하세요.

## 오늘의 한 줄

> **재현할 수 없다면, 기록해 두는 수밖에 없다.**
>
> 코드 수정 0줄 · 환경변수 3줄 — 그리고 병목은 **부모가 아니라 잎**에 있다. ★
