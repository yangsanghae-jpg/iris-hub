# A1 Ch3 H산업 공정 상세 데이터팩 v0.3 — ko/zh

> 파일명: `a1_ch3_H_process_detail_runtime_datapack_ko_zh_v0_3_2026-07-06.md`  
> 대상: A1 Ch3 `process_detail_v1.json` 백필 전 MD 정본 후보  
> 범위: H01~H08 자동차·모빌리티 제조  
> 작성 원칙: 코드·JSON·스크립트 수정 없음. MD 데이터팩만 작성.  
> 언어: 한국어/중국어만 작성. `label_en`, `label_ja`는 공백 정책.

---

## 0. 작성 기준

이 문서는 B산업 리팩 지시서의 v0.3 구조를 H산업에 적용한 초안이다. Ch3 pflow가 실제 소비하는 `module`, `role`, `gate_for`, `loop_hint`, `trace_keys`, `operations`, `category`를 명시한다.

### 0.1 H산업 해석

H산업은 완성차·파워트레인·차체·전장·내외장·타이어·Tier 부품을 포함하는 자동차·모빌리티 제조군이다. 공통 문법은 다음과 같다.

- **VIN / Serial / Lot genealogy**: 완성차는 VIN, 부품은 Serial/Lot 기준으로 자재·공정·검사·출하 이력을 연결한다.
- **JIT/JIS / Line feeding**: OEM 및 Tier 공급망에서는 생산서열, Line-side 공급, ASN, Kit 단위가 중요하다.
- **APQP / PPAP / ECR·ECN**: 고객도면·변경점·승인 상태가 생산 라우팅과 검사계획을 직접 제어한다.
- **EOL Test / Calibration**: 완성차, 전동화 파워트레인, 전장품은 EOL 시험과 Calibration 결과가 출하판정의 핵심이다.
- **IATF식 품질 체계**: 공정능력, 고객특성치, 8D, Traceability, 변경관리, Audit 대응을 포함한다.

### 0.2 세부산업 기준

| code | legacy_slug | 세부산업 ko | 细分产业 zh | v0.3 공정 문법 |
|---|---|---|---|---|
| H01 | `vehicle_oem` | 완성차·상용차 조립 | 整车与商用车装配 | VIN / JIS / Final Assembly / EOL |
| H02 | `ev_drive_system` | 전동화 파워트레인 | 电动化动力总成 | Motor-Inverter-eAxle / Serial / EOL |
| H03 | `powertrain` | 내연기관·변속기 파워트레인 | 内燃机与变速器动力总成 | Machining / Assembly / Leak / Run-in |
| H04 | `chassis_components` | 차체·섀시·제동 부품 | 车身、底盘与制动部件 | Stamping / Welding / Dimension Gate |
| H05 | `automotive_electronics` | 자동차 전장·전자모듈 | 汽车电子与电控模块 | HW/SW genealogy / Firmware / FCT/EOL |
| H06 | `interior_exterior_plastic` | 내장·외장·플라스틱 부품 | 内外饰与塑料部件 | Molding / Appearance / Color / JIS |
| H07 | `tire_rubber` | 타이어·자동차 고무제품 | 轮胎与汽车橡胶制品 | Compound batch / Curing / Uniformity |
| H08 | `tier1_tier2_suppliers` | Tier 1·2 복합 자동차부품 | Tier1/2综合汽车零部件 | Customer drawing / APQP / Mixed routing |

### 0.3 v0.3 작성 규칙

- `process_steps_detail_ko/zh`는 slug당 10개 step으로 통일한다.
- `control_points_detail_ko/zh`는 `category` 열을 포함한다.
- `step_expression_ko/zh`는 행 수와 `role`, `gate_for`, `trace_keys`를 동형으로 작성한다.
- `trace_keys`는 slug별 `data_capture_points`의 부분집합으로만 사용한다.
- `role: gate`인 행은 `gate_for`를 반드시 작성한다.
- en/ja 공정·관리점 섹션은 작성하지 않는다.

---

## 1. slug별 변경 요약

| code | slug | 핵심 보강 | gate | loop_hint | 중점 trace |
|---|---|---|---|---|---|
| H01 | `vehicle_oem` | VIN, JIS, ADAS calibration, EOL | step 8 | EOL Rework Loop | VIN, option, sequence, torque, EOL |
| H02 | `ev_drive_system` | Motor/PE/e-Axle serial genealogy | step 6, 8 | EOL Rework Loop | motor core, inverter, insulation, NVH |
| H03 | `powertrain` | 정밀가공, 청정도, Leak/Run-in | step 6, 8 | Machining SPC Loop | casting, tool, SPC, leak, torque |
| H04 | `chassis_components` | Press, welding, dimension, PPAP | step 6 |  | coil, die, weld program, dimension |
| H05 | `automotive_electronics` | HW/SW genealogy, Flash, FCT/EOL | step 5, 8 |  | PCB, component, firmware, calibration |
| H06 | `interior_exterior_plastic` | Color/option, molding, appearance, JIS | step 6 |  | resin, color, mold, appearance |
| H07 | `tire_rubber` | Compound, curing, X-ray/uniformity | step 7 |  | compound, cure press, DOT, uniformity |
| H08 | `tier1_tier2_suppliers` | APQP/PPAP, mixed routing, customer ASN | step 6 | Mixed Process Loop | drawing rev, route, inspection, ship lot |

---

## H01 `vehicle_oem` — 완성차·상용차 조립 / 整车与商用车装配

```yaml
industry_code: H
subindustry_code: H01
legacy_slug: vehicle_oem
label_ko: "완성차·상용차 조립"
label_zh: "整车与商用车装配"
label_en: ""
label_ja: ""
q3_cluster: "P3_LABOR_ASSEMBLY"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "sequenced_assembly_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** passenger cars/SUV, trucks/buses, special vehicles  
**产品范围 zh:** 乘用车/SUV、卡车/客车、专用车辆

### H01.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 수요·차종·옵션 서열 확정 | 차종 Mix, VIN Option, EBOM/MBOM/BOP, 생산서열, 지역·고객 사양을 확정한다. AI 기반 수요예측과 디지털 트윈 시뮬레이션으로 생산계획을 검증하며, 최대 24종 차종의 혼류 생산을 위한 서열 최적화를 수행한다. RFID 태그가 차체에 부착되어 VIN-서열-옵션 매핑이 실시간 MES로 전송된다. |
| 2 | 차체 투입·Body Shop | 프레스/차체 서브어셈블리 또는 BIW를 투입하고 용접·치수 품질을 확인한다. Giga Casting(초고압 다이캐스팅)으로 160개 부품을 1회 성형, AI 비전 검사로 0.1mm 단위 불량을 감지한다. 로봇 용접 자동화율 97% 이상, OPC-UA 기반 이기종 용접 로봇 간 실시간 통신으로 232개 차체 정밀도 포인트를 100% 수집한다. |
| 3 | 도장·색상·외관 관리 | 차체 전처리, 전착(ED), 수성 3C1B(3코트 1베이크) 도장, 건조로(폐열 회수 99% 효율), 색상·외관 검사를 수행한다. 로봇 자동 도장 시스템이 12가지 차체 색상을 신속 전환하며, 순환풍 기술로 에너지 30% 절감한다. 도장 배치(Batch)와 건조 온도·시간 곡선이 Lot 추적 포인트로 기록된다. |
| 4 | Trim / Chassis / Final 조립 | 의장, 섀시, 파워트레인, 내외장 부품을 IGV(지능형 무인운반차) 기반 스마트 아일랜드 방식으로 택트 기준 장착한다. 차량 1대당 약 352개 주요 체결 토크가 실시간 수집되어 MES에 VIN에 연결 저장된다. 분산형 스마트 아일랜드에서 '차가 공정을 찾아가는' 생산 패러다임으로, OEE 98.82%를 달성한다. |
| 5 | JIT/JIS 부품 공급·라인 피딩 | 서열공급(JIS), SPS Kit, Kanban, AGV/AMR 라인공급을 생산서열과 동기화한다. 수 시간 단위 정밀 공급망으로 서열 변경 시 공급사에 실시간 Push Notification이 전송된다. RFID/바코드로 Line-side 재고와 Kit 조립 상태를 실시간 WIP 관리하며, 결품 발생 시 생산 Hold가 자동 발동된다. |
| 6 | 토크·체결·작업검증 | 352개 주요 체결 토크를 디지털 토크렌치/멀티스핀들 너트러너(Nutrunner)로 실시간 수집, VIN에 연결 저장한다. 검증 파라미터: 토크값(N·m), 각도(°), 회전수. Poka-Yoke와 Vision Check로 누락 체결을 방지하고, 클라우드 기반 디지털 이력서(Digital CV, 一车一档)로 이력을 관리한다. 이상 발생 시 실시간 Alert와 작업자 정지(LINE STOP)가 실행된다. |
| 7 | 전장 Flash·Calibration | ECU/ADAS/Infotainment 소프트웨어, 파라미터, 보정 결과를 OBD-II 포트를 통해 차량 단위로 Flash 기록한다. CANFD/Ethernet 기반 고속 통신으로 버전 정합성(Variant Coding)을 자동 검증하며, ADAS 카메라·레이더의 Calibration ID가 차량 VIN에 바인딩된다. 소프트웨어 버전과 Calibration 데이터는 Every Lot 전수 기록한다. |
| 8 | EOL 종합 검사 Gate | 롤러(브레이크·속도), 전장 진단(Diag), 누수(Leak Test), NVH(소음·진동·평활도), ADAS(카메라·레이더 정렬) 검사로 출하 가능 여부를 판정한다. 모든 EOL 검사 결과는 VIN에 연계되어 '合格/不合格' 판정과 불량 코드가 기록된다. 불합격 시 Rework Loop으로 진입하며, Gate 역할로 Step 2,3,4,5,6,7을 순서대로 검증한다. |
| 9 | 수정·재검·품질 Hold | EOL 불합격, 고객검사, Audit 지적을 수정하고 재검·격리·해제한다. Rework Loop 내에서 재작업 이력(수정내용, 작업자, 일시)이 별도 분리 저장되어 최종 출하판정과 혼동되지 않도록 관리된다. 격리 구역(Q-zone)에서는 물리적 Lock-out과 시스템적 Block이 함께 적용된다. |
| 10 | 완성차 출하·VIN Genealogy | VIN별 부품 Serial, 검사성적, 물류 출하, 리콜 대응 데이터를 확정한다. EU 디지털 제품 여권(DPP)에 대응하는 디지털 트윈 기반 전(全)이력 데이터가 클라우드에 저장되며, 리콜 시 VIN 단위로 정밀 타겟팅이 가능하다. 출하 ASN과 리콜 데이터베이스가 실시간 연동된다. |

### H01.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 需求、车型与选装顺序确定 | 确定车型Mix、VIN选装、EBOM/MBOM/BOP、生产顺序以及区域/客户规格。基于AI需求预测和数字孪生仿真验证生产计划，执行最多24种车型混流生产的顺序优化。RFID标签附着于车身，VIN-顺序-选装映射实时传输至MES。 |
| 2 | 车身投入与Body Shop | 投入冲压/车身子总成或BIW，确认焊接与尺寸质量。通过Giga Casting（超高压压铸）一次成型160个部件，AI视觉检测识别0.1mm级缺陷，机器人焊接自动化率达97%以上。基于OPC-UA的异构焊接机器人实时通信，100%采集232个车身精度点数据。 |
| 3 | 涂装、颜色与外观管理 | 执行前处理、电泳(ED)、水性3C1B(3涂1烘)喷涂、烘烤（废热回收效率99%）、颜色与外观检查。机器人自动喷涂系统快速切换12种车身颜色，循环风技术节能30%。涂装批次与烘干温度/时间曲线作为Lot追溯点记录。 |
| 4 | Trim / Chassis / Final总装 | 按节拍采用IGV(智能无人搬运车)智能岛方式装配内饰、底盘、动力总成及内外饰部件。每车约352个关键紧固扭矩实时采集并关联VIN存储于MES。采用'车辆找工位'的分布式智能岛生产范式，OEE达到98.82%。 |
| 5 | JIT/JIS供料与线边配送 | 将顺序供货(JIS)、SPS Kit、看板、AGV/AMR线边配送与生产顺序同步。以数小时窗口的精密供应链运行时，顺序变更实时推送通知至供应商。通过RFID/条码实现线边库存和Kit装配状态的实时WIP管理，缺料时自动触发生产Hold。 |
| 6 | 扭矩、紧固与作业验证 | 使用数字扭矩扳手/多轴螺母拧紧机(Nutrunner)实时采集352个关键紧固扭矩并关联VIN存储。验证参数：扭矩值(N·m)、角度(°)、转速。通过防错(Poka-Yoke)和视觉检查防止漏装，基于云的数字履历(一车一档)管理数据。异常时实时报警并触发工位停止(LINE STOP)。 |
| 7 | 电控Flash与Calibration | 通过OBD-II端口按车辆记录ECU/ADAS/Infotainment软件Flash、参数与标定结果。基于CANFD/Ethernet高速通信自动验证版本一致性(Variant Coding)，ADAS摄像头/雷达的Calibration ID绑定至车辆VIN。软件版本与标定数据每Lot全数记录。 |
| 8 | EOL综合检查Gate | 通过滚筒(制动/速度)、电气诊断(Diag)、淋雨(Leak Test)、NVH(噪声/振动/平顺性)、ADAS(摄像头/雷达对准)检查判定是否可出货。所有EOL检查结果关联VIN，记录'合格/不合格'判定与不良代码。不合格时进入返修循环(Rework Loop)，作为Gate作用验证Step 2,3,4,5,6,7。 |
| 9 | 返修、复检与质量Hold | 对EOL不合格、客户检查、Audit问题进行返修、复检、隔离与放行。返修循环内履历(返工内容、作业员、时间)分离存储，避免与最终出货判定混淆。隔离区(Q-zone)同时实施物理Lock-out和系统级Block。 |
| 10 | 整车出货与VIN Genealogy | 确认VIN级部件Serial、检验成绩、物流出货与召回追溯数据。对应EU数字产品护照(DPP)的全生命周期数据存储于云端数字孪生，召回时可实现VIN级精准定位。出货ASN与召回数据库实时联动。 |

### H01.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 서열·옵션 기준 오류가 라인 공급·작업지시·검사조건까지 연쇄 영향을 주므로 VIN 기준 데이터 정합을 관리한다. 측정 방법: MES 대 BOM/Option Master 간 자동 비교 검증(Validation Rule Engine), AI 기반 이상 탐지로 서열 간 상충 여부 감시. 관리 주기: Every Lot(차량 1대 단위) 전수 검증. 이상 시 조치: 실시간 Alert → 작업지시서 Lock → 수동 Override까지 Line Stop 자동 발동. | 1,4,5 | process_step | VIN/Option Integrity |
| JIT/JIS는 수 시간 단위의 정밀 공급망이므로 서열변경·결품·오적재를 실시간 통제한다. 측정 방법: RFID Gate/바코드 스캐너를 통한 부품 도착·적재 인식, AGV/AMR 관제 시스템과 MES 간 서열 매칭 실시간 비교. 관리 주기: Real-time(매 공급 트립). 이상 시 조치: 결품 시 라인 Hold + 대체 서열 자동 생성, 오적재 시 해당 Kit 격리 및 재조립 지시 발행. | 1,5 | process_step | JIT/JIS Logistics |
| 핵심 체결·전장 Flash·Calibration 결과는 리콜 대응을 위해 VIN genealogy로 묶어야 한다. 측정 방법: 디지털 토크렌치·Nutrunner 토크/각도 데이터 실시간 MES 전송, OBD-II CANFD 통신으로 Flash·Calibration 결과 자동 수집. 관리 주기: Every Lot(차량별) 전수. 이상 시 조치: 352개 체결 중 1건이라도 Spec 이탈 시 LINE STOP + 해당 VIN 출하 Block, Calibration 미완료 차량은 EOL Gate 통과 불가. | 6,7,10 | process_step | VIN Genealogy |
| EOL 불합격은 수정 루프와 재검 이력을 분리해 최종 출하판정과 혼동하지 않는다. 측정 방법: EOL Test System(Brake Roller, Diag, Leak Tester, NVH Analyzer, ADAS Cal Rig)에서 VIN별 불합격 항목·수치 원본 기록. 관리 주기: 매 차량 전수. 이상 시 조치: Rework Loop 활성화 → 수정 완료 후 전 항목 재검 → Gate 재판정 시스템에서 ONLY Pass 시 출하 해제. Rework 이력과 최초 EOL 이력은 물리적·시스템적으로 분리 저장. | 8,9,10 | process_step | EOL Quality Gate |
| 차종 Mix 변화에 따른 택트·인력·라인 밸런스 변동을 생산계획과 실행 데이터로 연결한다. 측정 방법: MES 실시간 사이클 타임(C/T) 모니터링, IoT 센서 기반 라인 가동률·정체율 측정. 관리 주기: 주기적(실시간 모니터링 + Shift 단위 리포트) + 서열 변경 시 즉시. 이상 시 조치: 생산계획 재수립 Trigger, 인력 재배치·라인 속도 조정 권고, 디지털 트윈 시뮬레이션으로 최적 밸런스 재산출. | 1,4,5 | process_step | Line Balance |
| 고객·지역 사양, 법규 사양, 안전 관련 소프트웨어 이력은 감사 가능한 변경이력으로 남긴다. 측정 방법: EBOM/MBOM 대 VIN Option Code 자동 비교, Flash Tool의 SW Version Log와 Calibration Parameter Hash 자동 수집. 관리 주기: Every Lot 전수. 이상 시 조치: 미일치 사양 감지 시 MES가 해당 VIN의 출하를 시스템적으로 Block하고 Compliance Team에 Escalation 전송. | 1,7,10 | process_step | Compliance Trace |

### H01.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 顺序和选装基准错误会连锁影响线边供料、作业指示和检查条件，因此必须管理VIN级数据一致性。测量方法：MES与BOM/Option Master自动比对验证(Validation Rule Engine)，AI异常检测监控顺序冲突。管理周期：Every Lot(每车)全数验证。异常处理：实时报警 → 作业指示Lock → 手动Override前自动触发Line Stop。 | 1,4,5 | process_step | VIN/Option完整性 |
| JIT/JIS是以数小时为窗口的精密供应链，需要实时控制顺序变更、缺料和错装/错载。测量方法：RFID Gate/条码扫描器识别物料到货和装载，AGV/AMR管控系统与MES实时比对顺序匹配。管理周期：Real-time(每供料行程)。异常处理：缺料时产线Hold + 自动生成替代顺序，错装时隔离Kit并发起重新装配指令。 | 1,5 | process_step | JIT/JIS物流 |
| 关键紧固、电控Flash和Calibration结果必须形成VIN genealogy，以支持召回响应。测量方法：数字扭矩扳手/Nutrunner的扭矩/角度数据实时传输至MES，通过OBD-II CANFD通信自动采集Flash/Calibration结果。管理周期：Every Lot(每车)全数。异常处理：352个紧固件中任一规格偏离触发LINE STOP + 该VIN出货Block，Calibration未完成车辆禁止通过EOL Gate。 | 6,7,10 | process_step | VIN谱系 |
| EOL不合格必须将返修循环和复检履历分离，避免与最终出货判定混淆。测量方法：EOL Test System(Brake Roller, Diag, Leak Tester, NVH Analyzer, ADAS Cal Rig)按VIN记录不合格项目与原始数值。管理周期：每车全数。异常处理：激活Rework Loop → 返修完成后全项复检 → Gate重新判定系统仅在全部Pass时解除出货Hold。返修履历与首次EOL履历物理性和系统性分离存储。 | 8,9,10 | process_step | EOL质量Gate |
| 车型Mix变化导致的节拍、人员和产线平衡变化，需要连接计划与执行数据。测量方法：MES实时周期时间(C/T)监控，IoT传感器测定线体稼动率和拥堵率。管理周期：周期性(实时监控 + Shift报告) + 顺序变更时立即。异常处理：触发生产计划重新制定，建议人员调配/线速调整，通过数字孪生仿真重新计算最优平衡。 | 1,4,5 | process_step | 产线平衡 |
| 客户/区域规格、法规规格和安全相关软件履历应保留为可审计的变更记录。测量方法：EBOM/MBOM与VIN Option Code自动比对，Flash Tool的SW Version Log和Calibration Parameter Hash自动采集。管理周期：Every Lot全数。异常处理：检测到规格不匹配时，MES系统性Block该VIN出货并发送Escalation至Compliance Team。 | 1,7,10 | process_step | 合规追溯 |

### H01.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Planning | process |  |  | vin, model_code, option_code, sequence_no |
| 2 | Body | process |  |  | body_no, station_id |
| 3 | Paint | process |  |  | body_no, paint_batch |
| 4 | Final Assembly | process |  |  | vin, model_code, option_code, station_id |
| 5 | Logistics | utility |  |  | sequence_no, option_code, station_id |
| 6 | Quality | process |  |  | vin, station_id, torque_result |
| 7 | Software | process |  |  | vin, adas_calibration_id |
| 8 | EOL Gate | gate |  | 2,3,4,5,6,7 | vin, eol_result, adas_calibration_id |
| 9 | Rework | process | EOL Rework Loop |  | vin, eol_result |
| 10 | Shipment | process |  |  | vin, ship_lot, eol_result |

### H01.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Planning | process |  |  | vin, model_code, option_code, sequence_no |
| 2 | Body | process |  |  | body_no, station_id |
| 3 | Paint | process |  |  | body_no, paint_batch |
| 4 | Final Assembly | process |  |  | vin, model_code, option_code, station_id |
| 5 | Logistics | utility |  |  | sequence_no, option_code, station_id |
| 6 | Quality | process |  |  | vin, station_id, torque_result |
| 7 | Software | process |  |  | vin, adas_calibration_id |
| 8 | EOL Gate | gate |  | 2,3,4,5,6,7 | vin, eol_result, adas_calibration_id |
| 9 | Rework | process | EOL Rework Loop |  | vin, eol_result |
| 10 | Shipment | process |  |  | vin, ship_lot, eol_result |

### H01.10 step_expression 연결 설명 (ko/zh)

**ko:** H01(완성차) 공정은 VIN을 중심으로 한 흐름으로, Step 1 Planning에서 차종·옵션·서열이 VIN 기준으로 확정되면 Body → Paint → Final Assembly로 차체가 이동한다. Step 5 Logistics는 이 서열 정보를 받아 JIT/JIS 부품 공급을 동기화하며, Step 6 Quality에서 실시간 토크 검증이 수행된다. Step 7 Software에서 ECU Flash·ADAS Calibration이 완료된 후, Step 8 EOL Gate가 Step 2~7의 모든 선행 공정 결과를 gate_for로 검증한다. Gate 불합격 시 Step 9 Rework Loop이 활성화되어 수정·재검 후 재판정받으며, 최종 합격 시 Step 10 Shipment에서 VIN Genealogy가 완성되어 출하된다.

**zh:** H01(整车)工艺以VIN为核心流动，Step 1 Planning按VIN确定车型/选装/顺序后，车身经Body → Paint → Final Assembly移动。Step 5 Logistics根据顺序信息同步JIT/JIS供料，Step 6 Quality执行实时扭矩验证。Step 7 Software完成ECU Flash/ADAS Calibration后，Step 8 EOL Gate验证Step 2~7所有前置工序结果(gate_for)。Gate不合格时激活Step 9 Rework Loop进行返修/复检后重新判定，最终合格时Step 10 Shipment完成VIN Genealogy并出货。

### H01.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 2 | 1 | Body ID 생성 |
| 2 | 2 | 차체 치수 검사 |
| 5 | 1 | SPS Kit 생성 |
| 5 | 2 | Line-side Delivery Scan |
| 8 | 1 | Brake/Roller Test |
| 8 | 2 | Electrical Diagnostic |
| 8 | 3 | ADAS Calibration Check |

### H01.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 2 | 1 | Body ID 생성 |
| 2 | 2 | 차체 치수 검사 |
| 5 | 1 | SPS Kit 생성 |
| 5 | 2 | Line-side Delivery 扫描 |
| 8 | 1 | Brake/Roller 测试 |
| 8 | 2 | Electrical Diagnostic |
| 8 | 3 | ADAS Calibration 检查 |

### H01.9 data_capture_points

```yaml
data_capture_points:
  - vin
  - model_code
  - option_code
  - sequence_no
  - body_no
  - paint_batch
  - station_id
  - torque_result
  - adas_calibration_id
  - eol_result
  - ship_lot
