# 11주차 실습 코드 — RAG (2) 벡터 저장소 · 검색 전략 · Lost in the Middle

**2026년 11월 13일 (금)** / 최신인공지능 11주차
★ **RAG 에서 실무 비중이 가장 큰 차시입니다.**

> **"생성 모델을 더 좋은 것으로 바꾸는 것보다 검색을 개선하는 편이 효과가 큽니다."**
> — 이 말을 오늘 실험으로 확인합니다.

수업 계획서: [11week/plane/전체플렌.md](../plane/전체플렌.md)

## 파일 구성

| 실습 | 교시 | 파일 | 내용 |
|------|------|------|------|
| 공용 | — | [`rag_common.py`](rag_common.py) | ★ **10주차 인덱스를 이어 쓰는 잡일** (없으면 재생성) |
| 배포본 | 2교시 | [`questions.py`](questions.py) | ★ **통일 질문셋 10개** — LLM 호출 없음 · 무료 |
| **실습 1** | 1교시 2절 | [`rag_chain.py`](rag_chain.py) | **LCEL RAG 체인** + 검색 점수 + **메타데이터 필터** ★★ |
| **실습 2** ★★ | 2교시 2절 | [`retriever_strategies.py`](retriever_strategies.py) | **MMR · MultiQuery · 하이브리드** 3종 구현·비교 |
| — | 2교시 3절 | [`concepts_4.py`](concepts_4.py) | 개념 4종 + **7종 한눈에 표** (호출 없음) ★ |
| **실습 3** ★ | 3교시 2절 | [`lost_in_middle.py`](lost_in_middle.py) | **정답 문서의 위치·개수 실험** |
| **실습 4** | 3교시 4절 | [`citation.py`](citation.py) | **출처 표기** + 인용 번호 검증 / `--followup` 후속 질문 재작성 |
| 견본 | — | [`.env.example`](.env.example) | `WEEK11_INDEX` 로 10주차 인덱스 경로를 지정 ★ |

> 학생 저장소에서는 `week11/` 경로에 두게 합니다.

## ⚠️ 도입부 1~2분 — 10주차 인덱스 점검부터 하십시오 ★

```bash
python rag_common.py        # 인덱스가 있는가 / metadata 키가 심겨 있는가
```

**없는 학생이 많으면 배포본을 즉시 나눠 주고 시작해야 15분 실습이 성립합니다.**
없으면 코드가 그 자리에서 다시 만들어 주지만 **느립니다**(🔶 재적재).

`year` / `category` 가 안 심겨 있으면 **1교시 필터 검색을 만들 수 없습니다.**
10주차 2교시 3절의 *"지금 안 심으면 나중에 못 만듭니다"* 가 바로 이 장면입니다. ★★
**심어둔 학생과 안 심은 학생을 나란히 확인시키면 교훈이 확실히 남습니다.**

## 사전 준비

```bash
venv\Scripts\activate              # Windows

pip install -r requirements.txt     # ★ langchain-chroma · chromadb · rank_bm25 가 새로 추가

cp .env.example .env                # Windows: copy .env.example .env
python rag_common.py                # ★ 인덱스 점검
```

## 실행 순서 (수업 진행 순서)

```bash
# ── 수업 전날 (교수) 🔶 ─────────────────────────────────────
python rag_common.py                          # 인덱스·metadata 점검
python retriever_strategies.py                # ★★ 전략별로 결과가 갈리는지 ⏱
python lost_in_middle.py --repeat 3           # ★★ 위치에 따라 답이 갈리는지
python concepts_4.py --run parent             # 🔶 Parent Document 시연 준비

# ── 1교시 : 저장소와 RAG 체인
python rag_common.py                          # 도입부 점검 ★
python rag_chain.py                           # 실습 1 — retriever | prompt | llm | parser
python rag_chain.py --scores                  # 1-2절 검색 점수 ★
python rag_chain.py --filter                  # 1-3절 메타데이터 필터 ★★

# ── 2교시 : 검색 전략 ★★ 이 교시가 실무 비중 최대
python questions.py                           # 배포 질문셋 점검 — 무료 ★
python retriever_strategies.py --mmr          # λ 를 바꿔가며 ★
python retriever_strategies.py --multiquery   # ★★ 재작성된 질문을 반드시 보여줄 것
python retriever_strategies.py --hybrid       # weights 를 바꿔가며 ★
python retriever_strategies.py                # 전체 비교표 ⏱ 먼저 걸어 둘 것
python concepts_4.py                          # 개념 4종 + 7종 표 (무료) ★

# ── 3교시 : Lost in the Middle · 출처 표기
python lost_in_middle.py                      # 실습 3 ★
python citation.py --followup                 # 3절 후속 질문 재작성 ★
python citation.py                            # 실습 4 출처 표기 ★★
```

