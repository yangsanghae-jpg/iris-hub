# A1 Ch3 F산업 공정 상세 데이터팩 v0.3 — 소비재·식품 제조

> 파일명: `a1_ch3_F_process_detail_runtime_datapack_ko_zh_v0_3_2026-07-06.md`  
> 작성일: 2026-07-06  
> 범위: F01~F08, ko/zh only  
> 목적: A1 Ch3 pflow V3.023용 F산업 공정 상세 데이터팩 초안  
> 주의: JSON·코드·스크립트 적용 대상 아님. MD 리팩 산출물만 작성.

## 0. 작성 기준

본 파일은 B산업 리팩 지시서의 v0.3 구조를 F산업에 적용한 MD 초안이다. Ch3가 실제 소비하는 `module`, `role`, `gate_for`, `loop_hint`, `trace_keys`, `operations`, `control_points_detail.category`를 포함한다.

`control_points_ko/zh` 별도 섹션은 작성하지 않는다. 필요한 경우 변환 규칙에서 `control_points_detail_ko/zh`를 이용해 자동 생성한다.

## 0.1 F산업 공통 해석

F산업은 식품·음료·유제품·베이커리·화장품·생활용품·섬유패션·포장재를 포함한다. 공통적으로 다SKU, 유통기한 또는 시즌성, 고속 라인, 원료/포장재 Lot, Batch/Line genealogy, 라벨·코드 오류 방지, QA Release, Recall/Complaint Trace가 중요하다.

## 0.2 slug 목록

| code | legacy_slug | name_ko | name_zh | routing | preset_id |
|---|---|---|---|---|---|
| F01 | `food_processing` | 식품 가공 | 食品加工 | RT_BATCH_LINE | batch_line_food_v1 |
| F02 | `beverage` | 음료·주류 | 饮料与酒类 | RT_LINE | high_speed_filling_v1 |
| F03 | `food_processing` | 유제품·냉장식품 | 乳制品与冷藏食品 | RT_BATCH_COLD_CHAIN | cold_chain_batch_v1 |
| F04 | `food_processing` | 제과·베이커리 | 糕点与烘焙 | RT_LINE_BATCH | bakery_line_v1 |
| F05 | `personal_care` | 화장품·퍼스널케어 | 化妆品与个人护理 | RT_BATCH_PACK | cosmetic_batch_pack_v1 |
| F06 | `home_care` | 생활·가정용품 | 生活与家居用品 | RT_BATCH_LINE | homecare_batch_line_v1 |
| F07 | `consumer_goods` | 섬유·의류·패션 | 纺织服装与时尚消费品 | RT_JOBSHOP_LINE | apparel_job_line_v1 |
| F08 | `consumer_goods` | 포장재·일반 소비재 | 包装材料与一般消费品 | RT_LINE_CONVERTING | packaging_line_v1 |

## 0.3 F산업 Ch3 표현 원칙

- 식품·음료·유제품·베이커리: `Batch → CCP/Inline Gate → Packaging → QA Release → Shipment Trace`
- 화장품·생활용품: `Formula/Weighing → Bulk Making → Bulk Hold → Filling → Packaging → QA Release`
- 섬유·의류: `Style/Color/Size → Cutting Bundle → Sewing/Finishing → AQL Gate → Shipment/Return Trace`
- 포장재·일반 소비재: `Material/Roll → Print/Coating/Forming → Vision Gate → Case/Pallet Trace`
- `trace_keys`는 slug별 `data_capture_points`의 부분집합으로만 작성한다.
- en/ja 공정·관리점 섹션은 작성하지 않는다.


---

## F01 `food_processing` — 식품 가공 / 食品加工

```yaml
code: "F01"
legacy_slug: "food_processing"
industry_group: "F"
industry_name_ko: "식품 가공"
industry_name_zh: "食品加工"
routing: "RT_BATCH_LINE"
preset_id: "batch_line_food_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - supplier_lot
  - recipe_id
  - batch_id
  - ccp_id
  - cook_temp
  - hold_time
  - metal_detector_result
  - weight_check_result
  - pack_lot
  - expiry_date
  - label_code
  - qa_release_id
  - pallet_id
  - shipment_id
```

### F01.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원료 입고·검수 | 농축수산 원료(곡물·육류·어류·채소), 식품첨가물(MSG·산도조절제), 향신료, 포장재(필름·파우치·골판지)의 Lot번호·제조일자·유효기간·COA(CoA) 확인. 저장온도(곡물 15~20°C, 냉동육 -18°C 이하), 알레르겐(대두·밀·난류·우유·땅콩) 태깅, 규제 승인상태 (HACCP·FSSC 22000) 확인 후 입고 Lot ID 발행. 보관위치(Warehouse bin) 등록 및 FEFO(First Expiry First Out) 정책 설정. |
| 2 | 계량·배합 | Recipe Revision 기반 Batch 단위 계량. Hopper scale·Loss-in-weight feeder로 분말·액상 원료 계량 (정확도 ±0.5%). 혼합기: Ribbon blender(분말)·Paddle mixer(반죽)·Homogenizer(유화)·Kneader(면류). 파라미터: 혼합시간 5~20분, 온도 20~80°C, RPM, 점도·pH·수분 측정. Batch ID 발행 및 투입 Lot 이력 기록. 예: 삼양식품 라면 반죽은 1Batch 약 300kg, 혼합온도 28~35°C. |
| 3 | 전처리·가열·살균 | 원료 특성별 전처리 수행. 농산물: Drum washer·Brush roller로 이물·토사 세척, Optical sorter(Satake·Bühler)로 색상·크기 이물 선별. 육류: 트리밍·해동(4°C 이하 Cold thawing, 48~72h), Bone separator 수산물: Descaler·Filleting machine 사용. 파라미터: 세척수온 5~15°C, 염소농도 50~100ppm, 해동시간·온도 이력 (CCP 모니터링). 선별 불량품은 SPC(Statistical Process Control) 차트로 추적. 핵심 CCP 단계. UHT(135~150°C/2~4초), HTST(72~85°C/15~30초), Retort(121°C/10~30분), Cooker(튀김·볶음·찜·굽기) 등 가열공정. 발효조(탱크 용량 5~50톤) 온도 25~45°C, pH 4.0~6.5, 시간 제어. 파라미터: Core temperature, Holding time, Pressure, Steam flow. 공정 Deviation 발생 시 자동 Flow diversion valve 작동 또는 Alarm 발생. 시간·온도 이력은 Batch record에 자동 저장. |
| 4 | 냉각·중간보관 | 가열 완료 제품의 잔여열 관리. Tunnel chiller(냉각터널, 0~10°C, 10~40분), Spiral freezer(-18~-40°C, IQF 급속동결), Drying oven(분말·과자 수분 2~5%까지), Aging room(발효·숙성). 파라미터: 냉각속도(°C/min), 최종품온, 수분활성도(Aw, 0.85 이하 목표), 점도. 온도 이력 기록 (CCP 모니터링). 유제품·육가공품 숙성실 온·습도 24시간 감시. |
| 5 | 충전·성형 | 제품 형태별 포장 단위 생성. Rotary filler(액상·페이스트), Form-fill-seal(FFS, 스틱·파우치), Tray sealer(용기), Molding(과자·어묵 성형), Slitter cutter(면·과자 절단). 충전량 ±1g 정밀도, Filling nozzle·Mold 식별자로 추적. 포장재 Lot·Film tension·Seal temperature(150~200°C) 실시간 기록. 에어컨디셔닝 포장실 온도 20~25°C, 습도 <50%. |
| 6 | 금속검출·중량검사 | 이물·품질 이슈 최종 게이트. Metal detector (Fe 0.5~1.0mm, SUS 1.0~2.0mm 감도)로 금속 이물 검출. X-ray 검사기(유리·돌·뼈·플라스틱 이물, 제품 밀도 이상 검출). Leak detector(진공챔버). Visual inspection camera(제품 형상·색상·크기·표면 결함). 미생물 검사(일반세균·대장균군·살모넬라·리스테리아), 이화학 검사(염도·산도·수분·지방) 샘플링 및 결과 Lot 연결. 부적합 시 자동 Reject/Divert. |
| 7 | 포장·라벨링 | Seal integrity: 열접합 강도·Leak 검사 (Vacuum chamber·Tension tester). Label 부착 (앞·뒷면 동시 라벨러, 정확도 ±1mm). Inkjet/Laser coder로 제조일자·유통기한·Lot code·Barcode(ITF-14·GS1-128) 인쇄. Checkweigher (±0.2~0.5g)로 중량 Overfill·Underfill 차단. 포장재 Artwork Revision 확인 및 Vision 검사(Label 위치·날짜 가독성·Barcode decode). 개별 제품을 판매·물류 단위로 집합. Carton erector·Case packer(Robotic picker/Place packer·Wrap-around packer)로 정량(예: 20개/case) 포장. Palletizer(로봇·고속 레이어 방식)로 Case를 적층. Pallet ID·SSCC(Serial Shipping Container Code) 발행, Case Label·Pallet Label 출력. 혼재 방지(Lot 일관성 확인), Pallet pattern 검증. 완제품 수량·무게 Lot 연결 기록. |
| 8 | 검사·QA Release | 생산 전환(Campaign Change) 시 CIP(세척액 농도 NaOH 1~3%·HNO3 0.5~1.5%, 온도 60~85°C, 유량 2~6 m/s) 자동 운전. 알레르겐 교차오염 방지를 위한 Segregation Sequence 및 Dry/wet cleaning 조합. 세척 후 Swab test(ATP bioluminescence·단백질 잔류 검사)로 Line clearance 검증. Allergen clearance 승인 후 차기 Batch 생산 개시. 생산 수율(Yield) 분석: 투입 원료 대비 완제품 수율 (예: 김치공정 수율 85~92%). Overfill(과충전) Giveaway(허용중량 초과) 관리. Scrap·Food loss(원료 폐기·재작업 로스). Water·Energy(스팀·전력)·세제 소비 라인별·Batch별 분석. Pakcaging waste 분리수거·재활용률 기록. ESK(환경·안전·품질) KPI Dashboard 생성. |
| 9 | 완제품 보관 | Cold chain 온도 유지: 냉장 0~10°C, 냉동 -18°C 이하, 상온(15~25°C). Warehouse 관리(WMS)에 Location bin·Storage condition·FEFO 정책 설정. 온도 데이터로거(로거 간격 10~15분)와 실시간 감시(냉장·냉동고). 보관 기간 초과 시 Alert 발송. HACCP 기준을 충족한 환경 유지. |
| 10 | 출하·리콜 추적 | ERP 수주 정보 기반 FEFO·FIFO 할당. 출고 지시에 따라 Pallet·Case 단위 Picking (RF scanner·Voice picking) 및 재고 차감. 트럭 적재 전 Cold chain 온도 확인 (온도 기록 로거 탑재). 출하 승인 (품질 Hold·Release 상태 확인). ASN(Advanced Shipping Notice) 발행 및 거래처 EDI 전송. 시장 출하 Lot의 유통기한 모니터링 (유통기한 임박 시 E-Commerce 채널 우선 공급·재고 조정). FDA FSMA Rule 204 대비 Critical Tracking Event(CTE) 및 Key Data Element(KDE) 기록. Recall 필요 시 한 Batch가 들어간 제품·Case·Pallet·출하처 전체의 영향 분석 실행. 반품 접수 시 이유 코드·검품·재작업/폐기 결정. |

