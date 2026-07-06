# WORK ORDER — DIAG-SOT P4-cleanup (실행 지시서 v2)

- **발행:** 2026-07-06 · Gatekeeper(Claude) → **실행: M5 Cursor**
- **선행:** P4-core PASS · P5 PASS · repo `diagnosis-tool` `feat/diag-sot-sync`, `iris-hub` `feat/diag-sot`

---

## ⚠ 실행 규약 (반드시 읽고 그대로)

**이 문서는 실행 지시다. 단계마다 사람 승인을 기다리지 마라.**

1. 아래 **A, M1~M4를 순서대로 끝까지 실행**한다. (B, C는 §다음-사이클 — 이번엔 손대지 마라.)
2. 각 단계 끝의 **self-test를 네가 직접 실행**한다.
   - **GREEN이면 다음 단계로 즉시 진행.** 승인 대기 없음.
   - **FAIL이면 그 단계에서 멈추고**, 실패한 명령의 실제 출력과 함께 보고한다. (임의 우회·추정 수정 금지.)
3. A·M1~M4 전부 GREEN이면 → **네가 커밋·푸시·sync까지 수행** → **§제출 형식**대로 완료 패키지 1건 제출.
4. 판정(PASS)은 Gatekeeper가 제출 패키지로 post-hoc 검증한다. archive는 `_archive/` 이동이라 문제 시 복원 가능 = 사전 승인 불필요.

**절대 금지:** self-test 없이 진행 · FAIL 은폐 · 지정 외 파일 이동 · loader 코드 편집 · generator 위험 실행 · prod(C-Server) 접촉.

---

## 배치 A — archive 3후보 격리 (실행)

**대상 (P4-core에서 런타임 무참조 확정):**
1. `server/data/system_catalog.json`
2. `server/data/ch1/catalog/drivers.json`
3. `server/data/tools/diagnose_req_ch2.json`

### A-1. 무참조 재증명 (self-test ST-A1)
```bash
cd <repo>/diagnosis-tool
for b in system_catalog.json drivers.json diagnose_req_ch2.json; do
  echo "== $b =="
  grep -rn "$b" server client --include=*.py --include=*.js --include=*.mjs \
    | grep -viE "_backup|/archives/|/tests/|test_|/data/tools/|/_legacy|/scripts/|/_archive/"
done
```
**GREEN 조건:** 3개 모두 매치 0줄. (한 줄이라도 나오면 STOP + 보고.)

### A-2. 이동 (git mv)
```bash
D=_archive/diag-sot/2026-07-06
mkdir -p $D/server/data/ch1/catalog $D/server/data/tools
git mv server/data/system_catalog.json          $D/server/data/system_catalog.json
git mv server/data/ch1/catalog/drivers.json      $D/server/data/ch1/catalog/drivers.json
git mv server/data/tools/diagnose_req_ch2.json   $D/server/data/tools/diagnose_req_ch2.json
```

### A-3. ARCHIVE_MANIFEST 작성
`_archive/diag-sot/2026-07-06/ARCHIVE_MANIFEST.json` 를 아래 내용으로 생성:
```json
{
  "archived_on": "2026-07-06",
  "reason_policy": "loader_reference_status=unreferenced (P4-core 확정, 재-grep 0)",
  "restorable": true,
  "rows": [
    {"path": "server/data/system_catalog.json",
     "archive_path": "_archive/diag-sot/2026-07-06/server/data/system_catalog.json",
     "archive_reason": "legacy_duplicate_unreferenced",
     "live_replacement": "server/data/ch2/catalog/systems_catalog.json",
     "loader_reference_proof": "ST-A1 grep 0 matches"},
    {"path": "server/data/ch1/catalog/drivers.json",
     "archive_path": "_archive/diag-sot/2026-07-06/server/data/ch1/catalog/drivers.json",
     "archive_reason": "legacy_duplicate_unreferenced",
     "live_replacement": "server/data/ch1/catalog/drivers_catalog.json",
     "loader_reference_proof": "ST-A1 grep 0 matches"},
    {"path": "server/data/tools/diagnose_req_ch2.json",
     "archive_path": "_archive/diag-sot/2026-07-06/server/data/tools/diagnose_req_ch2.json",
     "archive_reason": "tool_fixture",
     "live_replacement": null,
     "loader_reference_proof": "ST-A1 grep 0 matches"}
  ]
}
```

