"""FastAPI 진입점.

실행:
    uvicorn poc.app.main:app --reload
    # 또는 poc/ 디렉터리에서: uvicorn app.main:app --reload
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .agent import verify_with_agent
from .config import settings
from .schemas import CaseResult
from .verification import verify_case

_UI_FILE = os.path.join(os.path.dirname(__file__), "static", "index.html")

app = FastAPI(
    title="수입가능여부 검토 AI 컨설팅 — PoC",
    version="0.1.0",
    description="성분표·한글표시를 검증해 수입가능여부(4단계)를 판정하는 PoC. "
    "AI는 보조이며 최종 판단·책임은 컨설턴트에게 있습니다.",
)


class VerifyRequest(BaseModel):
    ingredient_text: str
    label_text: str = ""
    product_name: str | None = None
    manufacturer: str | None = None


@app.get("/", response_class=HTMLResponse)
def ui() -> str:
    """컨설턴트 워크벤치 UI."""
    with open(_UI_FILE, encoding="utf-8") as f:
        return f.read()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": settings.model,
        "extraction_mock": settings.extraction_mock,
        "mfds_mock": settings.force_mock or not settings.mfds_service_key,
    }


@app.post("/verify", response_model=CaseResult)
def verify(req: VerifyRequest) -> CaseResult:
    """룰 기반(결정적) 검증 — 기본 경로."""
    return verify_case(
        ingredient_text=req.ingredient_text,
        label_text=req.label_text,
        product_name=req.product_name,
        manufacturer=req.manufacturer,
    )


@app.post("/verify/agent")
def verify_agent(req: VerifyRequest) -> dict:
    """Claude 도구사용 에이전트(서술형) — ANTHROPIC_API_KEY 필요."""
    if settings.extraction_mock:
        return {"error": "agent 모드는 ANTHROPIC_API_KEY 설정이 필요합니다."}
    return {"report": verify_with_agent(req.ingredient_text, req.label_text)}
