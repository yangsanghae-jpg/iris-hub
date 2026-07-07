# A1 Ch3 I산업 공정 상세 Runtime 데이터팩 v0.3 (ko/zh)

> 대상 산업: I — 정밀소재·정밀부품 제조 / 精密材料与精密部件制造
> 작성일: 2026-07-06
> 범위: MD 데이터팩 초안만 작성. JSON·코드·스크립트 미수정.
> 기준: B산업 리팩 지시서의 v0.3 섹션 규격을 I01~I08에 적용.

## 0. 적용 기준

- ko/zh만 작성한다. en/ja 공정·관리점 섹션은 작성하지 않는다.
- `control_points_ko/zh` 별도 bullet 테이블은 작성하지 않는다. 변환 시 `control_points_detail`에서 자동 생성한다.
- I01~I08은 기존 참조에서 `legacy_slug=None`인 항목이 많으므로 본 파일에서 runtime용 제안 slug를 둔다.
- I산업은 정밀 Job Shop과 고순도 Batch가 혼재한다. I03/I06은 Batch 중심, 나머지는 정밀 Job Shop 중심으로 작성한다.

### 0.1 외부 산업 반영 근거

- FDA QMSR 2026-02-02 발효 및 ISO 13485 정렬: 의료용 소재·부품의 공급사·공정·기록관리 요구 강화.
- SEMI 2026 발표: 2025년 반도체 소재 시장 매출 732억 달러, 선단공정·HPC·HBM 수요로 웨이퍼·PR·CMP·고순도 소재 qualification 강화.
- NIST Digital Thread: 설계·제조·검사 정보를 연결해 MBD/NC/CMM/검사성적/CoC를 이어주는 방향.
- IEA Critical Minerals: 니켈·코발트·리튬·희토류 등 critical mineral 공급망 집중과 traceability 필요성 강화.

## 0.2 slug별 변경 요약

| code | slug | routing | preset_id | expression_tier | 핵심 표현 |
|---|---|---|---|---|---|
| I01 | `medical_metal_functional_materials` | `RT_JOBSHOP_REGULATED` | `precision_jobshop_v1` | `P2` | module/trace/gate/operations |
| I02 | `precision_machined_metal_components` | `RT_JOBSHOP` | `precision_jobshop_v1` | `P2` | module/trace/gate/operations |
| I03 | `special_alloy_high_purity_metal` | `RT_BATCH` | `batch_process_v1` | `P2` | module/trace/gate/operations |
| I04 | `ceramic_materials_components` | `RT_JOBSHOP_BATCH` | `precision_jobshop_v1` | `P2` | module/trace/gate/operations |
| I05 | `optical_material_precision_optics` | `RT_JOBSHOP_CLEAN` | `precision_jobshop_v1` | `P2` | module/trace/gate/operations |
| I06 | `semiconductor_electronic_materials` | `RT_BATCH_QUALIFIED` | `batch_process_v1` | `P2` | module/trace/gate/operations |
| I07 | `precision_wire_spring_tube` | `RT_JOBSHOP_LINE` | `precision_jobshop_v1` | `P2` | module/trace/gate/operations |
| I08 | `tool_cutting_wear_components` | `RT_JOBSHOP` | `precision_jobshop_v1` | `P2` | module/trace/gate/operations |

---

## 1. I01 `medical_metal_functional_materials` — 의료용 금속·기능소재 / 医用金属与功能材料

```yaml
subindustry_code: I01
legacy_slug: "medical_metal_functional_materials"
label_ko: "의료용 금속·기능소재"
label_zh: "医用金属与功能材料"
label_en: ""
label_ja: ""
routing: "RT_JOBSHOP_REGULATED"
preset_id: "precision_jobshop_v1"
expression_tier: "P2"
```

> ko: 티타늄·코발트합금·니켈티타늄 선재/튜브·임플란트용 봉·판·와이어 중심의 규제형 정밀 소재 흐름.  
> zh: 以钛合金、钴基合金、镍钛线材/管材、植入物用棒材/板材/丝材为中心的法规型精密材料流程。

### 1.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객도면·규제 요구 기준선 | 도면 revision, ISO 13485/QMSR 적용여부, 고객 CTQ와 장기기록 요구를 확정한다. ASTM F67(순Ti), F136(Ti-6Al-4V ELI), F2063(NiTi), F90(CoCr) 등 재료규격 기준과 510(k)/PMA 요건을 함께 검토한다. |
| 2 | 원소재 Heat/Lot 입고·검증 | 금속 Heat No, MTC/CoA, 성분·기계적 물성, 공급사 승인상태를 확인한다. 인장시험(UTM, ASTM E8/E21 참조), 경도시험(Rockwell/Vickers), 초음파탐상(UT, ASTM A388)을 Lot별로 수행한다. 입고 Gate로 NCR 발행 기준을 둔다. |
| 3 | 절단·단조·압연 전처리 | 밴드쏘/워터젯 절단(절단속도 50~200 mm/min, 냉각수 온도제어), 단조(가열온도 850~1150℃, 유지시간 30~120분), 압연(Reduction 20~50%/pass, 압연속도 2~10 m/min) 조건과 소재 계보를 연결한다. Lot Split/merge 포인트로 반제품 ID를 생성한다. |
| 4 | 인발·튜브·와이어 성형 | NiTi·정밀선재·튜브의 인발 조건(Die angle 6~15°, Reduction 15~30%/pass, 인발속도 1~20 m/min), 직경(±0.01mm), 벽두께(±0.005mm), straightness(0.5mm/m max)를 관리한다. Mandrel/Turks head 교체이력과 Drawing Die ID를 coil/reel 단위로 추적한다. |
| 5 | CNC·연삭 정밀가공 | 5-Axis CNC Swiss-type(Star, Tsugami 등) 또는 Multi-axis grinding(Mikron, Studer), NC 프로그램, CBN/다이아몬드 공구, 치구 offset과 부품 serial을 연결해 치수품질(±0.002~0.01mm)을 만든다. Spindle RPM 2,000~15,000, Feed 0.005~0.1 mm/rev 범위를 공정조건으로 기록한다. |
| 6 | 열처리·형상기억 설정 | 진공열처리로(Schemetrical/Ipsen, 10^-4~10^-6 Torr), NiTi 형상기억처리(400~550℃, Ar 분위기, 급냉/시효), ST(용체화) 800~900℃ 가열 후 수냉, Aging 400~500℃×10~60min를 관리한다. Furnace Profile(±5℃ uniformity)과 적재패턴을 Heat Treat Lot에 연결한다. |
| 7 | 표면처리·Passivation | Passivation(ASTM A967, 20~50% HNO₃, 30~60min, 20~60℃), Electropolishing(전해액 온도 40~70℃, 전류밀도 0.1~1.0 A/cm²), Microblasting, Anodizing(Ti용, ASTM B136) 등 외주/자체 처리 certificate를 부품 serial에 연결한다. 표면거칠기 Ra ≤0.4μm 기준 적용. |
| 8 | 공정중 치수·표면 계측 Gate | CMM(Zeiss/Hexagon, ±0.5μm accuracy), 표면거칠기(Stylus/White-light interferometer, Ra/Rz/Rt 측정), Vision System(Keyness LM 시리즈, 결함검출), 공정능력(Cpk≥1.33) 결과를 Gate로 판단한다. 측정결과 불일치 시 NCR→MRB 경로로 Rework/Scrap 결정한다. |
| 9 | 세정·청정포장 | 초음파 세정(40~80kHz, 40~70℃, 탈이온수/알코올), Rinse(18MΩ·cm DI water, 최종 3회), 입자·이온 오염(LPC/IC), 세정 recipe revision, 포장재 PE/Nylon Bag lot, Class 10k/100k 청정환경과 보존조건(온도 15~30℃, 습도 20~75%RH)을 관리한다. |
| 10 | FAI·CoC·UDI 출하 | AS9102/PPAP FAI 양식으로 1st Article 측정결과, CMM report, 재료·공정 certificate 수록. 최종성적서(CoC: ISO 17025 기준 시험성적), UDI(ISO 15459, GS1-128 바코드/DM Code), 고객 라벨(UDI-DI/UDI-PI, Lot/Serial, 유효기간)과 출하단위를 일치시킨다. |

### 1.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户图纸与法规要求基准 | 确认图纸版本、ISO 13485/QMSR适用性、客户CTQ及长期记录要求。同时审查ASTM F67(纯Ti)、F136(Ti-6Al-4V ELI)、F2063(NiTi)、F90(CoCr)等材料规格基准及510(k)/PMA要求。 |
| 2 | 原材料 Heat/Lot 到货与验证 | 确认金属 Heat No、MTC/CoA、成分与机械性能、供应商批准状态。按Lot执行拉伸试验(UTM, 参照ASTM E8/E21)、硬度试验(Rockwell/Vickers)、超声波探伤(UT, ASTM A388)。入库Gate设定NCR签发标准。 |
| 3 | 切割·锻造·轧制预处理 | 带锯/水刀切割(切割速度50~200 mm/min, 冷却水温控)、锻造(加热温度850~1150℃, 保温时间30~120min)、轧制(Reduction 20~50%/pass, 轧制速度2~10 m/min)条件与材料谱系连接。Lot Split/merge时生成半成品ID。 |
| 4 | 拉拔·管材·线材成形 | 管理NiTi、精密线材、管材的拉拔条件(Die angle 6~15°, Reduction 15~30%/pass, 拉拔速度1~20 m/min)、直径(±0.01mm)、壁厚(±0.005mm)、直线度(0.5mm/m max)。按Coil/Reel追踪Mandrel/Turks head更换履历和Drawing Die ID。 |
| 5 | CNC·磨削精密加工 | 5轴CNC Swiss-type(Star, Tsugami等)或多轴磨床(Mikron, Studer)，将NC程序、CBN/金刚石刀具、夹具offset与零件序列号连接以形成尺寸质量(±0.002~0.01mm)。记录主轴转速2,000~15,000RPM、进给0.005~0.1 mm/rev作为工艺条件。 |
| 6 | 热处理与形状记忆设定 | 真空热处理炉(Schemetrical/Ipsen, 10^-4~10^-6 Torr)、NiTi形状记忆处理(400~550℃, Ar气氛, 急冷/时效)、固溶处理(ST)800~900℃加热后水冷、时效400~500℃×10~60min。炉温曲线(±5℃均匀性)和装载方式连接到Heat Treat Lot。 |
| 7 | 表面处理与钝化 | 钝化(ASTM A967, 20~50% HNO₃, 30~60min, 20~60℃)、电抛光(电解液温度40~70℃, 电流密度0.1~1.0 A/cm²)、微喷砂、阳极氧化(Ti用, ASTM B136)等外协/自处理证书连接到零件序列号。适用表面粗糙度Ra≤0.4μm标准。 |
| 8 | 过程尺寸与表面计量 Gate | CMM(Zeiss/Hexagon, ±0.5μm精度)、表面粗糙度(Stylus/白光干涉仪, Ra/Rz/Rt测量)、视觉系统(Keyence LM系列, 缺陷检测)、过程能力(Cpk≥1.33)结果作为Gate判断。测量结果不一致时由NCR→MRB路径确定Rework/Scrap。 |
| 9 | 清洗与洁净包装 | 超声波清洗(40~80kHz, 40~70℃, 去离子水/酒精)、Rinse(18MΩ·cm DI水, 最终3次)、颗粒/离子污染(LPC/IC)、清洗配方版本、包装材料PE/Nylon Bag Lot、Class 10k/100k洁净环境和保存条件(温度15~30℃, 湿度20~75%RH)。 |
| 10 | FAI·CoC·UDI 出货 | 以AS9102/PPAP FAI格式收录首件测量结果、CMM报告、材料/工艺证书。保证最终报告(CoC: 按ISO 17025标准的试验成绩)、UDI(ISO 15459, GS1-128条码/DM码)、客户标签(UDI-DI/UDI-PI, Lot/Serial, 有效期)与出货单元一致。 |

### 1.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: PLM/EDM 시스템에서 BOM/BOP 버전 비교. 주기: Every Work Order. 이상 시 Engineering Change Notice(ECN) 발행 후 재검토. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: MES Genealogy 기능으로 상하위 연결 검증. 방법: Heat No→Bar/Billet ID→Serial No→Shipment Lot 단계별 추적. 주기: Every Lot. 이상 시 Lot Hold 후 원인조사. | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건(Lot/Serial 단위)을 MES/PDA로 수집한다. 측정: Machine parameter logger 출력값과 recipe 기준값 비교. 주기: Every Batch/Lot. 이상 시 Machine Lock → 재교정 후 Lot 단위 재처리 또는 격리. | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: CMM program(Z810, Calypso, PC-DMIS) 실행 → 자동 Pass/Fail 판정. 주기: Every Lot(a2LA, ANSI Z540). 이상 시 NCR 발행 → MRB 검토(Rework/Scrap/Use-As-Is 결정). | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate(NADCAP)를 원부품 계보와 연결한다. 측정: 외주 수입 시 CoC 내용 검토(Certificate 번호, Lot/Serial 일치). 주기: Every outsourcing Lot. 이상 시 Receiving Inspection Fail → 반송 또는 현장 재작업. | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: 출하 전 Scan Gun으로 UDI/Lot 바코드 스캔 → ERP/Shipment Module 자동매칭. 주기: Real-time(Every Pallet/Box). 이상 시 Shipment Hold → 문서·Label 재발행. | [10] | process_step | 출하·문서·규제 |

### 1.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: PLM/EDM系统中BOM/BOP版本对比。周期: Every Work Order。异常时: 签发Engineering Change Notice(ECN)后重新审核。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: MES Genealogy功能验证上下级连接。方法: Heat No→Bar/Billet ID→Serial No→Shipment Lot逐级追溯。周期: Every Lot。异常时: Lot Hold后原因调查。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 设备参数记录仪输出值与Recipe基准值对比。周期: Every Batch/Lot。异常时: Machine Lock→重新校准后逐Lot处理或隔离。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: CMM程序(Z810, Calypso, PC-DMIS)执行→自动Pass/Fail判定。周期: Every Lot(a2LA, ANSI Z540)。异常时: 签发NCR→MRB审核(Rework/Scrap/Use-As-Is决定)。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书(NADCAP)连接到原零件谱系。测量: 外协入库时审查CoC内容(证书号、Lot/Serial一致性)。周期: Every outsourcing Lot。异常时: 入库检验Fail→退货或现场返工。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: 出货前使用扫描枪扫描UDI/Lot条码→ERP/出货模块自动匹配。周期: Real-time(Every Pallet/Box)。异常时: Shipment Hold→文件/标签重新签发。 | [10] | process_step | 出货·文件·法规 |

