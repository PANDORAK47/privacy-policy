"""실연동 자가진단 스크립트.

egress 허용 + 인증키/서비스ID(또는 data.go.kr URL) 설정 후 실행하면, 각 공공 API의
- 도달성(HTTP) / 활성 백엔드(datago | mfds | mock)
- 실제 출력 row 의 필드명
을 출력한다. 이를 보고 `app/mfds_api.py` 의 후보 키 목록(`_first(...)`)이나
요청변수(env `*_QUERY_FIELD`)를 1회 보정하면 실연동이 완료된다.

키 값은 절대 출력하지 않으며, 예외 메시지에 포함된 키/URL 의 인증키는 마스킹한다.

사용:
    cd poc
    python scripts/api_selftest.py            # 기본 검색어 '정제수'
    python scripts/api_selftest.py 카페인
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import mfds_api  # noqa: E402
from app.config import settings  # noqa: E402

SERVICES = ("ingredient", "additive", "pesticide", "recall")


def _mask(s: str) -> str:
    """예외/URL 문자열에서 인증키 노출을 방지(키 원문 치환 + serviceKey/key 파라미터 마스킹)."""
    s = str(s)
    for secret in (settings.mfds_service_key, settings.data_go_kr_api_key):
        if secret and len(secret) >= 8:
            s = s.replace(secret, "***")
    return re.sub(r"(?i)(serviceKey|key|apikey|token)=([^&\s'\"]+)", r"\1=***", s)


def main() -> None:
    term = sys.argv[1] if len(sys.argv) > 1 else "정제수"
    wrapped = {
        "ingredient": lambda: mfds_api.lookup_ingredient(term),
        "additive": lambda: mfds_api.lookup_additive(term),
        "pesticide": lambda: mfds_api.lookup_pesticide_mrl(term),
        "recall": lambda: mfds_api.check_recall(term),
    }

    print("=" * 60)
    print("API 자가진단")
    print("  MFDS base         :", settings.mfds_base)
    print("  MFDS_SERVICE_KEY  :", "SET" if settings.mfds_service_key else "MISSING")
    print("  DATA_GO_KR_API_KEY:", "SET" if settings.data_go_kr_api_key else "MISSING")
    print("  검색어            :", term)
    print("=" * 60)

    for label in SERVICES:
        b = mfds_api.backend(label)
        print(f"\n■ {label}  (backend={b})")
        # 1) 원시 호출 → 실제 필드명 확인(실연동 백엔드일 때만)
        if b != "mock":
            try:
                rows = mfds_api.raw_rows(label, term)
                if rows:
                    print("   raw row[0] fields:", list(rows[0].keys()))
                else:
                    print("   raw: 응답 row 없음(RESULT 코드/검색어/요청변수명 확인)")
            except Exception as exc:
                msg = _mask(str(exc))
                if "allowlist" in msg or "egress" in msg.lower():
                    print("   ⚠️ egress 차단: 환경 네트워크 허용목록에 호스트를 추가하세요.")
                print("   raw error:", type(exc).__name__, msg[:200])
        # 2) 래핑된 결과(표준화 / MOCK 폴백 포함)
        print("   wrapped:", wrapped[label]())


if __name__ == "__main__":
    main()