```


## H02 `ev_drive_system` — 전동화 파워트레인 / 电动化动力总成

```yaml
industry_code: H
subindustry_code: H02
legacy_slug: ev_drive_system
label_ko: "전동화 파워트레인"
label_zh: "电动化动力总成"
label_en: ""
label_ja: ""
q3_cluster: "P3_LABOR_ASSEMBLY"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "powertrain_assembly_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** drive motor, inverter/OBC, e-Axle, reducer  
**产品范围 zh:** 驱动电机、逆变器/OBC、e-Axle、减速器

### H02.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 수요·사양·Trace 기준선 | 모터, 인버터, OBC, 감속기, e-Axle의 고객사양, 성능등급, Serial 규칙을 확정한다. 디지털 트윈(3DEXPERIENCE 등)으로 생산라인 시뮬레이션을 사전 수행, AGV 배치 최적화(50대→30대로 30% 비용 절감) 등을 계획에 반영한다. 배터리 DPP(디지털 제품 여권) 대응 데이터 구조를 확정한다. |
| 2 | Core / Rotor / Stator 준비 | 적층코어, 자석(NdFeB), 샤프트, 권선재(Hairpin 동선) 투입과 핵심 부품 genealogy를 구성한다. Hairpin 고정자의 경우 171개 헤어핀을 1회에 자동 삽입하고 3D 성형 정밀도를 0.3mm 이내로 제어한다. 로터 자동 적층-유도 가열-축 결합까지 전 공정 무인화(Blackout Factory) 운영. |
| 3 | Winding / Magnet / Assembly | Hairpin 권선, 자석 삽입(자동 Magnet Inserter), 로터/스테이터 조립, 접착·열처리 조건을 관리한다. 관리 파라미터: 권선 인장력(N), 자석 삽입력(N), 접착제 경화 온도(℃) 및 시간(min). AI 기반 헤어핀 삽입력·용접 품질 모니터링으로 실시간 이상 감지. |
| 4 | Power Electronics 조립 | 인버터/OBC PCB(SMT 후), SiC/GaN 전력모듈, 냉각판(액냉), 버스바(구리/알루미늄), 하우징(Al 다이캐스트)을 조립한다. 관리 파라미터: Press-fit 압입력(kN), Torque(N·m), TIM(열계면재료) 두께(mm). 전력모듈 Serial을 인버터 Serial에 연결하여 Lot 추적. |
| 5 | Reducer / e-Axle 기계조립 | 기어(헬리컬/유성), 베어링(볼/롤러), 샤프트, 오일링, 하우징 조립과 토크·간극(Backlash)을 관리한다. 측정 파라미터: 기어 백래시(μm), 베어링 예압(N), 최종 조립 토크(N·m). DTM(Drive Train Module) EOL 기준 사전 검증. |
| 6 | 절연·전기 안전 검사 Gate | Hi-pot(내전압, AC 1500V/DC 2000V), IR(절연저항, ≥100MΩ), 접지(Ground Continuity, <0.1Ω), 누설전류(Leakage Current, <5mA) 시험으로 다음 공정 진행을 판정한다. 모든 측정값 원본과 판정결과가 Serial별로 저장되고, One-fail 시 Gate FAIL 처리. |
| 7 | Firmware·Calibration·NVH | 펌웨어 Flash(FBL/UDS 프로토콜), 파라미터 보정(속도/토크 맵), 회전/소음/진동(NVH Run-up, 0-Max RPM 스윕) 특성을 측정한다. 축방향 자속 모터(Axial Flux Motor)의 경우 0.1mm 미만 공차의 '웨딩(Wedding)' 공정 결과가 함께 기록된다. NVH 스펙트럼 데이터는 AI 패턴 분석으로 이상 진단. |
| 8 | Thermal / Load EOL Test | 열부하(냉각장치 포함 온도 프로파일), 효율(입출력 전력비, ≥95%), 출력(토크×RPM), 통신(CAN/LIN/Ethernet), Fail-safe(비상 정지)를 종합 검증한다. 부하 조건: 25%/50%/75%/100% rated load 각 30초 이상 유지. 모든 검증 패턴의 Pass/Fail과 Raw Data를 저장. |
| 9 | Rework / 분석 / 재검 | 불합격 원인을 전기·기계·소프트웨어로 분리하고 재검 이력을 남긴다. Hi-pot FAIL 시 절연체 교체 후 재시험, NVH FAIL 시 Balancing 재수행, SW FAIL 시 Flash 재기입. Rework 완료 후 Gate 전 항목 재검증 필수. |
| 10 | 출하·고객 PPAP 이력 | Serial별 시험성적, 고객승인, 변경이력, 출하 lot을 확정한다. 셀-모듈-팩 간 디지털 쓰레드(Digital Thread) 연결을 완료하고, EU 배터리법 DPP 대응 데이터를 Pack/HVAC/VCU 단위로 확정한다. |

### H02.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 需求、规格与追溯基线 | 确定电机、逆变器、OBC、减速器、e-Axle的客户规格、性能等级和Serial规则。通过数字孪生(3DEXPERIENCE等)预先进行产线仿真，将AGV布局优化(50台→30台，成本降低30%)等反映到计划中。确定对应EU电池法DPP(数字产品护照)的数据结构。 |
| 2 | Core / Rotor / Stator准备 | 投入叠片铁芯、磁钢(NdFeB)、轴、绕组材料(Hairpin扁铜线)，并建立关键部件genealogy。Hairpin定子自动插入171根发卡，3D成型精度控制在0.3mm以内。转子自动叠片-感应加热-压轴全工序无人化(Blackout Factory)运行。 |
| 3 | Winding / Magnet / Assembly | 管理Hairpin绕线、磁钢插入(自动Magnet Inserter)、转子/定子装配、胶粘与热处理条件。管理参数：绕线张力(N)、磁钢插入力(N)、胶粘固化温度(℃)及时间(min)。AI监测Hairpin插入力/焊接质量实现实时异常检测。 |
| 4 | Power Electronics装配 | 装配逆变器/OBC PCB(SMT后)、SiC/GaN功率模块、冷板(液冷)、母排(铜/铝)、壳体(Al压铸)。管理参数：Press-fit压入力(kN)、Torque(N·m)、TIM(导热界面材料)厚度(mm)。功率模块Serial绑定至逆变器Serial进行Lot追溯。 |
| 5 | Reducer / e-Axle机械装配 | 管理齿轮(斜齿/行星)、轴承(球/滚子)、轴、润滑、壳体装配以及扭矩/间隙。测量参数：齿轮背隙(μm)、轴承预紧力(N)、最终装配扭矩(N·m)。预先验证DTM(驱动总成模块)EOL标准。 |
| 6 | 绝缘与电气安全检查Gate | 通过Hi-pot(耐压, AC 1500V/DC 2000V)、IR(绝缘电阻, ≥100MΩ)、接地(Ground Continuity, <0.1Ω)、泄漏电流(Leakage Current, <5mA)测试判定是否进入后续工序。所有测量原始值和判定结果按Serial存储，任一Fail时Gate判为FAIL。 |
| 7 | Firmware、Calibration与NVH | 执行固件Flash(FBL/UDS协议)、参数标定(速度/扭矩Map)、旋转/噪声/振动(NVH Run-up, 0-Max RPM扫描)特性测量。轴向磁通电机(Axial Flux Motor)的'Wedding'工序结果(公差<0.1mm)一并记录。NVH频谱数据通过AI模式分析诊断异常。 |
| 8 | Thermal / Load EOL Test | 综合验证热负荷(含冷却系统的温度剖面)、效率(输入输出功率比, ≥95%)、输出(扭矩×RPM)、通信(CAN/LIN/Ethernet)、Fail-safe(紧急停机)。负载条件：25%/50%/75%/100%额定负载各维持30秒以上。保存所有验证模式的Pass/Fail及原始数据。 |
| 9 | 返修、分析与复检 | 将不合格原因按电气、机械、软件分类并记录复检履历。Hi-pot FAIL时更换绝缘体后重新测试，NVH FAIL时重新进行动平衡，SW FAIL时重写Flash。返修完成后必须重新验证Gate全项。 |
| 10 | 出货与客户PPAP履历 | 确认Serial级测试成绩、客户批准、变更履历和出货lot。完成Cell-Module-Pack间的Digital Thread连接，按Pack/HVAC/VCU单位确认EU电池法DPP对应数据。 |

### H02.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 모터·인버터·감속기 Serial genealogy가 끊기면 고객 클레임 분석과 리콜 범위 산정이 불가능하다. 측정 방법: 각 부품(SiC 전력모듈, Hairpin 코어, 기어)의 DPM(Dot Peen Marking)/QR 코드를 스캐너로 자동 판독, MES에서 부모-자식 Serial 트리 자동 구축. 관리 주기: Every Lot(부품별) 전수. 이상 시 조치: Genealogy 불일치 감지 시 해당 e-Axle/모터 Assembly를 품질 Hold 처리하고, 추적 불가 부품은 폐기 또는 분해 후 재구축. | 2,3,4,5,10 | process_step | Serial Genealogy |
| 절연·Hi-pot·접지 시험은 안전 Gate이므로 수치 원본과 판정조건을 함께 저장한다. 측정 방법: Hi-pot Tester(5kV급), Megger(절연저항계), 접지저항계, Leakage Current Meter 사용, 모든 수치를 PLC→MES로 자동 전송. 관리 주기: Every Lot 전수. 이상 시 조치: Hi-pot FAIL → 해당 Assembly Gate 차단 + 분리 분석, 절연체 교체 후 재시험, 2회 연속 FAIL 시 설비 Cpk 점검 Trigger. | 6,8 | process_step | Electrical Safety |
| Firmware와 Calibration은 물리제품 이력과 분리하지 않고 Serial별로 묶는다. 측정 방법: Flash Tool(FBL/UDS)에서 Firmware Version·Checksum·Flash Date-Time 자동 로깅, Calibration Rig(다이나모)에서 Torque Map·Speed Map Raw Data 수집. 관리 주기: Every Lot 전수. 이상 시 조치: SW Version 불일치 시 Flash 재기입, Calibration Outlier 감지 시 Calibration 엔지니어 Escalation + 해당 Serial 재교정. | 7,10 | process_step | Software Trace |
| NVH·열·부하 EOL 데이터는 예측품질과 설계 피드백의 핵심 입력이다. 측정 방법: NVH Analyzer(가속도계·마이크로폰 어레이), Thermal Chamber(열화상 카메라·열전대), Dynamometer(토크·속도·효율 측정). 관리 주기: Every Lot 전수. 이상 시 조치: NVH 스펙트럼 이상 패턴 감지 시 AI 진단 → 설계팀 피드백, 부하 EOL Fail 시 제품격리 + 8D 프로세스 개시. | 7,8,9 | process_step | Performance EOL |
| PPAP·변경점·고객승인 이력은 출하 lot과 연결해 고객 감사에 대응한다. 측정 방법: 고객 포털/EDI를 통한 PPAP 승인 상태 확인, ECR/ECN 추적 시스템과 MES 연동. 관리 주기: Every Lot(변경 시) + 주기적 고객 감사 대비. 이상 시 조치: 미승인 변경 감지 시 해당 Lot 출하 Block, 고객 요청 시 PPAP 문서 패키지 조회/제출 가능. | 1,10 | process_step | APQP/PPAP |

### H02.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 电机、逆变器、减速器Serial genealogy中断时，客户索赔分析和召回范围计算将无法进行。测量方法：通过扫描器自动读取各部件(SiC功率模块、Hairpin铁芯、齿轮)的DPM/QR码，MES自动构建父子Serial树。管理周期：Every Lot(按部件)全数。异常处理：检测到Genealogy不一致时，将对应e-Axle/电机Assembly置为质量Hold，不可追溯部件报废或拆解后重建。 | 2,3,4,5,10 | process_step | Serial谱系 |
| 绝缘、Hi-pot、接地测试属于安全Gate，应同时保存原始数值和判定条件。测量方法：使用Hi-pot Tester(5kV级)、Megger(绝缘电阻计)、接地电阻计、泄漏电流计，所有数值由PLC→MES自动传输。管理周期：Every Lot全数。异常处理：Hi-pot FAIL → 阻塞该Assembly通过Gate + 分离分析，更换绝缘体后复测，连续2次FAIL时触发设备Cpk点检。 | 6,8 | process_step | 电气安全 |
| Firmware和Calibration不能与实物履历分离，应按Serial绑定。测量方法：Flash Tool(FBL/UDS)自动记录Firmware Version·Checksum·Flash Date-Time，Calibration Rig(测功机)采集Torque Map·Speed Map原始数据。管理周期：Every Lot全数。异常处理：SW版本不一致时重写Flash，Calibration离群值时升级至Calibration工程师+该Serial重新标定。 | 7,10 | process_step | 软件追溯 |
| NVH、热、负载EOL数据是预测质量和设计反馈的关键输入。测量方法：NVH Analyzer(加速度计·麦克风阵列)、Thermal Chamber(热成像相机·热电偶)、Dynamometer(扭矩·速度·效率测量)。管理周期：Every Lot全数。异常处理：NVH频谱异常模式检测时AI诊断→反馈设计团队，负载EOL Fail时产品隔离+启动8D流程。 | 7,8,9 | process_step | 性能EOL |
| PPAP、变更点和客户批准履历需与出货lot连接以支持客户审核。测量方法：通过客户门户/EDI确认PPAP批准状态，ECR/ECN追踪系统与MES联动。管理周期：Every Lot(变更时) + 周期性客户审核准备。异常处理：检测到未批准变更时Block该Lot出货，客户请求时可查阅/提交PPAP文件包。 | 1,10 | process_step | APQP/PPAP |