### 1.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_spec, heat_no |
| 2 | Material | process |  |  | material_spec, heat_no, material_lot, supplier_cert_id |
| 3 | Prep | process |  |  | material_lot, supplier_cert_id, melt_batch_id, work_order_id |
| 4 | Primary Process | process |  |  | melt_batch_id, work_order_id, serial_no, machine_id |
| 5 | Precision Process | process |  |  | serial_no, machine_id, nc_program_rev, fixture_id |
| 6 | Thermal/Special | process |  |  | nc_program_rev, fixture_id, tool_id, heat_treat_lot |
| 7 | Surface/Clean | process |  |  | tool_id, heat_treat_lot, surface_treatment_lot, cleaning_lot |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | surface_treatment_lot, cleaning_lot, inspection_report_id, cmm_program_id |
| 9 | Pack | process |  |  | inspection_report_id, cmm_program_id, coc_id, udi_code |
| 10 | Release | process |  |  | coc_id, udi_code, mrb_id |

### 1.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_spec, heat_no |
| 2 | Material | process |  |  | material_spec, heat_no, material_lot, supplier_cert_id |
| 3 | Prep | process |  |  | material_lot, supplier_cert_id, melt_batch_id, work_order_id |
| 4 | Primary Process | process |  |  | melt_batch_id, work_order_id, serial_no, machine_id |
| 5 | Precision Process | process |  |  | serial_no, machine_id, nc_program_rev, fixture_id |
| 6 | Thermal/Special | process |  |  | nc_program_rev, fixture_id, tool_id, heat_treat_lot |
| 7 | Surface/Clean | process |  |  | tool_id, heat_treat_lot, surface_treatment_lot, cleaning_lot |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | surface_treatment_lot, cleaning_lot, inspection_report_id, cmm_program_id |
| 9 | Pack | process |  |  | inspection_report_id, cmm_program_id, coc_id, udi_code |
| 10 | Release | process |  |  | coc_id, udi_code, mrb_id |

### 1.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 1.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 1.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - drawing_rev
  - material_spec
  - heat_no
  - material_lot
  - supplier_cert_id
  - melt_batch_id
  - work_order_id
  - serial_no
  - machine_id
  - nc_program_rev
  - fixture_id
  - tool_id
  - heat_treat_lot
  - surface_treatment_lot
  - cleaning_lot
  - inspection_report_id
  - cmm_program_id
  - coc_id
  - udi_code
  - mrb_id
```

---

## 2. I02 `precision_machined_metal_components` — 정밀 금속가공 부품 / 精密金属加工零件

```yaml
subindustry_code: I02
legacy_slug: "precision_machined_metal_components"
label_ko: "정밀 금속가공 부품"
label_zh: "精密金属加工零件"
label_en: ""
label_ja: ""
routing: "RT_JOBSHOP"
preset_id: "precision_jobshop_v1"
expression_tier: "P2"
```

> ko: CNC·연삭·절삭·복합가공 부품의 다품종 정밀 Job Shop 흐름.  
> zh: CNC、磨削、切削、复合加工零件的多品种精密 Job Shop 流程。

### 2.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 수주·도면·BOP 기준선 | 도면, 공차(ISO 2768-m/f, ASME Y14.5 GD&T), 표면거칠기(Ra 0.1~3.2μm), 검사계획, BOP와 납기 우선순위를 확정한다. 고객 PO 수주 시 Work Order를 발행하고 revision lock을 건다. |
| 2 | 소재 입고·절단 | 소재 lot(봉재/판재/형강), 규격, 절단 수량과 잔재 재고를 work order에 연결한다. 밴드쏘/원형톱 절단(절단속도 30~100 m/min, 냉각수 유량 5~15 L/min) 및 잔재바 ID를 ERP에서 관리한다. 절단면 Burr/변형 검사(Burr 높이 ≤0.2mm)를 수반한다. |
| 3 | 공정 Route Release | 공정 순서(선삭→밀링→드릴→연삭→외주열처리), 외주 여부, 설비군(Mazak/Doosan/Mori Seiki 등), 치구·공구 준비상태를 release한다. CAM Post-processor에서 NC program 생성 완료 여부와 작업표준서를 함께 release한다. |
| 4 | CNC 선삭·밀링 | 주요 치수(공차 ±0.01~0.05mm)와 가공시간을 좌우하는 NC program, Tool ID(DIN 69871, HSK-B63/100), offset(x,y,z 값), Spindle Load 모니터링값을 기록한다. CNC 선삭(Spindle 1,500~6,000 RPM, Feed 0.05~0.5 mm/rev), 밀링(Spindle 2,000~12,000 RPM, Stepover 0.2~2mm). |
| 5 | 연삭·방전·레이저 가공 | 고정밀 형상(공차 ±0.002~0.01mm)은 연삭(Grinding Wheel WA/GC, RPM 15,000~30,000, Coolant Filter 10μm), EDM(Wire EDM: Brass Wire φ0.2~0.3mm, 최종 Cut Ra≤0.4μm), Laser(피코초/나노초, Power 20~200W) 조건과 검사 결과를 serial에 연결한다. |
| 6 | 열처리·외주공정 | 열처리(침탄/질화/고주파 담금질, HRC 40~65 조건), 도금(경질Cr/Zn/Ni, 두께 5~50μm), 코팅(PTFE, AlCrN, TiAlN) 외주 반출입, certificate(NADCAC/ISO 9001), 재입고 상태를 outsourcing_lot 단위로 추적한다. 외주 후 입고검사(경도, 두께, 외관)를 Gate로 운영한다. |
| 7 | 세정·디버링·표면처리 | 디버링(에어 브러시/열적 디버링/전해 디버링), burr 잔류 검사(10x 현미경 육안검사 또는 Vision System), 표면 결함, 세정 상태(초음파 + 수세)를 확인한다. Burr 잔량 기준 ≤0.05mm 적용. 세정 후 부식방지 오일 도포(밀봉포장용). |
| 8 | CMM·치수검사 Gate | CMM program(Zeiss CALYPSO, Hexagon PC-DMIS, 측정속도 20~80 mm/s, Probe TIP φ1~5mm), Gauge calibration(Plug/Ring Gauge 교정주기 6~12개월), 측정 결과와 pass/fail을 Gate로 판단한다. Vision System(Keyence LM, Mitutoyo QV)을 조도·외형 검사에 병행한다. Cpk≥1.33 요구. |
| 9 | 조립·마킹·포장 | 레이저 마킹(CO₂/Fiber Laser, Power 10~50W, Speed 200~1,500 mm/s, Marking depth 0.01~0.05mm), Sub-assembly(나사체결토크관리, Loctite/접착제 Lot 관리), 포장단위(케이스/블리스터/크레이트)와 고객 PO를 연결한다. Dry Pack/VCI 포장지 적용 기준. |
| 10 | 최종검사·출하 | 최종검사(기능검사 Gage R&R Φ10% 이하, 누설시험 헬륨/수압 0.1~1.0MPa, NDT 침투탐상/자분탐상), NCR/MRB 상태 해소 여부 확인, 출하 lot과 성적서(CoC, 검사성적서 차트) 완결성을 확인한다. |

### 2.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 订单·图纸·BOP 基准 | 确认图纸、公差(ISO 2768-m/f, ASME Y14.5 GD&T)、表面粗糙度(Ra 0.1~3.2μm)、检验计划、BOP与交期优先级。客户PO下单时签发Work Order并锁定版本。 |
| 2 | 材料入库与切割 | 将材料Lot(棒材/板材/型材)、规格、切割数量和余料库存连接到工单。带锯/圆锯切割(切割速度30~100 m/min, 冷却液流量5~15 L/min)并在ERP中管理余料ID。附带切割面毛刺/变形检查(毛刺高度≤0.2mm)。 |
| 3 | 工艺路线Release | Release工序顺序(车削→铣削→钻孔→磨削→外协热处理)、外协与否、设备组(Mazak/Doosan/Mori Seiki等)、夹具/刀具准备状态。同时确认CAM后处理生成的NC程序版本和作业指导书状态。 |
| 4 | CNC 车削·铣削 | 记录影响关键尺寸(公差±0.01~0.05mm)与加工时间的NC程序、刀具ID(DIN 69871, HSK-B63/100)、offset(x,y,z值)、主轴负载监控值。CNC车削(主轴1,500~6,000RPM, 进给0.05~0.5mm/rev)、铣削(主轴2,000~12,000RPM, Stepover 0.2~2mm)。 |
| 5 | 磨削·放电·激光加工 | 高精度形状(公差±0.002~0.01mm)需将磨削(砂轮WA/GC, RPM 15,000~30,000, 冷却液过滤10μm)、EDM(Wire EDM: Brass Wire φ0.2~0.3mm, 最终Cut Ra≤0.4μm)、激光(皮秒/纳秒, 功率20~200W)条件与检验结果连接到序列号。 |
| 6 | 热处理与外协工序 | 热处理(渗碳/渗氮/高频淬火, HRC 40~65条件)、电镀(硬Cr/Zn/Ni, 厚度5~50μm)、涂层(PTFE, AlCrN, TiAlN)的外协出入、证书(NADCAP/ISO 9001)、再入库状态以outsourcing_lot追踪。外协后入库检查(硬度、厚度、外观)作为Gate。 |
| 7 | 清洗·去毛刺·表面处理 | 去毛刺(气刷/热去毛刺/电解去毛刺)、毛刺残留检查(10x显微镜目视或视觉系统)、表面缺陷、清洗状态(超声波+水洗)。毛刺残留标准≤0.05mm。清洗后涂防锈油(密封包装用)。 |
| 8 | CMM·尺寸检验 Gate | 以CMM程序(Zeiss CALYPSO, Hexagon PC-DMIS, 测量速度20~80 mm/s, 测针TIP φ1~5mm)、量具校准(塞规/环规校准周期6~12个月)、测量结果和pass/fail作为Gate判断。视觉系统(Keyence LM, Mitutoyo QV)并行用于粗糙度和外观检查。Cpk≥1.33要求。 |
| 9 | 装配·打标·包装 | 激光打标(CO₂/光纤激光, 功率10~50W, 速度200~1,500 mm/s, 深度0.01~0.05mm)、子装配(螺栓扭矩管理, Loctite/胶粘剂Lot管理)、包装单元(盒/泡壳/木箱)与客户PO连接。适用Dry Pack/VCI防锈纸标准。 |
| 10 | 最终检验与出货 | 最终检验(功能检具Gage R&R≤10%, 泄漏试验氦/水压0.1~1.0MPa, NDT渗透探伤/磁粉探伤)、NCR/MRB状态解除确认、出货Lot与报告(CoC, 检验报告图表)完整性核查。 |

### 2.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: PLM/ERP BOM 버전 Diff Tool 비교. 주기: Every Work Order Release. 이상 시 ECN 발행 → 변경영향분석 → Work Order 갱신. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: MES Barcode Scanner로 수불이력 스캔검증. 방법: Material Lot→Operation Lot→Serial No→Shipment Lot. 주기: Every Transaction. 이상 시 Transaction Rollback 후 재 Scanning. | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: CNC Load Meter, Coolant Temp(20~30℃), Spindle Vibration Sensor. 주기: Every Cycle(Real-time). 이상 시 Alarm 발생 → 즉시 Machine Stop → Lot 격리. | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: CMM 실행報告 자동 Pass/Fail, 미니탭 Cpk Report(≥1.33). 주기: Every Lot(초품 검사 + 주기 Sampling AQL 기준). 이상 시 NC Program 재검토 → Offset 조정 → 재측정. | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: 외주 CoC 수령 시 경도테스트(HRC/HV) 자체 검증. 주기: Every Outsourcing Lot. 이상 시 납품사 품질회의 → 공정 승인 재평가(Re-qualification). | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: ERP Shipment Module 라벨/성적서 Auto-matching. 주기: Real-time(Every Box). 이상 시 라벨 재발행 + 내부 부적합 보고서 작성. | [10] | process_step | 출하·문서·규제 |

### 2.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: PLM/ERP BOM版本Diff Tool对比。周期: Every Work Order Release。异常时: 签发ECN→变更影响分析→更新工单。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: MES条码扫描器验证收发货履历。方法: Material Lot→Operation Lot→Serial No→Shipment Lot。周期: Every Transaction。异常时: Transaction Rollback后重新扫描。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: CNC负载表、冷却液温度(20~30℃)、主轴振动传感器。周期: Every Cycle(Real-time)。异常时: Alarm发出→立即Machine Stop→Lot隔离。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: CMM执行报告自动Pass/Fail、Minitab Cpk报告(≥1.33)。周期: Every Lot(首件检验+按AQL抽检)。异常时: NC程序重审→Offset调整→重新测量。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: 外协CoC收取时自行验证硬度试验(HRC/HV)。周期: Every Outsourcing Lot。异常时: 供应商质量会议→工艺批准重新评估(Re-qualification)。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: ERP出货模块标签/报告自动匹配。周期: Real-time(Every Box)。异常时: 标签重发+内部不符合报告编写。 | [10] | process_step | 出货·文件·法规 |

### 2.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_spec, material_lot |
| 2 | Material | process |  |  | material_spec, material_lot, work_order_id, serial_no |
| 3 | Prep | process |  |  | work_order_id, serial_no, operation_seq, machine_id |
| 4 | Primary Process | process |  |  | operation_seq, machine_id, nc_program_rev, fixture_id |
| 5 | Precision Process | process |  |  | nc_program_rev, fixture_id, tool_id, offset_id |
| 6 | Thermal/Special | process |  |  | tool_id, offset_id, inspection_report_id, cmm_program_id |
| 7 | Surface/Clean | process |  |  | inspection_report_id, cmm_program_id, surface_roughness, rework_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | surface_roughness, rework_id, outsourcing_lot, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | outsourcing_lot, shipment_lot |
| 10 | Release | process |  |  | surface_roughness, rework_id, outsourcing_lot, shipment_lot |

### 2.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_spec, material_lot |
| 2 | Material | process |  |  | material_spec, material_lot, work_order_id, serial_no |
| 3 | Prep | process |  |  | work_order_id, serial_no, operation_seq, machine_id |
| 4 | Primary Process | process |  |  | operation_seq, machine_id, nc_program_rev, fixture_id |
| 5 | Precision Process | process |  |  | nc_program_rev, fixture_id, tool_id, offset_id |
| 6 | Thermal/Special | process |  |  | tool_id, offset_id, inspection_report_id, cmm_program_id |
| 7 | Surface/Clean | process |  |  | inspection_report_id, cmm_program_id, surface_roughness, rework_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | surface_roughness, rework_id, outsourcing_lot, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | outsourcing_lot, shipment_lot |
| 10 | Release | process |  |  | surface_roughness, rework_id, outsourcing_lot, shipment_lot |

### 2.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 2.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 2.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - drawing_rev
  - material_spec
  - material_lot
  - work_order_id
  - serial_no
  - operation_seq
  - machine_id
  - nc_program_rev
  - fixture_id
  - tool_id
  - offset_id
  - inspection_report_id
  - cmm_program_id
  - surface_roughness
  - rework_id
  - outsourcing_lot
  - shipment_lot
```