### A-4. builder에 archived 반영 (정확한 수정)
`scripts/data_poc/p4_build_manifest_lineage.py` 를 수정해, 이동으로 member가 사라진 3 legacy GROUP이 **빈 팩으로 증발하지 않고** `archived`로 남게 한다.

- 파일 상단(ARCHIVE 로드): `dxpacks` 로드 직후에 추가
  ```python
  ARCHIVE_MF = "_archive/diag-sot/2026-07-06/ARCHIVE_MANIFEST.json"
  archived = {}
  if os.path.isfile(ARCHIVE_MF):
      for r in json.load(open(ARCHIVE_MF))["rows"]:
          archived[r["path"]] = r
  ```
- 팩 루프(약 L188 `members = [m for m in members if m in rows]` 직전)에서, 원본 members 중 archived에 있는 건 보존:
  ```python
  orig_members = list(members)
  members = [m for m in orig_members if m in rows]
  arch_hit = [m for m in orig_members if m in archived]
  ```
- row 조립부에서, `arch_hit`가 있고 `members`가 비면:
  ```python
  if arch_hit and not members:
      row["coverage_status"] = "archived"
      row["member_paths"] = [archived[m]["archive_path"] for m in arch_hit]
      row["member_count"] = len(arch_hit)
      row["loader_reference_status"] = "archived_unreferenced"
      row["lineage_status"] = "archived"
      row["archive_reason"] = archived[arch_hit[0]]["archive_reason"]
      row["runtime_loader_paths"] = []
  ```
  (기존 `covered_paths.update(members)` 는 `members` 기준 유지 — archived는 live coverage에서 제외되어 인벤토리 109와 정합.)

### A-5. self-test ST-A2 (재생성·게이트)
```bash
python3 scripts/data_poc/p4_loader_scan.py
python3 scripts/data_poc/p4_build_manifest_lineage.py
python3 - <<'PY'
import json
inv=json.load(open('docs/diag-sot/reports/P4_INVENTORY.json'))
man=json.load(open('scripts/data_poc/DIAG_SOT_MANIFEST.json'))
assert inv['meta']['runtime_candidate_count']==109, inv['meta']['runtime_candidate_count']
assert man['meta']['orphan_live_packs']==[], man['meta']['orphan_live_packs']
arch=[p['pack_id'] for p in man['packs'] if p['coverage_status']=='archived']
assert set(arch)=={'system_catalog_root_legacy','ch1_drivers_legacy','tools_diagnose_req_fixture'}, arch
# live coverage 100% for remaining 109
assert man['meta']['covered_runtime_paths']==109, man['meta']['covered_runtime_paths']
print('ST-A2 GREEN: inventory 109, archived 3, orphan 0, covered 109')
PY
```
**GREEN 조건:** 스크립트가 `ST-A2 GREEN` 출력.

### A-6. 회귀 self-test ST-A3
```bash
# golden 회귀 + flag-off delta (레포의 기존 게이트 러너 사용 — P3b에서 쓰던 것)
<golden/delta test 명령>   # 예: python3 -m pytest server/tests -k "golden or flag_off" -q
```
**GREEN 조건:** 무변경/통과. (러너 경로 불명확하면 P3b_GATE_VERDICT의 명령을 그대로 재사용. 그래도 없으면 STOP + 보고.)

---

## M1 — q1/q5 generated_path null 보강

`scripts/data_poc/p4_build_manifest_lineage.py`:
- `DX_ARTIFACTS = {` 정의 근처에 추가:
  ```python
  CLIENT_GENERATED = {
      "q1_industry_product_taxonomy": "client/data/step1_5/industry_product_taxonomy_v3.json",
      "q5_recommendation_by_subindustry": "client/data/q5/recommendation_by_subindustry_v1.json",
  }
  ```
- L213 `row["generated_path"] = (dp or {}).get("generated_path")` →
  ```python
  row["generated_path"] = (dp or {}).get("generated_path") or CLIENT_GENERATED.get(pid)
  ```
**self-test:** 재생성 후 두 팩 `generated_path`가 non-null.
```bash
python3 -c "import json;m=json.load(open('scripts/data_poc/DIAG_SOT_MANIFEST.json'));print([(p['pack_id'],p.get('generated_path')) for p in m['packs'] if p['pack_id'] in ('q1_industry_product_taxonomy','q5_recommendation_by_subindustry')])"
```

