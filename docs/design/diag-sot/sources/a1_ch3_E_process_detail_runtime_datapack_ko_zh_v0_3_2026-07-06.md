# A1 Ch3 E산업 공정 상세 데이터팩 v0.3 (KO/ZH)

> 파일명: `a1_ch3_E_process_detail_runtime_datapack_ko_zh_v0_3_2026-07-06.md`  
> 작성일: 2026-07-06  
> 범위: E. 공정·화학(Process / Chemical) — E01~E08  
> 작성 규칙: B산업 리팩 지시서 v0.3 규격을 E산업에 적용. JSON·코드·스크립트 수정 없음.  
> 언어 정책: ko / zh만 작성. `label_en`, `label_ja`는 빈 문자열. en/ja 공정·관리점 섹션 작성 금지.

---

## 0. 작성 기준

- 본 데이터팩은 A1 Ch3 pflow가 소비하는 표현 메타를 포함한다.
- `process_steps_detail_ko/zh`: step, note의 기본 공정 흐름.
- `control_points_detail_ko/zh`: `category`, `text`, `step_refs`, `scope` 포함.
- `step_expression_ko/zh`: `module`, `role`, `loop_hint`, `gate_for`, `trace_keys` 포함.
- `operations_ko/zh`: drilldown 대상 step의 하위 실행 phase.
- `control_points_ko/zh` 별도 bullet 테이블은 작성하지 않는다. 필요 시 변환 규칙에서 자동 생성한다.
- `trace_keys`는 각 slug의 `data_capture_points` 부분집합으로 작성한다.

## 0.1 산업 반영 근거 요약

- ISA-88/S88 계열의 batch control 구조는 recipe, equipment hierarchy, procedure/operation/phase 분해를 기준으로 batch 공정 실행을 표준화한다.
- 공정산업 traceability는 원료 lot, recipe, batch record, tank/reactor history, in-process/lab result, 포장·출하 lot을 연결하는 방식이 핵심이다.
- 제약·정밀화학 계열은 Process Validation의 lifecycle, PPQ/CPV, 전자 Batch Record, deviation, QA release가 중요하다.
- 화학·소재 계열은 위험물, TSCA/REACH/GHS/MSDS, 저장·취급·폐기·배출 관리와 제조 lot의 연결이 필요하다.

## 0.2 slug 목록

| code | slug | label_ko | label_zh | routing | preset_id |
|---|---|---|---|---|---|
| E01 | `basic_chemicals` | 기초화학·무기/유기 원료 | 基础化学品·无机/有机原料 | RT_BATCH_CONTINUOUS | `process_batch_v1` |
| E02 | `petrochemical_refining` | 석유화학·정유·윤활유 | 石化·炼油·润滑油 | RT_CONTINUOUS_BATCH | `process_continuous_v1` |
| E03 | `specialty_chemicals` | 스페셜티 케미컬·첨가제 | 特种化学品·添加剂 | RT_BATCH | `process_batch_v1` |
| E04 | `fine_chemicals_api_intermediate` | 정밀화학·API 중간체 | 精细化学·API中间体 | RT_BATCH_GMP | `validated_batch_v1` |
| E05 | `paint_coating_adhesive_ink` | 도료·코팅·접착제·잉크 | 涂料·涂层·胶粘剂·油墨 | RT_BATCH | `process_batch_v1` |
| E06 | `polymer_resin_compound` | 수지·고무·컴파운드 | 树脂·橡胶·改性材料 | RT_BATCH_CONTINUOUS | `compound_extrusion_v1` |
| E07 | `glass_ceramic_powder` | 유리·세라믹·분말소재 | 玻璃·陶瓷·粉体材料 | RT_BATCH_HIGH_TEMP | `thermal_batch_v1` |
| E08 | `medical_materials_surface_treatment` | 의료기기용 소재·표면처리 | 医疗器械材料·表面处理 | RT_BATCH_REGULATED | `regulated_process_v1` |

---

## 1. E01 `basic_chemicals` — 기초화학·무기/유기 원료 / 基础化学品·无机/有机原料

```yaml
code: "E01"
legacy_slug: "basic_chemicals"
label_ko: "기초화학·무기/유기 원료"
label_zh: "基础化学品·无机/有机原料"
label_en: ""
label_ja: ""
routing: "RT_BATCH_CONTINUOUS"
flow_preset_id: "process_batch_v1"
expression_tier: "pflow_v0_3"
description_ko: "원료 저장, 계량, 반응, 분리·정제, 저장·출하가 이어지는 공정산업형 제조. Lot/Batch와 Tank/Vessel genealogy, Recipe version, 공정조건 CPV가 핵심이다."
description_zh: "以原料储存、称量、反应、分离精制、储运发货为主的流程制造。核心是Lot/Batch、Tank/Vessel genealogy、配方版本与过程条件持续验证。"
data_capture_points:
  - raw_lot_id
  - tank_id
  - vessel_id
  - batch_id
  - recipe_id
  - weigh_ticket
  - process_param
  - sample_id
  - lab_result
  - coa_id
  - shipment_lot
```

### 1.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원료 입고·검수 | 벌크 원료·첨가제를 입고하고 공급사 CoA, 위험물 등급, 보관 조건을 확인한다. 탱크로리(Tank lorry) 하역 시 질소 퍼지(N₂ Purging) 연결, 유량계(mass flow meter) 실시간 계량을 수행하며, 하역 파이프라인 라인 플러싱(Line flushing) 이력을 lot 단위로 기록한다. 입고 raw lot ID 발행 후 공급사 CoA의 순도·수분·비중 항목을 ERP/SRM과 자동 비교 검증한다. |
| 2 | 저장 Tank 배정 | 원료를 탱크·사일로·IBC에 배정하고 이전 lot 잔량과 혼합 가능성을 확인한다. 스테인리스(SUS304/316L) 또는 라이닝(Lining) 처리된 탱크에 질소 블랭킷(N₂ Blanket) 압력 0.5~1.0 barg, 온도 10~40°C, 레벨(Level) 20~80% 범위를 DCS에서 실시간 모니터링한다. Tank cleaning log(CIP/SIP)가 최신인지 batch 시작 전 확인하며, 동일 탱크에 이전 lot 잔량이 있을 경우 혼합 가능성을 Recipe version 기준으로 평가한다. |
| 3 | 계량·투입 준비 | Batch order 기준으로 원료 계량, 투입 순서, 설비 적격성, 작업자 권한을 확인한다. 로드셀(Load cell) 기반 계량 호퍼(Weigh hopper), 중간저장 호퍼(Intermediate Bulk Container), 계량 저울(Platform scale, 정밀도 ±0.1kg ~ ±1g)을 사용하며, 계량값과 Recipe 설정값 간 편차가 ±0.5% 이내여야 전자승인(Electronic Release)이 완료된다. 계량 데이터는 자동으로 weigh ticket에 기록되고 ERP/MES batch record와 연동된다. 작업자 인증(Card/ID Scanner, E-signature) 후 자동 밸브 시퀀스로 투입 준비가 완료된다. |
| 4 | 반응·혼합 | 반응기·혼합기에서 온도, 압력, pH, 교반, 투입 속도를 recipe 한계 내에서 제어한다. 재킷(Jacket) 방식 가열·냉각이 가능한 SUS316L/하스텔로이(Hastelloy) 재질 반응기(1~50m³)에서 온도 -10~250°C, 압력 -1~10 barg, 교반 속도(RPM, Anchor/Paddle/Turbine impeller) 50~500 RPM 범위를 DCS/PCS로 PID 제어한다. 투입 펌프(Progressing cavity pump, Diaphragm pump)의 유량(Flow rate)은 0.5~100 L/min 범위이며, 투입 순서 및 속도는 Recipe Phase에 따라 시퀀스 제어(Sequential control)된다. 반응 시점(Reaction endpoint)은 온도 곡선 변화(Thermal shift), pH 정체, GC 분석 등으로 판정하며, batch lot 단위로 모든 CPP를 자동 수집·저장한다. 본 공정은 Lot/Batch 추적 핵심 포인트이며, 주요 제품 사례로는 황산(H₂SO₄), 가성소다(NaOH), 에틸렌글리콜(EG), 아크릴산(AA) 등이 있다. |
| 5 | 분리·정제 | 여과, 증류, 세정, 탈수 등 단위조작을 통해 목표 순도와 수율을 확보한다. 필터 프레스(Filter press, 0.5~10µm), 원심분리기(Centrifuge, 1000~3000G), 증류탑(Distillation column, 이론단수 10~50단), 박막 증발기(Thin film evaporator), 추출기(Extraction column) 등이 사용된다. 증류 시 환류비(Reflux ratio) 0.5~5.0, 탑저온도(Bottom temp) 80~350°C, 탑정온도(Overhead temp) 40~200°C를 DCS로 제어한다. 분리 후 중간체 순도(In-process purity, GC/HPLC 면적%)가 Recipe下限(예: ≥95%)을 충족해야 다음 공정으로 이송된다. |
| 6 | 공정 중 샘플링 | 중간체 샘플을 채취하고 LIMS 결과로 다음 단계 진행 여부를 판정한다. 샘플링 포트(Sampling port, Quill type / Isolator type)에서 작업자 보호복(내화학성 장갑, 고글) 착용 후 무균·무오염 조건으로 채취한다. LIMS 의뢰 시 시험 항목(순도 GC/HPLC, 수분 KF, 점도 Brookfield, 비중, pH) 결과가 자동 수신되며, IPC Release 기준(예: 순도 ≥98.0%, 수분 ≤0.5%) 충족 시 DCS/MES에 Pass Flag가 자동 전송된다. 불합격 시 공정 Hold 상태로 전환되며, Deviation/OOS 절차가 트리거된다. Gate(Inspection) 포인트로서 Step 4,5의 진행을 제어한다. |
| 7 | 저장·Aging | 완제품 또는 중간체를 지정 탱크에서 안정화하고 보관 조건을 모니터링한다. SUS304 또는 라이닝 탱크(50~500m³)에서 질소 블랭킷 유지, 온도 15~40°C, 레벨 모니터링(레이더 레벨 게이지/서보 레벨 게이지)을 실시한다. Aging 기간(24~168시간) 동안 점도, 색상(Gardner/APHA color), 안정성(Sedimentation/분리 여부)을 주기적으로 확인하며, Tank genealogy(투입 lot, 잔량, 혼합 비율)를 batch record에 기록한다. |
| 8 | 최종 QC·CoA | 최종 규격 시험, CoA 발행, 규격 외 결과(OOS) 여부를 검토한다. 완제품 시험 항목(순도 GC/HPLC ≥99.5%, 수분 KF ≤0.1%, 중금속 ICP-OES, 색상, 밀도, 산가/수산화가)에 대해 2회 병행 시험(Duplicate test)을 수행한다. LIMS 결과가 모든 규격(Spec)을 충족하면 CoA가 자동 생성되고 QA 전자승인(Electronic QA Release) 후 출하 가능 상태가 된다. OOS 발생 시 Lab Investigation(LIR)·Full OOS Investigation 절차가 트리거되며, Deviation ID가 발행되어 batch record에 연결된다. |
| 9 | 충전·포장 | 드럼, IBC, 탱크로리 등 포장 단위에 충전하고 라벨·중량·위험물 표기를 확인한다. 자동 충전기(Auto filler, Mass flow meter/Coriolis meter 기반, 정밀도 ±0.1%), 드럼 캡핑(Capping)·팔레타이징(Palletizing) 로봇이 사용된다. 포장 단위별 Net weight (±0.5% 이내), Label(제품명, Lot No., 중량, 위험물 등급 UN No., GHS pictogram), Barcode/Sensor 기반 자동검증을 수행한다. 위험물 인화점(Flash point), MSDS 정보가 Label에 반영되었는지 최종 확인 후 Pallet 단위 Lot/Serial 번호를 생성한다. |
| 10 | 출하·Batch 종료 | 출하 lot과 고객 주문을 연결하고 batch record, 수율, deviation을 마감한다. 출하 중량대(Weighbridge)에서 차량 총중량·공차중량 계량, ERP/SAP 자동 전송, Custody transfer 문서(송장, packing list, CoA, MSDS)를 생성한다. Lot/Batch/Serial 추적을 위해 출하 lot ID와 고객 주문(Purchase Order)을 ERP에서 1:1 연결한다. 최종 Batch record review(수율 분석: 실제 수율 vs 이론 수율 ±5% 이내, 에너지 소비 kWh/kg, 원료 소비 kg/kg, Deviation 목록, 재작업 이력)를 완료하고 MES batch close 처리를 수행한다. |

### 1.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料收货与检验 | 接收大宗原料和添加剂，确认供应商CoA、危险品等级及储存条件。槽车卸料时连接氮气吹扫(N₂ Purging)，通过质量流量计(Mass flow meter)实时计量，管路吹扫(Line flushing)记录按lot保存。入厂raw lot ID生成后，自动与ERP/SRM比对供应商CoA的纯度、水分、比重等指标。 |
| 2 | 储罐分配 | 将原料分配到储罐、料仓或IBC，并确认前批残留与混批可行性。在SUS304/316L或衬里储罐中维持氮封(N₂ Blanket)压力0.5~1.0 barg、温度10~40°C、液位(Level)20~80%，由DCS实时监控。批次启动前确认储罐清洗记录(CIP/SIP)在有效期内，若同一罐内有前批余量，根据Recipe版本评估混批可行性。 |
| 3 | 称量与投料准备 | 按批生产指令确认原料称量、投料顺序、设备适用性和人员权限。使用基于称重传感器(Load cell)的称量料斗(Weigh hopper)、中间容器(IBC)和平台秤(Platform scale，精度±0.1kg~±1g)，称量值与配方设定值偏差在±0.5%以内方可电子放行(Electronic Release)。称量数据自动写入weigh ticket并与ERP/MES批记录联动。操作员经身份认证(Card/ID Scanner、E-signature)后自动阀门顺序进入投料待机状态。 |
| 4 | 反应与混合 | 在反应釜或混合机内控制温度、压力、pH、搅拌和投料速度，使其处于配方限值内。使用SUS316L/哈氏合金(Hastelloy)夹套反应釜(1~50m³)，温度-10~250°C、压力-1~10 barg、搅拌转速(RPM，Anchor/Paddle/Turbine叶轮)50~500 RPM，由DCS/PCS进行PID控制。投料泵(Progressing cavity pump、Diaphragm pump)流量0.5~100 L/min，投料顺序与速度按Recipe Phase顺序控制。反应终点(Reaction endpoint)通过温度拐点(Thermal shift)、pH稳定、GC分析等判断，所有CPP按batch lot自动采集储存。本工序为Lot/Batch追溯核心节点，代表产品如硫酸(H₂SO₄)、烧碱(NaOH)、乙二醇(EG)、丙烯酸(AA)等。 |
| 5 | 分离与精制 | 通过过滤、蒸馏、洗涤、脱水等单元操作确保目标纯度和收率。使用板框压滤机(Filter press，0.5~10µm)、离心机(Centrifuge，1000~3000G)、蒸馏塔(Distillation column，理论板数10~50块)、薄膜蒸发器(Thin film evaporator)、萃取塔(Extraction column)等。蒸馏时回流比(Reflux ratio)0.5~5.0、塔底温度(Bottom temp)80~350°C、塔顶温度(Overhead temp)40~200°C由DCS控制。分离后中间体纯度(In-process purity，GC/HPLC面积%)须满足Recipe下限(如≥95%)方可进入下一工序。 |
| 6 | 过程取样 | 采集中间体样品，并依据LIMS结果判断是否进入下一步骤。在取样口(Sampling port，Quill type/Isolator type)由操作员穿戴防护服(耐化手套、护目镜)以无菌无污染方式取样。LIMS委托检验项目(纯度GC/HPLC、水分KF、粘度Brookfield、比重、pH)结果自动返回，满足IPC放行标准(如纯度≥98.0%、水分≤0.5%)时DCS/MES自动接收Pass Flag。不合格时工序转入Hold状态，触发Deviation/OOS程序。作为Gate(Inspection)节点，控制Step 4、5的进程。 |
| 7 | 储存与熟化 | 将成品或中间体在指定储罐中稳定化，并监控储存条件。在SUS304或衬里储罐(50~500m³)中维持氮封、温度15~40°C、液位监控(雷达液位计/伺服液位计)。熟化期(24~168小时)内定期检查粘度、色度(Gardner/APHA色号)、稳定性(沉降/分层情况)，并将Tank genealogy(投入lot、余量、混合比例)记入批记录。 |
| 8 | 最终QC与CoA | 执行最终规格测试，签发CoA，并审核OOS风险。成品检验项目(纯度GC/HPLC≥99.5%、水分KF≤0.1%、重金属ICP-OES、色度、密度、酸值/羟值)进行平行双样(Duplicate test)检测。LIMS结果满足所有规格(Spec)时CoA自动生成并经QA电子放行(Electronic QA Release)后达到发货状态。OOS发生时触发实验室调查(LIR)和全面OOS调查程序，Deviation ID生成并关联到批记录。 |
| 9 | 灌装与包装 | 按桶、IBC或槽车等包装单元灌装，确认标签、重量和危险品标识。使用自动灌装机(Auto filler，基于质量流量计/科氏力流量计，精度±0.1%)、桶盖压合(Capping)、码垛(Palletizing)机器人。每包装单元净重(Net weight±0.5%以内)、标签(品名、Lot No.、重量、危险品等级UN No.、GHS象形图)通过Barcode/Sensor自动验证。最终确认危险品闪点(Flash point)和MSDS信息已在标签上体现后生成Pallet级Lot/Serial号。 |
| 10 | 发货与批次关闭 | 将发货批次与客户订单关联，关闭批记录、收率和偏差。通过地磅(Weighbridge)称量车总重与皮重，数据自动上传ERP/SAP，生成交接计量文件(发票、装箱单、CoA、MSDS)。Lot/Batch/Serial追溯通过ERP将发货lot ID与客户采购订单(Purchase Order)进行1:1关联。完成最终批记录审核(收率分析：实际收率vs理论收率±5%以内、能耗kWh/kg、原料消耗kg/kg、偏差清单、返工历史)后执行MES批次关闭处理。 |

### 1.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| 원료·공급사 추적 | 공급사 CoA, raw lot, 탱크 투입 이력을 batch record와 연결해야 한다. ERP/SRM에서 공급사 인증(Supplier Qualification) 상태를 Every Lot 단위로 조회하며, 입고 시 CoA 항목(순도 GC/HPLC ≥99.0%, 수분 KF ≤0.5%)을 자동 비교한다. 불일치 시 입고 차단(Hold) 후 품질 검토(Quality Review) 절차 진행. | 1,2 | process_step |
| Tank genealogy | 탱크 잔량, 혼합, cleaning 상태가 최종 lot에 어떤 영향을 주는지 추적해야 한다. Tank level transmitter(Radar/Servo, 정밀도 ±1mm)를 통해 실시간(Real-time) 잔량 모니터링하며, CIP/SIP Log(최종 cleaning 일시, cleaning agent 농도)를 Batch 시작 전 검증한다. 혼합 비율(Mix ratio)이 Recipe 허용 범위(±5%)를 벗어나면 Deviation 처리. | 2,7 | process_step |
| Recipe·투입 순서 | 투입 순서와 recipe version 불일치가 수율·품질 이상으로 이어지므로 전자승인과 이탈관리가 필요하다. DCS/PLC Sequence Controller에서 Recipe Phase별 승인된 투입 순서만 실행 가능하도록 Interlock 설정. 작업자 E-signature로 투입 전 이중 확인(Double Check)을 Every Batch 수행. 순서 이탈(Sequence deviation) 발생 시 자동 Alarm + Batch Hold. | 3,4 | process_step |
| 반응조건 관리 | 온도·압력·pH·교반 등 critical process parameter를 한계값과 trend로 관리한다. DCS Historian에서 CPP를 1초~1분 주기(Real-time)로 자동 수집하며, 상한/하한(LSL/USL) 초과 시 자동 Alarm + Trend 분석 대시보드 연동. 예: 반응온도 80±5°C, 압력 2±0.5 barg, 교반 200±20 RPM. Limit excursion 발생 시 CPP Deviation Record 자동 생성. | 4 | process_step |
| 시험·Release Gate | 중간·최종 시험 결과가 없으면 다음 단계와 출하를 차단해야 한다. LIMS에서 IPC 시험 결과(순도, 수분, 점도 등)가 자동 수신되고 MES Gate 규칙(Spec Pass/Fail)에 따라 Pass 시 자동 Release Flag 생성, Fail 시 Batch Hold + E-mail/알림 발송. Every Batch 단위 Gate Release 적용. | 6,8 | process_step |
| 위험물·EHS | MSDS, 위험물 등급, 보관 조건, 폐수·배출 관리와 제조 lot을 연결한다. GHS 분류(인화성, 부식성, 독성 등), MSDS 문서 버전(최신 Rev. 확인), 저장탱크 방류벽(Dike/Bund) 상태, 폐수 전처리(pH 조정 6~9, COD/BOD 분석) 이력을 lot별 연결. 화학물질 배출량(TRI/배출 인벤토리)을 Batch 단위로 추적 및 보고. | 1,7,9 | industry |
| Batch Record 마감 | 수율, deviation, 재작업, CoA, 출하 lot을 batch 단위로 닫아야 한다. MES Batch Close 시 수율 분석(실제/이론 비율 ±5% 이내), Deviation 건수(0건 권장), 재작업 이력(rework batch ID 연결), CoA 발행 완료 여부, 출하 lot ID(E2E 연결)를 검증한다. 모든 조건 충족 시 eBR 최종 Lock + QA 전자서명 완료. | 10 | process_step |

