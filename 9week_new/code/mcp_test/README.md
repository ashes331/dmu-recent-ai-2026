# mcp_test — MCP 맛보기 (9주차 2교시 보충)

설명 문서: `배포/[9주차]학생용_FastMCP_구성과_실습.html`

| 파일 | 역할 | 직접 실행? |
|---|---|---|
| `mcp_server.py` | MCP 서버 — `@mcp.tool` 로 `word_count`, `add` 를 내놓는다 | ✕ (아래 두 파일이 띄운다) |
| `check_server.py` | ① LLM 없이 서버에 도구 목록을 묻고 `add(2, 3)` 실행 | ○ |
| `mcp_client.py` | ② `MCPAdapter` → `bind_tools` → tool_calls → ToolMessage → 최종 답변 | ○ |
| `http_server.py` | (추가) 같은 도구를 **HTTP 로 띄워 두는** 서버 — 포트 8011 | ○ (터미널 1, 켜 둔다) |
| `http_client.py` | (추가) 띄워 둔 서버에 **주소로 접속** — `mcp_client.py` 와 한 줄만 다름 | ○ (터미널 2) |

## 준비

```bash
pip install -r requirements.txt      # langchain[mcp] → fastmcp 함께 설치
ollama pull llama3.2:3b              # ⚠️ gemma3:4b 는 도구 호출 미지원
```

## 실행 (이 폴더에서)

```bash
python check_server.py
python mcp_client.py          # 질문과 최종 답변만
python mcp_client.py -v       # 도구 목록 · tool_calls · ToolMessage 까지
```

## 실행 결과 (2026-10-29, fastmcp 4.1.4 · langchain 1.4.7 · llama3.2:3b)

```
결과: 5                                              ← check_server.py
답변: '나는 오늘 MCP를 배웠다'는 4 단어입니다.         ← mcp_client.py
```

- 실행할 때마다 `INFO Starting MCP server 'week9' with transport 'stdio'` 가 찍힙니다. 서버가 떴다는 정상 로그입니다.
- 모델 응답은 실행마다 달라질 수 있습니다. `tool_calls` 가 비면 모델이 도구 없이 답한 것입니다.
- 다른 모델을 쓰려면 루트 `.env` 에 `TOOL_MODEL=...` 을 적습니다(2교시 `tool_flow.py` 와 같음).

## (추가) HTTP 방식 — 서버를 띄워 두고 주소로 접속

```bash
# 터미널 1 — 켜 둔다 (끄기: Ctrl+C)
python http_server.py

# 터미널 2 — 실행할 때마다 터미널 1 에 POST /mcp 로그가 찍힌다
python http_client.py
python http_client.py "2 더하기 3은? add 도구를 써."
python http_client.py -v
```

| | stdio (`mcp_client.py`) | HTTP (`http_client.py`) |
|---|---|---|
| 접속 | `MCPAdapter(Path("mcp_server.py"))` | `MCPAdapter("http://127.0.0.1:8011/mcp")` |
| 서버 | 클라이언트가 띄우고 끝나면 종료 | 내가 먼저 띄워 두고 계속 켜 둠 |
| 여러 번 실행 | 매번 서버가 새로 뜸 | 서버 하나에 계속 접속 |

- 포트를 바꾸려면 루트 `.env` 에 `MCP_PORT=...` 를 적습니다. 서버·클라이언트가 같은 값을 읽습니다.
- 서버를 안 켜고 `http_client.py` 를 실행하면 «연결할 수 없습니다 — http_server.py 를 먼저 켜 두십시오» 안내가 나옵니다.
- `host="127.0.0.1"` 이라 내 PC 에서만 접속됩니다. `0.0.0.0` 으로 열면 다른 PC 도 내 도구를 실행할 수 있습니다(편의성 ↔ 보안).

실행 결과 (2026-10-29, 포트 8011): 서버를 다시 켜지 않고 세 번 접속 — `4 단어입니다` / `2 + 3 = 5` / `4 단어입니다`.
