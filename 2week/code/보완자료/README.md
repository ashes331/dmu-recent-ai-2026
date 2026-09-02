# 보완자료 실습 코드

**미이수자 보완 자료용**입니다. 2주차 정규 실습이 아닙니다.

선행 과목을 듣지 않은 학생에게 1주차에 신청받아 배포하는 자료의 코드입니다.
정규 실습 코드는 [상위 폴더](../)에 있습니다.

| 자료 | 배포 대상 |
|------|----------|
| [보완A_LLM작동원리.md](../../plane/보완자료/보완A_LLM작동원리.md) | 「빅데이터분석프로젝트」 6주차 미이수자 |
| [보완B_Attention과Transformer.md](../../plane/보완자료/보완B_Attention과Transformer.md) | 「딥러닝응용프로그래밍」 12주차 미이수자 |

---

## 보완A — LLM 작동 원리

| 절 | 파일 | 내용 | 환경 |
|----|------|------|------|
| 3-2 | `token_demo.py` | 토큰화하고 되돌리기 (무손실 확인) | 로컬 |
| 3-3 | `token_compare.py` | gpt-4 vs gpt-4o 토크나이저 비교 | 로컬 |
| 4-2 | `next_token.py` | **다음 토큰 확률 Top-5** ★★ | Colab |
| 4-3 | `next_token_ko.py` | 한국어 모델(KoGPT-2)로 확인 | Colab |
| 5-2 | `temperature_demo.py` | temperature별 생성 결과 비교 | Colab |

```powershell
# 로컬 (토큰 실습)
pip install tiktoken
python token_demo.py
python token_compare.py
```

## 보완B — Attention과 Transformer

| 절 | 파일 | 내용 | 환경 |
|----|------|------|------|
| 4-2~4-4 | `attention_viz.py` | GPT-2 Attention 히트맵 ★ | Colab |

셀 4(꺼내기) · 셀 5(`it`이 보는 곳) · 셀 6(히트맵)이 **한 파일에 순서대로** 들어 있습니다.
로컬에서는 그대로 실행하면 셋이 차례로 돕니다.

---

## Colab 실습 (`next_token*.py` · `temperature_demo.py` · `attention_viz.py`)

Colab에는 `torch`·`transformers`가 이미 설치되어 있습니다. 설치할 것이 없습니다.

> ⏱️ 첫 실행 시 GPT-2(약 500MB) 다운로드에 1~2분 걸립니다.

**로컬에서 돌리려면** — PyTorch가 필요합니다.

```powershell
pip install torch transformers matplotlib
```

> ⚠️ 2주차 방침상 **실습실 PC에는 PyTorch를 설치하지 않습니다.**
> 로컬 임베딩 모델 로딩은 10주차에 다룹니다. 보완자료는 Colab으로 진행하십시오.

---

## 셀 사이의 의존 관계

`temperature_demo.py`는 원래 Colab 셀 3으로, 셀 1(`next_token.py`)에서 만든 `tok`·`model`을
이어 씁니다. **단독 실행도 되도록 모델을 직접 불러오게 작성**했습니다.
Colab에서 셀 1을 이미 실행했다면 상단의 모델 로딩 세 줄은 건너뛰어도 됩니다.

`attention_viz.py`는 `attn_implementation="eager"`로 모델을 다시 불러옵니다.
이 옵션이 없으면 **attention 값이 `None`으로 나오므로** 셀 1의 모델을 재사용할 수 없습니다.