### 1.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| 原料与供应商追溯 | 供应商CoA、原料批次和储罐投料记录必须与批记录关联。通过ERP/SRM每批次(Lot)查询供应商认证(Supplier Qualification)状态，收货时自动比对CoA项目(纯度GC/HPLC≥99.0%、水分KF≤0.5%)。不一致时拦截收货并进入质量审核(Quality Review)程序。 | 1,2 | process_step |
| 储罐族谱 | 需要追踪储罐余量、混批和清洗状态对最终批次的影响。通过储罐液位变送器(Radar/Servo，精度±1mm)实时(Real-time)监控余量，批次启动前验证CIP/SIP记录(最近清洗时间、清洗剂浓度)。混合比例(Mix ratio)超出配方允许范围(±5%)时执行偏差处理。 | 2,7 | process_step |
| 配方与投料顺序 | 投料顺序和配方版本不一致会导致收率和质量异常，需要电子审批与偏差管理。DCS/PLC顺序控制器按Recipe Phase仅允许执行已批准的投料顺序，Interlock锁定。操作员电子签名双人复核(Double Check)每批次执行。顺序偏离(Sequence deviation)发生时自动报警+批次暂停(Batch Hold)。 | 3,4 | process_step |
| 反应条件管理 | 温度、压力、pH、搅拌等关键过程参数需按限值和趋势管理。DCS Historian按1秒~1分钟周期实时(Real-time)自动采集CPP，超过上下限(LSL/USL)时自动报警+趋势分析仪表板联动。例如：反应温度80±5°C、压力2±0.5 barg、搅拌200±20 RPM。限值偏离(Limit excursion)时CPP偏差记录自动生成。 | 4 | process_step |
| 检验与放行关口 | 无中间或最终检验结果时，应阻断后续步骤和发货。LIMS自动接收IPC检验结果(纯度、水分、粘度等)，MES Gate规则(Spec Pass/Fail)判定：Pass时自动生成Release Flag，Fail时批次暂停(Batch Hold)+邮件/通知发送。每批次(Every Batch)执行Gate放行。 | 6,8 | process_step |
| 危险品与EHS | MSDS、危险品等级、储存条件、废水和排放管理需与制造批次关联。GHS分类(易燃、腐蚀、有毒等)、MSDS文件版本(确认最新版)、储罐围堰(Dike/Bund)状态、废水预处理(pH调节6~9、COD/BOD分析)记录按批次关联。化学品排放量(TRI/排放清单)按批次跟踪报告。 | 1,7,9 | industry |
| 批记录关闭 | 收率、偏差、返工、CoA和发货批次必须按批次关闭。MES批次关闭(Batch Close)时验证收率分析(实际/理论比例±5%以内)、偏差件数(建议0件)、返工历史(关联返工批次ID)、CoA签发状态、发货批次ID(E2E关联)。所有条件满足后eBR最终锁定(Lock)+QA电子签名完成。 | 10 | process_step |

### 1.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_lot_id,coa_id |
| 2 | Storage | utility |  |  | tank_id,raw_lot_id |
| 3 | Weighing | batch |  |  | batch_id,recipe_id,weigh_ticket |
| 4 | Reaction | batch | Reaction Hold / Rework Loop |  | vessel_id,batch_id,recipe_id,process_param |
| 5 | Separation | process |  |  | batch_id,process_param |
| 6 | IPC Gate | gate |  | 4,5 | sample_id,lab_result,batch_id |
| 7 | Storage | utility |  |  | tank_id,batch_id,process_param |
| 8 | QC Gate | gate |  | 6,7 | sample_id,lab_result,coa_id |
| 9 | Packaging | process |  |  | batch_id,shipment_lot |
| 10 | Disposition | process |  |  | batch_id,coa_id,shipment_lot |

### 1.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Inbound | process |  |  | raw_lot_id,coa_id |
| 2 | Storage | utility |  |  | tank_id,raw_lot_id |
| 3 | Weighing | batch |  |  | batch_id,recipe_id,weigh_ticket |
| 4 | Reaction | batch | Reaction Hold / Rework Loop |  | vessel_id,batch_id,recipe_id,process_param |
| 5 | Separation | process |  |  | batch_id,process_param |
| 6 | IPC Gate | gate |  | 4,5 | sample_id,lab_result,batch_id |
| 7 | Storage | utility |  |  | tank_id,batch_id,process_param |
| 8 | QC Gate | gate |  | 6,7 | sample_id,lab_result,coa_id |
| 9 | Packaging | process |  |  | batch_id,shipment_lot |
| 10 | Disposition | process |  |  | batch_id,coa_id,shipment_lot |

### 1.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 원료 순차 투입 |
| 4 | 2 | 승온·반응 유지 |
| 4 | 3 | 냉각·종료 판정 |
| 6 | 1 | 샘플 채취 |
| 6 | 2 | LIMS 시험 의뢰 |
| 8 | 1 | 최종 규격 검토 |
| 10 | 1 | Batch record review |

### 1.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 原料顺序投料 |
| 4 | 2 | 升温与反应保持 |
| 4 | 3 | 冷却与终点判定 |
| 6 | 1 | 过程取样 |
| 6 | 2 | LIMS检验委托 |
| 8 | 1 | 最终规格审核 |
| 10 | 1 | 批记录审核 |

---

## 2. E02 `petrochemical_refining` — 석유화학·정유·윤활유 / 石化·炼油·润滑油

```yaml
code: "E02"
legacy_slug: "petrochemical_refining"
label_ko: "석유화학·정유·윤활유"
label_zh: "石化·炼油·润滑油"
label_en: ""
label_ja: ""
routing: "RT_CONTINUOUS_BATCH"
flow_preset_id: "process_continuous_v1"
expression_tier: "pflow_v0_3"
description_ko: "연속 공정과 저장·Blend·출하가 결합된 산업. Unit operation, tank farm, blend recipe, 품질 release, custody transfer 추적이 핵심이다."
description_zh: "连续装置与储运、调和、发货结合的行业。核心是单元装置、罐区、调和配方、质量放行和交接计量追溯。"
data_capture_points:
  - feed_lot_id
  - unit_id
  - stream_id
  - tank_id
  - blend_id
  - recipe_id
  - process_param
  - sample_id
  - lab_result
  - custody_meter
  - shipment_lot
```

### 2.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Feedstock 수급·분석 | 원유·나프타·기초유 등 feedstock 품질, 공급 lot, 저장 tank를 확인한다. 탱크로리/파이프라인/선박(Barge)으로 입고 시 샘플링(자동 샘플러/ASTM D4057) 후 API 비중(ASTM D287), 황 함량(ASTM D4294, 0.5~3.5%), 수분(KF, ASTM E1064), 염분(ASTM D3230)을 분석한다. 분석 결과는 Feedstock Blend Recipe 배정에 반영되며, Lot ID 기반 ERP/MES 연동. 대표 제품: 원유(CFD), 나프타(Naphtha), 등유(Kerosene), 중유(HFO). |
| 2 | 전처리·분류 | 탈염, 예열, 분류 등 전처리 조건과 unit 부하를 관리한다. 탈염기(Desalter, 전기식/혼합식)에서 온도 120~150°C, 압력 10~15 barg, 탈염수 주입량 3~8%로 원유 중 염분/고형물 제거. 예열기(Preheat train, Shell & Tube HX)에서 150~350°C로 승온 후 상압증류탑(Atm. Distillation Column, 30~50단)으로 이송. Column Feed 온도, Overhead/ Bottom 온도, 압력 강하(Delta P)를 DCS에서 연속 모니터링. AI 기반 APC(Advanced Process Control)가 적용된 경우, Unit 부하를 실시간으로 최적화하여 에너지 소비 최대 5% 절감. |
| 3 | 반응·전환 Unit | Cracking, reforming, hydrotreating 등 unit 조건을 운전 한계 내에서 관리한다. FCC(Fluid Catalytic Cracking) Unit: 반응기 온도 480~550°C, 압력 1~3 barg, 촉매/오일 비율(C/O ratio) 5~10, 재생기 온도 650~750°C. Hydrotreater(수첨탈황): 반응기 온도 300~400°C, 압력 30~100 barg, H₂ 분압 10~50 barg, LHSV 0.5~5 hr⁻¹. Reformer(접촉개질): 반응기 온도 480~530°C, 압력 3~15 barg, WHSV 1~5 hr⁻¹. 각 Unit의 촉매 순환율(Catalyst circulation rate), 압력차(Delta P), Bed 온도 Profile을 Historian에 1초 주기 저장. 주요 제품: FCC 가솔린, LPG, 경유(Diesel), 중질유(HCO), 바이오 연료 Co-processing 적용 확대. |
| 4 | 분리·분획 | 증류·분리 결과 stream별 수율과 품질을 확인한다. 상압증류탑(Atmospheric Column, 40~50단)에서 나프타·등유·경유·상압잔사유(AR)로 분획. 진공증류탑(Vacuum Column, 60~90 mmHgA)에서 VGO·VR로 추가 분리. 각 Side draw Stream에 대해 ASTM D86/D1160 증류 특성, API 비중, 유황 함량을 In-line Analyzer(Gas Chromatograph, NIR Analyzer)로 실시간 분석. 주입량 대비 각 Stream 수율(Mass Yield, Vol%)를 DCS/MES에서 Every Hour 집계. |
| 5 | Tank Farm 이송 | 중간 stream과 제품을 지정 탱크로 이송하고 탱크 genealogy를 생성한다. Pipeline/Battery Limit Valve를 통해 API 650/620 규격 플로팅루프(Floating Roof) 또는 콘루프(Cone Roof) 탱크(1,000~100,000m³)로 이송. Tank Level Transmitter(Radar, Servo), 온도(평균 온도 RTD), 밀도(자동 온라인 밀도계)를 실시간 모니터링. 이송 유량(Mass flow meter / PD meter) 적산값을 Tank 입고량에 반영하고, Tank Genealogy(Stream ID → Tank ID, 투입량, 혼합 비율, 체류 시간)를 MES에 기록. |
| 6 | Blend Recipe 실행 | 고객·제품 규격에 맞춰 blend recipe, 첨가제, 탱크 잔량을 반영한다. In-line Blending System(Static Mixer + Flow Controller)에서 각 Component(Multi-stream) 유량을 Coriolis/PG Flow Meter로 실시간 제어. Blend Recipe는 ASTM D4814(가솔린) 또는 EN 590(경유) 등 제품 규격에 따라 옥탄가(RON 91~98), 세탄가(CN 40~55), 증류 특성, 황 함량, 산화 안정성을 만족하도록 설계. 첨가제(Cetane Improver, Antioxidant, Detergent)는 Micro-metering Pump로 정밀 주입. Blend Batch ID 생성 후 실험실 분석(Every Batch)으로 최종 규격 확인. |
| 7 | In-line/랩 품질검사 | 점도, 황, 수분, 밀도 등 규격을 검사하고 release 여부를 판정한다. In-line Analyzer(Gas Chromatograph, NIR, Sulfur Analyzer, Density Meter)가 1~10분 주기로 연속 분석. 실험실 확인(Every Batch)은 시험 항목(점도 ASTM D445 @40°C, 황 ASTM D4294 ≥10ppm, 수분 ASTM D6304 ≤200ppm, 밀도 ASTM D4052 @15°C, RVP ASTM D6378)에 대해 수행. Release Gate: 모든 항목이 규격 이내이면 MES Auto Release; 1항목 이상 Off-spec 시 Blend Batch Hold + 재처리(Re-blend) 또는 Downgrade 판정. |
| 8 | 충전·Bulk 출하 | 탱크로리, 배관, 드럼, 선적 등 출하 단위와 계량 결과를 기록한다. 탱크로리 출하(Truck Loading Rack): Bottom/Submerged Loading Arm, Coriolis Mass Flow Meter (±0.1%), Vapor Recovery Unit(VRU) 운전. 배관 출하(Pipeline Transfer): SCADA 계량(Custody Meter, Prover Calibration 주기, 누적량). 선적(Marine Loading): Marine Loading Arm, 선박 탱크 게이지, Vapor Balance. 출하 중량/체적 계량값은 자동으로 ERP에 전송되고, 출하 lot ID와 연결. |
| 9 | Custody Transfer | 계량기, seal, 출하 문서, 고객 주문을 연결한다. Custody Meter(PD Meter / Coriolis Meter, ±0.1~0.2% 정밀도)의 Seal 번호/검정 일자 확인. 출하 문서(Bill of Lading, Packing List, CoA, Certificate of Quality/Quantity)를 ERP에서 생성하고, Custody Transfer Report(출하량, 온도 보정 계수, API CTW/CTL)를 자동 출력. Seal 번호와 계량기 누적값을 사진·스캔 기록으로 보존하며, 고객 주문 번호(Sales Order)와 출하 lot을 1:1 연결. |
| 10 | 운전 실적·Loss 마감 | 수율, off-spec, energy, flare/loss를 마감하고 개선 분석에 반영한다. Material Balance(Input vs Output ±1% 이내)를 Unit/Tank/Period별로 산출하여 Loss(공정 로스, Tank 증발 Loss, Flare, 드레인)를 확인. Energy 소비(Steam Mton, Power MWh, Fuel Gas Nm³)를 생산량(ton) 기준으로 집계(Every Shift/Every Day). AI 기반 예지보전(Predictive Maintenance) 시스템이 OEE 15% 개선 목표로 Unit 정지 원인을 분석. 주요 KPI: Yield(수율%), Energy Intensity(에너지 원단위), Loss Ratio(로스율%), On-spec Ratio(적합률%). |

### 2.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料接收与分析 | 确认原油、石脑油或基础油等原料质量、供应批次和储罐。通过槽车/管线/船舶(Barge)收货时取样(自动采样器/ASTM D4057)，分析API比重(ASTM D287)、硫含量(ASTM D4294，0.5~3.5%)、水分(KF，ASTM E1064)、盐分(ASTM D3230)。分析结果用于原料调配配方，Lot ID与ERP/MES联动。代表产品：原油(CFD)、石脑油(Naphtha)、煤油(Kerosene)、重油(HFO)。 |
| 2 | 预处理与分馏准备 | 管理脱盐、预热、分馏等预处理条件和装置负荷。在电脱盐器(Desalter，电混合式)中温度120~150°C、压力10~15 barg、注水率3~8%去除原油中盐分/固体。预热系统(Preheat train，管壳式换热器)升温至150~350°C后送入常压蒸馏塔(Atm. Distillation Column，30~50块塔板)。塔进料温度、顶/底温度、压降(Delta P)由DCS连续监控。应用AI基APC(先进过程控制)时装置负荷实时优化，能耗最高降低5%。 |
| 3 | 反应与转化装置 | 在操作边界内管理裂化、重整、加氢等装置条件。FCC(流化催化裂化)：反应器温度480~550°C、压力1~3 barg、剂油比(C/O ratio)5~10、再生器温度650~750°C。加氢处理器(Hydrotreater)：反应器温度300~400°C、压力30~100 barg、H₂分压10~50 barg、LHSV 0.5~5 hr⁻¹。重整装置(Reformer)：反应器温度480~530°C、压力3~15 barg、WHSV 1~5 hr⁻¹。各装置催化剂循环率、压差(Delta P)、床层温度曲线以1秒周期存入Historian。主要产品：FCC汽油、LPG、柴油(Diesel)、重循环油(HCO)，生物燃料Co-processing应用扩大。 |
| 4 | 分离与馏分 | 确认各物流的收率和质量。常压蒸馏塔(Atmospheric Column，40~50块塔板)分离出石脑油、煤油、柴油、常压渣油(AR)。减压蒸馏塔(Vacuum Column，60~90 mmHgA)进一步分离VGO和VR。各侧线馏分通过在线分析仪(气相色谱、NIR分析仪)实时分析ASTM D86/D1160馏程、API比重、硫含量。进料量与各物流收率(Mass Yield，Vol%)由DCS/MES每小时(Every Hour)汇总。 |
| 5 | 罐区转运 | 将中间物流和产品转入指定储罐，并形成储罐族谱。通过管线/电池界限阀运至API 650/620规格浮顶(Floating Roof)或拱顶(Cone Roof)储罐(1,000~100,000m³)。雷达液位计/伺服液位计、温度(平均温度RTD)、密度(在线密度计)实时监控。转运流量(质量流量计/容积式流量计)累积值计入储罐入库量，Tank Genealogy(Stream ID→Tank ID、投入量、混合比例、停留时间)记录于MES。 |
| 6 | 调和配方执行 | 按客户和产品规格执行调和配方、添加剂和罐内余量管理。在线调和系统(静态混合器+流量控制器)中各组分(Multi-stream)流量由科氏力/容积式流量计实时控制。调和配方按ASTM D4814(汽油)或EN 590(柴油)等产品规格满足辛烷值(RON 91~98)、十六烷值(CN 40~55)、馏程、硫含量、氧化安定性。添加剂(十六烷改进剂、抗氧化剂、清净剂)通过微量计量泵精确注入。调和Batch ID生成后经实验室分析(Every Batch)确认最终规格。 |
| 7 | 在线/实验室质量检验 | 检测粘度、硫、水分、密度等规格并判断放行。在线分析仪(气相色谱、NIR、硫分析仪、密度计)以1~10分钟周期连续分析。实验室确认(Every Batch)检测项目：粘度ASTM D445 @40°C、硫ASTM D4294≥10ppm、水分ASTM D6304≤200ppm、密度ASTM D4052 @15°C、雷德蒸气压ASTM D6378。放行关口：全部规格合格则MES Auto Release；一项以上Off-spec则调和批次暂停(Batch Hold)+再调和(Re-blend)或降级(Downgrade)判定。 |
| 8 | 灌装与散装发货 | 记录槽车、管线、桶装或船运等发货单元和计量结果。槽车发货(Truck Loading Rack)：底部/淹没式装车臂、科氏力质量流量计(±0.1%)、油气回收装置(VRU)运行。管线发货(Pipeline Transfer)：SCADA交接计量(Custody Meter，检定周期Prover Calibration、累积量)。船运发货(Marine Loading)：船用装油臂、船舱液位计、Vapor Balance。发货重量/体积计量值自动上传ERP并关联发货lot ID。 |
| 9 | 交接计量 | 关联计量仪表、铅封、发货文件和客户订单。确认交接计量表(PD Meter/科氏力流量计，精度±0.1~0.2%)的铅封号/检定日期。在ERP中生成发货文件(提单、装箱单、CoA、质量/数量证书)，自动输出交接计量报告(发货量、温度补偿系数、API CTW/CTL)。铅封号与计量表累积值以照片/扫描件保存，客户订单号(Sales Order)与发货lot进行1:1关联。 |
| 10 | 运行绩效与损耗关闭 | 关闭收率、off-spec、能耗、放空/损耗，并用于改善分析。按装置/储罐/期间计算物料平衡(Input vs Output±1%以内)，确认损耗(工艺损失、储罐蒸发Loss、放空、排水)。能耗(蒸汽Mton、电力MWh、燃料气Nm³)按产量(吨)基准汇总(每班/每天)。AI基预测维护(Predictive Maintenance)系统以OEE提升15%为目标分析装置停机原因。主要KPI：收率(Yield%)、能源单耗(Energy Intensity)、损耗率(Loss Ratio%)、合格率(On-spec Ratio%)。 |

### 2.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| Feedstock 품질 | 원료 성상 차이가 전 공정 수율과 off-spec에 영향을 주므로 입고 분석과 tank 배정을 연결한다. 매 로트(Every Lot) 분석 항목: API 비중(ASTM D287), 황(ASTM D4294), 수분(KF, ASTM E1064), 염분(ASTM D3230), 증류(ASTM D86). 분석 결과가 Tank Blend Recipe 허용 범위(예: API 30~40°)를 벗어나면 Tank 배정을 차단하고 별도 Tank에 격리(Isolate) 후 공급사 품질 검토 요청. | 1,2 | process_step |
| Unit condition trend | 연속 unit의 압력·온도·유량 trend와 alarm 이력을 lot/stream 기준으로 보존한다. DCS Historian에 1초~1분 주기로 모든 PV(Process Variable)를 저장하며, APC(Advanced Process Control) 적용 시 CPP(온도 ±5°C, 압력 ±0.5 barg, 유량 ±2%) 제어 편차를 실시간(Real-time) 모니터링. CPP 이탈 시 Alarm + Shift Log 기록 + Unit Manager Notification. | 3,4 | process_step |
| Tank/Stream genealogy | stream, tank, blend 간 이력을 추적해 품질 이슈 발생 시 영향 범위를 산정한다. Tank Level Transmitter(Radar, 정밀도 ±1mm) + 온도(RTD, 정밀도 ±0.1°C)로 실시간(Real-time) Tank Inventory 기록. Blend Recipe 실행 시 각 Stream ID와 Tank ID 간 Genealogy Tree를 자동 생성. Off-spec 발생 시 Genealogy 역추적으로 영향을 받은 Tank/Blend Lot 범위를 30분 이내에 특정 가능. | 4,5,6 | process_step |
| Blend recipe control | Blend recipe, 첨가제, 탱크 잔량, 고객 규격을 한 번에 검증해야 한다. Every Batch Blend 전 Component Tank 잔량(Level), 첨가제 Lot 번호/유효기간 확인. Coriolis Flow Meter(±0.1%) 유량 제어값과 Recipe 설정값 간 편차 ±1% 이내 검증. Product Spec(RON, CN, Viscosity, Sulfur, RVP)을 Blend Recipe 예측값과 비교하여 자동 Release/Reject 판정. | 6 | process_step |
| Quality release | 실험실 결과와 온라인 분석기를 출하 release gate로 연결한다. Lab 분석 주기: Every Batch (또는 4시간 주기) + Online Analyzer 연속(Continuous) 모니터링. LIMS 결과(점도, 황, 수분, 밀도)와 In-line Analyzer(Gas Chromatograph, NIR) 결과의 Cross-validation 수행. 모든 Spec Pass 시 MES 자동 Release + CoA 자동 생성. 1항목 이상 Fail 시 Batch Hold + QA Notification. | 7,8 | process_step |
| Custody·계량 | 출하 계량, seal, 차량·선박 정보는 매출·품질 클레임 근거가 된다. Custody Meter(PD Meter / Coriolis) ±0.1~0.2% 정밀도, 교정 주기(Certified Prover Calibration, 3~6개월). Seal 번호, 계량기 적산값, 온도·압력 보정(ASTM Table 54/60)을 Every 출하 단위로 기록. 차량번호·운전자·선박명·Barge ID를 ERP 출하 lot과 연결. | 8,9 | process_step |
| Loss/Energy 관리 | 공정 loss, flare, utility consumption을 batch/period 기준으로 분석한다. Material Balance(Input - Output = Inventory Change + Loss)를 Every Shift 산출하여 예상 Loss(증발 Loss, Flare량, 드레인)와 실제 Loss 차이 분석. Energy Intensity(TOE/ton product)를 Every Day 집계하여 기준 대비 5% 이상 초과 시 에너지 진단(Energy Audit) 실시. 탄소 배출량(Tier 1~3) 추적도 통합, CO₂ 오차 1% 이내. | 10 | industry |

