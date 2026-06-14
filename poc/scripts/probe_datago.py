"""data.go.kr 엔드포인트 1회 점검기 (.env/코드 수정 없이 후보 주소를 바로 시험).

사용:
    cd poc
    python scripts/probe_datago.py "<요청주소(경로까지)>" [검색어]
  예) python scripts/probe_datago.py "https://apis.data.go.kr/1471000/XxxService/getXxx" 정제수

동작:
  - `.env` 의 DATA_GO_KR_API_KEY 로 주어진 주소를 호출한다(serviceKey/type/페이지 자동 첨부).
  - 성공 시 실제 응답의 `raw row[0] fields: [...]` 한 줄을 출력(값이 아니라 필드명이라 안전).
  - 실패/무자료 시 HTTP 상태 + (키가 마스킹된) 응답 머리/오류를 출력하여 원인을 진단한다.
  - "필터없음" 시도까지 자동으로 해보므로, 검색변수명(기본 PRDLST_NM)이 달라도 엔드포인트
    자체가 살아있으면 필드명을 확인할 수 있다.

원료명 검색변수는 INGREDIENT_DATAGO_QUERY_FIELD(env)로 조정 가능.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import mfds_api  # noqa: E402
from app.config import settings  # noqa: E402


def _mask(s: str) -> str:
    s = str(s)
    for secret in (settings.data_go_kr_api_key, settings.mfds_service_key):
        if secret and len(secret) >= 8:
            s = s.replace(secret, "***")
    return re.sub(r"(?i)(serviceKey|key|apikey|token)=([^&\s'\"]+)", r"\1=***", s)


def _try(url: str, params: dict):
    import httpx

    resp = httpx.get(url, params=params, timeout=10.0)
    rows = []
    try:
        rows = mfds_api._extract_rows_datago(resp.json())
    except Exception:
        rows = []
    return resp.status_code, rows, resp.text


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].startswith("http"):
        print('사용: python scripts/probe_datago.py "<요청주소(경로까지)>" [검색어]')
        print('  예) python scripts/probe_datago.py "https://apis.data.go.kr/1471000/XxxService/getXxx" 정제수')
        sys.exit(2)

    url = sys.argv[1]
    term = sys.argv[2] if len(sys.argv) > 2 else "정제수"
    key = settings.data_go_kr_api_key
    qf = settings.dg_ingredient_qf

    print("=" * 60)
    print("data.go.kr 엔드포인트 점검")
    print("  URL               :", _mask(url))
    print("  DATA_GO_KR_API_KEY:", "SET" if key else "MISSING")
    print("  검색변수 / 검색어 :", qf, "/", term)
    print("=" * 60)

    if not key:
        print("❌ DATA_GO_KR_API_KEY 가 .env 에 없습니다.")
        print("   → poc/ 에서 `python3 scripts/setup_local.py` 재실행하거나 .env 를 확인하세요.")
        sys.exit(1)

    is_odcloud = "odcloud.kr" in url
    if is_odcloud:
        attempts = [
            ("odcloud · 검색", {"serviceKey": key, "page": "1", "perPage": "5", "returnType": "JSON",
                               f"cond[{qf}::LIKE]": term}),
            ("odcloud · 필터없음", {"serviceKey": key, "page": "1", "perPage": "5", "returnType": "JSON"}),
        ]
    else:
        attempts = [
            ("apis · 검색", {"serviceKey": key, "pageNo": "1", "numOfRows": "5", "type": "json", qf: term}),
            ("apis · 필터없음", {"serviceKey": key, "pageNo": "1", "numOfRows": "5", "type": "json"}),
        ]

    for label, params in attempts:
        print(f"\n■ 시도: {label}")
        try:
            status, rows, body = _try(url, params)
            print("   HTTP:", status)
            if rows:
                print("   ✅ raw row[0] fields:", list(rows[0].keys()))
                print("   → 이 한 줄을 회신해 주세요(값이 아니라 필드명이라 안전합니다).")
                return
            print("   row 없음. 응답 머리(키 마스킹):")
            print("    ", _mask(body)[:400].replace("\n", " ").strip())
        except Exception as exc:
            print("   오류:", type(exc).__name__, _mask(str(exc))[:200])

    print(
        "\n진단 힌트:"
        "\n  - 'SERVICE_KEY_IS_NOT_REGISTERED'/인증키 관련 → 키 등록 직후 대기(최대 1~2시간) 또는 키 확인"
        "\n  - 'NO_OPENAPI_SERVICE_ERROR'/'경로'/404 → 주소(operation)가 틀림 → data.go.kr 명세에서 재확인"
        "\n  - '필터없음'에서 row 가 나오면 → 엔드포인트는 정상, 검색변수명만 다름 → 그 필드명을 회신해 주세요"
        "\n  - 'Host not in allowlist'/타임아웃 → (원격 환경에서만) egress 허용목록에 apis.data.go.kr 추가"
    )


if __name__ == "__main__":
    main()