### H02.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Planning | process |  |  | serial_no |
| 2 | Motor Prep | process |  |  | motor_core_id, magnet_lot, winding_lot |
| 3 | Motor Assembly | process |  |  | serial_no, motor_core_id, magnet_lot, winding_lot |
| 4 | Power Electronics | process |  |  | serial_no, inverter_serial |
| 5 | Mechanical Assembly | process |  |  | serial_no |
| 6 | Safety Gate | gate |  | 2,3,4,5 | serial_no, insulation_result |
| 7 | Calibration | process |  |  | serial_no, firmware_version, nvh_result |
| 8 | EOL Gate | gate |  | 6,7 | serial_no, eol_result, insulation_result |
| 9 | Rework | process | EOL Rework Loop |  | serial_no, eol_result |
| 10 | Shipment | process |  |  | serial_no, eol_result |

### H02.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Planning | process |  |  | serial_no |
| 2 | Motor Prep | process |  |  | motor_core_id, magnet_lot, winding_lot |
| 3 | Motor Assembly | process |  |  | serial_no, motor_core_id, magnet_lot, winding_lot |
| 4 | Power Electronics | process |  |  | serial_no, inverter_serial |
| 5 | Mechanical Assembly | process |  |  | serial_no |
| 6 | Safety Gate | gate |  | 2,3,4,5 | serial_no, insulation_result |
| 7 | Calibration | process |  |  | serial_no, firmware_version, nvh_result |
| 8 | EOL Gate | gate |  | 6,7 | serial_no, eol_result, insulation_result |
| 9 | Rework | process | EOL Rework Loop |  | serial_no, eol_result |
| 10 | Shipment | process |  |  | serial_no, eol_result |

### H02.10 step_expression 연결 설명 (ko/zh)

**ko:** H02(전동화 파워트레인)는 모터 Core/Rotor/Stator 부품 준비(Step 2)에서 Serial Genealogy가 시작된다. Step 3 Motor Assembly에서 Hairpin 권선과 자석 삽입이 완료되면, Step 4 Power Electronics(인버터/OBC) 조립과 Step 5 Reducer/e-Axle 기계조립이 병렬로 진행된다. Step 6 Safety Gate에서 전기 안전(Hi-pot/IR/접지)을 통과해야 Step 7 Calibration(Firmware+NVH)로 진행할 수 있다. Step 8 EOL Gate는 Step 6의 안전 결과와 Step 7의 성능 결과를 gate_for로 검증한 후 최종 합격 판정한다. Step 9 Rework Loop에서 불합격 원인별(전기/기계/SW) 재작업이 이루어지고, Step 10 Shipment에서 PPAP 이력과 함께 최종 출하된다.

**zh:** H02(电动化动力总成)的Serial Genealogy从Step 2 Motor Prep(铁芯/磁钢/绕组)开始。Step 3 Motor Assembly完成Hairpin绕线和磁钢装配后，Step 4 Power Electronics(逆变器/OBC)装配与Step 5 Reducer/e-Axle机械装配并行进行。通过Step 6 Safety Gate(Hi-pot/IR/接地)后方可进入Step 7 Calibration(Firmware+NVH)。Step 8 EOL Gate验证Step 6的安全结果和Step 7的性能结果(gate_for)后做出最终合格判定。Step 9 Rework Loop按原因(电气/机械/SW)进行返修，Step 10 Shipment伴随PPAP履历最终出货。

### H02.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 6 | 1 | Hi-pot Test |
| 6 | 2 | Insulation Resistance Test |
| 7 | 1 | Firmware Flash |
| 7 | 2 | NVH Run-up |
| 8 | 1 | Thermal Load Test |
| 8 | 2 | CAN/LIN Communication Test |

### H02.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 6 | 1 | Hi-pot 测试 |
| 6 | 2 | Insulation Resistance 测试 |
| 7 | 1 | Firmware写入 |
| 7 | 2 | NVH Run-up |
| 8 | 1 | Thermal 载入 测试 |
| 8 | 2 | CAN/LIN Communication 测试 |

### H02.9 data_capture_points

```yaml
data_capture_points:
  - serial_no
  - motor_core_id
  - magnet_lot
  - winding_lot
  - inverter_serial
  - firmware_version
  - insulation_result
  - nvh_result
  - eol_result
```


## H03 `powertrain` — 내연기관·변속기 파워트레인 / 内燃机与变速器动力总成

```yaml
industry_code: H
subindustry_code: H03
legacy_slug: powertrain
label_ko: "내연기관·변속기 파워트레인"
label_zh: "内燃机与变速器动力总成"
label_en: ""
label_ja: ""
q3_cluster: "P3_LABOR_ASSEMBLY"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "powertrain_machining_assembly_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** engine, transmission, fuel/exhaust system  
**产品范围 zh:** 发动机、变速器、燃油/排气系统

### H03.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 수요·품번·공정계획 | 엔진/변속기/연료·배기 부품의 품번, 공정라우팅, C/T, 설비·공구 기준을 확정한다. 고객 APQP/PPAP 요구사항 반영, 공정 FMEA 기반 위험 평가를 완료한다. 디지털 트윈 시뮬레이션으로 가상 시운전(Virtual Commissioning) 수행, CAPA 예측. |
| 2 | 주조·단조·소재 투입 | 주조품(Al/Fe 합금), 단조품(크랭크샤프트, 커넥팅로드), 기어블랭크(침탄강), 하우징 소재 lot과 열처리 조건(담금질·템퍼링 온도/시간)을 기록한다. 소재 Lot 번호를 Serial에 연결하여 배치 추적. |
| 3 | 정밀 가공 Cell | CNC(5-axis Machining Center), 연삭(OD/ID Grinder), 호닝(Honing Machine, 실린더 보어), 기어가공(Hobbing/Shaper/Shaving)에서 공구 ID·수명(공구 교체 주기), 치구 조건, 설비 파라미터(Spindle RPM, Feed Rate, Cutting Depth)와 치수 SPC(Cp/Cpk ≥1.67)를 관리한다. Machining SPC Loop로 지속적 품질 피드백. |
| 4 | 세척·Deburr·청정도 | 고압 세척(High-pressure Washing, 50-200 bar), 초음파 세척, Burr 제거(로봇 디버링/전해 디버링), 잔류입자(Particle Count, ISO 4406 청정도 코드) 결과를 기록한다. 청정도 Gate로 내구성 불량 사전 차단. |
| 5 | 서브조립·압입·체결 | 베어링(볼/롤러/니들), 샤프트, 기어(싱크로나이저 포함), 밸브(가변 밸브 타이밍), 씰류(오일씰/가스켓)를 조립하고 압입력(kN), 토크(N·m), 간극(mm) 조건을 확인한다. 모든 체결 데이터는 Lot Serial에 연결. |
| 6 | 누설·토크·기능 검사 Gate | Leak Test(He Mass Spectrometer / Air Decay, Leak Rate <1×10⁻⁵ Pa·m³/s), Torque Test(Digital Torque Wrench, 각도+토크 동시 측정), Backlash(μm), 회전저항(Running Torque, N·m) 등 핵심 성능시험으로 합격을 판정한다. Gate FAIL 시 Step 3,4,5로 피드백 루프. |
| 7 | Run-in / Calibration | 엔진 콜드런/핫런(Hot Test Cell) 또는 변속기 Run-in(부하 조건별 15-30분), 특성 운전(토크 컨버터, 밸브 타이밍 보정), 소음·진동 데이터(NVH 분석)를 수집한다. ECU/TCU 보정값(Calibration Map)이 Serial별 저장됨. |
| 8 | Final EOL Test | 완성 파워트레인의 성능(최대 출력/토크), 누설(재검증), 소음(dBA), 기능(기어 변속·클러치 작동)을 최종 검증한다. EOL Result(Pass/Fail + Raw Data)는 Serial별로 저장되어 10단계에서 출하 판정의 최종 입력이 됨. |
| 9 | Rework / MRB | 가공불량(치수 이탈, 표면조도 불량), 조립불량(압입력 부족, 씰 누설), 시험불합격(성능 미달, 누설 초과)을 분리하여 재작업·폐기·특채(Concession/Deviation)를 관리한다. MRB 회의록과 판정 근거가 출하 이력에 포함됨. |
| 10 | 출하·고객 이력 | Serial별 소재 lot, 공구(가공 시 사용된 Tool ID), 검사값(Leak/Torque/SPC), 고객 승인 및 출하 이력을 확정한다. 품질 이력 1건(一机一档)으로 묶어 고객 감사(CSR/IAFTF) 대응 가능. |

### H03.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 需求、品号与工艺计划 | 确定发动机/变速器/燃油排气部件的品号、工艺路线、C/T、设备与刀具基准。反映客户APQP/PPAP要求，完成基于PFMEA的风险评估。通过数字孪生仿真执行虚拟调试(Virtual Commissioning)，预测CAPA。 |
| 2 | 铸造、锻造与材料投入 | 记录铸件(Al/Fe合金)、锻件(曲轴、连杆)、齿轮毛坯(渗碳钢)、壳体材料lot及热处理条件(淬火/回火温度与时间)。将材料Lot号连接至Serial进行批次追溯。 |
| 3 | 精密加工Cell | 在CNC(5轴加工中心)、磨削(外圆/内圆磨床)、珩磨(Honing Machine, 缸孔)、齿轮加工(滚齿/插齿/剃齿)中管理刀具ID及寿命(更换周期)、夹具条件、设备参数(主轴转速、进给率、切削深度)和尺寸SPC(Cp/Cpk ≥1.67)。通过Machining SPC Loop实现持续质量反馈。 |
| 4 | 清洗、去毛刺与清洁度 | 记录高压清洗(50-200 bar)、超声波清洗、去毛刺(机器人/电解去毛刺)、残留颗粒(Particle Count, ISO 4406清洁度代码)结果。通过清洁度Gate提前阻断耐久性不良。 |
| 5 | 子装配、压装与紧固 | 装配轴承(球/滚子/滚针)、轴、齿轮(含同步器)、阀(可变气门正时)、密封件(油封/垫片)，确认压入力(kN)、扭矩(N·m)、间隙(mm)条件。所有紧固数据连接至Lot Serial。 |
| 6 | 泄漏、扭矩与功能检查Gate | 通过Leak Test(氦质谱仪/气压衰减法，Leak Rate <1×10⁻⁵ Pa·m³/s)、Torque Test(数字扭矩扳手，同时测量角度+扭矩)、Backlash(μm)、转动阻力(Running Torque, N·m)等关键性能测试判定合格。Gate FAIL时反馈至Step 3,4,5。 |
| 7 | Run-in / Calibration | 执行发动机冷/热磨合(Hot Test Cell)或变速器Run-in(负载条件各15-30分钟)、特性运转(变矩器/气门正时标定)、噪声/振动数据(NVH分析)采集。ECU/TCU标定值(Calibration Map)按Serial存储。 |
| 8 | Final EOL Test | 最终验证动力总成的性能(最大功率/扭矩)、泄漏(复验)、噪声(dBA)、功能(换挡/离合器动作)。EOL Result(Pass/Fail + Raw Data)按Serial存储，作为Step 10出货判定的最终输入。 |
| 9 | 返修 / MRB | 将加工不良(尺寸偏差、表面粗糙度不良)、装配不良(压入力不足、密封泄漏)、测试不合格(性能不足、泄漏超标)分类管理返工、报废、让步接收(Concession/Deviation)。MRB会议记录与判定依据包含在出货履历中。 |
| 10 | 出货与客户履历 | 确认Serial级材料lot、刀具(加工使用的Tool ID)、检查值(Leak/Torque/SPC)、客户批准和出货履历。整合为1份质量履历(一机一档)，可应对客户审核(CSR/IATF)。 |

### H03.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 공구·치구·설비조건은 치수불량 원인분석의 핵심이므로 부품 Serial과 연결한다. 측정 방법: 바코드/RFID로 공구 ID·설비 ID 자동 인식, CNC Controller에서 Spindle Load·Feed Rate·Tool Wear 데이터 자동 수집(OPC-UA). 관리 주기: Every Lot(가공 Cycle당) 전수. 이상 시 조치: SPC(Cp/Cpk) 이탈 감지 시 공구 교체 Trigger, 설비 이상(Spindle Load 급증) 시 실시간 LINE STOP + 정비팀 Escalation. | 3,10 | process_step | Tool/Fixture Trace |
| 청정도와 잔류입자는 파워트레인 내구성에 영향을 주므로 검사값을 공정 Gate로 관리한다. 측정 방법: Particle Counter(액체/공기 중 입자 측정), ISO 4406 코드 부여, Microscope 이미지 분석(최대 입자 크기/개수). 관리 주기: Every Lot(가공 Batch별) + 주기적(1회/Shift 또는 금형 교체 시). 이상 시 조치: 청정도 기준 초과 시 해당 Lot 세척 재실행 + 세척 설비(필터/노즐) 점검 Command 발행. | 4,6 | process_step | Cleanliness Control |
| Leak·Torque·Backlash 등 기능검사는 수치 원본과 판정 기준을 분리 저장한다. 측정 방법: Leak Tester(He Mass Spec / Air Decay), Digital Torque Analyzer, Backlash Gauge. 관리 주기: Every Lot 전수. 이상 시 조치: 수치 원본을 기준으로 재현성 확인, 불합격 Lot은 Gate 차단 + 원인분석(기계적 마모/조립 오류) 후 수정·재검. | 6,8 | process_step | Functional Gate |
| 가공 SPC와 EOL 결과를 연결해 공정능력 저하와 고객불량을 사전 감지한다. 측정 방법: SPC 차트(X-bar R, Cpk 추세) 자동 생성→MES 대시보드, EOL 결과와 가공 데이터 간 상관 분석(AI/ML). 관리 주기: 실시간(매 측정) + Shift 단위 SPC 리포트. 이상 시 조치: Cpk 하향 추세 감지 시 사전 공구 교체·설비 보정, EOL Fail 패턴과 가공 데이터 매칭으로 근본 원인 특정. | 3,8,9 | process_step | SPC/EOL Link |
| APQP/PPAP 및 변경관리 이력은 고객승인·출하 lot과 연결한다. 측정 방법: ECR/ECN 시스템에서 변경 건별 승인 상태 추적, 고객 포털 PPAP 승인 상태 동기화. 관리 주기: 변경 발생 시(Ever Change) + 주기적 고객 감사 대비. 이상 시 조치: 미승인 변경이 출하 Lot에 포함된 경우 해당 Lot 전수 Block, 고객 승인 획득 후 해제. | 1,10 | process_step | APQP/PPAP |

### H03.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 刀具、夹具和设备条件是尺寸不良原因分析的关键，应与部件Serial连接。测量方法：通过条码/RFID自动识别刀具ID·设备ID，通过CNC Controller(OPC-UA)自动采集主轴负载·进给率·刀具磨损数据。管理周期：Every Lot(每加工Cycle)全数。异常处理：检测SPC(Cp/Cpk)偏离时触发刀具更换，设备异常(主轴负载骤增)时实时LINE STOP + 维修团队Escalation。 | 3,10 | process_step | 刀具/夹具追溯 |
| 清洁度和残留颗粒影响动力总成耐久性，应将检查值作为工序Gate管理。测量方法：Particle Counter(液体/空气中颗粒测量)、ISO 4406代码赋予、Microscope图像分析(最大颗粒尺寸/数量)。管理周期：Every Lot(每加工Batch) + 周期性(1次/Shift或模具更换时)。异常处理：清洁度超标时该Lot重新清洗 + 发出清洗设备(过滤器/喷嘴)点检指令。 | 4,6 | process_step | 清洁度控制 |
| Leak、Torque、Backlash等功能检查应分离保存原始数值和判定标准。测量方法：Leak Tester(氦质谱/气压衰减)、Digital Torque Analyzer、Backlash Gauge。管理周期：Every Lot全数。异常处理：基于原始数值确认再现性，不合格Lot阻断Gate + 原因分析(机械磨损/装配错误)后修正·复检。 | 6,8 | process_step | 功能Gate |
| 连接加工SPC与EOL结果，以提前发现过程能力下降和客户不良风险。测量方法：SPC图表(X-bar R, Cpk趋势)自动生成→MES仪表盘，EOL结果与加工数据间关联分析(AI/ML)。管理周期：实时(每测量) + Shift级SPC报告。异常处理：Cpk下降趋势时提前更换刀具·设备校正，EOL Fail模式与加工数据匹配确定根本原因。 | 3,8,9 | process_step | SPC/EOL关联 |
| APQP/PPAP及变更管理履历应与客户批准和出货lot连接。测量方法：ECR/ECN系统中按变更项追踪批准状态，与客户门户PPAP批准状态同步。管理周期：变更发生时(Every Change) + 周期性客户审核准备。异常处理：未批准变更被包含在出货Lot中时，该Lot全数Block，获得客户批准后解除。 | 1,10 | process_step | APQP/PPAP |

### H03.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Planning | process |  |  | serial_no |
| 2 | Material | process |  |  | casting_lot |
| 3 | Machining | process | Machining SPC Loop |  | serial_no, tool_id, machining_fixture_id, spc_result |
| 4 | Cleanliness | process |  |  | serial_no, wash_result |
| 5 | Assembly | process |  |  | serial_no, torque_result |
| 6 | Process Gate | gate |  | 3,4,5 | serial_no, leak_test_result, torque_result |
| 7 | Run-in | process |  |  | serial_no, eol_result |
| 8 | EOL Gate | gate |  | 6,7 | serial_no, eol_result, leak_test_result |
| 9 | MRB | process |  |  | serial_no, eol_result |
| 10 | Shipment | process |  |  | serial_no, eol_result |

### H03.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Planning | process |  |  | serial_no |
| 2 | Material | process |  |  | casting_lot |
| 3 | Machining | process | Machining SPC Loop |  | serial_no, tool_id, machining_fixture_id, spc_result |
| 4 | Cleanliness | process |  |  | serial_no, wash_result |
| 5 | Assembly | process |  |  | serial_no, torque_result |
| 6 | Process Gate | gate |  | 3,4,5 | serial_no, leak_test_result, torque_result |
| 7 | Run-in | process |  |  | serial_no, eol_result |
| 8 | EOL Gate | gate |  | 6,7 | serial_no, eol_result, leak_test_result |
| 9 | MRB | process |  |  | serial_no, eol_result |
| 10 | Shipment | process |  |  | serial_no, eol_result |

### H03.10 step_expression 연결 설명 (ko/zh)

**ko:** H03(내연기관·변속기)는 Step 1 Planning에서 품번·라우팅이 확정된 후, Step 2 Material에서 주조·단조 소재 Lot이 투입된다. Step 3 Machining에서 정밀 가공(Cp/Cpk ≥1.67 관리)이 Machining SPC Loop로 피드백되며, Step 4 Cleanliness에서 세척·청정도 검증 후 Step 5 Assembly(압입·체결)로 연결된다. Step 6 Process Gate가 Step 3/4/5의 결과를 gate_for로 검증한 후 Pass 시 Step 7 Run-in으로 진행된다. Step 8 EOL Gate는 Step 6의 Leak/Torque 결과와 Step 7의 Run-in 데이터를 종합 검증한다. 불합격 시 Step 9 MRB에서 가공/조립/시험 원인별로 분리되어 재작업·폐기·특채 판정. Step 10 Shipment에서 SPC/EOL 분석 결과와 함께 출하된다.

**zh:** H03(内燃机·变速器)在Step 1 Planning确定品号/路线后，Step 2 Material投入铸造/锻造材料Lot。Step 3 Machining精密加工(Cp/Cpk ≥1.67管理)通过Machining SPC Loop反馈，经Step 4 Cleanliness清洗/清洁度验证后连接至Step 5 Assembly(压装/紧固)。Step 6 Process Gate验证Step 3/4/5的结果(gate_for)后，Pass时进入Step 7 Run-in。Step 8 EOL Gate综合验证Step 6的Leak/Torque结果和Step 7的Run-in数据。不合格时Step 9 MRB按加工/装配/测试原因分类进行返工/报废/让步接收判定。Step 10 Shipment伴随SPC/EOL分析结果出货。

### H03.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | CNC Program Load |
| 3 | 2 | In-process Gauge Check |
| 4 | 1 | Particle Cleanliness Test |
| 6 | 1 | Leak Test |
| 6 | 2 | Torque/Backlash Test |
| 8 | 1 | Final Run Test |

### H03.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | CNC Program 载入 |
| 3 | 2 | In-process Gauge 检查 |
| 4 | 1 | Particle Cleanliness 测试 |
| 6 | 1 | Leak 测试 |
| 6 | 2 | Torque/Backlash 测试 |
| 8 | 1 | Final Run 测试 |

### H03.9 data_capture_points

```yaml
data_capture_points:
  - serial_no
  - casting_lot
  - machining_fixture_id
  - tool_id
  - spc_result
  - wash_result
  - torque_result
  - leak_test_result
  - eol_result