> ⏱ **`retriever_strategies.py`(전체)는 오래 걸립니다.** 질문 10개 × 전략 4종이고
> MultiQuery 는 질문마다 LLM 호출이 추가됩니다.
> **실행을 먼저 걸게 하고**, 도는 동안 3절(개념 4종)을 설명하십시오. ★

## ⚠️ 이 차시 최대의 위험 지점 — 결과가 갈리지 않는 것 ★★

```
   전략 4종의 결과가 전부 같다        → 2교시 25분 실습이 의미를 잃습니다
   위치를 바꿔도 답이 안 달라진다     → 3교시 17분 실습이 의미를 잃습니다
```

| 대비 | 조치 |
|---|---|
| 전략이 안 갈림 | 질문을 더 까다롭게 (구어체·조문번호), `K` 를 줄임 |
| 위치가 안 갈림 | 문서 수 10 → 15~20, **방해 문서를 더 그럴듯하게**(같은 규정집의 다른 조문) |
| 답이 매번 흔들림 | `--repeat 3` 으로 반복 측정 — **LLM 은 비결정적입니다**(6주차 1교시) ★ |

**수업 전날 반드시 확인하십시오.** 차이가 안 나면 그 절이 통째로 무의미해집니다.

## ⚠️ 안 될 때의 점검 순서 — 미리 판서해 두십시오

| 증상 | 원인 | 조치 |
|---|---|---|
| 인덱스를 못 찾음 | 10주차 산출물 미커밋 ★ | `python rag_common.py` (자동 재생성) / 배포본 사용 |
| `filter` 가 아무것도 안 걸러냄 ⚠️★ | `year` 를 안 심음 | **10주차의 회수 지점** — 그대로 짚고 넘어가십시오 ★★ |
| Chroma 에서 metadata 오류 🔶 | `None` 값을 거부함 | 코드가 걸러냅니다 / 10주차에서 키를 안 넣는 것이 원칙 |
| `EnsembleRetriever` import 실패 🔶 | 임포트 경로 이동 | 코드가 `langchain` → `langchain_community` 순으로 재시도 |
| BM25 가 아무것도 못 찾음 | 청크 목록이 비어 있음 | `python rag_common.py` 로 청크 수 확인 |
| MultiQuery 재작성이 안 보임 ★ | 로깅 미설정 | `--multiquery` 로 실행 (INFO 로깅이 켜집니다) |
| MultiQuery 가 매우 느림 ⏱ | 질문마다 LLM 추가 호출 | **정상입니다.** 그게 이 전략의 '대가' 입니다 ⚖️ |
| 점수가 **클수록** 유사해 보임 🔶 | 저장소마다 의미가 다름 | FAISS 기본은 **L2 거리 — 작을수록 가깝습니다** ★ |
| 한글이 `UnicodeEncodeError` | 콘솔 코드페이지(cp949) | `chcp 65001` 또는 `set PYTHONUTF8=1` |

## 수업 전 사전 테스트 (교수용) 🔶

- [ ] ★★ **`retriever_strategies.py`** — 전략별로 결과가 **실제로 갈리는지**
- [ ] ★★ **`lost_in_middle.py --repeat 3`** — 위치에 따라 답이 **실제로 갈리는지**
- [ ] ★ **`rag_chain.py --filter`** — 필터가 실제로 범위를 좁히는지
- [ ] ★ **완성 인덱스 배포본** — 10주차 산출물을 못 살린 학생 대비
- [ ] ★ **통일 질문셋 확정** — `questions.py` 를 그대로 쓰거나 교수 문서에 맞게 교체
      ⚠️ 학생마다 질문이 다르면 2교시 비교 논의가 통째로 불가능합니다
- [ ] 🔶 **Re-ranking 시연 화면 확보** — 재정렬 전/후 순위가 **실제로 바뀌는** 캡처
      (1차 검색을 20건으로 넓게 잡으면 잘 갈립니다 ★)
      ⚠️ **학생 PC 에는 설치하지 않습니다** — 8GB 초과 위험
- [ ] `concepts_4.py --run parent` — Parent Document 시연 동작 확인
- [ ] 과제 4 안내 자료 (3축 · 무료 한도 · **캡처 필수**)
- [ ] AI 뉴스 발표자 확인 및 타이머 준비

## ★ 강의안 코드에서 고친 곳 (실제로 돌려 보고 확인)

**① 10주차 인덱스가 없을 때를 코드가 처리합니다** ★

강의안은 `FAISS.load_local("week10/index_recursive", ...)` 로 시작합니다.
**인덱스를 못 살린 학생이 있으면 그 자리에서 실습이 멈춥니다.**

