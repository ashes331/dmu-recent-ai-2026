"""[1교시 / 1-6] 확인 C ★★ — 프롬프트 기법 4종, 쓸 때와 안 쓸 때

같은 모델 · 같은 온도로 **A(기법 없음) / B(기법 적용)** 를 나란히 돌려 차이를 눈으로 본다.

    ① Zero-shot          그냥 물어보기        vs  할 일과 답 후보를 지정하기
    ② Few-shot           예시 없이            vs  예시 3개를 대화로 보여주고
    ③ CoT                "답만 말해"          vs  "단계별로 생각해 보자"
    ④ Self-Consistency   CoT 1회만 보기       vs  CoT N회 + 다수결

⚠️ A·B에 **같은 temperature** 를 씁니다. 한쪽만 0으로 두면 실험이 성립하지 않습니다.
   (2교시 ab_failrate.py 와 같은 원칙)

출처 — 예시 문장과 문제는 Prompt Engineering Guide 한국어판에서 가져왔습니다.
    Zero-shot          https://www.promptingguide.ai/kr/techniques/zeroshot
    Few-shot           https://www.promptingguide.ai/kr/techniques/fewshot
    CoT                https://www.promptingguide.ai/kr/techniques/cot
    Self-Consistency   https://www.promptingguide.ai/kr/techniques/consistency

⚠️ 매 실행 결과가 달라집니다 — 온도가 0이 아니므로 정상입니다.
   자료의 숫자와 똑같이 나오지 않아도 됩니다. **경향(A < B)이 같은지**만 보십시오.

실행:
    python technique_ab.py            # 네 가지 전부 (LLM 호출 약 27회)
    python technique_ab.py cot        # 하나만 — zero / few / cot / self
    python technique_ab.py cot 9      # 반복 횟수를 9회로
"""

import re
import sys
from collections import Counter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_ollama import ChatOllama

MODEL = "gemma3:4b"
TEMP = 0.7  # ⚠️ A·B에 동일 적용 — 한쪽만 0이면 비교가 성립하지 않는다
N = 5  # 반복 횟수 (②③④에서 사용)
MAX_CONCURRENCY = 2  # ⚠️ 8GB VRAM 보호 — 2~3으로 제한

llm = ChatOllama(model=MODEL, temperature=TEMP)
parser = StrOutputParser()


# ══════════════════════════════════════════════════════════════════
# 출력 도우미
# ══════════════════════════════════════════════════════════════════
def title(text: str) -> None:
    print()
    print("━" * 74)
    print(f"  {text}")
    print("━" * 74)


def arm(tag: str, text: str) -> None:
    """A / B 한쪽의 실행 결과를 들여쓰기해 보여준다."""
    print(f"\n  [{tag}]")
    for line in text.strip().splitlines() or [""]:
        print(f"      {line}")


def run(prompt: ChatPromptTemplate, variables: dict) -> str:
    return (prompt | llm | parser).invoke(variables).strip()


def run_many(prompt: ChatPromptTemplate, variables: dict, n: int) -> list[str]:
    """같은 입력을 n번 — batch() 한 줄이 곧 반복 실행이다 ★"""
    chain = prompt | llm | parser
    outs = chain.batch([variables] * n, config={"max_concurrency": MAX_CONCURRENCY})
    return [o.strip() for o in outs]


def last_int(text: str) -> int | None:
    """문장에서 마지막에 나오는 정수를 뽑는다 (자동 채점용)."""
    nums = re.findall(r"-?\d+", text.replace(",", ""))
    return int(nums[-1]) if nums else None


def verdict(text: str) -> str | None:
    """참/거짓 중 마지막에 나온 것을 뽑는다."""
    found = re.findall(r"거짓|참|False|True", text)
    if not found:
        return None
    last = found[-1]
    return "거짓" if last in ("거짓", "False") else "참"


def rate(hits: int, total: int) -> str:
    return f"{hits}/{total} ({hits / total * 100:.0f}%)"


