# 수입가능여부 검토 AI 컨설팅 — PoC (Phase 0)

성분표·한글표시(라벨)를 입력받아 **수입가능여부를 4단계로 판정**하는 동작 가능한 골격입니다.
설계서: [`../docs/수입가능여부-검토-AI컨설팅시스템-설계서.md`](../docs/수입가능여부-검토-AI컨설팅시스템-설계서.md)

> **AI는 보조 도구입니다.** 최종 수입가능여부 판단과 책임은 담당 컨설턴트에게 있으며,
> 규정·기준은 최신 식약처 고시로 재확인해야 합니다.

## 무엇을 보여주나

- **추출 스키마**: Claude `messages.parse`(구조화 출력)로 성분표 → 원료 목록 정규화
- **원료정보 API 도구**: 수입식품 원료정보 조회로 **사용가능/제한/불가** 판정 (키 없으면 MOCK)
- **룰 + 리스크 스코어링**: 한글표시 9항목 점검 + 부적합 통계 기반 가중치
- **판정**: `수입가능 / 조건부(보완필요) / 추가검토 / 수입곤란`
- **두 가지 경로**: `/verify`(코드 주도·결정적·감사가능) · `/verify/agent`(Claude 도구사용 시연)

## 빠른 시작

```bash
cd poc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 키 없이도 MOCK 모드로 구동됨

# 단위 테스트(오프라인)
python -m pytest -q          # 또는: python -m unittest

# 서버 실행
uvicorn app.main:app --reload
```

## 호출 예시

```bash
curl -s localhost:8000/health

curl -s -X POST localhost:8000/verify \
  -H 'Content-Type: application/json' \
  --data @samples/sample_request.json | python -m json.tool
```

샘플(`samples/sample_request.json`)에는 `Caffeine`(제한)이 포함되어 **조건부(보완필요)** 가
나오도록 구성되어 있습니다. `마황/ephedra`를 넣으면 **수입곤란**, 미지 원료는 **추가검토**가 됩니다.

## 동작 모드

| 키 | 없을 때 | 있을 때 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 추출이 간이 MOCK 파서로 동작 | Claude로 구조화 추출 |
| `MFDS_SERVICE_KEY`(+serviceId) | 원료조회가 내장 MOCK | 공공 API 호출(실패 시 MOCK 폴백) |

## 구조

```
poc/
├─ app/
│  ├─ main.py          # FastAPI 엔드포인트 (/health, /verify, /verify/agent)
│  ├─ config.py        # 환경설정·MOCK 판단
│  ├─ schemas.py       # Pydantic 스키마(추출/판정)
│  ├─ extraction.py    # Claude messages.parse 구조화 추출 (+MOCK)
│  ├─ mfds_api.py      # 수입식품 원료정보 클라이언트 (+MOCK 폴백)
│  ├─ tools.py         # Claude tool 정의 + 실행기
│  ├─ agent.py         # Claude 도구사용 루프(서술형 보고)
│  ├─ rules.py         # 룰 + 한글표시 체크 + 스코어링 + 판정
│  └─ verification.py  # 오케스트레이션(추출→조회→룰→판정)
├─ samples/sample_request.json
├─ tests/test_rules.py
├─ requirements.txt
└─ .env.example
```

## 알려진 한계 / 다음 단계

- 공공 API의 **정확한 엔드포인트/파라미터/응답 필드**는 데이터셋 명세로 확인 후
  `mfds_api.py`의 `lookup_ingredient`/`_parse_response` 를 보정해야 합니다.
- 첨가물 기준(사용량 한도)·농약 MRL·중금속·부적합 이력 도구는 **미구현(확장 대상)**.
- 라벨 점검은 키워드 포함 여부의 간이 휴리스틱 → Vision/OCR 정교화 필요.
- HITL 워크벤치 UI, 케이스 영속화/감사로그는 Phase 1 범위.
