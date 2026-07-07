# A1 Ch3 D산업 공정 상세 데이터팩 v0.3 — 패널·신에너지 / Line Flow형 제조

> 파일명: `a1_ch3_D_process_detail_runtime_datapack_ko_zh_v0_3_2026-07-06.md`  
> 작성일: 2026-07-06  
> 대상: A1 Ch3 `process_detail_v1.json` 백필 전 MD 정본 초안  
> 범위: D01~D08, ko/zh only  
> 정책: JSON·코드·스크립트 수정 금지. 본 문서는 데이터팩 초안이며, 변환·검증은 별도 지시에서 수행한다.

---

## 0. v0.3 작성 원칙

### 0.1 B산업 리팩 지시서 적용 방식

본 D산업 데이터팩은 `A1_CH3_B_process_detail_datapack_refactor_instruction_2026-07-06.md`의 v0.3 규격을 D산업에 적용한다.

- `process_steps_detail_ko/zh`: 10단계 공정 흐름 유지
- `control_points_detail_ko/zh`: `category` 열 포함
- `step_expression_ko/zh`: `module`, `role`, `loop_hint`, `gate_for`, `trace_keys` 명시
- `operations_ko/zh`: drilldown이 필요한 대표 step에만 작성
- `data_capture_points`: slug 단위 trace key의 기준 집합
- `trace_keys`: 반드시 각 slug의 `data_capture_points` 부분집합
- `control_points_ko/zh` 별도 테이블은 작성하지 않는다. 필요 시 변환 규칙에서 `control_points_detail` 기반으로 자동 생성한다.
- en/ja 섹션은 작성하지 않는다.

### 0.2 D산업 공통 해석

D산업은 **패널·신에너지 Line Flow형 제조**로 정의한다. 공통 특징은 다음과 같다.

| 항목 | 해석 |
|---|---|
| 생산 문법 | 연속 라인·대면적 기판·Roll-to-Roll·셀/모듈 조립·Formation/Aging 등 긴 공정 체인 |
| 핵심 관리 | Recipe 조건, Inline 검사, 설비 상태, 환경 조건, 수율·등급·불량 지도, Lot/Panel/Cell genealogy |
| 정보화 초점 | MES + Recipe/Equipment interface + Inline QC + WMS/라인물류 + 수율분석 + Energy/ESG 데이터 |
| Ch3 표현 | 라인 구간을 `module`로 나누고, Inline inspection·Formation·EL·Final Test 등을 `role: gate`로 표현 |

### 0.3 외부 산업 자료 반영 메모

- 배터리 셀 제조는 전극 제조, 셀 조립, 셀 finishing/formation으로 나뉘며, 코팅·건조·Formation·Aging이 품질·비용에 큰 영향을 준다.
- 2025~2026 배터리 제조 트렌드는 Roll-to-Roll dry coating, 고속 계측, formation 최적화, 결함 조기 예측을 중심으로 발전한다.
- 태양광 모듈은 Cell stringing, Layup, Lamination, Framing/Junction box, EL/IV 검사 흐름이 핵심이다.
- 패널 제조는 TFT Array, Cell, Module, Optical/Electrical 검사, Defect map·Mura·Repair·Bin 관리가 핵심이다.
- 2024-2026년 AI 기반 스마트팩토리 고도화(디지털 트윈, 블랙라이트 팩토리, AI 비전 검사)가 세 산업 전반에 확산 중이며, EU 규제(배터리 여권 등) 대응을 위한 전수 데이터 추적성이 필수 요건으로 자리잡고 있다.

---

## 1. slug 구성

| code | slug | ko | zh | routing | preset_id 제안 | expression_tier |
|---|---|---|---|---|---|---|
| D01 | `tft_lcd_panel` | TFT-LCD 패널 | TFT-LCD面板 | RT_LINE | `line_process_v1` | line_gate_trace_v1 |
| D02 | `oled_display_panel` | OLED 디스플레이 패널 | OLED显示面板 | RT_LINE | `line_process_v1` | line_gate_trace_v1 |
| D03 | `cover_glass_touch` | 커버글라스·터치센서 | 盖板玻璃与触控传感器 | RT_LINE | `line_process_v1` | line_gate_trace_v1 |
| D04 | `battery_cell` | 이차전지 셀 | 二次电池电芯 | RT_LINE | `battery_line_v1` | battery_genealogy_v1 |
| D05 | `battery_module_pack` | 배터리 모듈·팩 | 电池模组与PACK | RT_LINE | `assembly_line_v1` | pack_trace_v1 |
| D06 | `pv_cell` | 태양광 셀 | 光伏电池片 | RT_LINE | `line_process_v1` | pv_cell_trace_v1 |
| D07 | `pv_module` | 태양광 모듈 | 光伏组件 | RT_LINE | `assembly_line_v1` | pv_module_trace_v1 |
| D08 | `functional_film_material` | 기능성 필름·신에너지 소재 | 功能膜与新能源材料 | RT_ROLL | `roll_to_roll_v1` | r2r_trace_v1 |

---

# D01 `tft_lcd_panel` — TFT-LCD 패널 / TFT-LCD面板

```yaml
code: D01
slug: tft_lcd_panel
label_ko: TFT-LCD 패널
label_zh: TFT-LCD面板
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: line_process_v1
expression_tier: line_gate_trace_v1
```

## D01.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Glass Input / Lot Start | 유리기판 lot을 투입하고 기판 ID, 크기, 세정 조건, 투입 라인을 확정한다. G8.5/G8.6 대면적 유리(2200×2500mm)를 Cassette 단위로 투입, 초음파+Scrubber 세정기(10단 Brush, DI Water 18MΩ·cm, Air Knife 건조 80℃)를 통과시킨다. Lot ID 기준 전수 Track-In Time stamp 저장. 대표 제품: TV(65"/75"), Monitor(27"), Notebook, Automotive Display. |
| 2 | Array Cleaning / Surface Preparation | TFT Array 형성 전 세정·건조·표면 상태를 관리한다. AP Plasma Cleaning(Ar/O₂, 100~300W, 30~60s) 또는 UV/Ozone 처리로 유기 잔류물 제거, 접촉각(Contact Angle <5°)을 Inline Contact Angle Meter로 측정 관리한다. Panel ID별 세정 조건 이력 저장. |
| 3 | TFT Array Patterning | 증착·노광·식각·박막 형성을 반복(5~7회 Mask Layer)하여 TFT 회로를 형성한다. CVD(PECVD SiNx/a-Si, 250~350℃, 1~5Torr), PVD(Sputter Mo/Al/Mo, DC Magnetron 1~5kW), PR Coating(Slit&Spin, 2~3μm), Stepper/Scanner 노광(365nm i-line, CD 1.5~3μm), Wet/Dry Etch(CF₄/O₂ 플라즈마, 50~200mTorr), Strip/Wet Cleaning 포함. Chamber ID별 Recipe Version 관리, Sheet/Shot 단위 Overlay 편차 <0.1μm. Lot/Panel/Shot 단위 추적. |
| 4 | Array Inspection / Repair Gate | AOI(고해상도 Line Camera, 3~5μm/pixel), 전기검사(Array Tester, Open/Short 소트키 테스트), 결함 지도 기반으로 수리·Hold·폐기 여부를 판정한다. Laser Repair(수율 >98%), Inkjet Repair 적용 가능. 결함 좌표(x, y, type, size, layer)를 Defect Map DB에 저장하고 다음 공정과 연계. Gate — Array 불량이 Cell 단계 진입을 차단하는 핵심 Checkpoint. |
| 5 | Color Filter / Cell Preparation | 컬러필터(RGB Stripe/Quad) 또는 대향기판을 준비하고 alignment 기준을 관리한다. Black Matrix(CR≥4000, 1.0~1.5μm), RGB Resin Coating(1.0~1.5μm, Dye/Pigment 분산), Photo Spacer(PS, 3~5μm), Overcoat(평탄화, 1~2μm), ITO Sputter(100~200Å, Sheet Resistance ~100Ω/□). CF 기판 ID와 Array Panel 1:1 Mapping 생성. |
| 6 | Cell Assembly / Liquid Crystal Fill | Array 기판과 CF 기판을 합착(ODF: One Drop Fill)하고 액정 주입·Seal(UV+Heat Curing) 공정을 수행한다. Seal Dispenser(UV 경화형, Line Width 300~500μm, 0.5~1.0mg/s), LC Dispense(량 제어 ±0.1mg), Vacuum Lamination(10⁻³Pa, Gap 3~5μm), UV Curing(500~3000mJ/cm²), Heat Curing(100~120℃, 30~60min). Panel ID별 Alignment Offset, Cell Gap(Interferometer, 실측 ±0.1μm) 저장. |
| 7 | Polarizer / Film Attachment | 편광판(PVA+TAC, 두께 100~200μm), 보상필름(WV, A-Plate), 보호필름을 Roll-to-Roll 방식으로 부착하고 기포·이물·위치 편차를 관리한다. Polarizer Cutter(치수 정밀도 ±0.2mm), Roll Laminator(압력 0.1~0.5MPa, 온도 40~70℃, Speed 3~10m/min), Autoclave(탈포, 50℃, 0.5MPa, 30min). Inline Vision Camera로 기포 크기·개수 저장, Polarizer Lot ID와 Panel ID 연결. |
| 8 | Optical Inspection / Mura Gate | 휘도(BL 점등 상태), 색도(CIE x,y), Mura(2D/1D, 5~10% Contrast 기준), 점결함(크기 100μm↑, 개수)을 검사하고 등급·수리 여부를 판정한다. CCD Camera + Pattern Generator + Prober Station, Gray Level 256~1024. Defect Map에 X·Y 좌표·유형 저장, Cell/Pixel 단위 결함 분류(A/B/C Grade). Gate — Optical Grade 불량이 Module 조립 진입 차단. |
| 9 | Module Assembly | Driver IC(COG 본딩, ACF Bonding, Pre-bond 80℃, Main-bond 150~200℃, 5~10s), FPC(COF Bonding, 40핀~80핀), Backlight(Edge형/Direct형, LED Bar, LGP, Diffuser, Prism Sheet, Reflector Sheet), Bezel(스테인리스/Al 합금) 등 조립. ACF Tape(이방성 도전 필름, 3~5μm Ball), Bonding Alignment(±5μm). Module Serial로 Driver IC·FPC·Backlight·Bezel 부품 Genealogy 구축. |
| 10 | Final Test / Grade / Packing | 최종 전기·광학 검사(Full On/Off, Gray Scale 32단계, Response Time, Contrast Ratio, Viewing Angle), 등급 분류(A/S+, A, B, C급), 포장·출하 라벨을 확정한다. Gamma 보정(8bit/10bit LUT, 1024 Gray Scale), Aging Test(고온 60℃, 24h, On/Off Cycling). 최종 Grade Code를 Panel Serial에 Link하여 Shipment DB 저장. |

## D01.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 玻璃投入 / 批次开始 | 投入玻璃基板批次，确认基板ID、尺寸、清洗条件与投入线体。使用G8.5/G8.6大尺寸玻璃(2200×2500mm)，经超声波+Scrubber清洗(10段Brush, DI Water 18MΩ·cm, Air Knife干燥80℃)。按Lot ID记录全Track-In时间戳。代表产品: TV(65"/75")、Monitor(27")、Notebook、车载显示器。 |
| 2 | Array清洗 / 表面准备 | TFT Array形成前管理清洗、干燥与表面状态。使用AP Plasma清洗(Ar/O₂, 100~300W, 30~60s)或UV/Ozone处理去除有机物残留，Inline接触角仪测量接触角(<5°)。按Panel ID保存清洗条件履历。 |
| 3 | TFT Array图形制程 | 通过沉积、曝光、刻蚀、薄膜形成等重复工序(5~7次Mask Layer)形成TFT电路。CVD(PECVD SiNx/a-Si, 250~350℃, 1~5Torr)、PVD(Sputter Mo/Al/Mo, DC Magnetron 1~5kW)、PR涂布(Slit&Spin, 2~3μm)、Stepper/Scanner曝光(365nm i-line, CD 1.5~3μm)、Wet/Dry刻蚀(CF₄/O₂等离子体, 50~200mTorr)。按Chamber ID管理Recipe Version，Shot级Overlay偏差<0.1μm。Lot/Panel/Shot级跟踪。 |
| 4 | Array检查 / 修复判定Gate | 基于AOI(高分辨Line Camera, 3~5μm/pixel)、电性检查(Array Tester, Open/Short测试)、缺陷地图，判定修复、Hold或报废。适用Laser Repair(收率>98%)、Inkjet Repair。将缺陷坐标(x, y, type, size, layer)存入缺陷地图DB。Gate — 阻止Array不良进入Cell阶段的关键关卡。 |
| 5 | 彩膜 / Cell准备 | 准备彩膜(RGB Stripe/Quad)或对向基板，管理对位基准。Black Matrix(CR≥4000, 1.0~1.5μm)、RGB Resin涂布(1.0~1.5μm, 染料/颜料分散)、Photo Spacer(PS, 3~5μm)、Overcoat(平坦化, 1~2μm)、ITO Sputter(100~200Å, Sheet Resistance ~100Ω/□)。建立CF基板ID与Array Panel 1:1 Mapping。 |
| 6 | Cell组立 / 液晶注入 | 贴合Array基板与CF基板(ODF: One Drop Fill)，执行液晶注入与Seal(UV+Heat固化)工序。Seal Dispenser(UV固化型, Line Width 300~500μm, 0.5~1.0mg/s)、LC Dispense(量控制±0.1mg)、真空贴合(10⁻³Pa, Gap 3~5μm)、UV固化(500~3000mJ/cm²)、加热固化(100~120℃, 30~60min)。按Panel ID保存Alignment Offset、Cell Gap(干涉仪实测±0.1μm)。 |
| 7 | 偏光片 / 膜材贴附 | 以Roll-to-Roll方式贴附偏光片(PVA+TAC, 厚度100~200μm)、补偿膜(WV, A-Plate)、保护膜，管理气泡、异物与位置偏差。Polarizer Cutter(尺寸精度±0.2mm)、Roll Laminator(压力0.1~0.5MPa, 温度40~70℃, Speed 3~10m/min)、Autoclave(脱泡, 50℃, 0.5MPa, 30min)。Inline视觉相机记录气泡尺寸数量。 |
| 8 | 光学检查 / Mura Gate | 检查亮度(BL点亮态)、色度(CIE x,y)、Mura(2D/1D, 5~10% Contrast基准)、点缺陷(粒径100μm↑, 数量)，判定等级与返修。CCD Camera + Pattern Generator + Prober Station, Gray Level 256~1024。按Cell/Pixel级分类缺陷(A/B/C Grade)。Gate — 光学等级不合格阻止进入Module组装。 |
| 9 | 模组组装 | 组装Driver IC(COG Bonding, ACF Bonding, Pre-bond 80℃, Main-bond 150~200℃, 5~10s)、FPC(COF Bonding, 40~80pin)、背光(Edge型/Direct型, LED Bar, LGP, Diffuser, Prism Sheet, Reflector Sheet)、边框(不锈钢/Al合金)。ACF Tape(异向导电膜, 3~5μm Ball)、对位精度±5μm。按Module Serial构建Driver IC·FPC·Backlight·Bezel部件Genealogy。 |
| 10 | 最终测试 / 分级 / 包装 | 完成最终电性光学测试(Full On/Off, Gray Scale 32级, Response Time, Contrast Ratio, Viewing Angle)、等级分类(A/S+, A, B, C级)、包装与出货标签确认。Gamma校正(8bit/10bit LUT, 1024级)、Aging Test(高温60℃, 24h, On/Off Cycling)。最终Grade Code链接至Panel Serial并存入Shipment DB。 |

## D01.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| 대면적 유리기판의 lot·panel ID가 공정 전 구간에서 끊기지 않아야 한다. 측정: Barcode Reader(기판 Laser Mark 2D Code)로 각 공정별 전수 스캔. 주기: Every Lot 전 구간 연속 추적. 이상 시: 소급 추적으로 불량 발생 공정 특정, Cassette 내 Lot 단위 Hold 후 재검사. | [1,3,6,9,10] | process_step | Genealogy |
| TFT Array 반복 공정은 recipe, mask, 설비 chamber, 검사 결과가 함께 추적되어야 한다. 측정: EAP(Equipment Automation Program) 장비 로그 자동 수집, RMS(Recipe Management System)에서 Recipe Version 관리. 주기: Every Panel(전수) + Real-time 장비 상태 모니터링. 이상 시: Chamber Lock/Recipe Rollback 후 Test Wafer 검증. | [3,4] | process_step | Array Process Control |
| Array 검사에서 발생한 결함 지도는 수리 이력과 최종 Mura·Grade 판정에 연결되어야 한다. 측정: AOI(3~5μm/pixel) + Array Tester 전수 검사, Defect Map DB(X·Y·Size·Type·Layer 저장). 주기: Every Panel. 이상 시: 결함 Cluster 발생 시 동일 Recipe·Chamber Batch 전체 Hold, SPC 분석. | [4,8,10] | process_step | Defect Map & Repair |
| Cell 합착과 액정 주입은 alignment, gap, seal 조건을 실측값으로 관리해야 한다. 측정: Interferometer(Cell Gap ±0.1μm), Vision System(Alignment Offset ±5μm), Seal Line Width 측정(±10μm). 주기: Every Panel. 이상 시: Offset 규격 이탈 시 해당 기판 재가공 또는 폐기, 공정 조건 피드백 조정. | [5,6] | process_step | Cell Assembly |
| 편광판·필름 부착은 자재 lot, 부착 위치, 기포·이물 불량을 함께 추적해야 한다. 측정: Inline Vision Camera(기포 크기·개수, 50μm↑ 검출, 이물 100μm↑), Polarizer 치수 Checker. 주기: Every Panel 전수 검사. 이상 시: 기포 규격 초과 시 Autoclave 재처리 또는 Panel 폐기, Polarizer Lot별 SPC. | [7] | process_step | Film Attachment |
| 광학검사 Gate는 Mura, 색도, 휘도, 점결함 기준을 제품 grade와 직접 연결해야 한다. 측정: CCD 2D Camera + Pattern Generator + Prober, Gray Level 256~1024, Mura Contrast 5~10% 기준. 주기: Every Panel 전수. 이상 시: A→B/C 등급 하향(Lot Hold→Sorting), 수리 가능 공정 회귀. | [8,10] | process_step | Optical Quality Gate |
| Driver IC·FPC·Backlight 조립 genealogy가 최종 panel ID와 연결되어야 한다. 측정: COG Bonder Alignment Camera(±5μm), ACF Pre-bond/Main-bond 온도 프로파일 기록, FPC Pull Test. 주기: Every Panel. 이상 시: Bonding 불량 Panel Rework(COG 탈착 후 재본딩), 부품 Lot 역추적. | [9,10] | process_step | Module Genealogy |
| 출하 등급과 고객 spec은 검사 raw data와 연결되어 사후 클레임 분석이 가능해야 한다. 측정: Final Grade Code를 Panel Serial에 Link, Gamma LUT·Aging Data·검사 이미지 패키지 저장. 주기: Every Panel. 이상 시: 고객 클레임 발생 시 Lot·Panel Serial 단위로 검사 Data 소급 조회, GRADE 재현 시험. | [10] | process_step | Customer Spec Trace |

## D01.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| 大尺寸玻璃基板的批次与panel ID必须在全流程中保持连续追溯。测量方法: Barcode Reader(基板Laser Mark 2D Code)在各工序全数扫描。管理周期: Every Lot全程连续。异常处理: 反向追溯定位不良工序，Cassette内批次Hold后复检。 | [1,3,6,9,10] | process_step | Genealogy |
| TFT Array重复制程需要同时追溯recipe、mask、设备chamber与检查结果。测量方法: EAP自动收集设备日志，RMS管理Recipe版本。管理周期: Every Panel(全数) + Real-time设备状态监控。异常处理: Chamber Lock/Recipe Rollback后Test Wafer验证。 | [3,4] | process_step | Array Process Control |
| Array检查产生的缺陷地图应与修复履历、最终Mura和等级判定关联。测量方法: AOI(3~5μm/pixel) + Array Tester全数检查，缺陷坐标·尺寸·类型·层存入DB。管理周期: Every Panel。异常处理: 缺陷Cluster时同Recipe·Chamber Batch全部Hold，SPC分析。 | [4,8,10] | process_step | Defect Map & Repair |
| Cell贴合与液晶注入需以实测值管理alignment、gap与seal条件。测量方法: 干涉仪(Cell Gap ±0.1μm)、视觉系统(Alignment Offset ±5μm)、Seal Line宽度(±10μm)。管理周期: Every Panel。异常处理: Offset偏离时基板返工或报废，反馈调整工序条件。 | [5,6] | process_step | Cell Assembly |
| 偏光片和膜材贴附需同时追溯材料批次、贴附位置、气泡与异物不良。测量方法: Inline视觉相机(气泡尺寸数量, 50μm↑检测, 异物100μm↑)、偏光片尺寸Checker。管理周期: Every Panel全数。异常处理: 气泡超标时Autoclave再处理或Panel报废，偏光片Lot级SPC。 | [7] | process_step | Film Attachment |
| 光学检查Gate需将Mura、色度、亮度与点缺陷标准直接连接到产品等级。测量方法: CCD 2D Camera + Pattern Generator + Prober, Gray Level 256~1024, Mura Contrast 5~10%。管理周期: Every Panel全数。异常处理: A→B/C级降等(Lot Hold→Sorting)，可修复工序回流。 | [8,10] | process_step | Optical Quality Gate |
| Driver IC、FPC、背光等组装genealogy必须连接到最终panel ID。测量方法: COG Bonder对位相机(±5μm)、ACF Pre-bond/Main-bond温度曲线记录、FPC Pull Test。管理周期: Every Panel。异常处理: Bonding不良Panel Rework(脱COG后重bonding)，部件Lot反向追溯。 | [9,10] | process_step | Module Genealogy |
| 出货等级与客户spec需连接到检查raw data，以支持客诉追溯分析。测量方法: Final Grade Code链接Panel Serial，Gamma LUT·Aging·检查图像打包保存。管理周期: Every Panel。异常处理: 客诉时按Lot/Panel Serial追溯检查数据，GRADE再现测试。 | [10] | process_step | Customer Spec Trace |