# ══════════════════════════════════════════════════════════════════
# ① Zero-shot — 그냥 물어보기 vs 할 일과 답 후보를 지정하기
# ══════════════════════════════════════════════════════════════════
SENTENCE = "휴가는 괜찮을 것 같아요."
LABELS = ("긍정", "부정", "중립")


def demo_zero_shot() -> dict:
    title("① Zero-shot — 할 일과 '답 후보'를 지정하면 달라진다")
    print("  같은 문장을 두 가지 방식으로 물어봅니다 —", SENTENCE)

    # A) 기법 없음 — 그냥 말을 건다
    a_prompt = ChatPromptTemplate.from_messages([("human", "{sentence}\n이 문장 어때?")])
    a_out = run(a_prompt, {"sentence": SENTENCE})

    # B) Zero-shot — 할 일 + 답 후보(레이블 공간)를 지정한다 ★
    #    가이드 원문 프롬프트를 그대로 옮긴 형태
    b_prompt = ChatPromptTemplate.from_messages(
        [("human", "텍스트를 중립, 부정 또는 긍정으로 분류합니다.\n\n텍스트: {sentence}\n감정:")]
    )
    b_out = run(b_prompt, {"sentence": SENTENCE})

    arm("A · 기법 없음 — 그냥 물어보기", a_out)
    arm("B · Zero-shot — 할 일과 답 후보 지정 ★", b_out)

    print()
    print(f"  글자 수      A {len(a_out):>4}자   →   B {len(b_out):>4}자")
    print(f"  레이블만인가 A {'예' if a_out in LABELS else '아니오':<4}   →   B {'예' if b_out in LABELS else '아니오'}")
    print()
    print("  ★ 모델을 바꾼 것이 아닙니다. '무엇을 할지'와 '답 후보'를 적어 준 것뿐입니다.")
    return {"기법": "① Zero-shot", "A": f"{len(a_out)}자", "B": f"{len(b_out)}자", "본 것": "출력 길이·형식"}


# ══════════════════════════════════════════════════════════════════
# ② Few-shot — 예시가 '형식'을 잡아 준다
# ══════════════════════════════════════════════════════════════════
# ★ 레이블을 P / N / U 로 둔 것이 요령이다.
#   말로 설명하면 장황해지는 '답의 모양'을, 예시 세 줄로 대신 가르친다.
EXAMPLES = [
    {"text": "배송이 빨라서 좋았어요", "label": "P"},
    {"text": "화면에 흠집이 있네요", "label": "N"},
    {"text": "가격은 적당합니다", "label": "U"},
]
CODES = ("P", "N", "U")
TARGET = "포장이 엉망이었어요"
SYSTEM = "문장의 감정을 분류하세요."  # ⚠️ 답 후보를 말로 알려 주지 않는다 — 예시로만 전달


def demo_few_shot(n: int) -> dict:
    title("② Few-shot — 말로 설명하기 어려운 '답의 모양'을 예시로 가르친다")
    print(f"  같은 문장을 {n}번씩 — 「{TARGET}」")
    print("  A·B의 지시문은 «문장의 감정을 분류하세요.» 로 똑같습니다.")
    print("  차이는 하나 — B에만 P / N / U 예시 세 줄이 붙어 있습니다.")

    a_prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", "{text}")])

    example_prompt = ChatPromptTemplate.from_messages([("human", "{text}"), ("ai", "{label}")])
    few_shot = FewShotChatMessagePromptTemplate(examples=EXAMPLES, example_prompt=example_prompt)
    b_prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), few_shot, ("human", "{text}")])

    a_outs = run_many(a_prompt, {"text": TARGET}, n)
    b_outs = run_many(b_prompt, {"text": TARGET}, n)

    a_ok = sum(o in CODES for o in a_outs)
    b_ok = sum(o in CODES for o in b_outs)

    arm("A · 예시 없음", "\n".join(f"{i + 1}회 │ {' '.join(o.split())[:56]}…" for i, o in enumerate(a_outs)))
    arm("B · 예시 3개 ★", "\n".join(f"{i + 1}회 │ {o}" for i, o in enumerate(b_outs)))

    print()
    print(f"  P/N/U 한 글자로만 답한 횟수   A {rate(a_ok, n)}   →   B {rate(b_ok, n)}")
    print()
    print("  ★ A 는 감정을 '틀리게' 읽은 것이 아닙니다. 부정이라는 것은 맞혔습니다.")
    print("    다만 **어떤 모양으로 답해야 하는지**를 몰랐을 뿐입니다.")
    print("    가이드도 «레이블 공간과 형식이 중요하다»(Min et al. 2022)고 말합니다.")
    return {"기법": "② Few-shot", "A": rate(a_ok, n), "B": rate(b_ok, n), "본 것": "형식이 지켜진 비율"}


