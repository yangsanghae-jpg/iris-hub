# A1 Ch3 G산업 공정 상세 데이터팩 v0.3 — 의약·바이오·의료 제조
> 파일명: `a1_ch3_G_process_detail_runtime_datapack_ko_zh_v0_3_2026-07-06.md`  
> 작성일: 2026-07-06  
> 범위: G01~G09, ko/zh only  
> 목적: A1 Ch3 pflow V3.023용 G산업 공정 상세 데이터팩 초안  
> 주의: JSON·코드·스크립트 적용 대상 아님. MD 리팩 산출물만 작성.
## 0. 작성 기준

본 파일은 B산업 리팩 지시서의 v0.3 구조를 G산업에 적용한 MD 초안이다. Ch3가 실제 소비하는 `module`, `role`, `gate_for`, `loop_hint`, `trace_keys`, `operations`, `control_points_detail.category`를 포함한다.

`control_points_ko/zh` 별도 섹션은 작성하지 않는다. 필요한 경우 변환 규칙에서 `control_points_detail_ko/zh`를 이용해 자동 생성한다.
## 0.1 G산업 공통 해석

G산업은 원료의약품, 완제의약품, 무균·주사제, 액제·외용제, 바이오의약품, 백신·세포·유전자치료제, CDMO, 의료기기·소모품, IVD·진단제품을 포함한다. 공통적으로 GMP/ISO 13485 등 규제 기반 운영, eBR/DHR, Deviation/CAPA, QA Release, Data Integrity, Lot/Serial/UDI/Chain of Identity 추적이 핵심이다. 효율보다 규정준수와 환자 안전이 우선이며, Ch3 공정도는 단순 제조 흐름이 아니라 규제 증적과 품질 게이트를 함께 보여야 한다.
## 0.2 slug 목록

| code | legacy_slug | name_ko | name_zh | routing | preset_id |
|---|---|---|---|---|---|
| G01 | `api` | 원료의약품 (API) | 原料药（API） | RT_REGULATED_BATCH | regulated_batch_v1 |
| G02 | `solid_dosage` | 고형제 완제의약품 | 固体制剂 | RT_REGULATED_BATCH_LINE | solid_dosage_v1 |
| G03 | `sterile_injectable` | 무균·주사제 | 无菌制剂与注射剂 | RT_ASEPTIC_BATCH | aseptic_fill_finish_v1 |
| G04 | `liquid_topical_inhalation` | 액제·외용제·흡입제 | 液体制剂/外用制剂/吸入制剂 | RT_REGULATED_BATCH_PACK | liquid_topical_pack_v1 |
| G05 | `biologics` | 바이오의약품 | 生物制品 | RT_BIOPROCESS_BATCH | bioprocess_upstream_downstream_v1 |
| G06 | `vaccine_cell_gene_therapy` | 백신·세포·유전자치료제 | 疫苗/细胞与基因治疗 | RT_ATMP_COLD_CHAIN | chain_identity_coldchain_v1 |
| G07 | `pharma_cdmo` | 의약 CDMO·다제품 생산 | 医药CDMO与多产品生产 | RT_MULTI_PRODUCT_CAMPAIGN | multi_product_cdmo_v1 |
| G08 | `medical_consumables` | 의료기기·의료용 소모품 | 医疗器械与医用耗材 | RT_DEVICE_LINE_STERILE | medical_device_dhr_v1 |
| G09 | `ivd_diagnostics` | IVD·진단제품 | IVD与诊断产品 | RT_REAGENT_KIT_DIAGNOSTIC | ivd_reagent_kit_v1 |

## 0.3 G산업 Ch3 표현 원칙

- API·완제·액제는 `Material → Weighing/Recipe → Batch Production → IPC/Lab Gate → Packaging → QA Release` 구조로 표현한다.
- 무균·주사제는 `CIP/SIP → Aseptic Filling → EM/Sterility Gate → Batch Closure`를 명시한다.
- 바이오·백신·ATMP는 `Cell/Seed/Identity → Upstream/Downstream → CQA/Potency Gate → Cold Chain/Release`를 명시한다.
- CDMO는 `Tech Transfer → Campaign/Changeover → Customer Release → Audit Pack`을 별도 관리 축으로 둔다.
- 의료기기·IVD는 `DMR/DHR 또는 eBR → UDI/Kit genealogy → Sterilization/Performance Gate → Recall Trace`를 표현한다.
- `trace_keys`는 slug별 `data_capture_points`의 부분집합으로만 작성한다.
- en/ja 공정·관리점 섹션은 작성하지 않는다.

---

## G01 `api` — 원료의약품 (API) / 原料药（API）

```yaml
code: "G01"
legacy_slug: "api"
industry_group: "G"
industry_name_ko: "원료의약품 (API)"
industry_name_zh: "原料药（API）"
routing: "RT_REGULATED_BATCH"
preset_id: "regulated_batch_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - supplier_lot
  - material_status
  - recipe_id
  - batch_id
  - reactor_id
  - equipment_id
  - process_parameter
  - ipc_sample_id
  - lab_result_id
  - impurity_profile
  - solvent_recovery_lot
  - deviation_id
  - ebr_id
  - qa_release_id
  - coa_id
```