## D01.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Input | process |  |  | lot_id, panel_id, glass_id, line_id |
| 2 | Array | process |  |  | lot_id, panel_id, recipe_id, equipment_id |
| 3 | Array | process | Array Pattern Loop |  | lot_id, panel_id, mask_id, recipe_id, chamber_id |
| 4 | Gate | gate |  | [3] | panel_id, defect_map_id, repair_code, inspection_result |
| 5 | Cell | process |  |  | panel_id, cf_lot_id, material_lot_id, alignment_offset |
| 6 | Cell | process |  |  | panel_id, seal_lot_id, gap_value, recipe_id |
| 7 | Film | process |  |  | panel_id, polarizer_lot_id, film_lot_id, defect_code |
| 8 | Gate | gate |  | [5,6,7] | panel_id, mura_code, optical_grade, inspection_result |
| 9 | Module | process |  |  | panel_id, driver_ic_lot_id, fpc_lot_id, backlight_lot_id |
| 10 | Final | gate |  | [8,9] | panel_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression 연결 설명(ko)**: Glass Input(1)에서 부여된 lot_id가 Array Cleaning(2)→Array Patterning(3)으로 이어지며, step3에서 반복 노광(Array Pattern Loop)을 통해 TFT 회로가 형성된 후 step4 Gate에서 최초 검증된다. Gate[4]를 통과한 Panel은 CF 준비(5)와 합착(6), 편광판 부착(7)을 거쳐 Optical Inspection Gate(8)에서 2차 검증된다. Module Assembly(9)에서 부품이 결합된 후 Final Test(10)에서 최종 Grade 확정. 전 구간에서 panel_id가 Primary Key 역할을 하며, step4의 defect_map_id가 step8의 mura_code와 step10의 final_grade에 연결되는 연쇄 추적 구조.

## D01.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Input | process |  |  | lot_id, panel_id, glass_id, line_id |
| 2 | Array | process |  |  | lot_id, panel_id, recipe_id, equipment_id |
| 3 | Array | process | Array Pattern Loop |  | lot_id, panel_id, mask_id, recipe_id, chamber_id |
| 4 | Gate | gate |  | [3] | panel_id, defect_map_id, repair_code, inspection_result |
| 5 | Cell | process |  |  | panel_id, cf_lot_id, material_lot_id, alignment_offset |
| 6 | Cell | process |  |  | panel_id, seal_lot_id, gap_value, recipe_id |
| 7 | Film | process |  |  | panel_id, polarizer_lot_id, film_lot_id, defect_code |
| 8 | Gate | gate |  | [5,6,7] | panel_id, mura_code, optical_grade, inspection_result |
| 9 | Module | process |  |  | panel_id, driver_ic_lot_id, fpc_lot_id, backlight_lot_id |
| 10 | Final | gate |  | [8,9] | panel_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression连接说明(zh)**: Glass Input(1)生成的lot_id传递至Array Cleaning(2)→Array Patterning(3)，step3通过重复曝光(Array Pattern Loop)形成TFT电路后，在step4 Gate首次验证。通过Gate[4]的Panel经CF准备(5)、Cell贴合(6)、偏光片贴附(7)后，在Optical Inspection Gate(8)二次验证。Module Assembly(9)完成部品结合，Final Test(10)确定最终等级。全程以panel_id为主键，step4的defect_map_id连接至step8的mura_code和step10的final_grade，形成连锁追溯结构。

## D01.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 3 | 1 | 박막 증착 |
| 3 | 2 | 포토 노광 |
| 3 | 3 | 식각 |
| 3 | 4 | 박리·세정 |
| 3 | 5 | CD/Overlay 측정 |
| 8 | 1 | 점등 검사 |
| 8 | 2 | Mura 분석 |
| 8 | 3 | 광학 grade 판정 |

## D01.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 3 | 1 | 薄膜沉积 |
| 3 | 2 | 光刻曝光 |
| 3 | 3 | 刻蚀 |
| 3 | 4 | 剥离与清洗 |
| 3 | 5 | CD/Overlay测量 |
| 8 | 1 | 点灯检查 |
| 8 | 2 | Mura分析 |
| 8 | 3 | 光学等级判定 |

```yaml
data_capture_points:
  - lot_id
  - panel_id
  - glass_id
  - line_id
  - equipment_id
  - chamber_id
  - recipe_id
  - mask_id
  - defect_map_id
  - repair_code
  - inspection_result
  - cf_lot_id
  - material_lot_id
  - alignment_offset
  - seal_lot_id
  - gap_value
  - polarizer_lot_id
  - film_lot_id
  - defect_code
  - mura_code
  - optical_grade
  - driver_ic_lot_id
  - fpc_lot_id
  - backlight_lot_id
  - final_grade
  - customer_spec_id
  - shipment_label_id
```

---

# D02 `oled_display_panel` — OLED 디스플레이 패널 / OLED显示面板

```yaml
code: D02
slug: oled_display_panel
label_ko: OLED 디스플레이 패널
label_zh: OLED显示面板
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: line_process_v1
expression_tier: line_gate_trace_v1
```

## D02.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Substrate Input / Cleaning | 유리 또는 flexible substrate를 투입하고 세정·건조 조건을 확정한다. G6(1500×1850mm) 유리 또는 Polyimide(PI) 기판(두께 10~20μm, 경화 온도 350~400℃). 초음파 세정 + Megasonic + IPA 증기 건조, Contact Angle <5°. Laser Lift-Off(LLO)용 Release Layer(EL 300~400nm) 증착 포함. 대표 제품: 스마트폰(6~7"), 태블릿(10~13"), Notebook(14~16"), TV(55"/65"/77"), AR/VR MicroOLED. |
| 2 | LTPS/Oxide Backplane Formation | TFT backplane을 형성하고 이동도, 누설, 균일도를 관리한다. ELA(Excimer Laser Annealing, XeCl 308nm, 300~400mJ/cm²)로 a-Si→p-Si 결정화. Ion Doping(5×10¹⁵/㎠), Gate Insulator(PECVD SiO₂, 50~100nm), Interlayer Dielectric(SiNx, 200~400nm). TFT 이동도(mobility) 80~150㎠/V·s, 누설 전류 <1pA/μm, Vth 편차 <±0.3V. TFT Pattern Loop 4~6회 반복. |
| 3 | Backplane Inspection Gate | 전기검사(ET: Electrical Test, Probe Station, Voltage 5~10V, Current nA 단위)와 defect map으로 repair·hold·scrap 여부를 판정한다. AOI(1~2μm/pixel), Defect Map(쇼트·오픈·Vth 이상). Laser Repair 또는 TFT Circuit Redundancy 설계 활용. Gate — Backplane 불량이 OLED 증착 진입 차단. |
| 4 | OLED Deposition / Patterning | 유기 발광층 증착(Evaporation, 10⁻⁶~10⁻⁷Torr, 0.1~1nm/s), Fine Metal Mask(FMM, 20~30μm Opening) alignment(±1~3μm), 두께 균일도(전면 ±3~5%)를 관리한다. RGB+공통층(HTL, ETL, HIL, EIL) 8~15층 적층. 또는 잉크젯 프린팅(IJP: Soluble OLED, 1~10pL/drop, 254~500PPI) 방식 적용(CSOT G8.6 프린팅 OLED). Chamber ID별 Material Lot·Thickness Map 저장. |
| 5 | Encapsulation | TFE(Thin Film Encapsulation: SiNx/AlOx/SiNx 3~5층, PE-CVD+ALD, 250~400℃, 1~3μm) 또는 봉지 공정(Glass Frit Sealing, 500℃, Laser Sealing)으로 수분·산소 침투를 차단한다. WVTR(Water Vapor Transmission Rate) <10⁻⁶g/m²·day(ALD 방식), <10⁻⁵(CVD 방식). Barrier Layer 두께 Inline Ellipsometer 측정. |
| 6 | Aging / Burn-in | 초기 구동 aging으로 픽셀 안정성, 전류 특성, 휘도 변화를 확인한다. Constant Current/Voltage Drive(조건: 50~200mA/panel, 60~85℃, 1~24h). 전면 점등 후 전류 맵·휘도 맵(CCD, 256 Gray) 수집. Pixel 단위 전압 변화 모니터링으로 Burn-in/Screen Burn 여부 판정. |
| 7 | Optical Compensation | Mura 보정(Demura, CCD Camera 기반 2D 보정 데이터 생성), Gamma 보정(8bit/10bit LUT, 22/2.4 Gamma Curve), Pixel Compensation(Internal/External) 데이터를 생성한다. Compensation File을 Panel에 Writing(One-Time Programming OTP, 1~4Kb). panel_id별 보정 파일 Mapping. |
| 8 | Optical/Electrical Test Gate | 휘도(100~1000nit), 색좌표(CIE 1931 x,y), 전류(SmA 단위, 전수 측정), Dead Pixel(50μm↑, 개수 제한), Mura(2%/5% Contrast) 기준으로 판정한다. CCD Camera + SMU(Source Measure Unit) + Prober Station. Gate — 불량 Panel이 Module 단계 진입 차단. |
| 9 | Module Assembly | Driver IC(COG Bonding, ACF, 150~200℃, ±3μm, 30~200pin), FPC(COF, 20~60pin), Touch Sensor(Direct/On-Cell), Cover Glass(GG/UTG, OCA 25~50μm), Bracket/Frame 조립. Module Serial로 Driver IC·Touch·Cover Genealogy 구축. |
| 10 | Final Grade / Packing | 최종 Grade(A/S+, A, B, C급 LGD·SDC·BOE 자체 기준), 고객 spec(Apple·Samsung·Huawei 등 OEM Spec 매칭), 출하 라벨(2D Code, Country of Origin, Date Code) 확정. Panel Serial-Grade-Packing Box ID-Shipment Lot 정보 DB 등록. |

## D02.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 基板投入 / 清洗 | 投入玻璃或柔性基板，并确认清洗、干燥条件。G6(1500×1850mm)玻璃或Polyimide(PI)基板(厚度10~20μm, 固化温度350~400℃)。超声波+Megasonic清洗+IPA蒸汽干燥，Contact Angle <5°。包含Laser Lift-Off(LLO)用Release Layer(EL 300~400nm)沉积。代表产品: 手机(6~7")、平板(10~13")、Notebook(14~16")、TV(55"/65"/77")、AR/VR MicroOLED。 |
| 2 | LTPS/Oxide背板形成 | 形成TFT背板，管理迁移率、漏电与均匀性。ELA(Excimer Laser Annealing, XeCl 308nm, 300~400mJ/cm²) a-Si→p-Si晶化。Ion Doping(5×10¹⁵/㎠)、Gate Insulator(PECVD SiO₂, 50~100nm)、Interlayer Dielectric(SiNx, 200~400nm)。TFT迁移率80~150㎠/V·s、漏电流<1pA/μm、Vth偏差<±0.3V。TFT Pattern Loop重复4~6次。 |
| 3 | 背板检查Gate | 通过电性检查(ET: Probe Station, 电压5~10V, 电流nA级)与缺陷地图判定repair、hold或scrap。AOI(1~2μm/pixel)、Defect Map(短路·开路·Vth异常)。Laser Repair或TFT Redundancy设计。Gate — 阻止背板不良进入OLED蒸镀。 |
| 4 | OLED蒸镀 / 图形化 | 管理有机发光层蒸镀(Evaporation, 10⁻⁶~10⁻⁷Torr, 0.1~1nm/s)、Fine Metal Mask(FMM, 20~30μm Opening)对位(±1~3μm)、厚度均匀性(全幅±3~5%)。RGB+共通层(HTL, ETL, HIL, EIL) 8~15层叠层。或喷墨打印(IJP: Soluble OLED, 1~10pL/drop, 254~500PPI)方式(CSOT G8.6打印OLED)。按Chamber ID保存Material Lot·Thickness Map。 |
| 5 | 封装 | 通过TFE(Thin Film Encapsulation: SiNx/AlOx/SiNx 3~5层, PE-CVD+ALD, 250~400℃, 1~3μm)或封装工序(Glass Frit Sealing, 500℃, Laser Sealing)阻隔水氧渗透。WVTR <10⁻⁶g/m²·day(ALD), <10⁻⁵(CVD)。Barrier层厚度Inline椭圆偏振仪测量。 |
| 6 | Aging / Burn-in | 通过初期点亮aging确认像素稳定性、电流特性与亮度变化。Constant Current/Voltage Drive(条件: 50~200mA/panel, 60~85℃, 1~24h)。全点亮后采集电流图·亮度图(CCD, 256 Gray)。监控像素级电压变化判定Burn-in/Screen Burn。 |
| 7 | 光学补偿 | 生成Mura补偿(Demura, CCD 2D补偿数据)、Gamma校正(8bit/10bit LUT, 22/2.4 Gamma Curve)、Pixel Compensation(Internal/External)数据。补偿文件写入Panel(One-Time Programming OTP, 1~4Kb)。按panel_id Mapping补偿文件。 |
| 8 | 光电测试Gate | 按亮度(100~1000nit)、色坐标(CIE 1931 x,y)、电流(SmA级)、Dead Pixel(50μm↑, 数量限制)、Mura(2%/5% Contrast)标准判定。CCD Camera + SMU + Prober Station。Gate — 不良Panel阻止进入Module阶段。 |
| 9 | 模组组装 | 组装Driver IC(COG Bonding, ACF, 150~200℃, ±3μm, 30~200pin)、FPC(COF, 20~60pin)、Touch Sensor(Direct/On-Cell)、Cover Glass(GG/UTG, OCA 25~50μm)、Bracket/Frame。按Module Serial构建Driver IC·Touch·Cover Genealogy。 |
| 10 | 最终分级 / 包装 | 确认最终等级(A/S+, A, B, C级 按厂商标准)、客户spec(OEM Spec匹配)、出货标签(2D Code, 原产地, 日期码)。Panel Serial-Grade-Packing Box ID-Shipment Lot信息登录DB。 |

## D02.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| OLED는 backplane 결함이 최종 pixel defect로 연결되므로 panel 단위 defect map 연계가 필수다. 측정: ET(Probe Station 5~10V, nA 전류 측정), AOI(1~2μm/pixel). 주기: Every Panel 전수. 이상 시: Defect Cluster 발생 시 해당 Chamber·Recipe Batch 전체 Hold, TFT 특성 SPC 분석 후 Repair 또는 Scrap. | [2,3,8] | process_step | Backplane Defect Trace |
| 증착 공정은 mask, chamber, material lot, 두께 균일도 데이터를 panel ID와 연결해야 한다. 측정: Crystal Monitor/Quartz Sensor(증착 속도 0.1~1nm/s), Ellipsometer(두께 ±3~5%), Inline Spectrometer(광학 특성). 주기: Every Panel(전수) + Every Chamber Cycle(Material Lot 교체 시). 이상 시: 두께 편차 발생 시 Chamber Recipe 조정, Mask Cleaning 또는 교체, Material Lot 교체. | [4] | process_step | OLED Deposition |
| Encapsulation 조건은 수분·산소 민감 불량과 직접 연결되므로 장비 조건과 검사 결과를 함께 보관해야 한다. 측정: WVTR 측정(Mocon Test, Ca Test), Ellipsometer(Barrier 두께), PL(Photoluminescence) 검사. 주기: Every Lot 배치당 샘플링(Sampling 주기 1회/Lot) + Real-time Chamber Pressure 모니터링. 이상 시: Permeation Rule 이탈 시 공정 조건 조정, ALD 사이클 수 증가, 해당 Lot 전수 Ca Test 재검증. | [5,8] | process_step | Encapsulation Integrity |
| Aging·Burn-in 결과는 compensation 데이터와 final grade 판정에 연결되어야 한다. 측정: SMU(전류·전압 프로파일), CCD(휘도 맵), Pixel 전압 센싱(External Compensation). 주기: Every Panel 전수(1~24h 동안 연속 계측). 이상 시: Burn-in 검출 시 Panel Scrap, Aging Profile 조정, Compensation Data 재생성. | [6,7,10] | process_step | Aging & Compensation |
| Optical/Electrical Test Gate는 dead pixel, mura, 색좌표, 전류 기준을 제품별 spec과 연결해야 한다. 측정: CCD Camera + Pattern Generator + SMU, Dead Pixel(50μm↑), Mura Contrast(2%/5%), 색좌표(CIE ΔE<3). 주기: Every Panel 전수. 이상 시: 등급 하향 판정(A→B/C), Grade별 Binning 후 고객 Spec 매칭. | [8,10] | process_step | Final Quality Gate |
| Driver IC, FPC, Touch, Cover genealogy가 최종 panel ID에 연결되어야 한다. 측정: COG Bonder 온도/압력/시간 프로파일 기록, Vision Alignment(±3μm), FPC Pull Test(1~3kgf). 주기: Every Panel. 이상 시: Bonding 불량 Panel Rework(COG 탈착 재본딩), 부품 Lot 역추적하여 교체. | [9,10] | process_step | Module Genealogy |
| Flexible OLED의 경우 bend/lamination 이력과 외관 결함을 별도 관리해야 한다. 측정: Bend Tester(곡률 반경 R, 1~5mm, 반복 10만~20만회), Vision Inspection(Bend 크랙·Fold Line·Delamination). 주기: Every Panel(전수 외관) + 샘플링 신뢰성 시험. 이상 시: Bend Crack 발생 시 Bend 조건 조정, Lamination Profile 최적화. | [1,5,9] | process_step | Flexible Process Risk |

## D02.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| OLED背板缺陷会连接到最终pixel defect，因此必须建立panel级缺陷地图关联。测量方法: ET(Probe Station 5~10V, nA电流测量)、AOI(1~2μm/pixel)。管理周期: Every Panel全数。异常处理: Defect Cluster时对应Chamber·Recipe Batch全部Hold，TFT特性SPC分析后Repair或Scrap。 | [2,3,8] | process_step | Backplane Defect Trace |
| 蒸镀工序需将mask、chamber、材料批次与厚度均匀性数据连接到panel ID。测量方法: Crystal Monitor/Quartz Sensor(蒸镀速率0.1~1nm/s)、Ellipsometer(厚度±3~5%)、Inline Spectrometer(光学特性)。管理周期: Every Panel全数 + Every Chamber Cycle(材料批次更换时)。异常处理: 厚度偏差时调整Chamber Recipe、Mask清洗或更换、材料批次更换。 | [4] | process_step | OLED Deposition |
| 封装条件直接影响水氧敏感不良，需同时保存设备条件与检查结果。测量方法: WVTR测量(Mocon Test, Ca Test)、Ellipsometer(Barrier厚度)、PL检查。管理周期: Every Lot采样(1次/Lot) + Real-time Chamber Pressure监控。异常处理: 渗透率偏离时调整工艺条件、增加ALD cycles、该Lot全数Ca Test复验。 | [5,8] | process_step | Encapsulation Integrity |
| Aging与Burn-in结果需连接到补偿数据和最终等级判定。测量方法: SMU(电流·电压曲线)、CCD(亮度图)、Pixel电压传感(External Compensation)。管理周期: Every Panel全数(1~24h连续测量)。异常处理: Burn-in检出时Panel Scrap、调整Aging Profile、重新生成Compensation Data。 | [6,7,10] | process_step | Aging & Compensation |
| 光电测试Gate需将dead pixel、mura、色坐标、电流标准连接到产品spec。测量方法: CCD Camera + Pattern Generator + SMU, Dead Pixel(50μm↑)、Mura Contrast(2%/5%)、色坐标(CIE ΔE<3)。管理周期: Every Panel全数。异常处理: 降级判定(A→B/C)、按Grade Binning匹配客户Spec。 | [8,10] | process_step | Final Quality Gate |
| Driver IC、FPC、Touch、Cover genealogy必须连接到最终panel ID。测量方法: COG Bonder温度/压力/时间曲线记录、Vision对位(±3μm)、FPC Pull Test(1~3kgf)。管理周期: Every Panel。异常处理: Bonding不良Panel Rework(脱COG重bonding)、部件Lot反向追溯更换。 | [9,10] | process_step | Module Genealogy |
| 对于柔性OLED，需要单独管理bend、lamination履历与外观缺陷。测量方法: Bend Tester(曲率半径R, 1~5mm, 重复10万~20万次)、Vision Inspection(Bend裂纹·Fold Line·分层)。管理周期: Every Panel全数外观 + 抽样可靠性试验。异常处理: Bend Crack时调整Bend条件、优化Lamination Profile。 | [1,5,9] | process_step | Flexible Process Risk |

## D02.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Input | process |  |  | lot_id, panel_id, substrate_id, line_id |
| 2 | Backplane | process | TFT Pattern Loop |  | panel_id, recipe_id, equipment_id, chamber_id |
| 3 | Gate | gate |  | [2] | panel_id, defect_map_id, repair_code, inspection_result |
| 4 | OLED | process |  |  | panel_id, mask_id, material_lot_id, chamber_id, thickness_map_id |
| 5 | Encapsulation | process |  |  | panel_id, encapsulation_lot_id, barrier_result, recipe_id |
| 6 | Aging | process |  |  | panel_id, aging_profile_id, current_map_id, luminance_map_id |
| 7 | Compensation | process |  |  | panel_id, compensation_file_id, gamma_code, mura_code |
| 8 | Gate | gate |  | [4,5,6,7] | panel_id, optical_grade, dead_pixel_count, inspection_result |
| 9 | Module | process |  |  | panel_id, driver_ic_lot_id, fpc_lot_id, touch_lot_id, cover_lot_id |
| 10 | Final | gate |  | [8,9] | panel_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression 연결 설명(ko)**: Substrate Input(1)→LTPS Backplane(2, TFT Pattern Loop 반복)에서 TFT가 형성된 후 Backplane Inspection Gate(3)에서 1차 검증을 통과한 Panel만 OLED 증착(4)으로 진입한다. 증착→Encapsulation(5)→Aging(6)→Compensation(7)을 거쳐 Optical/Electrical Test Gate(8)에서 2차 검증. Module Assembly(9) 후 Final Gate(10)에서 최종 Grade 확정. panel_id가 전 구간 Primary Key이며, step3의 defect_map_id가 step8의 optical_grade와 step10의 final_grade에 직결되는 연쇄 구조. Flexible OLED의 경우 step1 substrate_id(Glass/PI 구분)가 step5 encapsulation 조건과 step9 cover_lot_id에 영향.