---

## 3. I03 `special_alloy_high_purity_metal` — 특수합금·고순도 금속 / 特殊合金与高纯金属

```yaml
subindustry_code: I03
legacy_slug: "special_alloy_high_purity_metal"
label_ko: "특수합금·고순도 금속"
label_zh: "特殊合金与高纯金属"
label_en: ""
label_ja: ""
routing: "RT_BATCH"
preset_id: "batch_process_v1"
expression_tier: "P2"
```

> ko: 고온·내식 합금, 정밀합금, 자성재료, 고순도 금속·스퍼터 타깃의 Heat/Batch 중심 흐름.  
> zh: 高温/耐蚀合金、精密合金、磁性材料、高纯金属/溅射靶材的 Heat/Batch 中心流程。

### 3.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 소재사양·고객 Qual 기준선 | 합금규격(ASTM B348/AMS 4928 등), 불순물 한계(ppm/ppb level), 고객 승인 route와 공급망 trace 요구(IEA Critical Mineral 원산지 증명)를 확정한다. 고객 Product Qualification 승인 이력을 검토하고 재-Qual 필요여부를 결정한다. |
| 2 | 원료·스크랩·첨가재 입고 | 원료 lot(VIM/VAR용 Scrap, Master Alloy), 원산지(US/EU Origin Declaration), 스크랩 혼입비(≤30%), 첨가재(C, Si, Mn, Ti-B 등) 보관조건과 SAS(Supplier Approval Status)를 확인한다. XRD/XRF로 입고 성분 스크리닝을 수행한다. |
| 3 | 계량·Charge 구성 | 전자식 저울(정밀도 ±0.1g~±10g, Calibration 주기 월 1회), Charge 구성(약 50~500kg/batch), 작업자(용해사/금속기사 자격증) 승인과 Recipe revision(합금 비율 불변경 확인)을 기록한다. Charge Sheet를 ERP/Batch Record에 입력한다. |
| 4 | 용해·정련·탈가스 | VIM(Vacuum Induction Melting, 10^-2~10^-3 mbar, 온도 1,400~1,700℃), VAR(Vacuum Arc Remelting, 10^-4~10^-5 mbar, 전류 5~30kA), ESR(Electro-Slag Remelting, 슬래그 조성 CaF₂/CaO/Al₂O₃) 중 선택. 진공도, Ar 분위기, 탈가스 시간(10~60min), 용탕 온도(±5℃)를 heat no에 연결한다. |
| 5 | 주조·Ingot 형성 | Ingot ID(Heat ID + Ingot 번호), 주조조건(주입온도 1,450~1,650℃, 주입속도 1~10 kg/min, 주형재질 Cu/Graphite), 수축공/균열 UT 검사(ASTM A388, Frequency 2.25~5MHz), 표면결함 VT 검사를 기록한다. Ingot Weight 50~5,000kg 범위. |
| 6 | 균질화·단조·압연 | 균질화(1,050~1,250℃, 2~24h 유지), 단조(자유단조/금형단조, Forging Ratio 3:1~10:1, 온도 850~1,200℃), 압연(Hot Rolling 900~1,200℃, Reduction 20~50%/pass, 냉간압연 Optional)의 reduction, 온도, lot split/merge를 관리한다. 열간가공 후 서냉/급냉 조건. |
| 7 | 열처리·절단·가공 | 열처리(용체화처리/시효/응력제거, Furnace Profile ±10℃ 유지)와 절단(밴드쏘/플라즈마/EDM), 가공(CNC, 밀링, 그라인딩) 이력을 billet/bar/target 단위로 연결한다. Target 가공 시 Bonding Plate와의 접합 조건(무산소동/알루미늄 Backing Plate). |
| 8 | 성분·물성 Lab Gate | OES/ICP-MS 성분(정밀도 ppm~ppb), LECO 불순물(C/S/O/N/H 분석), 결정립 크기(ASTM E112), 인장/경도/파괴인성 결과로 batch release를 판단한다. Lab Gate Fail 시 Batch Quarantine→MRB→Recipe 재설계→재용해 경로로 진행. |
| 9 | 세정·포장·보관 | 산화·오염 방지(VCI Paper/질소퍼지 Seal, Silica Gel Dry Pack), 포장재(합판상자/플라스틱 컨테이너), 보관환경(온도 15~35℃, 습도 30~70%RH), Container ID(Shipping Mark 기준)를 관리한다. Critical Mineral Custody 정보를 포장 라벨에 포함. |
| 10 | CoA·출하·공급망 추적 | CoA(MIL-STD-1636/EN 10204 Type 3.1), 원산지 증명, Critical Mineral Custody Chain(광산→제련소→가공→출하), 고객출하 lot을 연결한다. 선적서류(Packing List + Commercial Invoice + CoA Bundle) 완결성 확인. |

### 3.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 材料规格与客户 Qual 基准 | 确认合金规格(ASTM B348/AMS 4928等)、杂质限值(ppm/ppb级)、客户批准路线和供应链追溯要求(IEA关键矿物原产地证明)。审核客户Product Qualification批准履历并决定是否需要Re-Qual。 |
| 2 | 原料·回炉料·添加剂入库 | 确认原料Lot(VIM/VAR用回炉料、母合金)、原产地(US/EU原产地声明)、回炉料比例(≤30%)、添加剂(C, Si, Mn, Ti-B等)保存条件与SAS(供应商批准状态)。使用XRD/XRF进行入库成分筛查。 |
| 3 | 称量与 Charge 构成 | 电子秤(精度±0.1g~±10g, 校准周期每月1次)、Charge构成(约50~500kg/batch)、操作人员(熔炼师/金属技师资质)批准与Recipe版本(确认合金比例不变)记录。将Charge Sheet输入ERP/Batch Record。 |
| 4 | 熔炼·精炼·脱气 | VIM(真空感应熔炼, 10^-2~10^-3 mbar, 温度1,400~1,700℃)、VAR(真空电弧重熔, 10^-4~10^-5 mbar, 电流5~30kA)、ESR(电渣重熔, 渣系CaF₂/CaO/Al₂O₃)中选择。真空度、Ar气氛、脱气时间(10~60min)、熔液温度(±5℃)连接到Heat No。 |
| 5 | 铸造与 Ingot 形成 | Ingot ID(Heat ID+Ingot编号)、铸造条件(浇注温度1,450~1,650℃, 浇注速度1~10 kg/min, 铸型材质Cu/Graphite)、缩孔/裂纹UT检查(ASTM A388, 频率2.25~5MHz)、表面缺陷VT检查记录。Ingot重量50~5,000kg范围。 |
| 6 | 均质化·锻造·轧制 | 均质化(1,050~1,250℃, 保温2~24h)、锻造(自由锻/模锻, Forging Ratio 3:1~10:1, 温度850~1,200℃)、轧制(热轧900~1,200℃, Reduction 20~50%/pass, 冷轧可选)管理Reduction、温度和Lot split/merge。热加工后缓冷/急冷条件。 |
| 7 | 热处理·切割·加工 | 热处理(固溶处理/时效/去应力, 炉温曲线±10℃保持)与切割(带锯/等离子/EDM)、加工(CNC、铣削、磨削)履历以billet/bar/target单位连接。靶材加工时记录与背板(无氧铜/铝背板)的结合条件。 |
| 8 | 成分·物性 Lab Gate | 以OES/ICP-MS成分(精度ppm~ppb)、LECO杂质(C/S/O/N/H分析)、晶粒度(ASTM E112)、拉伸/硬度/断裂韧性结果判断Batch Release。Lab Gate Fail时按Batch Quarantine→MRB→Recipe重新设计→重熔路径进行。 |
| 9 | 清洗·包装·保存 | 防氧化/防污染(VCI纸/氮气吹扫密封、硅胶干燥包)、包装材料(胶合板箱/塑料容器)、保存环境(温度15~35℃, 湿度30~70%RH)、Container ID(按Shipping Mark)管理。在包装标签中包含关键矿物Custody信息。 |
| 10 | CoA·出货·供应链追踪 | 连接CoA(MIL-STD-1636/EN 10204 Type 3.1)、原产地证明、关键矿物Custody Chain(矿山→冶炼→加工→出货)、客户出货Lot。确认装运文件(装箱单+商业发票+CoA包)完整性。 |

### 3.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: ERP Recipe/Formula 버전과 실제 Charge Sheet 비교. 주기: Every Batch. 이상 시 Batch On-Hold → Recipe 롤백 또는 ECN 발행. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: Heat No→Ingot No→Billet ID→Target Serial→Shipment Lot. 방법: ERP Batch Traceability Module. 주기: Every Heat. 이상 시 Heat Lot 격리 + 원료 공급사 조사. | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: Furnace Temperature Logger(열전대 Type K/R, ±0.5℃), 진공계(Pirani/Gauges). 주기: Every Batch(1초~1분 Logging Interval). 이상 시 Furnace Profile 재교정 → 해당 Batch 재처리. | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: OES/ICP-MS(자동 시료 주입, Calibration 표준용액 비교). 주기: Every Heat/Melt(용해당 1회~3회 샘플링). 이상 시 Batch Quarantine→MRB→Recipe 재검토→재용해/Scrap 결정. | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: 외주 열처리 로그(온도 기록지) 검토, NADCAP 인증 확인. 주기: Every Outsourcing Heat. 이상 시 Outsourcer 현장 감사 → 승인 취소 재검토. | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: CoA 출하값과 Lab Gate 결과 대조(성분/기계적물성). 주기: Every Shipment Lot. 이상 시 Shipment Hold → CoA 재작성 또는 Lab 재시험. | [10] | process_step | 출하·문서·규제 |

### 3.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: ERP Recipe/Formula版本与实际Charge Sheet对比。周期: Every Batch。异常时: Batch On-Hold→Recipe回滚或签发ECN。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: Heat No→Ingot No→Billet ID→Target Serial→Shipment Lot。方法: ERP Batch Traceability Module。周期: Every Heat。异常时: Heat Lot隔离+原料供应商调查。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 炉温记录仪(热电偶Type K/R, ±0.5℃)、真空计(Pirani/Gauges)。周期: Every Batch(1秒~1分钟记录间隔)。异常时: Furnace Profile重新校准→对应Batch重新处理。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: ICP-MS(自动进样, 标准溶液校准比对)。周期: Every Heat/Melt(每熔炼1~3次取样)。异常时: Batch Quarantine→MRB→Recipe重审→重熔/Scrap决定。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: 外协热处理日志(温度记录纸)审核, NADCAP认证确认。周期: Every Outsourcing Heat。异常时: 外协厂现场审核→重新评估批准状态。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: CoA出货值与Lab Gate结果对照(成分/机械性能)。周期: Every Shipment Lot。异常时: Shipment Hold→CoA重写或Lab复测。 | [10] | process_step | 出货·文件·法规 |

### 3.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, material_spec, raw_material_lot, origin_id |
| 2 | Material | process |  |  | raw_material_lot, origin_id, heat_no, charge_id |
| 3 | Prep | batch |  |  | heat_no, charge_id, melt_batch_id, furnace_id |
| 4 | Primary Process | batch |  |  | melt_batch_id, furnace_id, recipe_id, composition_result |
| 5 | Precision Process | process |  |  | recipe_id, composition_result, ingot_id, billet_id |
| 6 | Thermal/Special | process |  |  | ingot_id, billet_id, rolling_lot, heat_treat_lot |
| 7 | Surface/Clean | process |  |  | rolling_lot, heat_treat_lot, sample_id, lab_result_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | sample_id, lab_result_id, coa_id, container_id |
| 9 | Pack | process |  |  | coa_id, container_id, shipment_lot |
| 10 | Release | process |  |  | lab_result_id, coa_id, container_id, shipment_lot |

### 3.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, material_spec, raw_material_lot, origin_id |
| 2 | Material | process |  |  | raw_material_lot, origin_id, heat_no, charge_id |
| 3 | Prep | batch |  |  | heat_no, charge_id, melt_batch_id, furnace_id |
| 4 | Primary Process | batch |  |  | melt_batch_id, furnace_id, recipe_id, composition_result |
| 5 | Precision Process | process |  |  | recipe_id, composition_result, ingot_id, billet_id |
| 6 | Thermal/Special | process |  |  | ingot_id, billet_id, rolling_lot, heat_treat_lot |
| 7 | Surface/Clean | process |  |  | rolling_lot, heat_treat_lot, sample_id, lab_result_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | sample_id, lab_result_id, coa_id, container_id |
| 9 | Pack | process |  |  | coa_id, container_id, shipment_lot |
| 10 | Release | process |  |  | lab_result_id, coa_id, container_id, shipment_lot |

### 3.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 3.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 3.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - material_spec
  - raw_material_lot
  - origin_id
  - heat_no
  - charge_id
  - melt_batch_id
  - furnace_id
  - recipe_id
  - composition_result
  - ingot_id
  - billet_id
  - rolling_lot
  - heat_treat_lot
  - sample_id
  - lab_result_id
  - coa_id
  - container_id
  - shipment_lot
