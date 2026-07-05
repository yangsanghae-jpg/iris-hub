# 진단툴 데이터 전수 감사

- **작성일:** 2026-07-05
- **상태:** 감사 기록 · 방향 결정 보류
- **범위:** `diagnosis-tool/{server,client}/data` 전체 JSON **102개 relpath** (server 97 + client 16, 중복 relpath 병합) 실측 스캔.
- **관련 문서**
  - 구조 평가: [`DIAGNOSIS_TOOL_DATA_STRUCTURE_EVAL_2026-07-05.md`](./DIAGNOSIS_TOOL_DATA_STRUCTURE_EVAL_2026-07-05.md) — Ch1·Q4 한정 심층
  - 목업 탐색: [`DIAGNOSIS_PACK_MGMT_MOCKUP_DISCOVERY_REPORT_2026-07-05.md`](./DIAGNOSIS_PACK_MGMT_MOCKUP_DISCOVERY_REPORT_2026-07-05.md)

> 앞선 평가는 관리 탭 관련 팩(Ch1·Q4)만 봤고, 여기서 **툴 전체**로 확장한다. 결론: **불일치는 국소가 아니라 전역**이다.

---

## 0. 요약 — 심각도순

| # | 발견 | 규모 | 심각도 |
|---|------|------|--------|
| **F1** | **i18n 표기 완전 파편화** — 같은 중국어 라벨이 키 5+종 | `label_zh`(30)·`industry_label_zh`(12)·`industry_name_cn`(9)·`label_cn`(1)·`name_zh`(3)·`name_cn`(1) + nested `label:{zh}` | 🔴 |
| **F2** | **산업 표현 3중 병렬** — 같은 8~9개 산업이 3개 디렉터리·3개 스키마·3개 코드관례 | `ch1/industry_packs`(IND_A) · `ch1_industries`(IND_A, 축소본) · `ch1_mgmt_model/industries`(code `A`, `schema_version`) | 🔴 |
| **F3** | **메타 관례 6종 난립** | `version`(34)·`_meta`(18)·`schema_version`(17)·`metadata`(15)·`meta`(4)·`name`(3) | 🟠 |
| **F4** | **server/client 사본 드리프트** — 공유 11개 중 2개 내용 상이 | `step1_5/industry_product_taxonomy_v3`(Δ-51B)·`step3/scale_profile_v3`(Δ-278B) | 🔴 |
| **F5** | **중복/유사 카탈로그** | keywords_map ×3 · drivers ×2 · sub_industry ×3 · routing 관련 7분산 | 🟠 |
| **F6** | **버전 문자열 무포맷** | `1.0`/`v1.0`/`v1`/`3.1`/`v3.0-draft`/`ch1.driver_map_v1` 혼용, version key도 `version`(59) vs `schema_version`(19) | 🟠 |
| **F7** | **루트 shape 불일치** | ch1/catalogs 안에서도 일부는 `{version,entries}` dict, 일부는 top-level list (direction/kpi/module/mvp_codes) | 🟡 |
| **F8** | **Q4 도메인 이중표현** (평가 문서 F 재확인) | A01 등 74 sub: `weights.planning`(nested) vs `planning_importance`(flat 접두) | 🟠 |
| **F9** | **크기 이상치** | `step3/process_detail_v1` **2.2MB** · step4 255KB · step1_5 234KB · q5_rec 242KB · scale_profile 197KB · routing_product_nature 126KB | 🟡 |

🔴 데이터 정합성 위험 / 🟠 유지보수·UI 특수분기 유발 / 🟡 관찰 필요

---

## 1. F1 — i18n 표기 파편화 (전수 집계)

같은 "다국어 라벨" 개념을 표현하는 키가 툴 전체에서 다음처럼 갈린다:

```
label_zh          30    industry_label_zh  12    industry_name_cn   9
label_ko          20    industry_label_ko   9    label_en           6
routing_label_zh   5    routing_label_ko    5    name_zh            3
name_en            2    label_cn 1  label_ja 1  name_cn 1  name_ko 1
industry_name_en 1  industry_name_zh 1  scale_name_zh 1  ui_label_en 1
```
- **중국어 하나가** `zh`와 `cn` 두 언어코드로, `label_`/`name_`/`industry_label_`/`industry_name_` 네 접두로 → **5+종 키**.
- 여기에 Q4의 **nested** `label:{ko,zh,en,ja}`까지 더하면 flat/nested 두 패러다임 공존.
- **UI 함의:** 라벨 하나 꺼내는 데 정규화 매핑 없이는 팩마다 분기 필요.

## 2. F2 — 산업 표현 3중 병렬 (A 산업 실측)

| 경로 | code | 스키마 특징 |
|------|------|-------------|
| `ch1/industry_packs/IND_A_project_special.json` | `IND_A` | 풀 팩 10키 (sub_profiles·default_profile·legacy_sub_profiles) |
| `ch1_industries/A_project_special.json` | `IND_A` | 축소본 4키 (industry_label_zh·sub_industries·default_profile) |
| `ch1_mgmt_model/industries/industry_A_project_eto.json` | `A` | `schema_version`·`chapter`·`industry_name_cn`·`default`·`profiles` |

→ 같은 산업 A가 **3파일·3스키마·2코드관례(`IND_A` vs `A`)**. 어느 것이 SoT인지 데이터만으로는 불명. B(semiconductor)는 여기에 `ch1_mgmt_model/industries/industry_B_semiconductor/` **하위 5파일**까지 추가로 분해돼 있어 4중.

