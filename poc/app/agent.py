"""Claude 도구사용(tool use) 에이전트 변형.

성분표/라벨을 받아 Claude가 원료정보 API 도구를 호출하며 서술형 검토 보고서를
생성한다. 결정적 판정은 verification.verify_case(룰 기반)를 권장하며, 본 모듈은
설계서 9.4/9.6의 에이전트 패턴 시연용이다. (ANTHROPIC_API_KEY 필요)
"""

from __future__ import annotations

from .config import settings
from .tools import TOOLS, execute_tool

_SYSTEM = (
    "당신은 한국 수입식품 컨설턴트를 돕는 검토 보조 AI입니다. "
    "원료 사용가능여부·첨가물 기준·농약 MRL·회수/부적합 이력 등 사실은 반드시 제공된 도구"
    "(lookup_food_ingredient, lookup_food_additive, lookup_pesticide_mrl, check_recall_history)의 "
    "결과에 근거해 판단하고 추정하지 마십시오. 정보가 부족하거나 불확실하면 '추가검토'로 분류하십시오. "
    "최종 판단과 책임은 컨설턴트에게 있음을 전제로, 근거와 보완 액션을 한국어로 간결히 제시하십시오."
)


def verify_with_agent(ingredient_text: str, label_text: str = "", max_turns: int = 10) -> str:
    import anthropic

    client = anthropic.Anthropic()
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"[성분표]\n{ingredient_text}\n\n[한글표시(라벨) 텍스트]\n{label_text or '(미제공)'}\n\n"
                "각 원료를 도구로 조회한 뒤, 수입가능여부를 "
                "수입가능/조건부(보완필요)/추가검토/수입곤란 중 하나로 판정하고 "
                "근거와 보완 액션을 정리하세요."
            ),
        }
    ]

    response = None
    for _ in range(max_turns):
        response = client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=_SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            break
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": execute_tool(block.name, block.input),
                    }
                )
        messages.append({"role": "user", "content": tool_results})

    if response is None:
        return ""
    return "".join(b.text for b in response.content if b.type == "text")