# ══════════════════════════════════════════════════════════════════
# ③ CoT — "단계별로 생각해 보자" 한 줄
# ══════════════════════════════════════════════════════════════════
# 가이드 원문 예시: 홀수를 모두 더하면 15+5+13+7+1 = 41 → 홀수이므로 명제는 거짓
COT_CLAIM = "집합 {15, 32, 5, 13, 82, 7, 1}에서 홀수를 모두 더하면 짝수야."
COT_ANSWER = "거짓"


def demo_cot(n: int) -> dict:
    title("③ CoT — '단계별로 생각해 보자' 한 줄을 붙였을 때")
    print(f"  명제: {COT_CLAIM}")
    print(f"  정답: {COT_ANSWER} (홀수의 합 15+5+13+7+1 = 41 — 홀수입니다)")

    a_prompt = ChatPromptTemplate.from_messages(
        [("human", "{claim}\n참인가 거짓인가? 설명하지 말고 한 단어로만 답하라.")]
    )
    # ★ Zero-shot CoT (Kojima et al. 2022) — 예시 없이 한 줄만 덧붙인다
    b_prompt = ChatPromptTemplate.from_messages(
        [("human", "{claim}\n단계별로 생각해 보자. 마지막 줄에는 '참' 또는 '거짓'만 써라.")]
    )

    a_outs = run_many(a_prompt, {"claim": COT_CLAIM}, n)
    b_outs = run_many(b_prompt, {"claim": COT_CLAIM}, n)

    a_ok = sum(verdict(o) == COT_ANSWER for o in a_outs)
    b_ok = sum(verdict(o) == COT_ANSWER for o in b_outs)

    arm("A · 답만 요구", "\n".join(f"{i + 1}회 │ {verdict(o) or '?':<3} │ {o[:40]}" for i, o in enumerate(a_outs)))
    arm(
        "B · 단계별로 생각해 보자 ★",
        "\n".join(f"{i + 1}회 │ {verdict(o) or '?':<3} │ {' '.join(o.split())[:60]}…" for i, o in enumerate(b_outs)),
    )

    print()
    print(f"  정답({COT_ANSWER}) 횟수   A {rate(a_ok, n)}   →   B {rate(b_ok, n)}")
    print()
    print("  ★ 모델도 프롬프트도 같습니다. 덧붙인 것은 «단계별로 생각해 보자» 한 줄입니다.")
    return {"기법": "③ CoT", "A": rate(a_ok, n), "B": rate(b_ok, n), "본 것": "정답률"}


# ══════════════════════════════════════════════════════════════════
# ④ Self-Consistency — CoT 를 여러 번 시켜 다수결
# ══════════════════════════════════════════════════════════════════
# ⚠️ 답이 갈려야 의미가 있습니다. 가이드 원문 예시(나이 문제, 답 67)는 gemma3:4b 가
#    5회 모두 맞혀 표가 갈리지 않았습니다. 그래서 3교시 self_consistency.py
#    와 같은 일률 문제를 씁니다. 여기서도 만장일치가 나오면 문제를 바꿔 보십시오.
SC_QUESTION = (
    "어떤 일을 혼자 하면 갑은 6시간, 을은 12시간이 걸린다. "
    "둘이 함께 2시간 일한 뒤 을이 빠지면, 갑이 혼자 마무리하는 데 몇 시간이 더 걸리는가?"
)
SC_ANSWER = 3


