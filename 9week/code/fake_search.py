"""[2교시 / 실습 2 대비책] 🔶 가짜 검색 도구 — 고정 결과를 돌려준다 ★

  ⚠️ 왜 이 파일이 있는가

     강의실 전체가 같은 공인 IP 를 씁니다.
     30명이 동시에 DuckDuckGo 를 때리면 레이트리밋으로 차단되고,
     18분짜리 실습이 통째로 멈춥니다.

     [운영] 조별 순차 실행 (3~4개 조, 조별 3~4분 시차)
     [예비] 🔶 다른 검색 도구로 교체 (교수 사전 발급)
     [최후] ★ 이 파일 — 고정 결과를 돌려주는 가짜 검색 도구

  ★ 도구 호출 흐름 학습이 목적이지 검색 품질이 목적이 아닙니다.
    가짜 도구로도 오늘 배울 것(선택 → 요청 → 실행 → ToolMessage → 답변)은
    전부 그대로 배울 수 있습니다.

  ⚠️ 다만 하나는 못 봅니다 — 3교시의 '간접 주입'입니다.
     그건 indirect_injection.py 가 따로 시연합니다. ★

사용:
    # search_agent.py 에서 .env 로 자동 전환됩니다
    #   .env :  WEEK09_SEARCH=fake

    # 단독 확인
    python fake_search.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.tools import tool

# 🔶 실습 2 의 QUESTIONS 에 맞춰 미리 준비해 둔 고정 결과.
#    질문을 바꾸면 여기도 함께 바꾸십시오.
CANNED = {
    "노벨": "2026년 노벨물리학상은 (예시) 양자 오차 정정 연구자 3인에게 수여되었다. "
            "— 출처: 예시 뉴스 (수업용 고정 응답)",
    "날씨": "서울 현재 기온 12도, 맑음. — 출처: 예시 기상 자료 (수업용 고정 응답)",
    "환율": "1달러 = 1,380원. — 출처: 예시 금융 자료 (수업용 고정 응답)",
}

DEFAULT = ("검색 결과를 찾지 못했습니다. (수업용 가짜 검색 도구입니다 — "
           "실제 웹 검색을 하지 않습니다)")


# ★ 이름과 독스트링을 진짜 검색 도구와 비슷하게 맞춰 두었습니다.
#   그래야 '모델이 도구를 고르는 판단'이 실제와 비슷하게 재현됩니다. ★
@tool
def web_search(query: str) -> str:
    """웹을 검색해 최신 정보를 찾는다. 실시간 정보나 최근 사건이 필요할 때 사용한다."""
    for key, answer in CANNED.items():
        if key in query:
            return answer
    return DEFAULT


if __name__ == "__main__":
    print("가짜 검색 도구 — 고정 결과만 돌려줍니다 (레이트리밋 최후 대비책) 🔶\n")
    print("도구 이름       :", web_search.name)
    print("도구 설명       :", web_search.description)
    print("인자 스키마     :", web_search.args)
    print()
    for q in ["2026년 노벨물리학상 수상자는?", "오늘 서울 날씨", "파이썬 리스트와 튜플의 차이"]:
        print(f"  검색({q!r})")
        print(f"    → {web_search.invoke({'query': q})[:70]}")
