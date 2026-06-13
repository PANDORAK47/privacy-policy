"""공공데이터(식품안전나라 OpenAPI) 연동 클라이언트.

연동 surface는 식품안전나라 OpenAPI 한 가지로 표준화한다.
  호출: {base}/{인증키}/{서비스ID}/json/{start}/{end}[/{조건키}={조건값}]
  응답: { "<서비스ID>": {"RESULT":{"CODE","MSG"}, "total_count", "row":[{...}]} }

- 인증키 + 서비스ID 가 설정되면 실제 호출, 아니면(또는 실패 시) 내장 MOCK 으로 폴백.
- 응답 필드명은 데이터셋마다 다르므로, 후보 키 목록으로 방어적으로 매핑한다.
  (정확한 요청변수/출력필드는 각 데이터셋 명세에서 확인 후 후보 목록을 보정한다.)

지원 조회:
  lookup_ingredient   수입식품 원료정보(사용가능여부/제한/부위/조건)
  lookup_additive     식품첨가물 기준·규격(사용기준 존재 여부)
  lookup_pesticide_mrl 농약 잔류허용기준(MRL)
  check_recall         수입식품/식품 회수·판매중지(부적합/회수 이력)
"""

from __future__ import annotations

from typing import Any

from .config import settings


# ----------------------------------------------------------------------------
# 식품안전나라 OpenAPI 호출
# ----------------------------------------------------------------------------
def _call(service_id: str, conditions: dict[str, str] | None = None, rows: int = 5) -> list[dict]:
    """식품안전나라 OpenAPI 호출 → row 리스트. 실패/무자료 시 예외 또는 빈 리스트."""
    import httpx

    cond = ""
    if conditions:
        cond = "/" + "/".join(f"{k}={v}" for k, v in conditions.items())
    url = f"{settings.mfds_base}/{settings.mfds_service_key}/{service_id}/json/1/{rows}{cond}"
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    block = data.get(service_id, {}) if isinstance(data, dict) else {}
    result = block.get("RESULT", {}) if isinstance(block, dict) else {}
    code = result.get("CODE") if isinstance(result, dict) else None
    # INFO-000 = 정상, INFO-200 = 데이터 없음
    if code and code not in ("INFO-000",):
        return []
    return block.get("row", []) or []


def _first(row: dict, candidates: list[str]) -> Any | None:
    """row 에서 후보 키 중 처음 발견되는 값(부분일치 허용)."""
    if not isinstance(row, dict):
        return None
    for key in candidates:
        if key in row and row[key] not in (None, ""):
            return row[key]
    # 부분일치 폴백
    for k, v in row.items():
        if v in (None, ""):
            continue
        for cand in candidates:
            if cand.lower() in str(k).lower():
                return v
    return None


def _standard(usability: str, restriction=None, conditions=None, source="MFDS_API", extra=None) -> dict:
    out = {
        "found": usability != "unknown",
        "usability": usability,
        "restriction": restriction,
        "conditions": conditions,
        "source": source,
    }
    if extra:
        out.update(extra)
    return out


# ----------------------------------------------------------------------------
# MOCK 데이터(오프라인 데모/폴백)
# ----------------------------------------------------------------------------
_MOCK_INGREDIENT: dict[str, tuple[str, str | None, str | None]] = {
    "water": ("usable", None, None), "정제수": ("usable", None, None),
    "sugar": ("usable", None, None), "설탕": ("usable", None, None), "정백당": ("usable", None, None),
    "salt": ("usable", None, None), "소금": ("usable", None, None),
    "citric acid": ("usable", None, None), "구연산": ("usable", None, None),
    "flavor": ("usable", None, None), "향료": ("usable", None, None),
    "caffeine": ("restricted", "사용량/표시 제한", "표시기준에 따른 함량·주의문구 표시 필요"),
    "카페인": ("restricted", "사용량/표시 제한", "표시기준에 따른 함량·주의문구 표시 필요"),
    "ephedra": ("not_usable", "식품 원료로 사용 불가", None), "마황": ("not_usable", "식품 원료로 사용 불가", None),
    "ephedrine": ("not_usable", "식품 원료로 사용 불가", None),
}

# 사용기준이 정해진(=사용 가능) 대표 식품첨가물 MOCK
_MOCK_ADDITIVE = {
    "구연산": "사용기준 있음(일반사용)", "citric acid": "사용기준 있음(일반사용)",
    "안식향산": "보존료 — 대상식품·사용량 한도 있음", "benzoic acid": "보존료 — 대상식품·사용량 한도 있음",
    "아스파탐": "감미료 — 표시(페닐알라닌) 필요", "aspartame": "감미료 — 표시(페닐알라닌) 필요",
}

# MOCK 회수/부적합 이력(제품/제조사명 부분일치)
_MOCK_RECALL = {
    "recalled energy": "표시기준 위반으로 회수 사례(MOCK)",
}


