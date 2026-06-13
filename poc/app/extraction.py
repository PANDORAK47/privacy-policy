"""성분표 → 구조화 추출(Claude messages.parse).

- ANTHROPIC_API_KEY 가 없으면 간이 MOCK 파서로 동작.
- 텍스트 또는 PDF(base64 document 블록) 입력 지원.
"""

from __future__ import annotations

import base64

from .config import settings
from .schemas import ExtractedIngredient, IngredientExtraction

_EXTRACTION_INSTRUCTIONS = (
    "다음은 수입 예정 가공식품의 성분표(원재료/배합비율)입니다. "
    "각 원료의 원문명(name_original), 가능하면 한글 표준명(name_ko), 배합비율(percent), "
    "용도(role)를 추출하고, 제품명과 추정 식품유형(food_type_guess)을 채우세요. "
    "추정/창작하지 말고 문서에 있는 정보만 사용하세요.\n\n성분표:\n"
)


def _mock_extraction(text: str | None) -> IngredientExtraction:
    ingredients: list[ExtractedIngredient] = []
    for raw in (text or "").splitlines():
        line = raw.strip().strip(",").strip()
        if not line:
            continue
        ingredients.append(ExtractedIngredient(name_original=line, name_ko=line))
    if not ingredients:
        ingredients = [ExtractedIngredient(name_original="정제수", name_ko="정제수")]
    return IngredientExtraction(
        product_name="(MOCK) 샘플 제품",
        food_type_guess=None,
        ingredients=ingredients,
    )


def extract_ingredients(text: str | None = None, pdf_bytes: bytes | None = None) -> IngredientExtraction:
    if settings.extraction_mock:
        return _mock_extraction(text)

    import anthropic

    client = anthropic.Anthropic()
    content: list[dict] = []
    if pdf_bytes:
        content.append(
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(pdf_bytes).decode("utf-8"),
                },
            }
        )
    content.append({"type": "text", "text": _EXTRACTION_INSTRUCTIONS + (text or "")})

    response = client.messages.parse(
        model=settings.extract_model,
        max_tokens=settings.max_tokens,
        messages=[{"role": "user", "content": content}],
        output_format=IngredientExtraction,
    )
    return response.parsed_output or _mock_extraction(text)
