"""[1교시 / 1-3] Few-shot — 예시는 지시문이 아니라 데이터다

작년 방식은 예시를 프롬프트 문자열 안에 직접 적어 넣었다.

    prompt = '''다음 문장의 감정을 분류하세요.

    문장: 배송이 빨라서 좋았어요   → 긍정
    문장: 화면에 흠집이 있네요     → 부정

    문장: {text} →'''

동작은 한다. 그런데 예시를 5개 → 20개로 늘리려면?

    예시 추가·삭제        프롬프트 본문을 매번 편집 — 오타·형식 깨짐
    예시만 교체           지시문까지 통째로 복사
    예시 개수 실험        3개/5개/10개 버전을 파일 3개로 관리
    예시를 DB·CSV에서     ❌ 불가능  ★

★ 오늘 방식: 예시를 리스트(데이터)로 분리한다.
  그러면 examples 를 CSV·DB에서 읽어와도 나머지 코드는 그대로다.

실행:
    python few_shot.py
"""

from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

# ── ① 예시는 데이터다 — CSV·DB에서 읽어와도 된다 ★ ──────────
EXAMPLES = [
    {"text": "배송이 빨라서 좋았어요", "label": "긍정"},
    {"text": "화면에 흠집이 있네요", "label": "부정"},
    {"text": "가격은 적당합니다", "label": "중립"},
]


def build_prompt(examples: list[dict]) -> ChatPromptTemplate:
    # ── ② 예시 하나를 어떤 모양의 '대화'로 펼칠지 정한다 ────
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{text}"),
            ("ai", "{label}"),
        ]
    )

    # ── ③ 둘을 합치면 Few-shot 블록이 된다 ──────────────────
    few_shot = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
    )

    return ChatPromptTemplate.from_messages(
        [
            ("system", "문장의 감정을 긍정/부정/중립 중 하나로만 답하세요."),
            few_shot,  # ← 예시 블록이 통째로 끼워진다 ★
            ("human", "{text}"),
        ]
    )


def main() -> None:
    prompt = build_prompt(EXAMPLES)

    messages = prompt.invoke({"text": "포장이 엉망이었어요"}).to_messages()

    print("── 모델에게 실제로 전달되는 메시지 ─────────────────")
    for m in messages:
        print(f"  {type(m).__name__:15s} {m.content}")
    print()

    # ★ 관찰 포인트
    #   예시가 ("human", ...) / ("ai", ...) 대화 쌍으로 들어간다.
    #   지시문 안의 텍스트가 아니라 "이미 이렇게 대화한 적이 있다" 는 형태다.
    #   채팅 모델에서는 이쪽이 대체로 더 잘 먹힌다.

    # ── ④ 예시 개수만 바꿔 실험한다 — 코드는 그대로 ★ ──────
    print("── 예시 개수를 바꿔도 코드는 그대로 ────────────────")
    for k in (1, 2, 3):
        n_msgs = len(build_prompt(EXAMPLES[:k]).invoke({"text": "..."}).to_messages())
        print(f"  예시 {k}개 → 전달 메시지 {n_msgs}개")
    print()
    print("  문자열에 박아 넣었다면 이 실험을 하려고 프롬프트를 3벌 만들어야 했다.")
    print()
    print("💡 입력에 따라 예시를 골라 넣는 것(SemanticSimilarityExampleSelector)도 가능하다.")
    print("   다만 임베딩 유사도(2주차) + 벡터 저장소(11주차)가 필요하다 → 11주차에 재료가 갖춰진다.")


if __name__ == "__main__":
    main()