```
   rag_common.load_store()
     · 인덱스가 있으면       → 그대로 읽는다 (빠름)
     · 없으면               → 10주차 문서로 다시 만든다 (🔶 느리지만 진행은 됨)
     · 원본 문서도 없으면    → 무엇을 확인해야 하는지 알려주고 종료
```

> ⚠️ **그래도 10주차 인덱스는 반드시 커밋시키십시오.** 재적재는 도입부를 잡아먹습니다.

**② 하이브리드에 필요한 '청크 목록' 을 저장소에서 복구합니다**

강의안의 `BM25Retriever.from_documents(chunks)` 에서 `chunks` 는 10주차 변수입니다.
**11주차 파일에는 그 변수가 없습니다.** `rag_common.load_chunks()` 가
FAISS 의 docstore 에서 문서를 복구하고, 실패하면 원본을 다시 분할합니다. 🔶

**③ 인용 번호 검증을 코드로 넣었습니다** ★★

강의안 4-3 절은 *"모델이 없는 번호를 지어낼 수 있다 → 코드로 검증"* 이라고
**말만** 합니다. `citation.py` 의 `verify_citations()` 가 그것을 실제로 합니다.

```
  [검증] 본문이 쓴 인용 번호: [1, 7]   ← 이건 **모델이** 만듭니다
    ⚠️ 존재하지 않는 번호를 인용했습니다: [7]  ★ 코드로 잡아냈습니다
```

> 📌 **출처 목록은 코드가, 본문 번호는 모델이 만듭니다.**
> 5주차 *"형식은 강제해도 내용은 보장되지 않는다"* 가 여기서 또 나옵니다. ★★

**④ 질문셋에 "문서에 없는 내용" 을 넣었습니다**

`"장학금은 얼마나 받을 수 있나요?"` — 검색은 무언가를 가져옵니다.
그때 모델이 지어내는지, *"해당 내용을 찾을 수 없습니다"* 라고 하는지가
**환각 억제 프롬프트의 시험대**입니다. ★

## 📌 과제 4

```
  ① 검색 전략 3종 이상을 같은 질문셋에 적용
       · 실습 3종(MMR·MultiQuery·하이브리드) 중 2종 이상 — 필수
       · Compression · Parent Document · Self-Query 중 1종 이상 — 자유 선택
       · ⚠️ Re-ranking 은 교수 시연 대상이므로 제외

  ② LangSmith 데이터셋(10~20개)으로 3축 평가          ← 7주차 방식 그대로 ★
       · 정확성      — 답이 맞는가
       · 근거성      — 답이 가져온 문서에 실제로 근거하는가 (환각 여부) ★
       · 검색 적합성 — 가져온 문서가 질문과 관련 있는가

  ③ 결과표 + "어느 전략을 왜 고를지" 한 문단
```

| 주의 | 내용 |
|---|---|
| **무료 한도** | 질문 10개 × 전략 3종 = **30 traces**(+판정자) → 데이터셋 10~20개 유지 |
| ⚠️ **캡처 필수** | 보존 14일. **링크만 제출한 과제는 미제출로 간주** ★ |
| 공유 | ★ 평가 실행은 수업 후 → **12주차 도입부 15분에 결과 공유** |

> 📌 **학생마다 결론이 다르게 나오는 것이 정상**입니다. 그게 오늘의 메시지입니다 —
> ***"정답 전략은 없고, 내 데이터에서 재봐야 안다."*** ★

## 기말고사에 나올 만한 지점

- Vector Store 구축과 **메타데이터 필터 검색** ★
- **LCEL RAG 체인 구성**: `retriever | prompt | model | parser` / `RunnablePassthrough` 가 필요한 이유
- **기본 유사도 검색의 두 가지 한계** ★
- ★★ **검색 전략 7종이 각각 어떤 문제를 푸는가**
- **하이브리드 검색이 필요한 경우** (고유명사·코드·숫자)
- ★★ **Parent Document** 와 10주차 청크 크기 딜레마의 관계
- Self-Query 가 **메타데이터 설계를 전제**로 한다는 점
- MultiQuery·Compression·Re-ranking 의 **공통 대가** (추가 호출·지연)
- ★★ **Lost in the Middle** — 현상 · 원인 · 대응
- 후속 질문 재작성이 필요한 이유 (*"그건 언제까지야?"*)
- ★ **출처 표기(Citation)** 와 10주차 메타데이터 설계의 관계
- 인용 번호를 모델이 **지어낼 수 있다**는 점과 그 대응
- **RAG 평가 3축**: 정확성 / 근거성 / 검색 적합성

## 오늘의 한 줄

> **"검색이 정답을 가져왔다" 와 "모델이 그것을 봤다" 는 다른 이야기다.** ★★
>
> 그리고 — **정답 전략은 없다. 내 데이터에서 재봐야 안다.**