## 3. F4 — server/client 드리프트

공유 11파일 중 2개가 내용 상이 (해시 불일치):
- `step1_5/industry_product_taxonomy_v3.json` (server가 client보다 51B 큼)
- `step3/scale_profile_v3.json` (278B 차)

나머지 9개(step4 automation_profile 포함)는 동일. **정책 부재의 증거** — 어느 쪽이 SoT인지, 동기화 규칙이 있는지 불명. 2개가 이미 갈렸다는 건 나머지도 시간문제.

## 4. F5 — 중복/유사 카탈로그

```
keywords_map   ch1/catalog/keywords_map · ch2/catalog/keywords_map · ch2/catalog/keywords_map_merged (210키 동일 규모)
drivers        ch1/catalog/drivers · ch1/catalog/drivers_catalog
sub_industry   ch1/sub_industry_aliases · ch1/sub_industry_meta · ch1/catalogs/sub_industry_codes
routing        step2/routing_product_nature · ch1/catalogs/routing_codes · industry_routing_guide(C)
               · sub_to_routing(C) · _archive/industry_routing_map(C) · _archive/routing_industry_context(C)
```
`_merged`·`_archive` 접미가 **정리 안 된 마이그레이션 잔재**를 시사.

---

## 5. 전체 인벤토리 (요약)

| 그룹 | 파일수 | 대표 shape | 메타 | 비고 |
|------|--------|-----------|------|------|
| ch1/industry_packs | 9 | dict[10] FLAT i18n | (none) | IND_* 풀 팩 |
| ch1/routing_packs | 5 | dict[7~11] FLAT | (none) | RT_* |
| ch1/catalogs | 11 | dict `{version,entries}` **또는** top-list | version/ROOTLIST | shape 혼재 |
| ch1/catalog (별도) | 4 | dict[2] | version | keywords/drivers/kpis |
| ch1_industries | 8 | dict[4~7] | (none) | 축소 산업본 (F2) |
| ch1_mgmt_model/industries | 8+5 | dict[6] `schema_version` | (none) | 관리모델 산업본 (F2) |
| ch2/catalog(+stack_library) | 17 | dict[2~11] | _meta/(none) | systems·keywords·stack |
| ch3/ch4 | 2 | dict[5~6] | _meta/version | scope·plan |
| q5 | 3 | dict | metadata/version | rec 242KB |
| step1_5 / step2 / step3 / step4 / step5_2 | ~11 | 대형 dict | metadata/_meta | 드리프트·크기이상치 집중 |
| 루트 산재 | ~10 | dict | version/_meta | industry_master·rule_params·scale_master 등 |

전체 shape·메타·i18n·버전 컬럼은 §부록 A 스크립트로 재생성 가능.

---

## 6. 해석 — 관리 탭 관점

- 앞선 평가의 "불일치 7종"은 **국소가 아니라 전역 패턴**으로 확인됨.
- 특히 **F1(i18n)·F2(산업 3중)·F4(드리프트)** 는 렌더러-only(옵션 A)로는 못 덮는다 — 데이터 자체가 "무엇이 SoT인가"를 답하지 못하기 때문.
- 관리 탭이 **편집·저장**까지 하려면, 어느 파일이 정본인지 먼저 정해져야 함. 현재는 A산업 편집 시 3파일 중 무엇을 쓰는지가 미정의.

### 우선순위 제안 (보류 — 결정 시 참고)

1. **P0 · SoT 확정** — 산업(F2)·드리프트(F4)·중복 카탈로그(F5): "정본 1파일" 지정 + 나머지 파생/아카이브 격리.
2. **P1 · 표기 정규화 어댑터** — i18n(F1)·메타(F3)·버전(F6): import 시 한 겹 정규화 (평가 문서 옵션 B).
3. **P2 · 스키마 v4** — Q4 도메인 flat 해소(F8)·shape 통일(F7): 진단툴 팀 별도 트랙.

> 방향 미결. 본 감사는 근거만 제공.

---

## 부록 A. 재생성 스크립트

```bash
cd diagnosis-tool
# 전체 인벤토리 (shape·meta·i18n·version)
python3 - <<'EOF'
import json,glob,os
for root in ['server/data','client/data']:
    for p in sorted(glob.glob(root+'/**/*.json',recursive=True)):
        try: d=json.load(open(p))
        except Exception as e: print('ERR',p,e); continue
        shape=f"dict[{len(d)}]" if isinstance(d,dict) else (f"list[{len(d)}]" if isinstance(d,list) else type(d).__name__)
        print(f"{os.path.relpath(p,root):55} {os.path.getsize(p)//1024:4}KB {shape}")
EOF

# server/client 드리프트
python3 -c "
import glob,os,hashlib
s={os.path.relpath(p,'server/data'):p for p in glob.glob('server/data/**/*.json',recursive=True)}
c={os.path.relpath(p,'client/data'):p for p in glob.glob('client/data/**/*.json',recursive=True)}
h=lambda p:hashlib.md5(open(p,'rb').read()).hexdigest()
for r in sorted(set(s)&set(c)):
    print('DRIFT' if h(s[r])!=h(c[r]) else 'same', r)
"
```

## 부록 B. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-07-05 | 초판 — 102파일 전수 감사, 발견 F1~F9, 우선순위 P0~P2 |