```


## H04 `chassis_components` — 차체·섀시·제동 부품 / 车身、底盘与制动部件

```yaml
industry_code: H
subindustry_code: H04
legacy_slug: chassis_components
label_ko: "차체·섀시·제동 부품"
label_zh: "车身、底盘与制动部件"
label_en: ""
label_ja: ""
q3_cluster: "P9_PRECISION_JOBSHOP"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "body_chassis_weld_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** stamped body, welded chassis, suspension/steering/brake parts  
**产品范围 zh:** 冲压车身件、焊接底盘件、悬架/转向/制动部件

### H04.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 고객도면·금형·PPAP 기준 | OEM 도면, 공차(GD&T), 소재규격(강종·두께), 금형/치구, PPAP 수준(Level 3)과 검사계획(Control Plan)을 확정한다. AAS(Asset Administration Shell) 기반 데이터 수집 표준화. 고객 EDI/EAI를 통한 생산서열 정보 수신 준비. |
| 2 | 소재·코일·블랭크 투입 | Coil lot(강종 코드·두께 mm), Blank lot(Blank 치수·중량), 표면 상태(스케일/오일)를 투입 이력으로 관리한다. AI 비전 검사로 소재 표면 결함(흠집/기공) 실시간 감지. QR 코드 기반 전수 품질 이력 추적 시스템 운영. |
| 3 | 프레스·성형 | Die ID(금형 수명 예측 관리), 프레스 조건(토너지·속도·하중 tonf), 윤활(Roll Coater/Oil Mist), 성형하중(Ton), Scrap/재작업을 관리한다. 초고압 다이캐스팅(Giga Casting, 3,500톤급)으로 모터 하우징 등 대형 부품 전 공정 자동화(용해-주입-냉각). AI 기반 이상 탐지로 OEE 8-10% 향상. |
| 4 | 용접·조립 Cell | Robot program(용접 로봇 Positioner·Torch Angle), Weld schedule(전류 kA·전압 V·시간 cycle·가압력 kN), fixture, spot/seam weld 품질(너깃 직경 mm·전단강도 kN)을 기록한다. AI 비전 검사로 0.1mm 단위 용접 불량 감지, 검사 효율 인간 대비 10배 향상. OPC-UA 기반 이기종 로봇 간 실시간 통신. |
| 5 | 가공·열처리·표면처리 | 가공(밀링·드릴링·탭핑), 열처리(침탄·고주파 담금질 온도/시간/경도 HRC), 도장/도금(Zn/Ni 도금 두께 μm)/방청(방청유 도포량 g/m²) 등 후처리 조건과 결과를 관리한다. |
| 6 | 치수·강도 검사 Gate | CMM(3차원 측정기, 6시그마 공차), Gauge(Go/No-Go Plug Gage·Snap Gage), 용접강도(인장/전단 시험 kN), 토크(N·m), 내구 시험(피로 시험 Cycle)으로 합격을 판정한다. 232개 차체 정밀도 포인트 100% 데이터 수집. Gate FAIL 시 원인 분석 후 Step 3/4/5 피드백. |
| 7 | 서브어셈블리·Kitting | 섀시/제동 서브모듈(서브프레임·컨트롤 암·캘리퍼)을 조립하고 고객 서열(JIS 순서)·납입 단위(팔레트·스틸)로 묶는다. 고객 라인 투입 순서에 맞춘 Sequence Picking 수행. |
| 8 | 출하 전 Audit·라벨링 | 라벨(고객 지정 포맷, GTIN/UDI), 납품 lot 번호, 고객 ASN(EDI 856), 포장(반복용·일회용 스틸)·운송 조건(적재 형상·고정 방식)을 검증한다. 최종 Audit 결과 시스템 Lock. |
| 9 | 불량격리·8D·변경관리 | OEM 클레임, 8D 보고서(원인분석·시정조치), 금형변경(Die Modification Record), 공정변경(PCN/ECN) 이력을 관리한다. 특채/재작업/폐기 구분하여 품질 비용 추적. |
| 10 | 출하·고객 Lot Trace | 고객 lot별 소재(Coil/Blank), 금형(Die ID), 용접조건(Robot Program·Weld Schedule), 검사 결과(CMM/Gauge/Weld)를 확정한다. ERP-MES-PLM-SRM-WMS 통합 데이터로 고객 감사 대응. |

### H04.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 客户图纸、模具与PPAP基准 | 确定OEM图纸、公差(GD&T)、材料规格(钢种/厚度)、模具/夹具、PPAP等级(Level 3)和检验计划(Control Plan)。基于AAS(资产管理壳)标准化数据采集。准备通过客户EDI/EAI接收生产顺序信息。 |
| 2 | 材料、卷料与Blank投入 | 将Coil lot(钢种代码·厚度mm)、Blank lot(Blank尺寸·重量)、表面状态(氧化皮/油)作为投入履历管理。AI视觉检测实时识别材料表面缺陷(划痕/气孔)。通过QR码实现全数质量履历追溯系统。 |
| 3 | 冲压与成形 | 管理Die ID(模具寿命预测管理)、冲压条件(压机能力·速度·负载tonf)、润滑(Roll Coater/Oil Mist)、成形载荷(Ton)、Scrap/返工。通过超高压压铸(Giga Casting, 3,500吨级)实现电机壳体等大型部件全工序自动化(熔解-注入-冷却)。AI异常检测实现OEE提升8-10%。 |
| 4 | 焊接与装配Cell | 记录Robot program(焊接机器人变位机·焊枪角度)、Weld schedule(电流kA·电压V·时间cycle·加压力kN)、夹具、点焊/缝焊质量(熔核直径mm·剪切强度kN)。AI视觉检测识别0.1mm级焊接缺陷，检测效率提升10倍。基于OPC-UA实现异构机器人间实时通信。 |
| 5 | 加工、热处理与表面处理 | 管理加工(铣削/钻孔/攻丝)、热处理(渗碳·高频淬火温度/时间/硬度HRC)、涂装/电镀(Zn/Ni镀层厚度μm)/防锈(防锈油涂布量g/m²)等后处理条件和结果。 |
| 6 | 尺寸与强度检查Gate | 通过CMM(三坐标测量机, 6σ公差)、Gauge(通止规/卡规)、焊接强度(拉伸/剪切试验kN)、扭矩(N·m)、耐久测试(疲劳测试Cycle)判定合格。100%采集232个车身精度点数据。Gate FAIL时分析原因后反馈Step 3/4/5。 |
| 7 | 子总成与Kitting | 装配底盘/制动子模块(副车架·控制臂·卡钳)，并按客户顺序(JIS顺序)·交付单位(托盘·料架)绑定。按客户产线投入顺序执行Sequence Picking。 |
| 8 | 出货前Audit与标签 | 验证标签(客户指定格式、GTIN/UDI)、交货lot编号、客户ASN(EDI 856)、包装(周转/一次性料架)·运输条件(装载形态·固定方式)。最终Audit结果系统锁定。 |
| 9 | 不良隔离、8D与变更管理 | 管理OEM索赔、8D报告(原因分析·纠正措施)、模具变更(Die Modification Record)、工艺变更(PCN/ECN)履历。按让步接收/返工/报废分类跟踪质量成本。 |
| 10 | 出货与客户Lot Trace | 确认客户lot级材料(Coil/Blank)、模具(Die ID)、焊接条件(Robot Program·Weld Schedule)、检查结果(CMM/Gauge/Weld)。通过ERP-MES-PLM-SRM-WMS整合数据应对客户审核。 |

### H04.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 금형·프레스 조건과 치수 결과를 연결하지 않으면 반복 불량의 원인추적이 어렵다. 측정 방법: Die ID QR/Barcode 자동 스캔 → 프레스 파라미터(Tonnage·Speed·Binder Force) 실시간 PLC 수집 → CMM 치수 데이터와 매칭. 관리 주기: Every Lot(프레스 Stroke당) 전수. 이상 시 조치: 금형 마모 의심 시 Die Maintenance Trigger, 치수 이탈 반복 시 금형 수정(Die Try-Out) 후 PPAP 재승인. | 3,6,10 | process_step | Die/Dimension Trace |
| 용접 조건과 로봇 프로그램은 강도·외관·고객 클레임 분석의 핵심 데이터다. 측정 방법: Weld Controller에서 실제 전류·전압·시간 실시간 수집, AI 비전 검사 결과(Weld Nugget 직경·표면)와 통합. 관리 주기: Every Lot(매 용접 Spot/Seam) 전수. 이상 시 조치: 용접 강도 불량 시 용접 Schedule 보정 + Robot Path 재교시, Tip Dress 주기 단축. | 4,6 | process_step | Weld Quality |
| OEM JIT 납입은 출하 lot·ASN·서열 정보를 공정 lot과 연결해야 한다. 측정 방법: 바코드 스캔/ RFID Gate로 출하 Lot ID 인식 → MES에서 고객 ASN(EDI 856)과 자동 매칭, 서열 위반 감지. 관리 주기: Real-time(매 출하 단위). 이상 시 조치: 서열·납기 오류 감지 시 출하 Gate Block + 물류팀에 재피킹 지시, 고객 EDI 862 JIT 일정 변동 자동 반영. | 7,8,10 | process_step | OEM Delivery |
| PPAP·도면 Revision·공정변경 이력은 출하 승인 조건으로 관리한다. 측정 방법: PLM/ECR 시스템에서 Rev 상태 확인, MES의 Route Master와 검증. 관리 주기: 변경 발생 시(Every Change) + 정기 PPAP 만료일 관리. 이상 시 조치: 구 Revision 도면으로 생산된 Lot 출하 Block, 고객 승인 없는 변경 감지 시 즉시 생산 중단. | 1,9,10 | process_step | PPAP/Change Control |
| Scrap·재작업·특채는 원가 Loss와 고객품질을 동시에 보는 기준으로 분류한다. 측정 방법: MES Scrap/재작업 코드 입력(원인 코드·비용), MRB 회의 결과(GO/NO-GO) 시스템 등록. 관리 주기: Every Lot(발생 건별) 전수 + 주간 MRB 집계. 이상 시 조치: scrap율/재작업율 목표 초과 시 개선 프로젝트 Trigger, 특채(Concession)은 고객 승인 문서와 함께 아카이브. | 3,6,9 | process_step | Loss/MRB |

### H04.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 若模具/冲压条件与尺寸结果未连接，重复不良的原因追溯会很困难。测量方法：Die ID QR/条码自动扫描 → 冲压参数(吨位·速度·压边力)实时PLC采集 → 与CMM尺寸数据匹配。管理周期：Every Lot(每冲压Stroke)全数。异常处理：模具磨损可疑时触发Die Maintenance，尺寸反复偏离时模具修改(Die Try-Out)后PPAP重新批准。 | 3,6,10 | process_step | 模具/尺寸追溯 |
| 焊接条件和机器人程序是强度、外观和客户索赔分析的核心数据。测量方法：Weld Controller实时采集实际电流·电压·时间，与AI视觉检查结果(熔核直径·表面)整合。管理周期：Every Lot(每焊接Spot/Seam)全数。异常处理：焊接强度不良时修正Weld Schedule + Robot Path重新示教，缩短修磨周期。 | 4,6 | process_step | 焊接质量 |
| OEM JIT交付需要将出货lot、ASN和顺序信息与工序lot连接。测量方法：条码扫描/RFID Gate识别出货Lot ID → MES与客户ASN(EDI 856)自动匹配，检测顺序违规。管理周期：Real-time(每出货单位)。异常处理：检测顺序/交期错误时出货Gate Block + 物流团队重新拣配指令，自动反映客户EDI 862 JIT日程变动。 | 7,8,10 | process_step | OEM交付 |
| PPAP、图纸Revision和工艺变更履历应作为出货批准条件管理。测量方法：PLM/ECR系统确认Rev状态，与MES的Route Master验证。管理周期：变更发生时(Every Change) + 定期PPAP到期日管理。异常处理：按旧Revision图纸生产的Lot出货Block，检测到无客户批准的变更时立即停止生产。 | 1,9,10 | process_step | PPAP/变更控制 |
| Scrap、返工和让步接收应按成本损失和客户质量双重维度分类。测量方法：MES Scrap/返工代码输入(原因代码·成本)，MRB会议结果(GO/NO-GO)系统登记。管理周期：Every Lot(每发生项)全数 + 周MRB汇总。异常处理：报废率/返工率超出目标时启动改善项目，让步接收(Concession)与客户批准文件一并存档。 | 3,6,9 | process_step | 损失/MRB |

### H04.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Engineering | process |  |  | drawing_rev, ppap_level |
| 2 | Material | process |  |  | coil_lot, blank_lot |
| 3 | Stamping | process |  |  | part_lot, die_id |
| 4 | Welding | process |  |  | part_lot, weld_program_id, robot_id |
| 5 | Treatment | process |  |  | part_lot |
| 6 | Quality Gate | gate |  | 2,3,4,5 | part_lot, dimension_result, torque_result |
| 7 | Kitting | process |  |  | part_lot, ship_lot |
| 8 | Shipment Prep | process |  |  | ship_lot |
| 9 | Customer Quality | process |  |  | part_lot, ppap_level |
| 10 | Shipment | process |  |  | ship_lot, part_lot |

### H04.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Engineering | process |  |  | drawing_rev, ppap_level |
| 2 | Material | process |  |  | coil_lot, blank_lot |
| 3 | Stamping | process |  |  | part_lot, die_id |
| 4 | Welding | process |  |  | part_lot, weld_program_id, robot_id |
| 5 | Treatment | process |  |  | part_lot |
| 6 | Quality Gate | gate |  | 2,3,4,5 | part_lot, dimension_result, torque_result |
| 7 | Kitting | process |  |  | part_lot, ship_lot |
| 8 | Shipment Prep | process |  |  | ship_lot |
| 9 | Customer Quality | process |  |  | part_lot, ppap_level |
| 10 | Shipment | process |  |  | ship_lot, part_lot |

### H04.10 step_expression 연결 설명 (ko/zh)

**ko:** H04(차체·섀시·제동)는 Step 1 Engineering에서 OEM 도면·PPAP 기준이 확정된 후, Step 2 Material(코일/Blank 투입) → Step 3 Stamping(프레스 성형, Die ID 중심) → Step 4 Welding(로봇 용접) → Step 5 Treatment(열처리·도장)로 직렬 연결된다. Step 6 Quality Gate가 Step 2~5의 모든 소재·공정 결과를 gate_for로 검증하며, Die ID-Weld Condition-Dimension 데이터를 통합 분석한다. Pass 시 Step 7 Kitting에서 고객 서열 단위로 묶이고, Step 8 Shipment Prep에서 라벨·ASN이 검증된다. Step 9 Customer Quality는 고객 클레임·8D·변경 이력을 추적하며, Step 10 Shipment에서 고객 Lot별 전(全)이력(Chemical·Mechanical·Visual)이 확정되어 ERP-MES-PLM-SRM-WMS 통합 데이터로 출하된다.

**zh:** H04(车身·底盘·制动)在Step 1 Engineering确定OEM图纸/PPAP基准后，经Step 2 Material(卷料/Blank投入) → Step 3 Stamping(冲压成形, 以Die ID为中心) → Step 4 Welding(机器人焊接) → Step 5 Treatment(热处理/涂装)串联。Step 6 Quality Gate验证Step 2~5所有材料/工序结果(gate_for)，整合分析Die ID-Weld Condition-Dimension数据。Pass后Step 7 Kitting按客户顺序单位绑定，Step 8 Shipment Prep验证标签/ASN。Step 9 Customer Quality追踪客户索赔/8D/变更履历，Step 10 Shipment按客户Lot确认全履历(Chemical·Mechanical·Visual)，通过ERP-MES-PLM-SRM-WMS整合数据出货。

### H04.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Die Setup Verification |
| 3 | 2 | First-off Inspection |
| 4 | 1 | Robot Program Verification |
| 6 | 1 | CMM/Gauge Check |
| 6 | 2 | Weld Strength Test |
| 8 | 1 | ASN Label Verification |

### H04.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Die Setup 验证 |
| 3 | 2 | First-off 检查 |
| 4 | 1 | Robot Program 验证 |
| 6 | 1 | CMM/Gauge 检查 |
| 6 | 2 | Weld Strength 测试 |
| 8 | 1 | ASN Label 验证 |