### F01.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料收货与检验 | 在原料收货与检验阶段关联批次、产线与检验数据。 |
| 2 | 称量与配料 | 在称量与配料阶段关联批次、产线与检验数据。 |
| 3 | 预处理/加热/杀菌 | 在预处理/加热/杀菌阶段关联批次、产线与检验数据。 |
| 4 | 冷却与中间储存 | 在冷却与中间储存阶段关联批次、产线与检验数据。 |
| 5 | 灌装/成型 | 在灌装/成型阶段关联批次、产线与检验数据。 |
| 6 | 金检与重量检查 | 在金检与重量检查阶段关联批次、产线与检验数据。 |
| 7 | 包装与贴标 | 在包装与贴标阶段关联批次、产线与检验数据。 |
| 8 | 检验与QA放行 | 在检验与QA放行阶段关联批次、产线与检验数据。 |
| 9 | 成品储存 | 在成品储存阶段关联批次、产线与检验数据。 |
| 10 | 出货与召回追溯 | 在出货与召回追溯阶段关联批次、产线与检验数据。 |

### F01.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 원료 Lot·알레르겐 분리 | 2,3 | process_step | Material & Allergen |
| 2 | CCP 가열·살균 조건 이탈 감시 | 3 | process_step | CCP/HACCP |
| 3 | 금속검출·중량·포장 표시 연동 | 6,7 | process_step | Inline Quality |
| 4 | 유통기한·출하 Lot 리콜 추적 | 8,9,10 | process_step | Recall Trace |
| 5 | 세척·라인 클리어런스 확인 | 1,2,5 | process_step | Sanitation |
| 6 | 완제품 QA Release 전 Hold 관리 | 8,9 | process_step | QA Release |

### F01.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 原料批次与过敏原隔离 | 2,3 | process_step | Material & Allergen |
| 2 | CCP加热/杀菌条件偏差监控 | 3 | process_step | CCP/HACCP |
| 3 | 金检、重量、包装标识联动 | 6,7 | process_step | Inline Quality |
| 4 | 保质期与出货批次召回追溯 | 8,9,10 | process_step | Recall Trace |
| 5 | 清洗与清线确认 | 1,2,5 | process_step | Sanitation |
| 6 | 成品QA放行前Hold管理 | 8,9 | process_step | QA Release |

### F01.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, supplier_lot, recipe_id, batch_id |
| 2 | Preparation | batch |  |  | supplier_lot, recipe_id, batch_id, ccp_id |
| 3 | Processing | batch | Thermal Kill Step Loop |  | recipe_id, batch_id, ccp_id, cook_temp |
| 4 | Processing | process |  |  | batch_id, ccp_id, cook_temp, hold_time |
| 5 | Line | process | Thermal Kill Step Loop |  | ccp_id, cook_temp, hold_time, metal_detector_result |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | cook_temp, hold_time, metal_detector_result, weight_check_result |
| 7 | Packaging | process |  |  | hold_time, metal_detector_result, weight_check_result, pack_lot |
| 8 | QA Gate | gate |  | 1,2,3,4,5,6,7 | metal_detector_result, weight_check_result, pack_lot, expiry_date |
| 9 | Warehouse | process |  |  | weight_check_result, pack_lot, expiry_date, label_code |
| 10 | Shipment | process |  |  | pack_lot, expiry_date, label_code, qa_release_id |

### F01.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, supplier_lot, recipe_id, batch_id |
| 2 | Preparation | batch |  |  | supplier_lot, recipe_id, batch_id, ccp_id |
| 3 | Processing | batch | Thermal Kill Step Loop |  | recipe_id, batch_id, ccp_id, cook_temp |
| 4 | Processing | process |  |  | batch_id, ccp_id, cook_temp, hold_time |
| 5 | Line | process | Thermal Kill Step Loop |  | ccp_id, cook_temp, hold_time, metal_detector_result |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | cook_temp, hold_time, metal_detector_result, weight_check_result |
| 7 | Packaging | process |  |  | hold_time, metal_detector_result, weight_check_result, pack_lot |
| 8 | QA Gate | gate |  | 1,2,3,4,5,6,7 | metal_detector_result, weight_check_result, pack_lot, expiry_date |
| 9 | Warehouse | process |  |  | weight_check_result, pack_lot, expiry_date, label_code |
| 10 | Shipment | process |  |  | pack_lot, expiry_date, label_code, qa_release_id |

### F01.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F01.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F02 `beverage` — 음료·주류 / 饮料与酒类

```yaml
code: "F02"
legacy_slug: "beverage"
industry_group: "F"
industry_name_ko: "음료·주류"
industry_name_zh: "饮料与酒类"
routing: "RT_LINE"
preset_id: "high_speed_filling_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - syrup_batch
  - water_quality_result
  - recipe_id
  - cip_cycle_id
  - sip_cycle_id
  - filler_id
  - fill_volume
  - cap_torque
  - vision_result
  - label_code
  - expiry_date
  - pallet_id
  - shipment_id
```

### F02.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원수·원료 검수 | 원료: 농축과즙(NFC·FC)·정제수(WFI 품질)·탄산가스(CO₂) 식용알코올·첨가물(산도·감미·향료). 포장재: PET Preform·Can body·End·Label·Shrink film·Corrugated box. 입고 시 Sugar content(Brix) 확인·탄산수 농도 모니터링·알코올 도수 검증. COA Lot별 연결, 저장온도(과즙 -18°C·농축액 4°C). |
| 2 | 배합·시럽/원액 제조 | Recipe Management System 기반 원료 투입. Syrup blending tank: 물·시럽·산도조절제 비타민 등 계량 (Weight hopper·Magnetic flowmeter). 주류 배합: 주정·물·착향료·색소를 Blending Kettle에서 예비 혼합. Batch ID 할당 및 원료 Lot별 genealogy 기록. 파라미터: Brix, 산도(Titratable acidity), CO₂, Alcohol %, 점도, 색상. 혼합 RPM, 온도(탄산음료 1~4°C·주스 60~70°C) 기록. |
| 3 | 여과·균질·탈기 | 수처리: 정수(RO·UV)·연수기·여과로 용수 품질 확보 (전도도 <10μS/cm, TOC <200ppb). 시럽 제조: 설탕·고과당 용해 (용해기, 85~95°C), 활성탄 탈색·여과(Filtration), 시럽 Brix 조정 65~67°Bx. 탄산수 제조: Carbonator(탈기→냉각→CO₂ 주입). 주류: 배합 탱크에서 물·주정 착향료 혼합. 파라미터: Brix, CO₂ volume(2.5~4.0 vol), 알코올 도수(% ABV). |
| 4 | 살균·CIP/SIP 확인 | 음료 유형별 열처리: 과즙음료 HTST(85~95°C/15~30초)·UHT(120~140°C/2~10초) Plate/tubular heat exchanger. 주류: 맥주 발효탱크(발효 6~14일, 온도 8~16°C, pH 4.0~4.5, 원료 Lot→발효 Batch 연결), 막걸리 발효, 증류주 증류탑. 파라미터: 온도·압력·Holding time·Flow rate. CCP 이탈 시 자동 Alarm - 제품 Divert. 발효 Batch 이력 관리 (효모·원료 Lot). 음료 전환 시 CIP: 설비 유형별 CIP Recipe 적용(3단계: Pre-rinse→Caustic(70~80°C)→Rinse→Acid(60°C)→Rinse→Sanitize). 충전기 Filler bowl·Pipe·Tank·Valve 자동 세척. 알레르겐 전환:(우유 음료→과일 음료). Swab test·Rinse water ATP 검사. Line clearance 승인 후 생산 개시. |
| 5 | 충전·캡핑 | Filler: 알코올음료용 Isobaric counter-pressure filler(CO₂ 보존), 무가압 Gravity/Volumetric filler. 충전 속도 최대 1,200bpm(병)~2,000cpm(캔). Aseptic filler(UHT 음료 멸균 충전, ISO Class 5 환경). PET blow molding(Preform 가열→Stretch blow, 5~30g). Can maker(원통·End 부착, 300~400cpm). 충전량 ±0.5g(용기 350mL 기준). Nozzle·Mold ID 추적. |
| 6 | 인라인 검사 | Can·병의 누액검사(Leak tester: Pressure vacuum chamber). Metal detector(Fe 0.5mm, SUS 1.0mm) 및 X-ray 검사. 캔 외관: Seam inspection(두겹 이음부·Hook thickness). Brix·알코올·pH·CO₂ 온라인 측정(Process refractometer·NIR). 샘플링: 미생물 검사(무균 충전 제품), 관능검사(맛·향·색상). 부적합 자동 Reject (50~200ms 응답). |
| 7 | 라벨·팩킹 | Capper: Spindle capper(토크 10~25Nm)·Induction sealer(Aluminum foil, 80~150kW). Labeler: Wrap-around·PS label(±1mm)·Shrink sleeve. Inkjet/Laser coder: 생산일·유통기한·Lot code·Barcode. Checkweigher: Overfill/Giveaway 최소화(±0.2~0.5g). Vision system: Cap presence(Foam sku)·Label 오류·Date code 가독성 검사. |
| 8 | 팔레타이징 | Multi-packer: Can·PET 多량 묶음 (Plastic ring carrier·Shrink film). Case packer: Wrap-around(304 SS)와 Tray packer. Robotic palletizer: Pallet당 Case 적층 패턴과 Strapping/Stretch wrap 적용. 혼재 방지:Lot 단일성 확인. SSCC·Pallet Tag 출력. 물류 단위 각각의 고유 식별자(Pallet ID·Case RFID) 생성. |
| 9 | 품질 보류·Release | 냉장 제품: 0~10°C, 냉동 제품:-18°C, 상온 음료(15~25°C 60% RH). WMS Location 관리 및 FEFO/FIFO 정책 설정. 온도 로거·무선 온도 센서 모니터링. 냉장·냉동고 Door open alarm. Warehouse 재고 정확도(99%+). 하절기 제품 노화 방지를 위한 창고 온도 규정. 수율 분석: 원료 Brix·알코올 수율 vs 표준. 탄산음료 Overfill Giveaway(예:캔 +/-0.2g). PET Preform·Can End 재활용. 에너지: Steam/ton 제품, Electric/ton 비용. 폐수:BOD·COD 부하. PPWR(EU 포장 폐기물 규정) 대비 포장재 Recyclability·재생원료 비율 데이터 수집. |
| 10 | 창고·출하 | 계절 수요 대비 주문 할당(하절기 음료). FEFO Picking (RF scanner). 출하 시 트럭 적재 온도 기록(냉장·냉동 유지). 출하 승인(품질 상태, 정량 검증). ASN(Advanced Shipping Notice) 발행. 채널별 (할인점·편의점·유통·수출) 출하 이력 관리. 음료 유통기한(통상 6~12개월) 모니터링 및 시장 회수 시뮬레이션(Recall drill). FDA FSMA 204: CTE,KDE 기록. 유사시 동일 Batch가 들어간 모든 포장종류(캔·병·PET)·출하처 식별. 반품 제품은 외관검사·이화학 검사 후 재작업·Downgrade·폐기 판정. |

### F02.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 水源/原料检验 | 在水源/原料检验阶段关联批次、产线与检验数据。 |
| 2 | 调配与糖浆/原液制备 | 在调配与糖浆/原液制备阶段关联批次、产线与检验数据。 |
| 3 | 过滤/均质/脱气 | 在过滤/均质/脱气阶段关联批次、产线与检验数据。 |
| 4 | 杀菌与CIP/SIP确认 | 在杀菌与CIP/SIP确认阶段关联批次、产线与检验数据。 |
| 5 | 灌装与封盖 | 在灌装与封盖阶段关联批次、产线与检验数据。 |
| 6 | 在线检查 | 在在线检查阶段关联批次、产线与检验数据。 |
| 7 | 贴标与包装 | 在贴标与包装阶段关联批次、产线与检验数据。 |
| 8 | 码垛 | 在码垛阶段关联批次、产线与检验数据。 |
| 9 | 质量暂挂与放行 | 在质量暂挂与放行阶段关联批次、产线与检验数据。 |
| 10 | 仓储与出货 | 在仓储与出货阶段关联批次、产线与检验数据。 |

