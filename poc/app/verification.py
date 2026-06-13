"""검증 오케스트레이션(코드 주도, 결정적·감사가능).

흐름: 성분표 추출 → 원료별 API 조회 → 한글표시 점검 → 룰/스코어링 → 판정.
"""

from __future__ import annotations

from . import rules
from .extraction import extract_ingredients
from .mfds_api import lookup_ingredient
from .schemas import CaseResult, IngredientFinding, IngredientUsability


def verify_case(
    ingredient_text: str | None = None,
    pdf_bytes: bytes | None = None,
    label_text: str = "",
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
    return rules.evaluate(extraction, findings, label_findings)