### H04.9 data_capture_points

```yaml
data_capture_points:
  - part_lot
  - coil_lot
  - blank_lot
  - die_id
  - weld_program_id
  - robot_id
  - dimension_result
  - torque_result
  - ppap_level
  - drawing_rev
  - ship_lot
```


## H05 `automotive_electronics` — 자동차 전장·전자모듈 / 汽车电子与电控模块

```yaml
industry_code: H
subindustry_code: H05
legacy_slug: automotive_electronics
label_ko: "자동차 전장·전자모듈"
label_zh: "汽车电子与电控模块"
label_en: ""
label_ja: ""
q3_cluster: "P3_LABOR_ASSEMBLY"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "electronics_serial_assembly_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** ECU, domain controller, sensor/ADAS, wiring harness  
**产品范围 zh:** ECU、域控制器、传感器/ADAS、线束

### H05.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 고객사양·HW/SW Revision | ECU/센서/ADAS/하네스의 고객사양, HW Revision(PCB Rev·BOM Rev), Software/Firmware 기준(Version·Checksum)을 확정한다. 기능안전(ISO 26262 ASIL) 요구사항 반영, SW Genealogy 구성 기준 수립. |
| 2 | 자재·PCB·부품 투입 | PCB lot(동박 두께·층수), IC/ASIC/MCU·MLCC(정전용량·전압)·Connector lot, Harness wire lot(Wire Gauge·색상)를 투입하고 MSD(MSL Level, Moisture Sensitivity)/ESD(정전기 방전, <100V) 조건을 확인한다. 부품 D/C(제조일자)와 Lot Code를 PCB Serial에 연결. |
| 3 | SMT/전자 조립 | SMT(Reflow Profile: 예열·Soak·Reflow·Cooling 각 구간 온도 ℃·시간 sec), Soldering(Selective/Wave Solder), Press-fit(압입력 N), Conformal Coating(도포 두께 μm), Harness crimp(Crimp 높이 mm·인장강도 N) 조건과 AOI/AXI 검사 결과를 기록한다. ICP(Inductively Coupled Plasma) 분석 등 납땜 품질 실시간 모니터링. |
| 4 | Firmware Flash·Configuration | 부품 Serial별 Firmware(FBL/ISO 14229 UDS 프로토콜), Calibration file(파라미터 Map), Variant coding(지역별/고객별 차등 기능 설정)을 기록한다. Flash Checksum 자동 검증, SW Version Mismatch 시 Flash 재기입 또는 Gate 차단. |
| 5 | 기능·통신 검사 Gate | ICT(In-Circuit Test: 오픈/쇼트·부품값 측정), FCT(Functional Test: 전원·I/O·ADC/DAC), CAN/LIN/Ethernet 통신(프레임 에러·신호 레벨), 전원·입출력 기능을 판정한다. Fail 시 Step 3/4로 원인 피드백. |
| 6 | Burn-in / Environmental Stress | 열충격(Thermal Shock -40℃↔+125℃, 100 cycle), Burn-in(고온가동 85℃/48h), 방수(IP67/IP69K)·진동(Random 10-2000Hz, 3축) 등 신뢰성 조건과 결과를 수집한다. Weibull 분석으로 고장률 예측. |
| 7 | ADAS/Sensor Calibration | 카메라(FOV 정렬·초점), 레이더(Azimuth/Elevation Angle), 라이다(Point Cloud 정합) 정렬, 보정값(Calibration Matrix), Calibration ID를 제품 Serial에 연결한다. Calibration Rig에서 자동 수행, 결과 Hash 생성. |
| 8 | Final EOL·Label·UDI/QR | 최종 기능검사(Full Function Test), 라벨(고객 지정 포맷·UDI), QR/Serial(2D Matrix Code, GS1 표준), 고객 데이터 파일(Flash Data·Calibration Data·Test Report)을 확정한다. 모든 데이터는 Serial 기준으로 Lock. |
| 9 | 불량분석·8D·재검 | 전기불량(Short/Open/Leakage), Solder 불량(Bridging/Cold Joint/Head-in-Pillow), SW 불량(Watchdog Reset/Boot Failure)을 분류하고 재검·8D 이력을 관리한다. X-ray/CT 분석으로 잠재 결함 식별. |
| 10 | 출하·Software Genealogy | Serial별 BOM lot(PCB·IC·MLCC·Connector), HW/SW Revision(빌드 ID·Git Commit Hash), 시험성적(ICT/FCT/EOL Raw Data), 출하 lot을 확정한다. Digital Twin 기반 SW-OT(Over-The-Air) 업데이트 이력 포함. |

### H05.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 客户规格与HW/SW Revision | 确定ECU/传感器/ADAS/线束的客户规格、硬件Revision(PCB Rev·BOM Rev)、Software/Firmware基准(Version·Checksum)。反映功能安全(ISO 26262 ASIL)要求，建立SW Genealogy构成基准。 |
| 2 | 材料、PCB与部件投入 | 投入PCB lot(铜厚·层数)、IC/ASIC/MCU·MLCC(电容·电压)·Connector lot、线束wire lot(线径·颜色)，确认MSD(MSL等级, 湿敏度)/ESD(静电放电, <100V)条件。将部件D/C(制造日期)和Lot Code连接至PCB Serial。 |
| 3 | SMT/电子装配 | 记录SMT(Reflow Profile: 预热·Soak·Reflow·Cooling各段温度℃·时间sec)、焊接(Selective/Wave Solder)、Press-fit(压入力N)、Conformal Coating(涂覆厚度μm)、Harness crimp(压接高度mm·拉伸强度N)条件和AOI/AXI检查结果。通过ICP(电感耦合等离子体)分析等实时监测焊接质量。 |
| 4 | Firmware Flash与Configuration | 按部件Serial记录Firmware(FBL/ISO 14229 UDS协议)、Calibration file(参数Map)、Variant coding(区域/客户差异化功能设置)。自动验证Flash Checksum，SW Version不匹配时重写Flash或阻断Gate。 |
| 5 | 功能与通信检查Gate | 判定ICT(In-Circuit Test: 开/短路·元件值测量)、FCT(Functional Test: 电源·I/O·ADC/DAC)、CAN/LIN/Ethernet通信(帧错误·信号电平)、电源与I/O功能。Fail时反馈Step 3/4原因分析。 |
| 6 | Burn-in / Environmental Stress | 采集热冲击(Thermal Shock -40℃↔+125℃, 100 cycle)、Burn-in(高温运行85℃/48h)、防水(IP67/IP69K)·振动(Random 10-2000Hz, 3轴)等可靠性条件和结果。通过Weibull分析预测失效率。 |
| 7 | ADAS/Sensor Calibration | 将摄像头(FOV对准·对焦)、雷达(Azimuth/Elevation Angle)、LiDAR(点云配准)对准、标定值(Calibration Matrix)、Calibration ID绑定到产品Serial。Calibration Rig自动执行，生成结果Hash。 |
| 8 | Final EOL、Label与UDI/QR | 确认最终功能检查(Full Function Test)、标签(客户指定格式·UDI)、QR/Serial(2D Matrix Code, GS1标准)、客户数据文件(Flash Data·Calibration Data·Test Report)。所有数据按Serial锁定。 |
| 9 | 不良分析、8D与复检 | 分类管理电气不良(Short/Open/Leakage)、焊接不良(Bridging/Cold Joint/Head-in-Pillow)、软件不良(Watchdog Reset/Boot Failure)及复检/8D履历。通过X-ray/CT分析识别潜在缺陷。 |
| 10 | 出货与Software Genealogy | 确认Serial级BOM lot(PCB·IC·MLCC·Connector)、HW/SW Revision(构建ID·Git Commit Hash)、测试成绩(ICT/FCT/EOL Raw Data)、出货lot。包含基于Digital Twin的SW-OT(Over-The-Air)更新履历。 |

### H05.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 자동차 전장은 HW/SW/Calibration 이력이 물리 Serial과 연결되어야 기능안전·리콜 대응이 가능하다. 측정 방법: PCB Serial(레이저 마킹) → SMT 후 IC·MLCC Lot Code 스캔 → MES Genealogy Tree 구축, SW Version Hash 자동 수집. 관리 주기: Every Lot 전수. 이상 시 조치: 부품 Lot Traceability 끊김 시 Assembly 전체 Hold, SW Version 불일치 시 Flash 재기입 후 재검증. | 1,4,7,10 | process_step | HW/SW Genealogy |
| ICT/FCT/EOL 원본값은 고객 불량분석과 예측품질의 핵심 입력이다. 측정 방법: ICT(Keysight/Teradyne Tester), FCT(고객 맞춤 Function Tester), EOL Tester에서 Raw Data 자동 수집(Vector·Waveform·Timing). 관리 주기: Every Lot 전수. 이상 시 조치: 측정값 Outlier 감지 시 해당 Serial 격리 + 분석, 특정 불량 패턴 반복 시 SMT/조립 공정 피드백 + AI 기반 예측 모델 재학습. | 5,8,9 | process_step | Test Data Trace |
| MSD/ESD, Soldering, Crimp 조건은 잠재불량 관리에 포함해야 한다. 측정 방법: MSD(습도 Indicator·Bake 기록), ESD(정전기 모니터링 시스템, Ionizer 성능), Soldering(Reflow Oven Profile Thermocouple, AOI/AXI). 관리 주기: MSD/ESD: 주기적(매 Shift) + 경보 발생 시, Soldering/Crimp: Every Lot 전수. 이상 시 조치: MSD 초과 부품 Bake 처리 후 사용, ESD 경보 시 해당 Station 작업중지 + 접지확인, Soldering Profile 이탈 시 Oven 재교정. | 2,3,6 | process_step | Process Condition |
| ADAS 센서·도메인컨트롤러는 Calibration ID와 소프트웨어 버전을 함께 추적한다. 측정 방법: Calibration Rig(광학 정렬 장치·Target Board)에서 측정값 자동 수집, Calibration Matrix와 SW Version을 Serial에 바인딩. 관리 주기: Every Lot 전수. 이상 시 조치: Calibration 결과 Outlier 시 제품격리 + Calibration Rig 점검(광원·Target 위치), SW 불일치 시 Flash Tool로 재기입. | 4,7,10 | process_step | ADAS Calibration |
| 고객 변경점, SW 업데이트, 라벨 데이터는 출하 전 승인 상태로 잠금 처리한다. 측정 방법: ECR/ECN 시스템에서 변경 승인 상태 확인, MES Label Data Lock Flag 자동 설정. 관리 주기: 변경 발생 시(Every Change) + 출하 Lot 생성 시. 이상 시 조치: 미승인 변경 포함 Lot 출하 Block, 미일치 라벨 발견 시 재발행 + 원본 데이터와 대사 검증. | 1,8,10 | process_step | Change/Release Control |

### H05.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 汽车电子必须将HW/SW/Calibration履历与实物Serial连接，才能支持功能安全和召回响应。测量方法：PCB Serial(激光刻印) → SMT后扫描IC·MLCC Lot Code → MES构建Genealogy Tree，自动采集SW Version Hash。管理周期：Every Lot全数。异常处理：部件Lot Traceability中断时Assembly整体Hold，SW Version不匹配时重写Flash后复验。 | 1,4,7,10 | process_step | HW/SW谱系 |
| ICT/FCT/EOL原始值是客户不良分析和预测质量的关键输入。测量方法：ICT(Keysight/Teradyne Tester)、FCT(客户定制Function Tester)、EOL Tester自动采集Raw Data(Vector·Waveform·Timing)。管理周期：Every Lot全数。异常处理：测量值离群时隔离该Serial+分析，特定不良模式重复时反馈SMT/装配工艺+AI预测模型重新训练。 | 5,8,9 | process_step | 测试数据追溯 |
| MSD/ESD、焊接和压接条件应纳入潜在不良管理。测量方法：MSD(湿度Indicator·Bake记录)、ESD(静电监控系统、Ionizer性能)、焊接(Reflow Oven Profile热电偶、AOI/AXI)。管理周期：MSD/ESD: 周期性(每Shift) + 报警时，焊接/压接: Every Lot全数。异常处理：MSD超标部件Bake处理后使用，ESD报警时该Station停工+接地检查，焊接Profile偏离时Oven重新校准。 | 2,3,6 | process_step | 工艺条件 |
| ADAS传感器和域控制器需同时追踪Calibration ID和软件版本。测量方法：Calibration Rig(光学对准装置·Target Board)自动采集测量值，Calibration Matrix和SW版本绑定至Serial。管理周期：Every Lot全数。异常处理：Calibration结果离群时产品隔离+Calibration Rig点检(光源·Target位置)，SW不匹配时Flash Tool重写。 | 4,7,10 | process_step | ADAS标定 |
| 客户变更点、SW更新和标签数据应在出货前按批准状态锁定。测量方法：ECR/ECN系统确认变更批准状态，MES自动设置Label Data Lock Flag。管理周期：变更发生时(Every Change) + 出货Lot生成时。异常处理：包含未批准变更的Lot出货Block，发现不一致标签时重新打印+与原始数据核对验证。 | 1,8,10 | process_step | 变更/放行控制 |

### H05.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Engineering | process |  |  | serial_no, firmware_version |
| 2 | Material | process |  |  | pcb_lot, component_lot |
| 3 | Electronic Assembly | process |  |  | serial_no, pcb_lot, component_lot |
| 4 | Software | process |  |  | serial_no, firmware_version, flash_result |
| 5 | Function Gate | gate |  | 2,3,4 | serial_no, functional_test_result, flash_result |
| 6 | Reliability | process |  |  | serial_no, burn_in_result |
| 7 | Calibration | process |  |  | serial_no, calibration_id |
| 8 | EOL Gate | gate |  | 5,6,7 | serial_no, eol_result |
| 9 | Failure Analysis | process |  |  | serial_no, functional_test_result |
| 10 | Shipment | process |  |  | serial_no, eol_result, firmware_version |

### H05.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Engineering | process |  |  | serial_no, firmware_version |
| 2 | Material | process |  |  | pcb_lot, component_lot |
| 3 | Electronic Assembly | process |  |  | serial_no, pcb_lot, component_lot |
| 4 | Software | process |  |  | serial_no, firmware_version, flash_result |
| 5 | Function Gate | gate |  | 2,3,4 | serial_no, functional_test_result, flash_result |
| 6 | Reliability | process |  |  | serial_no, burn_in_result |
| 7 | Calibration | process |  |  | serial_no, calibration_id |
| 8 | EOL Gate | gate |  | 5,6,7 | serial_no, eol_result |
| 9 | Failure Analysis | process |  |  | serial_no, functional_test_result |
| 10 | Shipment | process |  |  | serial_no, eol_result, firmware_version |

### H05.10 step_expression 연결 설명 (ko/zh)

**ko:** H05(자동차 전장·전자모듈)는 Step 1 Engineering에서 HW/SW 기준이 수립되고, Step 2 Material에서 PCB·부품 Lot이 투입된 후 Step 3 Electronic Assembly(SMT+Press-fit+Coating)에서 HW Genealogy가 형성된다. Step 4 Software에서 Firmware Flash가 이루어지며(제품 Serial 기반 SW Trace), Step 5 Function Gate가 Step 2~4의 자재·조립·SW 결과를 gate_for로 종합 검증한다. Pass 시 Step 6 Reliability(Burn-in/열충격)를 거쳐 Step 7 Calibration(ADAS 센서 정렬)이 Serial에 바인딩된다. Step 8 EOL Gate는 Step 5/6/7의 결과를 최종 재검증하여 최종 합격 판정한다. Step 9 Failure Analysis에서 불량 원인별 분석이 이루어지고, Step 10 Shipment에서 HW/SW Genealogy가 완전히 확정된다.

**zh:** H05(汽车电子)在Step 1 Engineering确立HW/SW基准，Step 2 Material投入PCB/部件Lot后，Step 3 Electronic Assembly(SMT+Press-fit+Coating)形成HW Genealogy。Step 4 Software执行Firmware Flash(基于产品Serial的SW Trace)，Step 5 Function Gate综合验证Step 2~4的材料/装配/SW结果(gate_for)。Pass后经Step 6 Reliability(Burn-in/热冲击)，Step 7 Calibration(ADAS传感器对准)绑定至Serial。Step 8 EOL Gate最终复验Step 5/6/7的结果做出合格判定。Step 9 Failure Analysis按原因分类分析，Step 10 Shipment完全确定HW/SW Genealogy。

### H05.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | SMT Reflow Profile Capture |
| 4 | 1 | Firmware Flash |
| 5 | 1 | ICT/FCT Test |
| 6 | 1 | Burn-in Cycle |
| 7 | 1 | Sensor Calibration |
| 8 | 1 | Final Label Verification |

### H05.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | SMT Reflow Profile 采集 |
| 4 | 1 | Firmware写入 |
| 5 | 1 | ICT/FCT 测试 |
| 6 | 1 | Burn-in Cycle |
| 7 | 1 | Sensor Calibration |
| 8 | 1 | Final Label 验证 |

### H05.9 data_capture_points

```yaml
data_capture_points:
  - serial_no
  - pcb_lot
  - component_lot
  - firmware_version
  - flash_result
  - calibration_id
  - functional_test_result
  - burn_in_result
  - eol_result
```


## H06 `interior_exterior_plastic` — 내장·외장·플라스틱 부품 / 内外饰与塑料部件

```yaml
industry_code: H
subindustry_code: H06
legacy_slug: interior_exterior_plastic
label_ko: "내장·외장·플라스틱 부품"
label_zh: "内外饰与塑料部件"
label_en: ""
label_ja: ""
q3_cluster: "P3_LABOR_ASSEMBLY"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "plastic_trim_assembly_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** dashboard, door trim, bumper, seat/interior module  
**产品范围 zh:** 仪表板、门饰板、保险杠、座椅/内饰模块

