# 5주차 실습 코드 — 프롬프트 심화와 LCEL

2026년 10월 2일 (금) / 최신인공지능 5주차
※ 진도 맞바꿈 적용 — 10/2에 **5주차 진도**, 10/7(수) 보강일에 6주차 진도

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| **확인 A** ★ | 1교시 1-5 | [`ask_json.py`](ask_json.py) | "JSON으로 답해줘" 를 10회 실행 — 형식이 흔들리는 장면 |
| — | 1교시 1-3 | [`few_shot.py`](few_shot.py) | Few-shot — 예시를 문자열이 아닌 **데이터(리스트)** 로 |
| **확인 C** ★★ | 1교시 1-6 | [`technique_ab.py`](technique_ab.py) | **기법 4종 A/B** — Zero-shot · Few-shot · CoT · Self-Consistency 를 쓸 때와 안 쓸 때 |
| — | 2교시 1절 | [`placeholder_partial.py`](placeholder_partial.py) | `MessagesPlaceholder` · `partial()` |
| **실습 1** ★ | 2교시 3절 | [`structured.py`](structured.py) | **`with_structured_output()` + Pydantic** |
| **실습 2** ★★ | 2교시 4절 | [`ab_failrate.py`](ab_failrate.py) | **파싱 실패율 A/B 20회 측정** |
| — | 3교시 1절 | [`runnable_basics.py`](runnable_basics.py) | LCEL · `RunnableLambda` / `assign` / `RunnableParallel` |
| **실습 3** ★★ | 3교시 2절 | [`least_to_most.py`](least_to_most.py) | **Least-to-Most 분해 체인 (직렬)** |
| **실습 4** ★ | 3교시 3절 | [`self_consistency.py`](self_consistency.py) | **Self-Consistency — `batch()` 다수결 (병렬)** |
| **실습 5** ★ | 4교시 3절 | [`send_slack_message.py`](send_slack_message.py) | **Slack API 로 채널에 메시지 전송** (추가) |
| **실습 6** | 4교시 4절 | [`chain_to_slack.py`](chain_to_slack.py) | **체인 끝에 `RunnableLambda` 로 슬랙 붙이기** (추가) |
| 설정 | 4교시 | [`.env.example`](.env.example) · `.gitignore` | `SLACK_BOT_TOKEN` 견본 (추가) |
| 기록 | — | [`RESULTS.md`](RESULTS.md) | 실습 2·4의 **측정 결과 기록표** |

> 저장소에서는 `week05/` 경로에 두고 작업합니다.
> **`least_to_most.py` 가 6주차 [과제 2]("5주차 체인에 LangSmith 추적 적용")의 대상**입니다.

## 사전 준비

```bash
# 4주차까지 쓰던 가상환경을 그대로 사용합니다
# Windows
venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt

ollama list          # gemma3:4b 가 보여야 함
# 없으면: ollama pull gemma3:4b
```

1~3교시에 새로 설치할 것은 사실상 없습니다 — `pydantic` 은 `langchain-core` 의존성으로 이미 들어와 있습니다.

**(추가) 4교시 Slack 실습**은 패키지 하나와 슬랙 쪽 설정 4단계가 더 필요합니다.

```bash
pip install slack_sdk            # requirements.txt 에도 추가되어 있습니다

cp .env.example .env             # Git Bash  (PowerShell: Copy-Item .env.example .env)
#  .env 에 SLACK_BOT_TOKEN=xoxb-... 와 SLACK_CHANNEL=#수업-출력물 를 채웁니다

git check-ignore -v .env         # 출력이 나오면 무시되고 있는 것 = 안전 ★
```

`#수업-출력물` 채널은 **교수자가 이미 만들어 두었습니다.** 직접 만들 필요 없습니다.
채널 목록에서 찾아 **참여**한 뒤 `/invite @본인앱이름` 으로 **자기 봇만** 초대하면 됩니다.
수강생 전원이 한 채널을 쓰므로, 앱 이름을 `chain-notifier-학번` 으로 지어 보낸 사람을 구분합니다.

