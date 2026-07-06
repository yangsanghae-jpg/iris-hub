# 진단툴 진실원 관리 탭 — 재설계 가이드 (Gatekeeper)

- **작성:** 2026-07-06 · Gatekeeper(Claude) · **구현: M5 Cursor**
- **성격:** 방향·제약·수용기준. 구현 세부(Streamlit 위젯 선택 등)는 Cursor 재량.
- **상위 규정:** 아래 §1~2가 `DIAGNOSIS_TOOL_TAB_V2_SPEC.md`(M5 초안)의 **아키텍처·UX 결정을 교정**한다. 충돌 시 본 가이드 우선. 대체 대상 = 현 `diagnosis_sot.py`(P5 read-only 뷰).

---

## 1. 확정 결정 (변경 불가 — 여기서 어긋나지 마라)

### 1-1. SoT 저장 아키텍처
- **정본(편집 대상) = git-tracked JSON dx** (`diagnosis-tool/scripts/data_poc/_p*/dx_*.json`). 쓰기는 오직 여기로.
- **"DB" = JSON에서 로드 시 재생성하는 read-only 파생 인덱스**(SQLite in-memory 또는 DuckDB). **절대 쓰기 대상 아님.** 언제 삭제해도 JSON에서 재생성.
- 이유: 바이너리 DB를 정본화하면 git-diff 감사성·단일정본·byte-0 일관성을 잃음. DB의 유일 이점(FK/PK 강제·SQL)은 검증 스크립트 + 인메모리 인덱스로 대체.
- 반영 체인은 기존 그대로: **편집(dx JSON) → byte-0 재생성 → runtime JSON**. 신설 없음.

### 1-2. P5 MANIFEST/LINEAGE
- **뷰로는 폐기, 데이터층으로는 흡수.** 별도 lineage 화면 만들지 마라.
- MANIFEST → 팩 목록·상태. LINEAGE `pack_level_lineage` → 그리드 "어디에 반영" 컬럼·요약.
- `diagnosis_sot.py`의 read-only 로더(`src/store/diag_sot.py`)는 **재사용**(폐기 아님). 로드 대상에 dx JSON 파싱 추가.

### 1-3. 무접촉 규율
- runtime `server/data/**` 직접 편집 금지(재생성 결과물). prod·`DIAG_SOT_DEV` 규율 유지.

### 1-4. 편집 범위 (확정 — 2026-07-06)
- **편집 대상 = Q1~Q5 팩만.** 직관적·단순한 수치팩이라 UX·반영배선 검증에 적합.
  - `q1_industry_product_taxonomy` · `q2_routing_product_nature` · `q3_scale_profile` · `q4_automation_profile` · `q5_recommendation_by_subindustry` · `q5_axes` (+ `step2_route_diagram` · `step3_residual` 등 Q 인접 residual).
- **A1/A2 (Ch0~Ch6 리포트/제안 콘텐츠 팩) = 편집 보류.** 아직 챕터별 이견 여지 있음(구조·내용 미확정). **목록에는 표시하되 read-only 잠금** + 배지 `편집 보류 (이견 조정 중)`. 이견 해소 후 별도 확대.
  - 해당: `ch0_exec_subs` · `ch1_mgmt_model_*` · `ch2_systems_catalog` · `ch2_card_masters` · `ch2_overlays` · `ch3_scope_catalog` · `ch4_plan_defaults` · `ch6_roi_logic_catalog` · `step5_2_management_analysis` 등.
- **척추(registry: `industry_master`·`industry_codes`·`sub_industry_codes`) = 별도 판단.** 고영향·cascade라 이번 편집 범위 제외, 현재는 read-only 표시. (Q가 참조하므로 상태 가시화는 유지.)

---

## 2. UX 방향 (목업 기준 — 이 골격을 지켜라)

> 화면은 **이야기로 읽혀야 한다: 고른다 → 고친다 → 반영을 눈으로 확인.** 엔지니어 용어(Zone, hash, dirty, git HEAD, DB컬럼)를 **표면에 노출하지 마라.**

### 2-1. 상단 상태 스트립 (친절 요약)
- 예: `진실원 42팩 · 2,180행 · 아직 리포트에 안 넣은 팩 2 · 마지막 반영 오늘 09:34`
- 금지: `dx_sot.db`, `dirty`, `import e8bd8aa`, 해시 문자열을 그대로 노출.