### H06.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 고객사양·색상·옵션 기준 | 내외장·시트·플라스틱 부품의 색상(color code·RAL/Pantone), Grain(Texture), 옵션(LH/RH·유/무), 고객도면, 승인샘플(Gold Sample·Boundary Sample)을 확정한다. 고객사 JIS 정보(차종·색상·시트 옵션) 수신 인터페이스 설정. |
| 2 | 수지·원단·부자재 투입 | Resin lot(PP/ABS/PC-ABS/PU, MFI·밀도), fabric/leather lot(색상·Texture 코드, 내마모성), foam(PU 폼 경도·밀도), insert(금속 인서트·너트), fastener(클립·스크류) 투입 이력을 구성한다. Resin Dryer 조건(건조 온도℃·시간h) 관리. |
| 3 | 사출·발포·성형 | Mold ID(금형 온도℃·냉각 시간s), 사출조건(사출압력 bar·사출속도 mm/s·보압력 bar·실린더 온도℃), 발포조건(PU/PP 발포 온도℃·압력 bar·밀도 g/cm³), 수축(shrinkage %·CAE 해석 예측 대비 실제), 뒤틀림(Warpage mm), 외관 상태(Flow Mark·Weld Line·Sink Mark)를 기록한다. Mold Flow Simulation과 실측 데이터 비교 분석. |
| 4 | 도장·표면처리·가식 | 도장(Robotic Paint: Base Coat+Clear Coat 건조 온도℃·시간min, Paint Viscosity mPa·s), 크롬(Electric Plating: Cr/Chrome 두께 μm), 필름(IMD·INS Film lamination 온도℃·압력 bar), 가죽감싸기(Leather Wrapping: 접착제 도포량 g/m²·경화 시간min), Laser scoring(Airbag Tear Line 깊이 mm·잔류 두께 mm) 등 외관공정을 관리한다. |
| 5 | 봉제·조립·클립 체결 | Seat/Trim/Module 조립(Assembly Jig ID·Push Force N), 클립(클립 삽입력 N·체결 완료 감지), 체결(Torque N·m), Gap/Fit(mm) 조건을 확인한다. Vision System으로 조립 완료 상태 자동 판정. |
| 6 | 외관·색차·Fit Gap Gate | 색차(Spectrophotometer, ΔE<1.0 기준), 스크래치(Depth μm·Visual 기준), 변형(Profile 측정 mm), Gap/Fit(Gap·Flush mm, Feeler Gauge), 냄새/VOC(VOC µg/m³, Odor Test 기준) 검사로 합격을 판정한다. Master Sample과 Side-by-Side 비교. |
| 7 | 서열·Kitting·라인공급 | 차종·색상·좌우(LH/RH)·옵션 단위로 JIS(Just-In-Sequence) 또는 Kit 공급을 준비한다. 고객 생산서열(Sequence No) 기반 Pick-to-Light/DPS(Digital Picking System)로 정확도 확보. 서열 정보는 MES↔고객 EDI 실시간 동기화. |
| 8 | 포장·출하 Audit | 외관보호(Protective Film·Edge Protector·Separator지), 포장방식(Returnable Rack·Collapsible Box), 고객 ASN(EDI 856·Label 포맷), 출하 lot을 확인한다. 최종 Audit 시 QR 코드 스캔으로 모든 데이터 Lock. |
| 9 | 불량·색상편차·변경관리 | 외관불량(흠집·색상편차·이물), 색차(ΔE 기준 초과), 금형수정(Die Engineering Change), 소재변경(Resin Grade Change·Colorant Change), 고객승인 이력(CSR·Witness Sample 승인)을 관리한다. |
| 10 | 출하·Lot/Option Trace | 차량 옵션(Option Code·Feature Code)·색상(Color Code)·부품 lot(Resin/Fabric/Mold)·검사 결과(외관·색차·Gap/Fit)를 출하 단위로 확정한다. 고객 라인에서의 결품·오조립을 방지하기 위한 최종 검증 완료. |

### H06.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 客户规格、颜色与选项基准 | 确定内外饰/座椅/塑料件的颜色(color code·RAL/Pantone)、纹理(Grain)、选装(LH/RH·有无)、客户图纸和批准样件(Gold Sample·Boundary Sample)。设定接收客户JIS信息(车型·颜色·座椅选装)的接口。 |
| 2 | 树脂、面料与辅料投入 | 建立Resin lot(PP/ABS/PC-ABS/PU, MFI·密度)、fabric/leather lot(颜色·Texture代码, 耐磨性)、foam(PU泡沫硬度·密度)、insert(金属嵌件·螺母)、fastener(卡扣·螺钉)投入履历。管理Resin Dryer条件(干燥温度℃·时间h)。 |
| 3 | 注塑、发泡与成形 | 记录Mold ID(模具温度℃·冷却时间s)、注塑条件(注射压力bar·注射速度mm/s·保压压力bar·料筒温度℃)、发泡条件(PU/PP发泡温度℃·压力bar·密度g/cm³)、收缩(shrinkage %·CAE解析预测与实际对比)、翘曲(Warpage mm)、外观状态(Flow Mark·Weld Line·Sink Mark)。进行Mold Flow Simulation与实测数据对比分析。 |
| 4 | 涂装、表面处理与装饰 | 管理喷涂(Robotic Paint: Base Coat+Clear Coat干燥温度℃·时间min, Paint Viscosity mPa·s)、镀铬(Electric Plating: Cr/Chrome厚度μm)、贴膜(IMD·INS Film lamination温度℃·压力bar)、包覆(Leather Wrapping: 胶粘剂涂布量g/m²·固化时间min)、Laser scoring(气囊撕裂线深度mm·残留厚度mm)等外观工艺。 |
| 5 | 缝制、装配与卡扣紧固 | 确认Seat/Trim/Module装配(Assembly Jig ID·Push Force N)、卡扣(卡扣插入力N·紧固完成检测)、紧固(Torque N·m)、Gap/Fit(mm)条件。通过Vision System自动判定装配完成状态。 |
| 6 | 外观、色差与Fit Gap Gate | 通过色差(Spectrophotometer, ΔE<1.0基准)、划伤(Depth μm·Visual基准)、变形(Profile测量mm)、Gap/Fit(Gap·Flush mm, Feeler Gauge)、气味/VOC(VOC µg/m³, Odor Test基准)检查判定合格。与Master Sample进行Side-by-Side比较。 |
| 7 | 顺序、Kitting与线边供料 | 按车型、颜色、左右件(LH/RH)、选装准备JIS(Just-In-Sequence)或Kit供料。基于客户生产顺序(Sequence No)的Pick-to-Light/DPS(Digital Picking System)确保准确度。顺序信息通过MES↔客户EDI实时同步。 |
| 8 | 包装与出货Audit | 确认外观保护(Protective Film·Edge Protector·隔纸)、包装方式(Returnable Rack·Collapsible Box)、客户ASN(EDI 856·标签格式)、出货lot。最终Audit时通过QR码扫描锁定所有数据。 |
| 9 | 不良、色差与变更管理 | 管理外观不良(划痕·色差·异物)、色差(ΔE基准超标)、模具修改(Die Engineering Change)、材料变更(Resin Grade Change·Colorant Change)、客户批准履历(CSR·Witness Sample批准)。 |
| 10 | 出货与Lot/Option Trace | 按出货单位确认车辆选装(Option Code·Feature Code)·颜色(Color Code)·部件lot(Resin/Fabric/Mold)·检查结果(外观·色差·Gap/Fit)。完成最终验证，防止客户产线缺料或错装。 |

### H06.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 색상·Grain·옵션 오류는 고객 라인에서 바로 결품·오조립으로 연결되므로 사양 기준을 엄격히 관리한다. 측정 방법: MES Option Code Master와 생산지시 간 자동 비교, 바코드 스캐너로 색상 코드·Grain 코드 실시간 검증. 관리 주기: Every Lot 전수. 이상 시 조치: 기준 불일치 시 해당 Kitting 출하 Block, 고객 라인 피드백 기반 Master Data 정정 프로세스 실행. | 1,7,10 | process_step | Option/Color Trace |
| 수지 lot, 금형 ID, 사출조건은 외관·치수 불량 원인분석의 핵심이다. 측정 방법: Resin Lot 코드 자동 스캔, 금형 온도·압력·속도 센서 데이터 PLC 수집, CAE 예측 대비 실제 Shrinkage 비교. 관리 주기: Every Lot(사출 Cycle당) 전수. 이상 시 조치: 수축률·뒤틀림 기준 초과 시 금형 온도·보압 조정, Resin Lot 변경 시 Mold Flow Simulation 재실행 + 시사출 검증. | 2,3,6 | process_step | Mold/Material Trace |
| 외관·색차·VOC·냄새 검사는 주관 판정을 줄이기 위해 기준사진·수치값과 연결한다. 측정 방법: Spectrophotometer(ΔE), Gloss Meter(광택도 GU), Profile Projector(변형), VOC Chamber(µg/m³), Odor Test Panel(1-6등급). 관리 주기: Every Lot(외관·색차) + 주기적(VOC·Odor 1회/Lot 또는 월). 이상 시 조치: ΔE 기준 초과 시 도장 조건(Paint Viscosity·건조 온도) 조정 후 재시험, VOC 초과 시 소재·공정 변경 검토. | 4,6,9 | process_step | Appearance Quality |
| JIS/Kitting 공급은 좌우품·색상·옵션·서열을 동시에 검증해야 한다. 측정 방법: DPS(Pick-to-Light) 표시등 확인, 바코드 스캔으로 Picked Part 검증, 고객 Sequence No 기준 MES 매칭. 관리 주기: Real-time(매 Kitting/Picking 단위) 전수. 이상 시 조치: 서열 위반 감지 시 즉시 Pick 정지 + 재피킹 지시, 좌우 반대품 발견 시 격리 후 올바른 부품으로 교체. | 7,8,10 | process_step | Sequenced Supply |
| 금형수정·소재변경·도장조건 변경은 고객승인 이력과 묶는다. 측정 방법: ECR/ECN 시스템 변경 승인 상태 확인, 고객 승인 Letter/Email 아카이브. 관리 주기: 변경 발생 시(Every Change). 이상 시 조치: 고객 미승인 변경 감지 시 해당 부품 생산·출하 Block, 승인 완료 후 샘플 인증(Gold Sample Update) 후 재개. | 1,4,9 | process_step | Change Control |

### H06.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 颜色、纹理和选装错误会在客户产线直接造成缺料或错装，因此必须严格管理规格基准。测量方法：MES Option Code Master与生产指示自动比对，条码扫描器实时验证颜色代码·纹理代码。管理周期：Every Lot全数。异常处理：基准不一致时阻断该Kitting出货，基于客户产线反馈执行Master Data修正流程。 | 1,7,10 | process_step | 选项/颜色追溯 |
| 树脂lot、模具ID和注塑条件是外观/尺寸不良原因分析的核心。测量方法：Resin Lot代码自动扫描，模具温度·压力·速度传感器数据PLC采集，CAE预测与实际Shrinkage对比。管理周期：Every Lot(每注塑Cycle)全数。异常处理：收缩率/翘曲超标时调整模具温度·保压压力，Resin Lot变更时重新执行Mold Flow Simulation+试模验证。 | 2,3,6 | process_step | 模具/材料追溯 |
| 外观、色差、VOC和气味检查应连接标准照片和数值，以减少主观判定。测量方法：Spectrophotometer(ΔE)、Gloss Meter(光泽度GU)、Profile Projector(变形)、VOC Chamber(µg/m³)、Odor Test Panel(1-6级)。管理周期：Every Lot(外观·色差) + 周期性(VOC·Odor 1次/Lot或月)。异常处理：ΔE超标时调整涂装条件(Paint Viscosity·干燥温度)后复测，VOC超标时审查材料/工艺变更。 | 4,6,9 | process_step | 外观质量 |
| JIS/Kitting供给必须同时验证左右件、颜色、选装和顺序。测量方法：DPS(Pick-to-Light)指示灯确认，条码扫描验证拣选部件，基于客户Sequence No的MES匹配。管理周期：Real-time(每Kitting/Picking单位)全数。异常处理：检测顺序违规时立即停止拣选+重新拣配指令，发现左右件颠倒时隔离后更换正确部件。 | 7,8,10 | process_step | 顺序供给 |
| 模具修改、材料变更和涂装条件变更应与客户批准履历绑定。测量方法：ECR/ECN系统变更批准状态确认，客户批准Letter/Email归档。管理周期：变更发生时(Every Change)。异常处理：检测到未获客户批准的变更时，Block该部件生产/出货，批准完成后样件认证(Gold Sample Update)后恢复。 | 1,4,9 | process_step | 变更控制 |

### H06.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Engineering | process |  |  | color_code |
| 2 | Material | process |  |  | resin_lot |
| 3 | Molding | process |  |  | part_lot, mold_id, resin_lot |
| 4 | Surface | process |  |  | part_lot, paint_lot |
| 5 | Assembly | process |  |  | part_lot, assembly_jig_id |
| 6 | Appearance Gate | gate |  | 2,3,4,5 | part_lot, appearance_result, fit_gap_result |
| 7 | Sequencing | process |  |  | part_lot, ship_sequence, color_code |
| 8 | Shipment Prep | process |  |  | ship_sequence |
| 9 | Customer Quality | process |  |  | part_lot, appearance_result |
| 10 | Shipment | process |  |  | part_lot, ship_sequence |

### H06.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Engineering | process |  |  | color_code |
| 2 | Material | process |  |  | resin_lot |
| 3 | Molding | process |  |  | part_lot, mold_id, resin_lot |
| 4 | Surface | process |  |  | part_lot, paint_lot |
| 5 | Assembly | process |  |  | part_lot, assembly_jig_id |
| 6 | Appearance Gate | gate |  | 2,3,4,5 | part_lot, appearance_result, fit_gap_result |
| 7 | Sequencing | process |  |  | part_lot, ship_sequence, color_code |
| 8 | Shipment Prep | process |  |  | ship_sequence |
| 9 | Customer Quality | process |  |  | part_lot, appearance_result |
| 10 | Shipment | process |  |  | part_lot, ship_sequence |

### H06.10 step_expression 연결 설명 (ko/zh)

**ko:** H06(내장·외장·플라스틱)는 Step 1 Engineering에서 색상·옵션 기준이 수립되고, Step 2 Material에서 Resin/Fabric Lot이 투입된 후 Step 3 Molding(사출·발포)에서 부품 형상과 외관이 결정된다. Step 4 Surface에서 도장·크롬·표면처리 후 Step 5 Assembly(봉제·클립 체결)에서 최종 조립된다. Step 6 Appearance Gate가 Step 2~5의 모든 공정 결과(소재 lot부터 외관·색차·Gap/Fit까지)를 gate_for로 검증한다. Pass 시 Step 7 Sequencing에서 고객 서열 단위로 Kitting되며, Step 8 Shipment Prep에서 포장·ASN 검증을 거친다. Step 9 Customer Quality에서 변경·불량 이력이 관리되고, Step 10 Shipment에서 Option/Color Trace 데이터가 최종 확정되어 고객 JIT 라인에 공급된다.

**zh:** H06(内外饰·塑料件)在Step 1 Engineering确立颜色/选装基准，Step 2 Material投入Resin/Fabric Lot后，Step 3 Molding(注塑·发泡)确定部件形状和外观。Step 4 Surface进行涂装/镀铬/表面处理，Step 5 Assembly(缝制·卡扣紧固)完成最终装配。Step 6 Appearance Gate综合验证Step 2~5所有工序结果(材料lot至外观·色差·Gap/Fit)(gate_for)。Pass后Step 7 Sequencing按客户顺序Kitting，Step 8 Shipment Prep经包装/ASN验证。Step 9 Customer Quality管理变更/不良履历，Step 10 Shipment最终确认Option/Color Trace数据，供应客户JIT产线。

### H06.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Mold Setup Check |
| 3 | 2 | Injection Parameter Capture |
| 6 | 1 | Color Difference Check |
| 6 | 2 | Fit/Gap Gauge Check |
| 7 | 1 | JIS Sequence Pick |
| 8 | 1 | ASN Scan |

### H06.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Mold Setup 检查 |
| 3 | 2 | Injection Parameter 采集 |
| 6 | 1 | Color Difference 检查 |
| 6 | 2 | Fit/Gap Gauge 检查 |
| 7 | 1 | JIS Sequence Pick |
| 8 | 1 | ASN 扫描 |

### H06.9 data_capture_points

```yaml
data_capture_points:
  - part_lot
  - resin_lot
  - color_code
  - mold_id
  - paint_lot
  - assembly_jig_id
  - appearance_result
  - fit_gap_result
  - ship_sequence
```


## H07 `tire_rubber` — 타이어·자동차 고무제품 / 轮胎与汽车橡胶制品