### 2.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| 原料质量 | 原料性质差异会影响全流程收率和off-spec，需要关联入厂分析与储罐分配。每批次(Every Lot)分析项目：API比重(ASTM D287)、硫(ASTM D4294)、水分(KF，ASTM E1064)、盐分(ASTM D3230)、馏程(ASTM D86)。分析结果超出储罐调配配方允许范围(如API 30~40°)时阻断入罐分配，隔离至单独储罐并请求供应商质量审核。 | 1,2 | process_step |
| 装置条件趋势 | 连续装置的压力、温度、流量趋势和报警历史应按lot/stream保存。DCS Historian以1秒~1分钟周期保存所有PV(过程值)，应用APC时CPP(温度±5°C、压力±0.5 barg、流量±2%)控制偏差实时(Real-time)监控。CPP偏离时报警+日志记录+装置主管通知。 | 3,4 | process_step |
| 罐/物流族谱 | 追踪stream、tank与blend关系，以便质量异常时计算影响范围。通过雷达液位计(精度±1mm)+温度RTD(精度±0.1°C)实时(Real-time)记录储罐库存。Blend配方执行时各Stream ID与Tank ID之间的族谱树(Genealogy Tree)自动生成。Off-spec发生时通过族谱逆向追溯在30分钟内确定受影响Tank/Blend Lot范围。 | 4,5,6 | process_step |
| 调和配方控制 | 调和配方、添加剂、罐内余量和客户规格需同步验证。每批次(Every Batch)调和前确认组分罐余量(Level)、添加剂批次号/有效期。科氏力流量计(±0.1%)流量控制值与配方设定值偏差±1%以内验证。产品规格(RON、CN、粘度、硫、RVP)与Blend配方预测值比对后自动判断Release/Reject。 | 6 | process_step |
| 质量放行 | 将实验室结果和在线分析仪连接为发货放行关口。实验室分析频率：每批次(Every Batch)或每4小时+在线分析仪连续(Continuous)监控。LIMS结果(粘度、硫、水分、密度)与在线分析仪(气相色谱、NIR)结果交叉验证(Cross-validation)。全部规格通过时MES自动放行(Auto Release)+CoA自动签发。一项以上Fail时批次暂停+QA通知。 | 7,8 | process_step |
| 交接与计量 | 发货计量、铅封、车辆/船舶信息是结算与质量索赔依据。交接计量表(PD Meter/科氏力流量计)精度±0.1~0.2%，检定周期(Certified Prover Calibration，3~6个月)。铅封号、计量表累积值、温度压力补偿(ASTM Table 54/60)每发货单元记录。车牌号/司机/船名/Barge ID与ERP发货lot关联。 | 8,9 | process_step |
| 损耗与能耗管理 | 按批次或期间分析工艺损耗、放空和公用工程消耗。每班(Every Shift)计算物料平衡(Input - Output = 库存变化 + 损耗)，分析预期损耗(蒸发Loss、放空量、排水)与实际损耗差异。能源单耗(TOE/吨产品)每天(Every Day)汇总，超过基准5%以上时进行能源诊断(Energy Audit)。碳排放(Tier 1~3)追溯集成，CO₂误差1%以内。 | 10 | industry |

### 2.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Feed | process |  |  | feed_lot_id,tank_id |
| 2 | Pretreat | process |  |  | unit_id,process_param |
| 3 | Conversion | process | Unit Condition Loop |  | unit_id,stream_id,process_param |
| 4 | Separation | process |  |  | stream_id,process_param |
| 5 | Tank Farm | utility |  |  | tank_id,stream_id |
| 6 | Blend | batch |  |  | blend_id,recipe_id,tank_id |
| 7 | QC Gate | gate |  | 5,6 | sample_id,lab_result,blend_id |
| 8 | Shipment | process |  |  | shipment_lot,custody_meter |
| 9 | Custody | gate |  | 8 | custody_meter,shipment_lot |
| 10 | Performance | process |  |  | unit_id,process_param |

### 2.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Feed | process |  |  | feed_lot_id,tank_id |
| 2 | Pretreat | process |  |  | unit_id,process_param |
| 3 | Conversion | process | Unit Condition Loop |  | unit_id,stream_id,process_param |
| 4 | Separation | process |  |  | stream_id,process_param |
| 5 | Tank Farm | utility |  |  | tank_id,stream_id |
| 6 | Blend | batch |  |  | blend_id,recipe_id,tank_id |
| 7 | QC Gate | gate |  | 5,6 | sample_id,lab_result,blend_id |
| 8 | Shipment | process |  |  | shipment_lot,custody_meter |
| 9 | Custody | gate |  | 8 | custody_meter,shipment_lot |
| 10 | Performance | process |  |  | unit_id,process_param |

### 2.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 3 | 1 | 운전 조건 세트 확인 |
| 6 | 1 | Blend recipe 선택 |
| 6 | 2 | 첨가제 투입 |
| 7 | 1 | Lab 결과 수신 |
| 9 | 1 | 계량·Seal 확인 |

### 2.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 3 | 1 | 确认操作条件集 |
| 6 | 1 | 选择调和配方 |
| 6 | 2 | 添加剂投加 |
| 7 | 1 | 接收实验室结果 |
| 9 | 1 | 确认计量与铅封 |

---

## 3. E03 `specialty_chemicals` — 스페셜티 케미컬·첨가제 / 特种化学品·添加剂

```yaml
code: "E03"
legacy_slug: "specialty_chemicals"
label_ko: "스페셜티 케미컬·첨가제"
label_zh: "特种化学品·添加剂"
label_en: ""
label_ja: ""
routing: "RT_BATCH"
flow_preset_id: "process_batch_v1"
expression_tier: "pflow_v0_3"
description_ko: "고객별 배합, 소량다품종, 잦은 recipe 변경이 특징. 원료 계량, batch phase, 실험실 승인, 재작업과 포장 lot 추적이 중요하다."
description_zh: "具有客户配方、小批量多品种和频繁配方变更特点。关键是原料称量、批阶段、实验室批准、返工和包装批次追溯。"
data_capture_points:
  - customer_spec_id
  - raw_lot_id
  - batch_id
  - recipe_id
  - scale_id
  - vessel_id
  - process_param
  - sample_id
  - lab_result
  - rework_id
  - package_lot
  - coa_id
```

### 3.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객 Spec·Recipe 확인 | 고객별 규격, 원료 대체 가능성, recipe version을 확인한다. 고객 Spec Sheet(점도, 색상(Gardner/APHA), 고형분, 산가, 인화점, 첨가제 조성)를 ERP/CRM과 연동해 Recipe Master에 반영. Recipe Version 관리(R01.00→R01.01 변경 시 Change Control 승인 필요). 대표 제품: 소광제(Matting agent), 소포제(Defoamer), UV 흡수제, 가소제(Plasticizer), 가교제(Crosslinker), PVC 안정제. |
| 2 | 원료 피킹·계량 | 소량 원료와 첨가제를 저울·Barcode 기반으로 계량한다. 정밀 전자저울(Platform scale / Top-loading balance, 정밀도 ±0.01g~±1g)과 Barcode Scanner로 원료 Lot Traceability 확보. 원료 피킹 리스트(Picking list) 기반으로 투입용기(Pre-weigh container)에 계량 후 Double check(2차 Barcode 검증). 계량값은 자동 Scada/MES 전송되며, Recipe 편차 ±0.5% 초과 시 경고. |
| 3 | Pre-mix·분산 | 분산기, 혼합기에서 순서와 속도에 맞춰 pre-mix를 수행한다. 고속분산기(High-speed disperser, 500~3000 RPM) 또는 교반조(Anchor/Paddle mixer, 50~500 RPM)에서 액상/분체 원료 순차 투입. 온도 모니터링(분산 열로 인한 온도 상승: 40~80°C 제한)과 분산시간(5~30분) 관리. 점도(포(杯)형 점도계/Brookfield) 중간 확인. |
| 4 | 주반응·합성 | 반응기에서 투입 순서, 온도, 압력, 시간, 촉매 투입을 제어한다. SUS316L/Glass-lined 반응기(500L~20m³)에서 온도 -10~200°C, 압력 -1~6 barg, 교반 속도 50~300 RPM. Catalyst injection(정량 펌프, 0.1~10 L/min) 시점을 Recipe Step에 따라 시퀀스 제어. 온도 램프(Ramp rate 0.5~5°C/min), pH 변화, 반응 발열(Exotherm)을 DCS Historian에 기록. CPAI(2025) 사례: 배치 반응기 MPC(Model Predictive Control) 적용으로 일관성 15% 향상. |
| 5 | 숙성·Stabilization | 점도, 산가, 색상 등 물성 안정화를 위한 aging을 수행한다. Aging Tank(Jacket 탱크, 500L~10m³)에서 온도 20~80°C, 교반 30~100 RPM 유지, Aging 시간(2~48시간). 현장 점도 측정(Brookfield viscometer, ASTM D2196) 1~2시간 간격, 산가(Titration, ASTM D974) 4~8시간 간격. 온라인 NIR/Vis 센서로 색상(Gardner/APHA) 연속 모니터링 적용 가능. |
| 6 | 중간검사·보정 | 랩 결과에 따라 추가 투입, 희석, 재작업 여부를 결정한다. Lab(GC/HPLC, 비색계, Karl Fischer, Viscometer) 분석 결과(순도, 고형분, 점도, 수분, 색상)를 LIMS로 수신. 목표 규격 대비 부족 시 보정(희석용제 추가, 농축, 색상 보정 안료 투입) 지시를 MES에서 생성. 보정량은 Batch Recipe에 Deviation ID로 기록. 보정 후 재시험 → Pass 시 다음 단계. |
| 7 | 여과·탈포 | 불순물, 겔, 기포를 제거하고 포장 전 상태를 안정화한다. 필터(Filter bag 1~100µm, Filter cartridge 0.5~50µm, 자기여과기 Magnetic filter) 여과압력(Delta P 0.5~2 barg 초과 시 Filter 교체). 진공탈포(Vacuum degassing, -0.8~-1.0 barg, 10~30분)로 용존 기포 제거. Filter lot 번호, Mesh, 교체 일시를 Batch record에 기록. |
| 8 | 최종검사·승인 | 고객 spec별 최종 시험과 CoA 승인 여부를 판정한다. 시험 항목: 점도(Brookfield ASTM D2196, 20~60°C), 고형분(NV%, 105°C/1h), 산가(ASTM D974, mgKOH/g), 색상(Gardner/APHA), 수분(KF, ppm), 밀도(ASTM D4052), 인화점(Pensky-Martens, ASTM D93). LIMS 결과 고객 Spec 모두 Pass 시 CoA 자동 생성 → QA 전자승인. OOS 발생 시 Investigation → 추가 시험 또는 폐기 결정. |
| 9 | 소분·라벨링 | 고객 포장단위로 소분하고 label, shelf-life, 위험물 정보를 확인한다. 자동충전기(Auger filler / Piston filler, 정밀도 ±0.5~1.0%)로 1kg 캔~200kg 드럼 단위 충전. Label(제품명, Batch No., 제조일, 유통기한, 위험물 UN No., GHS pictogram, MSDS URL QR code) 자동 인쇄·부착. Package lot ID(Barcode)를 Batch ID와 1:N 연결. |
| 10 | Batch Review·출하 | batch record, deviation, rework, 출하 lot을 마감한다. 모든 전자기록(계량, 반응조건, Lab 결과, 여과, 보정, 포장)을 Batch record로 취합. Yield analysis(이론 대비 실제 수율 ±10% 이내), Deviation(건수, 원인, 조치), Rework history(rework batch ID 연결) 검증. 모든 조건 충족 시 E-Signature로 Batch Close + CoA 최종 발행 → ERP 출하 lot 연결. |

### 3.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户规格与配方确认 | 确认客户规格、原料替代规则和配方版本。客户规格表(粘度、色度Gardner/APHA、固含、酸值、闪点、添加剂组成)与ERP/CRM联动后反映至Recipe Master。配方版本管理(R01.00→R01.01变更需Change Control批准)。代表产品：消光剂(Matting agent)、消泡剂(Defoamer)、UV吸收剂、增塑剂(Plasticizer)、交联剂(Crosslinker)、PVC稳定剂。 |
| 2 | 原料拣配与称量 | 通过电子秤和条码称量小批量原料和添加剂。精密电子秤(Platform scale / Top-loading balance，精度±0.01g~±1g)与条码扫描器确保原料Lot Traceability。按拣配单(Picking list)在投料容器(Pre-weigh container)中称量后双重复核(二次条码验证)。称量值自动上传Scada/MES，配方偏差±0.5%超出时报警。 |
| 3 | 预混与分散 | 按顺序和转速在分散机或混合机内执行预混。高速分散机(High-speed disperser，500~3000 RPM)或搅拌罐(Anchor/Paddle mixer，50~500 RPM)中顺序投入液体/粉体原料。温度监控(分散发热限制40~80°C)与分散时间(5~30分钟)管理。中间粘度测量(杯式粘度计/Brookfield)。 |
| 4 | 主反应与合成 | 在反应釜内控制投料顺序、温度、压力、时间和催化剂投加。SUS316L/搪玻璃反应釜(500L~20m³)，温度-10~200°C、压力-1~6 barg、搅拌转速50~300 RPM。催化剂注入(计量泵，0.1~10 L/min)时间按Recipe Step顺序控制。升温速率(Ramp rate 0.5~5°C/min)、pH变化、反应放热(Exotherm)记录于DCS Historian。CPAI 2025案例：批次反应釜MPC(模型预测控制)应用使一致性提高15%。 |
| 5 | 熟化与稳定 | 通过aging使粘度、酸值、颜色等物性稳定。熟化罐(夹套储罐，500L~10m³)，温度20~80°C、搅拌30~100 RPM保持，熟化时间(2~48小时)。现场粘度测量(Brookfield，ASTM D2196)每1~2小时，酸值(滴定，ASTM D974)每4~8小时。在线NIR/Vis色度传感器连续监控(Gardner/APHA)可应用。 |
| 6 | 中间检验与调整 | 依据实验室结果决定补加、稀释或返工。Lab(GC/HPLC、色差计、Karl Fischer、粘度计)分析结果(纯度、固含、粘度、水分、色度)经LIMS接收。未达到目标规格时生成调整指令(MES中)，偏差ID记录为Batch Recipe一部分。调整后复测→Pass后进入下一工序。 |
| 7 | 过滤与脱泡 | 去除杂质、凝胶和气泡，稳定包装前状态。过滤器(Filter袋1~100µm、滤芯0.5~50µm、磁性过滤器Magnetic filter)过滤压力(Delta P 0.5~2 barg超时更换滤芯)。真空脱泡(Vacuum degassing，-0.8~-1.0 barg，10~30分钟)去除溶解气泡。滤芯批次号、目数、更换时间记入批记录。 |
| 8 | 最终检验与批准 | 按客户规格执行最终测试并判断CoA批准。检验项目：粘度(Brookfield ASTM D2196，20~60°C)、固含(NV%，105°C/1h)、酸值(ASTM D974，mgKOH/g)、色度(Gardner/APHA)、水分(KF，ppm)、密度(ASTM D4052)、闪点(Pensky-Martens，ASTM D93)。LIMS结果全部满足客户规格时CoA自动生成→QA电子放行。OOS发生时调查→追加检验或报废决定。 |
| 9 | 分装与标签 | 按客户包装单位分装，确认标签、保质期和危险品信息。自动灌装机(Auger filler/Piston filler，精度±0.5~1.0%)按1kg罐~200kg桶单位灌装。标签(品名、Batch No.、生产日期、保质期、危险品UN No.、GHS象形图、MSDS URL二维码)自动打印粘贴。Package lot ID(Barcode)与Batch ID进行1:N关联。 |
| 10 | 批审核与发货 | 关闭批记录、偏差、返工和发货批次。所有电子记录(称量、反应条件、Lab结果、过滤、调整、包装)汇总至批记录。收率分析(理论vs实际收率±10%以内)、偏差(件数、原因、措施)、返工历史(关联返工批次ID)验证。条件全部满足后E-Signature进行批次关闭+Batch Close+CoA最终签发→ERP发货lot关联。 |

### 3.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| 고객 Spec 동기화 | 고객 spec, recipe, 시험항목이 불일치하면 승인·클레임 문제가 발생한다. ERP/CRM의 고객 Spec Master와 Recipe Master를 Batch 발행 전(Every Batch) 자동 비교. Spec 변경 시 Change Control 절차를 통해 Recipe Version 업데이트. 고객별 CoA 포맷(언어, 항목, 허용 오차) 템플릿 관리. | 1,8 | process_step |
| 정밀 계량 | 소량 첨가제 계량 오차가 성능 편차로 직결되므로 scale calibration과 double check가 필요하다. 전자저울 Calibration 주기(주 1회 또는 매 사용 전 Span/Zero Check). Every Batch 계량값과 Recipe 설정값 편차 ±0.5% 이내 검증. 2차 Operator가 Barcode로 원료 종류 및 중량 재확인(Double Check). 이상 시 Scale Isolation + Calibration 재수행. | 2 | process_step |
| Recipe phase 실행 | 혼합·반응 phase별 파라미터와 작업자 개입을 전자기록으로 남긴다. DCS/PLC Sequence Controller에서 Recipe Phase(Pre-mix→Reaction→Aging)별 CPP(온도, RPM, 시간, 투입량)를 실시간(Real-time) 자동 수집. 작업자 수동 개입(Manual override) 시 전자서명(E-signature) + Comment 필수 기록. Phase 완료 시 자동 다음 Phase 전환. | 3,4 | process_step |
| Lab feedback loop | 중간검사 결과에 따라 보정·재작업 경로를 관리한다. LIMS 결과(점도, 고형분, 색상) 수신 시간: 30~60분 이내. Off-spec 시 MES에서 자동 Adjustment Order 생성(희석/보강량 계산). Rework 배치(Batch)는 Rework ID 발행 후 원 Batch ID와 1:N Genealogy 연결. 보정 후 재시험 → Pass 시까지 Loop 반복. | 6 | process_step |
| 여과·오염 관리 | 필터 lot, mesh, 압력 차, cleaning 상태를 batch에 연결한다. Filter 교체 시 Filter Lot/Batch 번호, Mesh(µm), 교체 시간을 MES에 기록. Delta P(차압 트랜스미터) 0.5~2 barg 초과 시 자동 Filter 교체 Alarm. Cleaning Log(최종 Cleaning 일시, 용제/세제 종류) Batch 시작 전 확인. | 7 | process_step |
| 고객별 CoA | 고객별 시험 규격과 CoA 문구를 자동 생성·승인한다. LIMS 결과(고객별 Spec) Pass 시 CoA Template(고객별 문구, 언어, 로고) 자동 적용. CoA 전자승인(QA E-signature) 후 ERP 전송. 고객 포털(EDI/Web) 자동 Upload 가능. | 8,9 | process_step |
| 재작업 이력 | Rework 투입량과 원 batch 이력을 최종 batch genealogy에 남긴다. 원 Batch ID(Base Batch) + Rework ID(R01, R02...)로 Genealogy Tree 구성. Rework 투입량(kg, L), 투입일시, 사유(Deviation ID) 기록. 최종 Batch record에 Rework History Section 포함. | 6,10 | industry |

### 3.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| 客户规格同步 | 客户规格、配方和检验项目不一致会导致放行和客诉问题。批次发放前(Every Batch)自动比对ERP/CRM的客户Spec Master与Recipe Master。Spec变更时通过Change Control程序更新Recipe Version。客户化CoA格式(语言、项目、允差)模板管理。 | 1,8 | process_step |
| 精密称量 | 少量添加剂称量误差会直接造成性能波动，需要电子秤校准和双人复核。电子秤校准周期(每周1次或每次使用前Span/Zero Check)。每批次(Every Batch)称量值与配方设定值偏差±0.5%以内验证。二次操作员通过条码双重确认原料种类和重量(Double Check)。异常时隔离秤具并重新校准。 | 2 | process_step |
| 配方阶段执行 | 按混合、反应阶段记录参数和人工干预。DCS/PLC顺序控制器按Recipe Phase(Pre-mix→Reaction→Aging)实时(Real-time)自动采集CPP(温度、RPM、时间、投料量)。操作员手动干预(Manual override)时需电子签名(E-signature)+备注记录。Phase完成后自动切换至下一Phase。 | 3,4 | process_step |
| 实验室反馈回路 | 依据中间检验结果管理调整和返工路径。LIMS结果(粘度、固含、色度)接收时间：30~60分钟内。Off-spec时MES自动生成调整指令(稀释/补加量计算)。返工批次(Rework Batch)发放Rework ID后与原始Batch ID进行1:N Genealogy关联。调整后复测→Pass前循环。 | 6 | process_step |
| 过滤与污染控制 | 将滤芯批次、目数、压差和清洗状态关联到批次。滤芯更换时记录Filter Lot/Batch号、目数(µm)、更换时间于MES。Delta P(差压变送器)超过0.5~2 barg时自动更换滤芯报警。批次启动前确认清洗记录(Cleaning Log，最后清洗时间、溶剂/洗涤剂种类)。 | 7 | process_step |
| 客户化CoA | 按客户检验规格自动生成并批准CoA。LIMS结果(客户Spec)全部Pass时CoA模板(客户化用语、语言、Logo)自动应用。CoA电子放行(QA E-signature)后发送至ERP。支持自动上传客户门户(EDI/Web)。 | 8,9 | process_step |
| 返工历史 | 返工投入量和原批次历史必须进入最终批次族谱。原始Batch ID(Base Batch)+Rework ID(R01、R02…)构成Genealogy Tree。记录返工投入量(kg、L)、投入时间、原因(Deviation ID)。最终批记录包含返工历史章节(Rework History Section)。 | 6,10 | industry |

### 3.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | customer_spec_id,recipe_id |
| 2 | Weighing | batch |  |  | raw_lot_id,batch_id,scale_id |
| 3 | Premix | batch |  |  | batch_id,vessel_id,process_param |
| 4 | Reaction | batch | Adjustment / Rework Loop |  | batch_id,recipe_id,vessel_id,process_param |
| 5 | Aging | process |  |  | batch_id,process_param |
| 6 | IPC Gate | gate |  | 3,4,5 | sample_id,lab_result,batch_id |
| 7 | Filtration | process |  |  | batch_id,process_param |
| 8 | QC Gate | gate |  | 6,7 | sample_id,lab_result,coa_id |
| 9 | Packaging | process |  |  | package_lot,batch_id |
| 10 | Review | process |  |  | batch_id,rework_id,package_lot,coa_id |

