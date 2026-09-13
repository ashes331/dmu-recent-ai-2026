# 12주차 실습 코드 — LangGraph (1) State · Node · Edge / 분기와 순환

**2026년 11월 20일 (금)** / 최신인공지능 12주차

> **"체인은 파이프이고, 그래프는 회로도입니다."**
> 파이프는 갈라지고 되돌아오게 만들 수 없습니다. 회로도는 됩니다. ★★

수업 계획서: [12week/plane/전체플렌.md](../plane/전체플렌.md)

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| 시연 | 2교시 1-3 | [`reducer_demo.py`](reducer_demo.py) | ★★ **리듀서** — 덮어쓰기 vs 누적 (LLM 호출 없음 · 무료) |
| **실습 1** | 2교시 2절 | [`first_graph.py`](first_graph.py) | **첫 그래프** — State → Node 2개 → `compile()` → `invoke()` |
| **실습 2** ★★ | 2교시 3절 | [`branch_graph.py`](branch_graph.py) | **조건부 엣지로 분기** (질문 분류 → 경로별 처리) |
| **실습 3** ★★ | 3교시 2절 | [`reflection.py`](reflection.py) | **Reflection 루프** — 생성 → 자기 평가 → 재작성 (종료 조건 포함) |
| **실습 4** | 3교시 3절 | [`visualize.py`](visualize.py) | 그래프 시각화 + 실행 경로 확인 |
| 견본 | — | [`.env.example`](.env.example) | ★ **순환 안전장치 2개**가 새로 추가됩니다 |

> 학생 저장소에서는 `week12/` 경로에 두게 합니다.
> 📌 **과제 5 = 실습 2의 확장.** 그리고 **미니 프로젝트의 골격**으로 쓰게 하십시오. ★

## ⚠️ 실습 3 시작 전에 반드시 먼저 설명하십시오 ★★

```
   종료 조건 없는 루프가 30명 PC 에서 동시에 돌면 실습실 전체가 느려집니다.

     반복 1회 = LLM 호출 2회 (생성 + 평가)
     반복 3회 = 6회 호출  × 30명 = 180회   ⚠️ 실습실 GPU 부하

   종료 조건은 **두 겹**으로 겁니다.
     ① 논리적 종료   attempts >= N 이면 END        ← 우리가 설계 ★
     ② 안전망        recursion_limit               ← 프레임워크의 강제 차단

   ⚠️ ②만 믿으면 안 됩니다. 그건 **에러를 내며 멈추는** 장치입니다.
      **정상 종료는 ①로 설계해야** 합니다.
```

기본값은 `.env` 에서 조정합니다 — `WEEK12_MAX_ATTEMPTS=3` / `WEEK12_RECURSION_LIMIT=10`.

## 사전 준비

```bash
venv\Scripts\Activate.ps1          # Windows

pip install -r requirements.txt     # ★ langgraph · grandalf 가 새로 추가됩니다

cp .env.example .env                # Windows: copy .env.example .env
```

## 실행 순서 (수업 진행 순서)

```bash
# ── 수업 전날 (교수) 🔶 ─────────────────────────────────────
python reflection.py           # ★★ 1회차가 '부실하게' 나오는지 — 안 그러면 루프가 무의미
python branch_graph.py         # ★  세 입력이 실제로 다른 경로를 타는지
python visualize.py            #    ASCII/Mermaid 중 무엇이 되는지 확인 🔶

# ── 2교시 : State · Node · Edge
python reducer_demo.py         # 1-3절 시연 ★★ — LLM 없음 · 즉시 · 무료
python first_graph.py          # 실습 1
python branch_graph.py         # 실습 2 ★★

# ── 3교시 : 순환과 Reflection
python reflection.py           # 실습 3 ★★ — 종료 조건을 먼저 설명하고 시작
python visualize.py            # 실습 4 — 되돌아가는 화살표가 보인다 ★
python visualize.py branch     #   분기 그래프도 그려 보기
python visualize.py reflection --png   # 🔶 PNG 는 안 되면 넘어갑니다
```

