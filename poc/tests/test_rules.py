"""룰/판정 로직 단위 테스트(오프라인, API 불필요).

실행: poc/ 에서  python -m pytest  (또는 python -m unittest)
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import rules  # noqa: E402
from app.schemas import (  # noqa: E402
    IngredientExtraction,
    IngredientFinding,
    IngredientUsability,
    Verdict,
)

FULL_LABEL = "제품명 식품유형 영업소 유통기한 내용량 원재료명 영양성분 보관방법 주의사항"


def _extraction() -> IngredientExtraction:
    return IngredientExtraction(product_name="테스트 제품", ingredients=[])


def _finding(name: str, usability: IngredientUsability) -> IngredientFinding:
    return IngredientFinding(name=name, usability=usability, source="MOCK")


class TestVerdict(unittest.TestCase):
    def test_blocked_when_not_usable(self):
        findings = [_finding("마황", IngredientUsability.NOT_USABLE)]
        result = rules.evaluate(_extraction(), findings, rules.check_label(FULL_LABEL))
        self.assertEqual(result.verdict, Verdict.BLOCKED)

    def test_review_when_unknown(self):
        findings = [_finding("미지원료", IngredientUsability.UNKNOWN)]
        result = rules.evaluate(_extraction(), findings, rules.check_label(FULL_LABEL))
        self.assertEqual(result.verdict, Verdict.REVIEW)

    def test_conditional_when_restricted(self):
        findings = [_finding("카페인", IngredientUsability.RESTRICTED)]
        result = rules.evaluate(_extraction(), findings, rules.check_label(FULL_LABEL))
        self.assertEqual(result.verdict, Verdict.CONDITIONAL)

    def test_conditional_when_label_missing(self):
        findings = [_finding("정제수", IngredientUsability.USABLE)]
        result = rules.evaluate(_extraction(), findings, rules.check_label("제품명만 있음"))
        self.assertEqual(result.verdict, Verdict.CONDITIONAL)

    def test_importable_when_clean(self):
        findings = [_finding("정제수", IngredientUsability.USABLE)]
        result = rules.evaluate(_extraction(), findings, rules.check_label(FULL_LABEL))
        self.assertEqual(result.verdict, Verdict.IMPORTABLE)
        self.assertEqual(result.risk_score, 0.0)

    def test_blocker_priority_over_restricted(self):
        findings = [
            _finding("정제수", IngredientUsability.USABLE),
            _finding("카페인", IngredientUsability.RESTRICTED),
            _finding("마황", IngredientUsability.NOT_USABLE),
        ]
        result = rules.evaluate(_extraction(), findings, rules.check_label(FULL_LABEL))
        self.assertEqual(result.verdict, Verdict.BLOCKED)


if __name__ == "__main__":
    unittest.main()
