# 13주차 실습 코드 — LangGraph (2) ReAct 에이전트 · 메모리 · HITL · Agentic RAG

**2026년 11월 27일 (금)** / 최신인공지능 13주차
★ **상용 API 배정 2순위 차시** — 순환 판단이 반복되어 소형 모델은 무한 루프·조기 종료가 잦습니다.

> **"모델이 속아도, 사람이 승인하지 않으면 실행되지 않습니다."** ★★
> HITL 은 친절한 UX 기능이 아니라 **프롬프트 주입에 대한 실질적 방어 수단**입니다.

수업 계획서: [13week/plane/전체플렌.md](../plane/전체플렌.md)

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| **실습 1** ★★ | 1교시 2절 | [`react_agent.py`](react_agent.py) | **ToolNode 에이전트** (9주차 도구 재사용) / `--broken` 리듀서 누락 시연 |
| **실습 2** | 2교시 2절 | [`memory_agent.py`](memory_agent.py) | **체크포인터 + `thread_id`** — 다른 thread 는 기억이 없다 ★ |
| **실습 3** ★★ | 2교시 4절 | [`hitl_agent.py`](hitl_agent.py) | **`interrupt` 승인 흐름** / `--injection` 주입 시나리오 |
| — | 3교시 1절 | [`time_travel.py`](time_travel.py) | 상태 되감기 — 비결정적 앱의 **재현 수단** ★ |
| **실습 4** ★★ | 3교시 2절 | [`agentic_rag.py`](agentic_rag.py) | **검색 여부를 스스로 판단** + 실패 시 재작성·재검색 |
| 견본 | — | [`.env.example`](.env.example) | `TOOL_MODEL`(9주차와 동일) + `WEEK13_INDEX` |

> 학생 저장소에서는 `week13/` 경로에 두게 합니다.

## ⚠️ 도입부 확인 — 두 가지가 있어야 오늘이 굴러갑니다 ★

```
   ① 9주차 도구 코드      → 실습 1 (없어도 이 폴더 코드로 진행 가능)
   ② 10주차 RAG 인덱스     → 실습 4 ⚠️ 없으면 실습 4를 못 합니다
                             (🔶 교수 배포본 준비)
```

```bash
python agentic_rag.py    # 인덱스가 없으면 무엇을 해야 하는지 알려주고 종료합니다
```

## 사전 준비

```bash
.venv\Scripts\activate              # Windows
pip install -r requirements.txt     # ★ 12주차와 거의 같습니다
cp .env.example .env                # Windows: copy .env.example .env
# ★ TOOL_MODEL 은 9주차에서 확정한 값을 그대로 쓰십시오
```

## 실행 순서 (수업 진행 순서)

```bash
# ── 수업 전날 (교수) 🔶 이 차시 최대의 위험 지점 ─────────────
python hitl_agent.py --auto approve   # ★★ interrupt / Command API 확정
python hitl_agent.py --auto reject    #    거부 경로도 정상 종료되는지
python agentic_rag.py                 # ★★ 세 질문이 다른 경로를 타는지
python react_agent.py --broken        #    무한 루프 시연이 실제로 되는지

# ── 1교시 : ReAct
python react_agent.py                 # 실습 1 ★★
python react_agent.py --broken        #   ⚠️ 리듀서를 빼면? — 반드시 시켜 볼 것 ★★

# ── 2교시 : 메모리와 사람의 개입
python memory_agent.py                # 실습 2 — chat-A / chat-B 를 비교 ★
python hitl_agent.py                  # 실습 3 ★★ — approve / reject 를 둘 다
python hitl_agent.py --injection      #   ★★ 9주차 간접 주입 시나리오 재현

# ── 3교시 : 되감기와 Agentic RAG
python time_travel.py                 # 1절 — 체크포인트 목록 + 되감아 재실행 ★
python agentic_rag.py                 # 실습 4 ★★
```

## ⚠️ 이 차시 최대의 위험 지점 — `interrupt` / `Command` API ★★

```
   LangGraph 에서 **변화가 특히 큰 영역**입니다.
     · 임포트 경로            langgraph.types 인가, 다른 곳인가
     · interrupt 의 반환 형태
     · Command(resume=...) 의 사용법
     · state.tasks[].interrupts 의 구조

   여기서 막히면 2교시 15분 실습이 통째로 멈춥니다.
```

| 대비 | 조치 |
|---|---|
| 전날 1회 실행 | `python hitl_agent.py --auto approve` ★ |
| 대안 방식 | `compile(interrupt_before=["tools"])` — 노드 진입 **전** 정지 🔶 |
| 최후 | 9주차 `guarded_tools.py` 의 `input()` 방식으로 개념만 설명 |