```

---

## 4. I04 `ceramic_materials_components` — 세라믹 소재·부품 / 陶瓷材料与部件

```yaml
subindustry_code: I04
legacy_slug: "ceramic_materials_components"
label_ko: "세라믹 소재·부품"
label_zh: "陶瓷材料与部件"
label_en: ""
label_ja: ""
routing: "RT_JOBSHOP_BATCH"
preset_id: "precision_jobshop_v1"
expression_tier: "P2"
```

> ko: 전자·구조 세라믹, 세라믹 기판, 내열·내마모 부품의 분말-성형-소결-가공 흐름.  
> zh: 电子/结构陶瓷、陶瓷基板、耐热/耐磨部件的粉体-成形-烧结-加工流程。

### 4.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객사양·재료조성 기준선 | 조성(Al₂O₃ 94~99.9%, ZrO₂, SiC, Si₃N₄ 등), 소결수축률(15~25%), 치수공차(±0.01~0.1mm), 표면 요구(Ra 0.05~0.8μm)와 고객 승인조건을 확정한다. 고객 특성시험 규격(절연파괴전압, 열전도율, 내열충격)을 검토한다. |
| 2 | 분말·바인더 입고 | 분말 lot(알루미나/지르코니아/탄화규소), 입도(D10/D50/D90, Laser Diffraction Method), 수분(≤0.5% by Karl Fischer), 바인더(PVA/PEG/Acrylic, 유효기간 6~12개월) lot와 유효기간을 확인한다. 분말 Lot당 밀도(Tap Density/True Density) 측정값 기록. |
| 3 | 배합·분쇄·Granulation | 배합비(세라믹 분말:바인더:용제=100:3~15:20~50 wt%), 분쇄시간(Ball Mill/Attritor Mill, 2~24h), slurry 점도(100~5,000 cP, Brookfield Viscometer), Granule 조건(Spray Dryer, Inlet Temp 200~350℃, Outlet Temp 80~120℃, Granule Size 50~500μm)을 batch로 관리한다. |
| 4 | 성형·Press·Green Body | Press 조건(Uniaxial Press 50~300 MPa/CIP 100~400 MPa/Iso-static Press), 금형(Mold ID, 마모율, 교체주기 5,000~50,000 Shot), Green Body ID와 균열·칩 상태(WLI 10x 검사)를 추적한다. Green Density(이론밀도의 50~65%) 측정 및 기록. |
| 5 | 탈지·소결·Firing | Kiln(Batch Kiln/Pusher Kiln/Roller Hearth Kiln, 최고온도 1,300~1,750℃), Firing Profile(승온속도 50~300℃/h, 유지시간 1~10h, 냉각속도 50~200℃/h), 분위기(Air/N₂/Ar/H₂) 및 적재패턴, 수축률(15~25%)을 관리한다. 소결밀도(이론밀도의 95~99.9%) 검사. |
| 6 | HIP·열처리·치밀화 | HIP(1,350~1,650℃, 100~200MPa Ar, 유지 1~4h), 열처리(응력제거 800~1,200℃, 1~2h), 밀도(Archimedes Method, KS L 4008)와 미세구조 결과(SEM ×1,000~5,000, Grain Size ASTM E112)를 연결한다. HIP로 제품 표면 접촉면 관리(Powder Packing 유무). |
| 7 | 연삭·Lapping·가공 | Diamond Grinding(Wheel D46~D151, RPM 2,000~6,000, Feed 0.005~0.1 mm/pass), Lapping(Al₂O₃/SiC Slurry, 입도 3~15μm), Edge Chipping(≤0.1mm 기준), 표면거칠기(Ra 0.02~0.4μm)를 관리한다. 가공 후 초음파 세정(40kHz, 5~10min) 수반. |
| 8 | 치수·밀도·Warpage Gate | 치수(마이크로미터/Vision Measuring System, ±0.001mm 분해능), 밀도(Archimedes, ±0.01 g/cm³), Warpage(Flatness Gauge/Talysurf, ≤0.05mm), 균열 Dye Penetrant 검사, 절연/열전도 특성(절연저항계/Laser Flash Method)으로 Gate 판단한다. NCR 발생 시 Rework/Downgrade 결정. |
| 9 | 세정·검사·포장 | 세정도(입자 검사: LPC/Filter Pad Method 0.5~10μm, Class 100~1,000 수준), 파티클, 포장재(ESD Bag/폼/격벽) Lot와 취급 손상(Edge Chip/Breakage)을 관리한다. Moisture Barrier Bag(MBB) 사용 시 Dry Pack 조건 확인. |
| 10 | CoA·출하 | CoA(밀도, 치수, 절연특성, 비파괴검사 결과), 검사성적서(차트 그룹), 출하 lot과 고객승인 상태(First Article/Pilot Lot)를 연결한다. 포장 상태 사진 기록 및 증빙 보관. |

### 4.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户规格与材料组成基准 | 确认组成(Al₂O₃ 94~99.9%, ZrO₂, SiC, Si₃N₄等)、烧结收缩率(15~25%)、尺寸公差(±0.01~0.1mm)、表面要求(Ra 0.05~0.8μm)与客户批准条件。审核客户特性试验规格(绝缘击穿电压、导热率、耐热冲击)。 |
| 2 | 粉体·粘结剂入库 | 确认粉体Lot(氧化铝/氧化锆/碳化硅)、粒度(D10/D50/D90, Laser Diffraction法)、水分(≤0.5%, Karl Fischer法)、粘结剂(PVA/PEG/Acrylic, 有效期6~12个月)Lot与有效期。记录每粉体Lot的密度(Tap Density/True Density)测量值。 |
| 3 | 配料·研磨·造粒 | 以Batch管理配比(陶瓷粉体:粘结剂:溶剂=100:3~15:20~50 wt%)、研磨时间(Ball Mill/Attritor Mill, 2~24h)、slurry粘度(100~5,000 cP, Brookfield Viscometer)、造粒条件(Spray Dryer, 入口温度200~350℃, 出口温度80~120℃, 颗粒尺寸50~500μm)。 |
| 4 | 成形·Press·Green Body | 追踪Press条件(Uniaxial Press 50~300 MPa/CIP 100~400 MPa/等静压)、模具(Mold ID, 磨损率, 更换周期5,000~50,000次压制)、Green Body ID与裂纹/崩边状态(WLI 10x检查)。测量并记录Green Density(理论密度50~65%)。 |
| 5 | 脱脂·烧结·Firing | 管理窑炉(Batch Kiln/Pusher Kiln/Roller Hearth Kiln, 最高温度1,300~1,750℃)、烧结曲线(升温速度50~300℃/h, 保温时间1~10h, 冷却速度50~200℃/h)、气氛(Air/N₂/Ar/H₂)和装载方式、收缩率(15~25%)。检查烧结密度(理论密度95~99.9%)。 |
| 6 | HIP·热处理·致密化 | HIP(1,350~1,650℃, 100~200MPa Ar, 保温1~4h)、热处理(去应力800~1,200℃, 1~2h)、密度(Archimedes法, KS L 4008)和显微组织结果(SEM ×1,000~5,000, 晶粒度ASTM E112)连接。管理HIP炉产品表面接触面(Powder Packing有无)。 |
| 7 | 磨削·Lapping·加工 | 金刚石磨削(砂轮D46~D151, RPM 2,000~6,000, 进给0.005~0.1 mm/pass)、Lapping(Al₂O₃/SiC Slurry, 粒度3~15μm)、崩边(≤0.1mm标准)、表面粗糙度(Ra 0.02~0.4μm)管理。加工后伴随超声波清洗(40kHz, 5~10min)。 |
| 8 | 尺寸·密度·翘曲 Gate | 以尺寸(千分尺/影像测量系统, ±0.001mm分辨率)、密度(Archimedes, ±0.01 g/cm³)、翘曲(平面度量规/Talysurf, ≤0.05mm)、裂纹Dye Penetrant检查、绝缘/导热特性(绝缘电阻表/Laser Flash法)进行Gate判断。NCR发生时决定Rework/Downgrade。 |
| 9 | 清洗·检验·包装 | 管理洁净度(颗粒检查: LPC/Filter Pad法 0.5~10μm, Class 100~1,000级)、颗粒、包装材料(ESD Bag/泡沫/隔板)Lot与搬运损伤(崩边/破损)。使用Moisture Barrier Bag(MBB)时确认Dry Pack条件。 |
| 10 | CoA·出货 | 连接CoA(密度、尺寸、绝缘特性、无损检测结果)、检验报告(图表组)、出货Lot与客户批准状态(首件/样品批)。记录并保存包装状态照片证据。 |

### 4.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: BOP/Formula 버전관리시스템 Diff Tool 검증. 주기: Every New Product/Run. 이상 시 Recipe Version Lock + 변경 이력 기록. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: 분말 Lot→Mix Batch→Green Body→Sinter Lot→Serial→Shipment Lot. 방법: ERP Batch Genealogy 화면. 주기: Every Batch. 이상 시 Batch Reconciliation(Split/Merge 이력 일치 확인). | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: Kiln Temperature Logger(열전대, ±0.5℃), Press Force Sensor, Spray Dryer 온도/압력. 주기: Every Batch(1~10분 Logging). 이상 시 Batch Isolation→Furnace/Press 재교정→재처리. | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: Vision Measuring System 정밀도 ±0.001mm, Archimedes Density Tester, SEM 이미지. 주기: Every Sinter Lot(밀도+치수) + 주기적(미세구조, 절연특성). 이상 시 NCR→소결 Profile 조정→재소결 또는 Scrap. | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: HIP 외주 Certificate(온도/압력 기록지) 검토. 주기: Every Outsourcing HIP Lot. 이상 시 외주처 품질 프로세스 감사 → 대체 외주처 검토. | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: CoA 수치와 Gate 통과값(밀도/치수/절연특성) 일치 여부. 주기: Every Shipment Lot. 이상 시 CoA 재발행 + 포장 해체 재검사. | [10] | process_step | 출하·문서·규제 |

### 4.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: BOP/Formula版本管理Diff Tool校验。周期: Every New Product/Run。异常时: Recipe Version Lock+变更履历记录。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: 粉体Lot→Mix Batch→Green Body→Sinter Lot→Serial→Shipment Lot。方法: ERP Batch Genealogy画面。周期: Every Batch。异常时: Batch Reconciliation(Split/Merge履历一致性确认)。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 窑炉温度记录仪(热电偶, ±0.5℃)、Press力传感器、喷雾干燥器温度/压力。周期: Every Batch(1~10分钟记录)。异常时: Batch Isolation→炉/压机重新校准→重新处理。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: 影像测量系统精度±0.001mm、Archimedes密度计、SEM图像。周期: Every Sinter Lot(密度+尺寸)+定期(显微组织、绝缘特性)。异常时: NCR→烧结曲线调整→重烧或Scrap。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: HIP外协Certificate(温度/压力记录纸)审核。周期: Every Outsourcing HIP Lot。异常时: 外协厂质量过程审核→替代外协厂评估。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: CoA数值与Gate通过值(密度/尺寸/绝缘特性)一致性确认。周期: Every Shipment Lot。异常时: CoA重发+拆包重新检验。 | [10] | process_step | 出货·文件·法规 |

### 4.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, material_spec, powder_lot, binder_lot |
| 2 | Material | process |  |  | powder_lot, binder_lot, mix_batch_id, press_lot |
| 3 | Prep | process |  |  | mix_batch_id, press_lot, green_body_id, kiln_id |
| 4 | Primary Process | process |  |  | green_body_id, kiln_id, firing_profile_id, sinter_lot |
| 5 | Precision Process | process |  |  | firing_profile_id, sinter_lot, grinding_machine_id, inspection_report_id |
| 6 | Thermal/Special | process |  |  | grinding_machine_id, inspection_report_id, density_result, warpage_result |
| 7 | Surface/Clean | process |  |  | density_result, warpage_result, surface_roughness, coa_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | surface_roughness, coa_id, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | warpage_result, surface_roughness, coa_id, shipment_lot |
| 10 | Release | process |  |  | warpage_result, surface_roughness, coa_id, shipment_lot |

### 4.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, material_spec, powder_lot, binder_lot |
| 2 | Material | process |  |  | powder_lot, binder_lot, mix_batch_id, press_lot |
| 3 | Prep | process |  |  | mix_batch_id, press_lot, green_body_id, kiln_id |
| 4 | Primary Process | process |  |  | green_body_id, kiln_id, firing_profile_id, sinter_lot |
| 5 | Precision Process | process |  |  | firing_profile_id, sinter_lot, grinding_machine_id, inspection_report_id |
| 6 | Thermal/Special | process |  |  | grinding_machine_id, inspection_report_id, density_result, warpage_result |
| 7 | Surface/Clean | process |  |  | density_result, warpage_result, surface_roughness, coa_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | surface_roughness, coa_id, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | warpage_result, surface_roughness, coa_id, shipment_lot |
| 10 | Release | process |  |  | warpage_result, surface_roughness, coa_id, shipment_lot |

### 4.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 4.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 4.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - material_spec
  - powder_lot
  - binder_lot
  - mix_batch_id
  - press_lot
  - green_body_id
  - kiln_id
  - firing_profile_id
  - sinter_lot
  - grinding_machine_id
  - inspection_report_id
  - density_result
  - warpage_result
  - surface_roughness
  - coa_id
  - shipment_lot
```

---

## 5. I05 `optical_material_precision_optics` — 광학 소재·정밀 광학부품 / 光学材料与精密光学部件

```yaml
subindustry_code: I05
legacy_slug: "optical_material_precision_optics"
label_ko: "광학 소재·정밀 광학부품"
label_zh: "光学材料与精密光学部件"
label_en: ""
label_ja: ""
routing: "RT_JOBSHOP_CLEAN"
preset_id: "precision_jobshop_v1"
expression_tier: "P2"
```

> ko: 광학유리·결정소재·렌즈·프리즘·필터·코팅 광학부품의 청정 정밀가공 흐름.  
> zh: 光学玻璃、晶体材料、镜片、棱镜、滤光片、镀膜光学部件的洁净精密加工流程。

