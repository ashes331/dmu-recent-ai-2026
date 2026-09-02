"""[수업 전 / 교수용] 실습실에서 LangSmith 로 나갈 수 있는지 1분 안에 확인한다.

✅ 외부망은 개방이 확인되었습니다 (2026-08-19).
   그래도 수업 당일 아침에 1회만 돌려 보십시오. 접속이 막히면
   1교시 실습 1이 통째로 무산됩니다.

이 파일은 키가 없어도 동작합니다 — 순수하게 '연결이 되는가' 만 봅니다.
표준 라이브러리만 씁니다 (설치 불필요).

실행:
    python net_check.py
"""

import socket
import ssl
import urllib.error
import urllib.request

TIMEOUT = 8  # 초

TARGETS = [
    ("LangSmith 웹",  "https://smith.langchain.com"),
    ("LangSmith API", "https://api.smith.langchain.com/info"),
    ("Ollama 로컬",   "http://localhost:11434/api/tags"),
]


def probe(url: str) -> str:
    """접속 결과를 사람이 읽는 한 줄로 돌려준다.

    401/403 도 '연결은 됐다' 는 뜻이므로 성공으로 셉니다. ★
    우리가 보려는 것은 인증이 아니라 '방화벽을 통과하는가' 입니다.
    """
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            return f"[O] HTTP {resp.status}  — 연결됨"
    except urllib.error.HTTPError as e:
        # 서버가 응답을 준 것 → 네트워크는 뚫려 있다
        return f"[O] HTTP {e.code}  — 연결됨 (인증/권한 응답이지 차단이 아님) ★"
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLError):
            return f"[X] SSL 오류 — 백신·사내 프록시가 가로채는 중일 수 있음 ({reason})"
        if isinstance(reason, socket.timeout):
            return f"[X] 시간 초과 ({TIMEOUT}초) — 방화벽 차단 의심"
        return f"[X] 연결 실패 — {reason}"
    except Exception as e:  # noqa: BLE001  수업용이므로 넓게 잡아 원인을 보여준다
        return f"[X] 예상 밖 오류 — {type(e).__name__}: {e}"


def main() -> None:
    print("=" * 64)
    print("  6주차 사전 점검 — LangSmith 접속 확인")
    print("=" * 64)

    for name, url in TARGETS:
        print(f"  {name:14s} {url}")
        print(f"  {'':14s} → {probe(url)}")
        print()

    print("-" * 64)
    print("""
읽는 법

  결과                          의미 / 조치
  ──────────────────────────────────────────────────────────────
  LangSmith 웹·API 둘 다 [O]    실습 진행 가능. 그대로 수업하십시오 ★
  둘 다 [X]                     방화벽·프록시 문제. 실습 1을 시연으로 전환
  웹만 [O], API 는 [X]          브라우저는 되는데 코드가 못 나가는 상태 ⚠️
                                → 사내 프록시 환경변수(HTTPS_PROXY) 확인
  Ollama 만 [X]                 ollama serve 가 안 떠 있는 것. 추적과 무관

⚠️ 이 스크립트는 키를 쓰지 않습니다. 키까지 확인하려면:
       python check_langsmith.py
""")
    print("=" * 64)


if __name__ == "__main__":
    main()
