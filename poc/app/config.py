"""환경 설정.

- ANTHROPIC_API_KEY 가 없으면 추출 단계는 MOCK 으로 동작(오프라인 데모 가능).
- MFDS_SERVICE_KEY 가 없으면 원료정보 조회는 내장 MOCK 데이터로 동작.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv 는 선택적 의존성
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


@dataclass
class Settings:
    # --- Claude(LLM) ---
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    # 기본 모델: Opus 4.8. 설계서 9.1의 모델 라우팅(분류=Haiku, 추출=Sonnet, 판정=Opus)을
    # 적용하려면 환경변수로 단계별 모델을 지정한다.
    model: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
    extract_model: str = os.getenv("CLAUDE_EXTRACT_MODEL", os.getenv("CLAUDE_MODEL", "claude-opus-4-8"))
    max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "16000"))

    # --- 공공데이터(식약처/식품안전나라) ---
    mfds_service_key: str | None = os.getenv("MFDS_SERVICE_KEY")
    # NOTE: 수입식품 원료정보 API 의 정확한 base/serviceId/파라미터는 데이터셋 명세
    # (data.go.kr 15111777 / 식품안전나라)에서 반드시 확인 후 설정한다.
    mfds_base: str = os.getenv("MFDS_INGREDIENT_API_BASE", "http://openapi.foodsafetykorea.go.kr/api")
    mfds_service_id: str = os.getenv("MFDS_INGREDIENT_SERVICE_ID", "")

    @property
    def extraction_mock(self) -> bool:
        if os.getenv("USE_MOCK", "").lower() in ("1", "true", "yes"):
            return True
        return not self.anthropic_api_key

    @property
    def mfds_mock(self) -> bool:
        if os.getenv("USE_MOCK", "").lower() in ("1", "true", "yes"):
            return True
        return not (self.mfds_service_key and self.mfds_service_id)


settings = Settings()
