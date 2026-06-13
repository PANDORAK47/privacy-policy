"""검토 결과를 보기 좋은 단독 HTML 보고서로 생성.

설치 없이 결과를 공유/시연하기 위한 산출물. (MOCK 데이터 기준 — 실연동 시 실데이터로 동일 형식)
사용: cd poc && python3 scripts/make_report.py  → samples/sample_report.html
"""

from __future__ import annotations

import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("USE_MOCK", "1")  # 보고서는 연습데이터로 생성

from app.verification import verify_case  # noqa: E402

FULL_LABEL = "제품명 식품유형 영업소 유통기한 내용량 원재료명 영양성분 보관방법 주의사항"

CASES = [
    ("① 수입가능 예시", dict(product_name="생수", ingredient_text="정제수", label_text=FULL_LABEL)),
    ("② 조건부(보완필요) 예시", dict(
        product_name="에너지 음료", manufacturer="ACME Foods",
        ingredient_text="Purified Water\nSugar\nCaffeine\nCitric Acid\nFlavor",
        label_text="제품명 식품유형 영업소 유통기한 내용량 원재료명 보관방법")),
    ("③ 추가검토 예시", dict(product_name="허브 추출물 음료",
        ingredient_text="정제수\n설탕\nMystery Herb Extract", label_text=FULL_LABEL)),
    ("④ 수입곤란 예시", dict(product_name="다이어트 보조 음료",
        ingredient_text="정제수\n설탕\n마황", label_text=FULL_LABEL)),
]

VERDICT_COLOR = {"수입가능": "#16a34a", "조건부(보완필요)": "#d97706", "추가검토": "#2563eb", "수입곤란": "#dc2626"}
PILL = {"usable": ("#dcfce7", "#166534"), "restricted": ("#fef3c7", "#92400e"),
        "not_usable": ("#fee2e2", "#991b1b"), "unknown": ("#e0e7ff", "#3730a3")}


def esc(x) -> str:
    return html.escape(str(x if x is not None else "-"))


def card(title: str, r) -> str:
    color = VERDICT_COLOR.get(r.verdict.value, "#334155")
    pct = round(r.risk_score * 100)
    rows = "".join(
        f"<tr><td>{esc(f.name)}</td>"
        f"<td><span style='background:{PILL.get(f.usability.value,('#eee','#333'))[0]};"
        f"color:{PILL.get(f.usability.value,('#eee','#333'))[1]};padding:2px 8px;border-radius:999px;font-size:11px'>"
        f"{esc(f.usability.value)}</span></td>"
        f"<td>{esc(f.restriction or f.conditions or '-')}</td><td style='color:#64748b'>{esc(f.source)}</td></tr>"
        for f in r.ingredient_findings
    )
    miss = [lf.item for lf in r.label_findings if not lf.present]
    acts = "".join(f"<li>{esc(a)}</li>" for a in r.actions)
    return f"""
    <section style="background:#fff;border-radius:12px;padding:18px;margin:14px 0;box-shadow:0 6px 18px rgba(0,0,0,.08)">
      <div style="font-size:13px;color:#64748b">{esc(title)} · {esc(r.product_name)}</div>
      <div style="display:flex;align-items:center;gap:12px;margin:8px 0">
        <span style="background:{color};color:#fff;font-weight:700;font-size:18px;padding:8px 14px;border-radius:8px">{esc(r.verdict.value)}</span>
        <span style="color:#475569;font-size:13px">리스크 {pct}%</span>
      </div>
      <div style="height:8px;background:#e2e8f0;border-radius:999px;overflow:hidden;margin-bottom:8px">
        <div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#22c55e,#eab308,#ef4444)"></div></div>
      <p style="color:#475569;font-size:13px;margin:6px 0">{esc(r.summary)}</p>
      <table style="width:100%;border-collapse:collapse;font-size:12.5px">
        <tr style="color:#64748b;text-align:left"><th style="padding:6px">원료</th><th>사용</th><th>제한/조건</th><th>근거</th></tr>
        {rows}
      </table>
      <p style="font-size:12px;color:#475569;margin-top:8px"><b>한글표시 누락:</b> {esc(', '.join(miss) if miss else '없음')}</p>
      <p style="font-size:12px;color:#475569;margin:4px 0"><b>회수/부적합 이력:</b> {esc('있음 - ' + '; '.join(r.recall.reasons) if (r.recall and r.recall.has_history) else '없음')}</p>
      <b style="font-size:12.5px">보완 액션</b><ul style="font-size:12.5px;color:#334155;margin:6px 0 0">{acts}</ul>
    </section>"""


def main() -> None:
    cards = "".join(card(t, verify_case(**kw)) for t, kw in CASES)
    doc = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>수입가능여부 검토 보고서(예시)</title></head>
<body style="font-family:-apple-system,'Malgun Gothic',sans-serif;max-width:820px;margin:0 auto;padding:20px;background:#f1f5f9">
<h1 style="color:#0f172a">📋 수입가능여부 검토 보고서 <span style="font-size:14px;color:#64748b">(예시 · 연습데이터)</span></h1>
<p style="color:#64748b;font-size:13px">성분표·한글표시 검증 → 4단계 판정. ⚠️ 본 결과는 AI 보조 사전 스크리닝이며 최종 판단·책임은 컨설턴트에게 있습니다.
실연동 시 동일 형식에 실제 식약처/공공데이터 결과가 반영됩니다.</p>
{cards}
</body></html>"""
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "sample_report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("생성:", out, f"({len(doc)} bytes)")


if __name__ == "__main__":
    main()