def demo_self_consistency(n: int) -> dict:
    title("④ Self-Consistency — CoT 를 한 번만 보면 위험하다")
    print(f"  문제: {SC_QUESTION}")
    print(f"  정답: {SC_ANSWER}시간 (함께 1시간에 1/6+1/12=1/4 → 2시간에 절반, 남은 절반을 갑이 3시간)")

    prompt = ChatPromptTemplate.from_messages(
        [("human", "{question}\n단계별로 생각해 보자. 마지막 줄에는 숫자만 써라.")]
    )
    outs = run_many(prompt, {"question": SC_QUESTION}, n)
    answers = [last_int(o) for o in outs]

    arm(
        f"CoT {n}회 — 같은 프롬프트, 같은 온도",
        "\n".join(f"{i + 1}회 │ 답 {a}" + ("  ✅" if a == SC_ANSWER else "  ❌") for i, a in enumerate(answers)),
    )

    hits = sum(a == SC_ANSWER for a in answers)
    votes = Counter(a for a in answers if a is not None)
    winner, count = votes.most_common(1)[0]

    print()
    print(f"  A · 한 번만 돌렸다면      → 정답일 확률 {rate(hits, n)}   (뽑힌 1회차는 {answers[0]})")
    print(f"  B · {n}회 다수결 ★         → {winner}  {'✅' if winner == SC_ANSWER else '❌'}   (표 {dict(votes)} — {count}표)")
    print()
    if len(votes) == 1:
        print("  ※ 이번에는 만장일치였습니다. 온도를 올리거나 더 어려운 문제로 바꿔 보십시오")
    else:
        print("  ★ 한 번만 돌리고 «이 모델은 못 푼다»고 결론 내렸을 수도 있는 장면입니다.")
        print("    개별 실행은 흔들려도, 여러 번의 다수결은 안정적입니다.")
    print("    ⚠️ temperature=0 이면 N번 돌려도 같은 답 → 다수결이 무의미합니다.")
    return {
        "기법": "④ Self-Consistency",
        "A": rate(hits, n),
        "B": f"다수결 {winner}",
        "본 것": "개별 정답률 vs 다수결",
    }


# ══════════════════════════════════════════════════════════════════
DEMOS = {
    "zero": demo_zero_shot,
    "few": demo_few_shot,
    "cot": demo_cot,
    "self": demo_self_consistency,
}


def main() -> None:
    args = [a for a in sys.argv[1:]]
    only = args[0] if args and args[0] in DEMOS else None
    n = next((int(a) for a in args if a.isdigit()), N)

    print(f"모델 {MODEL} · temperature {TEMP} (A·B 동일) · 반복 {n}회")

    rows = []
    for key, fn in DEMOS.items():
        if only and key != only:
            continue
        rows.append(fn() if key == "zero" else fn(n))

    title("정리 — 기법을 쓰면 무엇이 달라졌나")
    print(f"  {'기법':<20} {'A · 기법 없음':<16} {'B · 기법 적용':<16} 무엇을 본 것인가")
    print("  " + "─" * 70)
    for r in rows:
        print(f"  {r['기법']:<20} {r['A']:<16} {r['B']:<16} {r['본 것']}")
    print()
    print("  ★ 네 가지 모두 모델을 바꾸지 않았습니다. 바꾼 것은 '어떻게 물어보는가' 뿐입니다.")
    print("    그리고 이 넷은 각각 오늘·2교시·3교시의 코드 구조로 이어집니다 (4장 대응표).")


if __name__ == "__main__":
    main()