### 5.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 광학사양·도면 기준선 | 곡률(Sphere/Asphere/Freeform), Wavefront(λ/10~λ/4 @632.8nm), Transmission(>99.5%), Scratch-Dig(20-10, 40-20, 60-40), Coating Spec(AR/HR/BBAR/Partial/Filter, MIL-C-675, MIL-M-13508), 고객 승인조건(ISO 10110 표기법)을 확정한다. |
| 2 | Blank·Crystal 입고 | Blank/Crystal lot(OHARA/SCHOTT/AGC/Corning 등, Refractive Index ND, Abbe Number), 방향성(Crystal Axis X/Y/Z), 내부결함(Striae: Shadowgraph/Bubble & Inclusion: ISO 10110-3), 응력(Photoelectric Method, 5~10nm/cm Polarimeter), 보관상태를 확인한다. Blank 직경 10~300mm, 두께 3~50mm. |
| 3 | 절단·Rough Grinding | 절단 조건(Inner Diameter Saw/Wire Saw, RPM 500~3,000, Feed 0.1~1mm/min), Rough Grinding Removal(0.1~1.0mm, Diamond Wheel D151~D213, Coolant Water-based 10~20℃), Crack/Chip(Edge ≤0.1mm)을 관리한다. Center Thickness 가공여유 0.3~0.8mm. |
| 4 | Fine Grinding·Centering | Fine Grinding(Diamond Wheel D46~D76, RPM 1,500~3,000, Removal 0.05~0.3mm), Centering(곡률중심 정렬, Decenter ≤0.01mm, Prism Wedge ≤0.01mm), Thickness(±0.01mm), 설비 이력(Satisloh/Zeiss/Diafer CNC)을 연결한다. |
| 5 | Polishing·Figuring | Polishing Slurry(CeO₂/ZrO₂ Colloidal, 입자 0.5~3μm), Pad(Polyurethane/Pitch/Asphalt, Shore Hardness 60~90), Pressure(0.05~0.3kg/cm²), Removal(0.01~0.1mm/step), Wavefront Correction(Ion Beam Figuring/MRF Magnetorheological Finishing, Convergence Rate 80~95%)을 관리한다. 표면거칠기 Ra ≤0.5nm(λ/100). |
| 6 | 세정·Clean Tray 관리 | 세정 Recipe(UltraSonic Alkaline→DI Rinse→IPA Vapor Dry, 초순수 18MΩ·cm), Clean Tray ID(PTFE/Polypropylene, 입자발생 Zero), 입자/오염(LPC 0.3~1.0μm, Film Residue Contact Angle 측정 ≥70°)을 Class 100/1000 청정환경에서 관리한다. 세정 후 보존시간(Lifetime ≤4h 코팅 전까지). |
| 7 | Optical Coating | Coating Recipe(Ion-Assisted/Plasma Sputter/EB-Gun), Chamber(Bühler/Leybold/Satisloh, Base Pressure 10^-6~10^-7 Torr), 두께(Optical Monitoring λ/4~20층, Precision ±0.5%), Spectrum(UV-VIS-NIR Spectrophotometer, T/R±0.3%), Adhesion(MIL-C-675, Tape Test/Cheese Cloth Abrasion 20strokes)을 serial에 연결한다. |
| 8 | 광학계측 Gate | Interferometer(Zygo/4D, Fizeau/Twyman-Green λ=632.8nm, PV/RMS), Transmission(UV-VIS-NIR Spectrophotometer, 200~2,000nm), Scatter(Total Integrated Scatter TIS 0.1~1%), Scratch-Dig(MIL-PRF-13830, Dark Field 50x 현미경) 결과로 Gate 판단한다. 공정 전단계(3~7)의 누적 품질을 평가한다. |
| 9 | 조립·Bonding·Alignment | Bonding Material(Norland UV Adhesive/Epoxy, Lot, 유효기간, Refractive Index Matching), Alignment(Centering/Parcentricity ±0.005mm, Lens Spacer metal/plastic), Curing(UV Curing 365nm, 10~60s/Heat Curing 60~120℃, 1~24h) 조건을 추적한다. 조립 후 Wavefront Degradation ≤λ/20. |
| 10 | 최종검사·청정포장 | 최종 Optical Report(Pass/Fail 판정 차트: Wavefront Map, MTF, Spot Diagram), 포장상태(Kimwipes/PE Bag/Desiccant/ESD Foam, Seal Check), Clean Bag ID, 출하 lot과 Serial을 연결한다. MIL-STD-810 Humidity/Temperature 충격조건 포장검증. |

### 5.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 光学规格与图纸基准 | 确认曲率(Sphere/Asphere/Freeform)、Wavefront(λ/10~λ/4 @632.8nm)、透过率(>99.5%)、Scratch-Dig(20-10, 40-20, 60-40)、镀膜规格(AR/HR/BBAR/Partial/Filter, MIL-C-675, MIL-M-13508)和客户批准条件(ISO 10110标注法)。 |
| 2 | Blank·Crystal 入库 | 确认Blank/Crystal Lot(OHARA/SCHOTT/AGC/Corning等, 折射率ND, Abbe数)、取向(Crystal Axis X/Y/Z)、内部缺陷(条纹: Shadowgraph/气泡与夹杂: ISO 10110-3)、应力(光测法, 5~10nm/cm Polarimeter)和保存状态。Blank直径10~300mm, 厚度3~50mm。 |
| 3 | 切割·粗磨 | 管理切割条件(内圆切割/线切割, RPM 500~3,000, 进给0.1~1mm/min)、粗磨去除量(0.1~1.0mm, Diamond砂轮D151~D213, 冷却液水系10~20℃)、裂纹/崩边(Edge ≤0.1mm)。Center Thickness加工余量0.3~0.8mm。 |
| 4 | 精磨·定心 | 精磨(Diamond砂轮D46~D76, RPM 1,500~3,000, 去除量0.05~0.3mm)、定心(曲率中心对准, Decenter ≤0.01mm, Prism Wedge ≤0.01mm)、厚度(±0.01mm)、设备履历(Satisloh/Zeiss/Diafer CNC)连接。 |
| 5 | 抛光·面形修正 | 抛光Slurry(CeO₂/ZrO₂ Colloidal, 颗粒0.5~3μm)、抛光垫(Polyurethane/Pitch/Asphalt, Shore Hardness 60~90)、压力(0.05~0.3kg/cm²)、去除量(0.01~0.1mm/step)、Wavefront修正(Ion Beam Figuring/MRF磁流变, Convergence Rate 80~95%)管理。表面粗糙度Ra≤0.5nm(λ/100)。 |
| 6 | 清洗与 Clean Tray 管理 | 清洗配方(超声波碱性→DI Rinse→IPA Vapor Dry, 超纯水18MΩ·cm)、Clean Tray ID(PTFE/Polypropylene, 零颗粒产生)、颗粒/污染(LPC 0.3~1.0μm, 膜残留Contact Angle测量≥70°)在Class 100/1000洁净环境中管理。清洗后保存时间(Lifetime ≤4h至镀膜前)。 |
| 7 | 光学镀膜 | 镀膜配方(Ion-Assisted/Plasma Sputter/EB-Gun)、腔体(Bühler/Leybold/Satisloh, Base Pressure 10^-6~10^-7 Torr)、膜厚(Optical Monitoring λ/4~20层, 精度±0.5%)、光谱(UV-VIS-NIR Spectrophotometer, T/R±0.3%)、附着力(MIL-C-675, 胶带测试/Cheese Cloth Abrasion 20次)连接到序列号。 |
| 8 | 光学计量 Gate | 以干涉仪(Zygo/4D, Fizeau/Twyman-Green λ=632.8nm, PV/RMS)、透过率(UV-VIS-NIR Spectrophotometer, 200~2,000nm)、散射(Total Integrated Scatter TIS 0.1~1%)、Scratch-Dig(MIL-PRF-13830, Dark Field 50x显微镜)结果进行Gate判断。评估前工序(3~7)的累积质量。 |
| 9 | 装配·Bonding·Alignment | 追踪胶合材料(Norland UV胶/环氧树脂, Lot, 有效期, 折射率匹配)、Alignment(定心/偏心±0.005mm, Lens Spacer金属/塑料)、固化(UV固化365nm, 10~60s/热固化60~120℃, 1~24h)条件。装配后Wavefront Degradation≤λ/20。 |
| 10 | 最终检验与洁净包装 | 连接最终光学报告(Pass/Fail判定图表: Wavefront Map, MTF, Spot Diagram)、包装状态(Kimwipes/PE袋/干燥剂/ESD泡沫, Seal Check)、洁净袋ID、出货Lot与Serial。按MIL-STD-810湿度/温度/冲击条件进行包装验证。 |

### 5.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: PLM Optical Spec Table(곡률/코팅/Wavefront) 버전 비교. 주기: Every New Project/ECO. 이상 시 광학 설계 변경 → Coating Recipe 재계산. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: Blank Lot→Polishing Lot→Coating Batch→Serial→Assembly→출하. 방법: MES/ERP Serial Tracking. 주기: Every Lot. 이상 시 Serial 재매핑(Merge/Split 이력 보정). | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: Polishing Machine Position Sensor(RPM, Pressure, Slurry Flow 0.1~1.0 L/min), Coating Chamber Monitoring(QCM/OMS). 주기: Every Cycle(Real-time) + Every Batch(Recipe 확인). 이상 시 Machine Stop → Recipe 복구 → 해당 Lot 재처리. | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: Interferometer(λ/10~λ/4, Repeatability ±λ/200), Spectrophotometer(±0.1%T). 주기: Every Serial(100% 검사, 고객 요구 Lambda/20 이상). 이상 시 전단계 원인분석(Root Cause) → Rework(Polishing/Coating 재작업) 또는 Scrap. | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: Coating Service Certificate(Spectral Curve, MIL Spec 충족 여부 확인). 주기: Every Coating Batch. 이상 시 Coating Recipe 조정 → 재증착 또는 Design 검증 회의. | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: Optical Test Report Key Values를 ERP Shipment Spec과 자동 비교. 주기: Real-time(Every Serial). 이상 시 CoA 재작성 → 포장 재검사 → 출하보류. | [10] | process_step | 출하·문서·규제 |

### 5.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: PLM光学规格表(曲率/镀膜/Wavefront)版本对比。周期: Every New Project/ECO。异常时: 光学设计变更→镀膜Recipe重新计算。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: Blank Lot→Polishing Lot→Coating Batch→Serial→Assembly→出货。方法: MES/ERP Serial Tracking。周期: Every Lot。异常时: Serial重新映射(Merge/Split履历修正)。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 抛光机位置传感器(RPM, 压力, Slurry流量0.1~1.0 L/min), 镀膜腔体监控(QCM/OMS)。周期: Every Cycle(Real-time)+Every Batch(Recipe确认)。异常时: Machine Stop→Recipe恢复→对应Lot重新处理。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: 干涉仪(λ/10~λ/4, Repeatability ±λ/200), 分光光度计(±0.1%T)。周期: Every Serial(100%检查, 客户要求Lambda/20以上)。异常时: 前工序根本原因分析(Root Cause)→Rework(重新抛光/镀膜)或Scrap。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: 镀膜服务Certificate(光谱曲线, 确认满足MIL Spec)。周期: Every Coating Batch。异常时: Coating Recipe调整→重新沉积或Design验证会议。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: 光学测试报告Key Values与ERP出货Spec自动比较。周期: Real-time(Every Serial)。异常时: CoA重写→包装重新检验→出货暂缓。 | [10] | process_step | 出货·文件·法规 |

### 5.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, optical_spec, blank_lot, crystal_lot |
| 2 | Material | process |  |  | blank_lot, crystal_lot, work_order_id, serial_no |
| 3 | Prep | process |  |  | work_order_id, serial_no, grinding_machine_id, polishing_lot |
| 4 | Primary Process | process |  |  | grinding_machine_id, polishing_lot, slurry_lot, coating_recipe_id |
| 5 | Precision Process | process |  |  | slurry_lot, coating_recipe_id, chamber_id, metrology_report_id |
| 6 | Thermal/Special | process |  |  | chamber_id, metrology_report_id, transmission_result, wavefront_result |
| 7 | Surface/Clean | process |  |  | transmission_result, wavefront_result, scratch_dig_result, clean_tray_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | scratch_dig_result, clean_tray_id, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | wavefront_result, scratch_dig_result, clean_tray_id, shipment_lot |
| 10 | Release | process |  |  | wavefront_result, scratch_dig_result, clean_tray_id, shipment_lot |

### 5.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, optical_spec, blank_lot, crystal_lot |
| 2 | Material | process |  |  | blank_lot, crystal_lot, work_order_id, serial_no |
| 3 | Prep | process |  |  | work_order_id, serial_no, grinding_machine_id, polishing_lot |
| 4 | Primary Process | process |  |  | grinding_machine_id, polishing_lot, slurry_lot, coating_recipe_id |
| 5 | Precision Process | process |  |  | slurry_lot, coating_recipe_id, chamber_id, metrology_report_id |
| 6 | Thermal/Special | process |  |  | chamber_id, metrology_report_id, transmission_result, wavefront_result |
| 7 | Surface/Clean | process |  |  | transmission_result, wavefront_result, scratch_dig_result, clean_tray_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | scratch_dig_result, clean_tray_id, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | wavefront_result, scratch_dig_result, clean_tray_id, shipment_lot |
| 10 | Release | process |  |  | wavefront_result, scratch_dig_result, clean_tray_id, shipment_lot |

### 5.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 5.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 5.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - optical_spec
  - blank_lot
  - crystal_lot
  - work_order_id
  - serial_no
  - grinding_machine_id
  - polishing_lot
  - slurry_lot
  - coating_recipe_id
  - chamber_id
  - metrology_report_id
  - transmission_result
  - wavefront_result
  - scratch_dig_result
  - clean_tray_id
  - shipment_lot