> ⚠️ `interrupt_before` 는 도구 함수를 안 고쳐도 되지만 **어느 도구든 무조건 멈춥니다.**
> → 4-3절의 **승인 피로**를 그대로 만듭니다. 대비책으로만 쓰십시오.

## ★ 강의안 코드에서 고친 곳 (실제로 돌려 보고 확인)

**① 실습 2·3이 1교시 코드를 실제로 import 합니다** ★

강의안은 `# ... (1교시 react_agent.py 의 builder 정의 재사용)` 이라고
**주석으로만** 되어 있어 그대로는 실행되지 않습니다.

```python
# react_agent.py
def build_agent(tools=None, state_cls=State, model=None):
    ...
    return builder            # ★ 재사용 가능한 형태로 노출

# memory_agent.py
from react_agent import builder
graph = builder.compile(checkpointer=MemorySaver())

# hitl_agent.py
from react_agent import build_agent
graph = build_agent(TOOLS).compile(checkpointer=MemorySaver())   # 도구만 교체
```

**② 리듀서 누락 시연을 `--broken` 한 줄로** ★★

강의안 2-2 절이 *"리듀서를 일부러 빼면?"* 을 **말로만** 설명합니다.
`react_agent.py --broken` 이 실제로 그 State 로 돌리고,
`GraphRecursionError` 를 잡아 **왜 그랬는지**까지 설명합니다.

> ⚠️ 다만 **매번 루프에 빠지지는 않습니다**(모델·온도에 따라 갈립니다).
> 그때도 `messages` 가 쌓이지 않는 것은 출력에서 확인됩니다.
> **"갈린다" 는 사실 자체가 요점입니다** — 방어를 확률에 맡길 수 없습니다. ★

**③ `interrupt` 앞의 부작용 원칙을 코드로 지켰습니다** ★★

`delete_file()` 의 `interrupt` **앞에는 부작용이 하나도 없습니다.**
검증도, 로그도, 파일 접근도 없습니다. 실제 실행은 전부 `interrupt` **뒤**에 있습니다.

```
   ⚠️ 재개하면 그 노드가 "처음부터" 다시 실행됩니다.
      interrupt 앞에 log_to_db() 가 있으면 **두 번 기록됩니다.**
```

수업에서 **학생에게 이 코드가 원칙을 지키고 있는지 직접 확인시키십시오.** ✅

**④ 구조화 출력 실패를 '안전한 쪽' 으로 흡수**

`agentic_rag.py` 의 판단 노드가 실패하면 **검색하는 쪽**으로 보냅니다.
(못 하는 것보다 낭비하는 편이 낫습니다.)
평가 노드가 실패하면 그대로 답변으로 넘깁니다. 화면에 ⚠️ 로 표시됩니다.

**⑤ 되감기 지점을 코드가 골라 줍니다**

강의안의 `list(graph.get_state_history(config))[2]` 는 **인덱스가 우연히 맞아야**
동작합니다. `time_travel.py` 는 `next` 가 비어 있지 않은(=아직 실행할 노드가 남은)
체크포인트만 추려 그중 하나를 고릅니다. 🔶

## ⚠️ 안 될 때의 점검 순서 — 미리 판서해 두십시오

| 증상 | 원인 | 조치 |
|---|---|---|
| `tool_calls` 가 늘 비어 있음 ⚠️★ | 도구 호출 미지원 모델 🔶 | 9주차 `tool_support_check.py` → `.env` 의 `TOOL_MODEL` |
| **무한 루프** ⚠️★★ | **리듀서 누락** / 종료 조건 부재 | `Annotated[list, add_messages]` · `recursion_limit` |
| **조기 종료** (결과를 받고 답을 안 함) | 시스템 프롬프트 부족 | `SYSTEM` 의 두 문장을 확인 ★ |
| 도구를 아예 안 씀 | 도구가 많음 / description 부실 | 도구 2~3개, "언제 쓰는지" 를 명시 (9주차) |
| `interrupt` 임포트 실패 🔶 | 버전 차이 | 전날 확인 / `interrupt_before` 대안 |
| **재개 후 부작용이 두 번** ⚠️★★ | `interrupt` **앞**에 부작용 | 실행 코드를 `interrupt` **뒤**로 |
| `thread_id` 없이 실행 시 오류 | 체크포인터만 있음 | `config={"configurable": {"thread_id": ...}}` ★ |
| 재시작하니 대화가 없음 | `MemorySaver` 는 프로세스 메모리 | 정상입니다. 영속 저장소가 필요하면 🔶 |
| 실습 4에서 인덱스 없음 ⚠️ | 10주차 산출물 미커밋 | 배포본 사용 / 10주차 `embed.py` 재실행 |
| 세 질문이 같은 경로 ⚠️★ | 판단 노드가 흔들림 | 프롬프트 조정 / 상용 모델(배정 2순위) |
| 한글이 `UnicodeEncodeError` | 콘솔 코드페이지(cp949) | `chcp 65001` 또는 `set PYTHONUTF8=1` |