## D02.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Input | process |  |  | lot_id, panel_id, substrate_id, line_id |
| 2 | Backplane | process | TFT Pattern Loop |  | panel_id, recipe_id, equipment_id, chamber_id |
| 3 | Gate | gate |  | [2] | panel_id, defect_map_id, repair_code, inspection_result |
| 4 | OLED | process |  |  | panel_id, mask_id, material_lot_id, chamber_id, thickness_map_id |
| 5 | Encapsulation | process |  |  | panel_id, encapsulation_lot_id, barrier_result, recipe_id |
| 6 | Aging | process |  |  | panel_id, aging_profile_id, current_map_id, luminance_map_id |
| 7 | Compensation | process |  |  | panel_id, compensation_file_id, gamma_code, mura_code |
| 8 | Gate | gate |  | [4,5,6,7] | panel_id, optical_grade, dead_pixel_count, inspection_result |
| 9 | Module | process |  |  | panel_id, driver_ic_lot_id, fpc_lot_id, touch_lot_id, cover_lot_id |
| 10 | Final | gate |  | [8,9] | panel_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression连接说明(zh)**: Substrate Input(1)→LTPS Backplane(2, TFT Pattern Loop重复)形成TFT后，经Backplane Inspection Gate(3)首次验证的Panel才进入OLED蒸镀(4)。蒸镀→Encapsulation(5)→Aging(6)→Compensation(7)后，在Optical/Electrical Test Gate(8)二次验证。Module Assembly(9)后Final Gate(10)确定最终等级。全程panel_id为主键，step3的defect_map_id直接连接至step8的optical_grade和step10的final_grade。柔性OLED中step1的substrate_id影响step5封装条件和step9的cover_lot_id。

## D02.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | Mask 정렬 |
| 4 | 2 | 유기층 증착 |
| 4 | 3 | 두께 균일도 측정 |
| 6 | 1 | 초기 점등 |
| 6 | 2 | 전류·휘도 안정화 |
| 7 | 1 | Gamma 보정 |
| 7 | 2 | Mura 보정 파일 생성 |

## D02.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | Mask对位 |
| 4 | 2 | 有机层蒸镀 |
| 4 | 3 | 厚度均匀性测量 |
| 6 | 1 | 初始点亮 |
| 6 | 2 | 电流与亮度稳定化 |
| 7 | 1 | Gamma补偿 |
| 7 | 2 | Mura补偿文件生成 |

```yaml
data_capture_points:
  - lot_id
  - panel_id
  - substrate_id
  - line_id
  - recipe_id
  - equipment_id
  - chamber_id
  - defect_map_id
  - repair_code
  - inspection_result
  - mask_id
  - material_lot_id
  - thickness_map_id
  - encapsulation_lot_id
  - barrier_result
  - aging_profile_id
  - current_map_id
  - luminance_map_id
  - compensation_file_id
  - gamma_code
  - mura_code
  - optical_grade
  - dead_pixel_count
  - driver_ic_lot_id
  - fpc_lot_id
  - touch_lot_id
  - cover_lot_id
  - final_grade
  - customer_spec_id
  - shipment_label_id
```

---

# D03 `cover_glass_touch` — 커버글라스·터치센서 / 盖板玻璃与触控传感器

```yaml
code: D03
slug: cover_glass_touch
label_ko: 커버글라스·터치센서
label_zh: 盖板玻璃与触控传感器
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: line_process_v1
expression_tier: line_gate_trace_v1
```

## D03.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Glass / Film Input | 원판 유리(Gorilla Glass, Dragontrail, Al-Si 화학강화유리, 0.3~1.1mm), UTG(Ultra Thin Glass 30~100μm), PET/PI film 등 소재 lot을 투입한다. Laser Mark(2D Code)로 개별 glass ID 부여, Lot ID 기준 수량·치수·Grade 확인. 대표 제품: Smartphone Cover(2.5D/3D Glass), Tablet Cover, UTG Foldable Cover, Touch Sensor Module. |
| 2 | Cutting / Shaping | 절단(CNC Milling: Spindle 40,000~60,000rpm, 다이아몬드 Bit, 0.5~1.0mm/pass), Laser Cutting(CO₂ Laser, 10~30W, 355nm UV Laser, Heat Affected Zone <10μm), Edge Shaping(CNC Grinding, Edge Polishing, Chamfer 0.1~0.3mm) 조건을 관리한다. 치수 정밀도 ±0.05mm, Edge Crack <50μm. |
| 3 | Strengthening / Annealing | 화학강화(Ion Exchange: KNO₃ 380~450℃, 4~8h, CS(Center Stress) 600~800MPa, DoL(Depth of Layer) 30~60μm), 열처리(Pre-heating 200~300℃, Slow Cooling Annealing), 응력 완화 조건을 관리한다. Stress Meter(FSSM, 광탄성 측정), Retained Strength Bending Test(4-Point, 300~600MPa). |
| 4 | Coating / Printing | AF(Anti-Fingerprint, 5~20nm, PECVD/EB Evaporation), AR(Anti-Reflection, SiO₂/TiO₂ 다층막, 100~300nm, 반사율 <0.5%), AG(Anti-Glare, HF Etching 10~50μm 표면 거칠기) coating, BM(Black Matrix) Printing, Ink(Logo/Deco) 조건을 관리한다. Coating Thickness Inline Spectrometer 측정. |
| 5 | Touch Sensor Patterning | ITO(Indium Tin Oxide, DC Sputter, 10~50nm, Sheet Resistance 50~300Ω/□), Metal Mesh(AgNW·Cu, 3~10μm Line Width, Screen Printing/Photolithography) 등 센서 패턴을 형성한다. Sensor Channel Resistance ±15%, Capacitance 1~5pF. Sensor Pattern ID와 Glass ID Mapping. |
| 6 | Lamination | Cover Glass, Touch Sensor, OCA(Optical Clear Adhesive, 25~200μm), OCR(Optical Clear Resin, 100~300μm)를 합착한다. Vacuum Laminator(10⁻³Pa, 항온 40~80℃), Autoclave(탈포 50℃, 0.4~0.6MPa, 20~40min). 합착 후 기포(50μm↑, 개수) Inline Vision 검사. |
| 7 | Appearance Inspection Gate | Scratch(10μm↑, 길이), Chip(0.1mm↑), Stain(면적 0.5mm²↑), Particle(100μm↑), Bubble(50μm↑) 기준으로 외관을 판정한다. Dark Field/ Bright Field Vision Camera(3~5μm/pixel), Line Scan Camera. Gate — 외관 불량품이 전기검사 진입 차단. |
| 8 | Electrical / Touch Test Gate | 저항(ITO/Metal Mesh Line Resistance ±15%), Open/Short(Sensor Channel Scan, 5~10V), 터치 감도(Capacitance 변화 1~5pF, Self/Mutual Capacitance), Noise(S/N Ratio >30dB)를 검사한다. Touch Controller IC + Probe Station + Reference Capacitance Board. Gate — Touch 불량품이 최종 Packing 진입 차단. |
| 9 | Cleaning / Protection Film | 최종 세정(IPA/DI Water 초음파, 40℃, 5~10min, Air Knife 건조)과 보호필름(PET/PE 보호필름, 부착 Roll Laminator, 압력 0.1~0.3MPa, 기포 관리) 부착을 수행한다. |
| 10 | Final Grade / Packing | 등급(A/S+~C, Apple/Samsung Tier 1~3 기준), 고객 Spec, 포장 단위(Box: 50~100pcs, Pallet: 500~2000pcs)를 확정한다. Glass Serial→Box Barcode→Pallet ID→Shipment Lot Mapping. |

## D03.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 玻璃 / 膜材投入 | 投入原片玻璃(Gorilla Glass, Dragontrail, Al-Si化学强化玻璃, 0.3~1.1mm)、UTG(Ultra Thin Glass 30~100μm)、PET/PI film等材料批次。Laser Mark(2D Code)赋予单片glass ID，按Lot ID确认数量·尺寸·Grade。代表产品: 手机Cover(2.5D/3D Glass)、平板Cover、UTG折叠Cover、触控Sensor Module。 |
| 2 | 切割 / 成型 | 管理切割(CNC Milling: Spindle 40,000~60,000rpm, 钻石Bit, 0.5~1.0mm/pass)、Laser Cutting(CO₂ Laser, 10~30W, 355nm UV Laser, HAZ <10μm)、Edge Shaping(CNC Grinding, Edge Polishing, Chamfer 0.1~0.3mm)条件。尺寸精度±0.05mm, Edge Crack <50μm。 |
| 3 | 强化 / 退火 | 管理化学强化(Ion Exchange: KNO₃ 380~450℃, 4~8h, CS 600~800MPa, DoL 30~60μm)、热处理(Pre-heating 200~300℃, Slow Cooling Annealing)、应力释放条件。Stress Meter(FSSM, 光弹性测量), Retained Strength Bending Test(4-Point, 300~600MPa)。 |
| 4 | 涂布 / 印刷 | 管理AF(5~20nm, PECVD/EB蒸镀)、AR(SiO₂/TiO₂多层膜, 100~300nm, 反射率<0.5%)、AG(HF Etching 10~50μm表面粗糙度) coating、BM Printing、Ink(Logo/Deco)条件。Coating Thickness Inline Spectrometer测量。 |
| 5 | 触控Sensor图形化 | 形成ITO(DC Sputter, 10~50nm, Sheet Resistance 50~300Ω/□)、Metal Mesh(AgNW·Cu, 3~10μm Line Width, Screen Printing/光刻)等sensor图形。Sensor Channel Resistance ±15%, Capacitance 1~5pF。Sensor Pattern ID与Glass ID Mapping。 |
| 6 | 贴合 | 贴合Cover Glass、Touch Sensor、OCA(25~200μm)、OCR(100~300μm)。真空贴合机(10⁻³Pa, 恒温40~80℃)、Autoclave(脱泡50℃, 0.4~0.6MPa, 20~40min)。贴合后Inline Vision检查气泡(50μm↑, 数量)。 |
| 7 | 外观检查Gate | 按Scratch(10μm↑, 长度)、Chip(0.1mm↑)、Stain(面积0.5mm²↑)、Particle(100μm↑)、Bubble(50μm↑)标准判定外观。Dark Field/Bright Field视觉相机(3~5μm/pixel), Line Scan Camera。Gate — 外观不良品阻止进入电性检查。 |
| 8 | 电性 / 触控测试Gate | 检查电阻(ITO/Metal Mesh Line Resistance ±15%)、Open/Short(Sensor Channel Scan, 5~10V)、触控灵敏度(Capacitance变化1~5pF, Self/Mutual Capacitance)、Noise(S/N Ratio >30dB)。Touch Controller IC + Probe Station + Reference Capacitance Board。Gate — Touch不良阻止进入最终包装。 |
| 9 | 清洗 / 保护膜 | 执行最终清洗(IPA/DI Water超声波, 40℃, 5~10min, Air Knife干燥)与保护膜贴附(PET/PE保护膜, Roll Laminator, 压力0.1~0.3MPa, 气泡管理)。 |
| 10 | 最终分级 / 包装 | 确认等级(A/S+~C, Apple/Samsung Tier 1~3标准)、客户spec、包装单位(Box: 50~100pcs, Pallet: 500~2000pcs)。Glass Serial→Box Barcode→Pallet ID→Shipment Lot Mapping。 |

## D03.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| 원판 소재 lot과 개별 glass ID의 분할 genealogy가 유지되어야 한다. 측정: Laser Mark(2D Code) Reader로 개별 스캔, Lot→Glass ID 분할 매핑. 주기: Every Glass 전수. 이상 시: Lot 내 불량 발생 시 동일 Lot Glass 전수 Hold 후 재검사, 원판 Lot Supplier 역추적. | [1,2,10] | process_step | Material Split Genealogy |
| Cutting·CNC 조건은 edge crack, chip, 파손 불량과 연결되어야 한다. 측정: CNC Spindle Power 모니터링, Vision Edge Inspection(200μm 범위, 3~5μm/pixel), 치수 측정 Laser Micrometer(±0.05mm). 주기: Every Glass 전수 Edge 검사 + CNC Program별 Sampling 치수 검증. 이상 시: Edge Crack 빈도 증가 시 CNC Bit 교체 주기 단축, Feed Speed/RPM 조정. | [2,7] | process_step | Edge Quality |
| 강화 공정은 응력, 교환 시간, bath 조건을 검사 결과와 연결해야 한다. 측정: FSSM(Fast Spectral Stress Meter, CS·DoL 실측), KNO₃ Bath 온도(380~450℃) TC(열전대) 실시간 모니터링, Ion Exchange Time 자동 기록. 주기: Every Lot Sampling(5~10pcs/Lot, CS·DoL 측정) + Bath Temperature Real-time. 이상 시: CS/DoL 규격 이탈 시 Bath 분석(K⁺ 농도) 후 KNO₃ 교체 또는 Bath 온도 조정, 해당 Lot 전수 강도 시험. | [3,7] | process_step | Strengthening Control |
| Coating·Printing 조건은 외관 결함과 내구성 검사 결과에 연결되어야 한다. 측정: Inline Spectrometer(Coating 두께), Contact Angle Meter(AF: 100~120°, AR: 반사율 <0.5%), Taber Abrasion Test(CS-10F, 500g, 1000cycle 내구성). 주기: Every Lot Batches 샘플링 + Inline 전수 두께 모니터링. 이상 시: Coating 두께 편차 → Recipe 조정, AF 수명 불량 → Deposition Rate 재설정. | [4,7,10] | process_step | Coating Quality |
| Touch sensor 패턴 결함은 전기 검사 결과와 위치 정보로 관리해야 한다. 측정: Probe Station(Channel Scan, Open/Short, 5~10V), Capacitance Meter(Self/Mutual 1~5pF). 주기: Every Glass 전수 전기 검사. 이상 시: Open/Short 채널 위치 기반 Mask·Photo 조건 분석, Sensor Pattern Recipe 피드백. | [5,8] | process_step | Touch Circuit Trace |
| Lamination은 OCA/OCR lot, 압력, 진공, 기포 불량을 함께 추적해야 한다. 측정: Vision Camera(기포 50μm↑ 전수 검출), Autoclave 온도·압력 프로파일 기록. 주기: Every Glass. 이상 시: 기포 규격 초과 시 Autoclave 재처리 또는 Panel Scrap, OCA/OCR Lot 교체. | [6,7] | process_step | Lamination Quality |
| 최종 등급은 외관·전기·터치 검사 결과를 종합해 고객 spec 기준으로 확정해야 한다. 측정: 외관(Scratch·Chip·Stain·Particle·Bubble) + 전기(저항·Open/Short) + 터치(감도·Noise) 종합. 주기: Every Glass 전수. 이상 시: Grade별 Binning 후 저급품 외주 판매/재가공, Engineering 분석 요청. | [7,8,10] | process_step | Final Grade Gate |

## D03.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| 原片材料批次与单片glass ID的分割genealogy必须保持连续。测量方法: Laser Mark(2D Code) Reader全数扫描，Lot→Glass ID分割映射。管理周期: Every Glass全数。异常处理: 批次内不良时，同Lot Glass全数Hold后复检，原片Lot供应商反向追溯。 | [1,2,10] | process_step | Material Split Genealogy |
| Cutting与CNC条件需连接到edge crack、chip与破片不良。测量方法: CNC Spindle Power监控、Vision Edge Inspection(200μm范围, 3~5μm/pixel)、Laser Micrometer尺寸测量(±0.05mm)。管理周期: Every Glass全数Edge检查 + CNC Program别抽样尺寸验证。异常处理: Edge Crack增加时缩短CNC Bit更换周期、调整Feed Speed/RPM。 | [2,7] | process_step | Edge Quality |
| 强化工序需将应力、交换时间、bath条件与检查结果关联。测量方法: FSSM(CS·DoL实测)、KNO₃ Bath温度(380~450℃) TC实时监控、Ion Exchange Time自动记录。管理周期: Every Lot抽样(5~10pcs/Lot) + Bath Temperature实时。异常处理: CS/DoL偏离时Bath分析(K⁺浓度)后KNO₃更换或调温，该Lot全数强度试验。 | [3,7] | process_step | Strengthening Control |
| Coating与Printing条件需连接到外观缺陷和耐久性检查结果。测量方法: Inline Spectrometer(Coating厚度)、Contact Angle Meter(AF:100~120°, AR:反射率<0.5%)、Taber Abrasion Test(CS-10F, 500g, 1000cycle耐久性)。管理周期: Every Lot抽样 + Inline全数厚度监控。异常处理: 厚度偏差→Recipe调整、AF寿命不良→Deposition Rate重设。 | [4,7,10] | process_step | Coating Quality |
| Touch sensor图形缺陷需以电性检查结果和位置数据管理。测量方法: Probe Station(Channel Scan, Open/Short, 5~10V)、Capacitance Meter(Self/Mutual 1~5pF)。管理周期: Every Glass全数电性检查。异常处理: Open/Short通道位置分析Mask·Photo条件、Sensor Pattern Recipe反馈。 | [5,8] | process_step | Touch Circuit Trace |
| Lamination需同时追溯OCA/OCR批次、压力、真空与气泡不良。测量方法: Vision Camera(气泡50μm↑全数检出)、Autoclave温度·压力曲线记录。管理周期: Every Glass。异常处理: 气泡超标时Autoclave再处理或Panel Scrap、更换OCA/OCR批次。 | [6,7] | process_step | Lamination Quality |
| 最终等级需综合外观、电性、触控检查结果并按客户spec确定。测量方法: 外观(Scratch·Chip·Stain·Particle·Bubble) + 电性(电阻·Open/Short) + 触控(灵敏度·Noise)综合。管理周期: Every Glass全数。异常处理: 按Grade Binning，次级品外售/再加工，Engineering分析请求。 | [7,8,10] | process_step | Final Grade Gate |

## D03.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Input | process |  |  | lot_id, glass_id, material_lot_id, line_id |
| 2 | Shaping | process |  |  | glass_id, recipe_id, equipment_id, cutting_program_id |
| 3 | Strengthening | process |  |  | glass_id, bath_id, recipe_id, stress_value |
| 4 | Coating | process |  |  | glass_id, coating_lot_id, ink_lot_id, recipe_id |
| 5 | Sensor | process |  |  | glass_id, sensor_pattern_id, material_lot_id, equipment_id |
| 6 | Lamination | process |  |  | glass_id, oca_lot_id, ocr_lot_id, lamination_profile_id |
| 7 | Gate | gate |  | [2,3,4,6] | glass_id, appearance_grade, defect_code, inspection_result |
| 8 | Gate | gate |  | [5,6] | glass_id, resistance_value, touch_result, inspection_result |
| 9 | Finish | process |  |  | glass_id, cleaning_recipe_id, protection_film_lot_id |
| 10 | Final | gate |  | [7,8,9] | glass_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression 연결 설명(ko)**: Glass Input(1) → Cutting/Shaping(2) → Strengthening(3) → Coating/Printing(4) → Touch Sensor Patterning(5) → Lamination(6) 순으로 진행된다. Appearance Gate(7)가 [2,3,4,6]의 결과를 검증한 후, Electrical/Touch Gate(8)가 [5,6]의 전기적 특성을 검증한다. 최종 Cleaning(9) 후 Final Gate(10)에서 등급 확정. glass_id가 전 구간 Primary Key이며, step7의 defect_code와 step10의 final_grade가 직결. Sensor가 없는 Cover-only 제품의 경우 step5 Sensor는 Skip되며, gate_for[8]에서 [5]가 생략됨.

## D03.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Input | process |  |  | lot_id, glass_id, material_lot_id, line_id |
| 2 | Shaping | process |  |  | glass_id, recipe_id, equipment_id, cutting_program_id |
| 3 | Strengthening | process |  |  | glass_id, bath_id, recipe_id, stress_value |
| 4 | Coating | process |  |  | glass_id, coating_lot_id, ink_lot_id, recipe_id |
| 5 | Sensor | process |  |  | glass_id, sensor_pattern_id, material_lot_id, equipment_id |
| 6 | Lamination | process |  |  | glass_id, oca_lot_id, ocr_lot_id, lamination_profile_id |
| 7 | Gate | gate |  | [2,3,4,6] | glass_id, appearance_grade, defect_code, inspection_result |
| 8 | Gate | gate |  | [5,6] | glass_id, resistance_value, touch_result, inspection_result |
| 9 | Finish | process |  |  | glass_id, cleaning_recipe_id, protection_film_lot_id |
| 10 | Final | gate |  | [7,8,9] | glass_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression连接说明(zh)**: Glass Input(1)→Cutting/Shaping(2)→Strengthening(3)→Coating/Printing(4)→Touch Sensor(5)→Lamination(6)顺序。Appearance Gate(7)验证[2,3,4,6]的结果后，Electrical/Touch Gate(8)验证[5,6]的电性特性。最终Cleaning(9)后Final Gate(10)确定等级。glass_id全程为主键，step7的defect_code直接连接step10的final_grade。Cover-only产品跳过step5时，gate_for[8]中省略[5]。

## D03.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 원판 절단 |
| 2 | 2 | CNC 가공 |
| 2 | 3 | Edge polishing |
| 6 | 1 | OCA/OCR 도포 |
| 6 | 2 | 진공 합착 |
| 6 | 3 | 탈포·경화 |

## D03.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 原片切割 |
| 2 | 2 | CNC加工 |
| 2 | 3 | Edge polishing |
| 6 | 1 | OCA/OCR涂布 |
| 6 | 2 | 真空贴合 |
| 6 | 3 | 脱泡与固化 |

```yaml
data_capture_points:
  - lot_id
  - glass_id
  - material_lot_id
  - line_id
  - recipe_id
  - equipment_id
  - cutting_program_id
  - bath_id
  - stress_value
  - coating_lot_id
  - ink_lot_id
  - sensor_pattern_id
  - oca_lot_id
  - ocr_lot_id
  - lamination_profile_id
  - appearance_grade
  - defect_code
  - inspection_result
  - resistance_value
  - touch_result
  - cleaning_recipe_id
  - protection_film_lot_id
  - final_grade
  - customer_spec_id
  - shipment_label_id
```

---

# D04 `battery_cell` — 이차전지 셀 / 二次电池电芯

```yaml
code: D04
slug: battery_cell
label_ko: 이차전지 셀
label_zh: 二次电池电芯
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: battery_line_v1
expression_tier: battery_genealogy_v1
```

