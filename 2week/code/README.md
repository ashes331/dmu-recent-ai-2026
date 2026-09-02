# 2주차 실습 코드

「최신인공지능」 2026 — 2주차 *LangChain 생태계 조망과 임베딩·벡터 표현*

수업 계획서: [2week/plane/전체플렌.md](../plane/전체플렌.md)

---

## 실습 목록

| 실습 | 교시 | 파일 | 실행 환경 | 실행 기록 |
|------|------|------|----------|----------|
| **1** ★ | 2교시 1-1 | `fail_01_hallucination.py` | 로컬 Ollama | [실행결과](실행결과_fail_01_hallucination.md) |
| | 2교시 1-2 | `fail_02_no_memory.py` | 로컬 Ollama | [실행결과](실행결과_fail_02_no_memory.md) |
| | 2교시 1-3 | `fail_03_no_tools.py` | 로컬 Ollama | [실행결과](실행결과_fail_03_no_tools.md) |
| **2** | 3교시 2 | `embed_01_similarity.py` | Colab | |
| **3** ★ | 3교시 3 | `embed_02_search_compare.py` | Colab | |
| **4** | 3교시 4 | `embed_03_heatmap.py` | Colab | |

> 실습 1의 **실패 ④(관측 불가)** 는 코드가 아니라 상황으로 설명합니다.
> 자료: [2교시_단일_호출의_한계와_LangChain_생태계.md](../plane/2교시_단일_호출의_한계와_LangChain_생태계.md) 1-4절

> 📌 **모델 표기** — 슬라이드의 실측 결과는 자료 제작 PC 사정으로 `gemma3:1b`, 학생 배포 코드와 아래 명령은 `gemma3:4b` 입니다.
> 자세한 내용은 [실행결과_fail_01 · 모델 방침](실행결과_fail_01_hallucination.md#-모델-방침-확정)에 있습니다.

### 보조 파일

| 파일 | 용도 |
|------|------|
| `00_check_env.py` | 수업 전 실습실 PC 점검 (Ollama·모델·패키지) |
| `embed_local_ollama.py` | **Colab이 막힐 때의 대비책** — 실습 2·3을 로컬 Ollama 임베딩으로 |
| `2week_colab.ipynb` | 실습 2·3·4를 한 번에 돌리는 Colab 노트북 |
| `requirements.txt` | 패키지 목록 |

### 보완자료 코드 (정규 실습 아님)

미이수자 보완 자료의 실습 코드는 [보완자료/](보완자료/) 에 따로 있습니다.
1주차에 신청한 학생에게만 배포합니다. → [보완자료/README.md](보완자료/README.md)

| 자료 | 파일 |
|------|------|
| 보완A (LLM 작동원리) | `token_demo.py` · `token_compare.py` · `next_token.py` · `next_token_ko.py` · `temperature_demo.py` |
| 보완B (Attention·Transformer) | `attention_viz.py` |

---

## 1. 실습 1 — 로컬 Ollama (2교시)

**의도적으로 LangChain을 쓰지 않습니다.** 선행 과목에서 쓰던 `ollama` 패키지 그대로입니다.
"맨손으로 해보니 안 되더라"를 먼저 겪은 뒤, 3주차부터 도구를 쥐어주는 순서입니다.

```powershell
# 준비 (한 번만)
ollama serve            # 이미 떠 있으면 생략
ollama pull gemma3:4b
pip install ollama

# 실행
python fail_01_hallucination.py     # ① 모르는 것을 지어낸다
python fail_02_no_memory.py         # ② 어제 한 얘기를 기억 못 한다
python fail_03_no_tools.py          # ③ 바깥 세상을 모른다
```

모델을 바꾸려면 환경변수 `OLLAMA_MODEL` 을 씁니다.

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"
python fail_01_hallucination.py
```

---

## 2. 실습 2·3·4 — Colab (3교시)

`2week_colab.ipynb` 를 Colab에 업로드하거나, 새 노트북에 각 `.py` 내용을 붙여 넣습니다.
첫 셀에서 임베딩 모델(`snunlp/KR-SBERT-V40K-klueNLI-augSTS`, 768차원)을 1회 다운로드합니다.

```python
!pip install -q sentence-transformers
```

로컬에서 돌리려면:

```powershell
pip install -r requirements.txt
python embed_01_similarity.py
python embed_02_search_compare.py
python embed_03_heatmap.py
```

> ⚠️ 로컬 PC에 PyTorch를 설치하는 것은 **10주차 계획**입니다.
> 2주차는 개념 확인이 목적이므로 Colab을 기본으로 합니다.

---

## 3. Colab이 막힐 때 (대비책) — ⚠️ 한계 있음

접속은 되지만 **로그인·런타임 연결·pip 설치**에서 막힐 수 있습니다.

```powershell
ollama pull nomic-embed-text
python embed_local_ollama.py        # matplotlib 없이 표로 출력
```

**다만 이 대비책은 강의안의 결론을 재현하지 못합니다.** `nomic-embed-text` 는 영어 중심
모델이라 한국어에서 유사도 순위가 뒤집힙니다 (2026-08-21 실측).

```
질문 vs 졸업요건  0.73   <   질문 vs 학식메뉴  0.83      ← 역전
실습 3의 1위도 오답(문서1), 실습 4의 블록 구조도 없음
```

`embed_local_ollama.py` 는 실행 첫머리에서 이를 **자동 진단해 경고**합니다.

```
Colab이 막혔을 때
  1순위) 미리 캡처해 둔 Colab 실행 결과를 띄운다              ← 권장
  2순위) 로컬 결과를 그대로 보여주되, "한국어 지원이 모델 선택
         기준인 이유"의 실패 사례로 전환해 설명한다
