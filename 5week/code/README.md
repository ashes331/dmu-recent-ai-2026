# 5주차 실습 코드 — 프롬프트 심화와 LCEL

2026년 10월 2일 (금) / 최신인공지능 5주차
※ 진도 맞바꿈 적용 — 10/2에 **5주차 진도**, 10/7(수) 보강일에 6주차 진도

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| **확인 A** ★ | 1교시 1-5 | [`ask_json.py`](ask_json.py) | "JSON으로 답해줘" 를 10회 실행 — 형식이 흔들리는 장면 |
| — | 1교시 1-3 | [`few_shot.py`](few_shot.py) | Few-shot — 예시를 문자열이 아닌 **데이터(리스트)** 로 |
| — | 2교시 1절 | [`placeholder_partial.py`](placeholder_partial.py) | `MessagesPlaceholder` · `partial()` |
| **실습 1** ★ | 2교시 3절 | [`structured.py`](structured.py) | **`with_structured_output()` + Pydantic** |
| **실습 2** ★★ | 2교시 4절 | [`ab_failrate.py`](ab_failrate.py) | **파싱 실패율 A/B 20회 측정** |
| — | 3교시 1절 | [`runnable_basics.py`](runnable_basics.py) | LCEL · `RunnableLambda` / `assign` / `RunnableParallel` |
| **실습 3** ★★ | 3교시 2절 | [`least_to_most.py`](least_to_most.py) | **Least-to-Most 분해 체인 (직렬)** |
| **실습 4** ★ | 3교시 3절 | [`self_consistency.py`](self_consistency.py) | **Self-Consistency — `batch()` 다수결 (병렬)** |
| 기록 | — | [`RESULTS.md`](RESULTS.md) | 실습 2·4의 **측정 결과 기록표** |

> 학생 저장소에서는 `week05/` 경로에 두게 합니다.
> **`least_to_most.py` 가 6주차 [과제 2]("5주차 체인에 LangSmith 추적 적용")의 대상**입니다.

## 사전 준비

```bash
# 4주차까지 쓰던 가상환경을 그대로 사용합니다
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt

ollama list          # gemma3:4b 가 보여야 함
# 없으면: ollama pull gemma3:4b
```

새로 설치할 것은 사실상 없습니다 — `pydantic` 은 `langchain-core` 의존성으로 이미 들어와 있습니다.

## 실행 순서 (수업 진행 순서)

```bash
# 1교시
python ask_json.py             # 확인 A — 부탁의 실패 장면  ★
python few_shot.py             # 1-3절 (시간 여유가 있을 때)

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
```

## 온도(temperature) 설정 — 목적에 따라 반대로 잡습니다 ★

| 파일 | 온도 | 이유 |
|---|---:|---|
| `ask_json.py` | 0.7 | 형식이 **흔들려야** 실패 장면이 보인다 |
| `structured.py` | 0 | 구조화 출력은 **낮게** |
| `ab_failrate.py` | 0.7 | **A·B에 동일 적용** — 한쪽만 0이면 실험이 성립 안 함 ⚠️ |
| `least_to_most.py` | 0 | 분해·풀이는 낮게 |
| `self_consistency.py` | 0.8 | **0이면 N번 돌려도 같은 답** → 다수결이 무의미 ⚠️ |

## 수업 전 사전 테스트 (교수용) 🔶

- [ ] **`ask_json.py`** — 10~20회 돌려 **실패가 실제로 섞여 나오는지** 확인
      너무 잘 나오면 필드를 늘리거나(4~5개) 리뷰를 애매하게 만든다
- [ ] **`structured.py`** — ★ **이 교시 최대의 위험 지점**
      `with_structured_output()` 이 실습실 PC에서 동작하는지 반드시 확인.
      안 되면 `method="json_schema"` 를 시도하고, 그래도 안 되면 **OpenAI로 대체**
      (`langchain-openai` 주석 해제 + `llm = ChatOpenAI(...)` 한 줄 교체)
- [ ] **`ab_failrate.py`** — 20회 × 2 소요 시간 측정. 느리면 `N=10` 으로 배포
- [ ] **`self_consistency.py`** — `QUESTIONS` 후보 3개를 각각 5회씩 돌려
      **표가 갈리는 문제**를 골라 `QUESTION` 에 지정. 만장일치면 이 절이 밋밋해진다 ★
- [ ] `max_concurrency=2` 로 실습실 30명 동시 실행이 견디는지 확인

## 주의

- 모든 파일 상단에 `MODEL = "gemma3:4b"` 상수를 두었습니다.
  실습실 모델이 다르면 **이 한 줄만** 고치면 됩니다.
- `with_structured_output()` 뒤에 `| StrOutputParser()` 를 **붙이지 마십시오.**
  객체가 다시 문자열로 뭉개집니다.
- 오늘 만든 체인은 **반드시 커밋**하게 하십시오. 6주차 과제 2의 입력물입니다.

## 오늘의 한 줄

> **부탁은 확률이고, 스키마는 계약이다.**
>
> 직렬(`|`) · 병렬(`batch()`) — 그리고 **순환은 LCEL로 안 됩니다** → 12주차 LangGraph