## D04.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Raw Material / Slurry Preparation | 활물질(NCM·LFP·LCO·LMFP, 입도 D50 3~15μm), 도전재(Carbon Black·CNT, 5~30nm), 바인더(PVDF·SBR·CMC), 용매(NMP·Water) lot을 계량(±0.1g 정밀 저울)하여 Vacuum Mixer(Planetary, 1,000~3,000rpm, 30~120min, 진공도 <−95kPa)로 혼합, 양극/음극 slurry를 준비한다. 점도(3,000~10,000cP, Brookfield), 고형분(45~70%), 입도 측정. Slurry Batch ID별 전수 데이터 저장. 대표 제품: EV(18650·21700·4680 원통형), Pouch Cell(50~150Ah), Prismatic Cell. |
| 2 | Electrode Coating / Drying | 집전체(Al Foil 12~20μm 양극, Cu Foil 6~12μm 음극)에 slurry를 Slot-Die Coating(Coating Gap 100~300μm, Line Speed 10~80m/min)하고, Oven Drying(Zone별 80~150℃, 5~30m 길이, 풍속 1~5m/s) 조건, Coating Weight(±2%, Inline X-ray/β-ray Gauge), Coating Defect(Pinhole, Streak, Edge Irregularity)를 관리한다. 전극 Roll ID별 Coating Map 저장. 건식전극(Dry Electrode: PTFE Binder, Powder Press) 신규 공정은 별도 Recipe 관리. |
| 3 | Calendering / Slitting | Roll Press(Calendering: 선압 500~2,000kgf/cm, 온도 RT~100℃, Speed 10~50m/min)로 전극 밀도(2.5~3.8g/cc, 양극 기준) 관리. Slitter(절단 정밀도 ±0.1mm, Burr <10μm, Edge Wave <5mm, Dust 제거용 Vacuum Unit)로 폭 가공. Density 측정(Inline Density Gauge, X-ray). 전극 Roll Lot별 Slitting Lot 분할 관리. |
| 4 | Electrode Inspection Gate | Pinhole(100μm↑, Inline Vision Camera 10~20μm/pixel, Dark Field Illumination), Scratch(50μm↑, Depth), Coating Defect(Weight 편차 ±2% 초과), 두께(Inline Thickness Gauge, Contact/Non-Contact ±1μm)·중량 편차를 검사한다. Gate — 전극 결함이 Cell 조립 진입 차단. Defect Map을 전극 Roll ID 단위로 저장. |
| 5 | Cell Assembly | Winding(원통형·각형: Winder Tension 0.5~2N, Alignment ±0.5mm, Speed 2~10m/min) 또는 Stacking(파우치형: Z-Stacker, Separator+Electrode 교차 적층, 정밀도 ±0.3mm), Tab Welding(Ultrasonic Welding: 20~40kHz, 진폭 10~50μm, 압력 0.1~0.5MPa), Case Insertion(Can/Prismatic Case, Al/Steel)으로 셀 구조를 만든다. Electrode Roll ID·Separator Lot·Tab Lot이 Cell ID에 Genealogy 연결. |
| 6 | Electrolyte Filling / Sealing | 전해액 주입(Ar Atmosphere Glove Box, Dew Point <−50℃, 주입량 ±0.1g, Syringe/Vacuum 방식, 0.1~0.5mL/g cell), Wetting(진공 침지, 40~60℃, 0.5~24h), Sealing(파우치: Heat Sealing 150~200℃, 2~5s, 두께 3~10mm; Can: Laser Welding 후 Cap Sealing) 조건을 관리한다. Cell ID별 Filling Profile·Seal 조건 전수 저장. |
| 7 | Formation | 초기 충방전(CC/CV: Constant Current 0.02~0.5C, Cut-off Voltage 3.0~4.5V, CV to 0.05C, 온도 25~45℃)으로 SEI(Solid Electrolyte Interface)를 형성하고 전압·전류·용량 데이터를 Formation Channel 단위(32~512ch/Chamber)로 수집한다. Formation Profile ID별 전압 곡선·dQ/dV·용량 저장. Digital Twin + AI 기반 이상 조기 탐지(볼륨 팽창, 전압 이상 드리프트). |
| 8 | Aging / Degassing | Aging(Open Circuit 전압 OCV 모니터링 25~45℃, 1~7일, 전압 드리프트 <5mV/day), Leak Test(He Leak Detector, Mass Spec, <10⁻⁶mbar·L/s 또는 Pressure Decay <1kPa/10min), Gas 제거(파우치 Degassing: 1차 Sealing 후 Gas Pouch 절단, 2차 Sealing, 진공 1~10Torr) 조건을 관리한다. Cell ID별 Aging Time·OCV Curve·Leak Rate 저장. |
| 9 | Grading / Safety Test Gate | 용량(Grading: Capacity ±3%, CC/CV Full Cycle), 내부저항(IR: AC 1kHz, 10~50mΩ, Hioki/Keysight Meter), OCV(3.0~4.2V, ±1mV), 절연(Hi-Pot: 500~1,500V, Leakage Current <100μA), Leak 기준으로 Grade를 판정한다. 셀당 50~100개 파라미터 전수 데이터 기록. Gate — Grade 미달 Cell은 Module 조립 진입 차단. |
| 10 | Final Packing / Cell Shipment | 셀 Grade(A/B/C, Capacity Bin 코드), Barcode/QR Code(셀 UID), 포장(Tray·Box·Pallet 단위, ESD Packing, Vacuum Sealing), 출하 Lot을 확정한다. Cell Barcode→Box ID→Pallet ID→Shipment Lot ID 전수 Mapping. EU Battery Passport(2026 시행) 대응 데이터 패키지 구성(CO₂ footprint, 재활용률, 공급망 정보). |

## D04.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原材料 / 浆料制备 | 称量(±0.1g精密天平)活性材料(NCM·LFP·LCO·LMFP, 粒径D50 3~15μm)、导电剂(Carbon Black·CNT, 5~30nm)、粘结剂(PVDF·SBR·CMC)、溶剂(NMP·Water)批次，真空搅拌机(Planetary, 1,000~3,000rpm, 30~120min, 真空度<−95kPa)混合，制备正负极浆料。粘度(3,000~10,000cP, Brookfield)、固含量(45~70%)、粒径测量。按Slurry Batch ID全数保存数据。代表产品: EV(18650·21700·4680圆柱)、Pouch Cell(50~150Ah)、Prismatic Cell。 |
| 2 | 极片涂布 / 干燥 | 在集流体(Al Foil 12~20μm正极, Cu Foil 6~12μm负极)上以Slot-Die Coating(Coating Gap 100~300μm, Line Speed 10~80m/min)涂布浆料、Oven干燥(Zone别80~150℃, 5~30m长, 风速1~5m/s)条件、涂布重量(±2%, Inline X-ray/β-ray Gauge)、涂布缺陷(Pinhole, Streak, Edge Irregularity)管理。电极Roll ID级Coating Map保存。干法电极(Dry Electrode: PTFE Binder, Powder Press)新工艺独立Recipe管理。 |
| 3 | 辊压 / 分切 | Roll Press(Calendering: 线压500~2,000kgf/cm, 温度RT~100℃, Speed 10~50m/min)管理电极密度(2.5~3.8g/cc正极基准)。Slitter(切割精度±0.1mm, Burr<10μm, Edge Wave<5mm, 除尘Vacuum Unit)宽度加工。密度测量(Inline Density Gauge, X-ray)。电极Roll Lot级Slitting Lot分割管理。 |
| 4 | 极片检查Gate | 检查Pinhole(100μm↑, Inline Vision Camera 10~20μm/pixel, Dark Field), Scratch(50μm↑, Depth), Coating Defect(Weight偏差±2%超标), 厚度(Inline Thickness Gauge, Contact/Non-Contact ±1μm)·重量偏差。Gate — 电极缺陷阻止进入Cell装配。缺陷地图按电极Roll ID保存。 |
| 5 | 电芯装配 | 卷绕(圆柱·方形: Winder Tension 0.5~2N, Alignment ±0.5mm, Speed 2~10m/min)或叠片(软包型: Z-Stacker, 隔膜+电极交替层叠, 精度±0.3mm)、Tab焊接(Ultrasonic Welding: 20~40kHz, 振幅10~50μm, 压力0.1~0.5MPa)、入壳(Can/Prismatic Case, Al/Steel)形成电芯结构。电极Roll ID·隔膜Lot·Tab Lot连接到Cell ID的Genealogy。 |
| 6 | 注液 / 封口 | 注液(Ar Atmosphere Glove Box, Dew Point<−50℃, 注液量±0.1g, Syringe/Vacuum方式, 0.1~0.5mL/g cell)、Wetting(真空浸渍, 40~60℃, 0.5~24h)、封口(软包: Heat Sealing 150~200℃, 2~5s, 厚度3~10mm; 金属壳: Laser Welding后Cap Sealing)条件管理。按Cell ID全数保存Filling Profile·Seal条件。 |
| 7 | Formation | 初始充放电(CC/CV: Constant Current 0.02~0.5C, Cut-off Voltage 3.0~4.5V, CV to 0.05C, 温度25~45℃)形成SEI，采集电压·电流·容量数据于Formation Channel(32~512ch/Chamber)。按Formation Profile ID保存电压曲线·dQ/dV·容量。Digital Twin + AI早期异常检测(体积膨胀, 异常电压漂移)。 |
| 8 | Aging / Degassing | Aging(OCV监控25~45℃, 1~7天, 电压漂移<5mV/day)、Leak Test(He Leak Detector, Mass Spec, <10⁻⁶mbar·L/s或Pressure Decay <1kPa/10min)、除气(软包Degassing: 1次Sealing后Gas Pouch切除, 2次Sealing, 真空1~10Torr)条件管理。按Cell ID保存Aging Time·OCV Curve·Leak Rate。 |
| 9 | 分容 / 安全测试Gate | 容量(Grading: Capacity ±3%, CC/CV Full Cycle)、内阻(IR: AC 1kHz, 10~50mΩ, Hioki/Keysight Meter)、OCV(3.0~4.2V, ±1mV)、绝缘(Hi-Pot: 500~1,500V, Leakage Current<100μA)、Leak标准判定Grade。每cell 50~100参数全数数据记录。Gate — Grade不达标Cell阻止进入Module组装。 |
| 10 | 最终包装 / 电芯出货 | 确认电芯Grade(A/B/C, Capacity Bin代码)、Barcode/QR Code(电芯UID)、包装(Tray·Box·Pallet单位, ESD Packing, Vacuum Sealing)、出货Lot。Cell Barcode→Box ID→Pallet ID→Shipment Lot ID全数Mapping。EU Battery Passport(2026施行)数据包(CO₂足迹, 回收率, 供应链信息)。 |

## D04.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| 원재료 lot, slurry batch, 전극 roll, cell barcode의 genealogy가 끊기지 않아야 한다. 측정: Barcode/QR Reader(원재료 Lot ID, Slurry Batch ID, 전극 Roll ID, Cell ID 각 단계 전수 스캔). 주기: Every Batch/Lot 전수. 이상 시: Cell Grade 불량 발생 시 Cell ID→전극 Roll→Slurry Batch→원재료 Lot 순 역추적, 원인 Lot Hold 후 대체. | [1,2,3,5,10] | process_step | Battery Genealogy |
| 코팅·건조 조건은 전극 두께·중량·결함과 연결되어 셀 성능 분석에 사용되어야 한다. 측정: Inline β-ray Gauge(Coating Weight ±2%), Inline Vision(Defect Map), Dryer Zone 온도 TC(열전대) 전구간 Real-time. 주기: Real-time 연속 + Every Roll End 샘플링. 이상 시: Coating Weight 편차 → Slot-Die Gap 조정, Drying 불균일 → Zone 온도/풍속 재설정, 해당 Roll Batch 전수 검사. | [2,4,9] | process_step | Electrode Coating Quality |
| Calendering과 slitting 조건은 밀도, burr, edge 결함, 단락 위험과 연결되어야 한다. 측정: Inline Density Gauge(X-ray, ±0.03g/cc), Burr Inspector(Laser Triangulation, <10μm), Edge Wave 측정. 주기: Real-time 연속 + Every Slitting Program 변경 시 Sampling. 이상 시: Burr 규격 초과 → Slitter Blade 교체 주기 단축, Density 편차 → Roll Press Gap 조정. | [3,4,9] | process_step | Electrode Dimensional Control |
| Cell Assembly는 winding/stacking ID, tab welding 조건, case lot을 셀 barcode에 연결해야 한다. 측정: Winder Tension Sensor(0.5~2N), Welder Power Monitor(W, Ultrasonic Amplitude·Time 기록), Vision Alignment(±0.3~0.5mm). 주기: Every Cell 전수. 이상 시: Welding 불량 → Rework(Weld 재실행) 또는 Scrap, Alignment 이탈 → Winder Tension/Tab Position 조정. | [5,10] | process_step | Cell Assembly Trace |
| 전해액 주입·wetting·sealing 조건은 leak, gas, OCV 변동과 함께 분석되어야 한다. 측정: Filling Weight Check(±0.1g, Inline Balance), Glove Box Dew Point Sensor(−50℃↓), Heat Sealer 온도·압력·시간 프로파일. 주기: Every Cell 전수. 이상 시: Leak 검출 → Sealing 조건 강화(온도↑·시간↑), Filling 부족 → Syringe Calibration 재실행. | [6,8,9] | process_step | Electrolyte & Seal Control |
| Formation profile은 capacity, resistance, voltage curve, abnormal channel 데이터를 포함해야 한다. 측정: Battery Cycler(Channel 32~512ch, CC/CV 제어, 전압 ±1mV, 전류 ±0.05%), dQ/dV 분석. 주기: Every Channel 전수 Cycle 데이터 저장(1~3 Cycles). 이상 시: Abnormal Channel(Voltage Drop/Spike) → 해당 Channel Cell Scrap, Formation Profile 조정(Current·Cut-off Voltage 최적화). | [7,9] | process_step | Formation Data |
| Aging·Grading 결과는 셀 등급과 모듈 투입 가능 여부를 결정하는 품질 Gate로 사용되어야 한다. 측정: Hioki/Keysight Meter(IR AC 1kHz), Multimeter(OCV ±1mV), Hi-Pot Tester(절연 500~1,500V). 주기: Every Cell 전수(1~7일 Aging 연속 모니터링). 이상 시: Grade 불량 → 해당 Cell 폐기 또는 저급 Bin 전환, Grading 기준 재검토. | [8,9,10] | process_step | Grading Gate |
| 건식전극·고속 R2R 등 신규 공정은 별도 recipe version과 실험 lot 이력으로 분리 관리해야 한다. 측정: Dry Electrode: Powder Feeder Rate·Press Force·Temperature Profile 기존과 별도 Data Set. 주기: Experimental Lot Only, 기존 공정과 분리 관리. 이상 시: 파일럿 라인 데이터 기반 양산 Recipe Parameter 도출, Recipe Version 통제. | [1,2,3] | industry | Process Innovation Readiness |

## D04.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| 原材料批次、浆料batch、极片roll与cell barcode的genealogy必须连续。测量方法: Barcode/QR Reader(原材料Lot ID, Slurry Batch ID, 电极Roll ID, Cell ID各阶段全数扫描)。管理周期: Every Batch/Lot全数。异常处理: 发生Cell Grade不良时按Cell→电极Roll→Slurry Batch→原材料Lot反向追溯，Hold问题Lot后更换。 | [1,2,3,5,10] | process_step | Battery Genealogy |
| 涂布与干燥条件需连接到极片厚度、重量、缺陷，并用于电芯性能分析。测量方法: Inline β-ray Gauge(涂布重量±2%)、Inline Vision(Defect Map)、Dryer Zone温度TC全段实时。管理周期: Real-time连续 + Every Roll End采样。异常处理: 涂布重量偏差→调整Slot-Die Gap、干燥不均→调整Zone温度/风速、该Roll Batch全数复检。 | [2,4,9] | process_step | Electrode Coating Quality |
| 辊压与分切条件需连接到密度、毛刺、边缘缺陷与短路风险。测量方法: Inline Density Gauge(X-ray, ±0.03g/cc)、Burr Inspector(Laser Triangulation, <10μm)、Edge Wave测量。管理周期: Real-time连续 + Slitting Program变更时采样。异常处理: Burr超标→缩短Slitter Blade更换周期、密度偏差→调整Roll Press Gap。 | [3,4,9] | process_step | Electrode Dimensional Control |
| Cell Assembly需将winding/stacking ID、tab焊接条件、case批次连接到cell barcode。测量方法: Winder Tension Sensor(0.5~2N)、Welder Power Monitor(W, 超声波振幅·时间记录)、Vision Alignment(±0.3~0.5mm)。管理周期: Every Cell全数。异常处理: 焊接不良→Rework或Scrap、Alignment偏离→调整Winder Tension/Tab Position。 | [5,10] | process_step | Cell Assembly Trace |
| 注液、wetting、sealing条件需与leak、gas、OCV波动一起分析。测量方法: Filling Weight Check(±0.1g, Inline Balance)、Glove Box Dew Point Sensor(−50℃↓)、Heat Sealer温度·压力·时间曲线。管理周期: Every Cell全数。异常处理: Leak检出→加强Sealing条件(温度↑·时间↑)、注液不足→Syringe Calibration重做。 | [6,8,9] | process_step | Electrolyte & Seal Control |
| Formation profile需包含capacity、resistance、voltage curve与abnormal channel数据。测量方法: Battery Cycler(32~512ch, CC/CV控制, 电压±1mV, 电流±0.05%)、dQ/dV分析。管理周期: Every Channel全数Cycle数据保存(1~3 Cycles)。异常处理: Abnormal Channel(电压Drop/Spike)→该Channel Cell Scrap、调整Formation Profile(Current·Cut-off Voltage优化)。 | [7,9] | process_step | Formation Data |
| Aging与Grading结果应作为决定电芯等级和模组投入可否的质量Gate。测量方法: Hioki/Keysight Meter(IR AC 1kHz)、Multimeter(OCV ±1mV)、Hi-Pot Tester(绝缘500~1,500V)。管理周期: Every Cell全数(1~7天Aging连续监控)。异常处理: Grade不良→Cell报废或降Bin、重新审查Grading标准。 | [8,9,10] | process_step | Grading Gate |
| 干法电极、高速R2R等新工艺需以独立recipe version和实验批次履历管理。测量方法: Dry Electrode: Powder Feeder Rate·Press Force·Temperature Profile独立Data Set。管理周期: Experimental Lot Only，与量产工序分离管理。异常处理: 基于Pilot Line数据推导量产Recipe参数、Recipe Version管控。 | [1,2,3] | industry | Process Innovation Readiness |

## D04.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Electrode | batch | Slurry Batch Loop |  | material_lot_id, slurry_batch_id, recipe_id, mixing_equipment_id |
| 2 | Electrode | process | Coating Roll Loop |  | electrode_roll_id, coating_weight, dryer_zone_id, defect_map_id |
| 3 | Electrode | process |  |  | electrode_roll_id, thickness_value, density_value, slitting_lot_id |
| 4 | Gate | gate |  | [2,3] | electrode_roll_id, defect_code, inspection_result, hold_code |
| 5 | Assembly | process |  |  | cell_id, electrode_roll_id, stack_id, weld_profile_id, case_lot_id |
| 6 | Assembly | process |  |  | cell_id, electrolyte_lot_id, filling_profile_id, seal_result |
| 7 | Formation | process | Formation Channel Loop |  | cell_id, formation_channel_id, formation_profile_id, capacity_value |
| 8 | Aging | process |  |  | cell_id, aging_lot_id, ocv_value, leak_result, gas_result |
| 9 | Gate | gate |  | [7,8] | cell_id, capacity_value, resistance_value, safety_result, cell_grade |
| 10 | Final | gate |  | [9] | cell_id, cell_grade, barcode_id, shipment_lot_id |

**step_expression 연결 설명(ko)**: Slurry Preparation(1, Slurry Batch Loop)에서 batch 단위로 혼합된 Slurry가 Coating(2, Coating Roll Loop)에서 전극 Roll로 변환되고, Calendering/Slitting(3)을 거친 후 Electrode Inspection Gate(4)에서 1차 검증된다. 통과한 전극 Roll은 Cell Assembly(5)에서 Cell ID와 Genealogy 연결 후 전해액 주입(6)으로 이어진다. Formation(7, Formation Channel Loop)에서 셀 전기적 특성이 형성된 후 Aging(8)을 거쳐 Grading Gate(9)에서 최종 등급 판정. Final(10)에서 출하 정보 확정. electrod_roll_id가 초반 공정(1~4)의 Primary Key이며, step4 이후 cell_id로 전환되어 step9의 cell_grade 및 step10의 shipment_lot_id까지 연쇄 추적.

## D04.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Electrode | batch | Slurry Batch Loop |  | material_lot_id, slurry_batch_id, recipe_id, mixing_equipment_id |
| 2 | Electrode | process | Coating Roll Loop |  | electrode_roll_id, coating_weight, dryer_zone_id, defect_map_id |
| 3 | Electrode | process |  |  | electrode_roll_id, thickness_value, density_value, slitting_lot_id |
| 4 | Gate | gate |  | [2,3] | electrode_roll_id, defect_code, inspection_result, hold_code |
| 5 | Assembly | process |  |  | cell_id, electrode_roll_id, stack_id, weld_profile_id, case_lot_id |
| 6 | Assembly | process |  |  | cell_id, electrolyte_lot_id, filling_profile_id, seal_result |
| 7 | Formation | process | Formation Channel Loop |  | cell_id, formation_channel_id, formation_profile_id, capacity_value |
| 8 | Aging | process |  |  | cell_id, aging_lot_id, ocv_value, leak_result, gas_result |
| 9 | Gate | gate |  | [7,8] | cell_id, capacity_value, resistance_value, safety_result, cell_grade |
| 10 | Final | gate |  | [9] | cell_id, cell_grade, barcode_id, shipment_lot_id |

**step_expression连接说明(zh)**: Slurry Preparation(1, Slurry Batch Loop)以batch为单位混合的Slurry经Coating(2, Coating Roll Loop)转为电极Roll，Calendering/Slitting(3)后在Electrode Inspection Gate(4)首次验证。通过后的电极Roll在Cell Assembly(5)中与Cell ID建立Genealogy连接，进入注液(6)。Formation(7, Formation Channel Loop)形成电芯电性特性，Aging(8)后在Grading Gate(9)最终定级，Final(10)确定出货信息。electrode_roll_id为前段(1~4)主键，step4后转为cell_id，连接至step9的cell_grade和step10的shipment_lot_id的连锁追溯。