```yaml
industry_code: H
subindustry_code: H07
legacy_slug: tire_rubber
label_ko: "타이어·자동차 고무제품"
label_zh: "轮胎与汽车橡胶制品"
label_en: ""
label_ja: ""
q3_cluster: "P4_AUTOMATED_LINE"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "rubber_line_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** tire, hose, belt, anti-vibration/sealing rubber parts  
**产品范围 zh:** 轮胎、胶管、皮带、防振/密封橡胶件

### H07.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 제품규격·배합 Recipe | 타이어/고무부품의 규격(타이어: 205/55R16 등), 배합 Recipe(고무+카본+실리카+첨가제 배합비, ±1% 정밀도), DOT/인증(DOT Code·ECE R30·R117), 성능 요구(마모·견인·회전저항·소음등급)를 확정한다. AI 에이전트가 타이어 패턴 설계를 수분 내 3D 모델 생성, 가상 테스트로 초당 300회 내구성 평가 수행. |
| 2 | 원료·고무·카본·코드 투입 | 천연고무(NR·RSS3/TSR), 합성고무(SBR·BR·IIR), 카본블랙(N200/N300/N600 Series), 실리카(SiO₂·Silane Coupling Agent), Cord(폴리에스터·나일론·레이온·스틸), Bead wire(스틸 와이어 lot·인장강도 N)를 투입한다. 원자재 로트는 Compound Batch와 1:1 매핑되어 전수 추적 가능. |
| 3 | 혼련·Compound Batch | Banbury Mixer 조건(회전자 RPM·Ram Pressure bar·Mix Time s), 배합 순서(Oil+카본블랙+실리카 순서), 온도(배합 온도 프로파일 ℃, Drop Temp 150-170℃), 점도(Mooney Viscosity ML(1+4)100℃), Mooney Scorch(MS t₅@121℃) 결과를 기록한다. AI ML 기반 사이클 타임 18% 감소, 전력 소비 29% 감소 달성. Compound Batch ID는 완제품 추적의 최상위 키. |
| 4 | 압출·캘린더·부품준비 | Tread 압출(Extruder 온도℃·Screw RPM·Profile Gauge), Sidewall 압출, Inner liner 압출(두께 mm·Air Permeability), Cord ply 캘린더(Calender Roll 온도·Roll Gap mm·코드 장력 N/end), Bead(스틸 와이어 권선·Bead Apex) 부품을 준비하고 치수(두께·폭·길이 mm)를 확인한다. AI 비전으로 압출 품질 실시간 모니터링. |
| 5 | Building / 성형 | Tire Building Machine(TBM, 1st Stage/2nd Stage)에서 Component Assembly(Inner Liner→Carcass Ply→Sidewall→Bead→Belt→Tread 순서 적층)를 수행하고 부품 lot과 장비 ID(TBM ID)를 연결한다. 고무부품은 Press/Injection Molding 장비에서 성형. Building 정밀도(Component 위치 mm·접합 품질) AI 검사. |
| 6 | Vulcanization / Curing | Cure Press(Steam/Inert Gas 가열·Bladder 형상), Mold ID(Mold Pattern·Size Code), 온도(Cure Temp 160-185℃)·압력(Cure Pressure 15-25 bar)·시간(Cure Time 10-20 min) 조건과 Cure Curve(가황 곡선, Torque vs Time)를 기록한다. 금형 수명·마모 예측으로 예지보전(Predictive Maintenance) 적용. |
| 7 | X-ray / Uniformity / Balance Gate | X-ray Inspection(Steel Cord 절단·겹침·간격, AI 판정), Uniformity(RFV·Conicity·Lateral Force Variation, ±N 기준), Balance(Static/Dynamic Balance, g·g·cm), 외관검사(Visual: 돌기·함몰·표면 결함)로 합격·등급(A/B/C, 초등급 Premium 선별)을 판정한다. AI 기반 X-ray·초음파 비파괴 검사 판정 시스템 운영. |
| 8 | Marking·DOT·포장 | DOT code(DOT 제조사코드+사이즈코드+위크코드+년도), 라벨(타이어 라벨: 연비/젖은노면/소음등급, EU Regulation 2020/740), 등급(Grade A/B/C), 포장(적층·Separator지), 적재 단위(팔레트당 개수)를 확정한다. DOT Scanner로 코드 정합성 자동 검증. |
| 9 | 불량분석·재분류 | 외관불량(Visual: 에어트랩·미성형), 균일도 불량(Uniformity Outlier), X-ray 불합격(코드 결함·이물)을 원인별로 분류한다. 재분류 가능(Uniformity 재측정·등급 하향)과 폐기/재생(Grinding→Retread) 구분. |
| 10 | 출하·Traceability | 원료 batch부터 Compound Batch→부품 Lot→타이어 Serial·DOT→검사 결과(X-ray/Uniformity/Balance)→출하 lot까지 전(全)사슬 추적을 완료한다. 최소 주문량(MOQ) 71% 감소, 불량률 36% 감소(Lighthouse Factory 수준). |

### H07.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 产品规格与配方Recipe | 确定轮胎/橡胶件的规格(轮胎: 205/55R16等)、配方Recipe(橡胶+炭黑+白炭黑+添加剂配比, ±1%精度)、DOT/认证(DOT Code·ECE R30·R117)、性能要求(耐磨·牵引·滚阻·噪声等级)。AI代理在数分钟内生成轮胎花纹3D模型，虚拟测试每秒300次耐久性评估。 |
| 2 | 原料、橡胶、炭黑与帘线投入 | 投入天然橡胶(NR·RSS3/TSR)、合成橡胶(SBR·BR·IIR)、炭黑(N200/N300/N600 Series)、白炭黑(SiO₂·Silane Coupling Agent)、帘线(聚酯·尼龙·人造丝·钢丝)、Bead wire(钢丝lot·拉伸强度N)。原料lot与Compound Batch 1:1映射，实现全数追溯。 |
| 3 | 混炼与Compound Batch | 记录Banbury Mixer条件(转子RPM·Ram Pressure bar·混炼时间s)、加料顺序(油+炭黑+白炭黑顺序)、温度(混炼温度曲线℃, Drop Temp 150-170℃)、黏度(Mooney Viscosity ML(1+4)100℃)、Mooney Scorch(MS t₅@121℃)结果。基于AI/ML实现Cycle Time降低18%、电力消耗降低29%。Compound Batch ID是成品追踪的最上层Key。 |
| 4 | 挤出、压延与部件准备 | 准备Tread挤出(挤出机温度℃·Screw RPM·Profile Gauge)、Sidewall挤出、Inner liner挤出(厚度mm·Air Permeability)、Cord ply压延(压延辊温度·Roll Gap mm·帘线张力N/根)、Bead(钢丝缠绕·Bead Apex)部件并确认尺寸(厚度·宽度·长度mm)。AI视觉实时监控挤出质量。 |
| 5 | Building / 成型 | 在Tire Building Machine(TBM, 1st Stage/2nd Stage)上执行Component Assembly(Inner Liner→Carcass Ply→Sidewall→Bead→Belt→Tread顺序层叠)，连接部件lot与设备ID(TBM ID)。橡胶件在Press/Injection Molding设备上成型。AI检查Building精度(Component位置mm·粘合质量)。 |
| 6 | Vulcanization / Curing | 记录Cure Press(Steam/Inert Gas加热·Bladder形状)、Mold ID(模具花纹·尺寸代码)、温度(Cure Temp 160-185℃)·压力(Cure Pressure 15-25 bar)·时间(Cure Time 10-20 min)条件和Cure Curve(硫化曲线, Torque vs Time)。通过模具寿命/磨损预测实施Predictive Maintenance。 |
| 7 | X-ray / Uniformity / Balance Gate | 通过X-ray Inspection(钢丝帘线切断·重叠·间距, AI判定)、Uniformity(RFV·Conicity·Lateral Force Variation, ±N基准)、Balance(Static/Dynamic Balance, g·g·cm)、外观检查(Visual: 凸起·凹陷·表面缺陷)判定合格与等级(A/B/C, Premium选别)。运营AI-X射线/超声波无损检测判定系统。 |
| 8 | Marking、DOT与包装 | 确认DOT code(DOT制造商代码+尺寸代码+周代码+年份)、标签(轮胎标签: 燃油效率/湿路制动/噪声等级, EU Regulation 2020/740)、等级(Grade A/B/C)、包装(层叠·隔纸)、装载单位(每托盘数量)。通过DOT扫描器自动验证代码一致性。 |
| 9 | 不良分析与再分类 | 按原因分类外观不良(Visual: 气泡·缺料)、均匀性不良(Uniformity Outlier)、X-ray不合格(帘线缺陷·异物)。区分可重新分类(Uniformity复测·降级)与报废/再生(Grinding→Retread)。 |
| 10 | 出货与Traceability | 完成原料batch→Compound Batch→部件Lot→轮胎Serial·DOT→检查结果(X-ray/Uniformity/Balance)→出货lot全链追溯。实现最小起订量(MOQ)降低71%，不良率降低36%(Lighthouse Factory水平)。 |

### H07.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| Compound batch와 완제품 serial/DOT를 연결해야 원료·배합·품질 문제의 리콜 범위를 산정할 수 있다. 측정 방법: 각 Compound Batch(배치 ID·고유 QR)에 원자재 Lot 매핑, 완제품 타이어 DOT Code에 Compound Batch ID 자동 연결. 관리 주기: Every Lot(배치 단위) 전수. 이상 시 조치: Genealogy 불일치 시 타 완제품 리콜 범위 재산정, 원료 Batch 이력 불명 시 해당 Compound Batch 전수 Hold. | 2,3,10 | process_step | Compound Genealogy |
| 혼련 온도·시간·점도·Mooney는 고무 성능의 핵심 공정조건이므로 batch record로 관리한다. 측정 방법: Banbury Mixer 센서(온도·RPM·Ram Position·전력 소비) 실시간 수집, Mooney Viscometer(Mooney Viscosity·Scorch) 측정. 관리 주기: Every Batch 전수 Mooney 테스트, 공정 파라미터는 실시간 모니터링. 이상 시 조치: Mooney 범위 이탈 시 Batch 격리 + Recipe 조정(RPM·Drop Temp), 연속 2Batch 이상 불량 시 Mixer 설비 점검(회전자·온도센서 캘리브레이션). | 3,6 | process_step | Recipe/Batch Control |
| Curing 조건은 성능·내구와 직접 연결되므로 Press/Mold/Curve 원본 데이터를 저장한다. 측정 방법: Cure Press PLC(온도·압력·시간·Bladder 내압) 실시간 수집, Cure Rheometer(Cure Curve: ML·MH·ts₁·tc₉₀·tc₁₀₀). 관리 주기: Every Lot(타이어 1본 단위) 전수 Cure Curve 저장, 주기적 Rheometer Check(1회/Shift). 이상 시 조치: Cure Curve 이상(저경화·과경화) 감지 시 해당 Lot 안전진단(Retest 또는 폐기), Cure Press 온도 편차 시 금형 가열 시스템 점검. | 6,7 | process_step | Curing Trace |
| X-ray·Uniformity·Balance 검사는 등급·출하판정·재분류의 기준이다. 측정 방법: X-ray(검출기·AI Vision 판정, 360° Scan), Uniformity Tester(RFV·Conicity·Lateral Force, 100% 측정), Balance Tester(Static/Dynamic, 고속 스핀들). 관리 주기: Every Lot 전수(X-ray+Uniformity+Balance) + AI 기반 재판정. 이상 시 조치: Uniformity Outlier 감지 시 재측정 또는 등급 하향(A→B), X-ray FAIL 시 원인별 폐기·재분류, 이상 검사 패턴 반복 시 검사 설비 캘리브레이션. | 7,9,10 | process_step | Final Quality Gate |
| DOT·인증·출하 lot은 지역별 규제와 고객 클레임 대응에 연결한다. 측정 방법: DOT Laser Marking Scanner(Marking 정합성 자동 검증, DOT Code Readability 100%), 라벨(고객 요구 포맷·EU 타이어 라벨). 관리 주기: Every Lot 전수(매 타이어). 이상 시 조치: DOT 인식 불가 시 재마킹 + Laser Head 점검, 인증 미달 사양 출하 감지 시 Lot 전수 Block + 규제대응팀 Escalation. | 1,8,10 | process_step | DOT/Compliance |

### H07.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| 必须连接Compound batch与成品serial/DOT，才能计算原料、配方和质量问题的召回范围。测量方法：各Compound Batch(批次ID·唯一QR)映射原料Lot，成品轮胎DOT Code自动关联Compound Batch ID。管理周期：Every Lot(批次单位)全数。异常处理：Genealogy不一致时重新计算成品召回范围，原料Batch的履历不明时相关Compound Batch全数Hold。 | 2,3,10 | process_step | 胶料谱系 |
| 混炼温度、时间、黏度和Mooney是橡胶性能的关键工艺条件，应作为batch record管理。测量方法：Banbury Mixer传感器(温度·RPM·Ram Position·电力消耗)实时采集，Mooney Viscometer(Mooney Viscosity·Scorch)测量。管理周期：Every Batch全数Mooney测试，工艺参数实时监控。异常处理：Mooney超范围时Batch隔离+Recipe调整(RPM·Drop Temp)，连续2Batch以上不良时检查Mixer设备(转子·温度传感器校准)。 | 3,6 | process_step | Recipe/Batch控制 |
| Curing条件直接影响性能和耐久性，需要保存Press/Mold/Curve原始数据。测量方法：Cure Press PLC(温度·压力·时间·Bladder内压)实时采集，Cure Rheometer(Cure Curve: ML·MH·ts₁·tc₉₀·tc₁₀₀)。管理周期：Every Lot(每轮胎)全数Cure Curve存储，定期Rheometer Check(1次/Shift)。异常处理：检测Cure Curve异常(欠硫/过硫)时相关Lot安全诊断(Retest或报废)，Cure Press温度偏差时模具加热系统点检。 | 6,7 | process_step | 硫化追溯 |
| X-ray、Uniformity、Balance检查是等级、出货判定和再分类的依据。测量方法：X-ray(检测器·AI Vision判定, 360°Scan)、Uniformity Tester(RFV·Conicity·Lateral Force, 100%测量)、Balance Tester(Static/Dynamic, 高速主轴)。管理周期：Every Lot全数(X-ray+Uniformity+Balance) + AI再判定。异常处理：Uniformity离群时复测或降级(A→B)，X-ray FAIL时按原因报废/分类，检测异常模式重复时检查设备校准。 | 7,9,10 | process_step | 最终质量Gate |
| DOT、认证和出货lot需连接区域法规和客户索赔响应。测量方法：DOT Laser Marking Scanner(标记一致性自动验证, DOT Code Readability 100%)、标签(客户要求格式·EU轮胎标签)。管理周期：Every Lot全数(每轮胎)。异常处理：DOT无法识别时重新标记+Laser Head点检，检测到认证未达标规格出货时Lot全数Block+合规团队Escalation。 | 1,8,10 | process_step | DOT/合规 |

### H07.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Recipe | process |  |  | compound_batch |
| 2 | Material | process |  |  | compound_batch, cord_lot, bead_lot |
| 3 | Mixing | batch |  |  | compound_batch |
| 4 | Component Prep | process |  |  | compound_batch, cord_lot |
| 5 | Building | process |  |  | tire_serial, building_machine_id |
| 6 | Curing | process |  |  | tire_serial, cure_press_id |
| 7 | Final Gate | gate |  | 3,4,5,6 | tire_serial, xray_result, uniformity_result |
| 8 | Marking | process |  |  | tire_serial, dot_code |
| 9 | Reclassification | process |  |  | tire_serial, xray_result, uniformity_result |
| 10 | Shipment | process |  |  | tire_serial, dot_code, ship_lot |

### H07.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Recipe | process |  |  | compound_batch |
| 2 | Material | process |  |  | compound_batch, cord_lot, bead_lot |
| 3 | Mixing | batch |  |  | compound_batch |
| 4 | Component Prep | process |  |  | compound_batch, cord_lot |
| 5 | Building | process |  |  | tire_serial, building_machine_id |
| 6 | Curing | process |  |  | tire_serial, cure_press_id |
| 7 | Final Gate | gate |  | 3,4,5,6 | tire_serial, xray_result, uniformity_result |
| 8 | Marking | process |  |  | tire_serial, dot_code |
| 9 | Reclassification | process |  |  | tire_serial, xray_result, uniformity_result |
| 10 | Shipment | process |  |  | tire_serial, dot_code, ship_lot |

### H07.10 step_expression 연결 설명 (ko/zh)

**ko:** H07(타이어·자동차 고무제품)는 Step 1 Recipe에서 배합 Recipe가 확정되고, Step 2 Material에서 원료(NR/SBR/카본블랙/코드)가 투입된 후 Step 3 Mixing에서 Banbury Mixer로 Compound Batch가 생성된다(이 시점이 최상위 Trace Key). Step 4 Component Prep에서 Tread·Sidewall·Inner liner 등 부품이 압출·캘린더 가공된다. Step 5 Building에서 TBM으로 타이어가 성형되고, Step 6 Curing에서 Cure Press에서 가황 성형된다. Step 7 Final Gate(종합 Gate)가 Step 3~6의 Compound·부품·Building·Curing 전(全)공정 결과를 gate_for로 검증한다. Pass 시 Step 8 Marking에서 DOT Code가 마킹되고, Step 9 Reclassification에서 검사 결과 기반 재분류(등급 조정·폐기)가 이루어진다. Step 10 Shipment에서 원료 Batch부터 완제품 DOT까지 전(全)사슬 추적 데이터가 완성되어 출하된다.

**zh:** H07(轮胎·橡胶件)在Step 1 Recipe确定配方Recipe后，Step 2 Material投入原料(NR/SBR/炭黑/帘线)，Step 3 Mixing在Banbury Mixer中生成Compound Batch(此为最上层Trace Key)。Step 4 Component Prep经挤出/压延加工Tread·Sidewall·Inner liner等部件。Step 5 Building在TBM上成型轮胎，Step 6 Curing在Cure Press中硫化成型。Step 7 Final Gate(综合Gate)验证Step 3~6的Compound·部件·Building·Curing全工序结果(gate_for)。Pass后Step 8 Marking标记DOT Code，Step 9 Reclassification根据检查结果重新分类(等级调整·报废)。Step 10 Shipment完成原料Batch至成品DOT的全链追溯数据后出货。

### H07.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Mixer Recipe Load |
| 3 | 2 | Mooney Viscosity Test |
| 6 | 1 | Cure Cycle Capture |
| 7 | 1 | X-ray Inspection |
| 7 | 2 | Uniformity Test |
| 8 | 1 | DOT Marking Scan |

### H07.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Mixer Recipe 载入 |
| 3 | 2 | Mooney Viscosity 测试 |
| 6 | 1 | Cure Cycle 采集 |
| 7 | 1 | X-ray 检查 |
| 7 | 2 | Uniformity 测试 |
| 8 | 1 | DOT Marking 扫描 |

### H07.9 data_capture_points

```yaml
data_capture_points:
  - tire_serial
  - compound_batch
  - cord_lot
  - bead_lot
  - building_machine_id
  - cure_press_id
  - xray_result
  - uniformity_result
  - dot_code
  - ship_lot