### F02.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 배합·원액 Batch와 충전 Lot 연결 | 2,5 | process_step | Batch-to-Line |
| 2 | CIP/SIP 완료 상태와 생산 투입 통제 | 4,5 | process_step | CIP/SIP |
| 3 | 충전량·캡 토크·누액 검사 관리 | 5,6 | process_step | Inline Quality |
| 4 | 라벨·유통기한·케이스 코드 검증 | 7,8 | process_step | Label & Code |
| 5 | 고속라인 OEE와 SKU 전환 손실 관리 | 5,6,7 | process_step | Line Efficiency |
| 6 | 출하 단위 Lot·팔레트 추적 | 8,10 | process_step | Shipment Trace |

### F02.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 调配/原液批次与灌装批次关联 | 2,5 | process_step | Batch-to-Line |
| 2 | CIP/SIP完成状态与投产控制 | 4,5 | process_step | CIP/SIP |
| 3 | 灌装量、盖扭矩、漏液检查管理 | 5,6 | process_step | Inline Quality |
| 4 | 标签、保质期、箱码校验 | 7,8 | process_step | Label & Code |
| 5 | 高速线OEE与SKU切换损失管理 | 5,6,7 | process_step | Line Efficiency |
| 6 | 出货单位批次与托盘追溯 | 8,10 | process_step | Shipment Trace |

### F02.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, syrup_batch, water_quality_result, recipe_id |
| 2 | Preparation | batch |  |  | syrup_batch, water_quality_result, recipe_id, cip_cycle_id |
| 3 | Processing | process | High-Speed Filling Changeover |  | water_quality_result, recipe_id, cip_cycle_id, sip_cycle_id |
| 4 | Sanitation | utility |  |  | recipe_id, cip_cycle_id, sip_cycle_id, filler_id |
| 5 | Filling Line | process | High-Speed Filling Changeover |  | cip_cycle_id, sip_cycle_id, filler_id, fill_volume |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | sip_cycle_id, filler_id, fill_volume, cap_torque |
| 7 | Packaging | process |  |  | filler_id, fill_volume, cap_torque, vision_result |
| 8 | Warehouse | process |  |  | fill_volume, cap_torque, vision_result, label_code |
| 9 | Warehouse | process |  |  | cap_torque, vision_result, label_code, expiry_date |
| 10 | Shipment | process |  |  | vision_result, label_code, expiry_date, pallet_id |

### F02.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, syrup_batch, water_quality_result, recipe_id |
| 2 | Preparation | batch |  |  | syrup_batch, water_quality_result, recipe_id, cip_cycle_id |
| 3 | Processing | process | High-Speed Filling Changeover |  | water_quality_result, recipe_id, cip_cycle_id, sip_cycle_id |
| 4 | Sanitation | utility |  |  | recipe_id, cip_cycle_id, sip_cycle_id, filler_id |
| 5 | Filling Line | process | High-Speed Filling Changeover |  | cip_cycle_id, sip_cycle_id, filler_id, fill_volume |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | sip_cycle_id, filler_id, fill_volume, cap_torque |
| 7 | Packaging | process |  |  | filler_id, fill_volume, cap_torque, vision_result |
| 8 | Warehouse | process |  |  | fill_volume, cap_torque, vision_result, label_code |
| 9 | Warehouse | process |  |  | cap_torque, vision_result, label_code, expiry_date |
| 10 | Shipment | process |  |  | vision_result, label_code, expiry_date, pallet_id |

### F02.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F02.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F03 `food_processing` — 유제품·냉장식품 / 乳制品与冷藏食品

```yaml
code: "F03"
legacy_slug: "food_processing"
industry_group: "F"
industry_name_ko: "유제품·냉장식품"
industry_name_zh: "乳制品与冷藏食品"
routing: "RT_BATCH_COLD_CHAIN"
preset_id: "cold_chain_batch_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - supplier_lot
  - milk_tank_id
  - receiving_temp
  - recipe_id
  - batch_id
  - pasteurization_temp
  - pasteurization_time
  - culture_lot
  - fermentation_time
  - filler_id
  - pack_lot
  - expiry_date
  - cold_room_temp
  - micro_test_result
  - shipment_id
```

### F03.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원유·냉장 원료 입고 | 원유 수입검사: 냉각온도 4°C 이하, 산도(SH) 0.14~0.18, 비중 1.028~1.034, 세균수(<10만 CFU/mL), 체세포수(<40만/mL), 항생제 잔류 음성. 분말유·스타터 문화(냉동·동결건조)·안정제·유화제·향료·색소 입고·저장온도 확인. 포장재(용기·필름·라벨) Lot별 COA 및 유효기간. 모든 원료 입고 Lot에 저장 사일로·탱크 할당. |
| 2 | 검사·온도 승인 | 검사·온도 승인 단계에서 Lot·Batch·라인·검사 데이터를 연결한다. |
| 3 | 표준화·배합 | 원유 저장 사이로(4°C, 24시간 이내 처리). 원심분리 Cream separator(지방분 분리, 5,000~10,000G). 표준화:저지방·탈지 표준비율로 혼합(Standardization valve). 균질화(Homogenizer 150~200bar, 60~70°C): 지방구를 2μm 이하로 분쇄하여 크림 분리 방지. 균질화 압력·온도 Batch 기록. 발효유용 원유는 BT(95°C/5분) 고온 살균 강화. Stainless steel blending tank(3000~20000L). 표준화된 유제품 베이스에 분유·코코아·과즙·향료·미생물 배양액 Recipe별 투입. 계량 정확도 ±0.5%. 요구르트: 스타터(Streptococcus thermophilus·Lactobacillus bulgaricus) 접종(42~45°C). Batch ID 할당, 원료 Lot-Genealogy 생성. Mixing RPM, 온도, 투입 순서 기록. |
| 4 | 살균·균질 | 유제품 중심 변환공정: HTST(72~85°C/15초) 시유, UHT(135~145°C/1~4초) 초고온 멸균(멸균음료). 치즈: Pasteurization(72°C/15초)→Cooling→Rennet 첨가→Coagulation(31~35°C,약 30분)→Curd cutting(1cm 입방)→Cooking(38~40°C, 45분)→Whey drainage. 요구르트: 발효 incubation(42~45°C,pH 4.5 도달까지 4~6시간). 아이스크림: Pasteurize(80°C·25초)→ Aging(4°C·4~24시간)→ Freeze(-5~-8°C,Overrun 80~120%). |
| 5 | 발효·숙성 또는 냉각 | 제품별 냉각: 시유 급냉(Plate cooler 4°C 이하, 30분 이내). 요구르트 발효완료 후 급랭(4~7°C, Swelling 중단). 치즈: Salt brine 침지·Maturation room(8~16°C, 85~95% RH, 수주~수년). 아이스크림 Hardening tunnel(-25~-40°C, 30~60분, Core temp -18°C 목표). 파라미터: 냉각속도, 최종품온, 수분, pH, 지방산패도. 급변 온도 이력 기록. |
| 6 | 충전·실링 | Aseptic Filling(UHT 제품): Aseptic filler(Tetra Pak·Combibloc·SIG) ISO Class 5 환경,Carton·PET·Bottle 충전. 시유: Rotary Fill(정온 충전 4~7°C). 요구르트:Cup filler(Pre-formed cup·Foil seal). 치즈:Forming·Mold press(네덜란드 Gouda·에멘탈 Cheese wheel). 아이스크림: Extrusion·Cup filling·Mold. Fill weight ±1~3g. Nozzle-Cup-Mold ID 기록. 밀크·요구르트 Multi-pack carton·Case(12·24개). Palletizing:저온제품은 Cold store 전용 Palletizer(Stainless 재질, 0~7°C 환경). 아이스크림: Tray packing·Wrap. 유제품 Pallet 적층 시 냉기 순환 고려 패턴. SSCC/Pallet ID 발행. Case label·Pallet label (GS1-128) 포장 수량·Lot 일치 확인. |
| 7 | 냉장 보관 | 유제품 Seal integrity 핵심: Induction seal(Aluminum foil)/Heat seal/Seal cup foil. Leak test(Chamber pressure decay). Label(순수라벨·투명라벨). Use-by·Batch code·Barcode Laser/Inkjet 코딩. Checkweigher(±0.2~1g)로 품질 관리. 유치원 급식·Catering 등 유통경로별 Label 규정 준수 확인(영양성분·알레르겐 표시). |
| 8 | 미생물·품질 검사 | 유제품 이물 검출: Metal detector(Fe 0.8mm·SUS 1.2mm). X-ray(유·돌·뼈 파편). Leak Detector(요구르트·음용유). 외관: 용기 변형·후지(back swelling)·금속 캔 부식 검사. 품질: 지방·단백질·유당·총고형분(NIR online sensor, ±0.05%). 미생물 검사(일반세균·대장균·살모넬라·리스테리아):Lot당 샘플링 기준(HACCP 검증). 관능: 색·향·맛·질감 |
| 9 | 출하 피킹 | 냉장(0~10°C):시유·요구르트·치즈. 냉동(-18°C 이하):아이스크림·냉동유제품. 창고 온도·습도 실시간 모니터링(로거 10분 간격). FEFO 정책 설정(유통기한 7~14일 시유는 FIFO가 아니고 FEFO). 냉장 창고 Cold chain 보관 시간 및 온도 이탈 기록. 제품 Hold(품질 이슈 시 자체 격리) Zone 운영. |
| 10 | 콜드체인 추적 | ERP/WMS 수주 정보 기반 FEFO 할당. 저온 출하 Picking(냉동·냉장 창고). 온도 기록 Truck 적재(냉장 4°C·냉동 -18°C). 출하 승인(품질 Hold·Release). 선적 전 Loading inspection(Temperature check). 거래처 EDI 주문 연동. 소매점별 맞춤 피킹(스쿨밀크·급식 등). 유통기한(시유 7~14일·멸균 음료 6~9개월·치즈 6~12개월) 모니터링. 유통기한 임박 제품 E-Commerce 우선 할당·할인 처분. FDA FSMA 204 대비 CTE·KDE 기록. 원유 공급사→제조 Batch→출하처 전 Tracing. 리스테리아·살모넬라 의심 시 전제품 영향 분석(Recall 시나리오). 대규모 리콜(예: 미국 유제품 2025 Listeria recall) 사례 반영. 반품 접수·검품·재가공·폐기. |

### F03.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原奶/冷藏原料收货 | 在原奶/冷藏原料收货阶段关联批次、产线与检验数据。 |
| 2 | 检验与温度放行 | 在检验与温度放行阶段关联批次、产线与检验数据。 |
| 3 | 标准化与配料 | 在标准化与配料阶段关联批次、产线与检验数据。 |
| 4 | 杀菌与均质 | 在杀菌与均质阶段关联批次、产线与检验数据。 |
| 5 | 发酵/熟成或冷却 | 在发酵/熟成或冷却阶段关联批次、产线与检验数据。 |
| 6 | 灌装与封口 | 在灌装与封口阶段关联批次、产线与检验数据。 |
| 7 | 冷藏储存 | 在冷藏储存阶段关联批次、产线与检验数据。 |
| 8 | 微生物与质量检验 | 在微生物与质量检验阶段关联批次、产线与检验数据。 |
| 9 | 出货拣选 | 在出货拣选阶段关联批次、产线与检验数据。 |
| 10 | 冷链追溯 | 在冷链追溯阶段关联批次、产线与检验数据。 |

### F03.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 수입검사·온도 이탈 Lot 격리 | 1,2 | process_step | Cold Receiving |
| 2 | 살균 조건과 Batch Record 연결 | 4 | process_step | Pasteurization |
| 3 | 발효·숙성 시간과 품질 편차 관리 | 5 | process_step | Fermentation |
| 4 | 냉장 보관·출하 온도 이력 추적 | 7,9,10 | process_step | Cold Chain |
| 5 | 미생물 검사 전 출하 방지 | 8,9 | process_step | Micro QA |
| 6 | 짧은 유통기한 FEFO 피킹 | 9,10 | process_step | FEFO |