## 수업 전 사전 테스트 (교수용) 🔶

- [ ] ★★ **`hitl_agent.py --auto approve` / `--auto reject`** — **최우선**.
      `interrupt` / `Command` API 를 실제로 확정해 배포 코드에 반영
- [ ] ★★ **`hitl_agent.py --injection`** — 모델이 속아 승인 요청이 뜨는지
      (여기가 **학습목표 11(보안)의 완성 지점**입니다)
- [ ] ★★ **`agentic_rag.py`** — 세 질문이 **실제로 다른 경로**를 타는지
      특히 세 번째("학교 좀 쉬고 싶은데")가 **rewrite → search 순환**을 도는지
- [ ] ★ **`react_agent.py --broken`** — 무한 루프 시연이 되는지
- [ ] ★ **10주차 인덱스 배포본** — 실습 4를 못 하는 학생 대비
- [ ] `time_travel.py` — `get_state_history` API 형태 확인 🔶
- [ ] ★ **미니 프로젝트 중간 점검 체크리스트를 사전 제출받아 훑을 것**
      (10분에 전원 상담은 불가능합니다. **위험군만 지목**해 7분 상담)
- [ ] AI 뉴스 발표자 확인 및 타이머 준비

## 미니 프로젝트 중간 점검 (3교시 4절) ★

| 확인 항목 | 위험 신호 ⚠️ |
|---|---|
| **진행률** | 10주차 명세 대비 **절반 미만** |
| **필수 요건** | **LangSmith 추적**이 안 붙어 있다 ★ (감점이 아니라 **요건 미충족**) |
| **하드웨어** | 8GB 에서 **아직 안 돌려봤다** ⚠️ (설계만 한 팀) |
| **골격 재사용** | **과제 5 그래프와 별개로** 새로 만들고 있다 ★ |
| 잔여 범위 | 남은 1주에 **끝날 수 없는 분량** |

> ★★ **"과제 5를 프로젝트 골격으로 쓰고 있는가" 를 반드시 확인하십시오.**
> 별도로 만들고 있다면 **지금 합치게** 하십시오. 남은 1주에 두 개는 못 끝냅니다.

| 상황 | 조치 |
|---|---|
| 진행률 낮음 | **범위를 줄이십시오.** 기능 하나를 확실히 > 기능 셋을 미완성 ★ |
| 8GB 초과 설계 | 모델을 **소형으로 교체** (4주차 비교표 근거) |
| LangSmith 미적용 | **오늘 안에** `.env` 3줄 추가 — 10분이면 됩니다 |
| 아무것도 못 함 | **10주차 실습 산출물 + 오늘 그래프**를 합쳐 최소 형태로 완성 |

> ⚠️ **다음 주 최종 제출.** LangSmith 추적 캡처 필수 — 보존 **14일**.
> **링크만 제출하면 채점 시점에 소멸되어 0점 처리될 수 있습니다.** ★★
> **제출 직전에 캡처**하게 하십시오.

## 기말고사에 나올 만한 지점

- ★★ **ReAct 패턴** — 모델 ↔ 도구 순환의 구조와 **종료 조건**
- `ToolNode` 의 역할, **9주차 수동 도구 호출과의 차이**
- 소형 모델에서 에이전트가 실패하는 양상과 대응 (무한 루프 / 미사용 / 조기 종료)
- ★ **리듀서가 없으면 에이전트가 무한 루프에 빠지는 이유**
- ★★ **체크포인터와 `thread_id`** — 대화 메모리가 유지되는 원리, 단기/장기 구분
- ★ **Human-in-the-Loop(`interrupt`)** — 실행을 멈추고 승인받는 흐름
- ★★ **HITL 이 프롬프트 주입에 대한 방어 수단인 이유** (9주차 연결)
- `interrupt` 가 **체크포인터를 필요로 하는 이유**
- **승인 피로**와 권한 최소화의 관계
- **상태 되감기(Time Travel)** 가 가능한 이유와 활용 / 추적과의 차이
- ★★ **Agentic RAG** — 검색 여부를 스스로 판단하는 구조, **항상 검색하는 RAG 와의 차이**
- **Tree of Thoughts** 의 구조(분기·평가·가지치기) — 그래프 관점의 설명
- ★ Self-Consistency / Reflection / ToT **세 기법의 구조적 차이**

## 오늘의 한 줄

> **모델이 속아도, 사람이 승인하지 않으면 실행되지 않는다.** ★★
>
> 9주차에 **설계만** 했던 방어 ④가 오늘 **코드**가 되었다.