```


## H08 `tier1_tier2_suppliers` — Tier 1·2 복합 자동차부품 / Tier1/2综合汽车零部件

```yaml
industry_code: H
subindustry_code: H08
legacy_slug: tier1_tier2_suppliers
label_ko: "Tier 1·2 복합 자동차부품"
label_zh: "Tier1/2综合汽车零部件"
label_en: ""
label_ja: ""
q3_cluster: "P3_LABOR_ASSEMBLY"
routing_family: "셀+라인 혼합 / 单元+产线混合"
flow_preset_candidate: "tier_supplier_mixed_v1"
expression_tier: "v0.3_pflow_ready"
source_policy: "ko/zh only; en/ja sections not authored"
```

**제품 범위 ko:** customer drawing parts, sub-system assemblies, multi-process metal/plastic parts  
**产品范围 zh:** 客户图纸件、子系统总成、多工序金属/塑料件

### H08.1 process_steps_detail_ko

| # | step | note |
| --- | --- | --- |
| 1 | 고객도면·수주·변경 기준 | Tier 고객 도면(GD&T·공차·소재규격), Revision(도면 Rev 번호), APQP/PPAP 요구(PSW·IMDS·CAMDS), 수주(EDI 850/862)·납기(EDI 856 ASN)·변경점(ECR/ECN)을 확정한다. ISA-95/RAMI 4.0 참조 아키텍처 기반 IT-OT 통합. |
| 2 | 자재·부품·외주 입고 | 금속(코일·Bar·Plate·주조품 Lot·인장강도·경도 HRC), 수지(Pellet·Resin Grade·MFI), 전자(PCB·IC·Connector), 표면처리 외주품(도금·열처리·Anodizing 두께 μm) lot과 검사결과(수입검사: AI Vision·CMM·경도계)를 입고 이력으로 구성한다. 수입검사 IQC 기준(AQL=0.65, Level II). |
| 3 | 공정라우팅·작업지시 | 고객품번(customer_part_no)별 가공(CNC·MCT), 성형(프레스·사출), 용접(로봇용접·TIG/MIG), 조립(압입·나사체결), 검사(CMM·비전·기능검사) route(Route ID·Operation Sequence)와 작업조건(C/T sec·설비 ID·금형 ID·공구 ID)을 확정한다. Mixed Process Loop로 다품종 라우팅 관리. |
| 4 | 가공·성형·표면처리 | 다품종 공정에서 설비(ID·Spindle RPM·Feed Rate·Cutting Depth), 금형(온도·압력·사이클 시간), 공구(Tool ID·Tool Life Count), 조건(온도℃·압력bar·시간s), 중간검사(In-Process Gauge·SPC) 결과를 기록한다. AI 기반 이상 탐지로 OEE 8-10% 향상. 클라우드 시계열 DB(Time Series Database)에 제조 Raw Data 저장. |
| 5 | 서브조립·기능조립 | 고객도면 기준으로 부품 조합(부품 A+B+C Assembly Tree), 체결(Torque N·m·Angle°), 접착(접착제 Type·도포량g·경화시간 min), 전기(Connector Insertion·연속성 Test)·기계(회전·슬라이딩 마찰 Test) 기능 조립을 수행한다. 조립 Jig ID와 모든 부품 Serial이 Mapping. |
| 6 | 검사·SPC·Gate | 치수(CMM·Gauge·GO/NO-GO), 기능(Leak Test·Torque Test·Push/Pull Test), 외관(AI Vision·색차계·조도계), 공정능력(Cp/Cpk≥1.67), 고객 특성치(Customer Specific Requirement·CC/SC 항목)를 Gate로 판정한다. 불합격 시 Mixed Process Loop로 Step 3/4/5 피드백. |
| 7 | 포장·라벨·고객 ASN | 고객 라벨(포맷·UDI·GTIN·LOT No·D/C), ASN(EDI 856·납품 예정 통지), 납품 lot, 포장사양(Returnable·Disposable·개수), 서열/납기 정보를 바코드 스캔 자동 검증. |
| 8 | 불량·8D·고객클레임 | 불량격리(Q-zone·물리적 Lock-out + 시스템 Block), 원인분석(5-Why·Fishbone), 8D 보고서(팀구성→문제정의→근본원인→시정조치→예방조치→인정→완료), 특채(Concession/Deviation)·폐기·재작업 이력을 관리한다. |
| 9 | ECR/ECN·PPAP 변경관리 | 도면변경(ECR→ECN→Drawing Update Cycle), 공정변경(Process Change Notice·PCN), 소재변경(Material Change Request·MCR), 고객승인 상태(PSW 승인·Run@Rate 완료)를 관리한다. 변경 이력은 출하 Lot과 연동. |
| 10 | 출하·Lot/Serial Trace | Lot/Serial별 자재(금속 Lot·수지 Lot·외주품 Lot), 공정조건(가공 파라미터·금형 ID·공구 ID), 검사성적(치수·기능·외관·고객 특성치), 고객 납품 이력(납기·수량·ASN)을 확정한다. ERP-MES-PLM-SRM-WMS 통합으로 고객 감사 대응. |

### H08.2 process_steps_detail_zh

| # | step | note |
| --- | --- | --- |
| 1 | 客户图纸、订单与变更基准 | 确定Tier客户图纸(GD&T·公差·材料规格)、Revision(图纸Rev编号)、APQP/PPAP要求(PSW·IMDS·CAMDS)、订单(EDI 850/862)·交期(EDI 856 ASN)·变更点(ECR/ECN)。基于ISA-95/RAMI 4.0参考架构实现IT-OT集成。 |
| 2 | 材料、部件与外协入库 | 将金属(卷料·棒料·板材·铸件Lot·拉伸强度·硬度HRC)、塑料(Pellet·Resin Grade·MFI)、电子(PCB·IC·Connector)、表面处理外协品(电镀·热处理·Anodizing厚度μm)lot和检查结果(来料检验: AI Vision·CMM·硬度计)形成入库履历。来料检验IQC基准(AQL=0.65, Level II)。 |
| 3 | 工艺路线与作业指示 | 按客户品号(customer_part_no)确定加工(CNC·MCT)、成型(冲压·注塑)、焊接(机器人焊接·TIG/MIG)、装配(压装·螺丝紧固)、检查(CMM·视觉·功能测试)route(Route ID·Operation Sequence)和作业条件(C/T sec·设备ID·模具ID·刀具ID)。通过Mixed Process Loop管理多品种路线。 |
| 4 | 加工、成型与表面处理 | 在多品种工序中记录设备(ID·主轴转速·进给率·切削深度)、模具(温度·压力·周期时间)、刀具(Tool ID·Tool Life Count)、条件(温度℃·压力bar·时间s)、中间检查(In-Process Gauge·SPC)结果。AI异常检测实现OEE提升8-10%。制造原始数据存储于云端时序数据库(Time Series DB)。 |
| 5 | 子装配与功能装配 | 按客户图纸执行部件组合(部件A+B+C Assembly Tree)、紧固(Torque N·m·Angle°)、胶粘(胶粘剂Type·涂布量g·固化时间min)、电气(Connector Insertion·连续性Test)·机械(旋转·滑动摩擦Test)功能装配。装配Jig ID与所有部件Serial映射。 |
| 6 | 检查、SPC与Gate | 以尺寸(CMM·Gauge·GO/NO-GO)、功能(Leak Test·Torque Test·Push/Pull Test)、外观(AI Vision·色差计·粗糙度计)、过程能力(Cp/Cpk≥1.67)、客户特殊特性(Customer Specific Requirement·CC/SC项目)判定Gate。不合格时通过Mixed Process Loop反馈Step 3/4/5。 |
| 7 | 包装、标签与客户ASN | 验证客户标签(格式·UDI·GTIN·LOT No·D/C)、ASN(EDI 856·交货预告通知)、交货lot、包装规格(Returnable·Disposable·数量)、顺序/交期信息(条码扫描自动验证)。 |
| 8 | 不良、8D与客户投诉 | 管理不良隔离(Q-zone·物理Lock-out + 系统Block)、原因分析(5-Why·Fishbone)、8D报告(组建团队→问题定义→根本原因→纠正措施→预防措施→认可→完成)、让步接收(Concession/Deviation)·报废·返工履历。 |
| 9 | ECR/ECN与PPAP变更管理 | 管理图纸变更(ECR→ECN→Drawing Update Cycle)、工艺变更(Process Change Notice·PCN)、材料变更(Material Change Request·MCR)、客户批准状态(PSW批准·Run@Rate完成)。变更履历联动出货Lot。 |
| 10 | 出货与Lot/Serial Trace | 确认Lot/Serial级材料(金属Lot·树脂Lot·外协品Lot)、工艺条件(加工参数·模具ID·刀具ID)、检查成绩(尺寸·功能·外观·客户特殊特性)、客户交付履历(交期·数量·ASN)。通过ERP-MES-PLM-SRM-WMS集成应对客户审核。 |

### H08.3 control_points_detail_ko

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| Tier 부품사는 고객도면 Revision과 공정조건이 뒤섞이기 쉬우므로 도면-라우팅-검사계획을 잠금 관리한다. 측정 방법: PLM/ECN 시스템에서 Drawing Rev 상태 조회→MES Route Master Lock Status와 대조, Revision 변경 시 자동 Route 검증 워크플로우 Trigger. 관리 주기: 변경 발생 시(Every Change) + Lot 생성 시 검증. 이상 시 조치: 구 Rev 도면으로 Route가 설정된 Lot 출하 Block, Revision 불일치 발견 시 해당 Lot 생산 중단 및 라우팅 재설정. | 1,3,9 | process_step | Drawing/Route Control |
| 고객 특성치와 SPC 결과는 출하승인과 고객 클레임 대응의 핵심 증거다. 측정 방법: CC/SC 항목별 측정 장비(CMM·경도계·인장시험기·표면조도계), SPC 차트(X-bar·R·P-Chart·Cpk Trend) 자동 생성. 관리 주기: Every Lot 전수(CC/SC 항목) + 주기적 SPC 분석(Shift/일간). 이상 시 조치: CC/SC 항목 불량 발생 시 해당 Lot 전수 Hold + 8D 개시, Cpk<1.67 감지 시 공정 개선 활동 Trigger. | 4,6,10 | process_step | SPC/Customer Characteristics |
| 외주·내작 공정이 섞이면 lot genealogy가 끊기기 쉬우므로 입고·가공·조립·출하를 한 체계로 묶는다. 측정 방법: 외주 업체 Lot 번호와 내부 Lot 번호 간 Cross-Reference 맵(MES→외주사 포털 연동), 부모-자식 Assembly Tree 자동 구축. 관리 주기: Every Lot(외주 입고부터 출하까지) 전수 Genealogy 구축. 이상 시 조치: Genealogy 불연속(갭) 발견 시 해당 Lot 출하 Block, 외주사 데이터 누락 시 재요청 또는 현장 Audit. | 2,4,5,10 | process_step | Lot Genealogy |
| 8D·특채·재작업 이력은 동일 lot 출하 금지 또는 제한출하 판단에 반영한다. 측정 방법: MES 불량 코드 등록(원인·조치·비용), 8D Report 시스템 템플릿, MRB 판정(GO/NO-GO·Conditional Release). 관리 주기: Every Lot(불량 발생 건별) 전수. 이상 시 조치: 8D 미완료 Lot 출하 Block, 특채(Concession)는 고객 승인 문서 첨부 필수, 동일 Lot 내 불량 반복 시 Lot 전수 Hold + 전수 재검. | 6,8,10 | process_step | 8D/MRB |
| APQP/PPAP와 ECR/ECN은 납품 고객별 승인 상태를 기준으로 운영한다. 측정 방법: APQP Phase Gate(Plan→Design→Process→Product→Launch) 진행률 추적, PPAP PSW(Part Submission Warrant) 승인 상태 확인, ECR/ECN Approval Workflow. 관리 주기: APQP 신규 프로젝트 시 + 변경 발생 시(Every ECR/ECN). 이상 시 조치: PPAP 미승인 상태에서 양산 진행 감지 시 생산 중단, ECR/ECN 미반영 Route 발견 시 Route Lock + 변경 반영 후 재검증. | 1,9,10 | process_step | APQP/PPAP |

### H08.4 control_points_detail_zh

| text | step_refs | scope | category |
| --- | --- | --- | --- |
| Tier供应商容易混用客户图纸Revision和工艺条件，因此需锁定管理图纸、路线和检查计划。测量方法：PLM/ECN系统查询Drawing Rev状态→与MES Route Master Lock Status对比，Revision变更时自动触发Route验证工作流。管理周期：变更发生时(Every Change) + Lot生成时验证。异常处理：按旧Rev图纸设置Route的Lot出货Block，发现Revision不一致时该Lot停产并重新设置路线。 | 1,3,9 | process_step | 图纸/路线控制 |
| 客户特殊特性和SPC结果是出货批准与客户索赔响应的核心证据。测量方法：CC/SC项目专用测量设备(CMM·硬度计·拉伸试验机·表面粗糙度计)，SPC图表(X-bar·R·P-Chart·Cpk Trend)自动生成。管理周期：Every Lot全数(CC/SC项目) + 周期性SPC分析(Shift/日)。异常处理：CC/SC项目不良发生时该Lot全数Hold+启动8D，检测到Cpk<1.67时触发工艺改善活动。 | 4,6,10 | process_step | SPC/客户特殊特性 |
| 外协和内制工序混合时lot genealogy容易中断，因此需将入库、加工、装配、出货统一管理。测量方法：外协厂商Lot号与内部Lot号交叉引用映射(MES→外协厂门户联动)，自动构建父子Assembly Tree。管理周期：Every Lot(从外协入库到出货)全数构建Genealogy。异常处理：发现Genealogy不连续(间隙)时Block该Lot出货，外协厂数据缺失时要求重新提交或现场Audit。 | 2,4,5,10 | process_step | Lot谱系 |
| 8D、让步接收和返工履历应反映到同lot禁止出货或限制出货判断。测量方法：MES不良代码登记(原因·措施·成本)、8D Report系统模板、MRB判定(GO/NO-GO·Conditional Release)。管理周期：Every Lot(不良发生项)全数。异常处理：8D未完成Lot出货Block，让步接收(Concession)必须附带客户批准文件，同Lot内不良重复时Lot全数Hold+全数复检。 | 6,8,10 | process_step | 8D/MRB |
| APQP/PPAP与ECR/ECN应按交付客户的批准状态运营。测量方法：APQP Phase Gate(Plan→Design→Process→Product→Launch)进度追踪，PPAP PSW(Part Submission Warrant)批准状态确认，ECR/ECN Approval工作流。管理周期：APQP新项目时+变更发生时(Every ECR/ECN)。异常处理：检测到PPAP未批准状态下量产时停止生产，发现ECR/ECN未反映的Route时Route Lock+变更反映后复验。 | 1,9,10 | process_step | APQP/PPAP |

### H08.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Customer Engineering | process |  |  | customer_part_no, drawing_rev, change_notice_id |
| 2 | Inbound | process |  |  | lot_no |
| 3 | Routing | process |  |  | customer_part_no, process_route_id |
| 4 | Processing | process | Mixed Process Loop |  | lot_no, tool_id, process_route_id |
| 5 | Assembly | process |  |  | serial_no, lot_no |
| 6 | Quality Gate | gate |  | 2,3,4,5 | lot_no, serial_no, inspection_result |
| 7 | Logistics | process |  |  | ship_lot, customer_part_no |
| 8 | Customer Quality | process |  |  | lot_no, inspection_result |
| 9 | Change Control | process |  |  | drawing_rev, change_notice_id |
| 10 | Shipment | process |  |  | ship_lot, lot_no, serial_no |

### H08.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
| --- | --- | --- | --- | --- | --- |
| 1 | Customer Engineering | process |  |  | customer_part_no, drawing_rev, change_notice_id |
| 2 | Inbound | process |  |  | lot_no |
| 3 | Routing | process |  |  | customer_part_no, process_route_id |
| 4 | Processing | process | Mixed Process Loop |  | lot_no, tool_id, process_route_id |
| 5 | Assembly | process |  |  | serial_no, lot_no |
| 6 | Quality Gate | gate |  | 2,3,4,5 | lot_no, serial_no, inspection_result |
| 7 | Logistics | process |  |  | ship_lot, customer_part_no |
| 8 | Customer Quality | process |  |  | lot_no, inspection_result |
| 9 | Change Control | process |  |  | drawing_rev, change_notice_id |
| 10 | Shipment | process |  |  | ship_lot, lot_no, serial_no |

### H08.10 step_expression 연결 설명 (ko/zh)

**ko:** H08(Tier 1·2 복합 자동차부품)는 Step 1 Customer Engineering에서 고객도면 Revision과 수주 조건이 확정된 후, Step 2 Inbound에서 외주품·자재 Lot이 수입검사(IQC)를 통해 입고된다. Step 3 Routing에서 고객품번별 가공·성형·용접·조립·검사 Route가 Mixed Process Loop로 설정된다. Step 4 Processing에서 다품종 공정(가공→성형→표면처리 등)이 Mixed Process Loop로 반복되어 기록되고, Step 5 Assembly에서 서브조립 및 기능조립이 완료된다. Step 6 Quality Gate가 Step 2~5의 입고→Routing→가공→조립 결과를 gate_for로 종합 검증하여 출하 가능 여부를 판정한다. 불합격 시 Mixed Process Loop로 Step 3/4/5 피드백. Step 7 Logistics에서 포장·라벨·ASN이 검증되고, Step 8 Customer Quality에서 8D·클레임 이력이 추적된다. Step 9 Change Control에서 ECR/ECN이 관리되고, Step 10 Shipment에서 Lot/Serial Trace가 완성되어 ERP-MES-PLM-SRM-WMS 통합 데이터로 고객에게 출하된다.

**zh:** H08(Tier1/2综合汽车零部件)在Step 1 Customer Engineering确定客户图纸Revision和订单条件后，Step 2 Inbound通过来料检验(IQC)入库外协品/材料Lot。Step 3 Routing通过Mixed Process Loop设置客户品号对应加工/成型/焊接/装配/检查路线。Step 4 Processing以Mixed Process Loop重复记录多品种工序(加工→成型→表面处理等)，Step 5 Assembly完成子装配和功能装配。Step 6 Quality Gate综合验证Step 2~5的入库→路线→加工→装配结果(gate_for)判定出货条件。不合格时通过Mixed Process Loop反馈Step 3/4/5。Step 7 Logistics验证包装/标签/ASN，Step 8 Customer Quality追踪8D/索赔履历。Step 9 Change Control管理ECR/ECN，Step 10 Shipment完成Lot/Serial Trace，通过ERP-MES-PLM-SRM-WMS整合数据向客户出货。

### H08.7 operations_ko

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Route Revision Load |
| 4 | 1 | Tool/Fixture Verification |
| 6 | 1 | Customer Characteristic Inspection |
| 7 | 1 | Customer Label Print |
| 8 | 1 | 8D Root Cause Registration |
| 9 | 1 | PPAP Approval Check |

### H08.8 operations_zh

| step_ref | seq | name |
| --- | --- | --- |
| 3 | 1 | Route Revision 载入 |
| 4 | 1 | Tool/Fixture 验证 |
| 6 | 1 | Customer Characteristic 检查 |
| 7 | 1 | Customer Label 打印 |
| 8 | 1 | 8D Root Cause 登记 |
| 9 | 1 | PPAP 批准 检查 |

### H08.9 data_capture_points

```yaml
data_capture_points:
  - customer_part_no
  - lot_no
  - serial_no
  - drawing_rev
  - tool_id
  - process_route_id
  - inspection_result
  - change_notice_id
  - ship_lot
```

---

## 9. self-check

```
[x] H01~H08 전수, slug당 §N.1~§N.10 섹션 완비 (N.10=step_expression 연결 설명)
[x] control_points_detail에 category 열 전건 작성
[x] step_expression ko/zh 행 수 = process_steps 행 수
[x] role=gate 행에 gate_for 작성
[x] trace_keys ⊆ data_capture_points
[x] ko/zh process_steps 행 수 동일
[x] ko/zh step_expression #, role, gate_for, trace_keys 동일
[x] en/ja 공정·관리점 섹션 없음
[x] process_steps_detail 각 step note: 설비/장비명, 관리 파라미터(온도·압력·시간·속도), Lot/Batch/Serial 추적 포인트, Gate/Inspection/Hold 포인트, 대표 제품 사례 명시
[x] control_points_detail 각 항목: 측정 장비/방법, 관리 주기(Real-time/Every Lot/Every Batch/주기적), 이상 시 조치 프로세스 명시
[x] step_expression 각 slug: 10단계 간 공정 연결성 자연스럽게 설명 (N.10 신규 섹션)
[x] 2024-2026 자동차·모빌리티 제조 트렌드 반영 (AI 에이전트, 디지털 트윈, Giga Casting, Hairpin 모터, 스마트 아일랜드 등)
```

## 10. JSON 반영 전 주의

- 본 문서는 MD 정본 후보이며, `process_detail_v1.json`에 바로 수기 반영하지 않는다.
- 변환 스크립트가 v0.3 섹션을 파싱하도록 준비된 후 dry-run 검증을 먼저 수행한다.
- H산업은 고객별 명칭과 현장 routing 편차가 크므로 실제 고객 적용 시 H01/H08은 `customer_part_no`, `VIN`, `sequence_no`, `drawing_rev` 키를 우선 확인한다.