# ----------------------------------------------------------------------------
# 조회 함수(공개 API)
# ----------------------------------------------------------------------------
def lookup_ingredient(name: str) -> dict:
    """수입식품 원료정보: 원료의 사용가능여부/제한/부위/조건."""
    if settings.is_mock(settings.svc_ingredient):
        return _mock_ingredient(name)
    try:
        # NOTE: 조건키(원료명 검색)는 데이터셋 명세로 확인 후 보정. (예: PRDLST_NM)
        rows = _call(settings.svc_ingredient, {"PRDLST_NM": name})
        if not rows:
            return {**_mock_ingredient(name), "source": "MFDS_API(무자료→MOCK)"}
        row = rows[0]
        use_flag = str(_first(row, ["USE_YN", "USABLE", "사용여부", "사용가능여부"]) or "").upper()
        restriction = _first(row, ["LItem", "LIMIT", "사용제한", "RESTRICTION"])
        cond = _first(row, ["USE_COND", "사용조건", "CONDITION"])
        if use_flag in ("N", "FALSE", "0", "불가", "사용불가"):
            usability = "not_usable"
        elif restriction or cond:
            usability = "restricted"
        elif use_flag in ("Y", "TRUE", "1", "가능", "사용가능"):
            usability = "usable"
        else:
            usability = "unknown"
        return _standard(usability, restriction, cond)
    except Exception as exc:
        return {**_mock_ingredient(name), "source": f"MOCK(API 폴백: {type(exc).__name__})"}


def lookup_additive(name: str) -> dict:
    """식품첨가물 기준·규격: 사용기준 존재 여부(존재=사용가능, 단 한도 확인 필요)."""
    if settings.is_mock(settings.svc_additive):
        return _mock_additive(name)
    try:
        rows = _call(settings.svc_additive, {"NM": name})
        if not rows:
            return {**_mock_additive(name), "source": "MFDS_API(무자료→MOCK)"}
        row = rows[0]
        std = _first(row, ["STDR", "기준", "USE_STD", "사용기준"])
        return _standard("restricted" if std else "unknown", restriction="사용기준/한도 확인 필요",
                         conditions=std, source="MFDS_API")
    except Exception as exc:
        return {**_mock_additive(name), "source": f"MOCK(API 폴백: {type(exc).__name__})"}


def lookup_pesticide_mrl(pesticide: str, food: str | None = None) -> dict:
    """농약 잔류허용기준(MRL). 주로 농·축·수산 원료에 적용."""
    if settings.is_mock(settings.svc_pesticide):
        return {"found": False, "mrl": None, "source": "MOCK", "note": "MRL MOCK(미설정)"}
    try:
        conds = {"PRES_NM": pesticide}
        if food:
            conds["FOOD"] = food
        rows = _call(settings.svc_pesticide, conds)
        if not rows:
            return {"found": False, "mrl": None, "source": "MFDS_API(무자료)"}
        row = rows[0]
        return {"found": True, "mrl": _first(row, ["MRL", "잔류허용기준", "VALUE"]), "source": "MFDS_API"}
    except Exception as exc:
        return {"found": False, "mrl": None, "source": f"MOCK(API 폴백: {type(exc).__name__})"}


def check_recall(product_or_maker: str) -> dict:
    """수입식품/식품 회수·판매중지(부적합/회수) 이력 조회."""
    if settings.is_mock(settings.svc_recall):
        return _mock_recall(product_or_maker)
    try:
        rows = _call(settings.svc_recall, {"PRDLST_NM": product_or_maker})
        if not rows:
            return {"has_history": False, "reasons": [], "source": "MFDS_API"}
        reasons = [str(_first(r, ["RTRVL_RSON", "회수사유", "RECALL_REASON"]) or "사유미상") for r in rows]
        return {"has_history": True, "reasons": reasons[:5], "source": "MFDS_API"}
    except Exception as exc:
        return {**_mock_recall(product_or_maker), "source": f"MOCK(API 폴백: {type(exc).__name__})"}


# ----------------------------------------------------------------------------
# MOCK 구현
# ----------------------------------------------------------------------------
def _mock_ingredient(name: str) -> dict:
    key = (name or "").strip().lower()
    for k, (u, r, c) in _MOCK_INGREDIENT.items():
        if k and (k in key or key in k):
            return _standard(u, r, c, source="MOCK")
    return _standard("unknown", source="MOCK")


def _mock_additive(name: str) -> dict:
    key = (name or "").strip().lower()
    for k, std in _MOCK_ADDITIVE.items():
        if k and (k.lower() in key or key in k.lower()):
            return _standard("restricted", restriction="사용기준/한도 확인 필요", conditions=std, source="MOCK")
    return _standard("unknown", source="MOCK")


def _mock_recall(q: str) -> dict:
    key = (q or "").strip().lower()
    for k, reason in _MOCK_RECALL.items():
        if k and (k in key or key in k):
            return {"has_history": True, "reasons": [reason], "source": "MOCK"}
    return {"has_history": False, "reasons": [], "source": "MOCK"}