### F03.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 收货检验与温度偏差批次隔离 | 1,2 | process_step | Cold Receiving |
| 2 | 杀菌条件与批记录关联 | 4 | process_step | Pasteurization |
| 3 | 发酵/熟成时间与质量偏差管理 | 5 | process_step | Fermentation |
| 4 | 冷藏储存与出货温度履历追溯 | 7,9,10 | process_step | Cold Chain |
| 5 | 微生物检验前防止出货 | 8,9 | process_step | Micro QA |
| 6 | 短保质期FEFO拣选 | 9,10 | process_step | FEFO |

### F03.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | supplier_lot, milk_tank_id, receiving_temp, recipe_id |
| 2 | QC Gate | gate |  | 1 | milk_tank_id, receiving_temp, recipe_id, batch_id |
| 3 | Preparation | batch | Cold Chain Loop |  | receiving_temp, recipe_id, batch_id, pasteurization_temp |
| 4 | Thermal Process | batch |  |  | recipe_id, batch_id, pasteurization_temp, pasteurization_time |
| 5 | Fermentation/Cold | process | Cold Chain Loop |  | batch_id, pasteurization_temp, pasteurization_time, culture_lot |
| 6 | Filling | process |  |  | pasteurization_temp, pasteurization_time, culture_lot, fermentation_time |
| 7 | Cold Storage | process |  |  | pasteurization_time, culture_lot, fermentation_time, filler_id |
| 8 | QA Gate | gate |  | 1,2,3,4,5,6,7 | culture_lot, fermentation_time, filler_id, pack_lot |
| 9 | Picking | process |  |  | fermentation_time, filler_id, pack_lot, expiry_date |
| 10 | Shipment | process |  |  | filler_id, pack_lot, expiry_date, cold_room_temp |

### F03.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | supplier_lot, milk_tank_id, receiving_temp, recipe_id |
| 2 | QC Gate | gate |  | 1 | milk_tank_id, receiving_temp, recipe_id, batch_id |
| 3 | Preparation | batch | Cold Chain Loop |  | receiving_temp, recipe_id, batch_id, pasteurization_temp |
| 4 | Thermal Process | batch |  |  | recipe_id, batch_id, pasteurization_temp, pasteurization_time |
| 5 | Fermentation/Cold | process | Cold Chain Loop |  | batch_id, pasteurization_temp, pasteurization_time, culture_lot |
| 6 | Filling | process |  |  | pasteurization_temp, pasteurization_time, culture_lot, fermentation_time |
| 7 | Cold Storage | process |  |  | pasteurization_time, culture_lot, fermentation_time, filler_id |
| 8 | QA Gate | gate |  | 1,2,3,4,5,6,7 | culture_lot, fermentation_time, filler_id, pack_lot |
| 9 | Picking | process |  |  | fermentation_time, filler_id, pack_lot, expiry_date |
| 10 | Shipment | process |  |  | filler_id, pack_lot, expiry_date, cold_room_temp |

### F03.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F03.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F04 `food_processing` — 제과·베이커리 / 糕点与烘焙

```yaml
code: "F04"
legacy_slug: "food_processing"
industry_group: "F"
industry_name_ko: "제과·베이커리"
industry_name_zh: "糕点与烘焙"
routing: "RT_LINE_BATCH"
preset_id: "bakery_line_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - allergen_code
  - recipe_id
  - dough_batch
  - mixer_id
  - proofing_time
  - oven_zone_temp
  - bake_time
  - cooling_time
  - metal_detector_result
  - pack_lot
  - expiry_date
  - order_id
  - shipment_id
```

### F04.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원료 준비 | 밀가루(강력·박력), 설탕, 무염버터, 마가린, 쇼트닝, 계란액, 우유, 분유, 베이킹파우더, 이스트, 소금, 코코아, 견과류, 건과일 등 Lot별 입고. 저장 조건: 밀가루(15~20°C, <60% RH), 냉동 변형 지방·계란액(4°C), 이스트(냉장 0~5°C). 알레르겐 관리(밀·우유·계란·땅콩)는 입고 시점부터 Tagging. 포장재(코팅지·박스·필름) 규격·Lot COA 확인. |
| 2 | 계량·반죽 | Recipe 정밀 계량: 분말 0.1g·액체 1g 단위 계량. Sponge/Straight dough법 적용. Dough mixer(Spiral mixer·Planetary mixer): 혼합 속도(저속 2분·고속 5분), 반죽 온도 26~28°C, Gluten development 확인. Chocolate/short dough: 반죽 온도 18~22°C. Batch ID 부여. 1차 발효(Bulk fermentation): 온도 조건실(26~28°C, 75~80% RH, 30~60분). 발효 정도: 반죽 부피 1.5배. |
| 3 | 발효·휴지 | Dividing: Dough divider(자동 압출·커팅, 설정 중량 ±1g). Rounding(구형), Moulding(롤·식빵틀). 중간 발효(Intermediate proof, 26~28°C, 10~20분). 파이·크로와상: Butter lamination(3~4겹×3~4회, 온도 4~8°C). 초콜릿: Temper(40~45°C 25~30°C→27~28°C 31~32°C 결정화) Moulding. 성형 Gold·Biscuit: Rotary molder·Wire-cut·Extruder. |
| 4 | 성형·토핑 | Dry cleaning + Wet cleaning 병행. 빵 생지 잔류 Scraper·Brush·Vacuum·Air blow. 유지·초콜릿 등 잔여물 제거용 Wet cleaning(세제 1~3%·온수 40~60°C). 알레르겐 전환(땅콩→Plain·밀→GF) 시 Full wet cleaning + Allergen ELISA/Rapid test. Line clearance(First Off 제품 검사 승인) |
| 5 | 오븐 베이킹 | 최종 발효(Proofing Chamber: 35~38°C, 80~85% RH, 45~75분, 반죽 부피 2~3배). Baking Oven(Tunnel oven/Convection/Rack): 온도 160~230°C, 시간 15~60분(제품별). 핵심 CCP: Core temperature(빵 95~100°C·케이크 95~99°C·파이 90~95°C). 5~10분간 Steam injection(빵 껍질 광택). Color: Colorimetric sensor로 Bake endpoint 결정(CIE Lab ΔE). 오븐 Zone별 온도 설정·Profile 관리. |
| 6 | 냉각 | 베이킹 완료 후 냉각(De-pan→Cooling conveyor, 상온 20~25°C·10~40분→Core 32~35°C 이하). 제품 수분 이전(케이크 냉각 시간 45~60분). 쿠키 Cooling belt. Donut·Twist: Oil drain·Cooling(10~15분). 냉동 빵: Spiral freezer(-35~-40°C, 동결수분 30분). 안정화 종료: Core temp 32°C 이하 수분 최적. |
| 7 | 절단·소분 | 슬라이서(식빵 두께 12mm/15mm/22mm 자동 절단·블레이드 살균). 케이크 분할·장식(크림 Sandwich·토핑·살포). FFS(Form Fill Seal): 필름·트레이에 1포장씩 Seal. 개별 슬라이스 wrapping. 제조일·Lot 부여. Modified atmosphere packaging(MAP) 적용 가능(질소치환 N₂). 포장실 온도 18~22°C, 습도 40% 이하. |
| 8 | 포장·라벨링 | Seal: 열접합 온도 130~180°C(필름 종류별 Seal bar). Leak test: MAP 칼럼 압력 감쇠 검사(모든 식중독 원인균 차단). Label: 제품명·원재료·알레르겐·제조일·유통기한·영양성분·보관방법·가격. Barcode(SKU)-Date code(JDE/Day code)-Weight Checkweigher (±0.5g). 최종 제품 중량 표준 대비 실중량 ±2g 오차. 비정상 제품 Reject. 1차 포장 완료 제품을 12·24·48개/Case Pack. Carton erector·Case sealer. Palletizer(로봇·고속 적층)로 Pallet단위 생성. 외부 포장에 제품명·수량·Lot code·Pallet ID(SSCC) 표시. 혼재 방지(Lot 단일성). 물류 레이블(소매점 납품 정보). 냉동 제품용 Pallet 적층 고려(냉기 유통 구조). |
| 9 | 금속검출·검사 | Metal detector: Fe 0.8mm·SUS 1.2mm(X-ray 대체 가능). X-ray: 이물 검출(밀링·금속·유리·석회). 빵·케이크 색상·형상·균열·부서짐 Vision inspection(카메라 2~12MP, 200~1,000개/min). 샘플링 촉감·풍미·부패 검사(관능평가·지방산패). 미생물(일반세균·곰팡이·효모). 수분활성(Aw <0.85). 제품 특성(부피·질량·두께·기공) SPC 관리. |
| 10 | 출하 | 주문 및 계약 기반 FEFO 할당. 유통기한 모니터링. Pick: Pallet·Case 단위, RF Scanner·Voice. 출하 전 제품 검수(온도·중량·포장·Label 확인). 긴 유통기한 냉동 생지 수출·내수 구분. ASN·EDI 발송. 냉장/냉동 트럭 출하 온도 검증(적재 시 온도 기록). 유통기한 3~14일 단수명 제품 재고 회전 관리. 반품 상태에 따른 재가공·Downgrade·폐기. 알레르겐 오기재 교정 Recall. 곰팡이·이물 Recall 장외 모니터링(Batch·Line·Time window 연결). CTE/KDE 기록. 반품 검품·재포장·Downgrade(사료·재생원료) 결정. |

### F04.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料准备 | 在原料准备阶段关联批次、产线与检验数据。 |
| 2 | 称量与搅拌 | 在称量与搅拌阶段关联批次、产线与检验数据。 |
| 3 | 发酵与醒发 | 在发酵与醒发阶段关联批次、产线与检验数据。 |
| 4 | 成型与加料 | 在成型与加料阶段关联批次、产线与检验数据。 |
| 5 | 烘烤 | 在烘烤阶段关联批次、产线与检验数据。 |
| 6 | 冷却 | 在冷却阶段关联批次、产线与检验数据。 |
| 7 | 切割与分装 | 在切割与分装阶段关联批次、产线与检验数据。 |
| 8 | 包装与贴标 | 在包装与贴标阶段关联批次、产线与检验数据。 |
| 9 | 金检与检查 | 在金检与检查阶段关联批次、产线与检验数据。 |
| 10 | 出货 | 在出货阶段关联批次、产线与检验数据。 |

### F04.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 원료·알레르겐 투입 오류 방지 | 1,2 | process_step | Material & Allergen |
| 2 | 반죽 Batch·발효시간 추적 | 2,3 | process_step | Dough/Fermentation |
| 3 | 오븐 존별 온도·시간 조건 관리 | 5 | process_step | Oven Control |
| 4 | 냉각·포장 전 이물·금속검출 | 6,8,9 | process_step | Foreign Matter |
| 5 | 당일 생산·주문 출하 동기화 | 8,10 | process_step | Fresh Dispatch |
| 6 | 폐기·Loss 원인별 집계 | 2,5,7 | process_step | Yield/Loss |

### F04.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 防止原料与过敏原投料错误 | 1,2 | process_step | Material & Allergen |
| 2 | 面团批次与醒发时间追溯 | 2,3 | process_step | Dough/Fermentation |
| 3 | 烤炉分区温度与时间条件管理 | 5 | process_step | Oven Control |
| 4 | 冷却/包装前异物与金检 | 6,8,9 | process_step | Foreign Matter |
| 5 | 当天生产与订单出货同步 | 8,10 | process_step | Fresh Dispatch |
| 6 | 报废与损耗按原因统计 | 2,5,7 | process_step | Yield/Loss |

