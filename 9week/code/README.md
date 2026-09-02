# 9주차 실습 코드 — 중간고사 해설 / 도구 호출(Tool Calling)과 외부 연동

**2026년 10월 30일 (금)** / 최신인공지능 9주차
⚠️ **상용 API 배정 1순위 차시** — 8B급 로컬 모델은 도구 선택 실패율이 높습니다.

> **"모델은 도구를 '실행'하지 않습니다. '요청'할 뿐입니다. 실행은 우리 코드가 합니다."** ★★

수업 계획서: [9week/plane/전체플렌.md](../plane/전체플렌.md)

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| 사전 | — | [`tool_support_check.py`](tool_support_check.py) | 🔶 **교수용 · 전날 필수** — 이 모델이 도구 호출을 지원하는가 ★★ |
| **실습 1** ★★ | 2교시 2절 | [`tool_flow.py`](tool_flow.py) | **도구 정의 + 호출 흐름 완성** (`tool_calls` → 실행 → `ToolMessage`) |
| **실습 2** ★ | 2교시 3절 | [`search_agent.py`](search_agent.py) | **검색 도구 + 모델별 도구 선택 정확도 비교** |
| 대비책 | 2교시 3절 | [`fake_search.py`](fake_search.py) | 🔶 **레이트리밋 최후 대비** — 고정 결과 반환 |
| **실습 3** | 3교시 2절 | [`guarded_tools.py`](guarded_tools.py) | **주입 방어 적용** (검증 · 권한 최소화 · 사람 승인) |
| 시연 | 3교시 1-4 | [`indirect_injection.py`](indirect_injection.py) | ★★ **간접 주입** — 가져온 텍스트가 지시가 되는 장면 |
| 견본 | — | [`.env.example`](.env.example) | `TOOL_MODEL` 이 **새로 추가**됩니다 ★ |

> 학생 저장소에서는 `week09/` 경로에 두게 합니다.
> ★ **여기서 만든 도구를 13주차 실습 1에서 그대로 재사용합니다.** 잘 남겨 두게 하십시오.

## 사전 준비

```bash
# 7주차까지 쓰던 가상환경을 그대로 사용합니다
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt     # ★ langchain-community + 검색 백엔드가 새로 추가됩니다

cp .env.example .env                # Windows: copy .env.example .env
# ★ TOOL_MODEL 을 반드시 채우십시오 (아래 참조)

git check-ignore -v .env            # ★ 출력이 나와야 안전합니다
```

## 실행 순서 (수업 진행 순서)

```bash
# ── 수업 전날 (교수) ★★ 이 차시 최대의 위험 지점 ─────────────
python tool_support_check.py   # 🔶 도구 호출 지원 모델 확정 → .env 의 TOOL_MODEL
python search_agent.py --names #    검색 도구의 '실제 이름' 확인 (검색 호출 없음)
python indirect_injection.py   #    모델이 실제로 속는지 미리 확인 ★

# ── 2교시 : 도구 정의와 호출 흐름 ★★ 이 교시가 9주차의 핵심
python tool_flow.py            # 실습 1 ★★ — content 가 비어 있는 장면을 반드시 짚을 것
python search_agent.py --names # 실습 2 도입 — 학생이 직접 실행 (무료·즉시) ★
python search_agent.py         # 실습 2 ★ — ⚠️ 조별 순차 실행

# ── 3교시 : 주입 방어
python guarded_tools.py            # 실습 3 — 입력 검증·승인 (LLM 없음 · 즉시) ★
python guarded_tools.py --agent    #   ★ 학생이 직접 공격을 시도해 본다
python indirect_injection.py       # 시연 — 방어 없음 ⚠️
python indirect_injection.py --defend  # 시연 — 방어 켬 ★
```

## ⚠️ 이 차시 최대의 위험 지점 — 도구 호출 지원 모델

```
   모든 모델이 도구 호출을 지원하지는 않습니다.
   지원하지 않는 모델에 bind_tools() 를 하면
       · tool_calls 가 늘 비어 있거나        ← 오류가 안 나서 더 헷갈립니다 ⚠️
       · 오류가 납니다
   → 실습 1(20분)이 통째로 성립하지 않습니다.
```

