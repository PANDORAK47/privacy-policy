# 수입가능여부 검토 AI 컨설팅 — PoC (Phase 0)

성분표·한글표시(라벨)를 입력받아 **수입가능여부를 4단계로 판정**하는 동작 가능한 골격입니다.
설계서: [`../docs/수입가능여부-검토-AI컨설팅시스템-설계서.md`](../docs/수입가능여부-검토-AI컨설팅시스템-설계서.md)

> **AI는 보조 도구입니다.** 최종 수입가능여부 판단과 책임은 담당 컨설턴트에게 있으며,
> 규정·기준은 최신 식약처 고시로 재확인해야 합니다.

> 🍎 **맥북에서 기존 키(ifacs-unified)로 바로 실행**하려면 → [`맥북에서_실행하기.md`](맥북에서_실행하기.md)
> (`scripts/setup_local.py`가 `SKILL 2/.mcp.json`의 키를 자동으로 읽어 `.env` 생성)
>
> 🤝 **개발자에게 실연동을 맡긴다면** → [`개발자_인수인계.md`](개발자_인수인계.md) (목표·키 위치·완료 기준 1장 요약)

## 무엇을 보여주나

- **추출 스키마**: Claude `messages.parse`(구조화 출력)로 성분표 → 원료 목록 정규화
- **공공데이터 연동(식품안전나라 OpenAPI 단일 surface)** — 4종 조회 + Claude 도구:
  - `lookup_food_ingredient` 수입식품 원료정보(사용가능/제한/조건)
  - `lookup_food_additive` 식품첨가물 기준·규격(사용기준/한도 존재 여부)
  - `lookup_pesticide_mrl` 농약 잔류허용기준(MRL)
  - `check_recall_history` 수입식품/식품 회수·판매중지(부적합/회수 이력)
- **룰 + 리스크 스코어링**: 한글표시 9항목 점검 + 회수/부적합 이력 반영 + 부적합 통계 기반 가중치
- **판정**: `수입가능 / 조건부(보완필요) / 추가검토 / 수입곤란`
- **두 경로**: `/verify`(코드 주도·결정적·감사가능) · `/verify/agent`(Claude 도구사용 시연)

## 공공데이터 연동 방식(확정)

식품안전나라 OpenAPI 한 가지로 표준화:

```
GET {base}/{인증키}/{서비스ID}/json/{start}/{end}[/{조건키}={조건값}]
base = https://openapi.foodsafetykorea.go.kr/api
응답 = { "<서비스ID>": { "RESULT": {"CODE","MSG"}, "total_count", "row": [ {...} ] } }
```

- **인증키 + 데이터셋별 서비스ID**를 `.env`에 넣으면 즉시 실연동되고, 없으면 MOCK으로 동작.
- 데이터셋(공공데이터포털 ID): 수입식품 원료정보 `15111777` · 식품첨가물 기준·규격 `15116583`
  · 농약 잔류허용기준 `15074323` · 수입식품 회수·판매중지 `15095378`(또는 식품 `15074318`).
- ⚠️ 각 데이터셋의 **요청변수명·출력필드명**은 로그인 후 명세 페이지에서 확인해야 하므로,
  `mfds_api.py`의 후보 키 목록(`_first(...)`)과 조건키를 명세에 맞춰 한 번 보정하면 된다.
  (현재는 흔한 후보명으로 방어적 매핑 + 무자료/오류 시 MOCK 폴백)

## 실연동 마무리 런북 (키·egress 설정 후 1회)

원격 실행 환경은 일회성이라 키·네트워크가 환경 설정에 따릅니다. 아래 3단계로 실연동을 완료합니다.