```

---

## 6. I06 `semiconductor_electronic_materials` — 반도체·전자용 소재 / 半导体与电子材料

```yaml
subindustry_code: I06
legacy_slug: "semiconductor_electronic_materials"
label_ko: "반도체·전자용 소재"
label_zh: "半导体与电子材料"
label_en: ""
label_ja: ""
routing: "RT_BATCH_QUALIFIED"
preset_id: "batch_process_v1"
expression_tier: "P2"
```

> ko: 웨이퍼·포토레지스트·CMP·전자화학·세라믹/금속 패키지 소재의 초고순도 Batch/Qual 흐름.  
> zh: 晶圆、光刻胶、CMP、电子化学品、陶瓷/金属封装材料的超高纯 Batch/Qual 流程。

### 6.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객 Qual·소재 Grade 기준선 | 고객 Fab Qual(ASML/TSMC/Samsung Fab 승인), Impurity Limit(Fe, Ni, Cu, Na 등 metal 0.01~10ppb, Particle ≥0.2μm <100 ea/mL), Spec Sheet(Reagent Grade/EL Grade/Ultra-pure Grade), Shelf Life(3~36개월)와 변경통제 기준(SEMI MF57, MOC/PCN 절차)을 확정한다. |
| 2 | 고순도 원료·용기 입고 | 고순도 원료 lot(순도 99.999~99.9999%, ICP-MS 검증), Container Cleanliness(Inner Rinse + Particle Count, Class 10/100 Clean), 보관조건(N₂ Blanket, 온도 5~35℃, UV 차단), Supplier Qual 승인 상태를 확인한다. Silane/Specialty Gas는 Cylinder Certification 검토. |
| 3 | 정제·합성·배합 | Recipe(Mixing Ratio ±0.01%, Heating Profile 50~300℃, Pressure Control Atmospheric~100bar), Equipment(Stainless Steel/PTFE Reactor, 교반속도 50~500RPM), Cleanroom(Class 100~1,000, Temperature 20±2℃, Humidity 40±10%RH), Batch Split/Merge를 관리한다. Pre-filter(5~10μm)→Fine Filter(0.1~0.5μm) 단계별 운영. |
| 4 | 여과·Particle Control | Filter Lot(PTFE/PES Membrane 0.02~0.2μm, Cartridge Type), Differential Pressure(Initial 0.1~0.3 bar, Change-out ΔP≥2.0 bar), Particle Trend(LPC Inline Sensor, 0.1~1.0μm, Sampling Rate 1mL/min), Filter 교체 이력(Serial No, 교체일, 가동시간)을 추적한다. 최종 여과 후 Particle Spec 충족 확인. |
| 5 | Aging·Stabilization | Aging Time(2~72h), Temperature(20~60℃, ±0.5℃), Viscosity(0.5~100cP 변화, Brookfield/Viscometer, ±1%), 반응 안정성(pH 2~11, Conductivity, FT-IR Spectrum 변화 ≤1%)을 관리한다. Aging 완료 전/후 샘플링하여 Pre-Release QC 실시. |
| 6 | Filling·Containerization | Filling Line(Class 100 Clean Booth, Iso-static/Weight Filling, 정밀도 ±0.1~0.5%), Container ID(PFA/PE/Glass Bottle, 100mL~200L, Drum/IBCTote), Seal Integrity(He Leak Test ≤1×10⁻⁶ mbar·L/s), Label(Product ID, Lot No, Expiry Date, Hazmat 표시)와 Batch를 연결한다. Filling량 자동 검증(Weigh Scale). |
| 7 | 초고순도 Lab Gate | Purity(ICP-MS, 0.01~100ppb), Metal Contamination(TXRF/ICP-MS, Fe/Ni/Cr/Cu/Na 각각 1~50ppb max), Particle(LPC/Filter Pad Method, ≥0.2μm, ≥0.5μm, 기준 per SEMI MF Standard), Viscosity/Water Content(Karl Fischer, ≤10~1,000ppm) 등 Lab 결과로 Release를 판단한다. |
| 8 | 고객 샘플·Qual Lot | 고객 샘플 전달(Shipping Condition: Gel Pack/Dry Ice, 추적가능), Qual Lot(고객 Fab 테스트, 1~3개월 Feedback Cycle), Feedback(Pass/Fail/Exception), 승인상태(Qual Status Code)를 Batch와 연결한다. Qual Lot 결과는 Batch Release 조건으로 반영. |
| 9 | 보관·FEFO·Hold 관리 | 유효기간(3~36개월, FEFO First Expiry First Out 출고), 보관온도(5~35℃, Refrigerated 2~8℃), 습도(30~70%RH, Monitoring Data Logger), Quarantine/Hold/Release 상태(ERP Status Code)를 관리한다. Shelf Life Extension 시 재시험 Protocol 적용. |
| 10 | CoA·출하·변경관리 | CoA(Batch별 실제 분석값, SEMI Standard Format), Shipment Lot(Part/Serial/Lot/Batch 매핑), MOC/PCN(변경통지서, 고객 승인 30~90일 선행), 고객 승인 변경 이력을 연결한다. COA/Analytical Report + MSDS + Origin Certificate 묶음 발행. |

### 6.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户 Qual 与材料 Grade 基准 | 确认客户Fab Qual(ASML/TSMC/Samsung Fab批准)、杂质限值(Fe, Ni, Cu, Na等金属0.01~10ppb, 颗粒≥0.2μm <100 ea/mL)、Spec Sheet(Reagent Grade/EL Grade/Ultra-pure Grade)、保存期(3~36个月)与变更控制标准(SEMI MF57, MOC/PCN流程)。 |
| 2 | 高纯原料与容器入库 | 确认高纯原料Lot(纯度99.999~99.9999%, ICP-MS验证)、容器洁净度(内部Rinse+颗粒计数, Class 10/100 Clean)、保存条件(N₂ Blanket, 温度5~35℃, UV屏蔽)、Supplier Qual批准状态。硅烷/特种气体审查Cylinder Certification。 |
| 3 | 精制·合成·配料 | 管理Recipe(混合比±0.01%, 加热曲线50~300℃, 压力控制常压~100bar)、设备(不锈钢/PTFE反应器, 搅拌速度50~500RPM)、洁净室(Class 100~1,000, 温度20±2℃, 湿度40±10%RH)、Batch Split/Merge。按Pre-filter(5~10μm)→Fine Filter(0.1~0.5μm)分级运行。 |
| 4 | 过滤与 Particle Control | 追踪Filter Lot(PTFE/PES膜0.02~0.2μm, 滤芯型)、差压(Initial 0.1~0.3 bar, 更换ΔP≥2.0 bar)、颗粒趋势(LPC在线传感器, 0.1~1.0μm, 采样率1mL/min)、滤芯更换履历(Serial No, 更换日期, 运行时间)。确认最终过滤后满足Particle Spec。 |
| 5 | Aging·稳定化 | 管理Aging时间(2~72h)、温度(20~60℃, ±0.5℃)、粘度(0.5~100cP变化, Brookfield/Viscometer, ±1%)、反应稳定性(pH 2~11, 电导率, FT-IR光谱变化≤1%)。Aging完成前后取样实施Pre-Release QC。 |
| 6 | 灌装与容器化 | 灌装线(Class 100洁净间, 等静压/重量灌装, 精度±0.1~0.5%)、Container ID(PFA/PE/玻璃瓶, 100mL~200L, Drum/IBC/Tote)、密封完整性(He Leak Test ≤1×10⁻⁶ mbar·L/s)、标签(Product ID, Lot No, 有效期, Hazmat标识)与Batch连接。灌装量自动验证(称重天平)。 |
| 7 | 超高纯 Lab Gate | 以纯度(ICP-MS, 0.01~100ppb)、金属污染(TXRF/ICP-MS, Fe/Ni/Cr/Cu/Na各1~50ppb max)、颗粒(LPC/滤膜法, ≥0.2μm, ≥0.5μm, 按SEMI MF标准)、粘度/水分(Karl Fischer, ≤10~1,000ppm)等Lab结果判断Release。 |
| 8 | 客户样品与 Qual Lot | 客户样品交付(Shipping Condition: Gel Pack/Dry Ice, 可追溯)、Qual Lot(客户Fab测试, 1~3个月反馈周期)、Feedback(Pass/Fail/Exception)、批准状态(Qual Status Code)连接到Batch。Qual Lot结果作为Batch Release条件反映。 |
| 9 | 保存·FEFO·Hold 管理 | 管理有效期(3~36个月, FEFO First Expiry First Out出库)、保存温度(5~35℃, 冷藏2~8℃)、湿度(30~70%RH, Data Logger监控)、Quarantine/Hold/Release状态(ERP状态代码)。Shelf Life延长时应用复测Protocol。 |
| 10 | CoA·出货·变更管理 | 连接CoA(每Batch实际分析值, SEMI Standard格式)、Shipment Lot(Part/Serial/Lot/Batch映射)、MOC/PCN(变更通知, 客户审批30~90天提前)、客户批准变更履历。COA/分析报告+MSDS+原产地证明捆绑签发。 |

### 6.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: ERP Spec Master(Impurity Limit, Particle Spec) 버전과 Batch Recipe 버전 비교. 주기: Every New Grade/Customer Qual. 이상 시 MOC 발행 → 고객 승인 회신 대기 후 적용. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: Raw Material Lot→Purification Batch→Blend Batch→Fill Batch→Container Serial→Shipment Lot. 방법: ERP Batch Genealogy (Full Upward/Downward Traceability). 주기: Every Batch. 이상시 Batch Reconciliation(전/후물량 Balance 검증). | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: Reactor Temperature/ Pressure/Agitation RPM Data Logger, Filter ΔP Monitor, Particle Counter(Online). 주기: Real-time(Continuous Monitoring) + Every Batch(Recipe Step 확인). 이상 시 Batch Quarantine→설비 Calibration→재처리(Mixing/여과 재실행). | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: ICP-MS(Agilent/PerkinElmer, PPT~PPB 검출), LPC(Rion/Lighthouse 0.1~1.0μm), Karl Fischer(Metrohm). 주기: Every Batch(투입 전/중간/완료 3회 이상 Sampling). 이상 시 Batch Reject→Recipe 조정→재처리 또는 Scrap. Lab Data Linked to LIMS. | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: 외주 Contract Lab Certificate(ISO 17025 인증) 검토. 주기: Every Outsourced Test. 이상 시 Lab 재시험 요청 → 다른 인증 Lab 교차 검증. | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: CoA 수치와 LIMS/Lab Gate 결과 자동 비교(Function GRC: Golden Rule Check). 주기: Real-time(Every Container Label Scan). 이상 시 Shipment Hold → Label 재발행 + CoA 수정. | [10] | process_step | 출하·문서·규제 |

### 6.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: ERP Spec Master(杂质限值, 颗粒Spec)版本与Batch Recipe版本对比。周期: Every New Grade/Customer Qual。异常时: 签发MOC→等待客户批准回复后应用。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: Raw Material Lot→Purification Batch→Blend Batch→Fill Batch→Container Serial→Shipment Lot。方法: ERP Batch Genealogy(完整向上/向下追溯)。周期: Every Batch。异常时: Batch Reconciliation(前后物量Balance验证)。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 反应器温度/压力/搅拌RPM数据记录器、Filter ΔP监控器、颗粒计数器(Online)。周期: Real-time(连续监控)+Every Batch(Recipe步骤确认)。异常时: Batch Quarantine→设备校准→重新处理(重新混合/过滤)。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: ICP-MS(Agilent/PerkinElmer, PPT~PPB检测)、LPC(Rion/Lighthouse 0.1~1.0μm)、Karl Fischer(Metrohm)。周期: Every Batch(投料前/中/完成3次以上采样)。异常时: Batch Reject→Recipe调整→重新处理或Scrap。实验室数据连接LIMS。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: 外协合同Lab Certificate(ISO 17025认证)审核。周期: Every Outsourced Test。异常时: 请求重新测试→其他认证Lab交叉验证。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: CoA数值与LIMS/Lab Gate结果自动比较(GRC功能: Golden Rule Check)。周期: Real-time(每容器标签扫描)。异常时: Shipment Hold→标签重发+CoA修改。 | [10] | process_step | 出货·文件·法规 |

### 6.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, material_grade, raw_material_lot, container_id |
| 2 | Material | process |  |  | raw_material_lot, container_id, batch_id, recipe_id |
| 3 | Prep | batch |  |  | batch_id, recipe_id, equipment_id, cleanroom_id |
| 4 | Primary Process | batch |  |  | equipment_id, cleanroom_id, purity_result, particle_result |
| 5 | Precision Process | process |  |  | purity_result, particle_result, metal_contamination_result, viscosity_result |
| 6 | Thermal/Special | process |  |  | metal_contamination_result, viscosity_result, coa_id, qual_lot_id |
| 7 | Surface/Clean | process |  |  | coa_id, qual_lot_id, sample_id, hold_status |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | sample_id, hold_status, shipment_lot, expiry_date |
| 9 | Pack | process |  |  | shipment_lot, expiry_date |
| 10 | Release | process |  |  | sample_id, hold_status, shipment_lot, expiry_date |

### 6.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, material_grade, raw_material_lot, container_id |
| 2 | Material | process |  |  | raw_material_lot, container_id, batch_id, recipe_id |
| 3 | Prep | batch |  |  | batch_id, recipe_id, equipment_id, cleanroom_id |
| 4 | Primary Process | batch |  |  | equipment_id, cleanroom_id, purity_result, particle_result |
| 5 | Precision Process | process |  |  | purity_result, particle_result, metal_contamination_result, viscosity_result |
| 6 | Thermal/Special | process |  |  | metal_contamination_result, viscosity_result, coa_id, qual_lot_id |
| 7 | Surface/Clean | process |  |  | coa_id, qual_lot_id, sample_id, hold_status |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | sample_id, hold_status, shipment_lot, expiry_date |
| 9 | Pack | process |  |  | shipment_lot, expiry_date |
| 10 | Release | process |  |  | sample_id, hold_status, shipment_lot, expiry_date |

### 6.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 6.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 6.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - material_grade
  - raw_material_lot
  - container_id
  - batch_id
  - recipe_id
  - equipment_id
  - cleanroom_id
  - purity_result
  - particle_result
  - metal_contamination_result
  - viscosity_result
  - coa_id
  - qual_lot_id
  - sample_id
  - hold_status
  - shipment_lot
  - expiry_date
```

---

## 7. I07 `precision_wire_spring_tube` — 정밀 와이어·스프링·튜브 / 精密线材·弹簧·管材

```yaml
subindustry_code: I07
legacy_slug: "precision_wire_spring_tube"
label_ko: "정밀 와이어·스프링·튜브"
label_zh: "精密线材·弹簧·管材"
label_en: ""
label_ja: ""
routing: "RT_JOBSHOP_LINE"
preset_id: "precision_jobshop_v1"
expression_tier: "P2"
```

> ko: 정밀 선재·케이블·스프링·성형 와이어·극세/정밀 튜브의 Coil/Reel genealogy 흐름.  
> zh: 精密线材、电缆、弹簧、成形线材、微细/精密管材的 Coil/Reel 谱系流程。

### 7.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 도면·사양·공차 기준선 | 직경(φ0.02~10mm, 공차 ±0.005~0.1mm), 벽두께(튜브, 공차 ±0.005~0.05mm), 장력(N/mm²), 탄성(Elastic Modulus/Spring Constant, ±5%), 형상(Coil Diameter/Angle/Pitch), 고객 공차와 검사기준(Spring DIN 2095/2096, ASTM A228/A227)을 확정한다. |
| 2 | 소재 Coil·Tube 입고 | Coil/Reel/Tube Bundle ID와 소재 Lot(지름 φ2~30mm, 중량 50~500kg/coil), Heat No, 인장강도/경도 MTC 값, 표면상태(Patenting/Phosphating/Annealing 여부)를 연결한다. 입고 시 Eddy Current 표면검사(Defect ≥0.05mm 판별) 수행. |
| 3 | Annealing·전처리 | Annealing Profile(Continuous Furnace/Batch Furnace, 온도 600~950℃, 속도 5~20 m/min, 분위기 Air/Exothermic Gas/N₂+H₂), 산화(Scale 두께 ≤0.01mm), 표면상태(표면탄소/인산염 피막 두께)와 전처리 이력(산세 HCl/H₂SO₄ 10~25%, 40~80℃, 5~20min)을 관리한다. |
| 4 | Drawing·Rolling·Reduction | Die ID(초경/다이아몬드 Die φ0.02~10mm, 각도 6~15°), Reduction(10~35%/pass, 총 Reduction 50~95%), Speed(1~30 m/s), Tension(50~500N, Tension Controller), 윤활(유성/수용성 윤활제, 점도 10~100cSt, Filter 5μm) 조건을 coil genealogy(Coil Split/Joint)에 연결한다. |
| 5 | Spring Coiling·Forming | Coiling Program(CNC Spring Coiler, Wafios/SIMCO, Min/Max Wire φ0.02~10mm), Pitch(CNC Control, ±0.01mm), Free Length(±0.1mm), Coil Diameter(±0.05mm), Forming Tool(Die/Groove Roller) 이력(마모, 교체주기)을 관리한다. Cam/CNC 2D/3D Former 사용. |
| 6 | 절단·Straightening·End Form | 절단 길이(정밀도 ±0.1~0.5mm, Flying Shear/Cut-off Saw), Straightness(0.3~1.0mm/m, Roller Straightener), End Forming(Butt/Grind/Chamfer/Flatten, 전용 End Former), Scrap(권취단 미사용분, 재활용 가능 여부)를 기록한다. |
| 7 | 열처리·Stress Relief | Stress Relief Profile(Conveyor/Mesh Belt Furnace, 온도 300~500℃, 속도 3~10 m/min, 유지 5~30min, 분위기 Air/N₂), 경도(HRC/HV Change ±5%), Spring Constant(set loss ≤1%) 변화 결과를 연결한다. Quenching/Tempering 조건 관리(오일 60~100℃, 수냉). |
| 8 | 표면처리·세정 | Plating(Zn/Ni/Cr 전기도금, 두께 3~20μm, ASTM B633/B689), Coating(PTFE/Epoxy/Powder Coating), Passivation(Stainless 강, HNO₃ 20~30%, 30~60min), 세정도(초음파 탈지, Contact Angle ≤20°), 외주 Certificate를 관리한다. Hydrogen Embrittlement Relief Bake(190~220℃, 4~24h). |
| 9 | 직경·장력·벽두께 Gate | Diameter(Laser Micrometer, Keyence/Heidenhain, 정밀도 ±0.1~0.5μm, Real-time 100% Scan), Wall Thickness(Ultrasonic Gauge, 0.005~1mm, ±0.1μm), Tension(Universal Testing Machine, Extensometer, 0.1~50kN), Spring Constant(Spring Tester, 0.01~1,000N/mm), 표면결함(Eddy Current/Borescope/10x Visual)으로 Gate 판단한다. |
| 10 | Reel·Bundle 포장·출하 | Reel/Bundle Label(Metal/Plastic Reel ID, Bundle Tag, Customer Label, GS1-128 바코드), 포장조건(Wooden Drum/Corrugated Box/Plastic Wrap, VCI Oil Paper, 안전포장 요건), 출하 lot과 고객주문을 연결한다. 포장 전 마지막 직경·장력·외관 검사. |