| 대비 | 어디에 |
|---|---|
| 전날 확인 스크립트 | `python tool_support_check.py` — 실제로 1회 실행해 확정 ★ |
| 실행 중 안내 | `tool_flow.py` 가 `tool_calls` 가 비면 원인 두 가지를 안내합니다 |
| 최후 수단 | 본 차시는 **상용 API 배정 1순위**입니다. 로컬이 안 되면 상용으로 진행 |

## ⚠️ 두 번째 위험 지점 — DuckDuckGo 레이트리밋 ★

**강의실 전체가 같은 공인 IP를 씁니다. 접속 가능 ≠ 30명 동시 호출 가능.**

```
[운영] 조별 순차 실행                      ← 기본. 수업 전에 조 편성을 끝내 둘 것 ★
   · 3~4개 조, 조별 3~4분 시차
   · 대기 조는 그동안 description 개선 작업을 먼저 수행
   · 코드에 재시도 간격이 들어 있습니다 (.env 의 WEEK09_SEARCH_DELAY, 기본 3초)

[예비] 🔶 다른 검색 도구 키를 사전 발급해 둘 것 (LangChain 인터페이스는 동일)

[최후] .env 에  WEEK09_SEARCH=fake   → fake_search.py 로 즉시 대체
   · 도구 호출 흐름 학습에는 지장이 없습니다 — 검색 품질이 목적이 아니므로
```

## ⚠️ 안 될 때의 점검 순서 — 미리 판서해 두십시오

| 증상 | 원인 | 조치 |
|---|---|---|
| `tool_calls` 가 항상 빈 리스트 ⚠️★ | 모델이 도구 호출 미지원 🔶 | `python tool_support_check.py` → `.env` 의 `TOOL_MODEL` |
| `bind_tools` 에서 오류 | 위와 동일 | 위와 동일 |
| 검색에서 **Ratelimit / 202** ⚠️ | 동시 호출 차단 | 조별 순차 실행 / `WEEK09_SEARCH=fake` |
| 검색 도구 import 실패 | 백엔드 패키지명 변경 🔶 | `pip install ddgs` (구버전은 `duckduckgo-search`) |
| 기대값이 **전부 불일치** ⚠️★ | 도구의 **실제 이름**을 안 씀 | `python search_agent.py --names` 로 먼저 확인 |
| `.env` 를 고쳤는데 안 바뀜 ★ | 셸에 기존 환경변수가 남음 | **터미널을 새로 열고** 재실행 |
| `ToolMessage` 생성 방식 오류 🔶 | 버전 차이 | `tool_obj.invoke(call)` 형태 확인 (전날 1회 실행) |
| 한글이 `UnicodeEncodeError` | 콘솔 코드페이지(cp949) | `chcp 65001` 또는 `set PYTHONUTF8=1` 후 재실행 |

## 수업 전 사전 테스트 (교수용) 🔶

- [ ] ★★ **`tool_support_check.py`** — **최우선**. 통과 모델을 `.env` 에 확정해 배포
- [ ] ★ **`search_agent.py --names`** — 검색 도구의 실제 `name` 을 확인해 슬라이드에 반영
- [ ] ★ **DuckDuckGo 실제 검색 동작 확인** — 외부망은 개방 확인됨(2026-08-19)이나
      ⚠️ **레이트리밋은 별개 문제로 그대로 남아 있습니다**
- [ ] ★ **조별 순차 실행 계획 수립** — 조 편성과 실행 순서를 수업 전에 확정
- [ ] 🔶 예비 검색 도구 키 사전 발급 / `WEEK09_SEARCH=fake` 동작 확인
- [ ] ★ **도구 선택 실패 사례 캡처** — 소형 모델이 엉뚱한 도구를 고르는 장면
- [ ] ★ **`indirect_injection.py`** — 모델이 실제로 속는지 확인
      (안 속으면 `POISONED_PAGE` 문장을 더 강하게. **속는 장면이 있어야 3교시 1-4가 완성됩니다**)