## ★ 강의안 코드에서 고친 곳 (실제로 돌려 보고 확인)

**① `draw_ascii()` 는 "의존성이 가볍지" 않습니다** ★★

```python
# 강의안 (3교시 3-1)
# ASCII — 의존성이 가장 가볍다 ★
print(graph.get_graph().draw_ascii())
    → ⚠️ ImportError: Install grandalf to draw graphs: `pip install grandalf`

# 실제로 추가 설치 없이 되는 것은 이쪽입니다
print(graph.get_graph().draw_mermaid())      # ✅ 순수 파이썬
```

`requirements.txt` 에 `grandalf` 를 넣어 두었고, `visualize.py` 는
**ASCII 를 먼저 시도하고 실패하면 Mermaid 로 넘어갑니다.**

> 📌 **과제 5의 "시각화 이미지" 는 ASCII 캡처나 Mermaid 텍스트도 인정**한다고
> 반드시 명시하십시오. 여기서 막혀 제출을 못 하는 학생이 나옵니다. ★

**② 라우팅 함수에 기본 경로(fallback)를 넣었습니다** ★

강의안 3-3 절이 *"넣는 것이 안전합니다"* 라고 **권고만** 하는 것을 코드에 반영했습니다.

```python
def route(state) -> str:
    return state["category"] if state["category"] in ROUTES else "chat"
```

소형 모델이 라우팅 딕셔너리에 없는 값을 내면 **그래프가 그 자리에서 죽습니다.**
30명 실습에서는 반드시 누군가에게 일어납니다.

**③ 구조화 출력 실패를 루프가 흡수하도록 했습니다**

`with_structured_output()` 은 소형 모델에서 예외를 던지기도 합니다.
`branch_graph.py` 는 기본 경로로, `reflection.py` 는 "통과 처리 후 종료" 로 받습니다.
**실습이 예외 하나로 멈추지 않게** 하기 위한 것이며, 화면에 ⚠️ 로 표시됩니다. ★

**④ LLM 호출 수를 세어 화면에 찍습니다**

3교시 2-3 절의 *"호출 수 누계"* 표를 학생이 직접 채우려면 숫자가 보여야 합니다.
`reflection.py` 가 회차마다 누계를 출력합니다 — **"비용은 선형 증가" 를 숫자로.** ⚖️

## ⚠️ 안 될 때의 점검 순서 — 미리 판서해 두십시오

| 증상 | 원인 | 조치 |
|---|---|---|
| `draw_ascii` 에서 ImportError 🔶★ | grandalf 미설치 | `pip install grandalf` / **Mermaid 로 대체** |
| PNG 렌더링 실패 🔶 | 외부 의존성 | ASCII·Mermaid 로 충분합니다 ★ |
| **대화 이력이 매번 지워짐** ⚠️★★ | **리듀서 누락** | `Annotated[list, add_messages]` — `reducer_demo.py` 로 확인 |
| `GraphRecursionError` | 종료 조건 부재 | ① `attempts` 상한을 먼저 설계 ② `recursion_limit` 은 안전망 |
| 루프가 1회에 끝남 ⚠️★ | 평가 노드가 너무 관대 | `REQUIREMENT` 를 더 까다롭게 |
| 루프가 계속 "보완" | 평가 노드가 너무 엄격 | 요구사항을 완화 / `MAX_ATTEMPTS` 로 종료 |
| 라우팅에서 KeyError | 모델이 엉뚱한 값 반환 | `Literal` + fallback (코드에 적용됨) ★ |
| 상태 갱신에서 오류 | 노드가 **State 에 없는 키**를 반환 | 반환 키는 전부 State 에 선언되어야 합니다 ★ |
| 한글이 `UnicodeEncodeError` | 콘솔 코드페이지(cp949) | `chcp 65001` 또는 `set PYTHONUTF8=1` |

## 수업 전 사전 테스트 (교수용) 🔶