## D04.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 1 | 1 | 원재료 계량 |
| 1 | 2 | Slurry 혼합 |
| 1 | 3 | 점도·고형분 검사 |
| 2 | 1 | Slot-die coating |
| 2 | 2 | 건조 구간 통과 |
| 2 | 3 | 코팅 중량 측정 |
| 7 | 1 | 초기 충전 |
| 7 | 2 | 휴지 |
| 7 | 3 | 방전·용량 측정 |

## D04.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 1 | 1 | 原材料称量 |
| 1 | 2 | Slurry混合 |
| 1 | 3 | 粘度与固含量检查 |
| 2 | 1 | Slot-die coating |
| 2 | 2 | 通过干燥区 |
| 2 | 3 | 涂布重量测量 |
| 7 | 1 | 初始充电 |
| 7 | 2 | 静置 |
| 7 | 3 | 放电与容量测量 |

```yaml
data_capture_points:
  - material_lot_id
  - slurry_batch_id
  - recipe_id
  - mixing_equipment_id
  - electrode_roll_id
  - coating_weight
  - dryer_zone_id
  - defect_map_id
  - thickness_value
  - density_value
  - slitting_lot_id
  - defect_code
  - inspection_result
  - hold_code
  - cell_id
  - stack_id
  - weld_profile_id
  - case_lot_id
  - electrolyte_lot_id
  - filling_profile_id
  - seal_result
  - formation_channel_id
  - formation_profile_id
  - capacity_value
  - aging_lot_id
  - ocv_value
  - leak_result
  - gas_result
  - resistance_value
  - safety_result
  - cell_grade
  - barcode_id
  - shipment_lot_id
```

---

# D05 `battery_module_pack` — 배터리 모듈·팩 / 电池模组与PACK

```yaml
code: D05
slug: battery_module_pack
label_ko: 배터리 모듈·팩
label_zh: 电池模组与PACK
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: assembly_line_v1
expression_tier: pack_trace_v1
```

## D05.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Cell Receiving / Sorting | 입고 셀의 barcode(QR/DataMatrix), grade(A/B/C, Bin Code), OCV(3.0~4.2V, ±1mV), IR(AC 1kHz, 10~50mΩ), Capacity(±3%)를 확인하고 Grade·Bin Code별로 자동 선별한다. Cell Sorter(Inline Tester + Pick&Place Robot, Cycle Time <1s/cell). 입고 Inspection Report 자동 생성. 대표 제품: EV Module(4~12셀/Module), ESS Pack(100~500셀/Pack), Battery Pack(400~800V). |
| 2 | Cell Matching / Kitting | 모듈 조립을 위한 셀 조합(OCV·IR·Capacity Deviation <1~3% 이내 매칭), Lot Kitting, Position Mapping(Cell→Slot 위치 Matrix, Module XY 좌표 매핑)을 수행한다. Cell Matching Algorithm(Clustering·Sorting 기반, 최적 조합 도출), Kitting Tray 단위 셀 배치 Mapping 데이터 생성. |
| 3 | Cell Cleaning / Insulation | 셀 표면 세정(IPA/DI Water, Air Knife 건조), 절연필름(Myar/PI Tape, 25~100μm, Roll Laminator 또는 Hand Lay-up), Spacer(Compression Pad, Silicone/PE Foam), Adhesive(구조용 Adhesive/Silicone, 0.1~0.5mm, Dispenser 도포) 조건을 관리한다. |
| 4 | Module Assembly | 셀 Stacking(압축 Fixture, Compression Force 1~5kN, Cell-to-Cell Gap <0.5mm), End Plate·Side Plate 조립, Module Housing(Aluminum Extrusion, Bolt Torque 5~20Nm, Torque Wrench/Wrench Driver ±3%) 조립을 수행한다. Module ID 생성 및 Cell→Module Serial Genealogy 확정. |
| 5 | Busbar Welding Gate | Laser Welding(YAG/Fiber Laser, 500~2,000W, Spot/Seam, Pulse Width 1~10ms, Frequency 10~100Hz, Welding Depth 0.5~2mm) 또는 Ultrasonic Welding(20~40kHz, 진폭 20~50μm). Weld Quality 검사(CCD Vision Weld Image, Splash·Crack·Pull Test 50~200N). Gate — Welding 불량 Module이 다음 단계 진입 차단. |
| 6 | BMS / Harness Assembly | BMS(Battery Management System PCB, Cell Voltage Sensing Line ±1mV, Temperature NTC Sensor, Current Sensor Hall/Shunt), Harness(전압 센싱 케이블·전력 케이블, Connector Lock Check), ECU CAN Bus 통신 케이블을 조립하고 genealogy를 연결한다. BMS Firmware Version(Flashing), Module Serial과 BMS Serial Mapping. |
| 7 | Module Test Gate | 전압(Total Voltage ±0.5%, Cell Voltage ±1mV), 저항(Module IR, AC 1kHz), 절연(Hi-Pot 1,000~2,500V, Leakage <1mA), 통신(CAN Bus, 각 Cell Voltage Read/Write 확인), Leak(Module 내부, Pressure Decay/He Leak <10⁻⁵mbar·L/s), Thermal Sensor(NTC, 25℃ Resistance ±1%) 검사. Gate — Module Test 불량이 Pack 조립 진입 차단. |
| 8 | Pack Assembly | Module(Module→Pack Tray 조립, Bolting Torque 10~30Nm), Cooling Plate(Water/Glycol Channel, Coolant Leak Test 0.1~0.3MPa, 1~5min, Pressure Drop <5kPa), Enclosure(Al/Cover, IP67 Sealing Gasket, Bolt Torque), HV Component(Busbar·Relay·Fuse·Manual Service Disconnect)를 조립한다. Pack Serial 생성 및 Module→Pack Genealogy 연결. |
| 9 | EOL / Safety Test Gate | Pack EOL(End-of-Line: Full Charge/Discharge Cycle, Capacity Verification, Energy Efficiency), Insulation(Hi-Pot 1,500~3,000V, Leakage <1mA), Leak(IP67, 30kPa 5min), Charge/Discharge(CC/CV, 0.2~1C, 온도 25℃±5℃, 전압 범위), BMS 통신(Bootloader·CAN·Firmware Version 정합성) 검사. Gate — Pack Test 불량이 출하 진입 차단. |
| 10 | Final Packing / Shipment | Pack Serial(UID Laser Mark), SW Version(BMS ECU Firmware Version Tag), 고객 Spec(고객별 Acceptance Criteria), 출하 정보(Weight·Dimension·Pallet ID·Shipment Lot·Certification Doc) 확정. EU Battery Passport 데이터 패키지(셀→모듈→Pack 전 구간 Carbon Footprint·재활용 정보·공급망 이력) 최종 구성. |

## D05.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 电芯接收 / 分选 | 确认来料电芯barcode(QR/DataMatrix)、grade(A/B/C, Bin Code)、OCV(3.0~4.2V, ±1mV)、IR(AC 1kHz, 10~50mΩ)、Capacity(±3%)，按Grade·Bin Code自动分选。Cell Sorter(Inline Tester + Pick&Place Robot, Cycle Time <1s/cell)。自动生成来料检查报告。代表产品: EV Module(4~12cell/Module)、ESS Pack(100~500cell/Pack)、Battery Pack(400~800V)。 |
| 2 | 电芯配组 / Kitting | 执行模组组装用电芯配组(OCV·IR·Capacity偏差<1~3%内匹配)、Lot Kitting、位置Mapping(Cell→Slot位置Matrix, Module XY坐标映射)。Cell Matching Algorithm(Clustering·Sorting优化组合)、Kitting Tray级Cell配置Mapping数据生成。 |
| 3 | 电芯清洗 / 绝缘 | 管理电芯表面清洗(IPA/DI Water, Air Knife干燥)、绝缘膜(Myar/PI Tape, 25~100μm, Roll Laminator或Hand Lay-up)、Spacer(Compression Pad, Silicone/PE Foam)、Adhesive(结构Adhesive/Silicone, 0.1~0.5mm, Dispenser涂布)条件。 |
| 4 | 模组组装 | 电芯Stacking(压缩Fixture, Compression Force 1~5kN, Cell-to-Cell Gap <0.5mm)、End Plate·Side Plate组装、Module Housing(Aluminum Extrusion, Bolt Torque 5~20Nm, Torque Wrench ±3%)组装。生成Module ID并确认Cell→Module Serial Genealogy。 |
| 5 | Busbar焊接Gate | Laser Welding(YAG/Fiber Laser, 500~2,000W, Spot/Seam, Pulse Width 1~10ms, Frequency 10~100Hz, 熔深0.5~2mm)或Ultrasonic Welding(20~40kHz, 振幅20~50μm)。Weld Quality检查(CCD Vision焊点图像, Splash·Crack·Pull Test 50~200N)。Gate — 焊接不良Module阻止进入下一阶段。 |
| 6 | BMS / 线束组装 | 组装BMS(Battery Management System PCB, Cell电压传感±1mV, 温度NTC Sensor, Current Sensor Hall/Shunt)、Harness(电压传感线·电力线缆, Connector Lock Check)、ECU CAN Bus通信线缆并连接genealogy。BMS Firmware Version(Flashing)、Module Serial与BMS Serial Mapping。 |
| 7 | 模组测试Gate | 检查电压(Total ±0.5%, Cell ±1mV)、阻抗(Module IR, AC 1kHz)、绝缘(Hi-Pot 1,000~2,500V, Leakage <1mA)、通信(CAN Bus, 各Cell Voltage读写确认)、Leak(Module内部, Pressure Decay/He Leak <10⁻⁵mbar·L/s)、温度传感器(NTC, 25℃ Resistance ±1%)。Gate — Module Test不良阻止进入Pack组装。 |
| 8 | PACK组装 | 组装Module(Module→Pack Tray组装, Bolting Torque 10~30Nm)、Cooling Plate(Water/Glycol通道, Coolant Leak Test 0.1~0.3MPa, 1~5min, 压降<5kPa)、Enclosure(Al/Cover, IP67密封垫, Bolt Torque)、HV Component(Busbar·Relay·Fuse·Manual Service Disconnect)。生成Pack Serial并连接Module→Pack Genealogy。 |
| 9 | EOL / 安全测试Gate | Pack EOL(Full Charge/Discharge Cycle, Capacity验证, Energy Efficiency)、绝缘(Hi-Pot 1,500~3,000V, Leakage <1mA)、Leak(IP67, 30kPa 5min)、充放电(CC/CV, 0.2~1C, 温度25℃±5℃)、BMS通信(Bootloader·CAN·Firmware Version一致性)检查。Gate — Pack Test不良阻止出货。 |
| 10 | 最终包装 / 出货 | 确认Pack Serial(UID Laser Mark)、SW Version(BMS ECU Firmware Version Tag)、客户spec(OEM Acceptance Criteria)、出货信息(Weight·Dimension·Pallet ID·Shipment Lot·Certification Doc)。EU Battery Passport数据包(从Cell→Module→Pack全程Carbon Footprint·回收信息·供应链履历)最终构成。 |

## D05.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| Cell barcode, grade, OCV, IR, capacity가 module/pack serial로 상향 genealogy되어야 한다. 측정: Barcode Scanner(Cell ID, Module ID, Pack ID 각 단계 Mapping 스캔). 주기: Every Cell/Module/Pack 전수. 이상 시: Pack EOL 불량 발생 시 Pack→Module→Cell 순 소급 추적, Cell Grade 재확인 후 재조합. | [1,2,4,8,10] | process_step | Cell-to-Pack Genealogy |
| Cell matching은 위치별 mapping과 balancing 기준을 남겨 불량 셀 역추적이 가능해야 한다. 측정: Cell Matching System(OCV·IR·Capacity 통계, K-Means/Clustering), Position Map DB(Cell XY 위치 Matrix). 주기: Every Module 배치. 이상 시: 특정 Position 불량 Cell 검출 시 동일 Position 사용 Module 전수 Hold→Cell 교체, Matching Algorithm 재검토. | [2,7,9] | process_step | Matching & Position Map |
| Busbar welding은 설비 recipe, power, speed, weld image, pull test 결과와 연결되어야 한다. 측정: Laser/Ultrasonic Welder Power Monitor(W·Amplitude), CCD Weld Image(Width·Depth·Splash), Pull Tester(50~200N). 주기: Every Weld Point 전수 + Sampling Pull Test. 이상 시: Weld Image NG → Welding Parameter 조정(출력↑·속도↓), 동일 Recipe Lot 전수 Weld Image 재검사. | [5,7] | process_step | Welding Quality Gate |
| BMS·sensor·harness 부품 lot과 firmware/SW version이 pack serial에 연결되어야 한다. 측정: BMS Serial Scanner, Firmware Version Check(Bootloader Flashing Log), Harness Continuity Tester. 주기: Every Pack. 이상 시: BMS 미통신 → Flashing 재수행·Harness 재조립, SW Version Mismatch → Firmware Update. | [6,9,10] | process_step | BMS & Software Trace |
| Pack Assembly는 torque, leak, insulation, cooling path 검사 결과를 포함해야 한다. 측정: Torque Wrench Driver(±3%, 각 Bolt Torque 기록), Pressure Decay Tester(Coolant Channel 0.1~0.3MPa), Hi-Pot Tester(절연 1,500~3,000V). 주기: Every Pack 전수. 이상 시: Torque NG → Bolt 재조임/재조립, Leak 검출 → Sealing Gasket 교체 후 재시험, Insulation 저하 → HV Component 분리 점검. | [8,9] | process_step | Pack Safety Control |
| EOL 결과는 고객 spec, safety 기준, rework 이력과 함께 관리해야 한다. 측정: Battery Cycler Pack Level(Full CC/CV Cycle, 0.2~1C, Capacity·Efficiency), Insulation·Leak·BMS 통신 통합 Test. 주기: Every Pack 전수. 이상 시: Capacity 미달 → Cell 재매칭·Module 재조립 후 재시험, Safety 불합 → Pack Scrap/부분 재조립. | [9,10] | process_step | EOL Release Gate |
| 고전압 제품은 작업자 자격, 안전 interlock, 시험구역 접근권한 관리가 필요하다. 측정: 작업자 인증 카드 RFID 스캔, Interlock System(시험구역 Door Sensor, Emergency Stop, Light Curtain) 상태 자동 Logging. 주기: Every 작업 시작 시 + Real-time 안전 시스템 모니터링. 이상 시: Interlock 해제 시 라인 자동 정지, 인증 미달 작업자 접근 차단. | [8,9] | industry | HV Safety Governance |

## D05.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| Cell barcode、grade、OCV、IR、capacity必须向module/pack serial上层追溯。测量方法: Barcode Scanner(Cell ID, Module ID, Pack ID各阶段Mapping扫描)。管理周期: Every Cell/Module/Pack全数。异常处理: Pack EOL不良时按Pack→Module→Cell顺序反向追溯，Cell Grade确认后重组。 | [1,2,4,8,10] | process_step | Cell-to-Pack Genealogy |
| Cell matching需保留位置mapping与balancing标准，以支持不良电芯反查。测量方法: Cell Matching System(OCV·IR·Capacity统计, K-Means/Clustering)、Position Map DB(Cell XY位置Matrix)。管理周期: Every Module批次。异常处理: 特定Position不良Cell时，同Position Module全数Hold→Cell更换，复查Matching Algorithm。 | [2,7,9] | process_step | Matching & Position Map |
| Busbar welding需连接设备recipe、power、speed、weld image与pull test结果。测量方法: Laser/Ultrasonic Welder Power Monitor(W·Amplitude)、CCD Weld Image(Width·Depth·Splash)、Pull Tester(50~200N)。管理周期: Every Weld Point全数 + Sampling Pull Test。异常处理: Weld Image NG→调整参数(功率↑·速度↓)、同Recipe Lot全数Weld Image复检。 | [5,7] | process_step | Welding Quality Gate |
| BMS、sensor、harness部件批次与firmware/SW version需连接到pack serial。测量方法: BMS Serial Scanner、Firmware Version Check(Bootloader Flashing Log)、Harness Continuity Tester。管理周期: Every Pack。异常处理: BMS不通信→重烧Flashing·重装Harness、SW Version不匹配→Firmware Update。 | [6,9,10] | process_step | BMS & Software Trace |
| Pack Assembly需包含torque、leak、insulation与cooling path检查结果。测量方法: Torque Wrench Driver(±3%, 各Bolt Torque记录)、Pressure Decay Tester(Coolant通道0.1~0.3MPa)、Hi-Pot Tester(绝缘1,500~3,000V)。管理周期: Every Pack全数。异常处理: Torque NG→重新拧紧/重装、Leak检出→更换Sealing Gasket后重测、绝缘降低→分离检查HV部件。 | [8,9] | process_step | Pack Safety Control |
| EOL结果需与客户spec、安全标准、rework履历一起管理。测量方法: Battery Cycler Pack Level(Full CC/CV Cycle, 0.2~1C, Capacity·Efficiency)、绝缘·Leak·BMS通信综合Test。管理周期: Every Pack全数。异常处理: Capacity不达标→Cell重匹配·Module重装后重测、Safety不合格→Pack Scrap/部分重装。 | [9,10] | process_step | EOL Release Gate |
| 高压产品需管理作业员资质、安全interlock与测试区域访问权限。测量方法: 作业员认证卡RFID扫描、Interlock System(试验区Door Sensor, Emergency Stop, Light Curtain)状态自动Logging。管理周期: Every作业开始 + Real-time安全系统监控。异常处理: Interlock触发时线体自动停止、资质不足作业员禁止进入。 | [8,9] | industry | HV Safety Governance |

## D05.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Cell Input | gate |  | [2] | cell_id, cell_grade, ocv_value, resistance_value, capacity_value |
| 2 | Kitting | process |  |  | module_id, cell_id, position_map_id, matching_group_id |
| 3 | Prep | process |  |  | module_id, cell_id, insulation_lot_id, adhesive_lot_id |
| 4 | Module | process |  |  | module_id, fixture_id, compression_value, housing_lot_id |
| 5 | Gate | gate |  | [4] | module_id, welding_recipe_id, weld_image_id, weld_result |
| 6 | Electronics | process |  |  | module_id, bms_id, harness_lot_id, sw_version |
| 7 | Gate | gate |  | [5,6] | module_id, module_test_result, insulation_value, communication_result |
| 8 | Pack | process |  |  | pack_id, module_id, cooling_plate_lot_id, torque_result |
| 9 | Gate | gate |  | [8] | pack_id, eol_result, leak_result, safety_result, bms_result |
| 10 | Final | process |  |  | pack_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression 연결 설명(ko)**: Cell Input Gate(1)에서 입고 셀의 Grade·OCV·IR·Capacity가 검증된 후 Kitting(2)에서 Module ID별 Cell 위치 매핑 및 Cell Matching이 수행된다. Prep(3)→Module Assembly(4)를 거쳐 Busbar Welding Gate(5)에서 용접 품질 1차 검증. BMS/Harness Assembly(6) 후 Module Test Gate(7)에서 전압·절연·통신 종합 검증 후 Pack Assembly(8)로 진입. EOL Gate(9)에서 최종 안전·성능 검증 후 Final(10)에서 출하 정보 확정. cell_id→module_id→pack_id로 상향 Genealogy가 구축되며, 각 Gate에서 불량품의 단계간 전이를 차단. BMS의 sw_version이 step6에서 생성되어 step9의 bms_result와 step10의 shipment 정보까지 연계.

## D05.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Cell Input | gate |  | [2] | cell_id, cell_grade, ocv_value, resistance_value, capacity_value |
| 2 | Kitting | process |  |  | module_id, cell_id, position_map_id, matching_group_id |
| 3 | Prep | process |  |  | module_id, cell_id, insulation_lot_id, adhesive_lot_id |
| 4 | Module | process |  |  | module_id, fixture_id, compression_value, housing_lot_id |
| 5 | Gate | gate |  | [4] | module_id, welding_recipe_id, weld_image_id, weld_result |
| 6 | Electronics | process |  |  | module_id, bms_id, harness_lot_id, sw_version |
| 7 | Gate | gate |  | [5,6] | module_id, module_test_result, insulation_value, communication_result |
| 8 | Pack | process |  |  | pack_id, module_id, cooling_plate_lot_id, torque_result |
| 9 | Gate | gate |  | [8] | pack_id, eol_result, leak_result, safety_result, bms_result |
| 10 | Final | process |  |  | pack_id, final_grade, customer_spec_id, shipment_label_id |

**step_expression连接说明(zh)**: Cell Input Gate(1)验证来料Cell的Grade·OCV·IR·Capacity后，Kitting(2)进行Module ID级Cell位置映射和匹配。Prep(3)→Module Assembly(4)后Busbar Welding Gate(5)首次验证焊接质量。BMS/Harness(6)后Module Test Gate(7)综合检验电压·绝缘·通信后进入Pack Assembly(8)。EOL Gate(9)最终安全·性能验证后Final(10)确定出货信息。cell_id→module_id→pack_id向上构建Genealogy，各Gate拦截不良品跨阶段转移。BMS的sw_version从step6生成后连接至step9的bms_result和step10的出货信息。

## D05.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | Cell grade 확인 |
| 2 | 2 | 위치 mapping 생성 |
| 2 | 3 | Kitting 확정 |
| 5 | 1 | Busbar 위치 확인 |
| 5 | 2 | Laser welding |
| 5 | 3 | Weld image 검사 |
| 9 | 1 | 절연 시험 |
| 9 | 2 | Leak 시험 |
| 9 | 3 | BMS 통신 시험 |

## D05.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 电芯等级确认 |
| 2 | 2 | 位置mapping生成 |
| 2 | 3 | Kitting确认 |
| 5 | 1 | Busbar位置确认 |
| 5 | 2 | Laser welding |
| 5 | 3 | Weld image检查 |
| 9 | 1 | 绝缘测试 |
| 9 | 2 | Leak测试 |
| 9 | 3 | BMS通信测试 |

```yaml
data_capture_points:
  - cell_id
  - cell_grade
  - ocv_value
  - resistance_value
  - capacity_value
  - module_id
  - position_map_id
  - matching_group_id
  - insulation_lot_id
  - adhesive_lot_id
  - fixture_id
  - compression_value
  - housing_lot_id
  - welding_recipe_id
  - weld_image_id
  - weld_result
  - bms_id
  - harness_lot_id
  - sw_version
  - module_test_result
  - insulation_value
  - communication_result
  - pack_id
  - cooling_plate_lot_id
  - torque_result
  - eol_result
  - leak_result
  - safety_result
  - bms_result
  - final_grade
  - customer_spec_id
  - shipment_label_id
```