### 3.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | customer_spec_id,recipe_id |
| 2 | Weighing | batch |  |  | raw_lot_id,batch_id,scale_id |
| 3 | Premix | batch |  |  | batch_id,vessel_id,process_param |
| 4 | Reaction | batch | Adjustment / Rework Loop |  | batch_id,recipe_id,vessel_id,process_param |
| 5 | Aging | process |  |  | batch_id,process_param |
| 6 | IPC Gate | gate |  | 3,4,5 | sample_id,lab_result,batch_id |
| 7 | Filtration | process |  |  | batch_id,process_param |
| 8 | QC Gate | gate |  | 6,7 | sample_id,lab_result,coa_id |
| 9 | Packaging | process |  |  | package_lot,batch_id |
| 10 | Review | process |  |  | batch_id,rework_id,package_lot,coa_id |

### 3.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 원료 barcode 확인 |
| 2 | 2 | 계량값 자동수집 |
| 4 | 1 | 투입 순서 실행 |
| 6 | 1 | 보정 지시 생성 |
| 8 | 1 | 고객 Spec 비교 |

### 3.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 原料条码确认 |
| 2 | 2 | 称量值自动采集 |
| 4 | 1 | 执行投料顺序 |
| 6 | 1 | 生成调整指令 |
| 8 | 1 | 客户规格比对 |

---

## 4. E04 `fine_chemicals_api_intermediate` — 정밀화학·API 중간체 / 精细化学·API中间体

```yaml
code: "E04"
legacy_slug: "fine_chemicals_api_intermediate"
label_ko: "정밀화학·API 중간체"
label_zh: "精细化学·API中间体"
label_en: ""
label_ja: ""
routing: "RT_BATCH_GMP"
flow_preset_id: "validated_batch_v1"
expression_tier: "pflow_v0_3"
description_ko: "고순도 반응, 중간체 관리, GMP/비GMP 경계, 공정검증과 전자 Batch Record가 중요하다."
description_zh: "重视高纯反应、中间体管理、GMP/非GMP边界、工艺验证和电子批记录。"
data_capture_points:
  - material_lot
  - batch_id
  - recipe_id
  - equipment_id
  - cleaning_status
  - process_param
  - sample_id
  - lab_result
  - deviation_id
  - ebr_id
  - release_status
  - coa_id
```

### 4.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | MBR/Batch 지시 승인 | Master Batch Record와 생산 batch 지시, 설비·작업자 적격성을 확인한다. MBR Version Control(Rev 관리, 변경 시 Change Control 승인 + PPQ 재검증 필요)을 ERP/PLM에서 관리. Batch 지시에는 Recipe ID, 대상 설비(Reactor ID, Tank ID), 작업자 교육(Certification) 이력, 필요한 청정도 등급(ISO Class 7~8)이 포함. CPV(Critical Process Validation) 기준: FDA 21 CFR Part 11 / EU ANNEX 15 준수. 대표 제품: API 중간체(아세트아미노펜, 이부프로펜, 아토르바스타틴 중간체), GMP 정밀화학 중간체. |
| 2 | 원료 Dispensing | 원료 lot, 유효기간, 계량값, 이중확인을 전자기록화한다. GMP Dispensing Booth(HEPA 필터, ISO Class 7) 내에서 정밀 전자저울(Mettler Toledo/Sartorius, ±0.01g~±1g) 사용. 원료 Lot ID Scanning으로 유효기간(Expiry Date) 자동 검증, 유효기간 초과 시 Dispensing 차단(Hold). 계량 Double Check(Operator + Supervisor E-signature) → Weigh Ticket 자동 출력. 물질수지(Material Balance)를 Batch별로 계산하여 투입량 대비 Loss 0.5% 이내 검증. |
| 3 | 합성 반응 | 반응 온도, 시간, 투입 순서, 촉매, endpoint를 recipe와 비교한다. Glass-lined / SUS316L 반응기(100L~10m³)에서 온도 -20~200°C, 압력 -1~6 barg, 교반 50~400 RPM, Jacket 온도 PID 제어. CPP: 온도(설정값 ±5°C), 압력(±0.2 barg), 교반 속도(±20 RPM), 투입 속도(mL/min), pH(±0.3). 반응 Endpoint(TLC/In-process HPLC 면적%) 기준 Recipe 설정값(예: 출발물질 ≤1.0%) 충족 시까지 반응 유지. 모든 CPP를 DCS Historian에 1초~1분 주기 Real-time 저장. |
| 4 | Quench·Work-up | 반응 종료 후 quench, 추출, 세정 등 work-up 조건을 기록한다. Quench 용액(물, 산/염기 용액, 유기용제) 투입 속도(Temperature control, 0.5~10°C/min), Quench 후 pH 목표 범위(예: pH 3~5) 확인. Liquid-liquid Extraction(분액 깔때기/추출탑, Solvent/Aqueous ratio Recipe 지정). Washing(순수/염수/중탄산나트륨, 횟수 Recipe 지정). Quench 및 Work-up 조건(온도, 시간, pH, 층 분리 완료 여부)을 DCS/PLC Sequence Controller로 자동 기록. |
| 5 | 분리·정제 | 결정화, 여과, 건조, chromatography 등 정제 조건을 관리한다. 결정화(Crystallization): 냉각 속도(Cooling rate 0.1~2°C/min), 용매 조성(Antisolvent addition), Seeding 온도·량. 여과(Nutsche filter / Agitated Nutsche Filter Dryer(ANFD) / Centrifuge, 1000~2000G): 여과 시간, Cake 두께, Washing 용매량·횟수. 건조(ANFD / Vacuum Tray Dryer / Fluid Bed Dryer): 온도 40~80°C, 진공도 -0.8~-1.0 barg, 건조 시간. Chromatography(Column, Prep HPLC): 이동상 조성, 유속, 검출 파장, Fraction 수집 window. |
| 6 | In-process Test | IPC 시험 결과로 다음 단계 진행, hold, deviation을 결정한다. In-process Sample(반응 중, Work-up 후, 결정화 모액 등) 채취 후 시험 항목: 순도(HPLC 면적%), 출발물질 잔존량(≤1.0%), 수분(KF, ≤1.0%), 용매 조성(GC), 결정형(XRPD), 입도(PSD). LIMS 결과 수신(30~60분) → MES Gate 규칙: All Pass → Progress, 1건 Fail → IPC Hold + Deviation 생성. Gate(Inspection) 포인트로서 Step 3,4,5의 진행 제어. |
| 7 | 건조·분쇄·체분 | 잔류용매, 수분, 입도 등 물성 조건을 맞춘다. 건조 조건: 진공 건조기(Vacuum Tray Dryer / Double Cone Vacuum Dryer, 온도 40~80°C, 진공도 -0.9 barg)에서 잔류용매(GC, ICH Q3C 기준 Class 2 ≤0.5%, Class 3 ≤0.5%) 및 수분(KF ≤0.5%) 달성. 분쇄(Pin Mill / Jet Mill / Ball Mill): 분쇄 RPM, Classifier 속도, 공급 속도로 목표 입도(D90, D50) 확보. 체분(Vibrating Sieve / Air Jet Sieve): oversize ≥1% 초과 시 재분쇄 또는 체분 분리. |
| 8 | 최종 QC·Release | 시험성적, deviation, change, OOS를 검토하고 release status를 결정한다. 시험항목: 순도(HPLC ≥99.5%), 개별 불순물(≤0.1% USP/EP 기준), 총 불순물(≤1.0%), 잔류용매(GC, ICH Q3C), 수분(KF), 입도(PSD), 잔류금속(ICP-MS ICH Q3D), 결정형(XRPD), 중금속, 미생물 한도시험. 모든 항목 Pass 시 LIMS 결과 → MES Release Flag 전환. OOS(Out of Specification) 발생 시 Phase I Lab Investigation(LIR) → Phase II Full OOS Investigation 필요. QA 전자승인(Electronic QA Release) 후 Stamp 부여. |
| 9 | 포장·라벨 | 청정 포장, 라벨, 보관 조건, retest date를 확인한다. GMP Packing: ISO Class 7~8 환경, HDPE 드럼/알루미늄 백(+Silica gel)/Triple PE bag, Sealing(Induction Sealer / Heat Sealer). Label: 제품명, Batch No., 제조일, 재시험일(Retest Date, 제조일+24~60개월), 보관 조건(Store at 15~25°C), 경고문. 케이스/팔레트 Label에 Lot/Batch Barcode + Serial Number 할당. |
| 10 | EBR Review·마감 | 전자 Batch Record, audit trail, exception, QA 승인을 마감한다. eBR(Electronic Batch Record, FDA 21 CFR Part 11 / EU Annex 11 준수) 검증: 입력 필드 완전성, Sequence 준수, 수동 Override/Deviation/Comment 기록, Audit Trail(CRUD 로그: User ID, Time stamp, Before/After 값). Exception Report(Deviation, OOS, 수동 개입 리스트) 생성. QA 최종 검토 → 전자서명(E-signature) → eBR Lock(Read-only) → Batch Close. |

### 4.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | MBR/批指令批准 | 确认主批记录、生产批指令、设备和人员适格性。MBR版本管理(Rev管理，变更需Change Control批准+PPQ再验证)由ERP/PLM管理。批指令包含Recipe ID、目标设备(Reactor ID、Tank ID)、操作员培训(Certification)记录、所需洁净度等级(ISO Class 7~8)。CPV(Critical Process Validation)标准：遵守FDA 21 CFR Part 11/EU ANNEX 15。代表产品：API中间体(对乙酰氨基酚、布洛芬、阿托伐他汀中间体)、GMP精细化学品中间体。 |
| 2 | 原料分装称量 | 电子记录原料批次、有效期、称量值和双人复核。在GMP分装台(Dispensing Booth，HEPA过滤器，ISO Class 7)内使用精密电子秤(Mettler Toledo/Sartorius，±0.01g~±1g)。原料Lot ID扫码后自动验证有效期(Expiry Date)，过期时阻断分装。称量双重复核(操作员+主管E-signature)→Weigh Ticket自动打印。按批次计算物料平衡(Material Balance)，验证投入量损耗0.5%以内。 |
| 3 | 合成反应 | 将反应温度、时间、投料顺序、催化剂和终点与配方比对。在搪玻璃/SUS316L反应釜(100L~10m³)中温度-20~200°C、压力-1~6 barg、搅拌50~400 RPM，夹套温度PID控制。CPP：温度(设定值±5°C)、压力(±0.2 barg)、搅拌速度(±20 RPM)、投料速度(mL/min)、pH(±0.3)。反应终点(TLC/中间体HPLC面积%)按Recipe设定值(如起始物料≤1.0%)达标为止。所有CPP由DCS Historian以1秒~1分钟周期实时(Real-time)存储。 |
| 4 | 淬灭与后处理 | 记录反应结束后的淬灭、萃取、洗涤等后处理条件。淬灭溶液(水、酸/碱液、有机溶剂)投加速度(温度控制，0.5~10°C/min)，淬灭后pH目标范围(如pH 3~5)确认。液-液萃取(分液漏斗/萃取塔，溶剂/水相比例Recipe指定)。洗涤(纯水/盐水/碳酸氢钠溶液，次数Recipe指定)。淬灭及后处理条件(温度、时间、pH、分层完成状态)由DCS/PLC顺序控制器自动记录。 |
| 5 | 分离与精制 | 管理结晶、过滤、干燥、色谱等精制条件。结晶(Crystallization)：冷却速率(0.1~2°C/min)、溶剂组成(反溶剂添加)、晶种加入温度/量。过滤(抽滤器/Nutsche过滤器/搅拌式过滤干燥器ANFD/离心机，1000~2000G)：过滤时间、滤饼厚度、洗涤溶剂量/次数。干燥(ANFD/真空盘式干燥器/流化床干燥器)：温度40~80°C、真空度-0.8~-1.0 barg、干燥时间。色谱(Column、Prep HPLC)：流动相组成、流速、检测波长、馏分收集窗口。 |
| 6 | 过程检验 | 依据IPC结果决定继续、hold或偏差处理。中间体样品(反应中、后处理后、结晶母液等)采集后检验项目：纯度(HPLC面积%)、起始物料残留(≤1.0%)、水分(KF，≤1.0%)、溶剂组成(GC)、晶型(XRPD)、粒度(PSD)。LIMS结果接收(30~60分钟)→MES Gate规则：全部Pass→继续，1项Fail→IPC Hold+Deviation生成。作为Gate(Inspection)节点控制Step 3、4、5进程。 |
| 7 | 干燥·粉碎·过筛 | 控制残留溶剂、水分和粒度等物性条件。干燥条件：真空干燥器(真空盘式干燥器/双锥真空干燥器，温度40~80°C、真空度-0.9 barg)达残留溶剂(GC，ICH Q3C标准Class 2≤0.5%、Class 3≤0.5%)及水分(KF≤0.5%)。粉碎(Pin Mill/Jet Mill/Ball Mill)：粉碎转速、分级器速度、进料速度实现目标粒度(D90、D50)。过筛(振动筛/气流筛)：筛上≥1%时返回粉碎或过筛分离。 |
| 8 | 最终QC与放行 | 审核检验结果、偏差、变更和OOS，并决定放行状态。检验项目：纯度(HPLC≥99.5%)、单个杂质(≤0.1% USP/EP标准)、总杂质(≤1.0%)、残留溶剂(GC，ICH Q3C)、水分(KF)、粒度(PSD)、残留金属(ICP-MS ICH Q3D)、晶型(XRPD)、重金属、微生物限度检查。全部项目Pass时LIMS结果→MES Release Flag。OOS(Out of Specification)发生时启动Phase I Lab Investigation(LIR)→Phase II全面OOS调查。QA电子放行(Electronic QA Release)后盖Stamp。 |
| 9 | 包装与标签 | 确认洁净包装、标签、储存条件和复验期。GMP包装：ISO Class 7~8环境，HDPE桶/铝袋(+硅胶)/三层PE袋，密封(感应封口机/热封机)。标签：品名、Batch No.、生产日期、复验期(Retest Date，生产日+24~60个月)、储存条件(Store at 15~25°C)、警示语。箱/托盘标签含Lot/Batch Barcode+Serial Number。 |
| 10 | EBR审核关闭 | 关闭电子批记录、审计追踪、异常和QA批准。eBR(电子批记录，符合FDA 21 CFR Part 11/EU Annex 11)验证：输入字段完整性、顺序合规、手动Override/Deviation/Comment记录、审计追踪(CRUD日志：用户ID、时间戳、修改前/后值)。生成异常报告(Exception Report：Deviation、OOS、手动干预清单)。QA最终审核→电子签名(E-signature)→eBR锁定(Lock，只读)→Batch Close。 |

### 4.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| MBR/Recipe governance | 승인된 MBR와 recipe version만 실행되도록 통제한다. Every Batch 발행 전 ERP/PLM에서 MBR Version(최신 승인된 Rev) 자동 조회, 일치하는 Recipe ID만 DCS/PLC에서 실행 가능. MBR 변경 시 Change Control + PPQ(Process Performance Qualification) 검증 필요. 3rd party(Regulatory agency) Audit 대비 MBR 이력(Audit Trail) 보존. | 1,3 | process_step |
| 전자계량·물질수지 | 원료 투입량과 산출량을 batch별 물질수지로 검증한다. Dispensing Booth(HEPA, ISO Class 7) 내 Precision Balance(Mettler Toledo, ±0.01g), Every Batch 2회(Operator + Supervisor) E-signature Double Check. Batch 종료 시 Material Balance(Input kg = Output kg + In-process kg + WIP kg) 계산, Loss 0.5% 초과 시 Deviation 생성. Lot 추적 포인트: Material Lot → Batch ID. | 2,10 | process_step |
| Critical process parameter | 반응 endpoint와 CPP를 자동수집하고 limit excursion을 deviation으로 연결한다. DCS Historian에 CPP(온도 ±5°C, 압력 ±0.2 barg, RPM ±20, pH ±0.3) 1초 주기 Real-time 수집. Alarm 상한/하한 초과 시 자동 Alarm + Trend Plot Archive. CPP excursion → Auto Deviation ID 생성 → Batch Hold + QA Notification. 宿迁联盛科技(Suqian Union Technology) 디지털 트윈 사례 참조: 리드타임 12% 단축. | 3,4 | process_step |
| Cleaning status | 설비 cleaning, campaign, 교차오염 위험을 batch 시작 전 차단한다. Equipment Cleaning Log(CIP/SIP 일시, cleaning agent, 농도, 온도, 시간, Conductivity/Rinse pH 확인)를 Batch 발행 전 자동 검증. Cleaning Validation 이력(Visual inspection, Swab test/Rinse test, Limit: 10ppm / 1/1000 therapeutic dose) 확인. Campaign 관리(동일 제품 연속 생산 시 청소 면제) 조건 검증. | 1,5 | process_step |
| IPC Release Gate | IPC 결과 없이는 정제·건조·포장을 진행하지 못하게 한다. LIMS IPC 결과(순도 HPLC, 출발물질(≤1.0%), 수분 KF(≤1.0%))가 MES Gate 규칙에 의해 자동 판정. Fail 시 Step 6에서 진행 Stop + Deviation + E-mail/Notification. Hold 해제 원칙: Root cause 분석(CAPA) + 재시험 Pass 후 QA 승인. Every Batch Gate Release 적용. | 6,7 | process_step |
| QA Release | OOS, deviation, change control을 QA release와 연결한다. LIMS Final QC 결과(순도, 불순물, 잔류용매, 수분, 입도, 잔류금속(ICP-MS), 결정형(XRPD), 미생물) 모두 Pass 시 QA Release 후보. 전건 Deviation(0건 권장, Deviation 건수가 있는 경우 Root Cause + CAPA 완료 확인), Change Control(변경 사항 QA 승인 확인) 조건 충족 시 E-signature Release. 1건이라도 충족 못하면 QA Hold + Review Board. | 8,10 | process_step |
| Data integrity | Audit trail, 전자서명, 권한, 시간동기화를 eBR 기준으로 관리한다. 21 CFR Part 11 요구사항: 전자서명(User ID + Password/Biometric), Audit Trail(CRUD: 누가, 언제, 무엇을, Before/After 값), 시간동기화(NTP Server, Drift ±1분 이내), User Access Control(Role-based, Password Policy). eBR Lock/Close 시 Audit Trail Report 생성 → Regulatory Submission 준비. | 1,10 | industry |

### 4.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| MBR/配方治理 | 只允许执行已批准的MBR和配方版本。每批次(Every Batch)发放前由ERP/PLM自动查询MBR版本(最新批准的Rev)，仅匹配的Recipe ID可在DCS/PLC执行。MBR变更需Change Control+PPQ(工艺性能确认)验证。为3方(监管机构)审计保留MBR历史(Audit Trail)。 | 1,3 | process_step |
| 电子称量与物料平衡 | 按批次通过物料平衡验证原料投入和产出。分装台(Dispensing Booth，HEPA，ISO Class 7)内精密天平(Mettler Toledo，±0.01g)，每批次(Every Batch)操作员+主管双人E-signature Double Check。批次结束时计算物料平衡(Input kg = Output kg + In-process kg + WIP kg)，损耗超过0.5%时生成Deviation。Lot追溯节点：Material Lot→Batch ID。 | 2,10 | process_step |
| 关键过程参数 | 自动采集反应终点和CPP，并将限值偏离连接到偏差。DCS Historian以1秒周期实时(Real-time)采集CPP(温度±5°C、压力±0.2 barg、RPM±20、pH±0.3)。超报警上下限时自动报警+趋势曲线存档。CPP excursion→自动生成Deviation ID→Batch Hold+QA通知。参考宿迁联盛科技数字孪生案例：交期缩短12%。 | 3,4 | process_step |
| 清洁状态 | 在批次开始前阻断设备清洁、campaign和交叉污染风险。批次发放前自动验证设备清洁日志(CIP/SIP时间、清洗剂、浓度、温度、时间、电导率/冲洗水pH)。确认清洁验证历史(目视检查、Swab test/Rinse test，限度：10ppm/1/1000治疗剂量)。验证Campaign管理(同产品连续生产时免清洗)条件。 | 1,5 | process_step |
| IPC放行关口 | 无IPC结果时不得进入精制、干燥和包装。LIMS IPC结果(纯度HPLC、起始物料(≤1.0%)、水分KF(≤1.0%))由MES Gate规则自动判定。Fail时Step 6停止+Deviation+邮件/通知。解除Hold原则：根本原因分析(CAPA)+复测Pass后QA批准。每批次(Every Batch)执行Gate放行。 | 6,7 | process_step |
| QA放行 | 将OOS、偏差、变更控制连接到QA放行。LIMS最终QC结果(纯度、杂质、残留溶剂、水分、粒度、残留金属(ICP-MS)、晶型(XRPD)、微生物)全部Pass时成为QA放行候选。全部Deviation(0件推荐，有Deviation时确认Root Cause+CAPA完成)、Change Control(变更需QA批准)条件满足后E-signature放行。1项不满足则QA Hold+Review Board。 | 8,10 | process_step |
| 数据完整性 | 按eBR要求管理审计追踪、电子签名、权限和时间同步。21 CFR Part 11要求：电子签名(用户ID+密码/生物识别)、审计追踪(CRUD：谁、何时、做了什么、修改前/后值)、时间同步(NTP服务器，偏差±1分钟以内)、用户权限控制(基于角色、密码策略)。eBR锁定/关闭时生成审计追踪报告→准备监管提交。 | 1,10 | industry |

### 4.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | MBR | gate |  | 2,3 | recipe_id,ebr_id,release_status |
| 2 | Dispense | batch |  |  | material_lot,batch_id |
| 3 | Reaction | batch | Deviation / Hold Loop |  | batch_id,recipe_id,equipment_id,process_param |
| 4 | Workup | process |  |  | batch_id,process_param |
| 5 | Purification | process |  |  | equipment_id,cleaning_status,process_param |
| 6 | IPC Gate | gate |  | 3,4,5 | sample_id,lab_result,deviation_id |
| 7 | Drying | process |  |  | batch_id,process_param |
| 8 | QA Gate | gate |  | 6,7 | lab_result,release_status,deviation_id |
| 9 | Packaging | process |  |  | batch_id,coa_id |
| 10 | EBR Review | gate |  | 1,2,3,4,5,6,7,8,9 | ebr_id,deviation_id,release_status |