- [ ] `guarded_tools.py --agent` — 경로 이탈 공격이 실제로 차단되는지
- [ ] 중간고사 채점 완료 + **문항별 정답률 집계** → 해설 25분 우선순위 결정 ★
- [ ] MCP 개요 슬라이드 (개념 수준 — 구현은 다루지 않음)
- [ ] AI 뉴스 발표자 확인 및 타이머 준비

## ★ 강의안 코드에서 고친 곳 (실제로 돌려 보고 확인)

**① 경로 검증을 문자열 비교 → 경로 비교로** ★

```python
# 강의안 (3교시 2절)
if not str(target).startswith(str(ALLOWED_DIR)):
    → ⚠️ "./workspace-backup" 같은 '접두사 우연 일치' 를 통과시킵니다.
      workspace 밖인데 문자열로는 workspace 로 시작하기 때문입니다.

# 이 폴더의 코드 (guarded_tools.py)
if ALLOWED_DIR not in target.parents and target != ALLOWED_DIR:
    → 경로 관계로 판정하므로 접두사 우연 일치가 통하지 않습니다. ★
```

> 📌 **수업에서 그대로 써먹을 수 있는 장면입니다.**
> *"방어 코드에도 버그가 있습니다."* 7주차 *"평가자도 검증 대상"* 과 같은 구조입니다. ★

**② 검색 도구의 이름을 코드가 직접 읽게 함**

강의안에도 이미 `SEARCH = search.name` 으로 되어 있지만, `--names` 옵션을 두어
**검색 호출 없이(=무료로) 먼저 확인**할 수 있게 했습니다. 실습 도입부 2분에 씁니다.

**③ 방어 실패도 정상 흐름으로 처리**

`guarded_tools.py --agent` 에서 검증에 걸리면 예외로 죽지 않고
`ToolMessage(content="거부됨: ...")` 로 모델에게 되돌립니다.
**차단은 에러가 아니라 정상 흐름입니다** — 13주차 HITL 의 `reject` 와 같은 원칙입니다. ★

## 📌 과제 3

| # | 제출물 |
|---|---|
| ① | **커스텀 도구 2개 이상** (`@tool`, description 포함) |
| ② | **도구 호출 체인 코드** — 질문 → 선택 → 실행 → 최종 답변까지 동작 |
| ③ | ★ **LangSmith 추적 캡처** — `tool_calls` 와 `ToolMessage` 가 보일 것 |

**채점 포인트**

```
  · 도구 2개 이상이 실제로 선택·실행되는가
  · description 이 "언제 쓰는 도구인지" 를 명확히 설명하는가   ★
  · 추적에서 도구 선택 과정이 확인되는가
  · (가점) 위험한 도구에 방어 장치를 넣었는가                 ★
```

⚠️ **캡처 필수** — LangSmith 무료 플랜 보존기간은 **14일**입니다.
링크만 제출하면 채점 시점에 열리지 않습니다. (6주차 과제 2와 동일 원칙)

## 기말고사에 나올 만한 지점 (9~14주차 범위 / 12/11)

- `@tool` 데코레이터와 `bind_tools()` 의 역할
- ★ **도구 호출의 전체 흐름** — 모델은 *실행*하지 않고 *요청*한다 / `ToolMessage` 로 결과 반환
- ★ **도구 설명문(description) 작성이 중요한 이유**
- 소형 모델의 도구 선택 실패 원인과 **대응 2가지** (도구 수 제한 · 설명문 개선)
- 도구를 쓰지 말아야 할 질문에 도구를 쓰는 것도 **실패**인 이유
- ★★ **도구를 쥔 모델에서 프롬프트 주입이 실제 피해로 이어지는 경로**
- **방어 수단 4가지**: 구분자 / 입력 검증 / 권한 최소화 / 사람 승인
- ★ **간접 주입(Indirect Injection)** — 검색 결과·웹 문서가 공격 통로가 되는 이유
- 구분자만으로는 부족한 이유
- **MCP가 표준화하려는 것** (개념 수준)

## 오늘의 한 줄

> **모델은 도구를 실행하지 않는다. 요청할 뿐이다. 실행은 우리 코드가 한다.**
>
> 그래서 — **우리가 막을 수 있고, 우리가 안 막으면 아무도 안 막는다.** ★★