---

# D06 `pv_cell` — 태양광 셀 / 光伏电池片

```yaml
code: D06
slug: pv_cell
label_ko: 태양광 셀
label_zh: 光伏电池片
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: line_process_v1
expression_tier: pv_cell_trace_v1
```

## D06.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Wafer Receiving / Texturing | 실리콘 wafer(Mono/Multi-crystalline Si, P/N-Type, 182mm×182mm M10·210mm G12, 두께 150~200μm, 저항률 0.5~6Ω·cm, 9/12Busbar 적합) lot을 투입하고 Texturing(Alkaline KOH/IPA Solution 80~90℃, 3~15min, Pyramid 구조 2~8μm, 반사율 <10%) 조건을 관리한다. Laser Mark(UID, SEMI 기준)로 개별 Cell ID 부여. Inline Reflectance Spectrometer로 반사율 측정. 대표 제품: PERC Cell, TOPCon Cell, HJT(Heterojunction) Cell, Back Contact Cell. |
| 2 | Diffusion / Junction Formation | POCI₃/Liquid Dopant Source 확산(Tube Furnace, 800~950℃, 30~120min, N₂/O₂ Carrier Gas) 또는 Boron Doping(P-Type Wafer→N+ Emitter, BBr₃ 900~1,050℃)으로 PN Junction을 형성한다. Sheet Resistance 관리(80~180Ω/□, 4-Point Probe, ±5%). Inline Rs Mapping으로 전면 균일도 측정. |
| 3 | Edge Isolation / Cleaning | Edge Isolation(Laser Grooving: 355nm UV Laser, Isolation Width 20~50μm, 화학 Wet Bench: HF/HNO₃ 혼산 5~30s), 세정(SC1/SC2 표준 세정, RCA Cleaning, DI Water Rinse, IPA 건조), 표면 잔류물 관리를 수행한다. PSG(PhosphoSilicate Glass) 또는 BSG(BoroSilicate Glass) 제거 확인(FTIR or Ellipsometer). |
| 4 | Passivation / Coating | SiNx(PECVD, 250~450℃, 13.56MHz RF, 굴절률 1.9~2.1, 두께 70~90nm) Anti-Reflection Coating, AlOx(PECVD/ALD, 2~10nm, Negative Charge Density Passivation), SiOx/SiNx Stack 구조로 표면 Passivation·반사 방지막을 형성한다. Ellipsometer로 두께·굴절률 실시간 측정, Lifetime(Quasi-Steady-State Photoconductance, τ>500μs) 관리. |
| 5 | Metallization / Printing | Front/Back Electrode Silver/Aluminum Paste(Ag/Pb-Free Ag Paste, 80~90% Ag Content) Screen Printing(Stainless Steel Mesh 325~400mesh, Squeegee Hardness 70~90Shore A, Speed 100~400mm/s, Printing Pressure 50~150N), Finger Width 30~50μm, Busbar Width 0.5~1.5mm. 또는 Plating(Ni/Cu/Ag Light-Induced Plating) 방식. Print Inspection(2D/3D Vision, Finger Break·Smearing·Misalignment). |
| 6 | Firing / Annealing | IR Firing Furnace(Zone별 200~900℃, Belt Speed 3~10m/min, Total Time 30~120s)로 소성·Annealing 조건으로 Contact Resistance(1~5mΩ·cm², TLM Method)와 Electrode Quality를 안정화한다. Peak Temperature·Stay Time Profile 자동 기록. Firing 후 EL(전계발광) Quick Check. |
| 7 | Inline Inspection Gate | PL(Photoluminescence: 808nm Laser Excitation, InGaAs Camera, Lifetime·Defect Mapping), EL(Electroluminescence: 0.5~1A Forward Bias, Si CCD Camera, Crack·Break·Dark Region), 외관(Scratch·Chipping·Stain, Vision Camera), Sheet Resistance(4-Point Probe, Rs 분포), Thickness(Inline Micrometer) 검사. Gate — Cell 불량이 IV Test 이전 차단. |
| 8 | IV Test / Efficiency Bin Gate | Solar Simulator(Class AAA, Xenon Flash, 1000W/m² AM1.5G, 1 Sun, Pulse Width 10~100ms), I-V Curve 측정(Isc·Voc·FF·Pmax→Efficiency). Efficiency Bin(0.1% step, 18~24%+ TOPCon 24~26%+, HJT 24~27%) 판정. DARK IV(Shunt Resistance, Rs) 병행 검사. Temp. Correction(25℃±2℃) 자동 적용. Gate — Bin Code가 Module 투입 기준과 연결. |
| 9 | Sorting / Cell Packing | 색상(Visual Color Sorting, Bin별 Code: Blue/Dark Blue/Black, Haze), 효율(Efficiency Bin Code), 외관(Grade A/B급) 기준으로 Sorting(Inline Vision + Robot Pick&Place)하고 포장(Cell Tray·Cassette, ESD Packing, 100~500pcs/Box)한다. Cell ID별 Bin Code·Box ID Mapping. |
| 10 | Shipment to Module Line | 모듈 라인 투입을 위한 Lot 정보(Lot ID·Lot Size·Cell ID Range), Bin 정보(Bin Code·Efficiency Range·Box ID), 출하 정보를 확정한다. MES에서 Module Line 생산 계획과 Cell Lot 연계(ERP→MES→Inline RTD). |

## D06.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 硅片接收 / 制绒 | 投入硅片(Mono/Multi-crystalline Si, P/N-Type, 182mm×182mm M10·210mm G12, 厚度150~200μm, 电阻率0.5~6Ω·cm, 9/12Busbar适用)批次，管理制绒(Alkaline KOH/IPA 80~90℃, 3~15min, Pyramid结构2~8μm, 反射率<10%)条件。Laser Mark(UID, SEMI标准)赋予Cell ID。Inline反射光谱仪测量反射率。代表产品: PERC Cell, TOPCon Cell, HJT Cell, Back Contact Cell。 |
| 2 | 扩散 / 结形成 | POCI₃/Liquid Dopant扩散(Tube Furnace, 800~950℃, 30~120min, N₂/O₂ Carrier Gas)或Boron Doping(P-Type→N+ Emitter, BBr₃ 900~1,050℃)形成PN结。Sheet Resistance管理(80~180Ω/□, 4-Point Probe, ±5%)。Inline Rs Mapping全幅均匀性测量。 |
| 3 | 边缘隔离 / 清洗 | 边缘隔离(Laser Grooving: 355nm UV Laser, 宽度20~50μm, 化学Wet Bench: HF/HNO₃混酸5~30s)、清洗(SC1/SC2标准清洗, RCA清洗, DI Water Rinse, IPA干燥)、表面残留管理。去除PSG/BSG确认(FTIR或Ellipsometer)。 |
| 4 | 钝化 / 镀膜 | SiNx(PECVD, 250~450℃, 13.56MHz RF, 折射率1.9~2.1, 厚度70~90nm)减反射膜、AlOx(PECVD/ALD, 2~10nm, 负电荷密度Passivation)、SiOx/SiNx Stack结构形成表面钝化·减反射膜。Ellipsometer实时测量厚度·折射率、Lifetime(QSSPC, τ>500μs)管理。 |
| 5 | 金属化 / 印刷 | 正背电极Ag/Al Paste(Ag/无Pb Ag Paste, 80~90% Ag) Screen Printing(不锈钢网325~400mesh, Squeegee硬度70~90Shore A, Speed 100~400mm/s, 压力50~150N)、Finger宽度30~50μm、Busbar宽度0.5~1.5mm。或Plating(Ni/Cu/Ag LIP)方式。Print Inspection(2D/3D Vision, Finger Break·Smearing·Misalignment)。 |
| 6 | 烧结 / 退火 | IR烧结炉(Zone别200~900℃, Belt Speed 3~10m/min, 总时间30~120s)通过烧结·退火稳定Contact Resistance(1~5mΩ·cm², TLM法)和电极质量。Peak Temperature·Stay Time曲线自动记录。烧结后EL快速检查。 |
| 7 | Inline检查Gate | PL(808nm Laser激发, InGaAs Camera, Lifetime·Defect Mapping)、EL(0.5~1A Forward Bias, Si CCD Camera, Crack·Break·Dark Region)、外观(Scratch·Chipping·Stain, Vision Camera)、Sheet Resistance(4-Point Probe, Rs分布)、Thickness(Inline Micrometer)检查。Gate — 电池片不良被阻止进入IV测试。 |
| 8 | IV测试 / 效率Bin Gate | Solar Simulator(Class AAA, Xenon Flash, 1000W/m² AM1.5G, 1 Sun, Pulse Width 10~100ms), I-V曲线测量(Isc·Voc·FF·Pmax→Efficiency)。Efficiency Bin(0.1% step, 18~24%+ TOPCon 24~26%+, HJT 24~27%)判定。DARK IV(Shunt Resistance, Rs)并行检查。温度修正(25℃±2℃)自动应用。Gate — Bin Code直接连接Module投入标准。 |
| 9 | 分选 / 电池片包装 | 按颜色(Visual Color Sorting, Bin别Code: Blue/Dark Blue/Black, Haze)、效率(Efficiency Bin Code)、外观(Grade A/B级)Sorting(Inline Vision + Robot Pick&Place)并包装(Cell Tray·Cassette, ESD Packing, 100~500pcs/Box)。Cell ID级Bin Code·Box ID Mapping。 |
| 10 | 出货至组件线 | 确认进入组件线的Lot信息(Lot ID·Lot Size·Cell ID Range)、Bin信息(Bin Code·Efficiency Range·Box ID)、出货信息。MES中组件线生产计划与Cell Lot联动(ERP→MES→Inline RTD)。 |

## D06.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| Wafer lot에서 Cell ID, 효율 bin, module 투입 lot까지 genealogy가 유지되어야 한다. 측정: Laser Mark UID Reader(Wafer→Cell→Bin→Box 각 단계 스캔). 주기: Every Cell 전수. 이상 시: Module 출력 불량 시 Cell UID→Wafer Lot→Diffusion Recipe 순 역추적, 원인 Lot Hold. | [1,8,9,10] | process_step | Wafer-to-Cell Genealogy |
| Texturing·diffusion·passivation 조건은 효율·결함·색상 편차와 연결되어야 한다. 측정: Reflectance Spectrometer(Texturing 후 반사율 <10%), 4-Point Probe(Sheet Resistance ±5%), Ellipsometer(Passivation 두께·굴절률). 주기: Every Lot Sampling(전수 Rs Mapping) + Real-time Furnace 온도 프로파일. 이상 시: 효율 저하 Cluster → 해당 Recipe/Furnace Zone 분석, 온도·가스 유량 조정. | [1,2,4,8] | process_step | Cell Process Recipe |
| Metallization·Firing 조건은 접촉저항, finger break, 출력 저하와 연결되어야 한다. 측정: TLM(Transmission Line Method, 1~5mΩ·cm²), Vision Inspection(Finger Break 30μm↑, Smearing), EL Quick Check. 주기: Every Lot Sampling(전수 Print Vision) + Firing Profile Real-time. 이상 시: 접촉저항↑ → Firing Peak Temp 조정(5~10℃↑), Finger Break ↑ → Screen Mesh 교체 주기 단축. | [5,6,7,8] | process_step | Metallization Quality |
| PL/EL defect는 cell bin과 module 투입 제한 조건으로 사용되어야 한다. 측정: PL(InGaAs Camera, 808nm Laser, Lifetime·Dark Spot Mapping), EL(Si CCD, 0.5~1A Bias, Crack·Chip·Dark Region). 주기: Every Cell 전수 검사. 이상 시: Crack/Defect Cell Grade B 이하로 자동 분류, 동일 Wafer Lot 전수 Hold. | [7,8,10] | process_step | Defect Inspection Gate |
| IV test는 장비 calibration, 온도 보정, 고객 spec과 연결되어야 한다. 측정: Solar Simulator(Class AAA, Xenon Flash 1000W/m² AM1.5G), Reference Cell Calibration(주기 인증 교정), Temp Sensor(25℃±2℃ 보정). 주기: Every Cell 전수 + Reference Cell 주기적 Calibration. 이상 시: 측정 편차 >0.5%rel → Simulator 재교정, Temp 오차 → Temp Compensation Algorithm 조정. | [8,10] | process_step | IV Test Integrity |
| Sorting은 효율·색상·외관 기준을 동시에 반영해 module mismatch를 줄여야 한다. 측정: Vision Color Sorter(Bin별 허용 범위), EL/IV Data와 연동. 주기: Every Cell 전수. 이상 시: Module 내 Cell Power Mismatch → Sorting Bin Width 재설정, Bin 내 편차 분석 후 Algorithm Update. | [8,9,10] | process_step | Bin Matching |

## D06.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| 从wafer lot到cell ID、效率bin、组件投入批次的genealogy必须保持。测量方法: Laser Mark UID Reader(Wafer→Cell→Bin→Box各段扫描)。管理周期: Every Cell全数。异常处理: 组件输出不良时按Cell UID→Wafer Lot→Diffusion Recipe反向追溯，Hold问题Lot。 | [1,8,9,10] | process_step | Wafer-to-Cell Genealogy |
| Texturing、diffusion、passivation条件需连接到效率、缺陷与颜色偏差。测量方法: Reflectance Spectrometer(制绒后反射率<10%)、4-Point Probe(Sheet Resistance ±5%)、Ellipsometer(钝化厚度·折射率)。管理周期: Every Lot采样(全数Rs Mapping) + Real-time炉管温度曲线。异常处理: 效率下降Cluster→分析Recipe/Furnace Zone，调整温度·气体流量。 | [1,2,4,8] | process_step | Cell Process Recipe |
| Metallization与Firing条件需连接到接触电阻、finger break与输出下降。测量方法: TLM(1~5mΩ·cm²)、Vision Inspection(Finger Break 30μm↑, Smearing)、EL快速检查。管理周期: Every Lot采样(全数Print Vision) + Firing Profile实时。异常处理: 接触电阻↑→Firing Peak Temp调整(5~10℃↑)、Finger Break↑→缩短Screen Mesh更换周期。 | [5,6,7,8] | process_step | Metallization Quality |
| PL/EL defect应作为cell bin和module投入限制条件使用。测量方法: PL(InGaAs Camera, 808nm Laser, Lifetime·Dark Spot)、EL(Si CCD, 0.5~1A Bias, Crack·Chip·Dark Region)。管理周期: Every Cell全数。异常处理: 裂纹/缺陷Cell自动分入Grade B以下，同Wafer Lot全数Hold。 | [7,8,10] | process_step | Defect Inspection Gate |
| IV test需连接设备calibration、温度补偿与客户spec。测量方法: Solar Simulator(Class AAA, Xenon Flash 1000W/m² AM1.5G)、Reference Cell周期校准、Temp Sensor(25℃±2℃)。管理周期: Every Cell全数 + Reference Cell定期校准。异常处理: 测量偏差>0.5%rel→Simulator重校准、Temp偏差→调整Temp Compensation Algorithm。 | [8,10] | process_step | IV Test Integrity |
| Sorting需同时反映效率、颜色、外观标准以减少module mismatch。测量方法: Vision Color Sorter(Bin级允许范围)、联动EL/IV数据。管理周期: Every Cell全数。异常处理: Module内Cell Power Mismatch→重设Sorting Bin宽度，Bin级偏差分析后Algorithm Update。 | [8,9,10] | process_step | Bin Matching |

## D06.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Wafer Prep | process |  |  | wafer_lot_id, cell_id, recipe_id, equipment_id |
| 2 | Junction | process |  |  | cell_id, diffusion_recipe_id, sheet_resistance, furnace_id |
| 3 | Cleaning | process |  |  | cell_id, cleaning_recipe_id, equipment_id |
| 4 | Passivation | process |  |  | cell_id, coating_recipe_id, thickness_value, color_value |
| 5 | Metallization | process |  |  | cell_id, paste_lot_id, screen_id, print_result |
| 6 | Firing | process |  |  | cell_id, firing_profile_id, contact_resistance, furnace_id |
| 7 | Gate | gate |  | [1,2,4,5,6] | cell_id, el_image_id, pl_image_id, defect_code, inspection_result |
| 8 | Gate | gate |  | [7] | cell_id, iv_curve_id, efficiency_value, bin_code |
| 9 | Sorting | process |  |  | cell_id, bin_code, color_bin, box_id |
| 10 | Final | process |  |  | cell_id, wafer_lot_id, bin_code, shipment_lot_id |

**step_expression 연결 설명(ko)**: Wafer Texturing(1)→Diffusion(2)→Cleaning(3)→Passivation(4)→Metallization(5)→Firing(6)으로 이어지는 전공정을 Inline Inspection Gate(7)가 PL·EL·외관으로 종합 검증한다. Gate(7) 통과 Cell만 IV Test Gate(8)에서 Efficiency Bin이 확정되며, Sorting(9)에서 색상·외관 기준으로 분류된 후 Shipment(10)에서 Module 라인 투입 정보가 확정된다. cell_id가 전 구간 Primary Key이며, step7의 el_image_id·pl_image_id가 step8의 bin_code와 직결되어 결함→효율 등급 연쇄 분석 가능. wafer_lot_id는 step1에서 부여되어 step10까지 유지.

## D06.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Wafer Prep | process |  |  | wafer_lot_id, cell_id, recipe_id, equipment_id |
| 2 | Junction | process |  |  | cell_id, diffusion_recipe_id, sheet_resistance, furnace_id |
| 3 | Cleaning | process |  |  | cell_id, cleaning_recipe_id, equipment_id |
| 4 | Passivation | process |  |  | cell_id, coating_recipe_id, thickness_value, color_value |
| 5 | Metallization | process |  |  | cell_id, paste_lot_id, screen_id, print_result |
| 6 | Firing | process |  |  | cell_id, firing_profile_id, contact_resistance, furnace_id |
| 7 | Gate | gate |  | [1,2,4,5,6] | cell_id, el_image_id, pl_image_id, defect_code, inspection_result |
| 8 | Gate | gate |  | [7] | cell_id, iv_curve_id, efficiency_value, bin_code |
| 9 | Sorting | process |  |  | cell_id, bin_code, color_bin, box_id |
| 10 | Final | process |  |  | cell_id, wafer_lot_id, bin_code, shipment_lot_id |

**step_expression连接说明(zh)**: Wafer Texturing(1)→Diffusion(2)→Cleaning(3)→Passivation(4)→Metallization(5)→Firing(6)全流程经Inline Inspection Gate(7)以PL·EL·外观综合验证。通过Gate(7)的Cell才在IV Test Gate(8)中确定Efficiency Bin，Sorting(9)按颜色·外观分类后Shipment(10)确定组件线投入信息。cell_id全程为主键，step7的el_image_id·pl_image_id直接连接step8的bin_code，实现缺陷→效率等级连锁分析。wafer_lot_id从step1赋予并贯穿至step10。

## D06.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 5 | 1 | Front electrode printing |
| 5 | 2 | Back electrode printing |
| 5 | 3 | Print inspection |
| 8 | 1 | IV curve 측정 |
| 8 | 2 | Efficiency 계산 |
| 8 | 3 | Bin code 판정 |

## D06.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 5 | 1 | Front electrode printing |
| 5 | 2 | Back electrode printing |
| 5 | 3 | Print inspection |
| 8 | 1 | IV curve测量 |
| 8 | 2 | Efficiency计算 |
| 8 | 3 | Bin code判定 |

```yaml
data_capture_points:
  - wafer_lot_id
  - cell_id
  - recipe_id
  - equipment_id
  - diffusion_recipe_id
  - sheet_resistance
  - furnace_id
  - cleaning_recipe_id
  - coating_recipe_id
  - thickness_value
  - color_value
  - paste_lot_id
  - screen_id
  - print_result
  - firing_profile_id
  - contact_resistance
  - el_image_id
  - pl_image_id
  - defect_code
  - inspection_result
  - iv_curve_id
  - efficiency_value
  - bin_code
  - color_bin
  - box_id
  - shipment_lot_id
```

---

# D07 `pv_module` — 태양광 모듈 / 光伏组件

```yaml
code: D07
slug: pv_module
label_ko: 태양광 모듈
label_zh: 光伏组件
label_en: ""
label_ja: ""
routing: RT_LINE
preset_id: assembly_line_v1
expression_tier: pv_module_trace_v1
```