### 4.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | MBR | gate |  | 2,3 | recipe_id,ebr_id,release_status |
| 2 | Dispense | batch |  |  | material_lot,batch_id |
| 3 | Reaction | batch | Deviation / Hold Loop |  | batch_id,recipe_id,equipment_id,process_param |
| 4 | Workup | process |  |  | batch_id,process_param |
| 5 | Purification | process |  |  | equipment_id,cleaning_status,process_param |
| 6 | IPC Gate | gate |  | 3,4,5 | sample_id,lab_result,deviation_id |
| 7 | Drying | process |  |  | batch_id,process_param |
| 8 | QA Gate | gate |  | 6,7 | lab_result,release_status,deviation_id |
| 9 | Packaging | process |  |  | batch_id,coa_id |
| 10 | EBR Review | gate |  | 1,2,3,4,5,6,7,8,9 | ebr_id,deviation_id,release_status |

### 4.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 1 | 1 | MBR 버전 확인 |
| 2 | 1 | 전자계량 |
| 3 | 1 | CPP 자동수집 |
| 6 | 1 | IPC 판정 |
| 10 | 1 | Audit trail review |

### 4.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 1 | 1 | 确认MBR版本 |
| 2 | 1 | 电子称量 |
| 3 | 1 | CPP自动采集 |
| 6 | 1 | IPC判定 |
| 10 | 1 | 审计追踪审核 |

---

## 5. E05 `paint_coating_adhesive_ink` — 도료·코팅·접착제·잉크 / 涂料·涂层·胶粘剂·油墨

```yaml
code: "E05"
legacy_slug: "paint_coating_adhesive_ink"
label_ko: "도료·코팅·접착제·잉크"
label_zh: "涂料·涂层·胶粘剂·油墨"
label_en: ""
label_ja: ""
routing: "RT_BATCH"
flow_preset_id: "process_batch_v1"
expression_tier: "pflow_v0_3"
description_ko: "분산·혼합·조색·점도보정이 핵심. 색상, 점도, 고형분, 분산도, 고객 색차 관리와 소분 포장 추적이 중요하다."
description_zh: "核心是分散、混合、调色和粘度调整。重点管理颜色、粘度、固含、分散度、客户色差和分装追溯。"
data_capture_points:
  - color_code
  - raw_lot_id
  - batch_id
  - recipe_id
  - scale_id
  - mixer_id
  - dispersion_param
  - sample_id
  - lab_result
  - delta_e
  - package_lot
  - coa_id
```

### 5.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객 색상·Spec 확인 | 색상코드, 표준판, 용도, 점도·고형분 규격을 확인한다. 고객 Color Chip/Standard Plate(RAL, Pantone, NCS 코드)를 분광광도계(Spectrophotometer, HunterLab/X-Rite)로 측정하여 Delta-E(ΔE < 1.0) 기준 검증. 용도별 Spec: 실내/외용(UV 내구성), 금속/플라스틱용(부착성), 식품접촉용(FDA 규제), VOC 규제(환경부/EPA 기준). 대표 제품: 수성 아크릴 도료, 자동차 Clear Coat, 2K Epoxy 접착제, UV 경화형 잉크, 방오 코팅(Anti-fouling coating). |
| 2 | 원료·안료 계량 | 수지, 용제, 안료, 첨가제를 recipe 순서대로 계량한다. 정밀 전자저울(Platform scale ±0.1g~±0.5kg)과 Pre-weigh Container 사용. 안료/염료 분진 비산 방지(국소배기/밀폐 계량 Booth). 용제 계량: 질량 유량계(Mass flow meter, Coriolis) 자동 계량. 첨가제(분산제, 소포제, UV 안정제, 레올로지 개질제)는 Micro-metering pump(0.1~10 L/min) 정밀 주입. 계량 데이터 Scada/MES 자동 전송 + Recipe 편차 ±0.5% 감시. |
| 3 | Pre-mix | 저속 혼합으로 원료를 균질화하고 투입 누락을 방지한다. 저속 교반기(Low-speed mixer, Anchor/Paddle, 50~300 RPM)에서 수지+용제+안료/첨가제 순차 투입, 10~30분 혼합. 균질성(Hegman grind gauge, ASTM D1210) > 7(미크론) 수준 확인. Barcode/QR 코드로 투입 원료 순서 스캔 확인(투입 누락 방지). |
| 4 | 분산·Grinding | 비드밀·분산기 조건으로 입도와 색상 발현을 안정화한다. 수평형 비드밀(Horizontal Bead Mill, Netzsch/Bühler, ZrO₂ bead Ø0.3~2.0mm), 분산기(High-speed disperser, 1000~5000 RPM), 3-roll mill(paste type). 분산 조건: RPM, Bead filling rate(70~85%), Product temperature(≤60°C coolant control), Pass 횟수(1~5 pass). 목표 입도(Hegman > 7, PSD D90 < 10µm). 색상 발현 확인(Spectrophotometer, 계속 측정). |
| 5 | Let-down·조정 | 수지·용제·첨가제를 추가해 점도와 고형분을 조정한다. Let-down Tank(Jacket 교반조, 500L~20m³)에서 Let-down 수지(Resin)와 용제를 추가하며 교반(Anchor/Paddle, 100~500 RPM). Metering Pump/Diaphragm pump(0.5~50 L/min)로 첨가제(레올로지 개질제, 분산제 추가, UV 흡수제, 소포제, 레벨링제) 투입. 점도(Stormer viscometer KU / Brookfield), 고형분(NV%, 105°C/30min) In-process Check. |
| 6 | 색상·물성 검사 | Delta-E, 점도, 고형분, 광택, 접착력 등을 검사한다. 분광광도계(Spectrophotometer, HunterLab/X-Rite, D65/10°), Gloss meter(60°/20°/85°), 접착력 테스트(Cross-cut tape test ASTM D3359 / Pull-off test ASTM D4541), Impact resistance, Bend test, Hardness(Pencil hardness ASTM D3363). 결과를 LIMS로 수신하여 고객 Spec(ΔE < 1.0, Gloss > 80 GU for high gloss)과 비교 판정. |
| 7 | 보정·재분산 | 검사 결과에 따라 색상 보정, 희석, 추가 분산을 수행한다. ΔE > 1.0이면 Tinting(착색제 주입, Micro-metering pump, 점적(滴) 단위 보정). 점도 > 상한이면 용제 희석, 점도 < 하한이면 증점제/Resin 투입. 입도 부족 시 추가 Bead mill pass. MES Adjustment Order 생성: 보정량(kg, mL), 보정 후 재검사 → Pass 시까지 Loop. 각 Adjustment는 Deviation ID로 Batch Record에 기록. |
| 8 | 여과·충전 준비 | 필터 상태, 이물, 기포, 포장 라인을 확인한다. 필터(Filter bag 10~200µm, Filter cartridge 1~100µm, Magnetic filter): 여과압력(Delta P < 2 barg), Filter 교체 시기. 진공탈포(Vacuum degasser, -0.8 barg, 10~20min). 포장 라인: Hopper/Feed pump 상태, Filler nozzle cleanliness, Weighborge Calibration 확인. |
| 9 | 소분·라벨링 | 캔, 드럼, 카트리지 등 포장단위로 충전하고 라벨을 부착한다. 자동 충전기(Piston filler / Gravity filler / Auger filler, 정밀도 ±0.5~1.0%)로 0.5L 캔~200kg 드럼 충전. 캔 씰링(Seaming machine / Capping machine), 라벨(제품명, Batch No., 용량, 색상코드, VOC 함량, MSDS QR, 유통기한) 자동 부착. Package lot Barcode → Batch ID 1:N 매핑. |
| 10 | 출하·보관 | CoA, shelf-life, 보관온도, 위험물 정보를 출하 lot에 연결한다. CoA(고객별 템플릿: 색상 ΔE, 점도, 고형분, 비중, VOC, Flash point) 자동 생성 + QA E-signature. 보관 조건(온도 5~40°C, Humidity < 80%, 직사광선 회피, 가연물·산화제 격리)을 ERP 출하 lot에 연결. 인화성 액체(Class 3 UN 1263) 위험물 운송 규정 준수 확인. |

### 5.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户颜色与规格确认 | 确认色号、标准板、用途、粘度和固含规格。客户Color Chip/Standard Plate(RAL、Pantone、NCS代码)由分光光度计(Spectrophotometer，HunterLab/X-Rite)测量，验证Delta-E(ΔE < 1.0)标准。用途规格：室内/外用(UV耐久性)、金属/塑料用(附着力)、食品接触用(FDA监管)、VOC限制(环保部/EPA标准)。代表产品：水性丙烯酸涂料、汽车清漆、2K环氧胶粘剂、UV固化油墨、防污涂层(Anti-fouling coating)。 |
| 2 | 原料与颜料称量 | 按配方顺序称量树脂、溶剂、颜料和添加剂。使用精密电子秤(Platform scale±0.1g~±0.5kg)和Pre-weigh Container。防止颜料/染料粉尘飞散(局部排气/密闭称量柜)。溶剂称量：质量流量计(Mass flow meter，Coriolis)自动称量。添加剂(分散剂、消泡剂、UV稳定剂、流变改性剂)通过微量计量泵(0.1~10 L/min)精确注入。称量数据自动传至Scada/MES+配方偏差±0.5%监控。 |
| 3 | 预混 | 低速混合使原料均质化，并防止漏投。低速搅拌机(Low-speed mixer，Anchor/Paddle，50~300 RPM)中顺序投入树脂+溶剂+颜料/添加剂，混合10~30分钟。均质性(Hegman grind gauge，ASTM D1210)>7(微米)水平确认。通过Barcode/QR码扫描确认原料投入顺序(防漏投)。 |
| 4 | 分散与研磨 | 通过珠磨机或分散机条件稳定粒径和显色。卧式珠磨机(Horizontal Bead Mill，Netzsch/Bühler，ZrO₂珠Ø0.3~2.0mm)、分散机(High-speed disperser，1000~5000 RPM)、三辊研磨机(3-roll mill，膏状物)。分散条件：RPM、珠子填充率(70~85%)、物料温度(≤60°C冷却控制)、通次数(1~5 pass)。目标粒度(Hegman>7，PSD D90<10µm)。色泽确认(分光光度计，连续测量)。 |
| 5 | 调漆与调整 | 追加树脂、溶剂和添加剂以调整粘度和固含。调漆罐(夹套搅拌罐，500L~20m³)中加入调漆树脂(Resin)和溶剂，搅拌(Anchor/Paddle，100~500 RPM)。计量泵/隔膜泵(0.5~50 L/min)注入添加剂(流变改性剂、追加分散剂、UV吸收剂、消泡剂、流平剂)。粘度(Stormer viscometer KU/Brookfield)、固含(NV%，105°C/30min)过程检查(In-process Check)。 |
| 6 | 颜色与物性检验 | 检测Delta-E、粘度、固含、光泽和附着力等。分光光度计(Spectrophotometer，HunterLab/X-Rite，D65/10°)、光泽计(Gloss meter，60°/20°/85°)、附着力测试(百格刀Cross-cut tape test ASTM D3359/Pull-off test ASTM D4541)、耐冲击性、弯曲测试、硬度(铅笔硬度ASTM D3363)。结果经LIMS接收后与客户Spec(ΔE<1.0、高光泽>80 GU)比对判定。 |
| 7 | 修色与再分散 | 依据检验结果执行修色、稀释或追加分散。ΔE>1.0时调色(着色剂注入，微量计量泵，滴(滴)单位调整)。粘度>上限时溶剂稀释，粘度<下限时增稠剂/树脂投入。粒度不足时追加Bead mill pass。MES调整指令生成：调整量(kg、mL)，调整后复测→Pass前循环。每次调整以Deviation ID记录于批记录。 |
| 8 | 过滤与灌装准备 | 确认过滤器状态、异物、气泡和包装线状态。过滤器(Filter袋10~200µm、滤芯1~100µm、磁性过滤器Magnetic filter)：过滤压力(Delta P<2 barg)，滤芯更换时机。真空脱泡(Vacuum degasser，-0.8 barg，10~20分钟)。包装线：料斗/供料泵状态、灌装嘴清洁度、地磅校准确认。 |
| 9 | 分装与标签 | 按罐、桶、胶筒等包装单位灌装并贴标。自动灌装机(Piston filler/Gravity filler/Auger filler，精度±0.5~1.0%)按0.5L罐~200kg桶灌装。封罐机(Seaming machine)/压盖机(Capping machine)，标签(品名、Batch No.、容量、色号、VOC含量、MSDS二维码、保质期)自动粘贴。Package lot Barcode→Batch ID 1:N映射。 |
| 10 | 发货与储存 | 将CoA、保质期、储存温度和危险品信息关联到发货批次。CoA(客户化模板：颜色ΔE、粘度、固含、比重、VOC、闪点)自动生成+QA E-signature。储存条件(温度5~40°C、湿度<80%、避免直射阳光、与易燃物/氧化剂隔离)关联至ERP发货lot。确认符合易燃液体(Class 3 UN 1263)危险品运输规定。 |

### 5.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| 색상 Spec 관리 | 표준판, 색상코드, Delta-E 판정이 고객별로 달라 recipe와 연결해야 한다. 분광광도계(Spectrophotometer, HunterLab/X-Rite, D65/10°, 측정 Geometry d/8°)로 Every Batch 색상 측정. 다각도 측정(메탈릭/펄 색상: 15°/25°/45°/75°/110°) 필요 시 적용. ΔE < 1.0(고객 기준에 따라 0.5~2.0) 통과 시 Recipe에 색상 Code 연결 저장. ΔE > 1.0이면 Deviation 생성 → 보정(Step 7) Loop. | 1,6 | process_step |
| 안료·첨가제 계량 | 미량 안료와 첨가제 계량 오류가 색상·점도 편차를 만든다. Precision Scale(±0.01g) Calibration 주 1회(Span/Zero). Every Batch 계량값 vs Recipe값 편차 ±0.5% 이내 검증. Barcode 기반 Double Check(Operator+Supervisor). 이상 시 Scale Isolation → Calibration 재수행 → 원료 Lot Hold. | 2 | process_step |
| 분산 조건 | 분산시간, rpm, bead, 온도는 입도와 색상 재현성에 직접 영향을 준다. Bead Mill Process: Bead filling rate(70~85%), RPM(1500~4000), Pass 횟수(1~5), Mill 온도(≤60°C coolant). Hegman gauge(ASTM D1210) Every Batch 측정, D90 < 10µm. 입도 부족 시 추가 Pass 또는 Bead 교체. 온라인 입도계(FBRM, PVM) 실시간(Real-time) 모니터링 적용 가능. | 4 | process_step |
| 보정 loop | 색상·점도 보정 이력은 최종 batch record에 남겨야 한다. ΔE > 1.0 시 MES Adjustment Order 자동 생성: Tinting 보정액(색상별) 주입량 계산(mL/g). 점도/고형분 보정: 희석용제 또는 증점제 주입량 계산. 각 보정 Event를 Deviation ID와 함께 Batch Record에 저장. 보정 후 재시험 → Pass 시까지 Loop. | 6,7 | process_step |
| 여과·이물 | 필터 lot, mesh, 압력 차와 이물 검출 이력을 포장 lot에 연결한다. Filter 교체 시 Filter Bag/Cartridge Lot #, Mesh(µm), 교체 시간 MES 기록. Delta P(0.5~2 barg) 초과 시 Filter 막힘 Alarm → 교체. 이물 검사(Sieve test / Visual inspection / X-ray 검사) 기록 → 포장 lot 연결. | 8,9 | process_step |
| 위험물·VOC | 용제, VOC, 방폭, 보관 조건을 제품 lot과 연결한다. VOC 함량(Knudsen/Gravimetric method, EPA Method 24, ASTM D3960) Every Batch 측정. 인화점(Pensky-Martens, ASTM D93, 60°C 미만 Class 3) 기록. 폭발 위험 구역(방폭 Ex d/Ex e) 설비 검증 이력 연결. MSDS 최신 Rev. lot별 연결. | 2,10 | industry |
| 소분 genealogy | 한 batch가 여러 포장 lot으로 분할되므로 package genealogy가 필요하다. Batch ID와 각 Package Lot ID 간 1:N 관계를 ERP/MES에서 관리. Package lot별 충전량(kg), Serial Number 범위 기록. 리콜 시 Package Lot → Batch ID 역추적 가능 체계. | 9,10 | process_step |

### 5.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| 颜色规格管理 | 标准板、色号和Delta-E判定因客户不同而不同，必须与配方关联。分光光度计(Spectrophotometer，HunterLab/X-Rite，D65/10°，测量几何d/8°)每批次(Every Batch)测量颜色。必要时应用多角度测量(金属/珠光色：15°/25°/45°/75°/110°)。ΔE < 1.0(客户标准0.5~2.0)通过时颜色Code关联至Recipe储存。ΔE > 1.0时生成Deviation→修色(Step 7)循环。 | 1,6 | process_step |
| 颜料与添加剂称量 | 微量颜料和添加剂称量误差会造成颜色和粘度波动。精密天平(±0.01g)校准周期每周1次(Span/Zero)。每批次(Every Batch)称量值与配方值偏差±0.5%以内验证。条码基双重复核(操作员+主管)。异常时隔离秤具→重新校准→原料Lot Hold。 | 2 | process_step |
| 分散条件 | 分散时间、转速、珠子和温度直接影响粒径与颜色再现性。珠磨机工艺：珠子填充率(70~85%)、RPM(1500~4000)、通次数(1~5次)、磨机温度(≤60°C冷却控制)。Hegman刮板细度计(ASTM D1210)每批次(Every Batch)测量，D90<10µm。粒度不足时追加通次或更换珠子。在线粒度计(FBRM、PVM)可实时(Real-time)监控。 | 4 | process_step |
| 调整回路 | 修色和粘度调整历史必须保留在最终批记录中。ΔE>1.0时MES自动生成调整指令：调色剂(分色)注入量计算(mL/g)。粘度/固含调整：稀释溶剂或增稠剂注入量计算。每次调整事件以Deviation ID存入批记录。调整后复测→Pass前循环。 | 6,7 | process_step |
| 过滤与异物 | 滤芯批次、目数、压差和异物检测记录需关联到包装批次。更换滤芯时记录Filter Bag/Cartridge Lot#、目数(µm)、更换时间至MES。Delta P(0.5~2 barg)超时滤芯堵塞报警→更换。异物检查(筛网测试/目视检查/X-ray检查)记录→关联包装批次。 | 8,9 | process_step |
| 危险品与VOC | 溶剂、VOC、防爆和储存条件需关联到产品批次。VOC含量(Knudsen/重量法，EPA Method 24，ASTM D3960)每批次(Every Batch)测量。闪点(Pensky-Martens，ASTM D93，低于60°C为Class 3)记录。防爆区域(Ex d/Ex e)设备验证记录关联。MSDS最新版本按批次关联。 | 2,10 | industry |
| 分装族谱 | 一个批次会拆分为多个包装批次，需要包装族谱。Batch ID与各Package Lot ID之间的1:N关系由ERP/MES管理。记录每个Package lot灌装量(kg)和Serial Number范围。召回时可通过Package Lot→Batch ID逆向追溯体系。 | 9,10 | process_step |

### 5.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | color_code,recipe_id |
| 2 | Weighing | batch |  |  | raw_lot_id,batch_id,scale_id |
| 3 | Premix | batch |  |  | batch_id,mixer_id |
| 4 | Dispersion | batch | Color / Viscosity Adjustment Loop |  | batch_id,mixer_id,dispersion_param |
| 5 | Letdown | batch |  |  | batch_id,recipe_id |
| 6 | QC Gate | gate |  | 4,5 | sample_id,lab_result,delta_e |
| 7 | Correction | batch |  |  | batch_id,delta_e,lab_result |
| 8 | Filtration | process |  |  | batch_id,package_lot |
| 9 | Packaging | process |  |  | package_lot,batch_id |
| 10 | Shipment | process |  |  | package_lot,coa_id |

### 5.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | color_code,recipe_id |
| 2 | Weighing | batch |  |  | raw_lot_id,batch_id,scale_id |
| 3 | Premix | batch |  |  | batch_id,mixer_id |
| 4 | Dispersion | batch | Color / Viscosity Adjustment Loop |  | batch_id,mixer_id,dispersion_param |
| 5 | Letdown | batch |  |  | batch_id,recipe_id |
| 6 | QC Gate | gate |  | 4,5 | sample_id,lab_result,delta_e |
| 7 | Correction | batch |  |  | batch_id,delta_e,lab_result |
| 8 | Filtration | process |  |  | batch_id,package_lot |
| 9 | Packaging | process |  |  | package_lot,batch_id |
| 10 | Shipment | process |  |  | package_lot,coa_id |

### 5.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 미량 안료 계량 |
| 4 | 1 | 분산 조건 기록 |
| 6 | 1 | 색차 판정 |
| 7 | 1 | 조색 보정 |
| 9 | 1 | 포장 lot 생성 |

### 5.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 微量颜料称量 |
| 4 | 1 | 记录分散条件 |
| 6 | 1 | 色差判定 |
| 7 | 1 | 修色调整 |
| 9 | 1 | 生成包装批次 |

---

## 6. E06 `polymer_resin_compound` — 수지·고무·컴파운드 / 树脂·橡胶·改性材料

```yaml
code: "E06"
legacy_slug: "polymer_resin_compound"
label_ko: "수지·고무·컴파운드"
label_zh: "树脂·橡胶·改性材料"
label_en: ""
label_ja: ""
routing: "RT_BATCH_CONTINUOUS"
flow_preset_id: "compound_extrusion_v1"
expression_tier: "pflow_v0_3"
description_ko: "Polymerization 또는 compounding/extrusion 중심. 원료 lot, recipe, extruder 조건, pellet/roll lot, 물성시험 추적이 중요하다."
description_zh: "以聚合或改性挤出为核心。关键是原料批次、配方、挤出条件、颗粒/卷材批次和物性检验追溯。"
data_capture_points:
  - raw_lot_id
  - batch_id
  - recipe_id
  - extruder_id
  - mold_die_id
  - process_param
  - pellet_lot
  - sample_id
  - lab_result
  - mfi_value
  - tensile_result
  - package_lot
```