```

---

## 4. 수업 전 점검

```powershell
python 00_check_env.py
```

Ollama 서버·모델·패키지 설치 상태를 한 번에 확인하고, 빠진 것에 대한 조치를 알려줍니다.

---

## 5. 임베딩 모델을 바꾼 이유

강의안 초안의 `paraphrase-multilingual-MiniLM-L12-v2` (다국어 384차원)는 **한국어 성능이
떨어져 ★핵심 실습 3에서 오답을 1위로 올립니다.** 한국어 전용 모델로 교체했습니다.

| 모델 | 실습3 1위 | 실습2 격차 | 실습4 블록 |
|------|----------|-----------|-----------|
| `paraphrase-multilingual-MiniLM-L12-v2` | ❌ 문서4 캡스톤 | 0.37 vs 0.29 | 흐림 |
| `nomic-embed-text` (Ollama) | ❌ 문서1 | 0.73 **<** 0.83 역전 | 없음 |
| **`snunlp/KR-SBERT-V40K-klueNLI-augSTS`** | ✅ 문서0 | 0.49 vs 0.30 | 선명 |

> 📄 **근거(원문 출력)**: [실행결과_embed_모델비교.md](실행결과_embed_모델비교.md) — 두 모델의 실습 2·3·4 실행 결과
> 전문과 재현 스크립트. (2026-08-21 실측 / 2026-08-30 재현 확인)

모델을 바꾸려면 각 `embed_*.py` 상단의 `MODEL_NAME` 한 줄만 고치면 됩니다.

> 📌 이 교체 자체가 3교시 1-4절 **"한국어 지원이 모델 선택 기준인 이유"** 의 실제 사례입니다.
> 강의안에도 반영해 두었습니다.

---

## 파일별 관찰 포인트 요약

| 파일 | 학생이 확인할 것 |
|------|----------------|
| `fail_01` | 모른다고 하지 않고 **자신 있게 지어낸다**. 두 번 실행하면 답이 달라진다 |
| `fail_02` | 2차 호출에서 이름을 모른다 → `ollama.chat()` 은 **매 호출이 독립적**.<br>[B]에서 이력을 직접 쌓아 보내면 기억하는 것처럼 보인다 |
| `fail_03` | 날씨를 날짜까지 붙여 지어내고, 큰 수 곱셈은 틀린다 → **바깥과 연결되어 있지 않다** |
| `embed_01` | shape가 항상 `(N, 768)`. 졸업요건(0.49) > 학식(0.30) |
| `embed_02` | 키워드 검색은 정답·오답이 **1개씩 동점**이라 순위를 못 매김.<br>의미 검색은 정답을 **1위**로 올린다 |
| `embed_03` | 대각선 1.00, 주제별 **블록 구조**가 보인다 (블록 안 0.57~0.76 vs 사이 0.18~0.35) |

> 위 수치는 전부 2026-08-21 실제 실행으로 확인한 값입니다.