### F04.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, allergen_code, recipe_id, dough_batch |
| 2 | Dough | batch |  |  | allergen_code, recipe_id, dough_batch, mixer_id |
| 3 | Dough | process | Oven Batch Loop |  | recipe_id, dough_batch, mixer_id, proofing_time |
| 4 | Forming | process |  |  | dough_batch, mixer_id, proofing_time, oven_zone_temp |
| 5 | Oven | batch | Oven Batch Loop |  | mixer_id, proofing_time, oven_zone_temp, bake_time |
| 6 | Cooling | process |  |  | proofing_time, oven_zone_temp, bake_time, cooling_time |
| 7 | Cutting | process |  |  | oven_zone_temp, bake_time, cooling_time, metal_detector_result |
| 8 | Packaging | process |  |  | bake_time, cooling_time, metal_detector_result, pack_lot |
| 9 | Inline Gate | gate |  | 1,2,3,4,5,6,7,8 | cooling_time, metal_detector_result, pack_lot, expiry_date |
| 10 | Shipment | process |  |  | metal_detector_result, pack_lot, expiry_date, order_id |

### F04.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, allergen_code, recipe_id, dough_batch |
| 2 | Dough | batch |  |  | allergen_code, recipe_id, dough_batch, mixer_id |
| 3 | Dough | process | Oven Batch Loop |  | recipe_id, dough_batch, mixer_id, proofing_time |
| 4 | Forming | process |  |  | dough_batch, mixer_id, proofing_time, oven_zone_temp |
| 5 | Oven | batch | Oven Batch Loop |  | mixer_id, proofing_time, oven_zone_temp, bake_time |
| 6 | Cooling | process |  |  | proofing_time, oven_zone_temp, bake_time, cooling_time |
| 7 | Cutting | process |  |  | oven_zone_temp, bake_time, cooling_time, metal_detector_result |
| 8 | Packaging | process |  |  | bake_time, cooling_time, metal_detector_result, pack_lot |
| 9 | Inline Gate | gate |  | 1,2,3,4,5,6,7,8 | cooling_time, metal_detector_result, pack_lot, expiry_date |
| 10 | Shipment | process |  |  | metal_detector_result, pack_lot, expiry_date, order_id |

### F04.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F04.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F05 `personal_care` — 화장품·퍼스널케어 / 化妆品与个人护理

```yaml
code: "F05"
legacy_slug: "personal_care"
industry_group: "F"
industry_name_ko: "화장품·퍼스널케어"
industry_name_zh: "化妆品与个人护理"
routing: "RT_BATCH_PACK"
preset_id: "cosmetic_batch_pack_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - pack_material_lot
  - formula_id
  - batch_id
  - weighing_result
  - mixer_id
  - mix_temp
  - mix_time
  - viscosity_result
  - ph_result
  - micro_test_result
  - filler_id
  - pack_lot
  - label_code
  - qa_release_id
  - complaint_id
```