1. **네트워크 egress 허용** — 환경의 네트워크 허용목록에 호스트 추가
   (미추가 시 `Host not in allowlist` 403):
   - `openapi.foodsafetykorea.go.kr` (필수)
   - `api.anthropic.com` (Claude 추출/에이전트 사용 시)
   - `apis.data.go.kr` / `api.odcloud.kr` (data.go.kr REST 직접 호출 시), `unipass.customs.go.kr` (관세청, 확장)
   - 참고: <https://code.claude.com/docs/en/claude-code-on-the-web> (네트워크 설정)
2. **키·서비스ID 등록** — `.env` 또는 환경 시크릿:
   `MFDS_SERVICE_KEY`, `MFDS_INGREDIENT_SERVICE_ID`(+additive/pesticide/recall), (추출 시) `ANTHROPIC_API_KEY`
3. **자가진단 → 필드 보정** — 실제 응답 필드명을 확인하고 1회 보정:
   ```bash
   cd poc && python scripts/api_selftest.py 정제수
   # raw row[0] fields: [...]  ← 이 필드명에 맞게 app/mfds_api.py 의 _first(...) 후보 목록 또는
   #                              env MFDS_*_QUERY_FIELD(요청변수명)를 조정
   ```

## 빠른 시작

```bash
cd poc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 키 없이도 MOCK 모드로 구동됨

python -m pytest -q          # 또는: python tests/test_rules.py  (오프라인 8건)
uvicorn app.main:app --reload
```

## 워크벤치 UI

서버 실행 후 브라우저에서 **`http://localhost:8000/`** 접속 → 컨설턴트 워크벤치
(제품명·제조사·성분표·라벨 입력 → 판정/리스크/원료표/표시 체크리스트/회수이력/보완액션 시각화,
`샘플 채우기` 버튼 제공, 상단에 MOCK/실연동 배지 표시).

## API 호출 예시

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/verify \
  -H 'Content-Type: application/json' \
  --data @samples/sample_request.json | python -m json.tool
```

샘플은 `Caffeine`(제한)+`영양성분/주의사항` 표시 누락으로 **조건부(보완필요)** 가 나옵니다.
`마황/ephedra` → **수입곤란**, 미등록 원료 → **추가검토**, 회수 이력 존재 시 **추가검토로 상향**.

## 동작 모드

| 환경변수 | 없을 때 | 있을 때 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 추출이 간이 MOCK 파서 | Claude 구조화 추출 |
| `MFDS_SERVICE_KEY` + `MFDS_*_SERVICE_ID` | 해당 조회 MOCK | 식품안전나라 실호출(실패 시 MOCK 폴백) |

## 구조

```
poc/
├─ app/
│  ├─ main.py          # FastAPI (/health, /verify, /verify/agent)
│  ├─ config.py        # 환경설정·MOCK 판단(서비스ID별)
│  ├─ schemas.py       # Pydantic 스키마(추출/판정/회수)
│  ├─ extraction.py    # Claude messages.parse 구조화 추출 (+MOCK)
│  ├─ mfds_api.py      # 식품안전나라 OpenAPI 클라이언트 4종 (+MOCK 폴백)
│  ├─ tools.py         # Claude tool 4종 정의 + 실행기
│  ├─ agent.py         # Claude 도구사용 루프(서술형 보고)
│  ├─ rules.py         # 룰 + 한글표시 + 회수반영 + 스코어링 + 판정
│  └─ verification.py  # 오케스트레이션(추출→조회→회수→룰→판정)
├─ samples/sample_request.json
├─ tests/test_rules.py
├─ requirements.txt · .env.example · .gitignore
```

## 다음 단계(Phase 1)

- 서비스ID·요청/출력 필드명 **실명세 보정**(키 발급 후 1회) → 실데이터 검증
- 첨가물 **사용량 한도**·농약 **MRL 정량** 판정(현재 도구로 노출, 결정적 통합은 정량 데이터 확보 후)
- 중금속/유해물질 기준(`15058838`) 도구 추가
- 컨설턴트 워크벤치 UI · 케이스 영속화 · 감사로그
- 표준명 매핑 사전(영문↔한글↔코드)으로 원료 매칭 정확도 향상