- [ ] ★★ **`reflection.py`** — **1회차 답변이 눈에 띄게 부실한지**
      처음부터 잘 나오면 루프가 1회에 끝나 **실습의 의미가 사라집니다**
      (요구사항을 *"정확히 3문장"*, *"구체적 예시 포함"* 처럼 까다롭게 걸면 잘 갈립니다)
- [ ] ★ **`branch_graph.py`** — 세 입력이 **실제로 다른 경로**를 타는지
- [ ] ★ **`reducer_demo.py`** — 리듀서를 뺐을 때 이력이 사라지는 장면 (시연 필수)
- [ ] 🔶 `visualize.py` — 실습실 PC 에서 ASCII / Mermaid / PNG 중 무엇이 되는지 확정
- [ ] ★ 과제 4(RAG 평가) 결과를 **미리 취합해 요약 슬라이드** — 1교시 15분용
      (즉석에서 물어보면 15분이 흩어집니다. **결론이 갈리는 학생 3~4명을 미리 지목**)
- [ ] 과제 5 안내 자료 (**시각화는 ASCII·Mermaid 도 인정** 명시 ★)
- [ ] AI 뉴스 발표자 확인 및 타이머 준비

## 📌 과제 5

```
  ① 조건 분기를 포함한 그래프 코드
       · State 스키마 (TypedDict, ★ 리듀서 포함)
       · Node 3개 이상 (분류 노드 + 경로별 처리 노드)
       · 조건부 엣지로 최소 2개 경로 분기
  ② 그래프 시각화 이미지 (★ ASCII 캡처·Mermaid 텍스트도 인정)
  ③ 서로 다른 경로를 타는 입력 2개 이상의 실행 결과
  ④ LangSmith 추적 캡처 (실행 경로가 보일 것) ★
```

| 채점 포인트 | 확인 |
|---|---|
| 조건에 따라 **실제로 다른 노드**로 가는가 | 실행 결과 2개로 확인 |
| 상태가 노드 간에 **올바르게 전달·갱신**되는가 | **리듀서 선택이 적절한가** ★ |
| **종료 조건**이 있는가 | 순환을 넣었다면 필수 ★★ |

> ⚠️ **캡처 필수** — 보존 14일. (6·9·11주차와 동일 원칙)

> ★ **이 그래프는 미니 프로젝트의 골격이 됩니다.**
> ⚠️ 별도로 만들면 남은 2주에 완주가 어렵습니다.
> **13주차 중간 점검에서 "과제 5를 프로젝트 골격으로 쓰고 있는가" 를 확인합니다.** ★

## 기말고사에 나올 만한 지점

- ★★ **LCEL 체인으로 표현할 수 없는 제어 흐름**(순환·조건 분기·재시도)과 **그 이유**
- 세 한계의 공통 원인 — **상태 부재 · 단방향 연결**
- **State / Node / Edge** 의 역할과 `StateGraph` → `compile()` → `invoke()` 흐름 ★
- ★★ **`TypedDict` 상태 스키마와 리듀서(`add_messages`)** — 덮어쓰기 vs 누적
- **조건부 엣지의 동작 방식** — 라우팅 함수가 무엇을 반환하는가
- 노드가 **전체 상태가 아니라 갱신할 키만** 반환한다는 점
- 분기·순환이 없을 때 **체인이 더 나은 이유**
- **순환 구조와 `recursion_limit`** — 종료 조건이 없으면 생기는 문제 ★
- ★★ **Reflection** — 생성→평가→재작성 루프, **반복 횟수와 품질·비용의 관계**
- ★★ **Self-Consistency(병렬)와 Reflection(순환)의 구조적 차이**
- 자기 평가가 **같은 모델일 때의 한계**
- 그래프 실행 경로를 LangSmith 에서 확인하는 방법

## 오늘의 한 줄

> **기법은 실행 구조를 요구한다.**
>
> 다수결은 **병렬**이 없으면 못 하고, Reflection 은 **순환**이 없으면 못 한다. ★★