### 6.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 제품 Grade·Recipe 확인 | 제품 grade, 첨가제, 고객 물성 규격과 recipe version을 확인한다. Grade Master(예: PP HOMOPOLYMER, PE-LD, PS GPPS/HIPS, ABS, PA6, PET, PC/ABS blend)에 따른 Recipe 설정. Grade별 물성 Spec: MFI(ASTM D1238, g/10min), 인장강도(ASTM D638, MPa), 충격강도(ASTM D256, J/m), 탄성률(Flexural Modulus, MPa), 열변형온도(HDT, °C). 대표 제품: PP/PE Compounding(자동차 내장재/범퍼), ABS(가전 케이싱), PC/ABS(전장부품), TPE/TPU(신발/씰), 고무 컴파운드(타이어/씰/호스). |
| 2 | 원료 건조·계량 | 수지, 고무, filler, additive를 건조·계량한다. 원료 건조(Dehumidifying dryer / Hopper dryer, 온도 60~120°C, 건조 시간 2~4시간, Dew point ≤ -40°C)로 수분 함량 ≤200ppm(PA/PC/PET 등 흡습성 수지). 중량 계량기(Gravimetric feeder, Loss-in-weight feeder, 정밀도 ±0.25~0.5%) 또는 체적 계량기(Volumetric feeder)로 각 Component Recipe 비율 자동 계량. Filler(CaCO₃, Talc, Glass fiber) 및 Additive(Compatibilizer, Impact modifier, UV stabilizer, Color Masterbatch) 계량 순서 Recipe 지정. |
| 3 | 혼련·Kneading | Mixer 또는 kneader에서 분산과 온도 조건을 관리한다. Internal Mixer(Banbury mixer, F270/F370, Rotor speed 20~100 RPM, Ram pressure 0.3~0.6 MPa) 또는 Continuous Mixer(Co-/Twin-shaft kneader). 온도 설정 80~200°C, 혼련 시간 1~5분, 혼련 온도(Temperature profile)로 분산도(Dispersion quality, Black carbon 분산 ASTM D2663 등급) 확인. Torque(전류) 모니터링으로 혼련 종점 판정. |
| 4 | 압출·반응압출 | Extruder zone 온도, screw speed, pressure, torque를 관리한다. Twin-screw Extruder(Co-rotating, 직경 30~150mm, L/D 24~52) 또는 Single-screw Extruder. Zone 온도(Feed→Barrel→Die: 150~300°C, 수지별 상이), Screw speed(100~1200 RPM), Melt pressure(50~200 barg), Torque(30~90%). Die(Sheet / Strand / Profile), Screen pack(40~200 mesh), Melt filter(자동/수동 교체). 반응압출(Reactive extrusion): 단량체/개시제를 Extruder Barrel 중간 Injection하여 중합 진행. CPP(온도 ±5°C, Screw speed ±10 RPM, Torque ±5%) 자동 수집 → Deviation 생성. 물성(MFI, Density, 접도) In-line Real-time 센서(Soft sensor, NIR) 적용 확대. |
| 5 | Strand/Pelletizing | Strand 냉각, 절단, pellet 형상과 분진을 관리한다. Water Bath(수온 15~40°C, Strand 수 20~100가닥) 또는 Air Cooling으로 Strand 냉각. Pelletizer(Strand cutter / Underwater pelletizer / Hot-face pelletizer, Cutter speed 500~3000 RPM)로 Pellet 절단(Ø2~5mm, L/D 1:1~1:1.5). Pellet 형상(Cylindrical/Spherical), 분진량(Fines < 0.5%, Sieve analysis), 건조(Centrifugal dryer / Fluid bed dryer, Moisture ≤ 200ppm). Pellet lot ID 자동 생성 → MES Batch ID 연결. |
| 6 | 냉각·Blending | Silo 또는 blender에서 균질화하고 lot 균일성을 확보한다. Silo Blending(Homogenizing silo, 10~100ton, Air injection/Conical blending) 또는 V-Blender/Vertical Blender로 Pellet Blending. Blend 균일성: Blend 시간(15~60분), 온라인 Density/MFI 측정으로 균질도 확인. Batch or Continuous blending으로 Lot 균일화. Silo에서 Packaging 라인으로 이송 시 Metal detector(Fe, SUS, Non-ferrous 감지) 통과. |
| 7 | 물성시험 | MFI, 인장, 충격, 색상, 수분 등 시험 결과로 grade를 판정한다. 시험 항목: MFI(Melt Flow Indexer, ASTM D1238, 190°C/2.16kg~230°C/3.8kg), 인장(Universal Testing Machine, ASTM D638), 충격(Izod/Charpy, ASTM D256, J/m), 색상(Lab colorimeter, L*/a*/b*, △E), 수분(Moisture analyzer, ppm), Density(Density gradient column / Gas pycnometer), TGA(Vicat/HDT, ASTM D1525/D648). LIMS 결과(Every Batch) vs Grade Spec → MES Gate 판정(Release / Downgrade / Reprocess). |
| 8 | Reprocess·등급조정 | Off-spec이나 재생 원료 투입 시 reprocess 이력을 남긴다. Off-spec Batch(물성 불합격, 오염, 색상 이탈)는 Reprocess Queue에 투입; Reprocess 비율(0~30%, 원 Grade별 허용 한도 내) Recipe 설정. Recycled/Regrind(재생/분쇄물) 투입 시 Lot ID, 비율(%), 사전 검증(물성, 오염, 분진) 결과 기록. Reprocess Batch ID ↔ Original Batch ID Genealogy Tree 구성. |
| 9 | 포장·라벨 | Bag, jumbo bag, roll 등 단위로 포장하고 lot label을 부착한다. Automatic Bagging Machine(Valve bag / Open mouth bag, 25kg/500kg/1000kg Jumbo bag), Palletizing robot, Stretch wrapping. 라벨: 제품명, Grade, Batch No., Lot No., Net weight, 제조일자, 보관조건(Store in dry area < 40°C). Serial Shipping Container Code(SSCC) Barcode 할당 → ERP 출하 연결. |
| 10 | 출하·고객 Spec 매칭 | 고객 주문과 grade, CoA, 포장 lot을 연결한다. 고객 PO와 생산 Batch Lot 매칭(ERP), CoA(물성 데이터: MFI, Density, 인장, 충격, 색상) 자동 생성 + QA E-signature. 고객 Grade Code ↔ 내부 Grade Code 매핑 확인. 출하 문서(Invoice, Packing list, CoA, MSDS) 자동 생성. |

### 6.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 产品等级与配方确认 | 确认产品grade、添加剂、客户物性规格和配方版本。根据Grade Master(如PP HOMOPOLYMER、PE-LD、PS GPPS/HIPS、ABS、PA6、PET、PC/ABS blend)设置配方。Grade物性Spec：MFI(ASTM D1238，g/10min)、拉伸强度(ASTM D638，MPa)、冲击强度(ASTM D256，J/m)、弯曲模量(Flexural Modulus，MPa)、热变形温度(HDT，°C)。代表产品：PP/PE Compounding(汽车内饰件/保险杠)、ABS(家电外壳)、PC/ABS(电子部件)、TPE/TPU(鞋材/密封件)、橡胶胶料(轮胎/密封件/软管)。 |
| 2 | 原料干燥与称量 | 对树脂、橡胶、填料和添加剂进行干燥与称量。原料干燥(除湿干燥机/料斗干燥机，温度60~120°C，干燥时间2~4小时，露点≤-40°C)使水分含量≤200ppm(PA/PC/PET等吸湿性树脂)。失重式计量给料机(Gravimetric feeder，Loss-in-weight feeder，精度±0.25~0.5%)或体积式计量给料机(Volumetric feeder)按配方比例自动计量各组分。填料(CaCO₃、滑石粉、玻璃纤维)及添加剂(相容剂、增韧剂、UV稳定剂、色母)计量顺序按配方指定。 |
| 3 | 混炼 | 在混合机或密炼机中管理分散和温度条件。密炼机(Internal Mixer，Banbury，F270/F370，转子转速20~100 RPM，上顶栓压力0.3~0.6 MPa)或连续混炼机(Co-/Twin-shaft kneader)。温度设定80~200°C，混炼时间1~5分钟，混炼温度梯度确认分散度(Dispersion quality，炭黑分散ASTM D2663等级)。通过扭矩(电流)监控判断混炼终点。 |
| 4 | 挤出/反应挤出 | 管理挤出机各区温度、螺杆转速、压力和扭矩。双螺杆挤出机(Twin-screw Extruder，同向旋转，直径30~150mm，L/D 24~52)或单螺杆挤出机。区段温度(Feed→Barrel→Die：150~300°C，因树脂而异)、螺杆转速(100~1200 RPM)、熔体压力(50~200 barg)、扭矩(30~90%)。口模(Sheet/Strand/Profile)、滤网组(Screen pack，40~200 mesh)、熔体过滤器(自动/手动更换)。反应挤出(Reactive extrusion)：单体/引发剂从挤出机筒中间注入进行聚合。CPP(温度±5°C、螺杆转速±10 RPM、扭矩±5%)自动采集→生成Deviation。物性(MFI、密度、粘度)在线实时传感器(Soft sensor、NIR)应用扩大。 |
| 5 | 拉条与造粒 | 管理冷却、切粒、颗粒形态和粉尘。水浴(Water Bath，水温15~40°C，条数20~100根)或风冷冷却条料。切粒机(Pelletizer，条料切粒机/水下切粒机/热面切粒机，切刀转速500~3000 RPM)切粒(Ø2~5mm，L/D 1:1~1:1.5)。颗粒形态(圆柱形/球形)、粉尘量(Fines<0.5%，筛分分析)、干燥(离心干燥机/流化床干燥机，水分≤200ppm)。Pellet lot ID自动生成→MES Batch ID关联。 |
| 6 | 冷却与混批均化 | 在料仓或混料机中均化，确保批次一致性。均化料仓(Homogenizing silo，10~100吨，气吹/锥形混合)或V型混合机/立式混合机进行颗粒混合。混合均匀性：混合时间(15~60分钟)，在线密度/MFI测量确认均匀度。批次或连续混批实现批次均一化。从料仓送至包装线时通过金属检测器(Metal detector，Fe、SUS、非铁金属检测)。 |
| 7 | 物性检验 | 通过MFI、拉伸、冲击、颜色和水分等结果判定grade。检验项目：MFI(熔融指数仪，ASTM D1238，190°C/2.16kg~230°C/3.8kg)、拉伸(万能材料试验机，ASTM D638)、冲击(Izod/Charpy，ASTM D256，J/m)、颜色(Lab色差计，L*/a*/b*，△E)、水分(水分分析仪，ppm)、密度(密度梯度柱/气体比重瓶)、热性能(Vicat/HDT，ASTM D1525/D648)。LIMS结果(每批次)vs Grade Spec→MES Gate判定(放行/降级/再加工)。 |
| 8 | 再加工与等级调整 | off-spec或回用料投入时保留再加工历史。Off-spec批次(物性不合格、污染、色差)投入再加工队列，再加工比例(0~30%，按原Grade允许限度)Recipe设定。回收料/粉碎回料(Recycled/Regrind)投入时记录Lot ID、比例(%)、预验证(物性、污染、粉尘)结果。再加工Batch ID↔原始Batch ID族谱树(Genealogy Tree)。 |
| 9 | 包装与标签 | 按袋、吨包或卷材单位包装并贴lot标签。自动包装机(Automatic Bagging Machine，阀口袋/敞口袋，25kg/500kg/1000kg吨包)、码垛机器人(Palletizing robot)、缠绕膜包装(Stretch wrapping)。标签：品名、Grade、Batch No.、Lot No.、净重、生产日期、储存条件(Store in dry area<40°C)。分配SSCC(系列货运容器代码)Barcode→关联ERP发货。 |
| 10 | 发货与客户规格匹配 | 关联客户订单、grade、CoA和包装批次。客户PO与生产Batch Lot匹配(ERP)，CoA(物性数据：MFI、密度、拉伸、冲击、颜色)自动生成+QA E-signature。客户Grade Code↔内部Grade Code映射确认。自动生成发货文件(Invoice、Packing list、CoA、MSDS)。 |

### 6.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| Grade·Recipe 관리 | 동일 제품군 내 grade 차이는 recipe와 물성 규격으로 관리해야 한다. Grade Master Recipe(수지/첨가제/filler 비율, Extruder 조건 설정)를 ERP/PLM에서 관리. Grade별 물성 Spec(MFI, Density, Tensile, Impact, HDT, Color ΔE)을 LIMS 기준으로 설정. Grade 변경 시 Change Control 승인 필요. Every Batch Recipe Version 검증. | 1,7 | process_step |
| 건조·수분 관리 | 원료 수분과 건조 조건은 압출 안정성과 물성에 영향을 준다. Hopper Dryer / Dehumidifying Dryer 온도(60~120°C), Dew point(≤ -40°C), 건조 시간(2~4h) 설정. 건조 후 수분 함량(PA ≤500ppm, PC ≤200ppm, PET ≤50ppm)을 Every Batch Fine 분석. 수분 초과 시 Pre-dry 추가 또는 Deviation 생성(표면 결함, 기포 위험). | 2 | process_step |
| Extruder 조건 | Zone temperature, torque, pressure trend를 pellet lot과 연결한다. DCS Historian에 T1~T10(Zone 온도 ±5°C), Screw speed(±10 RPM), Melt pressure(±5 barg), Torque(±5%)를 1초 주기 Real-time 저장. CPP limit excursion(온도, 압력, Torque) 시 자동 Alarm + Trend 저장. Pellet Lot ID ↔ Extruder Condition Record 연결(Pellet lot에서 Extruder 운전 이력 역추적 가능). | 4,5 | process_step |
| Silo blending | 연속 생산과 포장 lot 사이의 혼합·분할 관계를 추적한다. Homogenizing Silo / Blender Blend 시간(15~60분), 균질도(On-line Density/MFI ±2% 이내) 확인. Continuous blending 시 Time-window 기준 Lot ID 할당. Lot 간 물성 변동성(CpK ≥1.33) 관리. Blender에서 Packaging Line 이송 전 Metal Detector 검증. | 6,9 | process_step |
| 물성 Release Gate | MFI, 인장, 충격 등 결과로 grade release 또는 downgrade를 결정한다. UTM(Universal Testing Machine), MFI Melt Flow Indexer, Impact Tester 측정 결과(Every Batch) → LIMS → MES Gate Rule. All Pass → Grade Release(고객 출하 가능). 1항목 Fail → Downgrade(저등급 용도 전환) 또는 Reprocess Queue 할당 + Deviation. CPK(Capability Index) < 1.33이면 장기 공정 개선(Process improvement) 대상. | 7,10 | process_step |
| Reprocess genealogy | 재생·재작업 투입은 최종 lot genealogy에 반드시 포함한다. Reprocess Batch ID ↔ Original Batch ID Genealogy Tree MES 기록. Reprocess 투입 비율(0~30%, Grade별 허용 한도) Batch Record 명시. Recycled/Regrind Lot Quality Pre-check(물성, 오염, 분진) 기록 필수. | 8 | industry |
| Die/Screen 관리 | Die, screen pack, filter 교체 이력과 품질 이상을 연결한다. Screen pack(40~200 mesh) 교체 주기(8~24h 또는 압력 Delta P > 100 barg), Filter 교체 기록(Pressure rise profile). Die contamination(겔, Black spec, Carbon deposit) 발생 시 Die Cleaning 이력 역추적. Soft Sensor 기반 Melt quality(겔, Foreign particle) 실시간(Real-time) 모니터링 적용 가능. | 4,5 | process_step |

### 6.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| Grade与配方管理 | 同一产品族内的grade差异需通过配方和物性规格管理。Grade Master Recipe(树脂/添加剂/填料比例、挤出条件设定)由ERP/PLM管理。Grade物性Spec(MFI、密度、拉伸、冲击、HDT、颜色ΔE)按LIMS标准设定。Grade变更需Change Control批准。每批次(Every Batch)验证Recipe版本。 | 1,7 | process_step |
| 干燥与水分管理 | 原料水分和干燥条件影响挤出稳定性和物性。料斗干燥机/除湿干燥机温度(60~120°C)、露点(≤-40°C)、干燥时间(2~4h)设定。干燥后水分含量(PA≤500ppm、PC≤200ppm、PET≤50ppm)每批次(Every Batch)细分析。水分超标时追加干燥或生成Deviation(表面缺陷、气泡风险)。 | 2 | process_step |
| 挤出机条件 | 将各区温度、扭矩和压力趋势关联到颗粒批次。DCS Historian以1秒周期实时(Real-time)存储T1~T10(区段温度±5°C)、螺杆转速(±10 RPM)、熔体压力(±5 barg)、扭矩(±5%)。CPP限值偏离(温度、压力、扭矩)时自动报警+趋势存档。Pellet Lot ID↔Extruder条件记录关联(可从Pellet lot逆向追溯挤出机运行历史)。 | 4,5 | process_step |
| 料仓混合 | 追踪连续生产与包装批次之间的混合和拆分关系。均化料仓/混合机混合时间(15~60分钟)，均匀度(在线密度/MFI±2%以内)确认。连续混批时按时间窗口分配Lot ID。批间物性变异(CpK≥1.33)管理。混合器至包装线输送前通过金属检测器(Metal Detector)验证。 | 6,9 | process_step |
| 物性放行关口 | 按MFI、拉伸、冲击等结果决定grade放行或降级。万能材料试验机(UTM)、MFI熔融指数仪、冲击试验机测量结果(每批次)→LIMS→MES Gate Rule。全部Pass→Grade放行(可发货给客户)。1项Fail→降级(转为低等级用途)或再加工队列分配+Deviation。CpK<1.33时作为长期工艺改善对象。 | 7,10 | process_step |
| 再加工族谱 | 回用和返工投入必须进入最终批次族谱。再加工Batch ID↔原始Batch ID族谱树(Genealogy Tree) MES记录。再加工投入比例(0~30%，按Grade允许限度)在Batch Record中注明。回收料/粉碎回料Lot品质预检(物性、污染、粉尘)记录必须保存。 | 8 | industry |
| 模头/滤网管理 | 将模头、滤网包和过滤器更换历史与质量异常关联。滤网组(Screen pack，40~200 mesh)更换周期(8~24h或压力Delta P>100 barg)，过滤器更换记录(压力上升曲线)。模头污染(凝胶、黑点、碳沉积)发生时逆向追溯模头清洗历史。可应用Soft传感器基熔体质量(凝胶、异物)实时(Real-time)监控。 | 4,5 | process_step |

### 6.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Grade | process |  |  | recipe_id,batch_id |
| 2 | Drying | process |  |  | raw_lot_id,process_param |
| 3 | Kneading | batch |  |  | batch_id,recipe_id,process_param |
| 4 | Extrusion | batch | Extruder Condition Loop |  | extruder_id,mold_die_id,process_param |
| 5 | Pelletizing | process |  |  | pellet_lot,process_param |
| 6 | Blending | utility |  |  | pellet_lot,batch_id |
| 7 | QC Gate | gate |  | 4,5,6 | sample_id,lab_result,mfi_value,tensile_result |
| 8 | Reprocess | batch |  |  | batch_id,raw_lot_id |
| 9 | Packaging | process |  |  | package_lot,pellet_lot |
| 10 | Shipment | process |  |  | package_lot,lab_result |

### 6.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Grade | process |  |  | recipe_id,batch_id |
| 2 | Drying | process |  |  | raw_lot_id,process_param |
| 3 | Kneading | batch |  |  | batch_id,recipe_id,process_param |
| 4 | Extrusion | batch | Extruder Condition Loop |  | extruder_id,mold_die_id,process_param |
| 5 | Pelletizing | process |  |  | pellet_lot,process_param |
| 6 | Blending | utility |  |  | pellet_lot,batch_id |
| 7 | QC Gate | gate |  | 4,5,6 | sample_id,lab_result,mfi_value,tensile_result |
| 8 | Reprocess | batch |  |  | batch_id,raw_lot_id |
| 9 | Packaging | process |  |  | package_lot,pellet_lot |
| 10 | Shipment | process |  |  | package_lot,lab_result |

### 6.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 건조 조건 확인 |
| 4 | 1 | Extruder zone 기록 |
| 7 | 1 | MFI·인장 시험 |
| 8 | 1 | 재작업 투입 승인 |

### 6.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | 确认干燥条件 |
| 4 | 1 | 记录挤出机温区 |
| 7 | 1 | MFI与拉伸测试 |
| 8 | 1 | 返工投入批准 |

---

## 7. E07 `glass_ceramic_powder` — 유리·세라믹·분말소재 / 玻璃·陶瓷·粉体材料

```yaml
code: "E07"
legacy_slug: "glass_ceramic_powder"
label_ko: "유리·세라믹·분말소재"
label_zh: "玻璃·陶瓷·粉体材料"
label_en: ""
label_ja: ""
routing: "RT_BATCH_HIGH_TEMP"
flow_preset_id: "thermal_batch_v1"
expression_tier: "pflow_v0_3"
description_ko: "분말 배합, 소성·용융, 분쇄·분급, 표면처리와 lot 균일성이 핵심. Kiln/Furnace 조건, particle size, contamination 추적이 중요하다."
description_zh: "核心是粉体配料、烧成/熔融、粉碎分级、表面处理和批次均一性。需追踪窑炉条件、粒度和污染。"
data_capture_points:
  - raw_lot_id
  - batch_id
  - recipe_id
  - furnace_id
  - kiln_profile_id
  - milling_id
  - particle_size
  - sample_id
  - lab_result
  - contamination_result
  - package_lot
  - coa_id
```

