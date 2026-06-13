"""환경 설정.

공공데이터 연동은 **식품안전나라 OpenAPI** 단일 surface로 표준화한다.
  base: https://openapi.foodsafetykorea.go.kr/api
  호출: {base}/{인증키}/{서비스ID}/json/{start}/{end}[/{조건키}={조건값} ...]
  응답: { "<서비스ID>": { "RESULT": {"CODE","MSG"}, "total_count", "row": [ {...} ] } }

각 데이터셋의 서비스ID는 운영자가 환경변수로 주입한다(식품안전나라/식의약 데이터포털
명세에서 확인). 인증키 또는 서비스ID가 없으면 해당 조회는 내장 MOCK으로 동작한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv 는 선택적 의존성
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").lower() in ("1", "true", "yes")


@dataclass
class Settings:
    # --- Claude(LLM) ---
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    # 기본 모델: Opus 4.8. 설계서 9.1 라우팅 적용 시 단계별 모델을 env로 지정.
    model: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
    extract_model: str = os.getenv("CLAUDE_EXTRACT_MODEL", os.getenv("CLAUDE_MODEL", "claude-opus-4-8"))
    max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "16000"))

    # --- 공공데이터(식품안전나라 OpenAPI) ---
    mfds_service_key: str | None = os.getenv("MFDS_SERVICE_KEY")
    mfds_base: str = os.getenv("MFDS_API_BASE", "https://openapi.foodsafetykorea.go.kr/api")

    # 데이터셋별 서비스ID(미설정 시 해당 조회는 MOCK).
    # 참고 데이터셋(공공데이터포털 ID): 수입식품 원료정보 15111777 ·
    # 식품첨가물 기준규격 15116583 · 농약 잔류허용기준 15074323 ·
    # 수입식품 회수판매중지 15095378 / 식품 회수·판매중지 15074318
    svc_ingredient: str = os.getenv("MFDS_INGREDIENT_SERVICE_ID", "")
    svc_additive: str = os.getenv("MFDS_ADDITIVE_SERVICE_ID", "")
    svc_pesticide: str = os.getenv("MFDS_PESTICIDE_SERVICE_ID", "")
    svc_recall: str = os.getenv("MFDS_RECALL_SERVICE_ID", "")

    @property
    def force_mock(self) -> bool:
        return _env_bool("USE_MOCK")

    @property
    def extraction_mock(self) -> bool:
        return self.force_mock or not self.anthropic_api_key

    def is_mock(self, service_id: str) -> bool:
        """해당 서비스 조회를 MOCK으로 할지 여부."""
        return self.force_mock or not (self.mfds_service_key and service_id)


settings = Settings()
