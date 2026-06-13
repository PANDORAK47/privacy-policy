"""룰 엔진 + 한글표시 체크리스트 + 리스크 스코어링 → 판정.

설계서 6장(판정 로직)의 PoC 축소판. 가중치는 2024 부적합 통계 기반 초기값.
"""

from __future__ import annotations

from .schemas import (
    CaseResult,
    IngredientExtraction,
    IngredientFinding,
    IngredientUsability,
    LabelFinding,
    RecallFinding,
    Verdict,
)

# 한글표시사항 대표 항목(식품등의 표시기준). 라벨 텍스트에 키워드 포함 여부로 간이 점검.
HANGEUL_LABEL_ITEMS = [
    "제품명",
    "식품유형",
    "영업소",       # 수입판매업소 명칭·소재지
    "유통기한",     # 또는 소비기한
    "내용량",
    "원재료명",
    "영양성분",
    "보관방법",
    "주의사항",
]

# 부적합 통계(2024) 기반 리스크 가중치
WEIGHT_NOT_USABLE = 0.31
WEIGHT_RESTRICTED = 0.20
WEIGHT_UNKNOWN = 0.10
WEIGHT_LABEL = 0.13


def check_label(label_text: str | None) -> list[LabelFinding]:
    text = label_text or ""
    return [LabelFinding(item=item, present=(item in text)) for item in HANGEUL_LABEL_ITEMS]


def evaluate(
    extraction: IngredientExtraction,
    ingredient_findings: list[IngredientFinding],
    label_findings: list[LabelFinding],
    recall: RecallFinding | None = None,
) -> CaseResult:
    not_usable = [f for f in ingredient_findings if f.usability == IngredientUsability.NOT_USABLE]
    restricted = [f for f in ingredient_findings if f.usability == IngredientUsability.RESTRICTED]
    unknown = [f for f in ingredient_findings if f.usability == IngredientUsability.UNKNOWN]
    missing_labels = [lf.item for lf in label_findings if not lf.present]

    n = max(len(ingredient_findings), 1)
    n_label = max(len(label_findings), 1)
    risk = min(
        1.0,
        WEIGHT_NOT_USABLE * (len(not_usable) / n)
        + WEIGHT_RESTRICTED * (len(restricted) / n)
        + WEIGHT_UNKNOWN * (len(unknown) / n)
        + WEIGHT_LABEL * (len(missing_labels) / n_label),
    )

    actions: list[str] = []
    if not_usable:
        verdict = Verdict.BLOCKED
        actions += [f"사용불가 원료 '{f.name}' — 제외 또는 대체 필요" for f in not_usable]
    elif unknown:
        verdict = Verdict.REVIEW
        actions += [f"원료 적격성 미확인 '{f.name}' — 표준명/근거자료 확인 필요" for f in unknown]
    elif restricted or missing_labels:
        verdict = Verdict.CONDITIONAL
        actions += [
            f"사용제한 원료 '{f.name}' — {f.restriction or f.conditions or '조건 확인'}"
            for f in restricted
        ]
        if missing_labels:
            actions.append("한글표시 보완 필요 항목: " + ", ".join(missing_labels))
    else:
        verdict = Verdict.IMPORTABLE
        actions.append("결정적·조건부 위반 미발견 — 통관/검역 진행 검토 가능")

    # 회수/부적합 이력 반영: 결정적 차단이 아니면 최소 '추가검토'로 상향, 리스크 가산.
    if recall and recall.has_history:
        risk = min(1.0, risk + 0.15)
        actions.append("회수/부적합 이력 발견: " + "; ".join(recall.reasons or ["사유미상"]))
        if verdict in (Verdict.IMPORTABLE, Verdict.CONDITIONAL):
            verdict = Verdict.REVIEW

    recall_note = ""
    if recall and recall.has_history:
        recall_note = f", 회수/부적합 이력 {len(recall.reasons)}건"

    summary = (
        f"[{verdict.value}] 원료 {len(ingredient_findings)}건 "
        f"(불가 {len(not_usable)} / 제한 {len(restricted)} / 미확인 {len(unknown)}), "
        f"표시 누락 {len(missing_labels)}건{recall_note}, 리스크 {risk:.2f}."
    )

    return CaseResult(
        product_name=extraction.product_name,
        verdict=verdict,
        risk_score=round(risk, 3),
        ingredient_findings=ingredient_findings,
        label_findings=label_findings,
        recall=recall,
        actions=actions,
        summary=summary,
    )