### 7.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 图纸·规格·公差基准 | 确认直径(φ0.02~10mm, 公差±0.005~0.1mm)、壁厚(管材, 公差±0.005~0.05mm)、张力(N/mm²)、弹性(弹性模量/弹簧常数, ±5%)、形状(弹簧直径/角度/节距)、客户公差与检验标准(Spring DIN 2095/2096, ASTM A228/A227)。 |
| 2 | 材料 Coil·Tube 入库 | 连接Coil/Reel/Tube Bundle ID与材料Lot(直径φ2~30mm, 重量50~500kg/coil)、Heat No、抗拉强度/硬度MTC值、表面状态(Patenting/Phosphating/Annealing与否)。入库时进行涡流表面检查(判断缺陷≥0.05mm)。 |
| 3 | Annealing 与预处理 | 管理Annealing曲线(连续炉/分批炉, 温度600~950℃, 速度5~20 m/min, 气氛Air/放热气体/N₂+H₂)、氧化(氧化皮厚度≤0.01mm)、表面状态(表面碳/磷酸盐涂层厚度)与预处理履历(酸洗HCl/H₂SO₄ 10~25%, 40~80℃, 5~20min)。 |
| 4 | 拉拔·轧制·Reduction | 将Die ID(超硬/金刚石Die φ0.02~10mm, 角度6~15°)、Reduction(10~35%/pass, 总Reduction 50~95%)、速度(1~30 m/s)、张力(50~500N, 张力控制器)、润滑(油基/水基润滑剂, 粘度10~100cSt, Filter 5μm)条件连接到Coil谱系(Coil Split/Joint)。 |
| 5 | 弹簧卷制·成形 | 管理Coiling程序(CNC Spring Coiler, Wafios/SIMCO, Min/Max Wire φ0.02~10mm)、节距(CNC控制, ±0.01mm)、自由长度(±0.1mm)、弹簧直径(±0.05mm)、成形工具(模具/沟槽滚轮)履历(磨损, 更换周期)。使用Cam/CNC 2D/3D成形机。 |
| 6 | 切割·校直·端部成形 | 记录切割长度(精度±0.1~0.5mm, Flying Shear/切管锯)、直线度(0.3~1.0mm/m, 辊式校直机)、端部成形(Butt/Grind/Chamfer/Flatten, 专用端部成形机)、Scrap(卷取端未使用部分, 可回收与否)。 |
| 7 | 热处理·Stress Relief | 连接Stress Relief曲线(网带炉, 温度300~500℃, 速度3~10 m/min, 保温5~30min, 气氛Air/N₂)、硬度(HRC/HV变化±5%)、弹簧常数(set loss ≤1%)变化结果。管理淬火/回火条件(油60~100℃, 水冷)。 |
| 8 | 表面处理·清洗 | 管理电镀(Zn/Ni/Cr电镀, 厚度3~20μm, ASTM B633/B689)、涂层(PTFE/Epoxy/Powder Coating)、钝化(不锈钢, HNO₃ 20~30%, 30~60min)、洁净度(超声波脱脂, Contact Angle ≤20°)、外协证书。氢脆消除Bake(190~220℃, 4~24h)。 |
| 9 | 直径·张力·壁厚 Gate | 以直径(激光千分尺, Keyence/Heidenhain, 精度±0.1~0.5μm, Real-time 100%扫描)、壁厚(超声波测厚仪, 0.005~1mm, ±0.1μm)、张力(万能试验机, 引伸计, 0.1~50kN)、弹簧常数(弹簧试验机, 0.01~1,000N/mm)、表面缺陷(涡流/内窥镜/10x目视)进行Gate判断。 |
| 10 | Reel·Bundle 包装与出货 | 连接Reel/Bundle标签(金属/塑料Reel ID, Bundle Tag, 客户标签, GS1-128条码)、包装条件(木桶/瓦楞纸箱/塑料膜, VCI防锈纸, 安全包装要求)、出货Lot与客户订单。包装前进行最终直径、张力、外观检查。 |

### 7.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: Spec(직경/장력/탄성)과 Drawing Parameters 비교. 주기: Every New Product & Drawing revision. 이상 시 Drawing Mark-up → 고객 승인 후 적용. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: Coil Lot→Split Coil ID→Draw Pass→Final Coil/Reel→Shipment Lot. 방법: MES Coil Genealogy(Coil Split/Joint 이력). 주기: Every Coil Split/Joint. 이상 시 Coil Reconciliation(중량/길이 Balance 확인). | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: Drawing Speed/Tension Controller Logger, Annealing Furnace Temp Profile, Die Wear(Optical Measuring). 주기: Real-time(Every Coil Pass) + Every Die Change. 이상 시 Line Stop → Die 교체 → Coil 재작업(Redraw). | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: Laser Micrometer(Inline, ±0.1μm), UT SWG Full Body Scan, Tension Tester. 주기: Real-time(직경 100% Scan) + Every Lot(장력/탄성 Sampling AQL). 이상 시 Coil 구간 Marking → Off-Spec 구간 절단 제거 → Retest. | [9] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: Plating/Coating Certificate(두께, 경도, Neut Salt Spray Test) 검증. 주기: Every Outsourcing Lot. 이상 시 Bath 분석 → 도금 조건 재조정 → 해당 Lot 재처리. | [8] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: Reel/Bundle Label Barcode와 ERP Shipment Order 매칭. 주기: Real-time(Every Reel/Bundle). 이상 시 Label Reprint → 재스캔 확인. | [10] | process_step | 출하·문서·규제 |

### 7.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: Spec(直径/张力/弹性)与Drawing参数对比。周期: Every New Product & Drawing revision。异常时: Drawing Mark-up→客户批准后应用。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: Coil Lot→Split Coil ID→Draw Pass→Final Coil/Reel→Shipment Lot。方法: MES Coil Genealogy(Coil Split/Joint履历)。周期: Every Coil Split/Joint。异常时: Coil Reconciliation(重量/长度Balance确认)。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 拉拔速度/张力Controller记录器、Annealing炉温曲线、Die磨损(光学测量)。周期: Real-time(每Coil Pass)+每Die更换。异常时: Line Stop→Die更换→Coil重新拉拔。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: 激光千分尺(在线, ±0.1μm)、UT SWG全长扫描、张力试验机。周期: Real-time(直径100%扫描)+Every Lot(张力/弹性抽样AQL)。异常时: Coil区段Marking→Off-Spec区段切除→Retest。 | [9] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: 电镀/涂层Certificate(厚度、硬度、中性盐雾试验)验证。周期: Every Outsourcing Lot。异常时: Bath分析→电镀条件重新调整→对应Lot重新处理。 | [8] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: Reel/Bundle标签条码与ERP出货订单匹配。周期: Real-time(每Reel/Bundle)。异常时: 标签重印→重新扫描确认。 | [10] | process_step | 出货·文件·法规 |

### 7.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_lot, coil_id |
| 2 | Material | process |  |  | material_lot, coil_id, reel_id, tube_bundle_id |
| 3 | Prep | process |  |  | reel_id, tube_bundle_id, draw_die_id, machine_id |
| 4 | Primary Process | process |  |  | draw_die_id, machine_id, recipe_id, heat_treat_lot |
| 5 | Precision Process | process |  |  | recipe_id, heat_treat_lot, spring_program_rev, surface_treatment_lot |
| 6 | Thermal/Special | process |  |  | spring_program_rev, surface_treatment_lot, inspection_report_id, tension_result |
| 7 | Surface/Clean | process |  |  | inspection_report_id, tension_result, diameter_result, wall_thickness_result |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | diameter_result, wall_thickness_result, shipment_lot |
| 9 | Pack | process |  |  | tension_result, diameter_result, wall_thickness_result, shipment_lot |
| 10 | Release | process |  |  | tension_result, diameter_result, wall_thickness_result, shipment_lot |

### 7.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_lot, coil_id |
| 2 | Material | process |  |  | material_lot, coil_id, reel_id, tube_bundle_id |
| 3 | Prep | process |  |  | reel_id, tube_bundle_id, draw_die_id, machine_id |
| 4 | Primary Process | process |  |  | draw_die_id, machine_id, recipe_id, heat_treat_lot |
| 5 | Precision Process | process |  |  | recipe_id, heat_treat_lot, spring_program_rev, surface_treatment_lot |
| 6 | Thermal/Special | process |  |  | spring_program_rev, surface_treatment_lot, inspection_report_id, tension_result |
| 7 | Surface/Clean | process |  |  | inspection_report_id, tension_result, diameter_result, wall_thickness_result |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | diameter_result, wall_thickness_result, shipment_lot |
| 9 | Pack | process |  |  | tension_result, diameter_result, wall_thickness_result, shipment_lot |
| 10 | Release | process |  |  | tension_result, diameter_result, wall_thickness_result, shipment_lot |

### 7.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 7.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 7.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - drawing_rev
  - material_lot
  - coil_id
  - reel_id
  - tube_bundle_id
  - draw_die_id
  - machine_id
  - recipe_id
  - heat_treat_lot
  - spring_program_rev
  - surface_treatment_lot
  - inspection_report_id
  - tension_result
  - diameter_result
  - wall_thickness_result
  - shipment_lot
