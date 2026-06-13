"""Claude tool use 정의 + 실행기.

설계서 9.4: 공공 API를 Claude의 '도구'로 노출하여, 사실(원료 적격성·기준·이력)은
반드시 도구 결과에 근거하도록 한다.
"""

from __future__ import annotations

import json

from . import mfds_api

INGREDIENT_TOOL = {
    "name": "lookup_food_ingredient",
    "description": (
        "수입식품 원료정보를 조회해 사용가능여부/사용제한/사용조건을 반환한다. "
        "성분 적격성 판단 시 각 원료마다 호출한다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"ingredient_name": {"type": "string", "description": "원료 표준명/영문명"}},
        "required": ["ingredient_name"],
        "additionalProperties": False,
    },
}

ADDITIVE_TOOL = {
    "name": "lookup_food_additive",
    "description": "식품첨가물의 기준·규격(사용기준/한도 존재 여부)을 조회한다. 첨가물성 원료에 대해 호출한다.",
    "input_schema": {
        "type": "object",
        "properties": {"additive_name": {"type": "string", "description": "첨가물명"}},
        "required": ["additive_name"],
        "additionalProperties": False,
    },
}

PESTICIDE_TOOL = {
    "name": "lookup_pesticide_mrl",
    "description": "농약 잔류허용기준(MRL)을 조회한다. 농·축·수산 원료/식품에 대해 호출한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pesticide": {"type": "string", "description": "농약명"},
            "food": {"type": "string", "description": "식품명(선택)"},
        },
        "required": ["pesticide"],
        "additionalProperties": False,
    },
}

RECALL_TOOL = {
    "name": "check_recall_history",
    "description": "수입식품/식품 회수·판매중지(부적합/회수) 이력을 제품명 또는 제조사명으로 조회한다.",
    "input_schema": {
        "type": "object",
        "properties": {"product_or_maker": {"type": "string", "description": "제품명 또는 제조사명"}},
        "required": ["product_or_maker"],
        "additionalProperties": False,
    },
}

TOOLS = [INGREDIENT_TOOL, ADDITIVE_TOOL, PESTICIDE_TOOL, RECALL_TOOL]


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "lookup_food_ingredient":
        result = mfds_api.lookup_ingredient(tool_input.get("ingredient_name", ""))
    elif name == "lookup_food_additive":
        result = mfds_api.lookup_additive(tool_input.get("additive_name", ""))
    elif name == "lookup_pesticide_mrl":
        result = mfds_api.lookup_pesticide_mrl(tool_input.get("pesticide", ""), tool_input.get("food"))
    elif name == "check_recall_history":
        result = mfds_api.check_recall(tool_input.get("product_or_maker", ""))
    else:
        result = {"error": f"unknown tool: {name}"}
    return json.dumps(result, ensure_ascii=False)
