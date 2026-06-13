"""Claude tool use 정의 + 실행기.

설계서 9.4: 공공 API를 Claude의 '도구'로 노출하여, 사실(원료 적격성)은
반드시 도구 결과에 근거하도록 한다.
"""

from __future__ import annotations

import json

from .mfds_api import lookup_ingredient

INGREDIENT_TOOL = {
    "name": "lookup_food_ingredient",
    "description": (
        "수입식품 원료정보를 조회하여 사용가능여부/사용제한/사용조건을 반환한다. "
        "성분 적격성을 판단할 때 각 원료마다 반드시 호출한다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ingredient_name": {
                "type": "string",
                "description": "원료 표준명 또는 영문명",
            }
        },
        "required": ["ingredient_name"],
        "additionalProperties": False,
    },
}

TOOLS = [INGREDIENT_TOOL]


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "lookup_food_ingredient":
        result = lookup_ingredient(tool_input.get("ingredient_name", ""))
        return json.dumps(result, ensure_ascii=False)
    return json.dumps({"error": f"unknown tool: {name}"}, ensure_ascii=False)
