"""맥북 로컬 자동 설정 도우미.

기존 `ifacs-unified` 설정(.mcp.json / claude_desktop_config.json)의 env 에서
API 키를 자동으로 읽어 `poc/.env` 를 생성한다. (키를 손으로 복사하거나 채팅에
붙여넣을 필요가 없다. 키 '값'은 화면에 출력하지 않고 길이만 표시한다.)

사용(맥 Terminal):
    cd poc
    python3 scripts/setup_local.py
    # 경로를 직접 지정하려면:
    python3 scripts/setup_local.py "/Users/<이름>/Downloads/SKILL 2/.mcp.json"
"""

from __future__ import annotations

import json
import os
import sys

DEFAULT_CONFIGS = [
    os.path.expanduser("~/Downloads/SKILL 2/.mcp.json"),
    os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json"),
]


def find_config(argv: list[str]) -> str | None:
    if len(argv) > 1 and argv[1]:
        return argv[1]
    for path in DEFAULT_CONFIGS:
        if os.path.exists(path):
            return path
    return None


def extract_env(cfg_path: str) -> dict:
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    servers = cfg.get("mcpServers", {}) or {}
    server = servers.get("ifacs-unified")
    if not server:  # ifacs-unified 가 없으면 env 를 가진 첫 서버 사용
        for s in servers.values():
            if isinstance(s, dict) and s.get("env"):
                server = s
                break
    return (server or {}).get("env", {}) or {}


def main() -> None:
    cfg = find_config(sys.argv)
    if not cfg or not os.path.exists(cfg):
        print("❌ .mcp.json / claude_desktop_config.json 을 찾지 못했습니다.")
        print("   경로를 직접 지정해 주세요(따옴표 포함):")
        print('   python3 scripts/setup_local.py "/Users/<이름>/Downloads/SKILL 2/.mcp.json"')
        sys.exit(1)

    print("설정 파일:", cfg)
    env = extract_env(cfg)
    if not env:
        print("❌ ifacs-unified(또는 임의 서버)의 env 에서 키를 찾지 못했습니다.")
        sys.exit(1)

    fsk = env.get("FSK_API_KEY", "")
    datago = env.get("DATA_GO_KR_API_KEY", "")
    unipass = {k: v for k, v in env.items() if k.startswith("UNIPASS_")}

    lines = [
        "# 자동 생성됨 (scripts/setup_local.py). 키가 들어있으니 절대 커밋/공유하지 마세요.",
        "CLAUDE_MODEL=claude-opus-4-8",
        "# 식품안전나라(FSK) 키를 기본 연동키로 사용",
        f"MFDS_SERVICE_KEY={fsk}",
        "MFDS_API_BASE=https://openapi.foodsafetykorea.go.kr/api",
        "# 아래 서비스ID는 식품안전나라/공공데이터 명세에서 확인 후 채우세요(비우면 MOCK).",
        "MFDS_INGREDIENT_SERVICE_ID=",
        "MFDS_ADDITIVE_SERVICE_ID=",
        "MFDS_PESTICIDE_SERVICE_ID=",
        "MFDS_RECALL_SERVICE_ID=",
    ]
    if datago:
        lines.append("# 공공데이터포털 REST 키(참고/확장용)")
        lines.append(f"DATA_GO_KR_API_KEY={datago}")
    for k, v in sorted(unipass.items()):
        lines.append(f"{k}={v}")

    out = os.environ.get(
        "POC_ENV_OUT",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    )
    if os.path.exists(out):
        print(f"⚠️ 이미 존재: {out} → 덮어쓰지 않았습니다. (백업 후 삭제하고 다시 실행)")
    else:
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"✅ 생성됨: {out}")

    # 키 '값'은 출력하지 않고 존재/길이만 표시(안전)
    print("\n읽어온 키(값은 비표시):")
    print(f"  - 식품안전나라 FSK_API_KEY      : {len(fsk)}자" if fsk else "  - 식품안전나라 FSK_API_KEY      : 없음")
    print(f"  - 공공데이터 DATA_GO_KR_API_KEY : {len(datago)}자" if datago else "  - 공공데이터 DATA_GO_KR_API_KEY : 없음")
    print(f"  - 관세청 UNIPASS_*              : {len(unipass)}개")
    print("\n다음 단계:")
    print("  1) (선택) poc/.env 의 MFDS_*_SERVICE_ID 채우기 — 비우면 MOCK으로 동작")
    print("  2) python3 scripts/api_selftest.py 정제수     # 실제 연결·응답 필드명 확인")
    print("  3) uvicorn app.main:app --reload   → 브라우저 http://localhost:8000")


if __name__ == "__main__":
    main()
