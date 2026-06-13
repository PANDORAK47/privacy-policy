"""도메인 스키마(Pydantic).

설계서 8.3 데이터 모델의 PoC 축소판.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class IngredientUsability(str, Enum):
    USABLE = "usable"          # 사용 가능
    RESTRICTED = "restricted"  # 사용 제한/조건 있음
    NOT_USABLE = "not_usable"  # 사용 불가
    UNKNOWN = "unknown"        # 미확인(추가검토)


class Verdict(str, Enum):
    IMPORTABLE = "수입가능"
    CONDITIONAL = "조건부(보완필요)"
    REVIEW = "추가검토"
    BLOCKED = "수입곤란"


# --- 추출 스키마(Claude 구조화 출력 대상) ---
class ExtractedIngredient(BaseModel):
    name_original: str = Field(description="원문 그대로의 원료명(영문 등)")
    name_ko: str | None = Field(default=None, description="한글 표준명(가능 시)")
    percent: float | None = Field(default=None, description="배합 비율(%)")
    role: str | None = Field(default=None, description="용도(예: 감미료, 보존제)")


class IngredientExtraction(BaseModel):
    product_name: str
    food_type_guess: str | None = Field(default=None, description="추정 식품유형")
    ingredients: list[ExtractedIngredient]


# --- 검증 결과 ---
class IngredientFinding(BaseModel):
    name: str
    usability: IngredientUsability
    restriction: str | None = None
    conditions: str | None = None
    source: str = Field(description="근거 출처(API/MOCK 등)")


class LabelFinding(BaseModel):
    item: str
    present: bool


class RecallFinding(BaseModel):
    query: str
    has_history: bool
    reasons: list[str] = []
    source: str = "MOCK"


class CaseResult(BaseModel):
    product_name: str
    verdict: Verdict
    risk_score: float = Field(ge=0.0, le=1.0)
    ingredient_findings: list[IngredientFinding]
    label_findings: list[LabelFinding]
    recall: RecallFinding | None = None
    actions: list[str]
    summary: str
    disclaimer: str = (
        "본 결과는 AI 보조 사전 스크리닝이며, 최종 수입가능여부 판단과 책임은 "
        "담당 컨설턴트에게 있습니다. 규정·기준은 최신 고시로 재확인하십시오."
    )