### 7.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 원료 배합설계 | 산화물, 첨가제, flux 등 원료 비율과 recipe version을 확정한다. 유리/세라믹/분말용 Batch Formulation: SiO₂(60~75%), Al₂O₃(0~15%), CaO(5~15%), Na₂O(10~15%), MgO(0~5%), K₂O(0~5%), 기타 산화물(Fe₂O₃, TiO₂, ZrO₂, PbO, B₂O₃, ZnO) 미량. Frit(프릿) 조성, Flux, Stabilizer, Coloring oxide(CoO, Cr₂O₃, Fe₂O₃ 등) 비율 Recipe에 반영. 대표 제품: 판유리(Float glass), 병유리(Container glass), 타일(Tile), 위생도기(Sanitary ware), 전자세라믹(Al₂O₃ 기판/MLCC), 내화물(Refractory), 글라스울, 기능성 분말(실리카, 알루미나, 지르코니아). |
| 2 | 계량·혼합 | 분말 원료를 계량하고 균일 혼합한다. 중량 계량기(Gravimetric batch charger, Loss-in-weight, 정밀도 ±0.1~0.5%) 또는 체적 계량기. Batch Mixer(Eirich mixer / Pan mixer / Ribbon blender)에서 Batch 시간(3~10분), 균질도 확인(Sieve analysis). Batch Batch ID 발행, 각 Component Lot 정보 기록. 유리 용융용 Batch: Cullet(유리 깨짐) 10~60% 포함 → Cullet Lot ID 및 비율 기록. |
| 3 | 성형·Granulation | 필요 시 과립화, 압축, 슬러리화 등 전처리를 수행한다. 세라믹 타일: Spray dryer(스프레이 드라이어, Spray tower, Inlet temp 300~500°C, Outlet temp 80~120°C)로 Granule 제조(수분 5~8%). 건식 프레싱(Dry pressing, Hydraulic press 500~5000 ton) 또는 압출 성형(Extrusion, Auger extruder, Pug mill). 슬리퍼 캐스팅(Slip casting, Gypsum mold) 또는 Tape casting(Doctor blade, 슬러리 점도·두께 관리). 유리용: Float bath(용융 주석 위)에서 연속 성형. |
| 4 | 소성·용융 | Kiln/Furnace 온도 profile, 분위기, 시간, 적재 위치를 관리한다. 유리 용융로(Glass melting furnace, Gas/Oxy-fuel, Electric Boost, 온도 1400~1600°C), 세라믹 소성로(Kiln, Tunnel kiln / Roller kiln / Shuttle kiln, 온도 800~1500°C). Kiln Profile: 승온 속도(1~10°C/min), 소성 온도(1100~1600°C, 제품별 상이), 유지 시간(30min~12h), 냉각 속도(0.5~5°C/min). 분위기(Air/Oxidizing/Reducing/N₂). Kiln Car/Sagger/Setter 적재 위치(Furnace zone별 온도차 ±5~10°C) 기록. 에너지 소비(소성로 가스/전력) Real-time 모니터링. AI 기반 Kiln Profile 최적화로 에너지 5~10% 절감. |
| 5 | 냉각·분쇄 | 냉각 후 jaw mill, ball mill, jet mill 등으로 분쇄한다. 냉각(Annealing lehr / Controlled cooling, 400°C→상온, 0.5~2°C/min). 분쇄: Primary crusher(Jaw crusher), Secondary mill(Ball mill, Al₂O₃/ZrO₂ media, RPM 20~60), Fine grinding(Jet mill / Attrition mill / Vibratory mill). 분쇄 조건: Mill time(30min~12h), Media type/size, RPM, Feed rate. Batch별 분쇄 Lot ID 생성. |
| 6 | 분급·Sieving | 입도 분포와 oversize/undersize를 관리한다. Sieve shaker(Vibrating sieve / Air jet sieve, Mesh 20~500µm), Air classifier(Horizontal/Vertical classifier, RPM 1000~10000), Cyclone. 목표 PSD(D10, D50, D90) 설정: 예) D50 2~5µm(정밀세라믹), D50 10~50µm(일반 세라믹/유리 원료). Oversize > 3% 시 재분쇄 또는 재분급 회송. Particle Size Analyzer(Laser diffraction, Malvern) Every Batch 분석. |
| 7 | 표면처리·코팅 | 표면개질, coating, coupling 처리를 수행한다. Silane coupling agent treatment(Henschel mixer / Fluidized bed, 80~120°C, 10~30min), Mechanical fusion(Nara hybridization / Mechanofusion), Spray coating(실험실/파일럿). 표면처리 조건: 처리제 종류·농도·온도·시간 기록. Coating Lot ID ↔ Base Material Batch ID 연결. |
| 8 | 품질검사 | 입도, 조성, 수분, 오염, 색상, 결정상을 검사한다. 시험 항목: 입도 PSA(Laser diffraction, Malvern Mastersizer), 비표면적(BET, m²/g), 조성(XRF, ICP-OES), 결정상(XRD, Rietveld定量), 수분(KF, 한도 ≤0.5%), 색상(CIE L*a*b*), 오염(Fe₂O₃ 함량 ICP, 0.1~1.0% 한도), pH, 전도도. LIMS 결과(Every Batch) → MES Gate Rule: All Pass → Release, 1건 Fail → Hold + OOS. |
| 9 | 포장·방습 | 방습·방오염 조건으로 포장하고 package lot을 생성한다. 포장 단위: 25kg PP bag / PE liner + PP bag, Jumbo bag(500~1500kg), Drum. 방습 조건: Sealing(Heat sealer / Impulse sealer), Aluminium foil bag + Silica gel, N₂ seal. 방오염: Dust-proof cover / Liner. Pallet 포장 후 Stretch wrap. Package lot ID(Barcode) 생성 → Batch ID 1:N 연결. |
| 10 | 출하·CoA | 고객 grade, CoA, 보관 조건을 출하 lot과 연결한다. CoA(입도 D10/D50/D90, 조성 XRF/ICP, BET, 수분, 색상 L*a*b*, 오염 Fe₂O₃, 결정상) 자동 생성 + QA E-signature. 보관 조건(온도 5~35°C, RH < 60%, 직사광선 회피, 비흡착성 포장) ERP 출하 lot 연결. 고객 포털 EDI/Web 자동 Upload. |

### 7.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 原料配方设计 | 确定氧化物、添加剂和助熔剂等原料比例及配方版本。玻璃/陶瓷/粉体用Batch Formulation：SiO₂(60~75%)、Al₂O₃(0~15%)、CaO(5~15%)、Na₂O(10~15%)、MgO(0~5%)、K₂O(0~5%)、其他氧化物(Fe₂O₃、TiO₂、ZrO₂、PbO、B₂O₃、ZnO)微量。Frit(熔块)组成、助熔剂、稳定剂、着色氧化物(CoO、Cr₂O₃、Fe₂O₃等)比例反映于配方。代表产品：平板玻璃(Float glass)、瓶罐玻璃(Container glass)、瓷砖(Tile)、卫生陶瓷(Sanitary ware)、电子陶瓷(Al₂O₃基板/MLCC)、耐火材料(Refractory)、玻璃棉、功能粉体(硅石、氧化铝、氧化锆)。 |
| 2 | 称量与混合 | 称量粉体原料并均匀混合。失重式计量给料机(Gravimetric batch charger，Loss-in-weight，精度±0.1~0.5%)或体积式计量。批次混合机(Batch Mixer，Eirich mixer/Pan mixer/Ribbon blender)中混合时间(3~10分钟)，均匀度确认(筛分分析)。发放Batch ID，记录各组分Lot信息。玻璃熔融用Batch：含碎玻璃(Cullet)10~60%→记录Cullet Lot ID及比例。 |
| 3 | 成型与造粒 | 必要时执行造粒、压制或制浆等前处理。陶瓷砖：喷雾干燥塔(Spray dryer，Spray tower，进风温度300~500°C，出风温度80~120°C)造粒(水分5~8%)。干压成型(Dry pressing，液压机500~5000吨)或挤出成型(Extrusion，螺旋挤出机、练泥机)。注浆成型(Slip casting，石膏模)或流延成型(Tape casting，刮刀，浆料粘度/厚度管理)。玻璃用：浮法(Float bath，熔融锡上)连续成型。 |
| 4 | 烧成与熔融 | 管理窑炉温度曲线、气氛、时间和装载位置。玻璃熔窑(Glass melting furnace，燃气/氧燃，电助熔，温度1400~1600°C)，陶瓷窑炉(Kiln，隧道窑/辊道窑/梭式窑，温度800~1500°C)。窑炉曲线：升温速度(1~10°C/min)、烧成温度(1100~1600°C，因产品而异)、保温时间(30min~12h)、冷却速度(0.5~5°C/min)。气氛(Air/Oxidizing/Reducing/N₂)。窑车/匣钵/垫板装载位置(窑区温差±5~10°C)记录。能耗(窑炉燃气/电力)实时(Real-time)监控。AI基窑炉曲线优化能耗降低5~10%。 |
| 5 | 冷却与粉碎 | 冷却后通过颚破、球磨或气流磨等粉碎。冷却(退火窑Annealing lehr/可控冷却，400°C→室温，0.5~2°C/min)。粉碎：初碎(Jaw crusher)、二次粉碎(Ball mill，Al₂O₃/ZrO₂介质，RPM 20~60)、细磨(Jet mill/Attrition mill/Vibratory mill)。粉碎条件：研磨时间(30min~12h)、介质类型/尺寸、转速、进料速度。按批次生成粉碎Lot ID。 |
| 6 | 分级与筛分 | 管理粒度分布及过粗/过细部分。筛分机(Sieve shaker，振动筛/气流筛，目数20~500µm)、气流分级机(Air classifier，水平/垂直分级器，RPM 1000~10000)、旋风分离器(Cyclone)。目标PSD(D10、D50、D90)设定：例如D50 2~5µm(精密陶瓷)、D50 10~50µm(一般陶瓷/玻璃原料)。粗粒(Oversize)>3%时返回粉碎或重新分级。激光粒度分析仪(Laser diffraction，Malvern)每批次(Every Batch)分析。 |
| 7 | 表面处理与涂层 | 执行表面改性、涂层或偶联处理。硅烷偶联剂处理(Henschel混合机/流化床，80~120°C，10~30分钟)、机械融合(Nara hybridization/Mechanofusion)、喷涂(实验室/中试)。表面处理条件：处理剂种类·浓度·温度·时间记录。涂层Lot ID↔基材Batch ID关联。 |
| 8 | 质量检验 | 检测粒度、成分、水分、污染、颜色和晶相。检验项目：粒度PSA(激光衍射，Malvern Mastersizer)、比表面积(BET，m²/g)、成分(XRF，ICP-OES)、晶相(XRD，Rietveld定量)、水分(KF，限度≤0.5%)、颜色(CIE L*a*b*)、污染(Fe₂O₃含量ICP，0.1~1.0%限度)、pH、电导率。LIMS结果(每批次)→MES Gate规则：全部Pass→放行，1项Fail→Hold+OOS。 |
| 9 | 包装与防潮 | 按防潮、防污染条件包装并生成包装批次。包装单位：25kg PP袋/PE内衬+PP袋、吨包(Jumbo bag，500~1500kg)、桶。防潮条件：密封(热封机/脉冲封口机)、铝箔袋+硅胶、氮气密封。防污染：防尘罩/内衬。托盘包装后缠绕膜(Stretch wrap)。Package lot ID(Barcode)生成→Batch ID 1:N关联。 |
| 10 | 发货与CoA | 将客户grade、CoA和储存条件关联到发货批次。CoA(粒度D10/D50/D90、成分XRF/ICP、BET、水分、颜色L*a*b*、污染Fe₂O₃、晶相)自动生成+QA E-signature。储存条件(温度5~35°C、RH<60%、避免直射阳光、非吸附性包装)关联至ERP发货lot。支持自动上传客户门户(EDI/Web)。 |

### 7.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| 원료 배합 추적 | 원료 lot과 배합비가 최종 조성·입도·색상에 영향을 준다. Every Batch 배합비(Recipe formulation, SiO₂ 65±2%, Al₂O₃ 15±1%, CaO 8±1% 등) 검증. XRF 분석(입고 시)으로 각 산화물 Lot의 조성 균일성 확인. 배합 변화(Flux 종류/량 변경) 시 Change Control 필요. SiO₂, Cullet 등 Main Component Lot ID와 Batch ID 연결. | 1,2 | process_step |
| Kiln profile 관리 | 온도 profile, 분위기, 적재 위치가 소성 품질과 직접 연결된다. Kiln Thermocouple(Thermocouple Type K/S/R, 10~20개 zone)로 1초~1분 주기 Real-time 온도 수집. 온도 편차(Zone 간 ±5~10°C) Alarm 발생 시 Kiln Operator Notification. 분위기(O₂%, CO%, Reducing/Oxidizing) Gas Analyzer 연속 측정. Kiln Car ID 및 적재 위치(Position) 기록으로 Lot Batch 역추적 가능. Profile excursion 시 Deviation 생성 → 소성 조건 재검증. | 4 | process_step |
| 분쇄·분급 조건 | Mill, media, classifier 조건과 입도 결과를 batch에 연결한다. Ball Mill 조건: RPM(60~80% Critical speed), Media size(Ø10~50mm Al₂O₃/ZrO₂), Mill time(2~12h). Jet Mill 조건: Grinding pressure(5~10 barg), Classifier RPM(1000~10000). Air Classifier: Classifier RPM과 Cut point(D50) 상관관계 관리. PSD(Laser diffraction, Malvern, Every Batch) → Mill/Cassifier 조건 설정 피드백. | 5,6 | process_step |
| 오염 관리 | Metal contamination, cross contamination, cleaning 상태를 lot별로 관리한다. Metal contamination: Fe 함량(ICP, Magnetic separator 전/후 비교, 한도 ≤100~500ppm). Mill media 마모(Mill Line/Al₂O₃ brick/Alubit ball) 상태 점검 주기(월 1회). Cleaning Log(전 Lot 생산 품목 → Cleaning Agent/wash → Post-Cleaning Swab test/Rinse water 분석) Batch 전 검증. | 5,8 | industry |
| 표면처리 recipe | 표면처리 조건과 coating lot을 최종 제품 genealogy에 포함한다. Surface treatment 조건: 처리제 종류/농도/온도(80~120°C)/시간(10~30min) Recipe화. Coating Lot ID ↔ Base Material Batch ID 1:1 Genealogy 연결. Coating 후 검사(Water contact angle, BET 변화, Silane coupling efficiency by TGA/FTIR) Every Batch. | 7 | process_step |
| 품질 Release Gate | 입도, 조성, 오염 결과가 없으면 포장·출하를 차단한다. LIMS 결과(PSD, XRF/ICP, BET, XRD, KF moisture, Color L*a*b*, Fe₂O₃ contaminant) Every Batch 수신 → MES Gate Rule. All Pass → Package Release. 1건 Fail → Batch Hold + OOS Investigation. 품질 결과 Database로 CpK ≥1.33 지속 관리. | 8,9 | process_step |
| 방습·포장 | 분말 소재는 수분·이물에 민감하므로 포장 조건을 추적한다. 포장 환경: RH(상대습도) ≤50% 청정실(ISO Class 7~8) 필요. 포장 단위별 Moisture Barrier 검증(Al foil + Silica gel + N₂ seal). Package lot Seal integrity(Seal strength test / Vacuum decay test) Every Lot 검증 기록. 분진 비산 방지(Dust collector / HEPA filter) 상태 확인. | 9,10 | process_step |

### 7.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| 原料配比追溯 | 原料批次和配比影响最终成分、粒度和颜色。每批次(Every Batch)验证配比(Recipe formulation，SiO₂ 65±2%、Al₂O₃ 15±1%、CaO 8±1%等)。XRF分析(收货时)确认各氧化物Lot的组成均匀性。配比变化(助熔剂种类/量变更)需Change Control。SiO₂、Cullet等主要组分Lot ID与Batch ID关联。 | 1,2 | process_step |
| 窑炉曲线管理 | 温度曲线、气氛和装载位置直接影响烧成质量。窑炉热电偶(Thermocouple Type K/S/R，10~20个区)以1秒~1分钟周期实时(Real-time)采集温度。温度偏差(区段间±5~10°C)报警时通知窑炉操作员。气氛(O₂%、CO%、还原/氧化)通过气体分析仪连续测量。记录窑车ID及装载位置(Position)实现批次逆向追溯。Profile偏离时生成Deviation→烧成条件再验证。 | 4 | process_step |
| 粉碎与分级条件 | 将磨机、介质和分级条件与粒度结果关联。球磨机条件：RPM(60~80%临界转速)、介质尺寸(Ø10~50mm Al₂O₃/ZrO₂)、研磨时间(2~12h)。气流磨条件：粉碎压力(5~10 barg)、分级器RPM(1000~10000)。气流分级器：分级器RPM与切割点(D50)相关性管理。PSD(激光衍射，Malvern，每批次)→反馈调整磨机/分级器条件设置。 | 5,6 | process_step |
| 污染管理 | 按批次管理金属污染、交叉污染和清洁状态。金属污染：Fe含量(ICP，磁选机前/后对比，限度≤100~500ppm)。磨机介质磨损(Mill衬里/Al₂O₃砖/Alubit球)状态检查周期(每月1次)。批次前验证清洁日志(前批产品→清洗剂/清洗→清洗后Swab test/冲洗水分析)。 | 5,8 | industry |
| 表面处理配方 | 将表面处理条件和涂层批次纳入最终产品族谱。表面处理条件：处理剂种类/浓度/温度(80~120°C)/时间(10~30min)配方化管理。涂层Lot ID↔基材Batch ID 1:1族谱关联。涂层后检验(水接触角、BET变化、TGA/FTIR测硅烷偶联效率)每批次(Every Batch)。 | 7 | process_step |
| 质量放行关口 | 无粒度、成分和污染结果时阻断包装与发货。LIMS结果(PSD、XRF/ICP、BET、XRD、KF水分、颜色L*a*b*、Fe₂O₃污染物)每批次(Every Batch)接收→MES Gate规则。全部Pass→包装放行。1项Fail→Batch Hold+OOS调查。质量结果Database管理CpK≥1.33持续改进。 | 8,9 | process_step |
| 防潮与包装 | 粉体材料对水分和异物敏感，需要追踪包装条件。包装环境：RH(相对湿度)≤50%洁净室(ISO Class 7~8)要求。各包装单位防潮性验证(铝箔+硅胶+氮气密封)。Package lot密封完整性(密封强度测试/真空衰减测试)每批次(Every Lot)验证记录。粉尘飞散防止(集尘器/HEPA过滤器)状态确认。 | 9,10 | process_step |

### 7.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Formula | process |  |  | recipe_id,raw_lot_id |
| 2 | Mixing | batch |  |  | batch_id,recipe_id |
| 3 | Forming | process |  |  | batch_id,process_param |
| 4 | Thermal | batch | Kiln / Furnace Profile Loop |  | furnace_id,kiln_profile_id,batch_id |
| 5 | Milling | process |  |  | milling_id,batch_id |
| 6 | Classification | process |  |  | particle_size,batch_id |
| 7 | Surface | batch |  |  | recipe_id,batch_id |
| 8 | QC Gate | gate |  | 4,5,6,7 | sample_id,lab_result,particle_size,contamination_result |
| 9 | Packaging | process |  |  | package_lot,batch_id |
| 10 | Shipment | process |  |  | package_lot,coa_id |

### 7.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Formula | process |  |  | recipe_id,raw_lot_id |
| 2 | Mixing | batch |  |  | batch_id,recipe_id |
| 3 | Forming | process |  |  | batch_id,process_param |
| 4 | Thermal | batch | Kiln / Furnace Profile Loop |  | furnace_id,kiln_profile_id,batch_id |
| 5 | Milling | process |  |  | milling_id,batch_id |
| 6 | Classification | process |  |  | particle_size,batch_id |
| 7 | Surface | batch |  |  | recipe_id,batch_id |
| 8 | QC Gate | gate |  | 4,5,6,7 | sample_id,lab_result,particle_size,contamination_result |
| 9 | Packaging | process |  |  | package_lot,batch_id |
| 10 | Shipment | process |  |  | package_lot,coa_id |

### 7.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | Kiln profile 지정 |
| 5 | 1 | 분쇄 media 확인 |
| 8 | 1 | 입도·오염 판정 |
| 9 | 1 | 방습 포장 확인 |

### 7.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | 指定窑炉曲线 |
| 5 | 1 | 确认研磨介质 |
| 8 | 1 | 粒度与污染判定 |
| 9 | 1 | 防潮包装确认 |

---

## 8. E08 `medical_materials_surface_treatment` — 의료기기용 소재·표면처리 / 医疗器械材料·表面处理

```yaml
code: "E08"
legacy_slug: "medical_materials_surface_treatment"
label_ko: "의료기기용 소재·표면처리"
label_zh: "医疗器械材料·表面处理"
label_en: ""
label_ja: ""
routing: "RT_BATCH_REGULATED"
flow_preset_id: "regulated_process_v1"
expression_tier: "pflow_v0_3"
description_ko: "의료용 금속·고분자·세라믹 소재와 표면처리. 소재 lot, heat/coil/billet genealogy, 세척·표면처리 recipe, 생체적합·청정도·추적성이 핵심이다."
description_zh: "面向医疗用金属、高分子、陶瓷材料及表面处理。核心是材料lot、炉号/卷号/坯料族谱、清洗与表面处理配方、生物相容性、洁净度和追溯。"
data_capture_points:
  - material_heat_no
  - raw_lot_id
  - batch_id
  - recipe_id
  - equipment_id
  - surface_treatment_id
  - cleaning_status
  - sample_id
  - lab_result
  - biocompatibility_ref
  - sterile_barrier_lot
  - coa_id
```