## M2 — related_issues 과매칭 축소 (iris-hub)

`iris-hub/src/store/diag_sot.py` `related_issues`:
- `fragments = {pack_id, *dx_paths}` 아래 **`fragments.add(Path(p).stem)` 루프(L114-115) 삭제.** (stem 부분매칭이 ch3/ch6 교차오염 유발.)
- 매칭을 pack_id **정확 일치** 또는 dx artifact **전체 경로** 포함으로 한정(이미 `dx_paths`가 full path이므로 stem만 제거하면 됨).
**self-test:** `python3 -m py_compile src/store/diag_sot.py` OK. (기능 회귀는 M3 스크린샷 때 SoT 탭 육안.)

## M3 — P5 UI 스크린샷 1장

라이브 `http://127.0.0.1:8765` → 🔧 진단툴 → **진실원(SoT) 관리** 라디오 → dx 그리드 + lineage 패널이 보이는 상태로 스크린샷 → `iris-hub/docs/design/diag-sot/assets/p5_sot_tab.png` 저장.
(M2 반영 반영 위해 저장 전 `sync-iris-hub.sh` 후 브라우저 새로고침.)

## M4 — ch1_mgmt_model 주석 정정 (builder)

`p4_build_manifest_lineage.py` 의 `ch1_mgmt_model_industries` GROUP notes:
- 현재: `"...needs live/unknown split at migration"`
- →: `"os.listdir(compose.py:311) 전량 로드 = live_indirect; unknown 없음. 산업 선택별 도달은 런타임 분기이나 파일 자체는 모두 live"`
**self-test:** 재생성 후 해당 팩 notes 반영 확인.

---

## 최종 self-test (커밋 전, 전부 GREEN 필수)

| # | 테스트 | GREEN |
|---|---|---|
| ST-A1 | archive 3후보 무참조 grep | 0 매치 |
| ST-A2 | 재생성 인벤토리 109·archived 3·orphan 0·covered 109 | 스크립트 통과 |
| ST-A3 | golden+flag-off 회귀 | 무변경 |
| ST-M1 | q1/q5 generated_path non-null | 확인 |
| ST-M2 | store py_compile | OK |
| ST-M3 | SoT 탭 스크린샷 존재 | 파일 저장 |
| ST-M4 | ch1_mgmt_model notes 정정 | 확인 |

## 커밋·푸시·sync (네가 수행)

- **diagnosis-tool** `feat/diag-sot-sync`: A(이동+ARCHIVE_MANIFEST)+A4 builder+M1+M4+재생성 산출물.
  커밋: `[DIAG-SOT][P4-cleanup] 배치A archive 3후보 격리 + MANIFEST/inventory 재생성(109) + MINOR(generated_path·mgmt_model 주석)`
- **iris-hub** `feat/diag-sot`: M2(store)+M3(스크린샷).
  커밋: `[DIAG-SOT][P4-cleanup] related_issues 정밀화 + P5 SoT 탭 스크린샷`
- 두 repo push + `sync-iris-hub.sh` 실행(:8765 200 확인).
- 커밋 메시지 끝에: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

## 제출 형식 (M5 → Gatekeeper, 1건)

```
[P4-cleanup 배치A + MINOR 완료]
- self-test: ST-A1..M4 전부 GREEN (각 핵심 출력 1~2줄)
- diagnosis-tool: <커밋 해시> / 인벤토리 112→109 / archived 3
- iris-hub: <커밋 해시> / :8765 <code>
- 스크린샷: docs/design/diag-sot/assets/p5_sot_tab.png
- 변경 파일 목록
```
FAIL 시: 실패 ST 번호 + 실제 출력만. 진행 중단 상태로 보고.

---

## 다음 사이클 (이번 지시서 범위 아님 — 손대지 마라)

- **배치 B (residual byte-0):** ch4_plan_defaults·ch0_exec_subs·step5_2 → **팩별 schema draft가 선행**(Gatekeeper 설계). draft 없이 byte-0 authoring 금지.
- **배치 C (generator 은퇴):** 7개 generator hash 비교 → **은퇴 지시서 별도 발행** 후.
- 두 배치는 A+MINOR 제출·PASS 후 Gatekeeper가 다음 지시서를 낸다.
