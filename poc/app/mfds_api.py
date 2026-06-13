"""수입식품 원료정보 조회 클라이언트.

- MFDS_SERVICE_KEY + serviceId 가 설정되어 있으면 실제 공공 API 호출을 시도한다.
- 키가 없거나 호출이 실패하면 내장 MOCK 데이터로 폴백한다(오프라인 데모/장애 대비).

⚠️ 실제 엔드포인트/파라미터/응답 필드는 데이터셋 명세(data.go.kr 15111777,
   식품안전나라 OpenAPI)에서 확인 후 `_parse_response` 와 `lookup_ingredient` 를
   해당 스키마에 맞게 보정해야 한다.
"""

from __future__ import annotations

from .config import settings

# 데모용 MOCK 원료 사전: (usability, restriction, conditions)
# 부분 일치(영/한)로 매칭. 실제 운영에서는 표준명 매핑 사전 + 공공 API로 대체.
_MOCK_DB: dict[str, tuple[str, str | None, str | None]] = {
    "water": ("usable", None, None),
    "정제수": ("usable", None, None),
    "sugar": ("usable", None, None),
    "설탕": ("usable", None, None),
    "정백당": ("usable", None, None),
    "salt": ("usable", None, None),
    "소금": ("usable", None, None),
    "citric acid": ("usable", None, None),
    "구연산": ("usable", None, None),
    "flavor": ("usable", None, None),
    "향료": ("usable", None, None),
    "caffeine": ("restricted", "사용량/표시 제한", "표시기준에 따른 함량·주의문구 표시 필요"),
    "카페인": ("restricted", "사용량/표시 제한", "표시기준에 따른 함량·주의문구 표시 필요"),
    "ephedra": ("not_usable", "식품 원료로 사용 불가", None),
    "마황": ("not_usable", "식품 원료로 사용 불가", None),
    "ephedrine": ("not_usable", "식품 원료로 사용 불가", None),
}


def _mock_lookup(name: str) -> dict:
    key = (name or "").strip().lower()
    for k, (usability, restriction, conditions) in _MOCK_DB.items():
        if k and (k in key or key in k):
            return {
                "found": True,
                "usability": usability,
                "restriction": restriction,
                "conditions": conditions,
                "source": "MOCK",
            }
    return {
        "found": False,
        "usability": "unknown",
        "restriction": None,
        "conditions": None,
        "source": "MOCK",
    }


def _parse_response(data: dict, name: str) -> dict:
    """공공 API 응답 → 표준 결과로 변환(베스트 에포트, 명세 확인 후 보정)."""
    # 식품안전나라 계열은 보통 { "<serviceId>": { "row": [ {...} ] } } 형태.
    rows = []
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict) and isinstance(v.get("row"), list):
                rows = v["row"]
                break
    if not rows:
        return {**_mock_lookup(name), "source": "API(빈 응답 → MOCK)"}

    row = rows[0]
    # 사용가능여부/사용제한 필드명은 명세에 맞게 보정 필요
    usable_flag = str(row.get("USE_YN", row.get("USABLE", ""))).upper()
    restriction = row.get("LIMIT_INFO") or row.get("RESTRICTION")
    conditions = row.get("USE_COND") or row.get("CONDITION")
    if usable_flag in ("N", "FALSE", "0"):
        usability = "not_usable"
    elif restriction or conditions:
        usability = "restricted"
    elif usable_flag in ("Y", "TRUE", "1"):
        usability = "usable"
    else:
        usability = "unknown"
    return {
        "found": True,
        "usability": usability,
        "restriction": restriction,
        "conditions": conditions,
        "source": "MFDS_API",
    }


def lookup_ingredient(name: str) -> dict:
    """원료명으로 사용가능여부 등을 조회한다."""
    if settings.mfds_mock:
        return _mock_lookup(name)
    try:
        import httpx

        # 식품안전나라 패턴: /{key}/{serviceId}/json/{start}/{end}[/조건]
        url = f"{settings.mfds_base}/{settings.mfds_service_key}/{settings.mfds_service_id}/json/1/5"
        # NOTE: 원료명 필터 파라미터명(PRDLST_NM 등)은 데이터셋 명세로 확인.
        resp = httpx.get(url, params={"PRDLST_NM": name}, timeout=10.0)
        resp.raise_for_status()
        return _parse_response(resp.json(), name)
    except Exception as exc:  # 네트워크/스키마 오류 → MOCK 폴백
        result = _mock_lookup(name)
        result["source"] = f"MOCK(API 폴백: {type(exc).__name__})"
        return result