### F05.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원료·포장재 입고 | 원료: 오일(호호바·올리브·Shea butter), 계면활성제, 고분자, 보존제(Benzalkonium chloride·Paraben·Phenoxyethanol), 향료, 색소, 활성성분(비타민·히알루론산·레티놀). 포장재: Glass bottle·PET·LDPE tube·Cap·Pump·Label·Carton. 원료 입고 시 COA 검증(고유 식별·순도·미생물·안전성). Lot별 저장 위치 할당(원료 보관 온도:25°C 이하, 광차폐·습기). |
| 2 | 원료 계량 | Vacuum Emulsifier(고전단 Homogenizer+Vacuum). 수상을 주요 반응조에 투입, 유상을 서서히 이송하면서 고속 교반. Homogenization: Rotor-stator 3000~5000rpm, 온도 70~80°C, 15~30분. 액상(토너·에센스): 단순 Dissolver. 선블록: ZnO·TiO2 분산(입자 30~100nm). Batch ID 부여. 혼합 RPM·시간·온도·진공압력(-0.05MPa). Viscosity(1,000~50,000cP) 확인. |
| 3 | 유화·혼합·조제 | 수상(WP) 제조: 정제수(RO·DI)→70~80°C 가열→보습제(glycerin·betaine)·고분자(carbomer) 용해·Fan-type mixer. 유상(OP) 제조:오일·왁스·에멀젼(70~80°C) 용해·교반. 색소·안료 분산(3-roll mill·Bead mill, 입도 5~50μm). 고형 제품: 가루·프레스드(눈썹·아이섀도우) 분말 균일 믹싱. 예열: 오일·수상 템퍼링. 가열 유화 완료→ 냉각: 재킷 40°C 이하(냉각수 순환). 40~45°C: 감온 성분(향료·방부제·비타민·UV filter 첨가), 교반 균일. 25~30°C: pH 조정(6.0~7.6→Citric acid·NaOH). 살균: 제품 Type별 멸균 공정(Cream: 단시간 75°C 살균, LP: UV/Ozone 살균). 안정화(재킷 25°C at 40~60분 교반, Air bubble 제거). Viscosity·pH·Appearance·Color·Odor 체크. |
| 4 | 중간품 검사 | 중간품 검사 단계에서 Lot·Batch·라인·검사 데이터를 연결한다. |
| 5 | 숙성·보관 | 제품별 안정화: 크림·로션: 25~30°C 안정화 후 24시간 Room temperature Aging. 선크림: 48시간 숙성·입자 안정화. 립스틱: Mold+ Cooling tunnel(2.4°C/min, 20~30분). 스틱·베이스: 냉각 30분. Gel·세럼: Air bubble 완전 제거(초음파 Degas). Stable화 판정: 점도·분산성·pH. 승인 후 충전 이송. |
| 6 | 충전 | 충전(Filling): Cream Tube(자동 Filler 6~24 Head, 분당 28~50개, 6~500mL). 병·펌프(회전 Fill), 앰플·소포장(무균 필러Lipstick Molding: 용융→Mold→냉각→Demolding→Flame polishing. 1차 포장: 용기·튜브 결합(열수축·캡). 포장실 환경 Class 100,000. Fill Weight ±0.5~1.0g. Nozzle·Mold·Tube ID 기록. |
| 7 | 캡핑·라벨·카톤 | Seal: Induction seal(Al foil)·Leak test(Vacuum Chamber). Label: Front/Back 자동 부착(±0.5mm), Sleeve(수축터널). Laser·Inkjet: 제조일·Lot No(Manufacture/Expiry/GM Pick code). Checkweigher: 정·오중량 분별(±0.3g). Vision: Label 오정렬·날짜 가독성·Barcode decode. 포장 재질·디자인 Artwork Revision(GMP 확인). 1차 포장 완료→ Carton(Display box·Gift set, 2~12pcs) Insert·Leaflet·Carton sealing. Case Pack(6~24pcs): Wrap-around case packer·Shrink bundler. Palletizing: 로봇/수동(Private label·수출 별도 요구). Pallet ID(SSCC) 생성. 물류 Label·수량 검증. 혼재 방지:Lot 단일성. |
| 8 | 외관·중량 검사 | Metal Detector(Fe 0.8·SUS 1.5mm). X-ray 제품 내 이물 검출(돌·금속·플라스틱). 외관 검사(Vision 360°: 표면 스크래치·변형·이물·용기 불량). Cap·Pump 기능 검사(분사·회전·개폐). 샘플링 품질: 관능(색·향·질감), 물성(pH·점도·비중·안정성30일), 미생물(Total aerobic·Yeast/Mold·Pathogens). 부적합 제품 자동 Reject&Log. |
| 9 | QA Release | 화장품은 일반적으로 상온(15~25°C, <60%RH) 보관. 유효성분(Brightening·Anti-aging) 특성에 따라 직사광선 회피. 냉장(0~10°C): 천연·유기농·생(生) 화장품. 창고 관리: FEFO 기준 재고 선회전. 온도·습도 모니터링. 유효기간 초과 Alert. 검수 의뢰정책(출하 전 QA 검수). |
| 10 | 출하·클레임 추적 | ERP 수주 정보 기반 FEFO 할당. 주문 단위(개·Display·Case·Pallet). RF Scanner Picking. 출하 전 2차 포장·Label 이상 점검(Artwork revision). 출하 허가(품질 Hold/Release). 수출: 13자리 GS1 GTIN·수량·중량·HS Code 선적 서류 연동. EDI 전송(거래처·물류사). 유통기한 30~36개월 관리. FDA/식약처 화장품 리콜 대비: Lot-GTIN-유통처 조회 시스템. 성분·표시사항 오류 Recall(전 유통경로). CTE·KDE 기록. 반품 제품 외관·물성 검사 후 재가공·재충전·Downgrade(사용 불가 시 폐기). 지속 관찰 안정성 시험 구간 설정. |

### F05.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料/包材收货 | 在原料/包材收货阶段关联批次、产线与检验数据。 |
| 2 | 原料称量 | 在原料称量阶段关联批次、产线与检验数据。 |
| 3 | 乳化/混合/配制 | 在乳化/混合/配制阶段关联批次、产线与检验数据。 |
| 4 | 中间品检验 | 在中间品检验阶段关联批次、产线与检验数据。 |
| 5 | 熟化与储存 | 在熟化与储存阶段关联批次、产线与检验数据。 |
| 6 | 灌装 | 在灌装阶段关联批次、产线与检验数据。 |
| 7 | 旋盖/贴标/装盒 | 在旋盖/贴标/装盒阶段关联批次、产线与检验数据。 |
| 8 | 外观与重量检查 | 在外观与重量检查阶段关联批次、产线与检验数据。 |
| 9 | QA放行 | 在QA放行阶段关联批次、产线与检验数据。 |
| 10 | 出货与客诉追溯 | 在出货与客诉追溯阶段关联批次、产线与检验数据。 |

### F05.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 성분 Lot·처방 버전 추적 | 1,2,3 | process_step | Formula Trace |
| 2 | 계량 오차·원료 대체 승인 관리 | 2 | process_step | Weighing Control |
| 3 | 점도·pH·미생물 검사 Release | 4,9 | process_step | QC Release |
| 4 | 중간품 숙성·보관 조건 관리 | 5 | process_step | Bulk Hold |
| 5 | 포장재 Artwork·라벨 코드 검증 | 6,7 | process_step | Packaging Compliance |
| 6 | 클레임 역추적·회수 범위 산정 | 9,10 | process_step | Complaint Trace |

### F05.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 成分批次与配方版本追溯 | 1,2,3 | process_step | Formula Trace |
| 2 | 称量误差与替代原料审批管理 | 2 | process_step | Weighing Control |
| 3 | 粘度、pH、微生物检验放行 | 4,9 | process_step | QC Release |
| 4 | 中间品熟化与储存条件管理 | 5 | process_step | Bulk Hold |
| 5 | 包材版面与标签代码校验 | 6,7 | process_step | Packaging Compliance |
| 6 | 客诉反查与召回范围判定 | 9,10 | process_step | Complaint Trace |

### F05.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, pack_material_lot, formula_id, batch_id |
| 2 | Weighing | batch |  |  | pack_material_lot, formula_id, batch_id, weighing_result |
| 3 | Bulk Making | batch | Bulk Hold Loop |  | formula_id, batch_id, weighing_result, mixer_id |
| 4 | QC Gate | gate |  | 1,2,3 | batch_id, weighing_result, mixer_id, mix_temp |
| 5 | Bulk Hold | process | Bulk Hold Loop |  | weighing_result, mixer_id, mix_temp, mix_time |
| 6 | Filling | process |  |  | mixer_id, mix_temp, mix_time, viscosity_result |
| 7 | Packaging | process |  |  | mix_temp, mix_time, viscosity_result, ph_result |
| 8 | Inline Gate | gate |  | 1,2,3,4,5,6,7 | mix_time, viscosity_result, ph_result, micro_test_result |
| 9 | QA Gate | gate |  | 1,2,3,4,5,6,7,8 | viscosity_result, ph_result, micro_test_result, filler_id |
| 10 | Shipment | process |  |  | ph_result, micro_test_result, filler_id, pack_lot |

### F05.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, pack_material_lot, formula_id, batch_id |
| 2 | Weighing | batch |  |  | pack_material_lot, formula_id, batch_id, weighing_result |
| 3 | Bulk Making | batch | Bulk Hold Loop |  | formula_id, batch_id, weighing_result, mixer_id |
| 4 | QC Gate | gate |  | 1,2,3 | batch_id, weighing_result, mixer_id, mix_temp |
| 5 | Bulk Hold | process | Bulk Hold Loop |  | weighing_result, mixer_id, mix_temp, mix_time |
| 6 | Filling | process |  |  | mixer_id, mix_temp, mix_time, viscosity_result |
| 7 | Packaging | process |  |  | mix_temp, mix_time, viscosity_result, ph_result |
| 8 | Inline Gate | gate |  | 1,2,3,4,5,6,7 | mix_time, viscosity_result, ph_result, micro_test_result |
| 9 | QA Gate | gate |  | 1,2,3,4,5,6,7,8 | viscosity_result, ph_result, micro_test_result, filler_id |
| 10 | Shipment | process |  |  | ph_result, micro_test_result, filler_id, pack_lot |

### F05.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F05.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F06 `home_care` — 생활·가정용품 / 生活与家居用品

```yaml
code: "F06"
legacy_slug: "home_care"
industry_group: "F"
industry_name_ko: "생활·가정용품"
industry_name_zh: "生活与家居用品"
routing: "RT_BATCH_LINE"
preset_id: "homecare_batch_line_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - raw_material_lot
  - chemical_id
  - formula_id
  - batch_id
  - tank_id
  - mix_time
  - mix_temp
  - viscosity_result
  - fill_volume
  - seal_result
  - label_code
  - pack_lot
  - pallet_id
  - shipment_id
```

### F06.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원료·포장재 입고 | 원료 수입: LAS(Linear alkylbenzene sulfonate acid)·Sodium lauryl ether sulfate, Caustic soda, Na silicate, 효소 분말, 향료·색소·방부제. 포장재: HDPE 용기(Blow molded)/PET·Cap·Pump·Label·Carton. 원료 입고 시 COA 확인(순도·안정성). Tank Farm 저장(Bulk storage tank, 양산 수준). 포장재 수량·규격 검수. |
| 2 | 계량·배합 | 원료 Tank Farm→Mass Flow meter 정밀 계량(계면활성제·NaOH·Sodium silicate). 고체 원료(Soda ash·염류)는 Autoloader·Bag dumping station. 정제수 회수(RO·탈염수 준비). 발열 반응 방지 Cooling Jacket. 농축 액상 조제 전 예열(40~60°C) 필요한 원료 준비. Buffer Tank 안전성(중간 저장). 주 원료(계면활성제 혼합물·NaOH·Na silicate·정제수)를 Batch 반응 탱크(Stainless 316/Glass Lined, 5~50톤)에서 배합·반응(중화·Sulfonation·제조). 액체 세제: 계면활성제+제타 첨가+점도 조정(Viscosity modifier+Air bubble control). 분말 세제: Spray drying(<100m 입자)+응집(Granulation). 혼합시간: 30~120분. Viscosity, pH(7~9), Solid%·Density 모니터링. Batch ID 할당. |
| 3 | 혼합·반응 | 액체 제품: 긴 배합 완료 후 제피 온도로 냉각(30~40°C, 냉각 Coil·Jacket). 세정제: 배합온도 60~80°C(지방·유지 가용화). 살균: PAG 제(광범위 살균) UV/Ozone 탈기. 분말 세제: Sulfonic acid 중화+ 스프레이 건조(Tower, 200~250°C 열풍→ 50~60°C 냉각). 제상용·탈취제: 기능성 제조(온도 25~35°C). |
| 4 | 중간품 저장 | 액체 완제품 탱크(중간 저장) 1~3일 Aging(점도 안정화). 분말: 건조 후 Cooler(≥40~45°C, Rotary cool·정전기 방지). 점도 최종 조정(Viscosity 500~5,000cP). Air bubble(Oil·Gas capture)·Foam 안정성 확인. 점도·pH·밀도(±1%)·투명도·향·색상 크로스 체크. |
| 5 | 충전·성형 | Filler: 자동 충전기(Liquid: Gravity/Volumetric/Piston filler, 6~36 헤드. 분말: Auger filler). 속도: 30~120개/min(1~5L병). 용기 공급: 자동 Blow molding(OH)/디스펜서. Cap: Screw capper/Induction sealer. Pouch: Doy pack·FFS. 액상 제품 충전 온도(25~35°C). Fill Weight ±1~5g(L 2L 기준). |
| 6 | 캡핑·실링 | 라인 세척: 제품 전환(Host 제품→Neutral→다음 제품) 시 적절한 Flush(물+희석 세제+릴리스). Split tube cleaning(Turbulent flow, 1~2m/s, 50~60°C). 잔류 향료·색소 제거(Hot water·Steam injection). 파이프 통행 Check. 비누·세정제 라인은 Dry cleaning 병행. 생산 전환 승인(Line clearance: 잔유물·pH 눈 측정). |
| 7 | 라벨·포장 | Seal: Induction cap seal(Aluminum foil, High frequency). Leak test(Cap torque·Pressure decay). Label: PS label(±1mm)·Sleeve(Polyethylene sleeve). Laser/Inkjet coder: 제조일·Lot·Barcode·VOC 규정. Checkweigher(±1~5g). Vision: Label·Code·Barcode 확인. MSDS·안전·주의문구·사용법 표시 사항 부착. 1차 포장 완료→ Multipack(Shrink bundle·Wrap-around case). Case pack(6~24개). Palletizing(로봇/고속 적층). Pallet ID(SSCC) 발행. 물류 단위 Label(제품명·수량·Lot·Pallet ID). 혼재 방지: 저장 금지 제품·화학물류 취급(분류). 수출: 별도 표시·영문 라벨·HS Code. |
| 8 | 검사 | Metal Detector(Fe 0.8·SUS 1.5·Non-ferrous 1.2mm). X-ray: 불순물 검출(원료 잔류·응집). 외관 검사(Vision: 라벨 오류·용기 오염·변형·Cap Flush). 부식·누액·변형 검사. 품질 검사 샘플링: Active 성분 농도(LAS%·Na2O%·Alkalinity), pH, 점도, 거품성, 밀도, 향, 색상. 불합격 제품 Reject. |
| 9 | 팔레타이징 | 생활용품(세제·청소제) 대부분 상온·저장. 인화성·폭발성·부식성 제품은 위험물 저장 창고(적절한 환기, 온도 제한). FEFO 관리. 유통기한 2~3년 관리. 점도 변화·변색·분말 응고·냄새 변질 모니터링 수단. 창고 관리(WMS). 재고 정확도 99%+. |
| 10 | 출하 | ERP 수주 기반 FEFO 할당. RF scanner·Voice Picking(대형마트·물류센터). 출하 전 검수(포장 상태·Label·수량). 유통·온라인·전문점 구분 출하. 위험물 운송 규정 준수(UN 승인 용기·운송 표시). ASN·EDI. 중량 검증. 유통기한(통상 2~3년) 모니터링. 유통기한 경과 전 재고 관리(프로모션·기부). CPSC(미국 소비재 안전)·K-REACH 등록 대비 원료·성분 데이터 관리. 성분·표시 오류 Recall 시뮬레이션. 반품 검사(누액·변질·용기 손상) 후 재이용·재포장·Downgrade·폐기. |

### F06.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料/包材收货 | 在原料/包材收货阶段关联批次、产线与检验数据。 |
| 2 | 称量与配料 | 在称量与配料阶段关联批次、产线与检验数据。 |
| 3 | 混合/反应 | 在混合/反应阶段关联批次、产线与检验数据。 |
| 4 | 中间品储存 | 在中间品储存阶段关联批次、产线与检验数据。 |
| 5 | 灌装/成型 | 在灌装/成型阶段关联批次、产线与检验数据。 |
| 6 | 旋盖/封口 | 在旋盖/封口阶段关联批次、产线与检验数据。 |
| 7 | 贴标与包装 | 在贴标与包装阶段关联批次、产线与检验数据。 |
| 8 | 检查 | 在检查阶段关联批次、产线与检验数据。 |
| 9 | 码垛 | 在码垛阶段关联批次、产线与检验数据。 |
| 10 | 出货 | 在出货阶段关联批次、产线与检验数据。 |

### F06.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 화학 원료·위험물 보관 상태 관리 | 1,2 | process_step | Chemical Material |
| 2 | 배합 Batch·Tank genealogy 추적 | 2,3,4 | process_step | Batch/Tank Trace |
| 3 | 충전량·실링·누액 검사 관리 | 5,6,8 | process_step | Filling Quality |
| 4 | 포장재·라벨 버전 오류 방지 | 7 | process_step | Label Control |
| 5 | 라인 전환·세척 상태 확인 | 4,5 | process_step | Line Clearance |
| 6 | 원단위·Loss·OEE 집계 | 2,5,9 | process_step | Cost/OEE |

### F06.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 化学原料与危险品储存状态管理 | 1,2 | process_step | Chemical Material |
| 2 | 配料批次与储罐谱系追溯 | 2,3,4 | process_step | Batch/Tank Trace |
| 3 | 灌装量、封口、漏液检查管理 | 5,6,8 | process_step | Filling Quality |
| 4 | 防止包材与标签版本错误 | 7 | process_step | Label Control |
| 5 | 换线与清洗状态确认 | 4,5 | process_step | Line Clearance |
| 6 | 单耗、损耗与OEE统计 | 2,5,9 | process_step | Cost/OEE |

### F06.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, chemical_id, formula_id, batch_id |
| 2 | Weighing | batch |  |  | chemical_id, formula_id, batch_id, tank_id |
| 3 | Bulk Making | batch | Filling Line Changeover |  | formula_id, batch_id, tank_id, mix_time |
| 4 | Bulk Hold | process |  |  | batch_id, tank_id, mix_time, mix_temp |
| 5 | Filling | process | Filling Line Changeover |  | tank_id, mix_time, mix_temp, viscosity_result |
| 6 | Filling | process |  |  | mix_time, mix_temp, viscosity_result, fill_volume |
| 7 | Packaging | process |  |  | mix_temp, viscosity_result, fill_volume, seal_result |
| 8 | Inline Gate | gate |  | 1,2,3,4,5,6,7 | viscosity_result, fill_volume, seal_result, label_code |
| 9 | Warehouse | process |  |  | fill_volume, seal_result, label_code, pack_lot |
| 10 | Shipment | process |  |  | seal_result, label_code, pack_lot, pallet_id |

### F06.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_material_lot, chemical_id, formula_id, batch_id |
| 2 | Weighing | batch |  |  | chemical_id, formula_id, batch_id, tank_id |
| 3 | Bulk Making | batch | Filling Line Changeover |  | formula_id, batch_id, tank_id, mix_time |
| 4 | Bulk Hold | process |  |  | batch_id, tank_id, mix_time, mix_temp |
| 5 | Filling | process | Filling Line Changeover |  | tank_id, mix_time, mix_temp, viscosity_result |
| 6 | Filling | process |  |  | mix_time, mix_temp, viscosity_result, fill_volume |
| 7 | Packaging | process |  |  | mix_temp, viscosity_result, fill_volume, seal_result |
| 8 | Inline Gate | gate |  | 1,2,3,4,5,6,7 | viscosity_result, fill_volume, seal_result, label_code |
| 9 | Warehouse | process |  |  | fill_volume, seal_result, label_code, pack_lot |
| 10 | Shipment | process |  |  | seal_result, label_code, pack_lot, pallet_id |

### F06.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F06.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F07 `consumer_goods` — 섬유·의류·패션 / 纺织服装与时尚消费品

```yaml
code: "F07"
legacy_slug: "consumer_goods"
industry_group: "F"
industry_name_ko: "섬유·의류·패션"
industry_name_zh: "纺织服装与时尚消费品"
routing: "RT_JOBSHOP_LINE"
preset_id: "apparel_job_line_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - fabric_lot
  - trim_lot
  - style_no
  - color_code
  - size_code
  - cut_lot
  - bundle_id
  - sewing_line_id
  - operation_id
  - wash_batch
  - defect_code
  - aql_result
  - carton_id
  - shipment_id
  - return_id
```

### F07.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원단·부자재 입고 | 원단: 직물(면·모·실크·합성), 편성물, 부직포, 레이스, denim. 부자재: 지퍼, 단추, 실, 라벨, 태그, 포장재. 입고 Lot(원단 Roll·Barcode Label)별 검사: 원단 폭·무게·색상 차이(dE<1)·Shrinkage/수축률·견뢰도. 공급사별 Lot 이력 관리. 부자재 인증(OEKO-TEX, GOTS, GRS). 창고 위치(Warehouse rack). 원단 검사: 육안/전자동 검사기(Fabric inspection: 장력·결함·얼룩·구멍·얼룩·purge·Bowing±). 정련·표백: Scouring(알칼리, 수축률 조정), Bleaching(과산화수소, 백도). 염색: Piece dyeing·Yarn dyeing·Garment dyeing(온도 60~130°C, 시간 30~120분, 염료 종류). Pre-shrinking(Sanforizing). Drying(Float dry→Stenter set). 파라미터: 수축률, 백도, pH, 강도. |
| 2 | 재단 | CAD 패턴(Cutting): Grading(S·M·L·XL), Marker making(원단 소재 배치율 80~92%). 자동 절단기(GERBER·Lectra·Kuris): 진동 나이프·Laser Cutter. 절단 속도(20~80m/min). Cutting plan ID, 원단 Roll No. Marking lot, 절단 부위 번호 부여. Lay plan(겹수 10~100장). 품번·사이즈·수량 스프레드시트. 원단 활용률(레코드). |
| 3 | 프린트·자수·가공 | 인쇄(Printing): Screen print(전사), Digital textile print(안료·반응성 염료, 속도 100~600m²/h), Sublimation(전사지 plus Hot press 180~220°C). 자수(Embroidery): 자수기(자동 6~20바늘, 300~1,000spm). 장식(Sequins·Rhinestones·Lace). 작업별 공정 시간, 불량률. Batch ID (커팅→봉제→자수→검사 연결). |
| 4 | 봉제·조립 | Sewing assembly: Overlock·Flatlock·Chainstitch·Coverstitch. 자동 재봉기. 봉제 라인(Flow·모듈러·번들). 작업자 속도(SAM: Standard Minute), 라인 밸런스(Balance chart). 니트(Knit whole garment·3D Knitting Seamless). 핸드메이드·고급 봉제. QC: Stitch length(bp), Seam strength, 패널 정렬·Symmetry. 작업자 ID·머신 ID 기록. |
| 5 | 세탁·후가공 | Pressing·Ironing: Steam iron·Flat press·Form finisher(풀빼기·주름 정리). Wash: Stone wash·Sand wash(desizing+softening). Finishing: Decatizing·Calendering·Ozone treatment. 최종 QC(Final inspection): 치수(±0.5cm), 외관, 봉제 결함, 파손, 오염. 불합격 긴급수선. Lot 단위 처방. 색상 변경: 염색조·파이프 Flush·Cleaning(알칼리/Na₂S₂O₄). 봉제 전환: Thread·Needle·부자재 교체(새 스타일). 다림질·프레스 기계 설정(온도·압력·스팀). 전환 승인(First off). 색상 변환 염색 시 Sample 승인, 불량 방지를 위한 염료 리스트 교체. |
| 6 | 중간검사 | 중간검사 단계에서 Lot·Batch·라인·검사 데이터를 연결한다. |
| 7 | 마감·다림질 | 마감·다림질 단계에서 Lot·Batch·라인·검사 데이터를 연결한다. |
| 8 | 최종 AQL 검사 | 금속 검출(Needle detector: 바늘 부서짐·포함 방지, Fe 0.8~1.2mm). 외관 검사: 색상 차이(Colorimeter dE<1.5), 원단 불량, 오염, 사이즈 불량. AQL(Acceptable Quality Level) 검사 기준(인라인·최종). 레벨 2.5(일반)~4.0(중요). 불량률 데이터(SCAR: Supplier Corrective Action Request). Sampling: 모든 사이즈·색상 포함. |
| 9 | 포장·라벨링 | 라벨·태그: Brand label·Hang tag·Size label·Care label·Price tag. RFID 태그 : 의류 단위 식별 및 재고 관리. 구성: 바코드(Brand/SKU/Supplier number). 자동 태깅기(1~2초/조립). Polybag packing(개별 각 폴리백). Folding·Boxing(의류 종류별). 로트 번호·수량·포장 리스트. 내부 포장(Folded→Polybag→Carton). 볼륨 포장(Carton packing: 12~24 pcs). 포장 조건(습기 방지·골판지 강도). Pallet 적층(Case 배치). Pallet ID·SSCC 발행. 혼재 방지 주문 확인. 포장 리스트·수량·중량·볼륨 기록. 온도(15~25°C)·습도(45~65% RH). 햇빛 차단(UV 필름). FEFO 기준. 주문 피킹: RF·Voice. 출하 검수. 재고 정확도(보증). 색상·사이즈별 할당. WMS/ERP 연동 팔레트·풀·사이즈 할당. |
| 10 | 출하·반품 추적 | ERP 수주 정보 기반 주문 할당. 바이어별(Whitman·Zara·Nike·Gucci) 출하 지시. Picking(품번·색상·사이즈·수량). 검품 후 출하 승인. EDI 전송(ASN·Invoice). 선적(LCL·FCL·항공). 원산지·세율·HS Code 서류 연결. AEO(Authorized Economic Operator) 제도. 시즌 말 재고: Off price·Outlet·재고 소각·기부. 품질 리콜(염료·봉제 결함·안전성). 파트너·공급사·고객 식별. 반품 검수(RMA·Credit memo). 시즌·색상·사이즈 노후화 관리. 폐기물 리사이클(Textile recycling). |

### F07.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 面料/辅料收货 | 在面料/辅料收货阶段关联批次、产线与检验数据。 |
| 2 | 裁剪 | 在裁剪阶段关联批次、产线与检验数据。 |
| 3 | 印花/绣花/加工 | 在印花/绣花/加工阶段关联批次、产线与检验数据。 |
| 4 | 缝制与组装 | 在缝制与组装阶段关联批次、产线与检验数据。 |
| 5 | 洗水与后整理 | 在洗水与后整理阶段关联批次、产线与检验数据。 |
| 6 | 中间检查 | 在中间检查阶段关联批次、产线与检验数据。 |
| 7 | 整烫与整理 | 在整烫与整理阶段关联批次、产线与检验数据。 |
| 8 | 最终AQL检查 | 在最终AQL检查阶段关联批次、产线与检验数据。 |
| 9 | 包装与贴标 | 在包装与贴标阶段关联批次、产线与检验数据。 |
| 10 | 出货与退货追溯 | 在出货与退货追溯阶段关联批次、产线与检验数据。 |

### F07.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | Style·Color·Size WIP 추적 | 1,2,4 | process_step | Variant WIP |
| 2 | 원단 Lot·색차·수축률 관리 | 1,3,5 | process_step | Fabric Quality |
| 3 | 외주·공정별 진척 가시화 | 3,4,5 | process_step | Outsourcing Progress |
| 4 | 봉제 불량·재작업 이력 관리 | 4,6,8 | process_step | Defect/Rework |
| 5 | AQL 검사와 출하 보류 연계 | 8,10 | process_step | AQL Gate |
| 6 | 반품 원인·Lot·작업조 추적 | 10 | process_step | Return Trace |

### F07.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 款式/颜色/尺码在制追溯 | 1,2,4 | process_step | Variant WIP |
| 2 | 面料批次、色差与缩水率管理 | 1,3,5 | process_step | Fabric Quality |
| 3 | 外协与工序进度可视化 | 3,4,5 | process_step | Outsourcing Progress |
| 4 | 缝制不良与返工履历管理 | 4,6,8 | process_step | Defect/Rework |
| 5 | AQL检查与出货暂挂联动 | 8,10 | process_step | AQL Gate |
| 6 | 退货原因、批次与班组追溯 | 10 | process_step | Return Trace |

### F07.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | fabric_lot, trim_lot, style_no, color_code |
| 2 | Cutting | batch |  |  | trim_lot, style_no, color_code, size_code |
| 3 | Decoration | process |  |  | style_no, color_code, size_code, cut_lot |
| 4 | Sewing | process | Bundle Flow Loop |  | color_code, size_code, cut_lot, bundle_id |
| 5 | Finishing | process |  |  | size_code, cut_lot, bundle_id, sewing_line_id |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | cut_lot, bundle_id, sewing_line_id, operation_id |
| 7 | Finishing | process |  |  | bundle_id, sewing_line_id, operation_id, wash_batch |
| 8 | QA Gate | gate |  | 1,2,3,4,5,6,7 | sewing_line_id, operation_id, wash_batch, defect_code |
| 9 | Packaging | process |  |  | operation_id, wash_batch, defect_code, aql_result |
| 10 | Shipment | process |  |  | wash_batch, defect_code, aql_result, carton_id |

### F07.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | fabric_lot, trim_lot, style_no, color_code |
| 2 | Cutting | batch |  |  | trim_lot, style_no, color_code, size_code |
| 3 | Decoration | process |  |  | style_no, color_code, size_code, cut_lot |
| 4 | Sewing | process | Bundle Flow Loop |  | color_code, size_code, cut_lot, bundle_id |
| 5 | Finishing | process |  |  | size_code, cut_lot, bundle_id, sewing_line_id |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | cut_lot, bundle_id, sewing_line_id, operation_id |
| 7 | Finishing | process |  |  | bundle_id, sewing_line_id, operation_id, wash_batch |
| 8 | QA Gate | gate |  | 1,2,3,4,5,6,7 | sewing_line_id, operation_id, wash_batch, defect_code |
| 9 | Packaging | process |  |  | operation_id, wash_batch, defect_code, aql_result |
| 10 | Shipment | process |  |  | wash_batch, defect_code, aql_result, carton_id |

### F07.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F07.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |


---

## F08 `consumer_goods` — 포장재·일반 소비재 / 包装材料与一般消费品

```yaml
code: "F08"
legacy_slug: "consumer_goods"
industry_group: "F"
industry_name_ko: "포장재·일반 소비재"
industry_name_zh: "包装材料与一般消费品"
routing: "RT_LINE_CONVERTING"
preset_id: "packaging_line_v1"
expression_tier: "v0.3_pflow_ready"
label_en: ""
label_ja: ""
data_capture_points:
  - material_lot
  - ink_lot
  - film_roll_id
  - mold_id
  - print_job_id
  - color_delta_e
  - coat_weight
  - drying_temp
  - slit_roll_id
  - vision_result
  - defect_code
  - sample_result
  - pack_lot
  - pallet_id
  - shipment_id
```

### F08.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원재료 입고 | 원료: 종이(골심지·라이너·백판지)·플라스틱(LDPE·PP·PET·EVOH Pellet·Film)·금속(Al·Tinplate·Steel coil)·유리(Soda-lime·Silica sand·Cullet). 잉크·코팅제·접착제·라미네이트 필름. 입고 Lot-COA-Batch 관리. 원재료 규격(종이 단위중량·PF·수분, 플라스틱 MFI·밀도·표면장력, 금속 경도·두께, 유리 점도). 저장 환경: 유지 온도·습도. 포장 전 고객 맞춤 작업 전 반제품 준비. |
| 2 | 인쇄·코팅 또는 성형 | 종이·판지: Corrugator(골심지·라이너 합지, 온도 170~230°C, 속도 100~300m/min→ Sheet→ Cut). 유리: Cullet+원료 계량→Batch 혼합→로(1,400~1,600°C 용융)→ Forming(Parison→Blow). 플라스틱: 압출(Blown film·Cast film·Sheet, 온도 180~250°C, extruder RPM, Cooling rate→Film). 금속: Coil→Slitting(절단)→Can body manufacturing(Welding→Flanging). 파라미터: 온도·압력·속도, Web tension, 건조 온도. 인쇄(Gravure: 150~600m/min, color registration ±0.1mm, CI Flexo: 200~400m/min, Digital HP Indigo·Xeikon 50~80m/min). UV/EB 코팅 : 광택·보호·열접착 배리어 기능(High-gloss, Matte).라미네이팅(드라이·무용제: PET/AL/PE/EVOH, Tension·온도·압력 조정).총 두께·밀도·표면장력(dyne) 확인. 코팅 온도·속도·점도 관리. LOT ID-용도 연결. 라인 전환: 잉크 색상 변화(Gravure cylinder·Anilox roll 교체·Doctor Blade). 인쇄기 Anilox roll·Chamber 세척(용제·물 + 초음파). 플라스틱 압출기 용융물 제거(Purging compound). 접착제·라미네이트 장치 세정(용제). 생산 라인 Code 교체(날짜·Lot). First-off 승인(인쇄 Register·색상 정확도 확인). 오염 유지·교체 주기 설정. |
| 3 | 건조·경화 | 종이/판지: 건조(Slot die Coating+Hot air drying 50~120°C). 플라스틱: Corona/Plasma 처리(표면 장력 38~52 dyne/cm). 금속: Lacquer coating(내부 도료 Bake 180~200°C·3~5분), Print coating(겉 도료). 유리: Annealing(Lehr, 500~600°C→100°C, 1~2hr 열응력 제거), Surface treatment(Cold end coating). 완전 경화 확인(MEK rub test·Cross hatch). |
| 4 | 슬리팅·절단 | 종이·판지: Sheeting/ Scoring(접는 선), Slotting(절개), Slitting(절단) → Blank 적층. 플라스틱 필름: Slitter rewinder(2~8회 절단 폭, 속도 100~600m/min). 접착제 도포(Hot melt·Water-based). 밀봉: 용기/상자 Sealing(Heat seal·Glue seal). 파우치: 3-side/4-side seal. 재단·스코어 정밀도(±0.5mm). 접착 강도(JIS 규격). |
| 5 | 조립·부착 | 종이: Die-cut(금형, 사양대로 절단·접착), Box forming(접착기·에어 피드). 플라스틱: Thermoforming(Sheet→가열→진공/압착 Forming→컷팅). 사출 성형(Kap·Preform·Container, 온도 200~300°C, 금형 온도 20~80°C, Holding pressure). 금속: Can making(변형·Flanging·Seaming). 유리: IS Machine(Non-stop 컨테이너). Die·Mold·Tool ID 추적. 각 제품 성형 공차 기록. |
| 6 | 인라인 외관검사 | 포장재: 두께(±0.01mm), 밀착도/Seal strength(표준 조건), 압축강도(BCT·ECT, 토마스), 인쇄 품질(dE<2, 등록 ±0.2mm). 유리: 치수·벽두께 편차·눈금선·Crack(Optical inspection). 금속: Seam integrity·Flange Weldability. 플라스틱: 두께·Sealing strength·Barrier test(산소 투 과도, 수분 투과도). Barcode/GUIN verify(Scan rate: >98%). Ink adhesion check. 불합격 시 Reject·Log. |
| 7 | 검수·샘플링 | 포장 완료품 Metal Detector(Fe 1.0·SUS 1.5mm)·X-ray(스크랩·박리). 중량·외관·Barcode 검사(Vision). 압축 강도·인열 강도·내충격 테스트(Sampling). 포장재 완제품 특성(Barrier·환경) 관리. 샘플 출력·고객 승인(AQL). Lot Pass/Fail 최종 기록. |
| 8 | 포장 | 완성된 포장재 제품 Packaging: Bundle/Stack→Carton→Case Pack. Pallet 적층(로봇·고속 포장기). Pallet ID·SSCC 발행. 혼재 방지(Lot 동일성·고객 납품 단위). 물류 Label 지정(수량·종류·중량). 적재 규정(내외부 안정성·PPWR 대비 포장 폐기물 저감). 수출 컨테이너 적재 계획. |
| 9 | 팔레타이징 | 포장재 특성에 맞춤: 종이·판지는 건조(20~30°C, 45~65% RH). 유리는 진동·충격 방지. 금속은 부식 방지(방청). 플라스틱은 UV 차단, 온도 15~30°C. 창고 재고 정확도 99%+. 유효기간(길이·중량·상품성) 모니터링. FEFO 정책(영구 관리). |
| 10 | 출하 | ERP 주문 할당(FEFO). 피킹(팔레트·케이스). 출하 검수(수량·종류·중량·Label). 포장재 검사 성적서 발급. 고객 포장 규격 확인. EDI 주문·출하 연동(ASN). 수출·내수 운송 계획. 인쇄 오류·규격 부적합 리콜(Lot-Batch-고객 출하처). 반품 원인 분석(생산 설비·재료·가공). 재가공(재절단·재인쇄·Down grade). 폐기물 관리(Scrap·재생 펄프·플라스틱 재생). 포장재 PPWR 규정 대응: 재생원료 비율·재활용 가능성·재사용 증빙. |

### F08.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原材料收货 | 在原材料收货阶段关联批次、产线与检验数据。 |
| 2 | 印刷/涂布或成型 | 在印刷/涂布或成型阶段关联批次、产线与检验数据。 |
| 3 | 干燥/固化 | 在干燥/固化阶段关联批次、产线与检验数据。 |
| 4 | 分切/裁切 | 在分切/裁切阶段关联批次、产线与检验数据。 |
| 5 | 组装/贴合 | 在组装/贴合阶段关联批次、产线与检验数据。 |
| 6 | 在线外观检查 | 在在线外观检查阶段关联批次、产线与检验数据。 |
| 7 | 检验与抽样 | 在检验与抽样阶段关联批次、产线与检验数据。 |
| 8 | 包装 | 在包装阶段关联批次、产线与检验数据。 |
| 9 | 码垛 | 在码垛阶段关联批次、产线与检验数据。 |
| 10 | 出货 | 在出货阶段关联批次、产线与检验数据。 |

### F08.3 control_points_detail_ko

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 원단·잉크·금형 Lot 연결 | 1,2 | process_step | Material Genealogy |
| 2 | 인쇄 색차·코팅량·건조조건 관리 | 2,3 | process_step | Print/Coating Quality |
| 3 | 슬리팅 Roll·Case 단위 추적 | 4,8,9 | process_step | Roll/Case Trace |
| 4 | 외관검사 Defect map과 불량코드 관리 | 6,7 | process_step | Vision Defect |
| 5 | 다SKU 전환·금형/판 교체 이력 | 2,5 | process_step | Changeover |
| 6 | 고객별 출하 Lot·클레임 역추적 | 9,10 | process_step | Customer Trace |

### F08.4 control_points_detail_zh

| # | text | step_refs | scope | category |
|---:|---|---|---|---|
| 1 | 基材、油墨、模具批次关联 | 1,2 | process_step | Material Genealogy |
| 2 | 印刷色差、涂布量与干燥条件管理 | 2,3 | process_step | Print/Coating Quality |
| 3 | 分切卷与箱单位追溯 | 4,8,9 | process_step | Roll/Case Trace |
| 4 | 外观检查缺陷图与不良代码管理 | 6,7 | process_step | Vision Defect |
| 5 | 多SKU切换与模具/版辊更换履历 | 2,5 | process_step | Changeover |
| 6 | 按客户出货批次与客诉反查 | 9,10 | process_step | Customer Trace |

### F08.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | material_lot, ink_lot, film_roll_id, mold_id |
| 2 | Converting | process |  |  | ink_lot, film_roll_id, mold_id, print_job_id |
| 3 | Converting | process | Converting Loop |  | film_roll_id, mold_id, print_job_id, color_delta_e |
| 4 | Converting | process |  |  | mold_id, print_job_id, color_delta_e, coat_weight |
| 5 | Assembly | process | Converting Loop |  | print_job_id, color_delta_e, coat_weight, drying_temp |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | color_delta_e, coat_weight, drying_temp, slit_roll_id |
| 7 | QA Gate | gate |  | 1,2,3,4,5,6 | coat_weight, drying_temp, slit_roll_id, vision_result |
| 8 | Packaging | process |  |  | drying_temp, slit_roll_id, vision_result, defect_code |
| 9 | Warehouse | process |  |  | slit_roll_id, vision_result, defect_code, sample_result |
| 10 | Shipment | process |  |  | vision_result, defect_code, sample_result, pack_lot |

### F08.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | material_lot, ink_lot, film_roll_id, mold_id |
| 2 | Converting | process |  |  | ink_lot, film_roll_id, mold_id, print_job_id |
| 3 | Converting | process | Converting Loop |  | film_roll_id, mold_id, print_job_id, color_delta_e |
| 4 | Converting | process |  |  | mold_id, print_job_id, color_delta_e, coat_weight |
| 5 | Assembly | process | Converting Loop |  | print_job_id, color_delta_e, coat_weight, drying_temp |
| 6 | Inline Gate | gate |  | 1,2,3,4,5 | color_delta_e, coat_weight, drying_temp, slit_roll_id |
| 7 | QA Gate | gate |  | 1,2,3,4,5,6 | coat_weight, drying_temp, slit_roll_id, vision_result |
| 8 | Packaging | process |  |  | drying_temp, slit_roll_id, vision_result, defect_code |
| 9 | Warehouse | process |  |  | slit_roll_id, vision_result, defect_code, sample_result |
| 10 | Shipment | process |  |  | vision_result, defect_code, sample_result, pack_lot |

### F08.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 계량·투입 확인 |
| 3 | 1 | Recipe/공정조건 확인 |
| 6 | 1 | Inline 검사 결과 판정 |
| 8 | 1 | QA Hold/Release 판정 |

### F08.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 称量与投料确认 |
| 3 | 1 | 配方/工艺条件确认 |
| 6 | 1 | 在线检查结果判定 |
| 8 | 1 | QA暂挂/放行判定 |

---

## 9. self-check

```
[x] F01~F08 전수, slug당 §N.1~§N.8 섹션 작성
[x] control_points_detail에 category 열 전건 작성
[x] step_expression ko/zh 행 수 = process_steps 행 수
[x] role=gate step에는 gate_for 작성
[x] trace_keys ⊆ data_capture_points
[x] ko/zh process_steps 행 수 동일
[x] ko/zh step_expression #, role, gate_for, trace_keys 동일
[x] control_points_detail ko/zh 행 수·step_refs·scope 동일
[x] en/ja 섹션 없음
[x] JSON·코드·스크립트 수정 없음
```

## 10. slug별 변경 요약

| code | 변경 요약 |
|---|---|
| F01 | 식품가공 Batch/CCP/금속검출/유통기한·리콜 추적 메타 추가 |
| F02 | 고속 충전라인, CIP/SIP, 충전량·캡토크·라벨 코드 검사 메타 추가 |
| F03 | 냉장 입고, 살균·발효, 콜드체인, 미생물 QA Release 메타 추가 |
| F04 | 반죽 Batch, 발효, 오븐 조건, 당일 생산·출하 메타 추가 |
| F05 | Formula, 계량, Bulk Hold, 충전·포장, 클레임 역추적 메타 추가 |
| F06 | 생활화학 배합·Tank, 충전·실링, 라인 클리어런스, 원단위/OEE 메타 추가 |
| F07 | Style/Color/Size, Cutting bundle, 봉제·AQL·반품 추적 메타 추가 |
| F08 | Roll/Material, 인쇄·코팅·슬리팅, Vision Defect, 고객별 출하 추적 메타 추가 |