## D07.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Cell Receiving / Bin Matching | 셀 lot, 효율 Bin(18~27%+), 색상 Bin(Blue·Dark Blue·Black), 외관 등급(A/B)을 확인하고 Module 설계 Target Power(Wattage Class, 300~700W)에 맞춰 Bin Matching Algorithm으로 최적 조합 선정. Cell→String Position Mapping 생성. 대표 제품: Residential Module(400~500W), Utility-Scale Module(550~700W, Bifacial), Building-Integrated PV(BIPV). |
| 2 | Cell Cutting / Stringing | 셀 절단(Laser Scribing: IR/Green Laser, 355nm/532nm, 절단면 Etch, Cell 반절·1/3절), Tabbing(Tabbing Ribbon: Cu 0.2~0.5mm×0.1~0.3mm, Soldering: Hot Air/IR 180~250℃, Flux 사용), Stringing(자동 Stringer, 6~15cell/String, 2~6String/Module) 조건과 Cell Breakage(Inline Vision, <0.5%)를 관리한다. String ID별 Pull Test(1~3N/ribbon) Sampling. |
| 3 | Layup | Glass(Tempered, 3.2mm, Anti-Reflection Coated), EVA/POE(Encapsulant Sheet, 0.4~0.6mm, Cross-Linking Degree 관리), Cell String(Serial Connection, Ribbon Interconnection), Backsheet(TPT/PET/PVDF Multilayer, White/Transparent, 0.3~0.5mm)를 순서대로 적층(자동 Layup Robot, Alignment ±1mm). Glass→EVA→String→EVA→Backsheet Stack. |
| 4 | EL Pre-Lamination Gate | 라미네이션 전 EL 검사(Forward Bias 0.5~1A/Module, Si CCD Camera, Crack·Solder Defect·Cell Mismatch·Breakage 검출). Defect Map 생성, String별 Current Distribution 분석. Gate — Pre-EL 불량 Module이 Lamination 진입 차단(Rework 가능: String 교체). |
| 5 | Lamination | Laminator(단층/다층 방식, Vacuum 0.5~5min, 10⁻²~1mbar, Heating 130~170℃, 고무 멤브레인 압력 0.5~1.0bar, Curing 10~20min), 온도·압력·Vacuum Profile 자동 기록. EVA/POE Cross-linking Degree(DSC 시차주사열량계 Sampling, Gel Content >85%). Cooling Station(수냉, <50℃) 후 Module 출하. |
| 6 | Trimming / Framing | Edge Trimming(Router/CNC, Laminated Module 가장자리 EVA/Backsheet Trim ≤2mm), Frame Assembly(Aluminum Alloy, Corner Key, Screw/Torque 5~15Nm, Silicone Sealant 도포(Manually/Automated, Bead Width 3~5mm). Torque Wrench 자동 기록. |
| 7 | Junction Box / Curing | Junction Box(JB, TUV/IEC 인증, MC4/Compat Connector, IP68, Cabling 4mm²/6mm², Length 0.9~1.2m), Potting(Silicone/PU, Potted Encapulant, Cure 25℃ 4~24h 또는 Heat 50~80℃ 10~30min), 납땜(Hand/Auto Soldering, 300~380℃, Flux) 또는 Clamp 방식. Curing Profile 온도·시간 자동 기록. Diode(By-pass Diode, 15~20A, Reverse Voltage Check). |
| 8 | EL / IV Final Test Gate | EL Final Test(Full Module: 1~2A Forward Bias, Si CCD Camera, Microcrack·Cell Break·Dark Cell·Active Area 분석), IV Test(Class AAA Solar Simulator, Flash Test, STC: 1000W/m² AM1.5G 25℃, Isc·Voc·FF·Pmax→Power Bin ±3%), Insulation Hi-Pot(2,000~3,000V+1000V×2, Leakage <50μA), Wet Leakage(IEC 61730, 3min, 500V, Leakage <50μA). Gate — Power Bin 불일치·Safety 불합격 Module 출하 차단. |
| 9 | Labeling / Packing | Serial Label(Module UID Barcode/QR, SEMI Standard), Nameplate(Rated Power·Voltage·Current·Certification Mark·Manufacturer·Origin·Date Code), 고객 Spec(MOQ·Label Position·Pack Configuration) Label 부착. 포장(Module 간 EPE Foam/Paper Interleaf, 수직 Packing Rack·Pallet, Strapping·Stretch Wrap, 15~35Module/Pallet). |
| 10 | Shipment / Warranty Trace | 출하 Lot(Batch ID·Shipment Date·Customer Order), Pallet(Serial·Weight·Dimension Barcode), 보증 추적 정보(Module Serial→Cell ID Range→Bin Code→Material Lot→공정 조건 전수 데이터 Package) 확정. 25~30년 선형 보증 데이터베이스 등록. |

## D07.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 电池片接收 / Bin匹配 | 确认电池片批次、效率Bin(18~27%+)、颜色Bin(Blue·Dark Blue·Black)、外观等级(A/B)，按Module目标功率(Wattage Class, 300~700W)以Bin Matching Algorithm选取最优组合。生成Cell→String Position Mapping。代表产品: Residential Module(400~500W)、Utility Module(550~700W, Bifacial)、BIPV。 |
| 2 | 电池片切割 / 串焊 | 电池片切割(Laser Scribing: IR/Green Laser, 355nm/532nm, 切面Etch, 半片·1/3片)、Tabbing(Tabbing Ribbon: Cu 0.2~0.5mm×0.1~0.3mm, Soldering: Hot Air/IR 180~250℃, Flux使用)、Stringing(自动Stringer, 6~15cell/String, 2~6String/Module)条件与Cell Breakage(Inline Vision, <0.5%)管理。String ID级Pull Test(1~3N/ribbon)采样。 |
| 3 | Layup叠层 | 按顺序叠放Glass(Tempered, 3.2mm, AR Coated)、EVA/POE(Encapsulant Sheet, 0.4~0.6mm, Cross-Linking程度管理)、Cell String(串联, Ribbon Interconnection)、Backsheet(TPT/PET/PVDF多层膜, White/Transparent, 0.3~0.5mm)。自动Layup Robot, Alignment ±1mm。 |
| 4 | 层压前EL Gate | 层压前EL检查(Forward Bias 0.5~1A/Module, Si CCD Camera, Crack·Solder Defect·Cell Mismatch·Breakage检测)。生成Defect Map, String级Current Distribution分析。Gate — Pre-EL不良Module阻止进入Lamination(Rework可: 更换String)。 |
| 5 | 层压 | Laminator(单层/多层, Vacuum 0.5~5min, 10⁻²~1mbar, 加热130~170℃, 橡胶膜压力0.5~1.0bar, Curing 10~20min)，温度·压力·真空曲线自动记录。EVA/POE Cross-linking Degree(DSC采样, Gel Content>85%)。冷却(水冷, <50℃)。 |
| 6 | 修边 / 装框 | Edge Trimming(Router/CNC, 层压组件边缘EVA/Backsheet Trim≤2mm)、Frame组装(Aluminum Alloy, Corner Key, Screw/Torque 5~15Nm, Silicone Sealant涂布(自动/手动, Bead Width 3~5mm)。Torque Wrench自动记录。 |
| 7 | Junction Box / 固化 | Junction Box(TUV/IEC认证, MC4/Compat连接器, IP68, Cabling 4mm²/6mm², Length 0.9~1.2m)、Potting(Silicone/PU, 灌封胶, 固化25℃ 4~24h或加热50~80℃ 10~30min)、焊接(手动/自动Soldering, 300~380℃, Flux)或Clamp方式。固化曲线温度·时间自动记录。Diode(By-pass Diode, 15~20A, Reverse Voltage检查)。 |
| 8 | EL / IV最终测试Gate | EL最终测试(Full Module: 1~2A Forward Bias, Si CCD Camera, Microcrack·Cell Break·Dark Cell·Active Area分析)、IV测试(Class AAA Solar Simulator, Flash Test, STC: 1000W/m² AM1.5G 25℃, Isc·Voc·FF·Pmax→Power Bin ±3%)、绝缘Hi-Pot(2,000~3,000V+1000V×2, Leakage<50μA)、Wet Leak(IEC 61730, 3min, 500V, Leakage<50μA)。Gate — Power Bin不匹配·Safety不合格Module阻止出货。 |
| 9 | 贴标 / 包装 | Serial Label(Module UID Barcode/QR, SEMI标准)、Nameplate(Rated Power·Voltage·Current·Certification Mark·制造商·原产地·日期码)、客户Spec(MOQ·Label Position·Pack Configuration)标签贴附。包装(Module间EPE Foam/Paper Interleaf, 垂直Packing Rack·Pallet, Strapping·Stretch Wrap, 15~35Module/Pallet)。 |
| 10 | 出货 / 质保追溯 | 确认出货批次(Batch ID·Shipment Date·Customer Order)、Pallet(Serial·Weight·Dimension Barcode)、质保追溯信息(Module Serial→Cell ID Range→Bin Code→Material Lot→工序条件全数据Package)。注册25~30年线性质保数据库。 |

## D07.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| Cell ID·bin·위치 정보가 module serial과 string position으로 연결되어야 한다. 측정: Barcode Scanner(Cell ID→String ID→Module Serial 전수 Scanning). 주기: Every Cell→String→Module 전수 Mapping. 이상 시: Module Power Mismatch 시 Cell Position 분석, 해당 Bin 미스매치 Cell 식별 후 재조합. | [1,2,3,9,10] | process_step | Cell-to-Module Genealogy |
| Stringing 조건은 solder defect, crack, power loss와 함께 분석되어야 한다. 측정: Soldering 온도 프로파일(Thermocouple, 180~250℃), Pull Tester(1~3N/Ribbon), EL Pre/Post 비교. 주기: Every String Sampling + Real-time Soldering Temp 모니터링. 이상 시: Solder Defect 증가 → Soldering Temp·Speed 조정, Flux 적용 방식 변경. | [2,4,8] | process_step | Stringing Quality |
| Layup 자재 lot은 glass, encapsulant, backsheet, ribbon까지 module serial에 연결되어야 한다. 측정: 자재 Lot Barcode Scanner, Module BOM 생성 시 자재 Lot Mapping DB 연동. 주기: Every Module. 이상 시: Lamination 불량(Delamination·Bubble) → 자재 Lot별 Encapsulant Curing Profile 분석, Lot 교체. | [3,5,9] | process_step | Material Genealogy |
| Pre/Post EL 이미지는 crack 발생 시점과 lamination 영향 분석에 사용되어야 한다. 측정: CCD Camera(EL Image, 1~2A Forward Bias, 0.5~1M Pixel), Image Analysis(Crack·Dark Cell·Solder Defect 자동 분류). 주기: Every Module(Pre·Post EL 전수). 이상 시: Lamination 후 Crack 증가 → Lamination Vacuum·Pressure Profile 조정, Cell Handling Robot Calibration. | [4,8] | process_step | EL Defect Trace |
| Lamination profile은 bubble, delamination, cell shift, yellowing risk와 연결되어야 한다. 측정: Laminator TC(온도 Zone별 프로파일), Vacuum Gauge, Pressure Sensor, DSC(Gel Content >85% 샘플링). 주기: Every Lot Lamination Profile 저장 + 주기적 Gel Content Sampling. 이상 시: Bubble·Delamination → Vacuum Time↑, 온도↑ 조정, Gel Content 불량 → Curing Time·Temp 조정. | [5,8] | process_step | Lamination Control |
| IV power bin은 고객 spec, nameplate, warranty data와 일치해야 한다. 측정: Class AAA Solar Simulator(Flash Test, STC 조건, ±0.5% 측정 정밀도), Reference Module Calibration. 주기: Every Module 전수. 이상 시: Power Bin 미달 → Cell 재Matching·재조립 또는 Power Class 하향 조정, Nameplate 재발행. | [8,9,10] | process_step | Power Bin Release |
| Junction box와 cable 부품 lot은 안전·화재 리스크 분석을 위해 추적되어야 한다. 측정: JB Connector Pull Test(>50N), Diode Reverse Voltage Test(15~20A, Vr 정합), Potting Curing Profile 기록. 주기: Every Module 전수 + JB Lot별 Sampling. 이상 시: Diode 불량 → JB Lot 전수 교체, Potting Curing 불량 → Curing Profile 재설정·재경화. | [7,8,10] | process_step | Electrical Safety Trace |

## D07.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| Cell ID、bin与位置信息必须连接到module serial和string position。测量方法: Barcode Scanner(Cell ID→String ID→Module Serial全数扫描)。管理周期: Every Cell→String→Module全数Mapping。异常处理: Module Power Mismatch时分析Cell Position，识别Bin Mismatch Cell后重组。 | [1,2,3,9,10] | process_step | Cell-to-Module Genealogy |
| Stringing条件需与solder defect、crack、power loss一起分析。测量方法: 焊接温度曲线(TC, 180~250℃)、Pull Tester(1~3N/Ribbon)、EL Pre/Post比较。管理周期: Every String采样 + Real-time焊接温度监控。异常处理: Solder Defect增加→调整焊接温度·速度、改变Flux方式。 | [2,4,8] | process_step | Stringing Quality |
| Layup材料批次需将glass、encapsulant、backsheet、ribbon连接到module serial。测量方法: 材料Lot Barcode Scanner，Module BOM生成时材料Lot Mapping DB联动。管理周期: Every Module。异常处理: Lamination不良(分层·气泡) →材料Lot级Encapsulant Curing曲线分析，更换Lot。 | [3,5,9] | process_step | Material Genealogy |
| Pre/Post EL图像应用于分析crack发生时点与lamination影响。测量方法: CCD Camera(EL Image, 1~2A Forward Bias, 0.5~1M Pixel), Image Analysis(Crack·Dark Cell自动分类)。管理周期: Every Module(Pre·Post EL全数)。异常处理: Lamination后Crack增加→调整Lamination真空·压力曲线、Cell Handling Robot Calibration。 | [4,8] | process_step | EL Defect Trace |
| Lamination profile需连接到bubble、delamination、cell shift、yellowing risk。测量方法: Laminator TC(温度Zone曲线)、Vacuum Gauge、Pressure Sensor、DSC(Gel Content>85%采样)。管理周期: Every Lot Lamination Curve保存 + 定期Gel Content采样。异常处理: Bubble·分层→延长Vacuum Time·升温、Gel Content不良→调整Curing Time·Temp。 | [5,8] | process_step | Lamination Control |
| IV power bin必须与客户spec、nameplate、warranty data一致。测量方法: Class AAA Solar Simulator(Flash Test, STC, ±0.5%精度)、Reference Module校准。管理周期: Every Module全数。异常处理: Power Bin不达标→Cell重匹配·重装或下调Power Class、重发Nameplate。 | [8,9,10] | process_step | Power Bin Release |
| Junction box和cable部件批次需追溯以支持安全与火灾风险分析。测量方法: JB Connector Pull Test(>50N)、Diode Reverse Voltage Test(15~20A, Vr确认)、Potting固化曲线记录。管理周期: Every Module全数 + JB Lot级采样。异常处理: Diode不良→JB Lot全数更换、Potting固化不良→重设固化曲线·再固化。 | [7,8,10] | process_step | Electrical Safety Trace |

## D07.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Cell Input | gate |  | [2] | cell_id, cell_bin, color_bin, cell_grade |
| 2 | Stringing | process |  |  | module_id, cell_id, string_id, solder_profile_id, breakage_code |
| 3 | Layup | process |  |  | module_id, glass_lot_id, encapsulant_lot_id, backsheet_lot_id |
| 4 | Gate | gate |  | [2,3] | module_id, pre_el_image_id, defect_code, inspection_result |
| 5 | Lamination | process |  |  | module_id, lamination_profile_id, vacuum_profile_id, equipment_id |
| 6 | Frame | process |  |  | module_id, frame_lot_id, silicone_lot_id, torque_result |
| 7 | Junction Box | process |  |  | module_id, junction_box_lot_id, cable_lot_id, curing_profile_id |
| 8 | Gate | gate |  | [5,6,7] | module_id, post_el_image_id, iv_curve_id, power_bin, safety_result |
| 9 | Label | process |  |  | module_id, serial_label_id, nameplate_id, customer_spec_id |
| 10 | Final | process |  |  | module_id, pallet_id, shipment_lot_id, warranty_id |

**step_expression 연결 설명(ko)**: Cell Input Gate(1)에서 입고 셀의 Bin·Grade를 검증한 후 Bin별로 Kitting되어 Stringing(2)→Layup(3)으로 진행된다. Pre-EL Gate(4)에서 String Soldering·Layup 결함을 1차 검증한 통과 Module만 Lamination(5)으로 진입. Framing(6)→Junction Box(7) 후 EL/IV Final Gate(8)에서 Module 출력 Bin·안전성을 최종 검증. Labeling(9)→Shipment(10)에서 보증 추적 정보 완성. module_id가 step2부터 Primary Key, cell_id는 step1~2에서 Module→Cell 하향 Genealogy를 구성하며 step4의 pre_el_image_id와 step8의 post_el_image_id·power_bin이 비교되어 Lamination 영향 분석 가능.

## D07.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Cell Input | gate |  | [2] | cell_id, cell_bin, color_bin, cell_grade |
| 2 | Stringing | process |  |  | module_id, cell_id, string_id, solder_profile_id, breakage_code |
| 3 | Layup | process |  |  | module_id, glass_lot_id, encapsulant_lot_id, backsheet_lot_id |
| 4 | Gate | gate |  | [2,3] | module_id, pre_el_image_id, defect_code, inspection_result |
| 5 | Lamination | process |  |  | module_id, lamination_profile_id, vacuum_profile_id, equipment_id |
| 6 | Frame | process |  |  | module_id, frame_lot_id, silicone_lot_id, torque_result |
| 7 | Junction Box | process |  |  | module_id, junction_box_lot_id, cable_lot_id, curing_profile_id |
| 8 | Gate | gate |  | [5,6,7] | module_id, post_el_image_id, iv_curve_id, power_bin, safety_result |
| 9 | Label | process |  |  | module_id, serial_label_id, nameplate_id, customer_spec_id |
| 10 | Final | process |  |  | module_id, pallet_id, shipment_lot_id, warranty_id |

**step_expression连接说明(zh)**: Cell Input Gate(1)验证来料Cell的Bin·Grade后按Bin Kitting进入Stringing(2)→Layup(3)。Pre-EL Gate(4)首次验证String Soldering·Layup缺陷，通过Module才进入Lamination(5)。Framing(6)→Junction Box(7)后在EL/IV Final Gate(8)最终验证Module输出Bin·安全性。Labeling(9)→Shipment(10)完成质保追溯信息。module_id从step2起为主键，cell_id在step1~2构成Module→Cell向下Genealogy，step4的pre_el_image_id与step8的post_el_image_id·power_bin对比可分析Lamination影响。

## D07.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | Cell cutting |
| 2 | 2 | Tabbing |
| 2 | 3 | String soldering |
| 5 | 1 | 진공 형성 |
| 5 | 2 | 가열·압착 |
| 5 | 3 | 냉각 |
| 8 | 1 | EL 검사 |
| 8 | 2 | IV 검사 |
| 8 | 3 | Power bin 판정 |

## D07.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | Cell cutting |
| 2 | 2 | Tabbing |
| 2 | 3 | String soldering |
| 5 | 1 | 真空形成 |
| 5 | 2 | 加热压合 |
| 5 | 3 | 冷却 |
| 8 | 1 | EL检查 |
| 8 | 2 | IV检查 |
| 8 | 3 | Power bin判定 |

```yaml
data_capture_points:
  - cell_id
  - cell_bin
  - color_bin
  - cell_grade
  - module_id
  - string_id
  - solder_profile_id
  - breakage_code
  - glass_lot_id
  - encapsulant_lot_id
  - backsheet_lot_id
  - pre_el_image_id
  - defect_code
  - inspection_result
  - lamination_profile_id
  - vacuum_profile_id
  - equipment_id
  - frame_lot_id
  - silicone_lot_id
  - torque_result
  - junction_box_lot_id
  - cable_lot_id
  - curing_profile_id
  - post_el_image_id
  - iv_curve_id
  - power_bin
  - safety_result
  - serial_label_id
  - nameplate_id
  - customer_spec_id
  - pallet_id
  - shipment_lot_id
  - warranty_id
```

---

# D08 `functional_film_material` — 기능성 필름·신에너지 소재 / 功能膜与新能源材料

```yaml
code: D08
slug: functional_film_material
label_ko: 기능성 필름·신에너지 소재
label_zh: 功能膜与新能源材料
label_en: ""
label_ja: ""
routing: RT_ROLL
preset_id: roll_to_roll_v1
expression_tier: r2r_trace_v1
```

## D08.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Raw Material / Resin Preparation | 수지(PE·PP·PET·PI·PEN·PVDF, MFR/Melt Flow Index 1~50g/10min), Solvent(Toluene·MEK·THF·NMP), Additive(Anti-block·UV Stabilizer·Slip Agent·Antistatic, 0.1~5wt%), Active Material(Coating용 Conductive/Barrier/Primer 기능성 분말) Lot을 준비한다. Silo·Tank·Drum 단위 Lot ID 관리. 대표 제품: 편광판 보호필름, Battery Separator(PE/PP Microporous, 12~25μm), Optical Clear Film(OCA), PV Backsheet, Barrier Film(Moisture·Oxygen WVTR <10⁻³g/m²·day). |
| 2 | Mixing / Dispersion | 혼합·분산(High-Speed Disperser 1,000~5,000rpm + Bead Mill 0.5~2mm Zr Beads, 분산 시간 30~120min), 점도(100~10,000cP, Brookfield/Rheometer), 입도(D50 0.1~10μm, Laser Diffraction), 고형분(10~70%, Halogen Moisture Analyzer)을 관리한다. Mixing Batch ID별 Recipe·시간·온도(25~80℃) 조건 자동 저장. |
| 3 | Coating / Casting | Roll-to-Roll Coating(Slot-Die: 10~500μm Wet Thickness, Coating Width 500~2,500mm, Line Speed 5~100m/min), Micro Gravure(1~50μm), Extrusion Casting(Melt Extrusion, 200~300℃, T-Die), Knife-over-Roll 방식. Coating Gap(±1μm), Pump Flow Rate(±0.5%), Web Tension(50~500N/m) 관리. Coating Thickness Inline β-ray/IR Gauge 실시간 Feedback. |
| 4 | Drying / Curing | 건조(Flotation/Air Float Oven, Zone별 50~180℃, 5~60m 길이, 풍속 1~15m/s, Multi-zone, 최대 12Zone), UV Curing(UV Lamp: Hg/UV-LED 365~395nm, Intensity 500~5,000mW/cm², Dose 100~1,000mJ/cm²), Electron Beam Curing(150~300kV, 10~50kGy). Web Tension(50~500N/m) Zone별 관리, Solvent 잔류량(Inline GC/MS 또는 NIR, <1,000ppm Target) 관리. |
| 5 | Lamination / Surface Treatment | Lamination(열/건식/습식 라미네이션: Nip Roll 압력 0.5~5kgf/cm, 온도 RT~150℃, Speed 5~50m/min), Plasma/Corona Treatment(38~50kHz, 500~2,500W, Dyne Level 38~56mN/m), Primer Coating(0.1~5μm, Roll/Gravure Coating), Surface Energy 측정(Dyne Test Pen, Contact Angle Meter). |
| 6 | Inline Inspection Gate | 두께(Inline β-ray/IR Gauge, ±0.1~1μm), Pinhole(Pinhole Detector: High Voltage Spark/IR Laser, >10μm), Scratch·Particle(Vision Camera, 20~50μm↑, Line Scan), Streak·Coating Defect(2D Vision, Periodic Pattern). Defect Map을 Mother Roll ID별 좌표·유형·크기 저장. Gate — 결함 Roll이 Slitting·출하 진입 차단. |
| 7 | Slitting / Rewinding | Slitter(Scoring/Knife Shear/Razor Slitting, 폭 10~2,000mm, 정밀도 ±0.1~0.5mm), Rewinding Tension Profile(Taper Tension, 50~500N/m → 30~300N/m End), Edge Inspection(Edge Crack·Wave·Burr, Vision Camera), Splice 이력(Splice Tape, Count·Position·Type) 관리. Mother Roll→Slit Roll 분할 Genealogy 자동 생성. |
| 8 | Aging / Stabilization | Aging Chamber(항온 23~60℃, 습도 30~80%RH, 1~7일), 소재 안정화(수축률 <1%, Optical Haze·Transmittance·Color 안정화), 성능 변화(Adhesion·Barrier·Optical Property 시간 경과 측정) 데이터를 관리한다. Slit Roll ID별 Aging 기간·조건·성능 시험 결과 저장. |
| 9 | Final Test / Grade Gate | 물성(인장강도·신율·Tear·Tensile Modulus, ASTM/DIN Method), 광학(Transmittance·Haze·Color·Gloss, UV-Vis Spectrophotometer), 전기(Volume/Surface Resistivity, Dielectric Constant, 4-Point Probe/Electrode Method), Barrier(Water Vapor/Oxygen Transmission Rate, Mocon Method: WVTR <10⁻²~10⁻⁶g/m²·day, OTR <10⁻¹~10⁻⁵cc/m²·day), Adhesion(Peel Test 180°/90°, 0.1~10N/cm) 검사로 Grade(A/S+~C) 판정. Gate — Grade 미달 Roll이 출하 진입 차단. |
| 10 | Packing / Shipment | Roll ID(UID Barcode), Box(Box·Pallet Label), 고객 Spec(Width·Length·Grade·Surface 특성·Winding 방향), 출하 정보(COA·TDS·MSDS·Shipment Lot·Certificate of Compliance) 확정. Roll→Box→Pallet→Shipment Lot 전수 Mapping. |

## D08.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原材料 / 树脂准备 | 准备树脂(PE·PP·PET·PI·PEN·PVDF, MFR 1~50g/10min)、溶剂(Toluene·MEK·THF·NMP)、添加剂(Anti-block·UV Stabilizer·Slip Agent·Antistatic, 0.1~5wt%)、活性材料(涂布用导电/阻隔/底涂功能性粉末)批次。Silo·Tank·Drum级Lot ID管理。代表产品: 偏光片保护膜、电池隔膜(PE/PP微孔膜, 12~25μm)、OCA光学胶、PV背板、阻隔膜(WVTR<10⁻³g/m²·day)。 |
| 2 | 混合 / 分散 | 管理混合·分散(High-Speed Disperser 1,000~5,000rpm + Bead Mill 0.5~2mm Zr Beads, 分散时间30~120min)、粘度(100~10,000cP, Brookfield/Rheometer)、粒径(D50 0.1~10μm, Laser Diffraction)、固含量(10~70%, Halogen Moisture Analyzer)。按Mixing Batch ID自动保存Recipe·时间·温度(25~80℃)条件。 |
| 3 | 涂布 / Casting | Roll-to-Roll涂布(Slot-Die: 10~500μm Wet Thickness, 宽度500~2,500mm, 线速度5~100m/min)、Micro Gravure(1~50μm)、挤出Casting(Melt Extrusion, 200~300℃, T-Die)、Knife-over-Roll方式。涂布Gap(±1μm)、泵流量(±0.5%)、Web张力(50~500N/m)管理。涂布厚度Inline β-ray/IR Gauge实时反馈。 |
| 4 | 干燥 / 固化 | 干燥(Flotation/Air Float Oven, Zone别50~180℃, 5~60m长, 风速1~15m/s, 多Zone最多12Zone)、UV固化(UV Lamp: Hg/UV-LED 365~395nm, 强度500~5,000mW/cm², 剂量100~1,000mJ/cm²)、EB固化(150~300kV, 10~50kGy)。Web张力(50~500N/m) Zone级管理、溶剂残留量(Inline GC/MS或NIR, <1,000ppm Target)管理。 |
| 5 | 贴合 / 表面处理 | Lamination(热/干/湿式: Nip Roll压力0.5~5kgf/cm, 温度RT~150℃, 速度5~50m/min)、Plasma/Corona处理(38~50kHz, 500~2,500W, Dyne Level 38~56mN/m)、Primer涂布(0.1~5μm, Roll/Gravure Coating)、表面能测量(Dyne Test Pen, Contact Angle Meter)。 |
| 6 | Inline检查Gate | 厚度(Inline β-ray/IR Gauge, ±0.1~1μm)、Pinhole(Pinhole Detector: 高压Spark/IR Laser, >10μm)、Scratch·Particle(Vision Camera, 20~50μm↑, Line Scan)、Streak·Coating Defect(2D Vision, Periodic Pattern)。缺陷地图按Mother Roll ID保存坐标·类型·尺寸。Gate — 缺陷Roll被阻止进入Slitting和出货。 |
| 7 | 分切 / 复卷 | Slitter(Scoring/Knife Shear/Razor Slitting, 宽度10~2,000mm, 精度±0.1~0.5mm)、复卷Tension Profile(Taper Tension, 50~500N/m→30~300N/m末端)、Edge Inspection(Edge Crack·Wave·Burr, Vision Camera)、Splice履历(Splice Tape, Count·Position·Type)管理。Mother Roll→Slit Roll分割Genealogy自动生成。 |
| 8 | Aging / 稳定化 | Aging Chamber(恒温23~60℃, 湿度30~80%RH, 1~7天)、材料稳定化(收缩率<1%, 光学Haze·Transmittance·Color稳定)、性能变化(Adhesion·Barrier·Optical Property时间推移测量)数据管理。按Slit Roll ID保存Aging期间·条件·性能测试结果。 |
| 9 | 最终测试 / 分级Gate | 物性(拉伸强度·延伸率·撕裂·Tensile Modulus, ASTM/DIN方法)、光学(Transmittance·Haze·Color·Gloss, UV-Vis Spectrophotometer)、电性(Volume/Surface Resistivity, Dielectric Constant, 4-Point Probe/Electrode Method)、阻隔(WVTR<10⁻²~10⁻⁶g/m²·day, OTR<10⁻¹~10⁻⁵cc/m²·day, Mocon Method)、粘接(Peel Test 180°/90°, 0.1~10N/cm)检查判定Grade(A/S+~C)。Gate — Grade不达标Roll被阻止出货。 |
| 10 | 包装 / 出货 | 确认Roll ID(UID Barcode)、Box(Box·Pallet Label)、客户spec(Width·Length·Grade·Surface特性·Winding方向)、出货信息(COA·TDS·MSDS·Shipment Lot·Certificate of Compliance)。Roll→Box→Pallet→Shipment Lot全数Mapping。 |

## D08.3 control_points_detail_ko

| text | step_refs | scope | category |
|---|---|---|---|
| 원재료 lot, 혼합 batch, mother roll, slit roll의 genealogy가 끊기지 않아야 한다. 측정: Barcode Scanner(재료 Lot→Mixing Batch ID→Mother Roll ID→Slit Roll ID 각 단계 전수 스캔). 주기: Every Batch/Roll 전수. 이상 시: 최종 Grade 불량 시 Slit Roll→Mother Roll→Mixing Batch→재료 Lot 순 역추적, 원인 Lot Hold. | [1,2,3,7,10] | process_step | Roll Genealogy |
| 혼합·분산 조건은 점도, 입도, 고형분, coating defect와 연결되어야 한다. 측정: Brookfield/Rheometer(점도, 100~10,000cP), Laser Diffraction(입도 D50 0.1~10μm), Halogen Analyzer(고형분 10~70%). 주기: Every Batch 사전 검사. 이상 시: 점도 편차 → Mixing Recipe 조정(Speed·Time), 입도 이상 → Bead Mill Media 교체, Coating Streak 발생 시 Batch 폐기. | [2,3,6] | process_step | Dispersion Quality |
| R2R coating 조건은 두께 편차, streak, pinhole, particle defect와 연결되어야 한다. 측정: Inline β-ray/IR Gauge(두께 ±0.1~1μm), Pinhole Detector(>10μm, High Voltage Spark), Vision Camera(Streak·Particle 20~50μm↑). 주기: Real-time 연속(두께 Feedback) + Every Roll 전수 Defect Map. 이상 시: 두께 편차 → Slot-Die Gap·Pump Rate 조정, Streak·Pinhole → Filter 교체·Coating Head Cleaning, Coating Recipe 조정. | [3,4,6] | process_step | Coating Uniformity |
| Drying·curing 조건은 residual solvent, 접착력, barrier 성능과 연결되어야 한다. 측정: Inline GC/MS 또는 NIR(residual solvent <1,000ppm), UV Intensity Meter(500~5,000mW/cm²), DSC(Cross-linking Degree). 주기: Real-time 연속 + Every Batch Sampling(접착·Barrier). 이상 시: 잔류 Solvent ↑ → Oven Temp↑·Speed↓, UV Curing 불량 → Lamp 교체·Intensity↑, Lamination 불량 → Nip Pressure·Temp 조정. | [4,8,9] | process_step | Drying & Curing Control |
| Slitting은 roll width, edge defect, splice, length loss를 roll ID별로 추적해야 한다. 측정: Width Laser Micrometer(±0.1~0.5mm), Edge Vision Camera(Wave·Burr·Crack), Splice Counter(개수·위치·유형). 주기: Every Slit Roll 전수. 이상 시: Edge Defect 증가 → Slitter Knife 교체, Width 편차 → Slitting Program 재설정, Splice 불량 → Splice Tape·Method 변경. | [7,10] | process_step | Slitting Trace |
| Final Test는 고객 spec별로 광학·전기·물성·barrier 성능을 분리 관리해야 한다. 측정: UV-Vis Spectrophotometer(Transmittance·Haze·Color), 4-Point Probe(Resistivity), Mocon(WVTR·OTR), Universal Testing Machine(Tensile·Elongation). 주기: Every Slit Roll Sampling(상위 10~30% 전수 Test) 또는 고객 요건별 전수. 이상 시: 성능 미달 → Grade 하향 Bin 전환, 해당 Roll Block 후 공정 Recipe 조정. | [9,10] | process_step | Material Performance Gate |
| 기능성 필름은 시간 경과 안정성, 보관 조건, shelf life 기준이 품질 판정에 포함되어야 한다. 측정: Aging Chamber(23~60℃, 30~80%RH, 1~7일), 성능 측정(초기값 vs. Aging 후 비교). 주기: Every Slit Roll 배치별 Aging 시험 + 주기적 Shelf Life 확인. 이상 시: 성능 저하 → Shelf Life 단축, 보관 조건 변경(온도↓·Humidity↓). | [8,10] | process_step | Aging & Shelf Life |

## D08.4 control_points_detail_zh

| text | step_refs | scope | category |
|---|---|---|---|
| 原材料批次、混合batch、mother roll、slit roll的genealogy必须连续。测量方法: Barcode Scanner(材料Lot→Mixing Batch ID→Mother Roll ID→Slit Roll ID各阶段全数扫描)。管理周期: Every Batch/Roll全数。异常处理: 最终Grade不良时按Slit Roll→Mother Roll→Mixing Batch→材料Lot反向追溯，Hold问题Lot。 | [1,2,3,7,10] | process_step | Roll Genealogy |
| 混合与分散条件需连接到粘度、粒径、固含量与coating defect。测量方法: Brookfield/Rheometer(粘度, 100~10,000cP)、Laser Diffraction(粒径D50 0.1~10μm)、Halogen Analyzer(固含量10~70%)。管理周期: Every Batch先检。异常处理: 粘度偏差→调整Mixing Recipe(Speed·Time)、粒径异常→更换Bead Mill介质、Coating Streak时Batch报废。 | [2,3,6] | process_step | Dispersion Quality |
| R2R coating条件需连接到厚度偏差、streak、pinhole与particle defect。测量方法: Inline β-ray/IR Gauge(厚度±0.1~1μm)、Pinhole Detector(>10μm, High Voltage Spark)、Vision Camera(Streak·Particle 20~50μm↑)。管理周期: Real-time连续(厚度反馈) + Every Roll全数Defect Map。异常处理: 厚度偏差→调整Slot-Die Gap·Pump Rate、Streak·Pinhole→更换Filter·清洗Coating Head、调整Coating Recipe。 | [3,4,6] | process_step | Coating Uniformity |
| Drying与curing条件需连接到residual solvent、adhesion与barrier性能。测量方法: Inline GC/MS或NIR(残留溶剂<1,000ppm)、UV Intensity Meter(500~5,000mW/cm²)、DSC(交联度)。管理周期: Real-time连续 + Every Batch采样(粘接·阻隔)。异常处理: 残留溶剂↑→Oven Temp↑·Speed↓、UV固化不良→更换Lamp·Intensity↑、Lamination不良→调整Nip Pressure·Temp。 | [4,8,9] | process_step | Drying & Curing Control |
| Slitting需按roll ID追溯roll width、edge defect、splice与length loss。测量方法: Width Laser Micrometer(±0.1~0.5mm)、Edge Vision Camera(Wave·Burr·Crack)、Splice Counter(数量·位置·类型)。管理周期: Every Slit Roll全数。异常处理: Edge Defect增加→更换Slitter刀片、Width偏差→重设Slitting Program、Splice不良→改变Splice Tape·方法。 | [7,10] | process_step | Slitting Trace |
| Final Test需按客户spec分别管理光学、电性、物性与barrier性能。测量方法: UV-Vis Spectrophotometer(Transmittance·Haze·Color)、4-Point Probe(Resistivity)、Mocon(WVTR·OTR)、Universal Testing Machine(Tensile·Elongation)。管理周期: Every Slit Roll采样(上10~30%全数测试)或按客户全数。异常处理: 性能不达标→降Bin转换、该Roll Block后调整Recipe。 | [9,10] | process_step | Material Performance Gate |
| 功能膜需将时间稳定性、保存条件与shelf life标准纳入质量判定。测量方法: Aging Chamber(23~60℃, 30~80%RH, 1~7天)、性能测量(初始 vs Aging后比较)。管理周期: Every Slit Roll批次别Aging试验 + 定期Shelf Life确认。异常处理: 性能下降→缩短Shelf Life、改变储存条件(温度↓·湿度↓)。 | [8,10] | process_step | Aging & Shelf Life |

## D08.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Material | batch |  |  | material_lot_id, resin_lot_id, solvent_lot_id, additive_lot_id |
| 2 | Mixing | batch | Mixing Batch Loop |  | batch_id, recipe_id, viscosity_value, particle_size, solid_content |
| 3 | Coating | process | R2R Coating Loop |  | mother_roll_id, coating_recipe_id, coating_weight, line_speed |
| 4 | Drying | process |  |  | mother_roll_id, dryer_zone_id, tension_value, residual_solvent |
| 5 | Treatment | process |  |  | mother_roll_id, treatment_recipe_id, lamination_lot_id, surface_energy |
| 6 | Gate | gate |  | [3,4,5] | mother_roll_id, thickness_map_id, defect_map_id, inspection_result |
| 7 | Slitting | process |  |  | slit_roll_id, mother_roll_id, width_value, splice_id, length_value |
| 8 | Aging | process |  |  | slit_roll_id, aging_lot_id, storage_condition_id, stability_result |
| 9 | Gate | gate |  | [6,8] | slit_roll_id, performance_result, adhesion_value, barrier_value, final_grade |
| 10 | Final | process |  |  | slit_roll_id, box_id, customer_spec_id, shipment_lot_id |

**step_expression 연결 설명(ko)**: Material Preparation(1, Batch)→Mixing(2, Mixing Batch Loop)에서 Slurry/Batch가 준비되며, Coating(3, R2R Coating Loop)에서 Mother Roll 단위로 연속 코팅된다. Drying(4)→Surface Treatment(5)를 거친 후 Inline Inspection Gate(6)에서 두께·결함 전구간 검증. 통과한 Mother Roll은 Slitting(7)에서 복수의 Slit Roll로 분할되며, 이 시점에서 mother_roll_id에서 slit_roll_id로 Primary Key 전환. Aging(8) 후 Final Test Gate(9)에서 성능 종합 검증, Packing/Shipment(10)에서 Roll→Box→Pallet Mapping 완료. step6의 mother_roll_id 기반 defect_map_id가 step9의 final_grade와 직결되어 코팅 결함→최종 등급 연쇄 분석 가능.

## D08.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Material | batch |  |  | material_lot_id, resin_lot_id, solvent_lot_id, additive_lot_id |
| 2 | Mixing | batch | Mixing Batch Loop |  | batch_id, recipe_id, viscosity_value, particle_size, solid_content |
| 3 | Coating | process | R2R Coating Loop |  | mother_roll_id, coating_recipe_id, coating_weight, line_speed |
| 4 | Drying | process |  |  | mother_roll_id, dryer_zone_id, tension_value, residual_solvent |
| 5 | Treatment | process |  |  | mother_roll_id, treatment_recipe_id, lamination_lot_id, surface_energy |
| 6 | Gate | gate |  | [3,4,5] | mother_roll_id, thickness_map_id, defect_map_id, inspection_result |
| 7 | Slitting | process |  |  | slit_roll_id, mother_roll_id, width_value, splice_id, length_value |
| 8 | Aging | process |  |  | slit_roll_id, aging_lot_id, storage_condition_id, stability_result |
| 9 | Gate | gate |  | [6,8] | slit_roll_id, performance_result, adhesion_value, barrier_value, final_grade |
| 10 | Final | process |  |  | slit_roll_id, box_id, customer_spec_id, shipment_lot_id |

**step_expression连接说明(zh)**: Material(1, Batch)→Mixing(2, Mixing Batch Loop)制备Slurry/Batch，Coating(3, R2R Coating Loop)以Mother Roll为单位连续涂布。Drying(4)→Surface Treatment(5)后Inline Inspection Gate(6)全段验证厚度·缺陷。通过Mother Roll在Slitting(7)分割为多个Slit Roll，此时从mother_roll_id切换为slit_roll_id为主键。Aging(8)后Final Test Gate(9)综合验证性能，Packing/Shipment(10)完成Roll→Box→Pallet Mapping。step6的mother_roll_id级defect_map_id直接连接step9的final_grade，实现涂布缺陷→最终等级连锁分析。

## D08.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 원재료 투입 |
| 2 | 2 | 고속 분산 |
| 2 | 3 | 점도·입도 검사 |
| 3 | 1 | Slot-die coating |
| 3 | 2 | 장력 제어 |
| 3 | 3 | Inline 두께 측정 |
| 7 | 1 | Slitting setup |
| 7 | 2 | Edge inspection |
| 7 | 3 | Rewinding |

## D08.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 原材料投入 |
| 2 | 2 | 高速分散 |
| 2 | 3 | 粘度与粒径检查 |
| 3 | 1 | Slot-die coating |
| 3 | 2 | 张力控制 |
| 3 | 3 | Inline厚度测量 |
| 7 | 1 | Slitting setup |
| 7 | 2 | Edge inspection |
| 7 | 3 | Rewinding |

```yaml
data_capture_points:
  - material_lot_id
  - resin_lot_id
  - solvent_lot_id
  - additive_lot_id
  - batch_id
  - recipe_id
  - viscosity_value
  - particle_size
  - solid_content
  - mother_roll_id
  - coating_recipe_id
  - coating_weight
  - line_speed
  - dryer_zone_id
  - tension_value
  - residual_solvent
  - treatment_recipe_id
  - lamination_lot_id
  - surface_energy
  - thickness_map_id
  - defect_map_id
  - inspection_result
  - slit_roll_id
  - width_value
  - splice_id
  - length_value
  - aging_lot_id
  - storage_condition_id
  - stability_result
  - performance_result
  - adhesion_value
  - barrier_value
  - final_grade
  - box_id
  - customer_spec_id
  - shipment_lot_id
```

---

## 9. slug별 변경 요약

| slug | 주요 보강 | gate step | loop_hint | trace 핵심 |
|---|---|---|---|---|
| D01 `tft_lcd_panel` | TFT Array, Cell, Film, Optical Gate 구조화 | 4,8,10 | Array Pattern Loop | panel_id, defect_map_id, mura_code |
| D02 `oled_display_panel` | Backplane, OLED 증착, Encapsulation, Aging/Compensation 반영 | 3,8,10 | TFT Pattern Loop | panel_id, thickness_map_id, compensation_file_id |
| D03 `cover_glass_touch` | Cutting, 강화, Coating, Touch, Lamination 분리 | 7,8,10 | - | glass_id, sensor_pattern_id, oca_lot_id |
| D04 `battery_cell` | 전극-조립-Formation-Aging-Grading genealogy 반영 | 4,9,10 | Slurry Batch Loop, Coating Roll Loop, Formation Channel Loop | cell_id, electrode_roll_id, formation_profile_id |
| D05 `battery_module_pack` | Cell-to-Pack, welding, BMS/SW, EOL safety trace 반영 | 1,5,7,9 | - | cell_id, module_id, pack_id, sw_version |
| D06 `pv_cell` | Wafer-to-cell, diffusion, passivation, metallization, IV bin 반영 | 7,8 | - | cell_id, el_image_id, iv_curve_id, bin_code |
| D07 `pv_module` | Cell-to-module, stringing, lamination, EL/IV, warranty trace 반영 | 1,4,8 | - | module_id, string_id, pre_el_image_id, power_bin |
| D08 `functional_film_material` | R2R coating, drying, slitting, aging, material performance gate 반영 | 6,9 | Mixing Batch Loop, R2R Coating Loop | mother_roll_id, slit_roll_id, thickness_map_id |

---

## 10. self-check

```text
[ ] D01~D08 전수, slug당 §N.1~§N.8 섹션 완비
[ ] §0 오기 없음: control_points_ko/zh는 R2 자동생성 전제
[ ] control_points_detail에 category 열 전건 작성
[ ] step_expression ko/zh 행 수 = process_steps 행 수
[ ] line/panel/battery/PV/R2R slug별 role=gate ≥1
[ ] trace_keys ⊆ data_capture_points slug별 검토 필요
[ ] ko/zh 동형 검증 필요
[ ] en/ja 섹션·문단 없음
[ ] JSON·코드·스크립트 수정 없음
```

---

## 11. 후속 작업 지시 초안

```text
【임무】D산업 A1 Ch3 데이터팩 v0.3 리뷰 및 JSON 변환 준비

【정본】
- a1_ch3_D_process_detail_runtime_datapack_ko_zh_v0_3_2026-07-06.md
- A1_CH3_B_process_detail_datapack_refactor_instruction_2026-07-06.md

【검증】
- slug별 trace_keys가 data_capture_points의 부분집합인지 확인
- ko/zh step 수, step_refs, role, gate_for, trace_keys 동형 확인
- role=gate의 gate_for 누락 여부 확인
- D04/D08처럼 batch 또는 roll loop가 있는 slug의 loop_hint 렌더링 영향 확인

【금지】
- JSON 수기 편집 금지
- en/ja 공정문 작성 금지
- control_points_ko/zh 별도 테이블 작성 금지
```