### G01.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | 원료 입고·격리 | 원료 입고·격리 단계에서 액체·고체 원료의 공급업체 Lot 번호, COA(Certificate of Analysis)를 eBR에 등록하고 격리 상태(Quarantine)로 전환한다. 저장 탱크(SUS/GL 재질, 교반·질소 퍼지 가능) 또는 드럼/파이버 드럼 단위로 Lot 추적을 시작한다. 입고 시 중량·순도·외관 1차 검수를 수행하고, 승인 전까지 물리적·전자적 이중 격리 상태를 유지한다. |
| 2 | 원료 샘플링·QC 승인 | QC 실험실에서 각 원료 Lot 대표 시료를 채취하여 HPLC(순도·개별 불순물), GC(잔류 용매), KF(수분), 중금속 시험을 수행한다. ALCOA+ 원칙에 따라 분석 결과를 LIMS에 기록하고, 적합 판정 시 ERP/MES에서 Released 상태로 전환한다. 부적합 시 Deviation 등록 후 격리 유지 또는 반품 처리한다. |
| 3 | 계량·투입 준비 | Recipe(Master Batch Record)에 지정된 양의 원료·용매·촉매를 청정 환경의 계량실에서 정밀 저울(0.01g~1kg 분해능)로 계량하고, 전자서명 및 이중 확인(Double Check)으로 정합성을 검증한다. 용매류는 질량 유량계(Coriolis)로 계량하여 Reactor Charging Port로 이송한다. 투입 순서와 속도가 반응에 결정적이므로 Recipe에 투입 시퀀스를 고정한다. |
| 4 | 반응·합성 | 원료를 GL 재킷 반응기(100L~20,000L, Hastelloy/SUS316L)에 투입하고, 교반 속도(50~500 RPM), 반응 온도(-20°C~250°C), 압력(진공~10 bar)을 DCS/PLC로 자동 제어한다. 핵심 CPP(Critical Process Parameters)인 반응 시간·온도 프로파일·pH·교반 토크를 1초~1분 간격으로 SCADA에 기록한다. IPC(In-Process Control) 시료를 채취하여 TLC/IR/HPLC로 반응 진행률을 확인하고, 목표 전환율 도달 시 Quenching 또는 냉각 후 다음 단계로 이송한다. 각 Batch의 반응 조건이 Recipe에 설정된 범위 내에 있는지 PAT(ReactIR, FBRM)로 실시간 모니터링한다. |
| 5 | 분리·세척 | 반응 혼합물을 원심분리기(Peeler Centrifuge, SUS316L, 500~1,500 G) 또는 Nutsche Filter Dryer(NFD)로 고액 분리한다. 분리된 Cake를 세정 용매(MeOH, EtOH, Acetone 등)로 1~3회 세척하여 잔류 원료·불순물을 제거한다. 세척액의 부피·온도·횟수를 eBR에 기록하고, 세척 종료 시점은 여액의 HPLC 순도 또는 굴절률로 판정한다. 용매 회수 시스템으로 사용 후 용매를 증류 재활용하며, 회수 Lot 번호를 부여하여 교차오염을 추적한다. |
| 6 | 결정화·건조 | 정제된 API 용액을 결정조(Crystallizer, GL 재킷, 교반기 부착)에서 냉각(예: 60°C→5°C, 1~2°C/min) 또는 반용매(Anti-Solvent) 투입으로 결정화한다. 결정 입도 분포(PSD)는 FBRM(Focused Beam Reflectance Measurement)으로 실시간 모니터링하고, 목표 PSD 달성 시 슬러리를 Nutsche Filter Dryer로 이송한다. 진공 건조(40~80°C, -0.08~-0.09 MPa) 또는 유동층 건조(Fludized Bed Dryer, 입구 온도 60~100°C)로 목표 LOD(Loss on Drying, 0.5% 이하)까지 건조한다. 건조 온도·진공도·시간이 LOD와 결정형(Polymorph)에 직접 영향을 미치므로 엄격히 통제한다. |
| 7 | 분쇄·체질·블렌딩 | 건조된 API를 Pin Mill(회전속도 5,000~15,000 RPM) 또는 Jet Mill(분쇄 압력 6~8 bar)로 목표 입도(D90: 10~200μm)로 분쇄한다. 체질(Sieve, Mesh #20~#100)을 통해 과립·미분을 분급하고, 블렌더(V-Blender, 15~30분, 10~20 RPM)로 다수 Batch 간 균질성을 확보한다. 블렌딩 종료 후 대표 시료를 채취하여 Assay, Impurity Profile, PSD를 QC에서 확인한다. 분쇄 시 발생하는 발열과 정전기로 인한 분진 폭발 위험을 관리한다(질소 분위기, 접지). |
| 8 | IPC·시험·일탈 검토 | 3~7단계에서 채취한 모든 IPC 시료와 완제품 시료의 QC 시험 결과(순도 ≥99.0%, 개별 불순물 ≤0.1%~0.5%, 중금속 ≤10~20 ppm, 잔류 용매 ICH Q3C 기준)를 LIMS에서 집계한다. Deviation(온도 이탈, 수율 부족, 불순물 Out-of-Spec)을 eBR에 연동하여 Impact Assessment를 수행하고, 필요시 CAPA(Corrective and Preventive Action)를 등록한다. 모든 시험 결과와 Deviation 처리가 완료되어야 QA 검토가 진행될 수 있음을 Gate 조건으로 설정한다. |
| 9 | 포장·라벨링 | 승인된 API를 PE Liner가 있는 Fiber Drum(10~50 kg) 또는 Aluminium Bag(1~5 kg)에 포장하고, 실링(Heat Sealing + Tape) 후 외부 라벨에 Product Name, Batch/Lot No., Net Weight, Manufacturing/Expiry Date, Storage Condition을 부착한다. 포장 Line Clearance로 전 Lot 잔류물 혼입을 방지하고, 각 포장 단위에 고유 Serial Number를 부여한다. 포장 완료 후 중량·실링 상태·라벨 정확성을 100% 검수한다. |
| 10 | QA Release·CoA 발행 | QA Reviewer가 eBR 전 항목(원료 Lot 추적 → 반응 파라미터 → IPC/Lab 결과 → Deviation/CAPA → 포장 기록)을 검토하고 전자서명으로 Release를 승인한다. LIMS에서 최종 COA(Certificate of Analysis)를 자동 생성하여 (순도, 불순물 프로파일, 잔류 용매, 중금속, PSD, 수분, 미생물 한도)를 기재한다. 고객/규제기관 제출용 CoA Package를 생성하고, Release된 API는 ERP에 완제 재고로 등록된다. |

### G01.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 原料收货与隔离 | 在原料收货与隔离阶段，将液体/固体原料的供应商批号、COA注册到eBR中，并切换为隔离状态(Quarantine)。通过储罐(SUS/GL材质，可搅拌/氮气吹扫)或桶/纤维桶单位进行批号追踪。收货时执行重量、纯度、外观初步检查，在批准前保持物理和电子双重隔离。 |
| 2 | 原料取样与QC批准 | QC实验室从每个原料批次采集代表性样品，执行HPLC(纯度与单个杂质)、GC(残留溶剂)、KF(水分)、重金属检测。按照ALCOA+原则将分析结果记录到LIMS，判定合格后在ERP/MES中切换为Released状态。不合格时注册偏差后保持隔离或退货处理。 |
| 3 | 称量与投料准备 | 按配方(Master Batch Record)指定量，在洁净环境的称量室使用精密天平(分辨率0.01g~1kg)称量原料/溶剂/催化剂，通过电子签名和双人复核(Double Check)验证一致性。溶剂类通过质量流量计(Coriolis)称量后输送至反应器加料口。投料顺序和速率对反应至关重要，投料序列固定在配方中。 |
| 4 | 反应与合成 | 将原料投入GL夹套反应器(100L~20,000L, Hastelloy/SUS316L)，采用DCS/PLC自动控制搅拌速度(50~500 RPM)、反应温度(-20°C~250°C)、压力(真空~10 bar)。关键CPP(反应时间、温度曲线、pH、搅拌扭矩)以1秒~1分钟间隔记录到SCADA。采集IPC样品通过TLC/IR/HPLC确认反应进度，达到目标转化率后淬灭或冷却转移到下一步。使用PAT(ReactIR, FBRM)实时监测各批次反应条件是否在配方设定范围内。 |
| 5 | 分离与洗涤 | 将反应混合物通过离心机(Peeler Centrifuge, SUS316L, 500~1,500 G)或Nutsche Filter Dryer(NFD)进行固液分离。分离后的滤饼用洗涤溶剂(MeOH, EtOH, Acetone等)洗涤1~3次去除残留原料和杂质。将洗涤液体积、温度、次数记录到eBR，通过滤液HPLC纯度或折光率判定洗涤终点。使用溶剂回收系统对使用后溶剂进行蒸馏回收，赋予回收批号以追踪交叉污染风险。 |
| 6 | 结晶与干燥 | 纯化后的API溶液在结晶罐(Crystallizer, GL夹套，带搅拌器)中通过冷却(例如60°C→5°C, 1~2°C/min)或反溶剂(Anti-Solvent)投加进行结晶。通过FBRM实时监测晶体粒度分布(PSD)，达到目标PSD后浆料转移至Nutsche Filter Dryer。采用真空干燥(40~80°C, -0.08~-0.09 MPa)或流化床干燥(进口温度60~100°C)至目标LOD(0.5%以下)。干燥温度、真空度、时间直接影响LOD和晶型(Polymorph)，须严格控制。 |
| 7 | 粉碎/过筛/混合 | 干燥后的API通过Pin Mill(转速5,000~15,000 RPM)或Jet Mill(粉碎压力6~8 bar)粉碎至目标粒度(D90: 10~200μm)。通过过筛(Sieve, Mesh #20~#100)分级颗粒和细粉，使用混合机(V-Blender, 15~30分钟, 10~20 RPM)确保多批次间均一性。混合结束后采集代表性样品由QC确认含量、杂质谱、PSD。管理粉碎时发热和静电引起的粉尘爆炸风险(氮气氛固、接地)。 |
| 8 | IPC/检验/偏差审核 | 在LIMS中汇总第3~7步所有IPC样品和成品QC检测结果(纯度≥99.0%，单个杂质≤0.1%~0.5%，重金属≤10~20 ppm，残留溶剂ICH Q3C标准)。将偏差(温度偏离、收率不足、杂质超标)关联到eBR执行影响评估，必要时注册CAPA。设定所有检测结果和偏差处理完成后方可进入QA审核的门条件。 |
| 9 | 包装与贴标 | 将批准的API装入带PE内衬的纤维桶(10~50 kg)或铝箔袋(1~5 kg)，密封(热封+胶带)后在外标签上标注产品名称、批号、净重、生产/有效期、储存条件。通过包装线清场防止前批残留物混入，每个包装单位赋予唯一序列号。包装完成后100%检查重量、密封状态和标签准确性。 |
| 10 | QA放行与CoA签发 | QA审核员审查eBR全部项目(原料批号追溯→反应参数→IPC/实验室结果→偏差/CAPA→包装记录)并通过电子签名批准放行。LIMS自动生成最终COA，记载(纯度、杂质谱、残留溶剂、重金属、PSD、水分、微生物限度)。创建客户/监管机构提交用CoA包，放行后的API在ERP中登记为成品库存。 |

### G01.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 원료 Lot·공급업체 승인 상태 확인 | 1,2 | process_step | Material Control |
| 2 | 계량·투입 전자서명과 이중확인 | 3 | process_step | Weighing Compliance |
| 3 | 반응 CPP와 Recipe Version 통제 | 4 | process_step | Recipe/CPP |
| 4 | 불순물 Profile·IPC 결과 기반 Hold/Release | 6,8 | process_step | Quality Gate |
| 5 | 용매 회수 Lot과 교차오염 추적 | 5,6 | process_step | Cross Contamination |
| 6 | eBR·Deviation·CoA 연결 | 8,9,10 | process_step | Batch Record |

### G01.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 原料批次与供应商批准状态确认 | 1,2 | process_step | Material Control |
| 2 | 称量投料电子签名与双人复核 | 3 | process_step | Weighing Compliance |
| 3 | 反应CPP与配方版本控制 | 4 | process_step | Recipe/CPP |
| 4 | 基于杂质谱与IPC结果的Hold/Release | 6,8 | process_step | Quality Gate |
| 5 | 溶剂回收批次与交叉污染追溯 | 5,6 | process_step | Cross Contamination |
| 6 | eBR、偏差与CoA关联 | 8,9,10 | process_step | Batch Record |

### G01.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | raw_material_lot, supplier_lot, material_status |
| 2 | Material | process |  |  | supplier_lot, material_status, recipe_id |
| 3 | Weighing | batch | Reaction Campaign Loop |  | material_status, recipe_id, batch_id |
| 4 | Reaction | batch | Reaction Campaign Loop |  | recipe_id, batch_id, reactor_id |
| 5 | Separation | batch |  |  | batch_id, reactor_id, equipment_id |
| 6 | Drying | process |  |  | reactor_id, equipment_id, process_parameter |
| 7 | Finishing | process |  |  | equipment_id, process_parameter, ipc_sample_id |
| 8 | Quality Gate | gate |  | 3,4,5,6,7 | process_parameter, ipc_sample_id, lab_result_id |
| 9 | Packaging | process |  |  | ipc_sample_id, lab_result_id, impurity_profile |
| 10 | Release | process |  |  | lab_result_id, impurity_profile, solvent_recovery_lot |

### G01.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | raw_material_lot, supplier_lot, material_status |
| 2 | Material | process |  |  | supplier_lot, material_status, recipe_id |
| 3 | Weighing | batch | Reaction Campaign Loop |  | material_status, recipe_id, batch_id |
| 4 | Reaction | batch | Reaction Campaign Loop |  | recipe_id, batch_id, reactor_id |
| 5 | Separation | batch |  |  | batch_id, reactor_id, equipment_id |
| 6 | Drying | process |  |  | reactor_id, equipment_id, process_parameter |
| 7 | Finishing | process |  |  | equipment_id, process_parameter, ipc_sample_id |
| 8 | Quality Gate | gate |  | 3,4,5,6,7 | process_parameter, ipc_sample_id, lab_result_id |
| 9 | Packaging | process |  |  | ipc_sample_id, lab_result_id, impurity_profile |
| 10 | Release | process |  |  | lab_result_id, impurity_profile, solvent_recovery_lot |

### G01.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 4 | 1 | Charge raw materials |
| 4 | 2 | Control reaction temperature |
| 4 | 3 | Sample and IPC check |
| 4 | 4 | Quench / transfer |

### G01.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 4 | 1 | 投料原料 |
| 4 | 2 | 控制反应温度 |
| 4 | 3 | 取样并进行IPC检查 |
| 4 | 4 | 终止反应/转移 |

---

## G02 `solid_dosage` — 고형제 완제의약품 / 固体制剂

```yaml
code: "G02"
legacy_slug: "solid_dosage"
industry_group: "G"
industry_name_ko: "고형제 완제의약품"
industry_name_zh: "固体制剂"
routing: "RT_REGULATED_BATCH_LINE"
preset_id: "solid_dosage_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - api_lot
  - excipient_lot
  - recipe_id
  - batch_id
  - granulation_id
  - dryer_id
  - blend_uniformity_result
  - compression_machine_id
  - tablet_weight
  - hardness_result
  - coating_recipe_id
  - dissolution_result
  - pack_material_lot
  - line_clearance_id
  - serialization_code
  - ebr_id
  - qa_release_id
```

### G02.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | 원료·부형제 입고 | API(원료의약품)와 부형제(Lactose, MCC, Croscarmellose Sodium, Magnesium Stearate 등) Lot 번호와 COA를 MES/eBR에 등록한다. 각 원료의 입자 크기(PSD), 함수율(LOD), 벌크/탭 밀도 데이터를 수집하여 추후 타정성 예측에 활용한다. 승인된 공급업체 목록(AML) 기준으로 Vendor 승인 상태를 실시간 검증하고, 미승인 Vendor Lot은 격리 후 반려 처리한다. |
| 2 | 칭량·Dispensing | Master Batch Record(MBR)에 따라 API와 각 부형제를 정밀 저울(0.1mg~0.1g 분해능)로 칭량한다. 칭량 데이터는 MES로 자동 전송되고, 설정 값 대비 ±0.5%~±1.0% 이내인지 검증된다. 칭량 완료 후 전자서명(Operator+Checker)으로 이중 확인하고, Dispensing Label을 생성하여 각 용기에 부착한다. 고효능 API(예: 스테로이드, 호르몬제)는 격리된 Containment 시스템(Isolator, RABS) 내에서 칭량한다. |
| 3 | 과립·건조 | 칭량된 원료를 고속 전과립기(High Shear Granulator, Diosna/Collette, 200~800L, Impeller 100~400 RPM, Chopper 1,000~3,000 RPM)에 투입하고, 정제수 또는 결합제 용액(PVP K30/HPMC 수용액)을 분무하여 과립화한다. 건조는 유동층 건조기(Fludized Bed Dryer, GEA/Aeromatic, 입구 온도 50~80°C, 출구 온도 30~45°C)로 목표 LOD(1.0~3.0%)까지 수행한다. 과립 종료 후 체분석(Sieve Analysis)과 유동성(Angle of Repose)을 확인한다. 과립의 입도 분포(D50 150~500μm)와 건조 감량(LOD)이 핵심 관리 파라미터다. |
| 4 | 정립·혼합 | 건조된 과립을 정립기(Oscillating Granulator/Comil, Mesh #12~#30)로 통과시켜 덩어리를 분쇄하고 균일한 입도를 확보한다. 최종 블렌딩 단계로 V-Blender 또는 Bin Blender(용량 200~2,000L, 회전 속도 10~25 RPM, 시간 10~30분)에서 정립된 과립과 외부상(External Phase: Croscarmellose Sodium, Magnesium Stearate 등)을 혼합한다. 블렌딩 종료 후 3~10개 위치에서 시료를 채취하여 Blend Uniformity(RSD ≤5.0%, Assay 95.0~105.0%)를 HPLC로 확인한다. 혼합 균일도 미달 시 재혼합 또는 Deviation 등록한다. |
| 5 | 타정·캡슐충전 | 균일하게 혼합된 과립을 Rotary Tablet Press(Fette/Kilian/Korsch, 30~80 스테이션, 분당 50,000~400,000정 생산)로 타정한다. 주요 관리 파라미터: 타정압(Main Compression Force, 10~40 kN), 예비타정압(Pre-compression, 2~10 kN), 타정 속도(회전 RPM), 충전 깊이(Fill Depth). 5~15분 간격으로 정기 IPC(Tablet Weight 20정, 경도(Hardness), 두께(Thickness), 붕해(Disintegration))를 실시하며, 100% 인라인 중량 검사기(Checkweigher)로 ±3~5% 이탈 정은 자동 제거(Reject)한다. 캡슐 충전의 경우 Capsule Filling Machine(Bosch/IMA)을 사용하여 동일한 중량·붕해 기준을 적용한다. |
| 6 | 코팅 | 타정된 Core Tablet을 Coating Pan(Accela Cota/Glatt, 300~1,500mm 직경, 분당 3~15 RPM)에서 Film Coating Suspension(HPMC/Eudragit/PVA 기반, TiO2+Colorant 포함)을 분무 코팅한다. 주요 파라미터: Inlet Air Temperature(55~75°C), Exhaust Temperature(35~45°C), Spray Rate(50~500 g/min), Pan Speed, Atomizing Air Pressure(1.5~3.0 bar). 코팅 증량(Target 2~5% weight gain) 도달 시 종료하고, 코팅 표면 결함(Peeling, Pitting, Orange Peel)을 육안 검사한다. 장용 코팅(Enteric Coating)의 경우 추가 코팅층과 USP 용출 시험 조건이 변경된다. |
| 7 | IPC·함량·용출시험 | 최종 정제의 대표 시료(n=20~30)를 채취하여 HPLC/UPLC로 함량(Assay), 용출(Dissolution, USP Apparatus 1/2, 37±0.5°C, 100 RPM, 시점 30/45/60분), 함량 균일성(Content Uniformity, n=10), 분해 산물(Degradation Products)을 시험한다. 용출 시험 결과는 S1/S2/S3 단계 기준(Q=80% 또는 Q=85%)에 따라 합격/재시험/불합격을 판정한다. 모든 시험 완료 전까지 Batch는 Hold 상태를 유지한다. |
| 8 | 포장 Line Clearance | 포장 라인 작업 전·후에 Line Clearance 절차를 수행하여 전 제품의 잔류 정제, 포장재, 라벨을 물리적으로 제거하고 전자 기록으로 증적을 남긴다. Blister Pack Machine(Uhlmann/IWK) 또는 Bottle Filling Line에서 사용되는 포장재(PVC/PVDC/Alu Blister Film, Alu-Alu, HDPE Bottle, Desiccant)의 Lot 번호를 MES에 스캔 등록하고, 승인된 포장재 규격과 일치하는지 검증한다. |
| 9 | Serialization·라벨검증 | 각 최종 판매 단위(Pack/Box/Pallet)에 GS1 표준 DataMatrix Code(GTIN + Batch/Lot No. + Expiry Date + Serial Number)를 생성하고 인라인 프린터(Videojet/Domino)로 라벨링한다. 2D 코드 리더(Cognex/Keyence)로 코드 가독성·정확성을 100% 검증하고, Aggregation 단계에서 Bundle-Case-Pallet 간 계층 관계를 데이터베이스에 기록한다. Serialization 데이터는 국가별 규제(유럽 FMD/EFPIA, 미국 DSCSA, 중국 알리바바 추적)에 따라 상위 기관 리포지토리에 업로드한다. 라벨 오류(인쇄 불량, 중복 Serial, 유효기간 오기) 발생 시 해당 단위를 자동 제거하고 이력을 보존한다. |
| 10 | QA Release·출하 | QA Reviewer가 eBR(칭량 기록→과립·타정·코팅 공정 파라미터→IPC/Lab 결과→Serialization 검증→포장 기록) 전체를 검토하고 전자서명한다. 모든 Deviation/CAPA가 종결되었는지 확인하고, 안정성 시험 Schedule(장기·가속)이 등록되었는지 확인한다. 최종 Release Label이 생성되고 ERP에서 완제 재고로 등록된 후 출하 지시가 발행된다. |

### G02.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 原辅料收货 | 将API(原料药)和辅料(乳糖、MCC、交联羧甲纤维素钠、硬脂酸镁等)的批号和COA注册到MES/eBR。收集各原料的粒度(PSD)、水分(LOD)、松/实密度数据用于后续压片性预测。根据批准供应商名录(AML)实时验证供应商批准状态，未批准供应商批次隔离后退回处理。 |
| 2 | 称量与发料 | 根据主批生产记录(MBR)用精密天平(分辨率0.1mg~0.1g)称量API和各辅料。称量数据自动传输至MES，验证是否在设定值±0.5%~±1.0%范围内。称量完成后通过电子签名(操作员+复核人)双重确认，生成发料标签贴附于各容器。高效力API(如类固醇、激素)在隔离的Containment系统(Isolator, RABS)内称量。 |
| 3 | 制粒与干燥 | 将称量后的原料投入高速剪切制粒机(High Shear Granulator, 200~800L, 主桨100~400 RPM, 切刀1,000~3,000 RPM)，喷入纯化水或粘合剂溶液(PVP K30/HPMC水溶液)制粒。采用流化床干燥器(进口温度50~80°C, 出口温度30~45°C)干燥至目标LOD(1.0~3.0%)。制粒结束后确认粒度分析(Sieve Analysis)和流动性(休止角)。颗粒粒度分布(D50 150~500μm)和干燥失重(LOD)是关键控制参数。 |
| 4 | 整粒与总混 | 干燥后的颗粒通过整粒机(Oscillating Granulator/Comil, Mesh #12~#30)破碎团块并获得均匀粒度。最终混合阶段在V型混合机或Bin Blender(容量200~2,000L, 转速10~25 RPM, 时间10~30分钟)中混合整粒后颗粒与外相(External Phase: 交联羧甲纤维素钠、硬脂酸镁等)。混合结束后从3~10个位置取样，通过HPLC确认混合均匀度(RSD ≤5.0%, 含量95.0~105.0%)。均匀度不达标时重新混合或注册偏差。 |
| 5 | 压片/胶囊充填 | 均匀混合后的颗粒在旋转压片机(30~80工位, 每分钟50,000~400,000片)上压片。关键控制参数: 主压力(10~40 kN)、预压力(2~10 kN)、转速、填充深度。每5~15分钟实施常规IPC(20片片重、硬度、厚度、崩解)，通过100%在线重量检测器自动剔除±3~5%偏离的片剂。胶囊充填时使用胶囊充填机(Bosch/IMA)，适用相同重量/崩解标准。 |
| 6 | 包衣 | 将素片在包衣锅(直径300~1,500mm, 转速3~15 RPM)中喷雾包覆薄膜包衣悬浮液(HPMC/Eudragit/PVA基，含TiO2+色料)。关键参数: 进风温度(55~75°C)、排风温度(35~45°C)、喷雾速率(50~500 g/min)、锅速、雾化压力(1.5~3.0 bar)。达到目标包衣增重(2~5% weight gain)时结束，目视检查包衣表面缺陷(脱皮、麻点、橘皮)。肠溶包衣时增加额外包衣层并改变USP溶出条件。 |
| 7 | IPC/含量/溶出检验 | 采集最终片剂代表性样品(n=20~30)，通过HPLC/UPLC检测含量(Assay)、溶出度(USP Apparatus 1/2, 37±0.5°C, 100 RPM, 取样30/45/60分钟)、含量均匀度(Content Uniformity, n=10)、降解产物(Degradation Products)。溶出结果按S1/S2/S3阶段标准(Q=80%或Q=85%)判定合格/复试/不合格。所有检测完成前批次保持Hold状态。 |
| 8 | 包装线清场 | 在包装线操作前后实施清场程序，物理移除前产品残留片剂、包材和标签，并留存电子记录证据。在泡罩包装机(Uhlmann/IWK)或瓶装线上使用的包材(PVC/PVDC/Alu泡罩膜、Alu-Alu、HDPE瓶、干燥剂)的批号扫码注册到MES，验证是否与批准的包材规格一致。 |
| 9 | 序列化与标签验证 | 在每个最终销售单元(Pack/Box/Pallet)上生成GS1标准DataMatrix码(GTIN+批号+有效期+序列号)，通过在线打印机(Videojet/Domino)进行标签打印。使用2D码读码器(Cognex/Keyence)100%验证码的可读性和准确性，在聚合阶段将Bundle-Case-Pallet层级关系记录到数据库。序列化数据按各国监管要求(欧盟FMD/EFPIA、美国DSCSA、中国阿里巴巴追溯)上传至上级机构仓库。标签错误(印刷不良、重复序列号、有效期错误)时自动剔除该单元并保留记录。 |
| 10 | QA放行与出货 | QA审核员审查eBR全部内容(称量记录→制粒/压片/包衣工艺参数→IPC/实验室结果→序列化验证→包装记录)并电子签名。确认所有偏差/CAPA已关闭，稳定性试验计划(长期/加速)已注册。生成最终放行标签，在ERP中登记为成品库存后发出货指令。 |

### G02.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 원료·부형제 Lot와 Recipe Version 정합 | 1,2 | process_step | Material/Recipe |
| 2 | Blend Uniformity와 타정 중량 편차 관리 | 4,5 | process_step | IPC Quality |
| 3 | 용출·함량 시험 결과 기반 Batch Hold | 7 | process_step | Lab Release |
| 4 | 포장 Line Clearance와 포장재 Lot 확인 | 8 | process_step | Line Clearance |
| 5 | Serialization Code 생성·검증·Aggregation | 9 | process_step | Serialization |
| 6 | eBR Review와 QA Release 지연 관리 | 7,10 | process_step | QA Release |

### G02.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 原辅料批次与配方版本一致性 | 1,2 | process_step | Material/Recipe |
| 2 | 混合均匀性与压片重量偏差管理 | 4,5 | process_step | IPC Quality |
| 3 | 基于溶出/含量检验的批次Hold | 7 | process_step | Lab Release |
| 4 | 包装线清场与包材批次确认 | 8 | process_step | Line Clearance |
| 5 | 序列化码生成、验证与聚合 | 9 | process_step | Serialization |
| 6 | eBR审核与QA放行延迟管理 | 7,10 | process_step | QA Release |

### G02.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | api_lot, excipient_lot, recipe_id |
| 2 | Dispensing | process |  |  | excipient_lot, recipe_id, batch_id |
| 3 | Granulation | batch | Batch Manufacturing Loop |  | recipe_id, batch_id, granulation_id |
| 4 | Blending | batch | Batch Manufacturing Loop |  | batch_id, granulation_id, dryer_id |
| 5 | Compression | batch |  |  | granulation_id, dryer_id, blend_uniformity_result |
| 6 | Coating | process |  |  | dryer_id, blend_uniformity_result, compression_machine_id |
| 7 | Quality Gate | gate |  | 3,4,5,6 | blend_uniformity_result, compression_machine_id, tablet_weight |
| 8 | Packaging | process |  |  | compression_machine_id, tablet_weight, hardness_result |
| 9 | Serialization | process |  |  | tablet_weight, hardness_result, coating_recipe_id |
| 10 | Release | process |  |  | hardness_result, coating_recipe_id, dissolution_result |

### G02.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | api_lot, excipient_lot, recipe_id |
| 2 | Dispensing | process |  |  | excipient_lot, recipe_id, batch_id |
| 3 | Granulation | batch | Batch Manufacturing Loop |  | recipe_id, batch_id, granulation_id |
| 4 | Blending | batch | Batch Manufacturing Loop |  | batch_id, granulation_id, dryer_id |
| 5 | Compression | batch |  |  | granulation_id, dryer_id, blend_uniformity_result |
| 6 | Coating | process |  |  | dryer_id, blend_uniformity_result, compression_machine_id |
| 7 | Quality Gate | gate |  | 3,4,5,6 | blend_uniformity_result, compression_machine_id, tablet_weight |
| 8 | Packaging | process |  |  | compression_machine_id, tablet_weight, hardness_result |
| 9 | Serialization | process |  |  | tablet_weight, hardness_result, coating_recipe_id |
| 10 | Release | process |  |  | hardness_result, coating_recipe_id, dissolution_result |

### G02.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 5 | 1 | Set compression tooling |
| 5 | 2 | Run tablet weight IPC |
| 5 | 3 | Reject abnormal tablets |

### G02.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 5 | 1 | 设置压片模具 |
| 5 | 2 | 执行片重IPC |
| 5 | 3 | 剔除异常片剂 |

---

## G03 `sterile_injectable` — 무균·주사제 / 无菌制剂与注射剂

```yaml
code: "G03"
legacy_slug: "sterile_injectable"
industry_group: "G"
industry_name_ko: "무균·주사제"
industry_name_zh: "无菌制剂与注射剂"
routing: "RT_ASEPTIC_BATCH"
preset_id: "aseptic_fill_finish_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - component_lot
  - wfi_lot
  - formulation_batch
  - filter_lot
  - sterilization_cycle_id
  - cip_sip_cycle_id
  - environment_monitoring_id
  - filling_line_id
  - fill_volume_result
  - container_closure_lot
  - visual_inspection_result
  - media_fill_id
  - deviation_id
  - ebr_id
  - qa_release_id
```

### G03.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | 원부자재·용기 입고 | 완제 의약품 원료(API), 주사용수(Water for Injection, WFI), 용기(유리 바이알/앰플/프리필드 시린지, 고무 마개(Rubber Stopper, Bromobutyl/Chlorobutyl), 알루미늄 캡(Aluminum Seal), 플라스틱(COP/PP) 시린지 바디)를 입고한다. 각 구성품의 Lot 번호, COA, Endotoxin/Bioburden 시험 성적서를 MES/eBR에 등록한다. 용기는 IR/형광 검사로 균열·이물질을 100% 선별한다. PVC-free Tubing 세트와 필터(Sterilizing Grade 0.22μm PES)도 함께 관리한다. |
| 2 | 세척·멸균·CIP/SIP | 유리 바이알은 Wash Machine(B+S/Inova)에서 WFI와 초순수로 초음파 세척 후 Depyrogenation Tunnel(입구 350~400°C, 출구 250~300°C, 체류 시간 5~10분)에서 건열 멸균·발열원 제거를 수행한다. 고무 마개는 Silicone 처리 후 오토클레이브(121°C, 15~30분)로 습열 멸균한다. 탱크·배관·필터 하우징·충전 노즐은 CIP(Clean-in-Place) 사이클(초순수→WFI→NaOH 1%→WFI→Steam)로 세정하고, SIP(Steam-in-Place, 121°C, 30~60분)로 멸균한다. CIP/SIP Cycle ID와 시간·온도·유량 데이터를 eBR에 기록한다. |
| 3 | 조제·여과 | API를 WFI에 용해 또는 희석하여 조제 탱크(Stainless Steel, 교반기 부착, 100~3,000L)에서 목표 농도로 Formulation한다. 필요시 pH 조정(0.1N HCl/NaOH), 등장화(NaCl/Dextrose), 첨가제(Antioxidant/Preservative)를 투입한다. 조제 완료 후 Pre-filter(1~5μm) → Sterilizing Filter(0.22μm PES/PVDF, 정전하 멤브레인)로 무균 여과한다. 필터 사용 전·후에 Bubble Point / Diffusion / Pressure Hold Test로 Filter Integrity를 검증하고, 결과가 기준 이내(예: 0.22μm PES ≥3.4 bar BP)여야 이후 충전이 진행된다. |
| 4 | 무균 충전 준비 | 충전 라인(Isolator/RABS, Class A 환경, 주변 Class B)을 가동 준비한다. 충전 노즐(Peristaltic/Time-Pressure/Piston Pump)을 SIP 완료하고, 사용 전 Media Simulation(APS, Aseptic Process Simulation) 최종 결과가 음성(0/5,000~10,000 unit)임을 확인한다. 환경 모니터링(EM) Probe 위치(Viable: Settle Plate/Active Air Sampler, Non-viable: Particle Counter)를 설정하고, 충전 시작 전 Class A(≥ISO 5), 주변 Class B(≥ISO 7) 기준을 충족하는지 확인한다. |
| 5 | Aseptic Filling | 무균 충전기(B+S/Inova/Groninger, 100~600 vials/min)에서 여과된 약액을 정량 충전한다. 충전량 목표 ±0.5~1.5% 이내로 인라인 Checkweigher 또는 Gravimetric(중량법)을 통해 100% 검증하고, 불량은 자동 Reject한다. 충전 중에도 EM을 지속 측정(Viable: Settle Plate 4시간 노출, Active Air 1 m³ 샘플링, Non-viable: ≥0.5μm/≥5μm 연속 모니터링)하고, Class A 기준 1회 초과 시 Intervention(청소·재검증) Protocol을 가동한다. 바이알 무균 충전 후 Partial Stoppering(동결건조 제품) 또는 Full Stoppering을 수행한다. |
| 6 | 동결건조/캡핑 | 동결건조(Lyophilization) 제품의 경우 바이알을 동결건조기(Lyophilizer, Hull/Tofflon, Shelf 온도 -50~+60°C, 진공 0.05~0.5 mbar, 냉각 온도 -70~-85°C, 체류 시간 24~120시간)에 장입한다. Freezing → Primary Drying(Shelf 온도 상승, 진공 유지) → Secondary Drying(온도 상승) Cycle을 Recipe에 따라 자동 제어하고, Product Temperature·Shelf Temperature·Pressure·시간을 eBR에 기록한다. 건조 종료 후 질소 Backfill 후 Full Stoppering을 기계적으로 수행한다. 비동결건조 제품은 바로 Capping Machine에서 Aluminum Seal을 Crimping하고, 실시간 Capping Torque를 모니터링한다. |
| 7 | 환경모니터링·무균성 시험 | 배치 충전 중 EM 데이터(부유균, 침강균, 부유 입자, 표면 오염, Glove/Finger Dabb Test)를 취합하여 Aseptic Area 기준 충족 여부를 eBR에 연동한다. 배치 무균성 시험은 배지 충전(Media Fill, 액체 배양 배지 충전 후 14일 배양) 결과로 최종 판정하고, 모든 무균 공정 조건이 유효함을 증명해야 Release 가능하다. Endotoxin 시험(LAL/rFC/rCR, ≤0.25~5.0 EU/mL, 제품별 기준)도 병행 시험한다. |
| 8 | 외관검사·용량검사 | 모든 충전 완료 단위를 자동 외관 검사기(Seidenader/Brevetti/ATS, High-speed Camera 5~8대, 360° 회전, LED 조명)로 이물질(Glass Particle, Fiber, Black Spec), 균열, 마감 불량, 충전량 이상을 검출하고 불량품을 자동 제거한다. 검사 기준은 USP <790>/EP 2.9.20 Visible Particulates에 따르며, 검증된 Sensitivity(≥50μm glass, ≥100μm non-glass)를 유지한다. 동결건조 제품은 Cake Appearance와 케이크 무결성도 검사한다. 검사 불량률이 허용 기준(보통 AQL 0.65~1.0%)을 초과하면 Root Cause 조사와 재검사 Protocol을 가동한다. |
| 9 | 포장·라벨링 | 합격된 Unit을 Tray/Blister에 적재하고 Leaflet과 함께 Cartoning Machine(IMA/Marchesini)으로 소포장 → 낱상자(Label 부착, Serialization 포함) → Pallet 적재를 수행한다. 각 단위의 Serial Number를 Aggregation하여 상위 포장 단계와 연결한다. 냉장 제품(2~8°C)은 보온 박스(Phase Change Material + Temperature Logger)에 포장한다. 라벨에 Product Name, Lot/Batch, Expiry, Storage, Rx Only(해당 시)를 명확히 인쇄하고 바코드로 정합성을 검증한다. |
| 10 | QA Release·Batch Closure | QA Reviewer가 eBR 전체(원료·용기 Lot 기록→CIP/SIP Cycle→Formulation/Filter→Aseptic Filling→동결건조/캡핑→Sterility/Endotoxin→Visual Inspection→Packaging→Serialization)를 검토하고 전자서명한다. Media Fill 최종 결과(14일 배양 완료)가 포함되어야 하므로, 2주 이상의 Lead Time이 소요된다. 모든 Deviation/CAPA가 종결되었음을 확인하고, 최종 Release Certificate를 발행한다. Batch Closure 후 모든 eBR과 시험 데이터를 Archive하여 규제 검사(식약처, FDA, EMA, NMPA)에 대비한다. |

### G03.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 原辅料与容器收货 | 接收成品原料药(API)、注射用水(WFI)、容器(玻璃西林瓶/安瓿/预充式注射器、橡胶塞(Bromobutyl/Chlorobutyl)、铝盖(Aluminum Seal)、塑料(COP/PP)注射器主体)。将各组件的批号、COA、内毒素/微生物限度检测报告注册到MES/eBR。通过IR/荧光检测100%筛选容器的裂纹和异物。同时管理无PVC软管组和过滤器(除菌级0.22μm PES)。 |
| 2 | 清洗/灭菌/CIP/SIP | 西林瓶在洗瓶机中用WFI和超纯水超声波清洗后，通过隧道式灭菌烘箱(入口350~400°C, 出口250~300°C, 停留5~10分钟)进行干热灭菌和去热原处理。胶塞经硅化处理后用高压灭菌器(121°C, 15~30分钟)湿热灭菌。储罐、管道、过滤器外壳、灌装针头通过CIP循环(纯化水→WFI→NaOH 1%→WFI→蒸汽)清洗，通过SIP(121°C, 30~60分钟)灭菌。将CIP/SIP周期ID及时间、温度、流量数据记录到eBR。 |
| 3 | 配液与过滤 | 将API溶解或稀释于WFI中，在配液罐(不锈钢，带搅拌器，100~3,000L)中配制至目标浓度。必要时调节pH(0.1N HCl/NaOH)、等渗化(NaCl/Dextrose)、添加辅料(抗氧化剂/防腐剂)。配液完成后依次通过预过滤器(1~5μm)和除菌过滤器(0.22μm PES/PVDF)进行无菌过滤。过滤器使用前后通过气泡点/扩散/保压测试验证过滤器完整性，结果在标准以内(如0.22μm PES BP≥3.4 bar)方可进行后续灌装。 |
| 4 | 无菌灌装准备 | 准备启动灌装线(Isolator/RABS, A级环境, 背景B级)。完成灌装针头(蠕动泵/时间-压力/活塞泵)的SIP操作，确认前次培养基模拟灌装(APS)最终结果为阴性(0/5,000~10,000支)。设定环境监测(EM)探头位置(活菌: 沉降碟/浮游菌采样器, 非活菌: 尘埃粒子计数器)，确认灌装开始前A级(≥ISO 5)、背景B级(≥ISO 7)标准满足要求。 |
| 5 | 无菌灌装 | 在无菌灌装机(100~600 vials/min)中定量灌装经过滤的药液。通过在线称重或重量法100%验证灌装量在目标值±0.5~1.5%以内，不合格品自动剔除。灌装期间持续进行EM监测(沉降碟4小时暴露, 浮游菌1 m³采样, 非活菌≥0.5μm/≥5μm连续监测)，A级标准1次超标时启动干预(清洁、重新验证)规程。西林瓶灌装后执行半压塞(冻干产品)或全压塞。 |
| 6 | 冻干/轧盖 | 冻干产品将西林瓶装入冻干机(搁板温度-50~+60°C, 真空0.05~0.5 mbar, 冷阱温度-70~-85°C, 停留24~120小时)。按配方自动控制冷冻→一次干燥(搁板升温并保持真空)→二次干燥(升温)循环，将产品温度、搁板温度、压力、时间记录到eBR。干燥结束后回填氮气并机械执行全压塞。非冻干产品直接在轧盖机上用铝盖封口(Crimping)，实时监测封口扭矩。 |
| 7 | 环境监测与无菌检验 | 汇总批灌装期间EM数据(浮游菌、沉降菌、悬浮粒子、表面污染、手套/手指接触碟)，将A级区域标准符合性关联到eBR。批无菌检验通过培养基灌装(灌装液体培养基后14天培养)结果最终判定，须证明所有无菌工艺条件有效方可放行。同步实施内毒素检测(LAL/rFC/rCR, ≤0.25~5.0 EU/mL, 按产品标准)。 |
| 8 | 外观与装量检查 | 所有灌装完成品通过自动灯检机(高速相机5~8台, 360°旋转, LED照明)检测异物(玻璃屑、纤维、黑点)、裂纹、封口缺陷、装量异常，不合格品自动剔除。检测标准按USP <790>/EP 2.9.20可见异物执行，维持已验证的灵敏度(≥50μm玻璃, ≥100μm非玻璃)。冻干产品还检查冻干饼外观和完整性。不合格率超允许标准(通常AQL 0.65~1.0%)时启动根本原因调查和复检规程。 |
| 9 | 包装与贴标 | 将合格品装入托板/泡罩，连同说明书通过装盒机进行小包装→中包装(贴标含序列化)→托盘堆叠。将各单元序列号通过聚合关联到上级包装层级。冷藏产品(2~8°C)使用保温箱(相变材料+温度记录仪)包装。标签清晰印刷产品名、批号、有效期、储存条件、处方药标志(如适用)，通过条码验证一致性。 |
| 10 | QA放行与批次关闭 | QA审核员审查eBR全部内容(原料/容器批号记录→CIP/SIP周期→配液/过滤→无菌灌装→冻干/轧盖→无菌/内毒素→灯检→包装→序列化)并电子签名。须包含培养基灌装最终结果(14天培养完成)，因此需2周以上前置时间。确认所有偏差/CAPA已关闭，签发最终放行证书。批次关闭后归档所有eBR和检测数据以应对监管检查。 |

### G03.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | CIP/SIP Cycle과 멸균 상태 확인 | 2 | process_step | Sterility Assurance |
| 2 | 여과 Filter Integrity와 조제 Batch 추적 | 3 | process_step | Formulation Control |
| 3 | 무균 충전 중 EM Alarm·Intervention 기록 | 4,5,7 | process_step | Aseptic Event |
| 4 | Media Fill·무균성 시험 결과 기반 Release | 7,10 | process_step | Sterility Gate |
| 5 | 용기밀봉·외관·충전량 검사 연동 | 6,8 | process_step | Container Closure |
| 6 | Deviation/CAPA와 eBR 동시 검토 | 7,10 | process_step | Compliance Review |

### G03.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | CIP/SIP循环与灭菌状态确认 | 2 | process_step | Sterility Assurance |
| 2 | 过滤器完整性与配液批次追溯 | 3 | process_step | Formulation Control |
| 3 | 无菌灌装过程EM报警与干预记录 | 4,5,7 | process_step | Aseptic Event |
| 4 | 基于培养基灌装与无菌检验的放行 | 7,10 | process_step | Sterility Gate |
| 5 | 容器密封、外观与装量检查联动 | 6,8 | process_step | Container Closure |
| 6 | 偏差/CAPA与eBR同步审核 | 7,10 | process_step | Compliance Review |

### G03.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | component_lot, wfi_lot, formulation_batch |
| 2 | Sterilization | process |  |  | wfi_lot, formulation_batch, filter_lot |
| 3 | Formulation | batch | Aseptic Campaign Loop |  | formulation_batch, filter_lot, sterilization_cycle_id |
| 4 | Aseptic Prep | batch | Aseptic Campaign Loop |  | filter_lot, sterilization_cycle_id, cip_sip_cycle_id |
| 5 | Aseptic Filling | batch |  |  | sterilization_cycle_id, cip_sip_cycle_id, environment_monitoring_id |
| 6 | Stoppering | process |  |  | cip_sip_cycle_id, environment_monitoring_id, filling_line_id |
| 7 | Sterility Gate | gate |  | 2,3,4,5,6 | environment_monitoring_id, filling_line_id, fill_volume_result |
| 8 | Inspection Gate | process |  |  | filling_line_id, fill_volume_result, container_closure_lot |
| 9 | Packaging | process |  |  | fill_volume_result, container_closure_lot, visual_inspection_result |
| 10 | Release | process |  |  | container_closure_lot, visual_inspection_result, media_fill_id |

### G03.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | component_lot, wfi_lot, formulation_batch |
| 2 | Sterilization | process |  |  | wfi_lot, formulation_batch, filter_lot |
| 3 | Formulation | batch | Aseptic Campaign Loop |  | formulation_batch, filter_lot, sterilization_cycle_id |
| 4 | Aseptic Prep | batch | Aseptic Campaign Loop |  | filter_lot, sterilization_cycle_id, cip_sip_cycle_id |
| 5 | Aseptic Filling | batch |  |  | sterilization_cycle_id, cip_sip_cycle_id, environment_monitoring_id |
| 6 | Stoppering | process |  |  | cip_sip_cycle_id, environment_monitoring_id, filling_line_id |
| 7 | Sterility Gate | gate |  | 2,3,4,5,6 | environment_monitoring_id, filling_line_id, fill_volume_result |
| 8 | Inspection Gate | process |  |  | filling_line_id, fill_volume_result, container_closure_lot |
| 9 | Packaging | process |  |  | fill_volume_result, container_closure_lot, visual_inspection_result |
| 10 | Release | process |  |  | container_closure_lot, visual_inspection_result, media_fill_id |

### G03.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 5 | 1 | Verify line clearance |
| 5 | 2 | Start aseptic filling |
| 5 | 3 | Monitor EM alarms |
| 5 | 4 | Reconcile filled units |

### G03.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 5 | 1 | 确认清场 |
| 5 | 2 | 开始无菌灌装 |
| 5 | 3 | 监控环境报警 |
| 5 | 4 | 核对灌装数量 |

---

## G04 `liquid_topical_inhalation` — 액제·외용제·흡입제 / 液体制剂/外用制剂/吸入制剂

```yaml
code: "G04"
legacy_slug: "liquid_topical_inhalation"
industry_group: "G"
industry_name_ko: "액제·외용제·흡입제"
industry_name_zh: "液体制剂/外用制剂/吸入制剂"
routing: "RT_REGULATED_BATCH_PACK"
preset_id: "liquid_topical_pack_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - container_lot
  - recipe_id
  - batch_id
  - mixing_tank_id
  - viscosity_result
  - ph_result
  - microbial_result
  - homogenizer_id
  - filling_line_id
  - fill_weight_result
  - closure_torque_result
  - label_code
  - ebr_id
  - qa_release_id
```

### G04.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | 원료·용기 입고 | API(항생제/항히스타민제/진해거담제 등), 용매(Purified Water/Ethanol/PEG/Propylene Glycol), 첨가제(감미료/향료/방부제/안정제), 용기(액제병 HDPE/PET, 점안제병 LDPE 무균, 흡입제 캐니스터/밸브 어셈블리, 크림/연고 튜브 Aluminium/Laminate)를 입고한다. 각 Lot 번호, COA, 용기 재질 인증서, 미생물 시험 성적서를 eBR에 등록한다. 용기는 세척·건조 상태를 1차 검수하고, 투명 액제 병은 이물·균열 검사를 수행한다. |
| 2 | 계량·Dispensing | Recipe에 따라 API, 용매, 첨가제를 Stainless Steel 계량 용기/저울(분해능 0.01g~0.1kg)에서 계량한다. 소량 첨가제(방부제, 향료)는 정밀 마이크로 저울(0.001g 분해능)로 계량한다. 계량 순서는 혼합 탱크 투입 시 혼화성(Compatibility)을 고려하여 고정하고, 각 투입 전 후 저울 영점·Spam 검증을 수행한다. 계량 데이터는 자동으로 MES에 전송되며, 목표량 대비 ±0.5~2.0% 편차 한도를 적용한다. |
| 3 | 혼합·용해 | Stainless Steel 혼합 탱크(Propeller/Turbine 교반기, 100~5,000L)에서 용매에 API를 투입하고 교반(50~500 RPM)하여 완전 용해시킨다. 온도 제어 자켓으로 용액 온도를 25~60°C 범위로 유지하며, 시간과 RPM을 Recipe에 따라 제어한다. 투명 액제는 용해 완료 후 Filter Press 또는 Inline Filter(1~10μm)를 통과시켜 불용성 이물을 제거한다. Suspension 제품은 Homogenizer에서 API 분말을 분산시킨다. pH meter로 pH 목표 범위(예: pH 5.0~7.0)를 확인하고, 부적합 시 산/염기로 조정한다. |
| 4 | 균질화·탈포 | 크림/연고/로션의 경우 고속 균질기(High Shear Rotor-Stator Homogenizer, IKA/Silverson, 3,000~10,000 RPM)로 Oil Phase와 Water Phase를 유화(Emulsification)하여 균일한 입자 크기(1~10μm)의 에멀전을 형성한다. 필요시 Colloid Mill을 통과시켜 추가 미세화한다. 균질화 후 진공 탈포(Vacuum Deaeration, -0.06~-0.08 MPa, 10~30분)로 혼입 기포를 제거하고 최종 점도와 밀도를 측정한다. 흡입제의 경우 정량 밸브(MDI Metering Valve)에 약액을 충전하는 별도 라인에서 균질 Suspension을 유지한다. |
| 5 | 중간시험·Hold | Bulk 약액의 대표 시료를 채취하여 pH, 점도(Viscosity, Brookfield Viscometer), 비중(Specific Gravity, Density Meter), 굴절률(Refractive Index, 투명 액제), 함량(HPLC Assay), 미생물 한도 시험(TAMC/TYMC, 1g/mL 기준)을 수행한다. 크림/연고의 경우 분산 균일성(Microscopic Examination)과 Texture Analysis도 시험한다. 모든 중간시험 기준 충족 전까지 Batch는 Hold Tank(질소 Blanket, 온도 15~30°C)에서 보관하고, Hold 시간을 eBR에 기록한다. |
| 6 | 충전·캡핑 | 승인된 Bulk 약액을 충전 라인(Piston/Peristaltic/Time-Pressure Filler, 10~300 units/min)에서 용기에 충전한다. 충전량은 인라인 Checkweigher로 목표 중량 ±1~2% 범위를 100% 검증하고, 이탈 시 자동 Reject Valve로 불량품을 제거한다. 충전 후 바로 Capping Machine에서 나사식(Screw Cap) 또는 Snap Cap을 밀봉하고, Capping Torque Meter로 Torque 값(예: 0.5~2.0 N·m)을 실시간 측정하여 기준 이탈 시 경고 발생 및 Adjustment를 유도한다. |
| 7 | 중량·Torque·누액검사 | 완성된 각 제품 단위에 대해 인라인 중량 검사, Torque 검사(나사 마개), 누액 검사(Leak Tester, Vacuum Chamber/압축 공기 Submersion, -0.05~-0.09 MPa, 30~120초)를 순차적으로 수행한다. 시험 기준: 누액 불가, 중량 ±2~5% 이내, Torque 하한값 이상. 누액 검사 불량품은 원인 분석 후 배치 영향 평가 실시. 흡입제의 경우 캐니스터 밸브 작동 누출 테스트(MDI Valve Integrity, Water Bath 37°C, 3분, 누설 기준 0.5%/년)를 수행한다. |
| 8 | 라벨·포장 | 합격품에 라벨(Product Name, Dosage Form, Strength, Lot/Batch, Expiry Date, Storage, Usage Direction, Caution)을 부착하고, 바코드/2D 코드 스캔으로 라벨 정합성을 검증한다. 액제는 Leaflet + 소포장 상자(Carton) → Shrink Wrap(다수 Pack) → Case Packing → Pallet 단계를 Cartoning Machine으로 수행한다. 패키지의 무결성(Seal 확인, 라벨 위치 정확도)을 인라인 비전 시스템으로 검사한다. 냉장 제품은 보온 포장재와 콜드 체인 라벨을 적용한다. |
| 9 | 미생물·안정성 검토 | 배치의 미생물 시험 결과(TAMC ≤100~1,000 CFU/g, TYMC ≤10~100 CFU/g, 지정 병원균 불검출)를 LIMS에서 확정하고 eBR에 연동한다. 안정성 시험 계획(장기 25°C/60% RH, 가속 40°C/75% RH, 시점 0/3/6/9/12/18/24/36개월)을 수립하여 시험 Lab에 샘플을 의뢰한다. 의외제의 경우 사용 중 안정성(In-use Stability, 개봉 후 4주 30°C) 시험도 포함한다. 안정성 시험 결과 이상 징후(함량 감소, pH 변화, 외관 변화) 발생 시 Deviation 등록 후 Impact Assessment를 수행한다. |
| 10 | QA Release·출하 | QA Reviewer가 eBR(원료 Lot→계량→혼합/균질화→중간시험→충전→Torque/누액검사→라벨→미생물→안정성 Schedule)을 전자 검토하고 전자서명한다. 배치 Release의 전제 조건: 모든 IPC가 기준 이내, 미생물 시험 음성, 모든 Deviation/CAPA 종결, 안정성 시험 계획 등록. Release Label 발행 후 ERP에서 완제 재고로 등록, 출하 지시가 생성된다. |

### G04.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 原料与容器收货 | 接收API(抗生素/抗组胺药/镇咳祛痰药等)、溶剂(纯化水/乙醇/PEG/丙二醇)、辅料(甜味剂/香料/防腐剂/稳定剂)、容器(液剂瓶HDPE/PET、滴眼剂瓶LDPE无菌、吸入剂罐/阀组件、乳膏/软膏管Aluminium/Laminate)。将各批号、COA、容器材质证书、微生物检验报告注册到eBR。容器检查清洗和干燥状态，透明液剂瓶检查异物和裂纹。 |
| 2 | 称量与发料 | 按配方在SS称量容器/天平(分辨率0.01g~0.1kg)上称量API、溶剂和辅料。少量辅料(防腐剂、香料)使用精密微量天平(分辨率0.001g)称量。称量顺序考虑混合罐投料时的相容性并固定，每次投料前后执行天平零点/跨度验证。称量数据自动传输至MES，应用目标量±0.5~2.0%偏差限度。 |
| 3 | 混合与溶解 | 在不锈钢混合罐(桨式/涡轮搅拌器，100~5,000L)中向溶剂投入API，搅拌(50~500 RPM)至完全溶解。通过温度控制夹套维持溶液温度在25~60°C范围，按配方控制时间和RPM。透明液剂溶解完成后通过板框过滤器或在线过滤器(1~10μm)去除不溶性异物。混悬产品在均质机中分散API粉末。用pH计确认pH目标范围(例如pH 5.0~7.0)，不合格时用酸/碱调整。 |
| 4 | 均质与脱泡 | 乳膏/软膏/洗剂使用高速均质机(3,000~10,000 RPM)将油相和水相乳化，形成均匀粒径(1~10μm)的乳液。必要时通过胶体磨进一步微细化。均质后通过真空脱泡(-0.06~-0.08 MPa, 10~30分钟)去除混入气泡，测量最终粘度和密度。吸入剂在单独线上将药液充入定量阀(MDI Metering Valve)并维持均匀混悬状态。 |
| 5 | 中间检验与Hold | 采集批量药液代表性样品，检测pH、粘度(Brookfield粘度计)、比重(密度计)、折光率(透明液剂)、含量(HPLC Assay)、微生物限度(TAMC/TYMC, 1g/mL标准)。乳膏/软膏还检测分散均匀性(显微镜检查)和质构分析。所有中间检验标准满足前，批次在Hold罐(氮气保护, 温度15~30°C)中保存，Hold时间记录到eBR。 |
| 6 | 灌装与旋盖 | 已批准的批量药液在灌装线(活塞/蠕动泵/时间-压力灌装机, 10~300 units/min)上充入容器。灌装量通过在线检重秤100%验证目标重量±1~2%范围，偏离时通过自动剔除阀去除不合格品。灌装后立即通过旋盖机以螺旋盖或扣盖密封，用旋盖扭矩计实时测量扭矩值(例如0.5~2.0 N·m)，偏离标准时发出警报并引导调整。 |
| 7 | 重量/扭矩/泄漏检查 | 对每个成品单元依次执行在线重量检查、扭矩检查(螺旋盖)、泄漏检查(真空腔/压缩空气浸没法, -0.05~-0.09 MPa, 30~120秒)。检验标准: 无泄漏、重量±2~5%以内、扭矩不低于下限。泄漏检查不合格品执行原因分析及批次影响评估。吸入剂执行罐阀组件泄漏测试(MDI阀完整性, 37°C水浴, 3分钟, 泄漏率标准0.5%/年)。 |
| 8 | 贴标与包装 | 合格品上贴附标签(产品名、剂型、规格、批号、有效期、储存条件、使用说明、注意事项)，通过条码/2D码扫描验证标签一致性。液剂通过装盒机完成说明书+小包装盒→收缩膜多联包→装箱→托盘码垛各阶段。通过在线视觉系统检查包装完整性(密封确认、标签位置精度)。冷藏产品应用保温包装材料和冷链标签。 |
| 9 | 微生物与稳定性审核 | 从LIMS确认批次微生物检测结果(TAMC ≤100~1,000 CFU/g, TYMC ≤10~100 CFU/g, 指定病原菌未检出)并关联到eBR。建立稳定性试验计划(长期25°C/60% RH, 加速40°C/75% RH, 取样0/3/6/9/12/18/24/36个月)，委托试验Lab送样。外用制剂还包含使用中稳定性(开封后4周30°C)试验。稳定性结果异常(含量降低, pH变化, 外观变化)时注册偏差并执行影响评估。 |
| 10 | QA放行与出货 | QA审核员电子审查eBR(原料批号→称量→混合/均质→中间检验→灌装→扭矩/泄漏→标签→微生物→稳定性计划)并电子签名。批次放行前提条件: 所有IPC在标准内, 微生物检测阴性, 所有偏差/CAPA已关闭, 稳定性试验计划已注册。放行标签签发后在ERP登记为成品库存, 生成出货指令。 |

### G04.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | Recipe Version과 원료 Lot 정합 | 1,2 | process_step | Material/Recipe |
| 2 | pH·점도·미생물 기준 이탈 관리 | 3,5,9 | process_step | IPC/Lab |
| 3 | Bulk Hold 시간과 탱크 상태 관리 | 4,5 | process_step | Bulk Hold |
| 4 | 충전중량·Torque·누액검사 연동 | 6,7 | process_step | Inline Quality |
| 5 | 라벨·사용기한·포장재 Lot 검증 | 8 | process_step | Label/Pack |
| 6 | eBR·QA Release와 안정성 검토 연결 | 9,10 | process_step | QA Release |

### G04.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 配方版本与原料批次一致性 | 1,2 | process_step | Material/Recipe |
| 2 | pH、黏度、微生物标准偏差管理 | 3,5,9 | process_step | IPC/Lab |
| 3 | Bulk Hold时间与罐状态管理 | 4,5 | process_step | Bulk Hold |
| 4 | 灌装重量、扭矩与泄漏检查联动 | 6,7 | process_step | Inline Quality |
| 5 | 标签、有效期与包材批次验证 | 8 | process_step | Label/Pack |
| 6 | eBR、QA放行与稳定性审核关联 | 9,10 | process_step | QA Release |

### G04.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | raw_material_lot, container_lot, recipe_id |
| 2 | Dispensing | process |  |  | container_lot, recipe_id, batch_id |
| 3 | Mixing | batch | Bulk Hold Loop |  | recipe_id, batch_id, mixing_tank_id |
| 4 | Homogenizing | batch | Bulk Hold Loop |  | batch_id, mixing_tank_id, viscosity_result |
| 5 | Quality Gate | gate |  | 3,4 | mixing_tank_id, viscosity_result, ph_result |
| 6 | Filling | process |  |  | viscosity_result, ph_result, microbial_result |
| 7 | Inline Quality | process |  |  | ph_result, microbial_result, homogenizer_id |
| 8 | Packaging | process |  |  | microbial_result, homogenizer_id, filling_line_id |
| 9 | Lab Review | process |  |  | homogenizer_id, filling_line_id, fill_weight_result |
| 10 | Release | process |  |  | filling_line_id, fill_weight_result, closure_torque_result |

### G04.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | raw_material_lot, container_lot, recipe_id |
| 2 | Dispensing | process |  |  | container_lot, recipe_id, batch_id |
| 3 | Mixing | batch | Bulk Hold Loop |  | recipe_id, batch_id, mixing_tank_id |
| 4 | Homogenizing | batch | Bulk Hold Loop |  | batch_id, mixing_tank_id, viscosity_result |
| 5 | Quality Gate | gate |  | 3,4 | mixing_tank_id, viscosity_result, ph_result |
| 6 | Filling | process |  |  | viscosity_result, ph_result, microbial_result |
| 7 | Inline Quality | process |  |  | ph_result, microbial_result, homogenizer_id |
| 8 | Packaging | process |  |  | microbial_result, homogenizer_id, filling_line_id |
| 9 | Lab Review | process |  |  | homogenizer_id, filling_line_id, fill_weight_result |
| 10 | Release | process |  |  | filling_line_id, fill_weight_result, closure_torque_result |

### G04.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 3 | 1 | Charge materials |
| 3 | 2 | Mix to target viscosity |
| 3 | 3 | Sample for pH/viscosity |

### G04.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 3 | 1 | 投料 |
| 3 | 2 | 混合至目标黏度 |
| 3 | 3 | 取样检测pH/黏度 |

---

## G05 `biologics` — 바이오의약품 / 生物制品

```yaml
code: "G05"
legacy_slug: "biologics"
industry_group: "G"
industry_name_ko: "바이오의약품"
industry_name_zh: "生物制品"
routing: "RT_BIOPROCESS_BATCH"
preset_id: "bioprocess_upstream_downstream_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - cell_bank_id
  - seed_train_id
  - bioreactor_id
  - media_lot
  - single_use_lot
  - cpp_setpoint
  - cqa_result
  - harvest_lot
  - chromatography_run_id
  - filter_lot
  - hold_time
  - viral_clearance_result
  - deviation_id
  - ebr_id
  - qa_release_id
```

### G05.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Cell Bank·Seed 준비 | MCB(Master Cell Bank)와 WCB(Working Cell Bank)에서 하나의 Vial을 꺼내 급속 해동(37°C Water Bath, 1~2분)한 후, Biosafety Cabinet(Class II, A2)에서 배양 배지(RPMI 1640/DMEM/Freestyle CHO, 10% FBS 또는 화학 정의 배지)에 접종한다. T-Flask → Shake Flask(125mL~2.8L, 120~150 RPM, 5~8% CO₂, 36~37°C) → Seed Bioreactor(10~50L, SUS or Single-Use, 교반 100~300 RPM, 포기 0.1~0.5 vvm)로 계대 확대(Seed Train)한다. 각 Passage에서 Cell Viability(≥90%, Trypan Blue Exclusion/CEDEX), Cell Density(Viable Cell Density, VCD), Doubling Time을 기록하고, 세포 계대 수(PDL)가 승인된 한계 내(예: ≤15 PDL)인지 확인한다. |
| 2 | 배지·Single-use 준비 | 세포 배양용 액체 배지(Basal Media + Feed Media, CD CHO/FortiCHO/ActiCHO 등, Glucose 4~8 g/L, Glutamine 4~8 mM)를 Stainless Steel 또는 SU Media Prepare Vessel(50~2,000L)에서 조제한다. 조제 후 0.22μm 필터로 무균 여과하고 2~8°C에서 최대 7~14일 보관 가능(보관 기간 검증 완료된 배지 사용). Single-Use Bioreactor(SUB, 50~2,000L, Thermo Fisher/Xcellerex/Applikon), Single-Use Mixer, SU Connector(Tri-Clamp/MPC/ReadyMate), SU Filter, SU Bag을 사용 전 검수하고 Radiation Sterilization Lot 번호를 추적한다. 또한 Antifoam C/Pluronic F-68, Base(NaOH/Na₂CO₃, 0.5~2.0 M) 준비. |
| 3 | Upstream 배양 | Seed Train 완료된 세포를 Production Bioreactor(SUS or Single-Use, 500~20,000L, 교반 Marine/Disk Turbine Impeller, 50~200 RPM, Microsparger/Frit Sparger로 포기 0.01~0.1 vvm, DO setpoint 30~50%, pH 6.8~7.2, Temperature 36~37°C)에 접종 Density 0.3~1.0×10⁶ cells/mL로 접종한다. Fed-Batch 배양 기간 10~21일 동안 매일 Glucose/Fed-batch(Feed Medium, 배양액의 2~10% v/v/day)를 공급하고, VCD, Viability, Metabolite(Glucose/Lactate/Glutamine/Glutamate/Ammonium/IgG titer, Cedex Bio/Roche Cedex Bioanalyzer)를 24시간 간격으로 측정한다. CPP: 누적 VCD, 배양 시간, DO, pH, 온도, pCO₂, Osmolality. AI 기반 공정 최적화와 디지털 트윈을 통한 공정 파라미터 실시간 조정이 최근 도입되고 있다. Viability ≤80~70% 또는 정체기(VCD Plateau) 진입 시 Harvest 결정하고, Titer(Protein A HPLC 1~10 g/L)를 최종 확인한다. |
| 4 | Harvest·Clarification | 배양액(2~20,000L)을 Depth Filtration(Kleansep/Thermo Scientific, 1차 5~10μm → 2차 0.5~1μm → 3차 0.2μm) 및 Disc Stack Centrifuge(GEA/Westfalia, 5,000~10,000 G, 연속 배출)로 세포 및 Debris를 제거하여 Clarified Harvest(CFC)를 얻는다. Depth Filter 전·후 압력(Pressure Δ, ≤1.5 bar), Turbidity(≤50 NTU)를 모니터링하고, Filter Train Integrity Test를 수행한다. 단일 사용 기술(SUT, Single-Use Technology)의 채택률 60% 이상이며, SU Depth Filter와 SU Hold Bag(2~8°C, 24~72시간 Hold 가능)이 표준으로 자리잡았다. CFC 시료를 채취하여 Titer, Bioburden(≤1 CFU/mL), Endotoxin(≤1~5 EU/mL) 사전 검사를 수행한다. |
| 5 | Capture Chromatography | 단백질 A(Porosa MabCapture A/MabSelect PrismA/Amsphere A3) 친화 크로마토그래피 컬럼(Column 직경 20~200cm, 수지 높이 10~30cm, 로딩 20~60 g/L 수지)으로 Clarified Harvest에서 목적 항체를 Capturing한다. AKTA Avant/Pure/Process 또는 Bio-Rad NGC 시스템으로 자동 실행. Cycle: Equilibrium(중성 Buffer, 3 CV)→Load(CFC)→Wash(고염/중성 Buffer, 5~10 CV)→Elution(산성 Buffer pH 2.5~3.5, 3~5 CV)→CIP(0.1~1.0M NaOH, 2~3 CV)→재평형. 중요 관리: Flow Rate(Residence Time 3~6분), Elution pH Profile/A280, Pool Volume, Pool Titer. Elution Pool Titer를 UV A280/SEC-HPLC로 확인하고, Pool은 2~8°C에서 12~48시간 Hold. 연속 크로마토그래피(CaptureSMB)가 최근 정제 효율 혁신을 이끌고 있다. |
| 6 | Polishing·Viral Clearance | Capture Pool을 Ion Exchange(IEX: CEX Anion/Cation, Poros 50HS/Capto S ImpAct/Capto Q) 및 HIC(Hydrophobic Interaction, Butyl/Phenyl Sepharose)로 심층 정제한다. CEX Buffer: pH 5.0~6.0, NaCl Gradient 0~1.0M. Flow-through Mode(Capto Q, pH 7.5~8.5)에서 HCP(Host Cell Protein, ELISA ≤100~500 ppm), Leached Protein A, DNA(≤10 ng/dose), Endotoxin를 제거한다. 바이러스 제거는 Low pH Hold(≤pH 3.5±0.1, 30~120분, 18~25°C) 및 Viral Filtration(Planova 20N/15N/BioOptimal VF, 20nm nominal pore, 압력 0~2.0 bar, 전·후 Integrity Test)으로 수행한다. Viral Clearance Log Reduction Value(LRV ≥4~6 log)는 규제 요구사항을 충족해야 하며, ICH Q5A에 따른 검증이 완료되어야 한다. |
| 7 | UF/DF·Bulk Hold | 정제된 항체 용액을 Tangential Flow Filtration(TFF, Pellicon/Dow PES/PVDF Membrane, 30/50/100 kD MWCO, Transmembrane Pressure 0.5~2.0 bar, Feed Flow 2~6 L/min/m²)으로 농축(Concentration Factor 10~30x) 및 정용여과(Diafiltration, DF, 5~15 DV, Formulation Buffer로 Buffer Exchange)한다. 농축 목표: 20~200 mg/mL. DF 완료 후 SDS-PAGE/SEC로 Aggregate(≤2~5%) 및 Fragment 수준을 확인하고, 마지막으로 0.22μm 필터로 무균 여과 후 Bulk Container(SU Bag/Fluorinated Ethylene Propylene Bottle)에 수집한다. Bulk Hold 조건(2~8°C, 24시간~6개월, 보관 기간 검증 필요)과 Hold Time을 eBR에 기록한다. |
| 8 | CQA 시험·일탈 검토 | 최종 Drug Substance(Bulk DS)에 대한 모든 CQA 시험 결과를 LIMS에서 취합한다: Appearance, pH, Identity(Peptide Mapping/CE-SDS), Purity/Impurities(SEC-HPLC, CE-SDS, ICIEF), Potency(Cell-based Bioassay/ELISA Binding, 70~130% Reference), Protein Concentration(A280/BCA), Subvisible Particles(USP <787>), Bioburden(≤1 CFU/mL), Endotoxin(≤1~5 EU/mL / ≤0.5 EU/mg). 모든 결과가 CQA Release Specification에 부합해야 하며, Deviation(규격 이탈, 수율 저하, 비정상 SEC Profile) 발생 시 Impact Assessment와 함께 CAPA를 등록한다. CQA 결과가 Gate 조건이 되어 Release 진행 여부가 결정된다. |
| 9 | 충전·보관 인계 | DS를 SU Bag/Stainless Steel Container에 포장하고, 각 용기에 DS Lot 번호, 제품명, Volume, Concentration, 보관 조건을 라벨링한다. DR(Defrost/Storage) 영역으로 이송 기록을 생성하고, 온도 기록계(Temperature Logger, 2~8°C 또는 -20~-80°C, 1~10분 간격)를 부착한다. Drug Product(DP) 제조 사이트로의 Shipment가 필요할 경우 Dry Ice/SLN2 Shipper에 Cold Chain 포장하고 배송 tracking을 개시한다. 인계 시점의 BOM(Bill of Materials) 정합성을 eBR에 자동 기록한다. |
| 10 | QA Release·Batch Closure | QA Reviewer가 eBR(MCB/WCB 계대 기록→Seed Train→Upstream 배양 CPP/CQA→Harvest/Clarification→Protein A Capture→Polishing/Viral Clearance→UF/DF→CQC 시험→Bulk 인계) 전체를 검토하고 전자서명한다. 모든 시험 결과, Viral Clearance LRV, Deviation/CAPA, 안정성 계획이 승인된 상태여야 한다. 최종 Release Certificate 발행 후 ERP에 완제 DS 재고 등록. Batch Record와 시험 증적은 규제 검사(FDA BLA, EMA MAA, NMPA) 대비 15~25년간 보관된다. |

### G05.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 细胞库与种子准备 | 从MCB(主细胞库)和WCB(工作细胞库)取一个冻存管快速解冻(37°C水浴, 1~2分钟)后，在生物安全柜中将细胞接种于培养基(RPMI 1640/DMEM/Freestyle CHO, 10% FBS或化学成分限定培养基)。通过T-Flask → Shake Flask(125mL~2.8L, 120~150 RPM, 5~8% CO₂, 36~37°C) → Seed Bioreactor(10~50L, SUS或一次性, 搅拌100~300 RPM, 通气0.1~0.5 vvm)进行传代扩大(种子链)。每代记录细胞活力(≥90%, 台盼蓝排斥法/CEDEX)、活细胞密度(VCD)、倍增时间，确认细胞传代数(PDL)在批准限度内(例如≤15 PDL)。 |
| 2 | 培养基与一次性耗材准备 | 在不锈钢或一次性培养基配制罐(50~2,000L)中配制细胞培养用液体培养基(基础培养基+补料培养基, 葡萄糖4~8 g/L, 谷氨酰胺4~8 mM)。配制后经0.22μm过滤器无菌过滤，可在2~8°C下保存最长7~14天(使用经验证保存期的培养基)。使用前检查一次性生物反应器(SUB, 50~2,000L)、一次性混合器、一次性连接器(TC/MPC/ReadyMate)、一次性过滤器、一次性袋，追踪辐照灭菌批号。同时准备消泡剂C/Pluronic F-68、碱液(NaOH/Na₂CO₃, 0.5~2.0 M)。 |
| 3 | 上游培养 | 将完成种子链扩增的细胞以接种密度0.3~1.0×10⁶ cells/mL接种至生产规模生物反应器(500~20,000L, 搅拌速度50~200 RPM, 微泡/烧结曝气器通气0.01~0.1 vvm, DO setpoint 30~50%, pH 6.8~7.2, 温度36~37°C)。Fed-Batch培养周期10~21天期间每日补料(Feed Medium, 培养液2~10% v/v/day)，每24小时测量VCD、活力、代谢物(葡萄糖/乳酸/谷氨酰胺/谷氨酸/铵/IgG滴度)。CPP: 累积VCD、培养时间、DO、pH、温度、pCO₂、渗透压。近期引入AI驱动工艺优化和数字孪生实现工艺参数实时调整。活力≤80~70%或进入平台期时决定收获，最终确认滴度(Protein A HPLC 1~10 g/L)。 |
| 4 | 收获与澄清 | 将培养液(2~20,000L)通过深层过滤(1级5~10μm → 2级0.5~1μm → 3级0.2μm)和碟片式离心机(5,000~10,000 G, 连续出料)去除细胞和碎片，获得澄清收获液(CFC)。监测深层过滤器前后压差(ΔP, ≤1.5 bar)和浊度(≤50 NTU)，执行过滤器完整性测试。一次性使用技术(SUT)采用率超过60%，一次性深层过滤器与一次性暂存袋(2~8°C, 可Hold 24~72小时)已成为标准。采集CFC样品预检测滴度、微生物限度(≤1 CFU/mL)、内毒素(≤1~5 EU/mL)。 |
| 5 | 捕获层析 | 使用蛋白A亲和层析柱(柱直径20~200cm, 树脂高度10~30cm, 载量20~60 g/L树脂)从澄清收获液中捕获目标抗体。通过AKTA系统自动运行。循环: 平衡(中性缓冲液, 3 CV)→上样→洗涤(高盐/中性缓冲液, 5~10 CV)→洗脱(酸性缓冲液pH 2.5~3.5, 3~5 CV)→CIP(0.1~1.0M NaOH, 2~3 CV)→再平衡。关键控制: 流速(保留时间3~6分钟)、洗脱pH曲线/A280、收集液体积、收集液滴度。通过UV A280/SEC-HPLC确认收集液滴度，收集液在2~8°C下Hold 12~48小时。连续层析(CaptureSMB)近期引领纯化效率革新。 |
| 6 | 精制与病毒清除 | 通过离子交换层析(IEX: CEX阴离子/阳离子)和HIC(疏水相互作用)深度纯化捕获收集液。CEX缓冲液: pH 5.0~6.0, NaCl梯度0~1.0M。Flow-through模式去除HCP(ELISA ≤100~500 ppm)、泄漏蛋白A、DNA(≤10 ng/dose)、内毒素。病毒清除通过低pH孵育(pH ≤3.5±0.1, 30~120分钟, 18~25°C)和病毒过滤(Planova 20N/15N, 20nm名义孔径, 压力0~2.0 bar, 前后完整性测试)实现。病毒清除对数降低值(LRV ≥4~6 log)须满足监管要求，按ICH Q5A完成验证。 |
| 7 | UF/DF与Bulk Hold | 通过切向流过滤(TFF, 30/50/100 kD MWCO, 跨膜压0.5~2.0 bar, 进液流速2~6 L/min/m²)对纯化抗体溶液进行浓缩(浓缩倍数10~30x)和换液(DF, 5~15 DV, 置换为制剂缓冲液)。浓缩目标: 20~200 mg/mL。DF完成后通过SDS-PAGE/SEC确认聚集体(≤2~5%)和片段水平，最后通过0.22μm过滤器无菌过滤后收集至Bulk容器(一次性袋)。将Bulk Hold条件(2~8°C, 24小时~6个月, 需验证保存期)和Hold时间记录到eBR。 |
| 8 | CQA检验与偏差审核 | 从LIMS汇总最终原液(DS)的所有CQA检测结果: 外观、pH、鉴别(肽图/CE-SDS)、纯度/杂质(SEC-HPLC, CE-SDS, ICIEF)、效价(细胞学效价测定/ELISA结合, 70~130%标准品)、蛋白浓度(A280/BCA)、亚可见颗粒(USP <787>)、微生物限度(≤1 CFU/mL)、内毒素(≤1~5 EU/mL / ≤0.5 EU/mg)。所有结果须符合CQA放行标准，偏差(规格偏离、收率降低、SEC异常)时执行影响评估并注册CAPA。CQA结果构成门条件以决定是否可进行放行。 |
| 9 | 灌装与储存交接 | 将DS装入一次性袋或不锈钢容器，在每个容器上标识DS批号、产品名、体积、浓度、储存条件。生成转移记录至DR(解冻/储存)区域，附温度记录仪(2~8°C或-20~-80°C, 1~10分钟间隔)。若需运送至DP生产场地，则使用干冰/LN2运输箱冷链包装后启动配送跟踪。将交接时点的BOM一致性自动记录到eBR。 |
| 10 | QA放行与批次关闭 | QA审核员审查eBR全部内容(MCB/WCB传代记录→种子链→上游培养CPP/CQA→收获/澄清→蛋白A捕获→精制/病毒清除→UF/DF→CQA检验→Bulk交接)并电子签名。所有检测结果、病毒清除LRV、偏差/CAPA、稳定性计划均须处于批准状态。签发最终放行证书后在ERP中登记为DS成品库存。批记录和检验证据保存15~25年以应对监管检查。 |

### G05.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | Cell Bank·Seed Train Genealogy 보존 | 1,3 | process_step | Cell Genealogy |
| 2 | Single-use Lot·Media Lot 교차오염 추적 | 2,3 | process_step | Material Trace |
| 3 | CPP/CQA 실시간 연계와 배양 Drift 감시 | 3,8 | process_step | CPP/CQA |
| 4 | Chromatography Run과 Viral Clearance 증적 관리 | 5,6 | process_step | Downstream Quality |
| 5 | Bulk Hold 시간·온도·상태 관리 | 7 | process_step | Bulk Hold |
| 6 | eBR·Deviation·QA Release 통합 Review | 8,10 | process_step | Compliance Review |

### G05.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 细胞库与种子链谱系保留 | 1,3 | process_step | Cell Genealogy |
| 2 | 一次性耗材批次与培养基批次交叉污染追溯 | 2,3 | process_step | Material Trace |
| 3 | CPP/CQA实时关联与培养漂移监控 | 3,8 | process_step | CPP/CQA |
| 4 | 层析运行与病毒清除证据管理 | 5,6 | process_step | Downstream Quality |
| 5 | Bulk Hold时间、温度与状态管理 | 7 | process_step | Bulk Hold |
| 6 | eBR、偏差与QA放行综合审核 | 8,10 | process_step | Compliance Review |

### G05.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Cell Bank | process |  |  | cell_bank_id, seed_train_id, bioreactor_id |
| 2 | Preparation | process |  |  | seed_train_id, bioreactor_id, media_lot |
| 3 | Upstream | batch | Bioreactor Campaign Loop |  | bioreactor_id, media_lot, single_use_lot |
| 4 | Harvest | batch | Bioreactor Campaign Loop |  | media_lot, single_use_lot, cpp_setpoint |
| 5 | Downstream | batch |  |  | single_use_lot, cpp_setpoint, cqa_result |
| 6 | Viral Clearance | process |  |  | cpp_setpoint, cqa_result, harvest_lot |
| 7 | Bulk | process |  |  | cqa_result, harvest_lot, chromatography_run_id |
| 8 | CQA Gate | gate |  | 3,4,5,6,7 | harvest_lot, chromatography_run_id, filter_lot |
| 9 | Fill Handoff | process |  |  | chromatography_run_id, filter_lot, hold_time |
| 10 | Release | process |  |  | filter_lot, hold_time, viral_clearance_result |

### G05.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Cell Bank | process |  |  | cell_bank_id, seed_train_id, bioreactor_id |
| 2 | Preparation | process |  |  | seed_train_id, bioreactor_id, media_lot |
| 3 | Upstream | batch | Bioreactor Campaign Loop |  | bioreactor_id, media_lot, single_use_lot |
| 4 | Harvest | batch | Bioreactor Campaign Loop |  | media_lot, single_use_lot, cpp_setpoint |
| 5 | Downstream | batch |  |  | single_use_lot, cpp_setpoint, cqa_result |
| 6 | Viral Clearance | process |  |  | cpp_setpoint, cqa_result, harvest_lot |
| 7 | Bulk | process |  |  | cqa_result, harvest_lot, chromatography_run_id |
| 8 | CQA Gate | gate |  | 3,4,5,6,7 | harvest_lot, chromatography_run_id, filter_lot |
| 9 | Fill Handoff | process |  |  | chromatography_run_id, filter_lot, hold_time |
| 10 | Release | process |  |  | filter_lot, hold_time, viral_clearance_result |

### G05.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 3 | 1 | Inoculate bioreactor |
| 3 | 2 | Monitor CPP |
| 3 | 3 | Sample CQA |
| 5 | 1 | Run capture chromatography |

### G05.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 3 | 1 | 接种生物反应器 |
| 3 | 2 | 监控CPP |
| 3 | 3 | 取样检测CQA |
| 5 | 1 | 执行捕获层析 |

---

## G06 `vaccine_cell_gene_therapy` — 백신·세포·유전자치료제 / 疫苗/细胞与基因治疗

```yaml
code: "G06"
legacy_slug: "vaccine_cell_gene_therapy"
industry_group: "G"
industry_name_ko: "백신·세포·유전자치료제"
industry_name_zh: "疫苗/细胞与基因治疗"
routing: "RT_ATMP_COLD_CHAIN"
preset_id: "chain_identity_coldchain_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - donor_id
  - patient_id
  - chain_of_identity_id
  - chain_of_custody_id
  - cell_bank_id
  - vector_lot
  - culture_batch
  - viral_seed_lot
  - potency_result
  - sterility_result
  - cryostorage_id
  - temperature_log_id
  - shipment_id
  - deviation_id
  - ebr_id
  - qa_release_id
```

### G06.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Donor/Patient·Seed 등록 | 공여자(동종제품) 또는 환자(자가제품)의 고유 식별자(Donor ID/Patient ID)를 전자 Chain of Identity(COI) 시스템에 최초 등록한다. 채취된 세포 조직(혈액/골수/지방/피부)의 채취 일시, 용량, 용기 수, 채취 병원, 운송 조건을 기록하고, 고유 COI 문서를 발행한다. 바이러스 벡터 백신의 경우 WVS(Working Virus Seed) 또는 PPV(Production Passage Virus)의 Source, Passage History, 저장 위치를 추적한다. mRNA 백신의 경우 DNA Template(Plasmid) Lot, Linearized DNA Lot을 등록한다. 각 Patient/Seed에 대해 환자의 Rx Claim(전자 승인)과 연결된 고유 Batch ID를 eBR에 생성한다. |
| 2 | Chain of Identity 설정 | COI 문서에 따라 모든 생산 단계에서 환자/공여자-중간체-완제품 간의 연결성을 보장하는 Chain of Custody(COC)를 설정한다. 각 이송/처리 시점마다 Operator 2인이 COI 문서를 확인하고 전자서명한다. Auto/Allo에 따라 단일 환자 Batch 또는 Pooled Batch에 대한 2D Barcode/QR Code 추적 체계를 구축한다. CGT(Cell&Gene Therapy)의 경우 Miltenyi CliniMACS Prodigy 또는 Lonza Cocoon 같은 밀폐형 플랫폼에서 COI가 전자적으로 유지되며, 환자별 세포가 타 환자 세포와 교차되지 않도록 물리적 격리(ID Badge, 바코드 스캔, 생체 인식 잠금)한다. |
| 3 | 세포/바이러스 배양 | (세포 치료제) 환자 유래 세포를 Miltenyi CliniMACS Prodigy / Lonza Cocoon / Terumo Quantum(밀폐형 자동 배양 시스템)에서 배양·활성화·유전자 조작한다. 배양 조건: 37°C, 5% CO₂, Perfusion Rate 0.5~2.0 mL/min, 배양 기간 7~14일. VCD, Viability, Transduction Efficiency(유전자 변형 효율, Vector Copy Number per Cell)를 모니터링한다. (mRNA 백신) 연속 IVT(In Vitro Transcription, T7 RNA Polymerase + NTPs + Cap Analogue, 37°C, 30~60분)에 이어 연속 정제(Oligo dT Affinity + TFF)를 RNAbox/Merck Life Sciences 등의 연속 흐름 시스템으로 처리한다. (전통 백신) Embryonated Eggs(SPF, 11~12일)에 Virus Seed를 접종하고 Incubator(37°C, 70% RH, 2~3일)에서 배양 후 Allantoic Fluid Harvest. 또는 Vero/MDCK 세포에 접종, Bioreactor(10~1,000L, Microcarrier, 100~200 RPM, 37°C, 3~7일)로 배양한다. |
| 4 | 수확·정제 | 세포 치료제(CAR-T/TCR-T 등) 배양 완료 후 자동 세척(Washer/CytoSmart, DPBS로 1~3회, 300~500 G, 5~10분) 및 농축(TFF, 300~500 kDa MWCO, TMP 0.5~2.0 bar)을 수행하고 목표 VCD(1~5×10⁶ cells/mL)로 제형화한다. mRNA 백신: Oligo dT 친화 크로마토그래피 → Cellulofine Sulfate/포스페이트 크로마토그래피 → TFF 농축 → 0.22μm 여과. LNP(Lipid Nanoparticle) 캡슐화는 Microfluidics(Precision NanoSystems/GenVoy, 총 유속 10~50 mL/min, N/P ratio 6:1, 에탄올 40~50%)로 수행하여 균일한 입경(80~120nm, PDI ≤0.2)을 확보한다. 전통 백신: Allantoic Fluid를 연속 원심분리 및 Density Gradient(CsCl/Sucrose) 정제 → Ultrafiltration 농축 → Inactivation(β-Propiolactone/Formalin, 37°C, 24~72 h) → 탈독(Dialysis/TFF). 바이러스 제품(Vector)은 IEX/HIC 크로마토그래피(AKTA Process)로 정제한다. |
| 5 | Formulation·Fill | 세포 치료제: 최종 제형화 세포를 Cryopreservation Medium(DMSO 5~10% + Albumin/Dextran + Cryoprotectant)에 혼합 후 동결용 백(Baxter/Fresenius Cryobag, 또는 Miltenyi CryoMACS Bag)에 분주(Fill, 10~100mL/bag)한다. 각 Bag에 환자 식별 2D Code 태그를 부착한다. mRNA/LNP: LNP 피막 mRNA를 Formulation Buffer(Tris/Sucrose 10~20%, pH 7.5)로 희석하여 0.22μm 무균 여과 후 바이알/프리필드 시린지에 충전(100~500μL/vial). 전통 백신: Bulk 백신을 Formulation Tank(Stainless Steel, 교반)에서 PBS/Stabilizer(Sucrose/Trehalose/Gelatin) + Adjuvant(Alum/CpG/AS01 등)와 혼합한 후 무균 충전라인에서 바이알/앰플(0.5~10mL)에 충전한다. |
| 6 | 동결·초저온 보관 | 세포 치료제: Controlled Rate Freezer(CRF, Planer/Stericell, 1~5°C/min, -4~-10°C/min, -80°C까지 40~60분)로 동결 후 Vapor Phase LN₂ Tank(-150~-196°C, MSR/MVE/Cryotherm)에 롱텀 보관한다. 각 동결 용기의 좌표(Rack/Box/Position)를 COI 시스템에 등록한다. mRNA 백신: -20°C 또는 -70°C 초저온 냉동고에 보관, 온도 기록계로 1~10분 간격 연속 모니터링하고 24/7 알람 시스템과 연동한다. 전통 백신: 2~8°C 차가운 방(Refrigerated Cold Room)에 보관하고, 온도 Logger로 2~8°C 지속 모니터링. 백신별 허용 Temperature Excursion(예: 2~8°C 기준 ±2°C, 72시간 이하)을 자동 체크하고, 이탈 시 경고 및 Deviation 등록. |
| 7 | Potency·무균·안전성 시험 | 세포/유전자 치료제: Potency(Bioassay, 세포 살상능/사이트카인 분비/Vector Copy Number, 70~130% Reference Standard), Sterility(BacT/Alert 14일 배양, 음성), Mycoplasma(Q-PCR/NAT, 음성), Endotoxin(LAL ≤5 EU/mL), Viability(≥70%), Identity(Flow Cytometry, CD3+/CD19+/CD4+/CD8+ %), Copy Number Control(VCN ≤5/cell for CAR-T)를 시험한다. mRNA 백신: Potency(Cell-based Luciferase Assay/EUSA ELISA, 70~130%), Sterility, Endotoxin(≤5 EU/mg), mRNA Integrity(CE/RE, ≥80%), Encapsulation Efficiency(RiboGreen, ≥85%), Sequence Confirmation(NGS/Sanger). 전통 백신: Potency(Neutralization Assay/Hemagglutination/Single Radial Immunodiffusion), Sterility, Abnormal Toxicity, Endotoxin, Identity(ELISA/SDS-PAGE). 모든 최종 Potency 결과가 규제 기준(예: ≥0.7 IU/mL Influenza HA)을 충족해야 한다. |
| 8 | QA Review·Release | QA Reviewer가 eBR(COI/COC 전 단계→배양/IVT→수확/정제→Formulation/Fill→동결→Potency/무균/안전성 시험)을 검토하고 전자서명한다. CGT/ATMP의 경우 환자별로 eBR과 COI가 일치하는지 개별 확인한다. Safety Testing(무균, Mycoplasma, Endotoxin, Replication-competent Lentivirus(RCL) for LVV)이 음성임을 Final Release의 전제 조건으로 한다. Potency Release 시험 결과가 장기 검증되기 전 가조건 Release(예: 응급 치료 승인/Early Access Program)가 필요한 경우, 별도 SOP에 따른 Risk Assessment 문서가 첨부되어야 한다. |
| 9 | Cold Chain 포장 | Release된 제품을 적절한 Cold Chain 포장 시스템에 포장한다: 세포 치료제 Dry Vapor Shipper(Dry Shipper, LN₂ 흡수 패드, -150°C 유지 5~10일, 온도 Logger 내장) → 분자 생물학적 검증된 무균 포장. mRNA 백신: Dry Ice Box(Polystyrene/Phase Change Material, -70°C 유지 72~120시간) → Temperature Recorder 부착. 전통 백신: Refrigerated Box(Gel Pack/Ice Pack/Phase Change Material, 2~8°C 유지 24~72시간) → Temperature Logger + Cold Chain Indicator 부착. 각 Shipper 외부에 Lot/Batch 번호, 환자 정보(해당 시), 온도 모니터링 바코드, 경고 라벨(Do Not Freeze, Do Not X-ray 등)을 부착한다. |
| 10 | 출하·인계·회수 추적 | 출하 전 WMS/ERP에서 Shipment ID 생성, Delivery Order 발행. CGT 세포 치료제는 의료기관으로의 직송(Direct-to-Clinic) 또는 Apheresis Center 반환 경로로, 실시간 GPS 온도 모니터링과 예상 도착 시간(ETA)을 Tracking Portal에 표시한다. 수령 측에서 제품 도착 시 제품 식별(환자 정보 포함), 온도 기록(Temperature Logger 다운로드), 포장 무결성을 확인하고 eBR/COI에 서명한다. 회수 상황에 대비하여 Lot/Serial/환자 ID를 데이터베이스에 영구 연결하고, 허용 가능한 온도 이상 이력이 있는 Batch는 회수 범위에 포함되지 않도록 명확한 기록을 유지한다. |

### G06.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 供者/患者与种子登记 | 在电子身份链(COI)系统中首次注册供者(同种产品)或患者(自体产品)的唯一标识符(Donor ID/Patient ID)。记录采集的细胞组织(血液/骨髓/脂肪/皮肤)的采集时间、容量、容器数量、采集医院、运输条件，签发唯一COI文件。对于病毒载体疫苗，追溯WVS或PPV的源、传代历史、储存位置。对于mRNA疫苗，注册DNA模板(质粒)批号、线性化DNA批号。为每个患者/种子创建与患者Rx Claim(电子批准)关联的唯一批次ID到eBR。 |
| 2 | 建立身份链 | 根据COI文件在所有生产阶段建立确保患者/供者-中间体-成品之间连接性的监管链(COC)。每个转移/处理时间点由2名操作员确认COI文件并电子签名。根据自体/异体分别建立单患者批次或合并批次的2D条码/QR码追溯体系。对CGT产品，COI通过CliniMACS Prodigy或Lonza Cocoon等密闭平台电子维持，通过物理隔离(ID徽章、条码扫描、生物识别锁)防止患者细胞与其他患者细胞交叉。 |
| 3 | 细胞/病毒培养 | (细胞治疗) 患者来源细胞在密闭式自动培养系统中培养、活化和基因改造。培养条件: 37°C, 5% CO₂, 灌流速率0.5~2.0 mL/min, 培养周期7~14天。监测VCD、活力、转导效率(基因改造效率, 每个细胞的载体拷贝数)。(mRNA疫苗) 连续IVT(37°C, 30~60分钟)后经RNAbox等连续流系统进行连续纯化。(传统疫苗) 将病毒种子接种至鸡胚(SPF, 11~12天)，在培养箱(37°C, 70% RH, 2~3天)中培养后收获尿囊液。或将Vero/MDCK细胞接种于微载体生物反应器(10~1,000L, 100~200 RPM, 37°C, 3~7天)培养。 |
| 4 | 收获与纯化 | (细胞治疗) 培养完成后自动洗涤和浓缩，以目标VCD配制。(mRNA疫苗) 亲和层析→纯化→TFF浓缩→过滤。通过微流控(总流速10~50 mL/min, N/P比6:1, 乙醇40~50%)进行LNP包封，获得均匀粒径(80~120nm, PDI ≤0.2)。(传统疫苗) 尿囊液经连续离心及密度梯度纯化→超滤浓缩→灭活(β-丙内酯/福尔马林, 37°C, 24~72小时)→脱毒。(病毒载体产品) 通过IEX/HIC层析纯化。 |
| 5 | 配方与灌装 | (细胞治疗) 将最终配制细胞与冷冻保护培养基混合后分装至冷冻用袋(10~100mL/袋)。每袋贴附患者识别2D码标签。(mRNA/LNP) LNP包封mRNA用配制缓冲液稀释，0.22μm无菌过滤后充入西林瓶/预充式注射器(100~500μL/瓶)。(传统疫苗) 将Bulk疫苗在配制罐中与缓冲液/稳定剂+佐剂混合后，在无菌灌装线充入西林瓶/安瓿(0.5~10mL)。 |
| 6 | 冷冻与超低温储存 | (细胞治疗) 通过程序控温冷冻仪(1~5°C/min, -4~-10°C/min, 至-80°C 40~60分钟)冷冻后，在气相LN₂罐(-150~-196°C)中长期保存。各冷冻容器坐标注册到COI系统。(mRNA疫苗) 保存在-20°C或-70°C超低温冰箱，温度记录仪1~10分钟间隔连续监控并联动24/7报警系统。(传统疫苗) 保存在2~8°C冷库，持续监控温度。自动检查各疫苗的允许温度偏移范围并触发警报和偏差注册。 |
| 7 | 效价/无菌/安全性检验 | (细胞/基因治疗) 检测效价、无菌(14天培养阴性)、支原体、内毒素、活力(≥70%)、鉴别、拷贝数(VCN ≤5/cell for CAR-T)。(mRNA疫苗) 检测效价(70~130%)、无菌、内毒素、mRNA完整性(≥80%)、封装效率(≥85%)、序列确认。(传统疫苗) 检测效价(中和试验/血凝/单向免疫扩散)、无菌、异常毒性、内毒素、鉴别。所有最终效价结果须满足监管标准。 |
| 8 | QA审核与放行 | QA审核员审查eBR(COI/COC全阶段→培养/IVT→收获/纯化→配制/灌装→冷冻→效价/无菌/安全性检验)并电子签名。对于CGT/ATMP产品，逐患者确认eBR和COI一致。安全性检测(无菌、支原体、内毒素、RCL对于慢病毒载体)阴性为最终放行前提。 |
| 9 | 冷链包装 | 将已放行产品装入适当的冷链包装系统: (细胞治疗)干式液氮运输罐(-150°C保持5~10天, 内置温度记录仪)→无菌包装。(mRNA疫苗)干冰保温箱(-70°C保持72~120小时)→附温度记录仪。(传统疫苗)冷藏保温箱(2~8°C保持24~72小时)→温度记录仪+冷链指示器。各运输箱外部贴附批号、患者信息(如适用)、温度监控条码、警示标签。 |
| 10 | 出货交接与召回追溯 | 出货前在WMS/ERP中生成Shipment ID, 签发Delivery Order。CGT细胞治疗产品通过直送诊所或单采中心返回路径配送，实时GPS温度监控和预计到达时间显示在追踪门户上。收货方确认产品识别(含患者信息)、温度记录、包装完整性并在eBR/COI上签名。为应对召回场景，批次/序列号/患者ID在数据库中永久关联，记录可接受的温度偏移历史的批次不应包含在召回范围内。 |

### G06.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | Chain of Identity/Custody 단절 방지 | 1,2,10 | process_step | Identity/Custody |
| 2 | Vector·Seed·Cell Bank Lot 추적 | 3,4 | process_step | Biological Material |
| 3 | Potency·무균·안전성 시험 기준 관리 | 7 | process_step | Potency/Sterility |
| 4 | 초저온 보관·운송 온도 이탈 감시 | 6,9,10 | process_step | Cold Chain |
| 5 | 환자별/소량 Batch eBR와 QA Release 연결 | 7,8 | process_step | QA Release |
| 6 | Deviation·CAPA와 회수 추적성 보존 | 8,10 | process_step | Regulatory Trace |

### G06.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 防止身份链/监管链断裂 | 1,2,10 | process_step | Identity/Custody |
| 2 | 载体、种子与细胞库批次追溯 | 3,4 | process_step | Biological Material |
| 3 | 效价、无菌与安全性检验标准管理 | 7 | process_step | Potency/Sterility |
| 4 | 超低温储存与运输温度偏差监控 | 6,9,10 | process_step | Cold Chain |
| 5 | 患者级/小批量eBR与QA放行关联 | 7,8 | process_step | QA Release |
| 6 | 偏差/CAPA与召回追溯保留 | 8,10 | process_step | Regulatory Trace |

### G06.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Identity | process |  |  | donor_id, patient_id, chain_of_identity_id |
| 2 | Identity | process |  |  | patient_id, chain_of_identity_id, chain_of_custody_id |
| 3 | Culture | process | Identity/Custody Loop |  | chain_of_identity_id, chain_of_custody_id, cell_bank_id |
| 4 | Purification | process | Identity/Custody Loop |  | chain_of_custody_id, cell_bank_id, vector_lot |
| 5 | Fill | process |  |  | cell_bank_id, vector_lot, culture_batch |
| 6 | Cryostorage | process |  |  | vector_lot, culture_batch, viral_seed_lot |
| 7 | Potency Gate | gate |  | 3,4,5,6 | culture_batch, viral_seed_lot, potency_result |
| 8 | Release Gate | process |  |  | viral_seed_lot, potency_result, sterility_result |
| 9 | Cold Chain | process |  |  | potency_result, sterility_result, cryostorage_id |
| 10 | Trace | process |  |  | sterility_result, cryostorage_id, temperature_log_id |

### G06.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Identity | process |  |  | donor_id, patient_id, chain_of_identity_id |
| 2 | Identity | process |  |  | patient_id, chain_of_identity_id, chain_of_custody_id |
| 3 | Culture | process | Identity/Custody Loop |  | chain_of_identity_id, chain_of_custody_id, cell_bank_id |
| 4 | Purification | process | Identity/Custody Loop |  | chain_of_custody_id, cell_bank_id, vector_lot |
| 5 | Fill | process |  |  | cell_bank_id, vector_lot, culture_batch |
| 6 | Cryostorage | process |  |  | vector_lot, culture_batch, viral_seed_lot |
| 7 | Potency Gate | gate |  | 3,4,5,6 | culture_batch, viral_seed_lot, potency_result |
| 8 | Release Gate | process |  |  | viral_seed_lot, potency_result, sterility_result |
| 9 | Cold Chain | process |  |  | potency_result, sterility_result, cryostorage_id |
| 10 | Trace | process |  |  | sterility_result, cryostorage_id, temperature_log_id |

### G06.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 2 | 1 | Verify identity |
| 3 | 1 | Start culture |
| 6 | 1 | Move to cryostorage |
| 9 | 1 | Pack with temperature logger |

### G06.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 2 | 1 | 确认身份链 |
| 3 | 1 | 开始培养 |
| 6 | 1 | 转入冷冻储存 |
| 9 | 1 | 带温度记录器包装 |

---

## G07 `pharma_cdmo` — 의약 CDMO·다제품 생산 / 医药CDMO与多产品生产

```yaml
code: "G07"
legacy_slug: "pharma_cdmo"
industry_group: "G"
industry_name_ko: "의약 CDMO·다제품 생산"
industry_name_zh: "医药CDMO与多产品生产"
routing: "RT_MULTI_PRODUCT_CAMPAIGN"
preset_id: "multi_product_cdmo_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - customer_id
  - tech_transfer_id
  - product_id
  - recipe_id
  - campaign_id
  - batch_id
  - equipment_id
  - cleaning_validation_id
  - changeover_id
  - customer_doc_id
  - deviation_id
  - ebr_id
  - qa_release_id
  - audit_pack_id
  - shipment_id
```

### G07.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | 기술이전·Master Data 설정 | 고객사(제약사/바이오텍)로부터 기술 이전 패키지(Tech Transfer Package: MBR/SOP/Process Description/Analytical Methods/Stability Data/Validation Protocols)를 접수하고, 제품 고유 ID(Product ID)를 생성한다. 고객 Recipe(MBR)를 MES Master Recipe로 변환하고, 원자재(BOM), 분석 방법, 설비 요구 사항을 Master Data로 등록한다. 기술 이전 Gap Analysis(Scale-up 영향, 설비 차이, 분석 방법 간 차이)를 수행하고, 기술 이전 프로토콜(TTP, Tech Transfer Protocol) 대로 시험 배치(Engineering Batch) 1~3회 실행하여 성능 검증한다. 각 증적을 Tech Transfer ID로 추적 가능하게 연결하고, Audit Trail을 남긴다. |
| 2 | 고객 Recipe·문서 승인 | 고객이 제공한 Recipe Version(고유 Version ID), SOP, 분석 시험법(Raw Material/Intermediate/Final Product Spec., Test Method ID)을 CDMO의 문서 관리 시스템(DMS)에 업로드하고, 승인 Workflow(고객 승인 + CDMO QA 승인 → Released 상태 전환)를 실행한다. 각 문서 간의 Cross-reference(예: BOM Item → Recipe Step → Analytical Method ID → Spec Limit)를 시스템에 설정하여, 한 문서가 변경되면 연관 문서에 변경 알림이 자동 발송되도록 한다. 고객별 Document Vault를 설정하고 인가된 사용자만 접근 가능하게 Role-based Access Control(RBAC)을 적용한다. |
| 3 | Campaign 계획·자원 예약 | 다제품 생산 Campaign 계획을 수립한다: 제품 A 5 Batch → Cleaning Changeover → 제품 B 3 Batch → 제품 C 2 Batch 등. 고객 주문 수요와 배송 일정을 고려하여 MPS(Master Production Schedule)에서 Line/Equipment, Operator, Material(주원료·포장재), QC Lab Capacity를 예약한다. Campaign 간 Cleaning Validation(제품 A→B 전환 시 Cleaning Swab/저장소 rinsate 시료를 HPLC로 측정, 잔류 기준 ≤10 ppm 또는 기준 용량의 1/1,000 이하) 기준을 설정하고, Campaign Schedule에 각 Cleaning Changeover 일정을 포함한다. 변경 시 재계획(Rescheduling) 시나리오를 MES에서 시뮬레이션한다. |
| 4 | Line Clearance·Cleaning Validation | 제품 전환(Changeover) 시 전(前) 제품의 설비 잔류물, 문서, 포장재, 라벨을 완전히 제거하는 Line Clearance 절차를 수행하고, Operator + Supervisor 전자서명으로 확인한다. Cleaning Validation Protocol에 따라 설비 세척(예: CIP, WFI Rinse, Detergent 0.5~2.0%, Manual Wipe) 후 Swab Test(50~100 cm², 표준 Swab)와 Rinse Water Test(TOC ≤500 ppb, Conductivity ≤1.3 μS/cm @25°C)를 실시한다. 또한 Product Changeover가 아닌 Batch 간 연속 생산일 경우 Batch-to-Batch Visual Clean만으로 수행한다. 결과가 Cleaning Validation 기준을 충족해야 다음 제품 Batch 생산을 승인하고, 부적합 시 재세척 및 추가 시험(Repeat Cleaning + Swab)을 수행한다. |
| 5 | Batch 생산 실행 | 고객 Recipe에 따라 Batch 생산을 실행한다. CDMO의 Equipment(API 반응기/정제 라인/완제 포장라인)에 Batch ID를 할당하고, MES에서 MBR을 로드하여 공정 단계별 eBR를 생성한다. 각 단계에서 Operator가 공정 파라미터(온도, 압력, pH, RPM, 시간)를 입력하고, DCS/PLC에서 자동 수집된 CPP를 실시간 연동한다. 도중 Deviation(예: 수율 부족, 온도 이탈, 장비 고장) 발생 시 MES에서 Deviation 등록 → Impact Assessment → 고객 통보(Notification) Workflow를 실행한다. CDMO 고유의 SOP와 고객 Recipe 사이에 충돌이 있을 경우 Deviation 처리하고 수정 사항을 양측 QA가 승인한다. |
| 6 | IPC·Lab 시험 | 생산 실행 중 채취한 IPC 시료(In-Process Control: Assay, Purity, pH, Impurity Profile 등)와 배치 완료 후 QC 시료(완제품/안정성 start-up)를 LIMS에 등록하고 분석을 의뢰한다. 분석 결과는 LIMS에서 MES로 자동 전송되며, Spec 내/외를 시스템이 자동 판정한다. Out-of-Spec(OOS) 발생 시 QC Investigation Phase I(분석 오류 가능성 검토, 원래 시료 재분석) → Phase II(제조 프로세스 조사, Deviation 연동)로 자동 Workflow 전환되며, 고객 포털(Customer Portal)에 조사 현황이 공유된다. |
| 7 | eBR Review·Deviation | 생산 완료 후 eBR 전체(원료 Lot → 칭량 → 반응/공정 파라미터 → IPC/Lab 결과 → Cleaning Line Clearance 기록)를 DMS에서 취합하고, System Validation Rule(필수 입력 항목, 값 범위, 전자서명 누락)이 충족되었는지 자동 검증한다. Deviation이 있는 경우 해당 영향 평가(Impact Assessment)와 CAPA(Corrective and Preventive Action) 계획을 eBR에 첨부한다. CDMO QA Team은 Pre-eBR Review를 수행하고, 고객이 서명할 최종 eBR Package를 생성한다. Review 중 발견된 미비점(Data Integrity Issue, 빈 필드, 서명 누락)은 Deviation으로 처리하고 수정한다. |
| 8 | QA/고객 Release | CDMO QA가 선행 검토 후, CDMO 내부 Release(CDMO Batch Release) 및/또는 고객 QA의 Formal Release(고객사 QA Release) 절차에 따라 배치 Release를 결정한다. Release 전 확인 사항: 모든 시험 완료 및 기준 이내, 모든 Deviation/CAPA 종결 및 QA 승인, 모든 서명 수집, Cleaning Validation 이상 없음, Shipment Approval. 고객 Release의 경우 CDMO QA가 Release Package(eBR + CoA + Stability Data + Deviation Log)를 고객 포털에 업로드하고, 고객 QA의 전자서명으로 최종 Release가 완료된다. |
| 9 | 포장·출하 | Release된 제품을 적절한 포장(분류 제품의 경우 Fiber Drum/LDPE Bag/Alu Bag, 완제의 경우 팔레트/박스/Shrink Wrap)에 포장하고, 고객 요구 라벨(Product Name, Customer LOT#, Manufacturing Date, Retest/Expiry Date, Storage Condition, CMO Name, 고객 별도 규격 라벨)을 부착한다. 출하 전 WMS에서 Shipment ID를 생성하고 연동된 Serial Number/UDI 데이터를 고객 포털에 전송한다. 냉장/냉동 제품은 Cold Chain 포장에 Temperature Logger를 포함시키고, 출하 승인 전 Loading Checklist에서 제품 식별·수량·포장 상태를 확인한다. |
| 10 | Audit Pack·문서 인계 | 고객의 규제 제출(IND/NDA/BLA/MAA) 및 규제 기관 검사(FDA/EMA/NMPA)에 대비하여 모든 생산 관련 문서를 Audit Pack으로 패키징한다. Audit Pack 구성: Tech Transfer Package → MBR/SOP → Batch Records(eBR) → CoA/CoC → Deviation/CAPA Log → Cleaning Validation Reports → Equipment Qualification(CQ/IQ/OQ/PQ) → Stability Data → Change Control History → Training Records. 각 문서에 Version History와 QA Approval 로그를 포함한다. 문서는 전자 형식(eCTD 규격)으로 작성하며, CDMO는 Release 후 1~3개월 이내에 최종 문서 Package를 고객사에 전송한다. 생산 종료 후 최소 15년(규정 기간) 동안 전자 문서를 보관하고, 고객사의 요청 시 언제든지 열람 가능한 상태를 유지한다. |

### G07.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 技术转移与主数据建立 | 接收客户(制药/生物科技公司)的技术转移包(包含MBR/SOP/工艺描述/分析方法/稳定性数据/验证方案)，创建产品唯一ID。将客户配方(MBR)转换为MES主配方，将原材料(BOM)、分析方法、设备要求注册为主数据。执行技术转移差距分析后，按技术转移方案执行(试产)1~3批验证性能。将各证据通过技术转移ID关联以实现追踪，维护审计追踪。 |
| 2 | 客户配方与文件批准 | 将客户提供的配方版本(SOP、分析方法)上传至CDMO的文件管理系统，执行批准流程。在系统中建立各文档间的交叉引用，文档变更时自动通知关联文档。建立客户专用文档库，通过基于角色的访问控制(RBAC)确保仅授权用户可访问。 |
| 3 | Campaign计划与资源预约 | 制定多产品生产Campaign计划。综合客户订单需求和交货日程，在MPS中预定产线、设备、操作员、原材料、QC实验室能力。设定Campaign间清洁验证的标准，将各清洁切换日程纳入Campaign计划。通过MES模拟变更时的重新排程场景。 |
| 4 | 清场与清洁验证 | 产品切换时彻底清除前产品设备残留物、文件、包材和标签，由操作员+主管电子签名确认。按清洁验证方案执行设备清洗后，执行擦拭试验和淋洗水检测。结果满足清洁验证标准方可批准下一产品批生产，不合格时重复清洗和检测。 |
| 5 | 批次生产执行 | 按客户配方执行批次生产。为CDMO设备分配批次ID，在MES中加载MBR生成各步骤的eBR。操作员输入工艺参数，DCS/PLC自动采集的CPP实时联动。偏差发生时在MES中执行偏差注册→影响评估→客户通知流程。CDMO标准SOP与客户配方冲突时通过偏差处理并由双方QA批准修正。 |
| 6 | IPC与实验室检验 | 将生产过程中采集的IPC样品和批次完成后QC样品在LIMS中注册并委托分析。分析结果自动从LIMS传输至MES，系统自动判定规格内/外。OOS发生时自动转换至QC调查流程，调查状态在客户门户共享。 |
| 7 | eBR审核与偏差 | 生产完成后在DMS中汇总eBR全部内容，自动验证系统合规规则。附偏差影响评估和CAPA计划。CDMO QA团队执行预审核，生成供客户签字的最终eBR包。审核中发现的缺陷通过偏差处理并修正。 |
| 8 | QA/客户放行 | 根据CDMO QA先行审核后内部放行和/或客户QA的正式放行程序决定批次放行。放行前确认事项: 所有检测完成且符合标准, 所有偏差/CAPA关闭且QA批准, 所有签名齐全, 清洁验证无异常, 出货批准。客户放行时CDMO QA将放行包上传至客户门户，经客户QA电子签名完成最终放行。 |
| 9 | 包装与出货 | 将放行产品适当包装，贴附客户要求的标签。出货前在WMS中生成Shipment ID并将关联的序列号/UDI数据传输至客户门户。冷藏/冷冻产品包含冷链包装及温度记录仪，出货批准前通过装载清单确认产品识别、数量、包装状态。 |
| 10 | 审计包与文件交付 | 为客户的监管提交和监管机构检查，将所有生产相关文档打包为审计包。各文档包含版本历史和QA批准日志。文档以电子格式编制，CDMO在放行后1~3个月内将最终文档包发送给客户。生产结束后按规定期限至少保存电子文档15年，应客户要求随时可供查阅。 |

### G07.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 기술이전 Package와 Master Data Freeze | 1,2 | process_step | Tech Transfer |
| 2 | 고객별 Recipe·SOP·Spec Version 통제 | 2 | process_step | Customer Document |
| 3 | Campaign 생산·전환·Cleaning Validation 관리 | 3,4,5 | process_step | Campaign Control |
| 4 | 다제품 교차오염·Line Clearance 확인 | 4 | process_step | Cross Contamination |
| 5 | eBR·Deviation·고객 승인 Workflow | 7,8 | process_step | Release Workflow |
| 6 | Audit Pack·문서 인계 누락 방지 | 10 | process_step | Audit Documentation |

### G07.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 技术转移包与主数据冻结 | 1,2 | process_step | Tech Transfer |
| 2 | 客户级配方、SOP与规格版本控制 | 2 | process_step | Customer Document |
| 3 | Campaign生产、切换与清洁验证管理 | 3,4,5 | process_step | Campaign Control |
| 4 | 多产品交叉污染与清场确认 | 4 | process_step | Cross Contamination |
| 5 | eBR、偏差与客户批准流程 | 7,8 | process_step | Release Workflow |
| 6 | 防止审计包与文件交付遗漏 | 10 | process_step | Audit Documentation |

### G07.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Tech Transfer | process |  |  | customer_id, tech_transfer_id, product_id |
| 2 | Document | process |  |  | tech_transfer_id, product_id, recipe_id |
| 3 | Planning | process | Campaign/Changeover Loop |  | product_id, recipe_id, campaign_id |
| 4 | Clearance | process | Campaign/Changeover Loop |  | recipe_id, campaign_id, batch_id |
| 5 | Production | process |  |  | campaign_id, batch_id, equipment_id |
| 6 | Quality | process |  |  | batch_id, equipment_id, cleaning_validation_id |
| 7 | Review Gate | process |  |  | equipment_id, cleaning_validation_id, changeover_id |
| 8 | Release Gate | gate |  | 1,2,4,5,6,7 | cleaning_validation_id, changeover_id, customer_doc_id |
| 9 | Shipment | process |  |  | changeover_id, customer_doc_id, deviation_id |
| 10 | Documentation | process |  |  | customer_doc_id, deviation_id, ebr_id |

### G07.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Tech Transfer | process |  |  | customer_id, tech_transfer_id, product_id |
| 2 | Document | process |  |  | tech_transfer_id, product_id, recipe_id |
| 3 | Planning | process | Campaign/Changeover Loop |  | product_id, recipe_id, campaign_id |
| 4 | Clearance | process | Campaign/Changeover Loop |  | recipe_id, campaign_id, batch_id |
| 5 | Production | process |  |  | campaign_id, batch_id, equipment_id |
| 6 | Quality | process |  |  | batch_id, equipment_id, cleaning_validation_id |
| 7 | Review Gate | process |  |  | equipment_id, cleaning_validation_id, changeover_id |
| 8 | Release Gate | gate |  | 1,2,4,5,6,7 | cleaning_validation_id, changeover_id, customer_doc_id |
| 9 | Shipment | process |  |  | changeover_id, customer_doc_id, deviation_id |
| 10 | Documentation | process |  |  | customer_doc_id, deviation_id, ebr_id |

### G07.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 1 | 1 | Load tech transfer package |
| 3 | 1 | Reserve campaign resources |
| 4 | 1 | Verify cleaning status |
| 7 | 1 | Review eBR and deviation |

### G07.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 1 | 1 | 加载技术转移包 |
| 3 | 1 | 预留Campaign资源 |
| 4 | 1 | 确认清洁状态 |
| 7 | 1 | 审核eBR与偏差 |

---

## G08 `medical_consumables` — 의료기기·의료용 소모품 / 医疗器械与医用耗材

```yaml
code: "G08"
legacy_slug: "medical_consumables"
industry_group: "G"
industry_name_ko: "의료기기·의료용 소모품"
industry_name_zh: "医疗器械与医用耗材"
routing: "RT_DEVICE_LINE_STERILE"
preset_id: "medical_device_dhr_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - device_model
  - udi_code
  - component_lot
  - serial_no
  - mold_cavity_id
  - assembly_line_id
  - process_parameter
  - inspection_result
  - sterilization_lot
  - pack_integrity_result
  - label_code
  - dhr_id
  - dmr_version
  - nonconformance_id
  - qa_release_id
  - shipment_id
```

### G08.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | DMR·공정조건 설정 | ISO 13485 / FDA 21 CFR Part 820(QSR)에 따라 Device Master Record(DMR)를 설정한다. DMR 구성: Device Specification(재질·치수·공차), Manufacturing Process Specification(Assembly Drawing, Process Flow, Work Instruction), Quality Assurance Procedures(Inspection Plan, AQL, Sampling Plan), Packaging/Labeling Specification. Mold CAD 파일, 사출 성형 조건(Temperature Profile, Injection Pressure 800~2,000 bar, Hold Pressure 400~1,000 bar, Cooling Time 5~30초), Assembly Line Work Instruction을 DMR에 포함하고 Version을 관리한다. DMR 변경 시 Engineering Change Order(ECO)를 통해 승인 히스토리가 추적 가능해야 한다. |
| 2 | 원부자재·부품 입고 | 의료용 Polymer(PVC, PP, PE, PC, ABS, Silicone, TPU), 금속 부품(Stainless Steel, Nitinol, Titanium), 전자 부품(PCB, Sensor, Motor, LED), 접착제(UV Curable/Epoxy), 포장재(Tyvek, Medical-grade Paper, Pouch Film)를 입고한다. 각 부품에 Supplier Lot 번호와 ISO 13485 Certificate/REACH/RoHS 인증서를 등록한다. 의료기기 부품의 경우 생물학적 평가(ISO 10993: Cytotoxicity, Irritation, Sensitization)의 적합 여부를 입고 시 확인해야 한다. 수입 의료기기의 경우 관세·통관 문건도 함께 관리한다. |
| 3 | 성형·가공 | Injection Molding Machine(Arburg/Demag/Fanuc, 50~500톤 클램프력, 사출 압력 800~2,000 bar, 금형 온도 40~120°C)에서 의료용 Polymer를 성형한다. Multi-cavity Mold(4~128 Cavity)에서 생산되는 각 부품에 Mold Cavity ID를 각인 또는 RFID 태그로 부착하여 추적한다. 주기적(매 30분~2시간) Cavity별 중량·치수(CMM, Coordinate Measuring Machine, ±0.01mm 공차)를 측정하고, Vision Inspection System(비전 검사, 정확도 99.5% 이상)으로 Burr, Short Shot, Flash, Sink Mark를 실시간 검사한다. AI 기반 품질 예측으로 사출 불량을 사전 감지하는 시스템이 도입되고 있다. Extrusion(튜브/카테터/시트)의 경우 Extruder(30~120mm Screw, L/D 20~30:1, Zone 온도 150~250°C)로 연속 성형한다. |
| 4 | 조립·접합 | 성형 부품·전자 부품·금속 부품을 Assembly Line(수동/반자동/로봇 자동 조립)에서 조립한다. 접합 방법: Ultrasonic Welding(초음파 용접, 주파수 20~40 kHz, 압력 0.1~0.5 MPa, 시간 0.5~2.0초), Laser Welding, UV Curing(자외선 경화, 365~405nm, 500~5,000 mJ/cm²), Adhesive Bonding(의료용 접착제 Cyanoacrylate/Epoxy), 열용접. 각 Assembly Station의 작업 시간·품질 검사 결과를 MES에서 추적하고, 주요 공정 파라미터(초음파 진폭, 레이저 출력, 자외선 조사량)를 SCADA에서 수집하여 DHR에 기록한다. 조립된 각 Device에 Serial Number(제조년월일+라인+순번)를 부여한다. |
| 5 | In-process 검사 | 각 조립 단계별 In-process 검사를 ISO 2859-1(AQL) 기준으로 수행한다. 검사 항목: 외관(비전 스테이션, 360° Camera, 0.5mm Resolution, LED 조명), 치수(레이저 마이크로미터, 공기 마이크로미터), 기능(Leak Test: 압력 강하법, 0~300 kPa, 10~120초; 조립 Force/Gap/Lumen 직경), 전기적 시험(연속성, 절연 저항, 내전압, 1~5 kV). 불량품(Nonconformance) 발견 시 MES에 Nonconformance Report(NCR)를 등록하고, 불량 발생 Cavity ID/Assembly Station/Batch Lot을 추적한다. Critical/Najor 불량 시 즉시 공정 중단(Stop Line) Protocol을 가동하고 Root Cause 분석을 진행한다. |
| 6 | 세척·포장 | 조립 완료 제품을 의료기기용 세척 시스템(Ultra Sonic Cleaning + DI Water Rinse + Isopropyl Alcohol Rinse + HEPA Filtered Air Drying)으로 세척한다. 세척 후 생물학적 오염 기준(ISO 19227: Bioburden ≤100 CFU/device)을 충족해야 한다. 세척 완료된 제품을 Cleanroom 환경(ISO Class 7/8, 22±3°C, 45~65% RH)에서 Primary Packaging(Inner Pouch: Tyvek + Medical-grade PE, Heat Seal 조건 150~200°C, 0.2~0.4 MPa, 1~3초)한다. 포장 무결성(Package Integrity)을 Seal Peel Test(ISO 11607-1, Peel Strength 0.5~3.0 N/15mm)로 검증하고, Dye Ingress/Visual Check로 누설 여부를 확인한다. |
| 7 | 멸균·Sterile Barrier 확인 | 포장된 제품을 멸균 처리한다(제품 유형별 선택): Ethylene Oxide(EO) 멸균: 37~63°C, 50~80% RH, EO 농도 400~800 mg/L, Exposure 4~12시간, Aeration 8~48시간, EO 잔류 ≤5μg/g. Gamma Radiation: 25~40 kGy, Cobalt-60 Source, Dose Audit(ISO 11137). Steam Autoclave(121°C/134°C, 15~30분). EO 멸균 시 Biological Indicator(BI, Bacillus atrophaeus, 6-log kill 확인)와 Chemical Indicator(CI, EO 외부 지시약)를 각 멸균 Lot에 포함시킨다. 멸균 Cycle의 물리적 파라미터(온도, 압력, 시간, 가스 농도)를 SCADA에 기록하고, BI 결과 음성(14일 배양)이 확인되어야 Release 가능하다. |
| 8 | UDI·라벨검증 | 각 제품에 UDI(Unique Device Identification)를 부여한다: UDI-DI(Device Identifier - GTIN/Model/Catalog Number) + UDI-PI(Production Identifier - Lot/Batch/Serial No.+Expiry Date+Manufacturing Date). Label Printing Machine(Videojet/Domino)에서 UDI Code(GS1 DataMatrix/AIM DPM)를 인쇄하고, Vision System으로 가독성·정확성·배치를 100% 검증한다. EU MDR(2017/745) 요구사항: UDI Carrier, UDI-DI 등록(EUDAMED), Basic-UDI-DI. FDA 21 CFR Part 801/830 요구사항: GUDID 등록, Direct Marking(재사용 기기). UDI Database(GUDID/EUDAMED)에 제품 정보를 등록/업데이트하고, 각 UDI Code와 연관된 DHR 데이터를 10년 이상 보관한다. |
| 9 | DHR Review·QA Release | Device History Record(DHR)를 QA가 검토한다. DHR 구성(Manufacturing Date, UDI Code, Component Lot/Batch/Serial 이력, Assembly Process Parameters, In-process Inspection Results, Sterilization Cycle Record, BI/CI 결과, Package Integrity Test, Label Verification Scan). 모든 DHR 필드가 완성되고 Nonconformance가 모두 종결되었는지 자동 검증 Rule을 통해 확인한다. QA Reviewer가 전자서명으로 Release하고, Device Release Certificate(완제품 COC)를 발행한다. ERP에 완제 재고 등록, 출하 허가 상태로 전환. |
| 10 | 출하·Complaint/Recall 추적 | 출하 시 Shipment ID 생성과 함께 UDI Code(개별 단위)와 Lot/Batch ID(출하 일괄)를 WMS에 기록한다. 고객/의료기관에 납품된 Device에 대해 Complaint(의심되는 기기 오작동, 부작용, 상해) 접수 시 MDR(Medical Device Reporting, FDA 21 CFR Part 803)/Vigilance(EU MDR Article 87~92)에 따라 30일(치명적) 또는 90일(경미) 내에 규제 보고한다. Recall(자발적/규제 명령) 발생 시 UDI/Lot/Serial로 생산 이력 전수를 추적하고, 고객·유통사에 통보한다. 각 Device의 생산부터 폐기까지 전 추적 이력을 DHR에 연결하여 검색 가능한 상태로 유지한다. |

### G08.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | DMR与工艺条件设置 | 按照ISO 13485 / FDA 21 CFR Part 820(QSR)设定DMR(设备主记录)。DMR包含: 设备规格、制造工艺规格(装配图、工艺流程图、作业指导书)、质量保证程序(检验计划、AQL、抽样计划)、包装/贴标规格。将模具CAD文件、注塑成型条件、装配线作业指导书纳入DMR并管理版本。DMR变更须通过ECO追踪批准历史。 |
| 2 | 原辅料与部件收货 | 接收医用高分子材料、金属部件、电子部件、粘合剂、包装材料。给各部件注册供应商批号和ISO 13485证书/REACH/RoHS认证。确认医疗器械部件的生物学评价(ISO 10993)符合性。进口医疗器械时同时管理关税和清关文件。 |
| 3 | 成型与加工 | 在注塑成型机中将医用高分子材料成型。多腔模具生产的各部件通过模腔ID标识并追溯。每30分钟~2小时周期性测量各腔体重量/尺寸，通过视觉检测系统实时检测毛边、缺料、飞边、缩痕。引入AI质量预测系统预先检测注塑缺陷。挤出工艺通过挤出机连续成型。 |
| 4 | 组装与连接 | 在装配线上组装成型件/电子件/金属件。连接方法包括超声波焊接、激光焊接、UV固化、粘合剂粘接、热焊接。通过MES追踪各工位作业时间和质量检测结果，通过SCADA收集关键工艺参数并记录至DHR。给各组装设备赋予唯一序列号。 |
| 5 | 过程检验 | 按ISO 2859-1(AQL)标准执行各组装阶段的过程检验。检验项目: 外观(视觉工位, 360°相机, 0.5mm分辨率)、尺寸(激光/气动千分尺)、功能(泄漏测试、组装力/间隙/管腔直径)、电气测试(连续性、绝缘电阻、耐压)。不合格品发现时在MES中注册NCR，追踪缺陷发生腔体/工位/批号。关键/主要缺陷时立即启动停线规程并执行根本原因分析。 |
| 6 | 清洗与包装 | 将组装完成品通过医疗器械专用清洗系统清洗，满足生物污染标准。清洗完成品在洁净室环境中进行内包装。通过密封剥离测试验证包装完整性，通过染色渗透/目视检查确认有无泄漏。 |
| 7 | 灭菌与无菌屏障确认 | 对包装产品进行灭菌处理(按产品类型选择): EO灭菌(37~63°C, 50~80% RH, EO浓度400~800 mg/L, 暴露4~12小时), 伽马辐照(25~40 kGy), 蒸汽灭菌(121°C/134°C, 15~30分钟)。EO灭菌时各灭菌批含生物指示剂和化学指示剂。将灭菌周期物理参数记录至SCADA，BI结果阴性(14天培养确认)后方可放行。 |
| 8 | UDI与标签验证 | 给各产品赋予UDI(UDI-DI + UDI-PI)。在标签打印机上打印UDI码，通过视觉系统100%验证可读性/准确性/位置。按EU MDR和FDA 21 CFR Part 801/830要求管理UDI。将产品信息注册/更新至UDI数据库(GUDID/EUDAMED)，关联DHR数据保存10年以上。 |
| 9 | DHR审核与QA放行 | QA审核DHR。通过自动验证规则确认所有DHR字段完整且不合格项全部关闭。QA审核员电子签名放行并签发设备放行证书，在ERP中登记为成品库存。 |
| 10 | 出货与投诉/召回追溯 | 出货时在WMS中记录Shipment ID和UDI码。投诉接收时按MDR/Vigilance规定时限内报告监管部门。召回发生时通过UDI/批号/序列号全量追溯生产历史并通知客户和经销商。维持每个设备从生产到废弃的全追溯历史可检索状态。 |

### G08.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | DMR Version과 실제 제조조건 정합 | 1,3 | process_step | DMR Control |
| 2 | 부품 Lot·Serial·UDI Genealogy 연결 | 2,4,8 | process_step | UDI/Genealogy |
| 3 | 공정검사·Nonconformance 격리 | 5 | process_step | Inspection/NC |
| 4 | 멸균 Lot·포장 무결성 증적 관리 | 6,7 | process_step | Sterile Barrier |
| 5 | DHR Review와 QA Release 누락 방지 | 9 | process_step | DHR Release |
| 6 | Complaint/Recall 발생 시 Lot·Serial 역추적 | 10 | process_step | Post-market Trace |

### G08.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | DMR版本与实际制造条件一致 | 1,3 | process_step | DMR Control |
| 2 | 部件批次、序列号与UDI谱系关联 | 2,4,8 | process_step | UDI/Genealogy |
| 3 | 过程检验与不合格品隔离 | 5 | process_step | Inspection/NC |
| 4 | 灭菌批次与包装完整性证据管理 | 6,7 | process_step | Sterile Barrier |
| 5 | DHR审核与QA放行防遗漏 | 9 | process_step | DHR Release |
| 6 | 投诉/召回时批次与序列号反向追溯 | 10 | process_step | Post-market Trace |

### G08.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | DMR | process |  |  | device_model, udi_code, component_lot |
| 2 | Material | process |  |  | udi_code, component_lot, serial_no |
| 3 | Fabrication | process | Device Lot/Serial Loop |  | component_lot, serial_no, mold_cavity_id |
| 4 | Assembly | process | Device Lot/Serial Loop |  | serial_no, mold_cavity_id, assembly_line_id |
| 5 | Inspection Gate | process |  |  | mold_cavity_id, assembly_line_id, process_parameter |
| 6 | Packaging | process |  |  | assembly_line_id, process_parameter, inspection_result |
| 7 | Sterilization Gate | process |  |  | process_parameter, inspection_result, sterilization_lot |
| 8 | UDI | process |  |  | inspection_result, sterilization_lot, pack_integrity_result |
| 9 | DHR Release | gate |  | 3,4,5,6,7,8 | sterilization_lot, pack_integrity_result, label_code |
| 10 | Trace | process |  |  | pack_integrity_result, label_code, dhr_id |

### G08.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | DMR | process |  |  | device_model, udi_code, component_lot |
| 2 | Material | process |  |  | udi_code, component_lot, serial_no |
| 3 | Fabrication | process | Device Lot/Serial Loop |  | component_lot, serial_no, mold_cavity_id |
| 4 | Assembly | process | Device Lot/Serial Loop |  | serial_no, mold_cavity_id, assembly_line_id |
| 5 | Inspection Gate | process |  |  | mold_cavity_id, assembly_line_id, process_parameter |
| 6 | Packaging | process |  |  | assembly_line_id, process_parameter, inspection_result |
| 7 | Sterilization Gate | process |  |  | process_parameter, inspection_result, sterilization_lot |
| 8 | UDI | process |  |  | inspection_result, sterilization_lot, pack_integrity_result |
| 9 | DHR Release | gate |  | 3,4,5,6,7,8 | sterilization_lot, pack_integrity_result, label_code |
| 10 | Trace | process |  |  | pack_integrity_result, label_code, dhr_id |

### G08.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 4 | 1 | Assemble device |
| 5 | 1 | Record inspection |
| 7 | 1 | Run sterilization cycle |
| 8 | 1 | Verify UDI label |

### G08.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 4 | 1 | 组装器械 |
| 5 | 1 | 记录检验 |
| 7 | 1 | 执行灭菌循环 |
| 8 | 1 | 验证UDI标签 |

---

## G09 `ivd_diagnostics` — IVD·진단제품 / IVD与诊断产品

```yaml
code: "G09"
legacy_slug: "ivd_diagnostics"
industry_group: "G"
industry_name_ko: "IVD·진단제품"
industry_name_zh: "IVD与诊断产品"
routing: "RT_REAGENT_KIT_DIAGNOSTIC"
preset_id: "ivd_reagent_kit_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - reagent_lot
  - antibody_lot
  - calibrator_lot
  - control_lot
  - kit_lot
  - recipe_id
  - batch_id
  - filling_line_id
  - stability_result
  - performance_test_result
  - calibration_curve_id
  - udi_code
  - expiry_date
  - dhr_id
  - qa_release_id
  - shipment_id
```

### G09.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | 원료·항체·표준품 입고 | 진단 시약 원료(Monoclonal/Polyclonal Antibody, Enzyme(GOD/POD/Horseradish Peroxidase/AP), Substrate(TMB/pNPP), Buffer Salts(Tris, Phosphate, HEPES), Stabilizer(BSA/Casein/Trehalose), Preservative(ProClin 300/Sodium Azide))를 입고한다. 각 Lot 번호, COA, 순도(HPLC/SDS-PAGE ≥90~95%), 활성도(Enzyme Activity Unit/mg, ELISA Titer)를 LIMS에 등록한다. Calibrator/Control 표준품은 국제 표준(WHO International Standard/IRMM Reference Material) 또는 Internal Reference Standard(2차 표준)의 Lot 번호와 인증서를 별도 관리하고, Expiry Date를 경고 시스템에 등록한다. Biotin-Streptavidin Conjugate, Magnetic Bead, Polystyrene Latex Bead, Gold Nanoparticle 등 Conjugate 원료의 Lot 간 변이 추적이 중요하다. |
| 2 | 시약 조제·배합 | IVD 시약 조제는 정밀 조제 탱크(Stainless Steel 또는 Glass Lined, 10~500L, 교반 50~300 RPM, 온도 제어 2~25°C, 필요 시 질소 Blanket)에서 Recipe에 따라 Buffer, Stabilizer, Preservative를 혼합하여 Assay Buffer/Conjugate Buffer/Wash Buffer 등을 조제한다. 조제 완료 후 pH(±0.1), Conductivity, Osmolality, Bioburden(≤10~100 CFU/mL)을 측정하고 기준 충족 시 승인한다. Antibody-Enzyme Conjugation(예: HRP-H2O2 activated / SMCC / Maleimide-NHS chemistry)을 4~25°C 반응 조건에서 수행하고, Conjugation Efficiency(SEC-HPLC, Conjugate Concentration via A280/A403 nm)를 확인한다. 각 시약 Component의 Batch/Lot ID를 생성하고 MES에 등록한다. |
| 3 | 여과·분주 | 조제 완료된 시약을 0.22μm PES/PVDF Filter로 무균 여과(IVD Reagent Grade)하고, Dispensing System(Peristaltic/Syringe Pump, 0.1~10 mL/min)으로 Pre-filled Tube/Vial/Bottle에 분주한다. 점도가 높은 시약(Concentrated Wash Buffer)은 정밀 Piston Pump 사용. 분주량 허용 오차: ≤±1~3%(v/v) 목표. 분주 후 자동 Checkweigher로 중량 확인하며, 허용 범위 이탈 시 Reject한다. 필요 시 동결건조(Lyophilization, 초기 냉동 -40~-50°C, 1차 건조 -20~+20°C 0.1~0.3 mbar, 2차 건조 +20~+30°C 0.01~0.05 mbar)하여 Reagent Pellet/Paper Type으로 제조하고, Residual Moisture(≤1~3%, Karl Fischer)를 확인한다. |
| 4 | Kit 구성품 준비 | Kit 구성품을 준비한다: Test Strip(Lateral Flow의 경우 NC Membrane 위에 Capture/Detection Line Coating, Conjugate Pad, Sample Pad, Absorbent Pad Assembly), Microplate(ELISA의 경우 96 Well Plate에 Capture Antibody Coating, Post-coating Blocking, Washing, Drying), Cartridge/Test Cassette, Device Body(형광/면역진단 기계), Cuvette/Reaction Cell, Connectors/Tubing. 각 Lot 번호를 Kit Lot에 연결하고, Coating 공정의 Consistency(Immobilized Protein Amount Per Well/Strip, CV ≤5~10%)를 QC 검증한다. 필요 시 Coating된 Plate/Strip의 성능(Stability at 37°C 3~7일 Accelerated)을 사전 검증한다. |
| 5 | 충전·밀봉 | Kit 구성품을 조립/충전 라인(반자동/자동 Kit Assembly System, 10~60 Kits/min)에서 순차 조립한다: Tray에 Reagent Bottle/Vial Array → Test Strip Pouch → Calibrator/Control Vial → Instruction Leaflet → Desiccant(필요 시). 이후 Tray를 Carton Sleeve에 삽입 → Heat Shrink Wrap/Overwrap → Outer Box에 넣고 Seal 직전에 Kit 무게를 Checkweigher로 검증한다. 각 Kit에 고유 Kit Lot 번호를 인쇄/부착한다. 밀봉 후 내부 Dryness/Humidity Indicator(Desiccant 포함 Kit의 경우)의 색상 변화를 최종 확인한다. |
| 6 | Calibration/QC 시험 | 완성된 Kit에서 대표 시료(n=3~10 Kit)를 채취하여 Calibration 시험(Calibrator Panel: 5~8 농도 Point, Calibration Curve 작성, Curve Fit 4-PL/5-PL/Rational Function)을 수행한다. QC(High, Mid, Low Control)의 측정값이 각각 정해진 Control Range(예: ±2~3 SD from Target Mean) 이내인지 확인한다. 주요 시험 조건: Platform(Analyzer Model: Cobas/Abbott Architect/Beckman Access/Bio-Rad - 사용자 장비 연동), Wavelength, Incubation Time/Temperature, Wash Step, Reaction Volume. Calibration Curve 데이터와 QC 결과를 LIMS에서 자동 판정하고, 부적합 시 Deviation 등록 후 원인 조사한다. |
| 7 | 성능·안정성 시험 | Kit의 진단 성능 시험을 수행한다: Sensitivity(검출 한계 LoD/LoQ, 음성 공시료 20회 측정 평균+2~3SD), Specificity(교차 반응 물질 시험, Negative Sample Panel), Precision(반복성 Repeatability, n=10~20, CV ≤5~15%), Accuracy(회수율 Recovery, 90~110%), Linearity(측정 범위 내, R² ≥0.99). 안정성 시험: 실시간 안정성(2~8°C, 시점 0/1/3/6/12/18/24/36개월), 가속 안정성(37°C, 7~14일로 실시간 6~12개월 예측), 개봉 후 안정성(Open-vial Stability, 30일 2~30°C), Freeze-thaw Stability(3~5 Cycle, -20°C ↔ 2~8°C). 이 시험 결과가 배치 Release의 Gate 조건이 된다. |
| 8 | UDI·라벨·유효기간 검증 | 각 Kit 및 개별 구성품(Reagent Bottle, Control Vial, Test Strip Pouch)에 UDI Code(GS1 DataMatrix, GTIN+Lot+Serial+Expiry)를 인쇄하고, 2D Code Reader로 100% 검증한다. 라벨 항목 검증: Product Name(용도·형식·분류), Intended Use, Kit Contents, Storage Condition(2~8°C/~20°C/실온), Expiry Date(출발일 기준), LOT/Batch Number, REF/Catalog Number, CE Mark(해당 시, NB 번호, 2017/746 EU IVDR), IVD 표시, Warnings(Cautions, Biological Risk), Symbols(ISO 15223). IVDR 2017/746에 따라 EUDAMED 등록(UDI-DI + Basic-UDI-DI)과 Performance Study 데이터 연동을 확인한다. 유효기간 만료 전 사용 가능한 재고량을 ERP에서 실시간 조회 가능하게 한다. |
| 9 | DHR/eBR Review·QA Release | DHR/eBR을 QA가 검토한다. DHR 구성: 원료/항체 Lot → 시약 조제 Batch → 여과·분주 → Kit 구성품 준비 → 충전·밀봉 → Calibration Curve → QC Control 결과 → Performance 시험 → 안정성 데이터(Realtime/Accelerated) → UDI/라벨 검증. 모든 결과가 Release Spec 내에 있고, Deviation/CAPA가 종결되었으며, 안정성 시험 Schedule이 등록되어 있어야 Release 가능하다. QA Reviewer가 DHR의 모든 Required Signature Field에 전자서명하고, Release Certificate를 발행한다. ERP에 완제 Kit 재고 등록, 유효기간 자동 계산 및 경고 설정. |
| 10 | 출하·온도·회수 추적 | 출하 시 온도 제어 포장(냉장 2~8°C 또는 실온)에 Kit를 포장하고, 각 Shipper에 Temperature Logger/Indicator를 포함시킨다. WMS에서 Shipment ID 생성, Kit Lot 번호, UDI Code, 수량, 배송처, 예상 도착일을 기록한다. 고객(In-Vitro Diagnostic Medical Laboratory)의 수령 확인 시 제품 상태(온도, 포장 무결성)를 기록한다. 회수 상황(제조 결함, 규제 명령) 발생 시 UDI/Lot으로 전수 조회하고, 출하처·고객에 통보 절차를 즉시 시작한다. Temperature Excursion이 발생한 Lot은 안정성 Impact Assessment를 수행한 후에만 사용 가능/폐기 여부를 결정한다. |

### G09.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | 原料/抗体/标准品收货 | 接收诊断试剂原料(单克隆/多克隆抗体、酶、底物、缓冲盐、稳定剂、防腐剂)。将各批号、COA、纯度、活性度注册到LIMS。校准品/质控品标准品单独管理国际标准或内部参考标准的批号、证书和有效期至预警系统。对结合物原料(生物素-链霉亲和素结合物、磁珠、乳胶微球、金纳米颗粒)进行批间差异追踪。 |
| 2 | 试剂配制与混合 | IVD试剂配制在精密配制罐中按配方混合缓冲液、稳定剂和防腐剂。配制完成后测量pH、电导率、渗透压、微生物限度并批准。在4~25°C反应条件下执行抗体-酶偶联并确认偶联效率。在MES中注册各试剂组分的批次ID。 |
| 3 | 过滤与分装 | 配制完成的试剂经0.22μm过滤器无菌过滤后，通过分装系统分装至预装管/瓶。高粘度试剂使用精密活塞泵。分装量允许偏差: ≤±1~3%(v/v)目标值。分装后通过自动检重秤确认重量，偏离允许范围时剔除。必要时执行冻干并确认残留水分。 |
| 4 | 试剂盒组件准备 | 准备试剂盒组件: 检测试纸条、微孔板、卡盒/检测盒、仪器机身、比色皿/反应池、连接器/软管。将各批号关联到试剂盒批号，用QC验证包被工艺一致性，必要时预验证包被后的板/条性能。 |
| 5 | 灌装与密封 | 在半自动/全自动试剂盒组装系统中依次组装: 将试剂瓶阵列放入托盘→检测条袋→校准品/质控品瓶→说明书→干燥剂(如需要)。托盘插入纸盒套→热缩膜包裹→外包装盒→密封前通过检重秤验证试剂盒重量。在每个试剂盒上印刷/贴附唯一试剂盒批号。密封后最终确认内部干燥度/湿度指示剂状态。 |
| 6 | 校准/QC检验 | 从完成试剂盒中采集代表性样品执行校准试验和QC试验，确认各质控品的测量值在设定的控制范围内。主要试验条件: 分析仪型号、波长、孵育时间/温度、洗涤步骤、反应体积。校准曲线数据和QC结果由LIMS自动判定，未通过时注册偏差并调查原因。 |
| 7 | 性能与稳定性检验 | 执行试剂盒诊断性能检验: 灵敏度(检测限)、特异性(交叉反应物试验)、精密度(重复性CV ≤5~15%)、准确性(回收率90~110%)、线性(R² ≥0.99)。稳定性检验: 实时稳定性、加速稳定性、开瓶稳定性、冻融稳定性。该检验结果为批次放行门条件。 |
| 8 | UDI/标签/有效期验证 | 在各试剂盒及组件上打印UDI码并通过2D码读码器100%验证。验证标签项目: 产品名、预期用途、试剂盒内容物、储存条件、有效期、批号、目录号、CE标志、IVD标志、警告、符号。根据IVDR确认EUDAMED注册和性能研究数据联动。在ERP中实时查询有效期前可用的库存量。 |
| 9 | DHR/eBR审核与QA放行 | QA审核DHR/eBR。DHR构成: 原料/抗体批号→试剂配制批号→过滤/分装→试剂盒组件准备→灌装/密封→校准曲线→QC质控结果→性能检验→稳定性数据→UDI/标签验证。所有结果在放行规格内且偏差/CAPA关闭且稳定性试验计划已注册后方可放行。QA审核员电子签名所有要求的签章字段并签发放行证书。在ERP中登记成品试剂盒库存，自动计算有效期并设置预警。 |
| 10 | 出货、温度与召回追溯 | 出货时将试剂盒装于温控包装中，各运输箱包含温度记录仪/指示器。在WMS中记录Shipment ID、试剂盒批号、UDI码、数量、收货方、预计到达日期。客户确认收货时记录产品状态。召回时通过UDI/批号全量查询并立即启动通知流程。发生温度偏移的批次须经过稳定性影响评估后决定使用/报废。 |

### G09.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 항체·시약·표준품 Lot Genealogy 연결 | 1,2 | process_step | Reagent Genealogy |
| 2 | 분주·Kit 구성품 누락 방지 | 3,4,5 | process_step | Kit Assembly |
| 3 | Calibration Curve와 QC 결과 보존 | 6 | process_step | Calibration/QC |
| 4 | 진단 성능·안정성 시험 기준 관리 | 7 | process_step | Performance/Stability |
| 5 | UDI·유효기간·라벨 오류 방지 | 8 | process_step | UDI/Expiry |
| 6 | DHR/eBR Release와 출하 온도 추적 | 9,10 | process_step | Release/Trace |

### G09.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---|---|---|---|---|
| 1 | 抗体、试剂与标准品批次谱系关联 | 1,2 | process_step | Reagent Genealogy |
| 2 | 防止分装与试剂盒组件遗漏 | 3,4,5 | process_step | Kit Assembly |
| 3 | 校准曲线与QC结果保留 | 6 | process_step | Calibration/QC |
| 4 | 诊断性能与稳定性检验标准管理 | 7 | process_step | Performance/Stability |
| 5 | 防止UDI、有效期与标签错误 | 8 | process_step | UDI/Expiry |
| 6 | DHR/eBR放行与出货温度追踪 | 9,10 | process_step | Release/Trace |

### G09.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | reagent_lot, antibody_lot, calibrator_lot |
| 2 | Reagent Prep | process |  |  | antibody_lot, calibrator_lot, control_lot |
| 3 | Filling Prep | process | Reagent Lot Stability Loop |  | calibrator_lot, control_lot, kit_lot |
| 4 | Kit Assembly | process | Reagent Lot Stability Loop |  | control_lot, kit_lot, recipe_id |
| 5 | Filling | process |  |  | kit_lot, recipe_id, batch_id |
| 6 | QC Gate | process |  |  | recipe_id, batch_id, filling_line_id |
| 7 | Performance Gate | gate |  | 2,3,4,5,6 | batch_id, filling_line_id, stability_result |
| 8 | UDI/Expiry | process |  |  | filling_line_id, stability_result, performance_test_result |
| 9 | Release | process |  |  | stability_result, performance_test_result, calibration_curve_id |
| 10 | Trace | process |  |  | performance_test_result, calibration_curve_id, udi_code |

### G09.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---|---|---|---|---|---|
| 1 | Material | process |  |  | reagent_lot, antibody_lot, calibrator_lot |
| 2 | Reagent Prep | process |  |  | antibody_lot, calibrator_lot, control_lot |
| 3 | Filling Prep | process | Reagent Lot Stability Loop |  | calibrator_lot, control_lot, kit_lot |
| 4 | Kit Assembly | process | Reagent Lot Stability Loop |  | control_lot, kit_lot, recipe_id |
| 5 | Filling | process |  |  | kit_lot, recipe_id, batch_id |
| 6 | QC Gate | process |  |  | recipe_id, batch_id, filling_line_id |
| 7 | Performance Gate | gate |  | 2,3,4,5,6 | batch_id, filling_line_id, stability_result |
| 8 | UDI/Expiry | process |  |  | filling_line_id, stability_result, performance_test_result |
| 9 | Release | process |  |  | stability_result, performance_test_result, calibration_curve_id |
| 10 | Trace | process |  |  | performance_test_result, calibration_curve_id, udi_code |

### G09.7 operations_ko

| step_ref | seq | name |
|---|---|---|
| 2 | 1 | Prepare reagent |
| 6 | 1 | Run calibrator/control QC |
| 7 | 1 | Run performance panel |
| 8 | 1 | Verify expiry label |

### G09.8 operations_zh

| step_ref | seq | name |
|---|---|---|
| 2 | 1 | 配制试剂 |
| 6 | 1 | 执行校准品/质控品QC |
| 7 | 1 | 执行性能面板测试 |
| 8 | 1 | 验证有效期标签 |

---

## 9. self-check

- [x] G01~G09 전수, slug당 §N.1~§N.8 섹션 완비
- [x] control_points_detail에 category 열 전건 작성
- [x] step_expression ko/zh 행 수 = process_steps 행 수
- [x] role=gate 및 gate_for 지정
- [x] GMP/ISO13485/UDI/eBR/DHR/QA Release 문법 반영
- [x] trace_keys는 slug별 data_capture_points 부분집합으로 작성
- [x] ko/zh 동형 검증 완료
- [x] en/ja 섹션·문단 없음
- [x] JSON·코드·스크립트 미수정
- [x] G01~G09 각 10단계 레이블 변경 없음, 구조 보존
- [x] G01~G09 전 slug 10단계 note에 구체적 장비명·파라미터·추적포인트 추가 완료
- [x] G01~G09 control_points_detail_ko/zh 구조(6개 row, category 열) 보존
- [x] G01~G09 step_expression_ko/zh module·role·loop_hint·gate_for·trace_keys 변경 없음