### 2-2. 레이아웃 — 그리드가 전폭 작업공간 (2026-07-06 개정)
> 1차 구현에서 좌목록+우그리드 2단이 Streamlit 좁은 폭에서 그리드를 짓눌러 `값`·`반영`이 잘림. **그리드가 주(작업공간), 목록은 종(선택기)** 로 재배치한다.
- **팩 선택기 = 상단 가로 스트립.** 편집 대상이 Q팩(~8개)뿐이라 가로로 짧다. 각 팩 칩: `한글명` + 상태 점(녹색=반영됨/주황=미반영) + 선택 하이라이트. 세로 좌측 컬럼 폐지.
- **편집 그리드 = 그 아래 전폭**(`use_container_width`, wide). 잘림 없어야 함.
- **전체 39팩 상태**(A1/A2·척추 포함)는 상단 접이식 "전체 팩 상태" 요약으로. 작업공간 점유 금지. (요구 #1 상태 가시화는 여기서 충족.)
- 금지: 팩을 개별 nav 항목/서브탭으로 만들기(메인 nav와 충돌·산만).

### 2-3. 우측 3요소
1. **팩 제목 + 한 줄 설명** (평문). 예: "Q3 규모 프로필 — 세부산업별 규모 진단 가중치와 권장 성숙도".
2. **반영 흐름 배너** = 요구 #2의 주인공. `여기서 편집 → 실제 진단 리포트` + 상태:
   - 일치: `✓ 리포트와 일치` (녹색)
   - 편집 후: `⚠ 수정됨 · 아직 반영 안 됨` (주황) + 액션 `저장하고 리포트에 반영`
3. **편집 그리드 = 3컬럼만**: `항목(무슨 뜻인지)` | `값` | `어디에 반영`
   - 항목 셀: 한글 의미(주) + 부제(예: "0~1 사이 값", "L1~L5 등급").
   - 값 셀: 편집 가능=입력칸 / 잠금=🔒 + 회색.
   - 반영 셀: 편집 필드만 `→ Q3 권장 등급`처럼 소비 지점. 잘리지 않게 전폭 확보.
   - **식별자(세부산업 코드·산업명·항목 경로)를 컬럼으로 매 행 반복 금지.** 이게 1차 구현 협소의 주원인(`A01 플랜트·EPC 제작` 반복). 세부산업은 상단 필터/그룹 헤더로 **컨텍스트화**, 그리드 본문엔 해당 세부산업의 `항목\|값\|반영`만.
   - **`세부산업/산업명/DB컬럼/json_pointer 원문` = 기본 화면 제거.** 필요 시 "개발자 보기" 토글 뒤로.

### 2-4. 액션 버튼
`되돌리기` · `검증`(FK·범위·커버리지·issue) · `저장하고 리포트에 반영`(dx UPDATE → byte-0 재생성 → 상태 갱신). primary는 1개만.

### 2-5. 카피 규율
사람 말·한글 우선·문장부호 없는 짧은 버튼. 코드/식별자는 부제·툴팁으로. "성공적으로"·"!"·명령형 영어 금지.

---

## 3. 필드 잠금 규칙 — 키 고정, 내용만 수정 (강화 2026-07-06)

> **모든 데이터를 수정하게 두지 않는다.** 실수 방지를 위해 **키/식별자는 잠금 고정, 값·내용만 편집.** 기본은 잠금, 명시적 화이트리스트만 편집 허용(fail-safe).

| 유형 | 예 | 처리 |
|---|---|---|
| PK(식별자) | `sub_code`, `field_path`, `system_id` | 🔒 잠금 고정 — 편집 위젯 자체를 안 줌(회색 텍스트). 컬럼 반복 대신 컨텍스트로 |
| FK(참조) | `parent_code`, `industry_code` | 🔒 잠금 고정 |
| provenance | `source_json_pointer`, `source_ref` | 🔒 잠금 "추적·재현용" |
| manifest | `pack_id`, `phase_introduced` | 🔒 잠금 |
| **편집 가능(화이트리스트)** | `label_ko/en/…`, `weight`, `value_num/text`, 권장등급 등 비즈니스 값 | 입력칸 |

- **기본 정책 = 잠금.** 편집 허용 필드는 팩타입별 화이트리스트에 명시된 것만. 목록에 없으면 자동 잠금(새 필드가 실수로 편집되는 것 방지).
- 팩 타입별 화이트리스트는 **`dx_*` 스키마 + P1_SCHEMA 승인본**에서 팩타입별 JSON으로 관리(하드코딩 금지). Cursor가 이 매핑 파일을 설계·산출.
- 저장 시 서버측에서도 화이트리스트 재검증(UI 잠금만 믿지 않음).

---

## 4. Cursor 재량 (내가 지정 안 함)
- Streamlit 컴포넌트 선택(`st.data_editor` column_config vs 커스텀), 파생 인덱스 구현(SQLite in-mem vs DuckDB vs dict), 상태 캐싱, 저장 트랜잭션 방식, 그룹핑 상세.
- 단, §1~3 제약과 §5 수용기준을 위반하지 않는 선에서.

## 5. 수용기준 (Gatekeeper 검증 항목 — 구현 후 이걸로 판정)
- [ ] 표면에 Zone/hash/dirty/git HEAD/DB컬럼 **미노출** (개발자 토글 제외).
- [ ] **팩 선택기 상단 가로 · 그리드 전폭 · `값`/`반영` 잘림 없음.**
- [ ] **그리드 본문에 세부산업/산업명 식별자 매행 반복 없음**(컨텍스트/필터로).
- [ ] 팩 선택 시 그리드 교체 동작 · 전체 39팩 상태는 접이식 요약.
- [ ] 값 편집 → 반영 배너 즉시 `미반영`으로 · 반영 후 `일치`로.
- [ ] **키/식별자 편집 위젯 미제공(고정)** · 편집=화이트리스트 필드만 · 저장 시 서버측 재검증.
- [ ] 쓰기 경로가 **dx JSON에만** (runtime/파생인덱스 직접 쓰기 0 — 코드 grep).
- [ ] 파생 인덱스는 JSON에서 재생성(정본 아님)임이 코드로 확인.
- [ ] MANIFEST/LINEAGE 재사용(목록·반영컬럼 소스).
- [ ] 데이터 미배치 시 graceful 안내 · 라이브 sync 반영.

## 6. 파일럿 → 확산

### 6-1. 파일럿 q3 — ✅ PASS (Gatekeeper 독립 검증 2026-07-06)
- 파생 인덱스 in-mem SQLite(JSON 재생성, 정본 아님) ✅ · 저장=dx JSON 쓰기+runtime 재생성 실제 배선 ✅
- **byte-0 충실성 독립 확인:** rebuild(dx)==커밋 runtime 이 q2/q3/q4 전건 MATCH.
- 잠금 whitelist(`field_locks.json`) + 저장 전 서버측 재검증(`validate_q3_edits`) ✅

### 6-2. 확산 전 필수 수정 1건 (BLOCKER)
- **server/client 미러 동시 재생성.** 현재 `save`가 `member_paths[0]`(server)만 재생성 → `client/data/step3/scale_profile_v3.json`(질문지 UI가 읽음) stale, parity 붕괴, 반영 배너가 server만 보고 "일치" 오표기.
  - 수정: 저장 시 dx의 `_server`·`_client` 미러 행 동시 편집 + 두 runtime(server·client) 재생성. `runtime_sync_status`도 두 경로 모두 byte-0 확인 후 "일치".
- 이 수정을 q3에서 먼저 끝내고 확산(안 그러면 결함을 Q2/Q4에 복제).

### 6-3. 확산 범위 = Q2·Q4 (dx_q_matrix 동일 구조)
- Q2 routing · Q4 automation은 q3와 **동일 dx_q_matrix 구조 + byte-0 이미 MATCH** → rebuild 그대로 적용.
- **게이트(팩별):** 편집 열기 전 "무편집 상태 synced"(rebuild==runtime) 확인. mismatch면 열지 마라.

### 6-4. Q1·Q5 = 별건 (구조 상이)
- q1(taxonomy)·q5(recommendation)는 **dx_q_matrix에 없음** → `rebuild_q_pack_payload` 미적용. 구조별 rebuild + byte-0 증명 **별도** 후 편집 개방. Q2/Q4 확산에 끼워넣지 마라.

### 6-5. A1/A2·척추
- read-only 표시만(편집 미착수). §1-4.

### 6-6. MINOR (비차단)
- iris-hub가 p1b build 알고리즘을 **재구현**(`rebuild_q_pack_payload`) — diagnosis-tool build_data와 별개 복제. sync 바이트체크가 drift를 잡지만, 장기적으로 공유 모듈/원 파이프라인 호출이 이상적. 추적만.

## 7. 구현 순서 (권장, Cursor 조정 가능)
S0 파생 인덱스(JSON→in-mem) + 팩타입 화이트리스트 매핑 → S1 상단 상태 스트립 + 가로 팩 선택기 → S2 전폭 편집 그리드(3컬럼·키 고정·세부산업 필터 컨텍스트화) → S3 반영 배너 + 저장→byte-0 재생성 배선 → S4 검증 버튼 → S5 sync·수용기준 자체점검 → 제출.

## 8. 제출 형식 (Cursor → Gatekeeper)
`변경 파일 · 수용기준 자체점검 결과 · 스크린샷(목록+편집+미반영/일치 두 상태) · dx-only write grep · 파생인덱스 재생성 증명 · 커밋 해시 · :8765 코드`.
