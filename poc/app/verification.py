"""검증 오케스트레이션(코드 주도, 결정적·감사가능).

흐름: 성분표 추출 → 원료별 사용가능여부 조회 → 한글표시 점검 →
      회수/부적합 이력 조회 → 룰/스코어링 → 판정.

첨가물 기준·농약 MRL 은 정량 데이터가 필요해 결정적 파이프라인에는 포함하지 않고
도구(tools.py)로 노출한다(에이전트/후속 확장용).
"""

from __future__ import annotations

from . import rules
from .extraction import extract_ingredients
from .mfds_api import check_recall, lookup_ingredient
from .schemas import CaseResult, IngredientFinding, IngredientUsability, RecallFinding


def verify_case(
    ingredient_text: str | None = None,
    pdf_bytes: bytes | None = None,
    label_text: str = "",
    product_name: str | None = None,
    manufacturer: str | None = None,
) -> CaseResult:
    extraction = extract_ingredients(text=ingredient_text, pdf_bytes=pdf_bytes)

    findings: list[IngredientFinding] = []
    for ing in extraction.ingredients:
        query = ing.name_ko or ing.name_original
        result = lookup_ingredient(query)
        findings.append(
            IngredientFinding(
                name=ing.name_original,
                usability=IngredientUsability(result["usability"]),
                restriction=result.get("restriction"),
                conditions=result.get("conditions"),
                source=result["source"],
            )
        )

    label_findings = rules.check_label(label_text)

    recall_query = manufacturer or product_name or extraction.product_name
    raw = check_recall(recall_query)
    recall = RecallFinding(
        query=recall_query,
        has_history=raw["has_history"],
        reasons=raw.get("reasons", []),
        source=raw["source"],
    )

    return rules.evaluate(extraction, findings, label_findings, recall=recall)
