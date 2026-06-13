"""실연동 자가진단 스크립트.

egress 허용 + 인증키/서비스ID 설정 후 실행하면, 각 공공 API의
- 도달성(HTTP) / RESULT 코드
- 실제 출력 row 의 필드명
을 출력한다. 이를 보고 `app/mfds_api.py` 의 후보 키 목록(`_first(...)`)이나
요청변수(env `MFDS_*_QUERY_FIELD`)를 1회 보정하면 실연동이 완료된다.

사용:
    cd poc
    python scripts/api_selftest.py            # 기본 검색어 '정제수'
    python scripts/api_selftest.py 카페인
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import mfds_api  # noqa: E402
from app.config import settings  # noqa: E402


def main() -> None:
    term = sys.argv[1] if len(sys.argv) > 1 else "정제수"
    print("=" * 60)
    print("API 자가진단")
    print("  base            :", settings.mfds_base)
    print("  MFDS_SERVICE_KEY:", "SET" if settings.mfds_service_key else "MISSING")
    print("  검색어          :", term)
    print("=" * 60)

    services = [
        ("ingredient", settings.svc_ingredient, settings.qf_ingredient, lambda: mfds_api.lookup_ingredient(term)),
        ("additive", settings.svc_additive, settings.qf_additive, lambda: mfds_api.lookup_additive(term)),
        ("pesticide", settings.svc_pesticide, settings.qf_pesticide, lambda: mfds_api.lookup_pesticide_mrl(term)),
        ("recall", settings.svc_recall, settings.qf_recall, lambda: mfds_api.check_recall(term)),
    ]

    for label, svc, qf, wrapped in services:
        print(f"\n■ {label}  (service_id={'SET' if svc else 'MISSING'}, query_field={qf}, mock={settings.is_mock(svc)})")
        # 1) 원시 호출 → 실제 필드명 확인(키+서비스ID 설정 시에만)
        if settings.mfds_service_key and svc and not settings.force_mock:
            try:
                rows = mfds_api._call(svc, {qf: term})
                if rows:
                    print("   raw row[0] fields:", list(rows[0].keys()))
                else:
                    print("   raw: 응답 row 없음(RESULT 코드/검색어 확인)")
            except Exception as exc:
                msg = str(exc)
                if "allowlist" in msg or "egress" in msg.lower():
                    print("   ⚠️ egress 차단: 환경 네트워크 허용목록에 호스트를 추가하세요.")
                print("   raw error:", type(exc).__name__, msg[:140])
        # 2) 래핑된 결과(표준화/ MOCK 폴백 포함)
        print("   wrapped:", wrapped())


if __name__ == "__main__":
    main()