슬랙 쪽 4단계(① 앱 생성 → ② `chat:write` → ③ 설치·토큰 → ④ `/invite`)는
`PPT/4교시_Slack_API_메시지_전송.html` 슬라이드 5~13에 화면과 함께 있습니다.
⚠️ **예전 자료의 `From scratch` 는 현재 `Blank app`** 입니다. 2026년에 화면이 바뀌었습니다.

## 실행 순서 (수업 진행 순서)

```bash
# 1교시
python ask_json.py             # 확인 A — 부탁의 실패 장면  ★
python few_shot.py             # 1-3절 (시간 여유가 있을 때)
python technique_ab.py         # 확인 C — 기법 4종 A/B  ★★ (약 27회 호출, 수 분)
python technique_ab.py cot     #   시간이 빠듯하면 ③ CoT 하나만 (약 3분)

# 2교시
python placeholder_partial.py  # 1절
python structured.py           # 실습 1  ★
python ab_failrate.py          # 실습 2  ★★   (20회 × 2 = 수 분 소요)
python ab_failrate.py 10       #   시간이 빠듯하면 N=10

# 3교시
python runnable_basics.py      # 1절
python least_to_most.py        # 실습 3  ★★
python self_consistency.py 0   # 실습 4 — 먼저 temp=0 (만장일치를 보여준다) ★
python self_consistency.py     # 그다음 temp=0.8 (표가 갈린다)

# 4교시 (추가)
python send_slack_message.py            # 실습 5 — 슬랙 전송  ★
python send_slack_message.py "테스트"    # 내용을 바꿔 보낼 때
python chain_to_slack.py                # 실습 6 — 가벼운 1단 체인 + 슬랙 (권장: 먼저)
python chain_to_slack.py full           #   3교시 분해 체인 + 슬랙 (LLM 5~6회, 수 분)
```

## 온도(temperature) 설정 — 목적에 따라 반대로 잡습니다 ★

| 파일 | 온도 | 이유 |
|---|---:|---|
| `ask_json.py` | 0.7 | 형식이 **흔들려야** 실패 장면이 보인다 |
| `structured.py` | 0 | 구조화 출력은 **낮게** |
| `ab_failrate.py` | 0.7 | **A·B에 동일 적용** — 한쪽만 0이면 실험이 성립 안 함 ⚠️ |
| `least_to_most.py` | 0 | 분해·풀이는 낮게 |
| `self_consistency.py` | 0.8 | **0이면 N번 돌려도 같은 답** → 다수결이 무의미 ⚠️ |
| `technique_ab.py` | 0.7 | **A·B에 동일 적용** — 한쪽만 0이면 비교가 성립 안 함 ⚠️ |

## 주의

- 모든 파일 상단에 `MODEL = "gemma3:4b"` 상수를 두었습니다.
  실습실 모델이 다르면 **이 한 줄만** 고치면 됩니다.
- `with_structured_output()` 뒤에 `| StrOutputParser()` 를 **붙이지 마십시오.**
  객체가 다시 문자열로 뭉개집니다.
- 오늘 만든 체인은 **반드시 커밋**하세요. 6주차 과제 2의 입력물입니다.
- **(추가)** `.env` 는 **절대 커밋 금지**입니다. 토큰이 공개 저장소에 올라가면
  봇이 자동으로 찾아내고, 슬랙도 감지 즉시 토큰을 무효화합니다.
  노출했다면 숨기지 말고 **Regenerate** 하는 것이 정답입니다.
- **(추가)** 슬랙 에러의 대부분은 코드 문제가 아니라 **설정 4단계 중 하나를 건너뛴 문제**입니다.
  `send_slack_message.py` 의 `HINTS` 표가 에러 코드별 해결을 바로 찍어 줍니다.

## 오늘의 한 줄

> **부탁은 확률이고, 스키마는 계약이다.**
>
> 직렬(`|`) · 병렬(`batch()`) — 그리고 **순환은 LCEL로 안 됩니다** → 12주차 LangGraph