```

---

## 8. I08 `tool_cutting_wear_components` — 공구·절삭·마모 부품 / 工具·切削·耐磨部件

```yaml
subindustry_code: I08
legacy_slug: "tool_cutting_wear_components"
label_ko: "공구·절삭·마모 부품"
label_zh: "工具·切削·耐磨部件"
label_en: ""
label_ja: ""
routing: "RT_JOBSHOP"
preset_id: "precision_jobshop_v1"
expression_tier: "P2"
```

> ko: 절삭공구·인서트·초경/다이아몬드 공구·정밀 마모부품의 소재-가공-열처리-코팅-성능시험 흐름.  
> zh: 切削工具、刀片、硬质合金/金刚石工具、精密耐磨件的材料-加工-热处理-涂层-性能测试流程。

### 8.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 제품사양·용도 기준선 | 가공대상 소재(강/주철/스테인리스/초합금/비철), 절삭조건(절삭속도 50~500 m/min, 이송 0.05~0.5 mm/rev, 절삭깊이 0.5~5mm), 수명 요구(한면당 가공시간 10~60min), 형상(CNMG/SNMG/WNMG 인서트 형상, ISO 1832), 코팅 Spec(TiN/TiAlN/AlCrN/DLC/Diamond, 두께 1~15μm), 고객 승인조건을 확정한다. |
| 2 | 분말·초경·Blank 입고 | 분말 lot(WC/Co/TiC/TaC/NbC, 입도 0.5~10μm, Fisher Sub-Sieve Size), Blank ID(압분체/Pre-sinter Blank), 초경 Grade(ISO K10~K30, P10~P40, M10~M20), Binder 함량(Co 6~12wt%, Ni 0~5wt%)과 Supplier Cert(밀도, 경도, XRD 상분석)를 확인한다. |
| 3 | Press·성형·Preform | Press 조건(Mechanical Press/HIP Press 100~300 MPa, Multi-cavity Die), 금형(Mold ID, 캐비티수 2~32, 마모 0.002mm 이내), Preform ID, Green Density(이론밀도의 50~65%, ±0.1 g/cm³)를 관리한다. Press 후 Burr/모서리 결함 검사(10x Zoom Microscope). |
| 4 | 소결·HIP·열처리 | Sinter Furnace(Vacuum Sinter/HIP Sinter, 최고온도 1,350~1,550℃, 유지 30~120min, 분위기 Vacuum/Ar/H₂, Pressure 0.1~100bar), Sinter Profile(승온 5~10℃/min, 냉각 10~20℃/min), Shrinkage(17~22% linear), HIP(1,350~1,500℃, 50~150MPa Ar, 1~4h)을 연결한다. 소결밀도(이론밀도 99.5% 이상). |
| 5 | 연삭·Profile 가공 | Grinding Program(CNC Tool Grinder, Walter/ANCA/Ewag, Diamond Wheel D46~D76), Wheel(Resin/Vitreous/Metal Bond, RPM 3,000~8,000, Feed 0.001~0.05mm/pass), Coolant(Oil-based/Water-based 10~40℃, Filter <5μm), Profile Dimension(인서트 IC 직경 ±0.01mm, 두께 ±0.005mm, Relief Angle ±0.5°)을 관리한다. |
| 6 | Edge Prep·Polishing | Edge Preparation(Honing/Brush/Waterjet, Edge Radius 0.005~0.05mm, 반복정밀도 ±0.002mm), Chamfer(폭 0.05~0.3mm, 각도 20~45°), Polishing(Mechanical/Chemical/Electro, 표면거칠기 Ra ≤0.05μm), 조건을 추적한다. Edge Prep 후 질감 SEM 검사. |
| 7 | PVD/CVD/DLC Coating | Coating Recipe(PVD Arc/ Sputter, CVD HT/LT, DLC sputter), Chamber(Ionbond/Oerlikon/CemeCon, Base Pressure 10^-5~10^-6 Torr, Bias Voltage 50~150V), 두께(1~15μm, Ball Crater/Calotest, ±0.5μm), Adhesion(Rockwell HRC Indentation VDI 3198, HF1~HF4, Scratch Test Lc), 외관결함(Optical Microscope 50x)을 관리한다. |
| 8 | 경도·Edge·치수 Gate | Hardness(Rockwell A/Vickers, HRA 88~94, HV 1,300~2,200), Edge Radius/Olometer(Laser Profilometer, ±0.001mm), Profile(Vision Measuring System, Profile Projector), Runout(0.005~0.02mm TIR), Surface Defect(50x Microscope/Dye Penetrant)로 Gate 판단한다. NCR 발생 시 정밀 연삭/코팅 재수행 또는 Scrap. |
| 9 | 성능·마모 시험 | Wear Test(Cutting Test Lathe/Milling Machine, 실제 공작물 가공, 절삭력 Dynamometer), Cutting Trial(고객 제공 재료로 가공, 수명 측정: Edge Life min, Flank Wear VB max 0.3mm), Life Result(분당 가공수, 공구당 총 가공시간)와 고객 적용조건을 연결한다. 성능 Gate 5~10개 Sampling. |
| 10 | 마킹·포장·출하 | Laser Marking(Fiber Laser, Power 10~30W, ISO 1832 인서트 마킹 규격, DPM Code), Package(Insert Tray/Box/Blister Tray, Qty 10/20/50 pcs), Shipment Lot(Part No+Lot No+Qty), Certificate(CoC, 성적서, 성능시험 Data Sheet)를 연결한다. 포장 전 최종 육안검사(Coating Color/Edge Chip). |

### 8.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 产品规格与用途基准 | 确认被加工材料(钢/铸铁/不锈钢/超合金/非铁金属)、切削条件(切削速度50~500 m/min, 进给0.05~0.5 mm/rev, 切深0.5~5mm)、寿命要求(每刃加工时间10~60min)、形状(CNMG/SNMG/WNMG刀片形状, ISO 1832)、涂层Spec(TiN/TiAlN/AlCrN/DLC/金刚石, 厚度1~15μm)、客户批准条件。 |
| 2 | 粉体·硬质合金·Blank 入库 | 确认粉体Lot(WC/Co/TiC/TaC/NbC, 粒度0.5~10μm, Fisher Sub-Sieve Size)、Blank ID(压粉体/预烧结Blank)、硬质合金Grade(ISO K10~K30, P10~P40, M10~M20)、Binder含量(Co 6~12wt%, Ni 0~5wt%)与供应商证书(密度, 硬度, XRD相分析)。 |
| 3 | Press·成形·Preform | 管理Press条件(机械压机/HIP压机100~300 MPa, 多腔模具)、模具(Mold ID, 腔数2~32, 磨损0.002mm以内)、Preform ID、Green Density(理论密度50~65%, ±0.1 g/cm³)。Press后毛刺/边角缺陷检查(10x Zoom显微镜)。 |
| 4 | 烧结·HIP·热处理 | 连接烧结炉(真空烧结/HIP烧结, 最高温度1,350~1,550℃, 保温30~120min, 气氛Vacuum/Ar/H₂, 压力0.1~100bar)、烧结曲线(升温5~10℃/min, 冷却10~20℃/min)、收缩率(17~22%线性)、HIP(1,350~1,500℃, 50~150MPa Ar, 1~4h)。烧结密度(理论密度99.5%以上)。 |
| 5 | 磨削·Profile 加工 | 管理Grinding程序(CNC工具磨床, Walter/ANCA/Ewag, Diamond砂轮D46~D76)、砂轮(树脂/陶瓷/金属结合剂, RPM 3,000~8,000, 进给0.001~0.05mm/pass)、冷却液(油基/水基10~40℃, 过滤<5μm)、轮廓尺寸(刀片IC直径±0.01mm, 厚度±0.005mm, Relief Angle±0.5°)。 |
| 6 | Edge Prep·Polishing | 追踪Edge Preparation(Honing/Brush/Waterjet, Edge Radius 0.005~0.05mm, 重复精度±0.002mm)、倒角(宽度0.05~0.3mm, 角度20~45°)、抛光(机械/化学/电解, 表面粗糙度Ra≤0.05μm)条件。Edge Prep后质感SEM检查。 |
| 7 | PVD/CVD/DLC 涂层 | 管理Coating配方(PVD Arc/ Sputter, CVD HT/LT, DLC sputter)、腔体(Ionbond/Oerlikon/CemeCon, Base Pressure 10^-5~10^-6 Torr, Bias Voltage 50~150V)、膜厚(1~15μm, Ball Crater/Calotest, ±0.5μm)、附着力(Rockwell HRC压痕VDI 3198, HF1~HF4, Scratch Test Lc)、外观缺陷(光学显微镜50x)。 |
| 8 | 硬度·刃口·尺寸 Gate | 以硬度(Rockwell A/Vickers, HRA 88~94, HV 1,300~2,200)、刃口半径(Olometer/激光轮廓仪, ±0.001mm)、轮廓(影像测量系统、投影仪)、跳动(0.005~0.02mm TIR)、表面缺陷(50x显微镜/染色渗透)进行Gate判断。NCR发生时进行精密磨削/重新涂层或Scrap。 |
| 9 | 性能·磨耗测试 | 连接Wear Test(切削试验车床/铣床, 实际工件加工, 切削力测力仪)、Cutting Trial(客户提供的材料进行加工, 寿命测量: Edge Life min, Flank Wear VB max 0.3mm)、寿命结果(每分钟加工数, 每刀总加工时间)与客户应用条件。性能Gate 5~10个抽样。 |
| 10 | 打标·包装·出货 | 连接激光打标(光纤激光, 功率10~30W, ISO 1832刀片打标规格, DPM码)、包装(Insert Tray/Box/Blister Tray, Qty 10/20/50 pcs)、出货Lot(Part No+Lot No+Qty)、Certificate(CoC, 报告, 性能测试Data Sheet)。包装前最终目视检查(涂层颜色/刃口崩边)。 |

### 8.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 고객도면·사양·검사계획·공정조건·문서 revision의 적용시점을 work order 기준으로 고정한다. 측정: Drawing(ISO 1832 형상)과 Mold/Grinding Program Parameter 일치 확인. 주기: Every New Insert Type & Drawing Rev. 이상 시 Program Parameter Update → Mold 재가공 또는 재정렬. | [1] | process_step | 기준선·형상관리 |
| 2 | 원소재 Lot/Heat/Batch에서 반제품·부품 Serial·출하 Lot까지 split/merge genealogy를 유지한다. 측정: Powder Lot→Press Lot→Sinter Batch→Serial→Shipment Box. 방법: ERP/MES Batch Genealogy. 주기: Every Batch. 이상 시 Batch Reconciliation(중량계수 Loss 확인). | [2] | process_step | 원소재·Lot Genealogy |
| 3 | Machine, recipe/program, tool/fixture, 작업자 승인과 핵심 공정조건을 Lot/Serial 단위로 수집한다. 측정: Sinter Furnace Temp/Pressure Logger, HIP Program Log, Grinder Power/Spindle Load. 주기: Every Batch(1~10분 Logging) + Real-time(Grinder). 이상 시 Batch Isolation → Furnace/Grinder Calibration → 재처리 또는 재연삭. | [3] | process_step | 공정조건·설비 Recipe |
| 4 | CMM/Lab/계측/기능시험 결과를 gate로 판단하고 NCR·MRB·Rework 상태와 연결한다. 측정: Rockwell/Vickers Tester(Calibration 주기 월 1회), Vision Measuring(±0.001mm), Laser Profilometer Edge Radius. 주기: Every Sinter Batch(밀도+경도) + Every Serial(치수, Edge 조건 Sampling). 이상 시 NCR→Grinding Program 조정→재연삭 또는 Coating 재수행. | [8] | process_step | 품질 Gate·검사성적 |
| 5 | 열처리·도금·코팅·시험 등 외주 특수공정의 반출입, 승인상태, certificate를 원부품 계보와 연결한다. 측정: Coating Service Cert(두께/경도/부착력/색상 측정값) 검토. 주기: Every Coating Batch. 이상 시 Pre-treatment(Edge Prep/Bath) 조건 재확인 → 재증착. | [7] | process_step | 외주·특수공정 |
| 6 | CoA/CoC/FAI/UDI/고객라벨과 출하단위가 제품·검사·규제 요구와 일치하는지 검증한다. 측정: Laser Marking 내용(ISO 코드, Lot No)과 Shipment Data 매칭 Scan 검증. 주기: Real-time(Every Tray/Box). 이상 시 Marking 재가공 → 라벨 재발행. | [10] | process_step | 출하·문서·규제 |

### 8.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 以工单为基准固定客户图纸、规格、检验计划、工艺条件和文件版本的适用时点。测量: Drawing(ISO 1832形状)与模具/Grinding Program参数一致性确认。周期: Every New Insert Type & Drawing Rev。异常时: Program Parameter Update→模具重新加工或重新调校。 | [1] | process_step | 基准与构型管理 |
| 2 | 保持从原材料 Lot/Heat/Batch 到半成品、零件序列号和出货 Lot 的 split/merge 谱系。测量: Powder Lot→Press Lot→Sinter Batch→Serial→Shipment Box。方法: ERP/MES Batch Genealogy。周期: Every Batch。异常时: Batch Reconciliation(重量系量Loss确认)。 | [2] | process_step | 原材料与 Lot 谱系 |
| 3 | 按 Lot/Serial 采集 Machine、recipe/program、tool/fixture、人员批准和关键工艺条件。测量: 烧结炉温度/压力记录器、HIP程序日志、磨床功率/主轴负载。周期: Every Batch(1~10分钟记录)+Real-time(磨床)。异常时: Batch Isolation→烧结炉/磨床校准→重新处理或重新磨削。 | [3] | process_step | 工艺条件与设备 Recipe |
| 4 | 以 CMM/Lab/计量/功能测试结果作为 Gate 判断，并连接 NCR、MRB、Rework 状态。测量: Rockwell/Vickers试验机(校准周期每月1次)、影像测量(±0.001mm)、激光轮廓仪Edge Radius。周期: Every Sinter Batch(密度+硬度)+Every Serial(尺寸, Edge条件抽样)。异常时: NCR→Grinding Program调整→重新磨削或重新涂层。 | [8] | process_step | 质量 Gate 与检验报告 |
| 5 | 将热处理、电镀、涂层、试验等外协特殊工序的出入、批准状态和证书连接到原零件谱系。测量: 涂层服务Cert(厚度/硬度/附着力/颜色测量值)审核。周期: Every Coating Batch。异常时: 前处理(Edge Prep/Bath)条件重新确认→重新沉积。 | [7] | process_step | 外协与特殊工序 |
| 6 | 验证 CoA/CoC/FAI/UDI/客户标签与出货单元是否符合产品、检验与法规要求。测量: Laser打标内容(ISO代码, Lot No)与出货Data匹配扫描验证。周期: Real-time(每Tray/Box)。异常时: 打标重新加工→标签重发。 | [10] | process_step | 出货·文件·法规 |

### 8.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_spec, powder_lot |
| 2 | Material | process |  |  | material_spec, powder_lot, blank_id, press_lot |
| 3 | Prep | process |  |  | blank_id, press_lot, sinter_lot, machine_id |
| 4 | Primary Process | process |  |  | sinter_lot, machine_id, grinding_program_rev, tool_id |
| 5 | Precision Process | process |  |  | grinding_program_rev, tool_id, coating_recipe_id, chamber_id |
| 6 | Thermal/Special | process |  |  | coating_recipe_id, chamber_id, edge_prep_result, hardness_result |
| 7 | Surface/Clean | process |  |  | edge_prep_result, hardness_result, wear_test_result, inspection_report_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | wear_test_result, inspection_report_id, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | hardness_result, wear_test_result, inspection_report_id, shipment_lot |
| 10 | Release | process |  |  | hardness_result, wear_test_result, inspection_report_id, shipment_lot |

### 8.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Baseline | process |  |  | customer_id, drawing_rev, material_spec, powder_lot |
| 2 | Material | process |  |  | material_spec, powder_lot, blank_id, press_lot |
| 3 | Prep | process |  |  | blank_id, press_lot, sinter_lot, machine_id |
| 4 | Primary Process | process |  |  | sinter_lot, machine_id, grinding_program_rev, tool_id |
| 5 | Precision Process | process |  |  | grinding_program_rev, tool_id, coating_recipe_id, chamber_id |
| 6 | Thermal/Special | process |  |  | coating_recipe_id, chamber_id, edge_prep_result, hardness_result |
| 7 | Surface/Clean | process |  |  | edge_prep_result, hardness_result, wear_test_result, inspection_report_id |
| 8 | Quality Gate | gate |  | [2,3,4,5,6,7] | wear_test_result, inspection_report_id, shipment_lot |
| 9 | Pack | process | Precision Rework Loop |  | hardness_result, wear_test_result, inspection_report_id, shipment_lot |
| 10 | Release | process |  |  | hardness_result, wear_test_result, inspection_report_id, shipment_lot |

### 8.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 조건 확인 |
| 4 | 2 | 주요 공정 실행 |
| 4 | 3 | 공정결과 기록 |
| 8 | 1 | 계측 준비 |
| 8 | 2 | 검사 실행 |
| 8 | 3 | Gate 판정 |

### 8.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 条件确认 |
| 4 | 2 | 关键工序执行 |
| 4 | 3 | 工艺结果记录 |
| 8 | 1 | 计量准备 |
| 8 | 2 | 检验执行 |
| 8 | 3 | Gate 判定 |

### 8.9 data_capture_points

```yaml
data_capture_points:
  - customer_id
  - drawing_rev
  - material_spec
  - powder_lot
  - blank_id
  - press_lot
  - sinter_lot
  - machine_id
  - grinding_program_rev
  - tool_id
  - coating_recipe_id
  - chamber_id
  - edge_prep_result
  - hardness_result
  - wear_test_result
  - inspection_report_id
  - shipment_lot
```

---

## 9. Self-check
- [x] I01~I08 전수, slug당 §N.1~N.9 섹션 완비
- [x] control_points_detail에 category 열 전건 작성
- [x] step_expression ko/zh 행 수 = process_steps 행 수
- [x] role=gate는 각 slug 1건 이상, gate_for 명시
- [x] I03/I06은 batch_process_v1로 role=batch 포함
- [x] trace_keys는 slug별 data_capture_points 부분집합
- [x] ko/zh process_steps 행 수·step_refs·role·gate_for·trace_keys 동형
- [x] en/ja 공정·관리점 섹션 없음
- [x] JSON·코드·스크립트 수정 없음
