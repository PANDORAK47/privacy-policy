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

    # 검색 조건(요청변수)명 — 명세 확인 후 env로 보정 가능(코드수정 불필요).
    qf_ingredient: str = os.getenv("MFDS_INGREDIENT_QUERY_FIELD", "PRDLST_NM")
    qf_additive: str = os.getenv("MFDS_ADDITIVE_QUERY_FIELD", "NM")
    qf_pesticide: str = os.getenv("MFDS_PESTICIDE_QUERY_FIELD", "PRES_NM")
    qf_recall: str = os.getenv("MFDS_RECALL_QUERY_FIELD", "PRDLST_NM")

    # --- 공공데이터포털(data.go.kr) REST (옵션 B, 권장) ---
    # 원료 등 일부 조회는 식품안전나라가 아니라 공공데이터포털 REST(serviceKey 인증,
    # items[]/data[] 응답)로 제공된다. 아래 *_DATAGO_URL 을 채우면 그 조회는
    # 식품안전나라 대신 data.go.kr REST 를 사용한다(없으면 식품안전나라 → MOCK 순서).
    #   예) https://apis.data.go.kr/1471000/<서비스>/<오퍼레이션>
    #       https://api.odcloud.kr/api/15111777/v1/uddi:<uuid>
    data_go_kr_api_key: str | None = os.getenv("DATA_GO_KR_API_KEY")
    dg_ingredient_url: str = os.getenv("INGREDIENT_DATAGO_URL", "")
    dg_additive_url: str = os.getenv("ADDITIVE_DATAGO_URL", "")
    dg_pesticide_url: str = os.getenv("PESTICIDE_DATAGO_URL", "")
    dg_recall_url: str = os.getenv("RECALL_DATAGO_URL", "")
    # data.go.kr 검색 요청변수명(미지정 시 식품안전나라용 후보를 그대로 사용).
    dg_ingredient_qf: str = os.getenv("INGREDIENT_DATAGO_QUERY_FIELD", os.getenv("MFDS_INGREDIENT_QUERY_FIELD", "PRDLST_NM"))
    dg_additive_qf: str = os.getenv("ADDITIVE_DATAGO_QUERY_FIELD", os.getenv("MFDS_ADDITIVE_QUERY_FIELD", "NM"))
    dg_pesticide_qf: str = os.getenv("PESTICIDE_DATAGO_QUERY_FIELD", os.getenv("MFDS_PESTICIDE_QUERY_FIELD", "PRES_NM"))
    dg_recall_qf: str = os.getenv("RECALL_DATAGO_QUERY_FIELD", os.getenv("MFDS_RECALL_QUERY_FIELD", "PRDLST_NM"))

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