### 8.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 규격·재질 승인 | 의료용 재질 규격, 고객 도면, 규제 요구, 소재 heat/lot을 확인한다. 의료용 재질 표준: ASTM F138(316L 스테인리스), ASTM F67/ ASTM F136(Ti Grade 1~4 / Ti-6Al-4V), ASTM F75(Co-Cr 합금), ISO 5832 시리즈, ASTM F1088(의료용 PEEK). 재질 인증서(MTR, Mill Test Report, Heat No./ Melt No./ Lot No.)를 ERP에서 검증. 생체적합성 근거(DMF, ISO 10993 시험 보고서) 등록 확인. 대표 제품: 의료용 스테인리스 봉재/선재(Wire), Ti 봉재/판재, Co-Cr 합금 소재, 생분해성 고분자(PLA/PGA), 생체세라믹(Hydroxyapatite), 의료용 코팅 원료. |
| 2 | 절단·전처리 | 봉재, 선재, 판재를 절단하고 표면 오염을 제거한다. 절단 장비: Band saw / Abrasive cut-off saw / CNC wire EDM, 절단 치수 공차 ±0.1~0.5mm(고객 도면 기준). 전처리: Degreasing(알칼리/초음파 세척, 40~60°C, 5~15분), Descaling(산세: HNO₃+HF / Mechanical grinding). 표면 Cleaning 후 Water break test(소수성 불균일 확인). 절단 Batch Lot ID ↔ Heat No./Coil No. 연결. |
| 3 | 열처리·성형 | 열처리, 교정, 성형 조건과 furnace profile을 관리한다. 열처리 Furnace(Vacuum furnace / Atmosphere furnace / Box furnace): 온도 200~1200°C(재질별 상이), 분위기(Vacuum 10⁻⁵ Torr/Ar/N₂/H₂), 승온 속도(2~10°C/min), 유지 시간(30min~4h), Quenching(Water/Oil/Air/N₂). 교정(Straightening, Roller / Press straightener, Bow ≤ 0.5mm/m). 성형(Bending, Swaging, Drawing, Forging, Rolling). Heat Treat Batch ID → Furnace Profile 기록 → Material property 경화물성(Tensile, Hardness, Microstructure) 시험. Gate(Inspection) 포인트: 열처리 후 기계적 특성 검증 필요(Step 7에서 확인). |
| 4 | 기계가공·연마 | 가공 치수, burr, 표면 거칠기, tool 상태를 관리한다. CNC Machining Center(Turning / Milling / Drilling), Swiss-type auto lathe(의료용 소형 부품). 가공 공차: 일반 ±0.01~0.05mm, 정밀 ±0.005mm. 표면 거칠기(Ra ≤ 0.2~0.8µm, 고객 도면 기준). Burr 제거(Deburring, Mechanical / Electrochemical / Thermal). Tool Life Management(Lot 사용 횟수, 교체 주기). In-process Inspection(Go/No-go gage, CMM, Vision system) Every Batch. |
| 5 | 세척·Passivation | 세척 recipe, passivation 조건, 청정도 기준을 관리한다. ASTM A380/A967(스테인리스 Passivation): HNO₃ 20~50% + Na₂Cr₂O₇ 2~6% 또는 Citric Acid 4~10%, 20~60°C, 20~60분. Ultrasonic cleaning(알칼리/탈이온수/에탄올, 20~60kHz, 40~60°C, 5~15분). Rinsing(탈이온수 Resistivity ≥10MΩ·cm, 최종 Rinse water Conductivity ≤1µS/cm). Cleanliness: Residual contamination 검사(Organic: GC-MS, Inorganic: SEM-EDX / ICP). Cleaning Batch ID → Cleaning Recipe 기록. Gate(Inspection) 포인트: 세척 후 청정도 검증 필요(Step 7에서 확인). |
| 6 | 표면처리·코팅 | Anodizing, blasting, coating, functional surface treatment를 수행한다. Anodizing(의료용 Ti/Ti-6Al-4V, Type II/III, Electrolyte H₂SO₄/H₃PO₄, 전압 10~100V, 두께 5~50µm, 색상 관리). Blasting(Al₂O₃/SiO₂ abrasive, Grit size 30~200µm, 압력 2~8 barg → 표면 거칠기 Ra 0.5~3µm). Coating(HA coating: Plasma spray / Sol-gel, 두께 50~200µm, 결정도/접착력); DLC(Diamond-like Carbon, PVD/CVD, 경도 15~30GPa); 약물 용출 코팅(Drug-eluting, Polymer + drug layer). 표면처리 조건(전압/전류, Temp, Time, Coating thickness, Adhesion strength) Recipe화. Coating Batch ID → Surface Treatment Record 연결. |
| 7 | 검사·시험 | 치수, 표면, 조성, 청정도, 기계적 특성, 생체적합 근거를 확인한다. 시험 항목: 치수(CMM, Vision system, Micrometer), 표면 거칠기(Profilometer, Ra ≤ Spec), 표면 결함(Visual inspection 10x, Dye penetrant, SEM), 조성(PMI/OES, XRF), 청정도(SEM-EDX 잔류 탄소/입자), 기계적 특성(UTM Tensile/Hardness), 생체적합 근거(ISO 10993 시험 보고서 참조). LIMS + MES Gate Rule: All Pass → Release, 1건 Fail → Hold + Non-conformance Report(NCR). |
| 8 | Traceability Review | 소재 heat부터 표면처리 batch까지 genealogy를 검토한다. Genealogy Chain: Heat No.(Melt No.) → Raw Material Lot → Machining Batch → Heat Treat Batch → Cleaning Batch → Surface Treatment Batch → Final Inspection Batch → Packaging Lot → Shipment Lot. MES Genealogy Dashboard에서 1차원으로 전 공정 추적 검증. 누락 링크 발견 시 Batch Hold → QA Review. ISO 13485 / FDA 21 CFR Part 820 / EU MDR 추적성 요구사항 충족 확인. Gate(Inspection) 포인트: 출하 전 최종 추적성 검증. |
| 9 | 포장·보관 | 의료용 포장, sterile barrier 또는 청정 포장 lot을 연결한다. 의료용 포장: Blister pack / Tyvek pouch / Double barrier bag(PE + Nylon/Al), Sealing(Heat sealer, Seal width ≥3mm, Seal integrity test). Clean room packaging(ISO Class 7~8), Sterile barrier(ETO Sterilization / Gamma irradiation / Steam Autoclave 가능). Label(UDI 코드: GTIN + Production Identifier(Expiry/Batch/Serial), 의료기기 라벨 규격 FDA UDI / EU MDR). Package lot ID(Barcode) 생성 → Batch ID 1:N 연결. |
| 10 | 출하·문서마감 | CoA, 검사성적서, 고객 문서, 변경·deviation을 마감한다. 출하 문서: CoA(재질/기계적 특성/표면처리/청정도/생체적합), 검사성적서(Inspection Certificate 3.1 per EN 10204), 고객 요구 문서(PFMEA, Control Plan, PPAP Level 3, MTR, BOM). 변경 이력(Engineering Change Notice, ECN) 및 Deviation(NCR) 승인 완료 확인. QA 최종 Release 전자서명(E-signature) → ERP 출하 lot 연결 → 고객 EDI/Portal 전송. |

### 8.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 规格与材料批准 | 确认医疗材料规格、客户图纸、法规要求和材料炉号/批次。医用材料标准：ASTM F138(316L不锈钢)、ASTM F67/ASTM F136(Ti Grade 1~4/Ti-6Al-4V)、ASTM F75(Co-Cr合金)、ISO 5832系列、ASTM F1088(医用PEEK)。材料证书(MTR，Mill Test Report，Heat No./Melt No./Lot No.)在ERP中验证。确认生物相容性依据(DMF、ISO 10993测试报告)注册。代表产品：医用不锈钢棒/丝(Wire)、Ti棒/板、Co-Cr合金材料、可生物降解聚合物(PLA/PGA)、生物陶瓷(Hydroxyapatite)、医用涂层原料。 |
| 2 | 切割与前处理 | 切割棒材、线材或板材，并去除表面污染。切割设备：带锯(Band saw)/砂轮切割机(Abrasive cut-off saw)/CNC线切割(Wire EDM)，切割尺寸公差±0.1~0.5mm(按客户图纸)。前处理：脱脂(Degreasing，碱液/超声波清洗，40~60°C，5~15分钟)、去氧化皮(Descaling，酸洗HNO₃+HF/机械研磨)。表面清洗后Water break test(疏水不均匀确认)。切割Batch Lot ID↔Heat No./Coil No.关联。 |
| 3 | 热处理与成形 | 管理热处理、矫直、成形条件和炉温曲线。热处理炉(Vacuum furnace/气氛炉/箱式炉)：温度200~1200°C(因材料而异)、气氛(Vacuum 10⁻⁵ Torr/Ar/N₂/H₂)、升温速度(2~10°C/min)、保温时间(30min~4h)、淬火(Water/Oil/Air/N₂)。矫直(Straightening，Roller/Press矫直机，弯曲度Bow≤0.5mm/m)。成形(Bending、Swaging、Drawing、Forging、Rolling)。Heat Treat Batch ID→Furnace Profile记录→材料力学性能(Tensile、Hardness、Microstructure)测试。Gate(Inspection)节点：热处理后需验证机械特性(Step 7确认)。 |
| 4 | 机加工与抛光 | 管理加工尺寸、毛刺、表面粗糙度和刀具状态。CNC加工中心(Turning/Milling/Drilling)、瑞士型自动车床(Swiss-type auto lathe，医用小型零件)。加工公差：一般±0.01~0.05mm，精密±0.005mm。表面粗糙度(Ra≤0.2~0.8µm，按客户图纸)。去毛刺(Deburring，机械/电化学/热力法)。刀具寿命管理(Lot使用次数、更换周期)。过程检验(In-process Inspection，Go/No-go量规、CMM、视觉系统)每批次(Every Batch)。 |
| 5 | 清洗与钝化 | 管理清洗配方、钝化条件和洁净度标准。ASTM A380/A967(不锈钢钝化)：HNO₃ 20~50%+Na₂Cr₂O₇ 2~6%或柠檬酸4~10%，20~60°C，20~60分钟。超声波清洗(碱液/去离子水/乙醇，20~60kHz，40~60°C，5~15分钟)。漂洗(去离子水Resistivity≥10MΩ·cm，最终漂洗水电导率≤1µS/cm)。洁净度：残留污染物检查(有机：GC-MS，无机：SEM-EDX/ICP)。清洗Batch ID→清洗配方记录。Gate(Inspection)节点：清洗后需验证洁净度(Step 7确认)。 |
| 6 | 表面处理与涂层 | 执行阳极氧化、喷砂、涂层或功能性表面处理。阳极氧化(医用Ti/Ti-6Al-4V，Type II/III，电解液H₂SO₄/H₃PO₄，电压10~100V，厚度5~50µm，颜色管理)。喷砂(Al₂O₃/SiO₂磨料，Grit 30~200µm，压力2~8 barg→表面粗糙度Ra 0.5~3µm)。涂层(HA涂层：等离子喷涂/溶胶-凝胶，厚度50~200µm，结晶度/附着力)；DLC(类金刚石涂层，PVD/CVD，硬度15~30GPa)；药物洗脱涂层(Drug-eluting，聚合物+药物层)。表面处理条件(电压/电流、温度、时间、涂层厚度、附着力)配方化。Coating Batch ID→表面处理记录关联。 |
| 7 | 检验与测试 | 确认尺寸、表面、成分、洁净度、机械性能和生物相容性依据。检验项目：尺寸(CMM、视觉系统、千分尺)、表面粗糙度(轮廓仪，Ra≤Spec)、表面缺陷(目视检查10x、渗透染色、SEM)、成分(PMI/OES、XRF)、洁净度(SEM-EDX残留碳/颗粒)、机械性能(UTM拉伸/硬度)、生物相容性依据(参照ISO 10993测试报告)。LIMS+MES Gate规则：全部Pass→放行，1项Fail→Hold+不符合报告(NCR)。 |
| 8 | 追溯审核 | 审核从材料炉号到表面处理批次的族谱。族谱链：Heat No.(Melt No.)→Raw Material Lot→Machining Batch→Heat Treat Batch→Cleaning Batch→Surface Treatment Batch→Final Inspection Batch→Packaging Lot→Shipment Lot。通过MES族谱仪表盘(Genealogy Dashboard)一维追溯全工艺验证。发现链接缺失时Batch Hold→QA审核。确认符合ISO 13485/FDA 21 CFR Part 820/EU MDR追溯要求。Gate(Inspection)节点：发货前最终追溯性验证。 |
| 9 | 包装与储存 | 关联医疗包装、无菌屏障或洁净包装批次。医疗包装：泡壳包装(Blister pack)/Tyvek袋/双重屏障袋(PE+Nylon/Al)，密封(热封机，密封宽度≥3mm，密封完整性测试)。洁净室包装(ISO Class 7~8)，无菌屏障(EO灭菌/Gamma辐照/蒸汽高压灭菌适用)。标签(UDI码：GTIN+生产标识符(有效期/批次/序列号)，医疗器械标签规范FDA UDI/EU MDR)。Package lot ID(Barcode)生成→Batch ID 1:N关联。 |
| 10 | 发货与文件关闭 | 关闭CoA、检验报告、客户文件、变更和偏差。发货文件：CoA(材料/机械性能/表面处理/洁净度/生物相容性)、检验报告(Inspection Certificate 3.1 per EN 10204)、客户要求文件(PFMEA、Control Plan、PPAP Level 3、MTR、BOM)。变更历史(Engineering Change Notice，ECN)及Deviation(NCR)批准完成确认。QA最终放行电子签名(E-signature)→ERP发货lot关联→客户EDI/Portal发送。 |

### 8.3 control_points_detail_ko

| category | text | step_refs | scope |
|---|---|---|---|
| 소재 genealogy | Heat no, coil, billet, raw lot을 완제품·출하 문서까지 연결한다. Mill Certificate(MTR, Heat No./ Melt No.) ERP 등록, Every Raw Material Lot과 Heat No. 1:1 연결. Machining/Laser Marking으로 개별 부품에 Heat No. + Batch No. 마킹. MES genealogy dashboard로 전 공정 1차원 추적(Heat→Final Product→Shipment) 실시간(Real-time) 조회. 추적성 누락 시 Step 8 Gate에서 Batch Hold. | 1,8 | process_step |
| 열처리 조건 | Furnace profile과 material property를 lot별로 연결해야 한다. Vacuum furnace / Atmosphere furnace 온도 profile(2~10°C/min ramp, 유지 30min~4h, ±5°C) Real-time 수집. Quenching(Cooling rate, Oil/Water/Air/N₂ temp) Every Batch 기록. Mechanical properties(Tensile ASTM E8/E8M, Hardness HRC/HV, Microstructure grain size ASTM E112) 시험 결과(Every Batch) → Heat Treat 조건 피드백. Limit excursion 시 Deviation 생성 + 재열처리(Re-heat treat) 또는 폐기. | 3,7 | process_step |
| 표면 청정도 | 세척·passivation 조건과 잔류물·오염 검사 결과를 연결한다. Cleaning/Passivation 조건 Recipe화: 세척제 종류/농도, 온도(20~60°C), 시간(20~60분), Ultrasonic frequency(20~60kHz). Rinse water Conductivity(≤1µS/cm), Resistivity(≥10MΩ·cm) Every Batch 기록. 잔류 오염 검사: Organic(GC-MS, ≤0.1mg/cm²), Inorganic(SEM-EDX, 1~5 particles > NVR limit). 비적합 시 Re-cleaning → 재시험 → Pass 확인. | 5,7 | process_step |
| 표면처리 recipe | 표면처리 조건은 생체적합성과 기능 성능에 영향을 주므로 recipe화한다. Anodizing: 전압(10~100V), 전류(A/dm²), 전해질 온도(0~20°C), 두께(5~50µm), 색상 CIE L*a*b* 관리. Coating: Plasma spray parameters(Distance mm, Powder feed rate g/min), Coating thickness(50~200µm), Porosity(≤5%), Bond strength(ASTM C633 ≥15MPa). Coating Batch ID별 조건(Recipe Version) 및 검사 결과 기록. | 6 | process_step |
| 규제 문서 | 검사성적서, CoA, 고객 요구 문서를 lot별로 보존한다. EN 10204 Type 3.1/3.2 Inspection Certificate, CoA(재질성분, 기계적 특성, 표면처리, 청정도, 생체적합 근거). 고객 요구 문서(PFMEA, Control Plan, PPAP, DMR, DHR) Lot별 번들 보존. 규제 기관(FDA, NB) Audit 대비 15년 보존(의료기기 규제 기준). | 7,10 | industry |
| 추적성 Review Gate | 소재부터 포장까지 genealogy 누락 시 출하를 차단한다. MES Genealogy Check: Heat No. → Raw Lot → Processing batch(Heat/Clean/Surface/Inspection) → Package Lot → Shipment Lot 모든 링크 존재 여부 자동 검증. 누락 링크 발견 시 화면에 Red Flag 표시 + Batch Hold + E-mail Notification. QA Manager 수동 해제(Hold Release)만 가능. | 8,9 | process_step |
| 변경·Deviation | 소재 대체, 공정조건 변경, 재작업은 고객 승인·문서화가 필요하다. Engineering Change Notice(ECN): 재질 변경, 공정 변경, 설비 변경, 유틸리티 변경 시 고객(의료기기 제조사) 사전 승인 필요. Deviation(Non-conformance Report, NCR): off-spec, 공정 이탈, 재작업 → 고객 승인(고객 QA 부서) 후 처리. 모든 변경 History Lot별 추적 가능. | 1,10 | industry |

### 8.4 control_points_detail_zh

| category | text | step_refs | scope |
|---|---|---|---|
| 材料族谱 | 将炉号、卷号、坯料和原料批次连接到成品与发货文件。Mill Certificate(MTR，Heat No./Melt No.)在ERP中注册，每原料批次(Every Raw Material Lot)与Heat No. 1:1关联。通过机加工/激光打标在各零件上标注Heat No.+Batch No.。MES族谱仪表盘实时(Real-time)查询全工艺一维追溯(Heat→最终产品→出货)。追溯缺失时Step 8 Gate中Batch Hold。 | 1,8 | process_step |
| 热处理条件 | 炉温曲线和材料性能必须按批次关联。真空炉/气氛炉温度曲线(2~10°C/min ramp，保温30min~4h，±5°C)实时(Real-time)采集。淬火(冷却速度、油/水/空气/N₂温度)每批次(Every Batch)记录。力学性能(拉伸ASTM E8/E8M、硬度HRC/HV、晶粒度ASTM E112)测试结果(每批次)→反馈至热处理条件。限值偏离时生成Deviation+重新热处理或报废。 | 3,7 | process_step |
| 表面洁净度 | 将清洗、钝化条件与残留物和污染检验结果关联。清洗/钝化条件配方化：清洗剂种类/浓度、温度(20~60°C)、时间(20~60分钟)、超声波频率(20~60kHz)。漂洗水电导率(≤1µS/cm)、电阻率(≥10MΩ·cm)每批次(Every Batch)记录。残留污染物检查：有机(GC-MS，≤0.1mg/cm²)、无机(SEM-EDX，1~5颗粒超出NVR限度)。不符合时重新清洗→复测→Pass确认。 | 5,7 | process_step |
| 表面处理配方 | 表面处理条件影响生物相容性和功能性能，需要配方化管理。阳极氧化：电压(10~100V)、电流(A/dm²)、电解液温度(0~20°C)、厚度(5~50µm)、颜色CIE L*a*b*管理。涂层：等离子喷涂参数(距离mm、送粉率g/min)、涂层厚度(50~200µm)、孔隙率(≤5%)、结合强度(ASTM C633≥15MPa)。Coating Batch ID关联条件(Recipe Version)及检验结果记录。 | 6 | process_step |
| 法规文件 | 按批次保存检验报告、CoA和客户要求文件。EN 10204 Type 3.1/3.2检验证书、CoA(材料成分、力学性能、表面处理、洁净度、生物相容性依据)。客户要求文件(PFMEA、Control Plan、PPAP、DMR、DHR)按批次打包保存。为监管机构(FDA、NB)审计保留15年(医疗器械监管标准)。 | 7,10 | industry |
| 追溯审核关口 | 从材料到包装的族谱缺失时阻断发货。MES族谱检查：Heat No.→Raw Lot→加工批次(热处理/清洗/表面/检验)→Package Lot→Shipment Lot所有链接存在性自动验证。发现缺失链接时屏幕红色标记+批次暂停+邮件通知。仅QA经理可手动解除暂停(Hold Release)。 | 8,9 | process_step |
| 变更与偏差 | 材料替代、工艺条件变更和返工需要客户批准和文件化。工程变更通知(ECN)：材料变更、工艺变更、设备变更、公用工程变更时需客户(医疗器械制造商)事先批准。偏差(Non-conformance Report，NCR)：off-spec、工艺偏离、返工→客户批准(客户QA部门)后处理。所有变更历史按Lot可追溯。 | 1,10 | industry |

### 8.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | gate |  | 2,3 | material_heat_no,raw_lot_id,recipe_id |
| 2 | Prep | process |  |  | raw_lot_id,batch_id |
| 3 | Heat Treat | batch | Heat Treatment Profile Loop |  | equipment_id,batch_id,process_param |
| 4 | Machining | process |  |  | equipment_id,batch_id |
| 5 | Cleaning | batch |  |  | cleaning_status,recipe_id,batch_id |
| 6 | Surface | batch |  |  | surface_treatment_id,recipe_id,batch_id |
| 7 | Inspection | gate |  | 3,4,5,6 | sample_id,lab_result,biocompatibility_ref |
| 8 | Trace Review | gate |  | 1,2,3,4,5,6,7 | material_heat_no,batch_id,coa_id |
| 9 | Packaging | process |  |  | sterile_barrier_lot,batch_id |
| 10 | Release | gate |  | 8,9 | coa_id,lab_result |

### 8.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | gate |  | 2,3 | material_heat_no,raw_lot_id,recipe_id |
| 2 | Prep | process |  |  | raw_lot_id,batch_id |
| 3 | Heat Treat | batch | Heat Treatment Profile Loop |  | equipment_id,batch_id,process_param |
| 4 | Machining | process |  |  | equipment_id,batch_id |
| 5 | Cleaning | batch |  |  | cleaning_status,recipe_id,batch_id |
| 6 | Surface | batch |  |  | surface_treatment_id,recipe_id,batch_id |
| 7 | Inspection | gate |  | 3,4,5,6 | sample_id,lab_result,biocompatibility_ref |
| 8 | Trace Review | gate |  | 1,2,3,4,5,6,7 | material_heat_no,batch_id,coa_id |
| 9 | Packaging | process |  |  | sterile_barrier_lot,batch_id |
| 10 | Release | gate |  | 8,9 | coa_id,lab_result |

### 8.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 1 | 1 | 소재 Heat 확인 |
| 3 | 1 | 열처리 profile 수집 |
| 5 | 1 | 세척 recipe 실행 |
| 8 | 1 | genealogy review |
| 10 | 1 | 문서 release |

### 8.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 1 | 1 | 确认材料炉号 |
| 3 | 1 | 采集热处理曲线 |
| 5 | 1 | 执行清洗配方 |
| 8 | 1 | 族谱审核 |
| 10 | 1 | 文件放行 |

---

## 9. Self-check

- [x] E01~E08 전수, slug당 v0.3 섹션 완비
- [x] `control_points_detail`에 `category` 열 전건 작성
- [x] `step_expression_ko/zh` 행 수 = process_steps 행 수
- [x] `role=gate`에는 `gate_for` 작성
- [x] `trace_keys`는 slug별 `data_capture_points` 부분집합으로 작성
- [x] Batch/Process 산업 특성 반영: Recipe, Tank/Vessel, Batch Record, Lab Result, CoA, EHS
- [x] ko/zh step 수·step_refs·role·gate_for·trace_keys 동형
- [x] en/ja 섹션 없음

## 10. 적용 제외

- JSON 반영 없음
- 코드 수정 없음
- 변환 스크립트 실행 없음
- `control_points_ko/zh` 중복 작성 없음
