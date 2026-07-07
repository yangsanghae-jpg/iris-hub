# A산업 A1 Ch3 공정분석 런타임형 데이터팩 v0.3
## 프로젝트·특수 제조 / ETO·ATO — 한국어·중국어

> 작성 기준: 2026-07-06  
> 대상: A01~A08  
> 목적: `process_detail_v1.json` 반영 전 검토용 MD 데이터팩  
> 적용 기준: `A1_CH3_B_process_detail_datapack_refactor_instruction_2026-07-06.md`의 v0.3 authoring 규격 준용  
> 언어: 한국어 / 중국어만 작성. `label_en`, `label_ja`는 공백. en/ja 공정·관리점 섹션 작성 금지.  
> 작업 범위: MD 데이터팩 작성만. JSON·코드·변환 스크립트 수정 없음.

---

## 0. 작성 원칙

```yaml
industry_code: A
industry_name_ko: 프로젝트·특수 제조
industry_name_zh: 项目型·特殊制造
expression_tier: P2_PROJECT_WBS
runtime_target:
  file: server/data/step3/process_detail_v1.json
  builder: server/assemble/process_analysis.py
  screen: A1 Step5 Ch3 Process Analysis
language_policy:
  ko: true
  zh: true
  en: ""
  ja: ""
```

### 0.1 §0 오기 수정

- `control_points_ko/zh`는 본 MD에서 별도 작성하지 않는다.
- 필요한 경우 변환 단계에서 `control_points_detail_ko/zh[].text`를 flat list로 자동 생성한다.
- Ch3 pflow가 소비하는 `module`, `role`, `gate_for`, `loop_hint`, `trace_keys`, `operations`, `category`를 본 MD에 명시한다.

### 0.2 A산업 공통 표현 규칙

A산업은 모두 프로젝트형 제조로 묶을 수 있지만, 실제 공정 표현은 세부산업별로 달라야 한다.

| 코드 | 세부산업 | legacy_slug | 핵심 표현 단위 |
|---|---|---|---|
| A01 | 플랜트·EPC 제작 | `plant_epc` | Engineering / Procurement / Fabrication / Site / Commissioning |
| A02 | 주문형 산업기계·중장비 | `heavy_equipment` | Part Fabrication / Structural Assembly / Hydraulic·Electrical / FAT |
| A03 | 반도체·디스플레이 제조장비 | `semi_equipment` | Frame / Chamber / Vacuum·Gas / Motion / Electrical / SW / FAT·SAT |
| A04 | 배터리·태양광 제조장비 | `battery_equipment` | Roll-to-Roll / Coating / Dry Room / Formation / PV Module Equipment |
| A05 | 조선·해양플랜트 | `shipbuilding` | Steel Preparation / Block / Dock / Outfitting / Paint / Sea Trial |
| A06 | 항공우주·방산 시스템 | `aerospace_equipment` | Part / Special Process / Sub Assembly / Final Assembly / FAI / Qualification |
| A07 | 금형·치공구·전용기 | `mold_tooling_dedicated_machine` | Mold Design / Machining / EDM / Assembly / Tryout / Correction |
| A08 | 대형 구조물·특수 제작 | `large_structure_fabrication` | Plate·Beam / Fit-up / Welding / NDT / Coating / Site Erection |

### 0.3 산업 현황 반영 메모

```yaml
trend_reflection_ko:
  A01: 모듈화·프리패브, BIM·디지털 트윈, AI·로봇·현장 진도 가시화
  A02: ETO/CTO 디지털 스레드, 고객 구성정보-EBOM-MBOM-작업지시 연결
  A03: AI/HPC 투자에 따른 반도체 장비 수요, 진공·가스·Particle·Recipe·SECS/GEM·SAT 관리
  A04: 배터리 전극 제조 실시간 제어, 건식 전극, 고속 코팅, 화성·검사 장비
  A05: Shipyard 4.0, Pipe Spool 추적, Block 물류, 설계-작업장 Digital Thread
  A06: MBD/MBSE, FAI, Qualification, Digital Thread, 보안·수출통제 추적
  A07: 금형 자동화, 적층제조·Conformal Cooling, Tryout 반복 저감, AI 품질예측
  A08: 용접 자동화, AI 품질검사, 소재 Heat 추적, Green Steel·탄소 추적
trend_reflection_zh:
  A01: 模块化/预制化、BIM/数字孪生、AI/机器人、现场进度可视化
  A02: ETO/CTO数字线程，客户配置-EBOM-MBOM-作业指导连接
  A03: AI/HPC投资带动半导体设备需求，真空/气体/Particle/Recipe/SECS-GEM/SAT管理
  A04: 电池电极制造实时控制、干法电极、高速涂布、化成与检测设备
  A05: Shipyard 4.0、Pipe Spool追踪、Block物流、设计到车间执行的数字线程
  A06: MBD/MBSE、FAI、Qualification、数字线程、安全与出口管制追踪
  A07: 模具自动化、增材制造/随形冷却、减少试模迭代、AI质量预测
  A08: 焊接自动化、AI质量检测、材料Heat追踪、绿色钢材与碳追踪
```

---


# 1. A01 — 플랜트·EPC 제작

```yaml
subindustry_code: A01
legacy_slug: plant_epc
label_ko: 플랜트·EPC 제작
label_zh: 工厂工程·EPC制造
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  플랜트·EPC는 설계, 조달, 모듈·스키드 제작, 현장 설치, Commissioning이 프로젝트/WBS 기준으로 연결되는 구조다. Ch3는 단일 생산라인보다 WBS·Module·Spool·Site 단계의 흐름을 보여줘야 한다.
routing_description_zh: >
  EPC制造以项目/WBS为主线，连接工程设计、采购、模块/Skid预制、现场安装和调试交付。Ch3应表达WBS、Module、Spool和现场阶段，而不是单一生产线。
```

## 1.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 계약·요구사항 기준선 | 계약범위, 성능조건, 규제·안전조건, 인수기준과 프로젝트 기준선을 확정한다. |
| 2 | 기본설계 / FEED | 공정흐름, 용량, Layout, 주요 장비, Utility, Interface와 설계 기준을 정의한다. |
| 3 | 상세설계 / 3D Model / IFC | P&ID, 3D Model, ISO Drawing, 구조·배관·전장 상세도와 IFC 도면을 Release한다. |
| 4 | 장납기품·주요 장비 조달 | 압력용기, 펌프, 밸브, 전장품, 계장품, 특수소재와 외주품의 발주·승인·납기를 관리한다. |
| 5 | 자재 입고·검사·Project Kitting | MTC/CoC, Heat No., Lot, 보존상태를 확인하고 WBS·Module 기준으로 자재를 Kit 구성한다. |
| 6 | 배관 Spool·철골·Skid 제작 | 절단, 가공, Fit-up, 용접, 치수검사, Spool/Skid 단위 제작을 수행한다. |
| 7 | Shop NDT·압력·누설 시험 | RT/UT/PT/MT, Hydro/Pneumatic Test, Leak Test와 NCR·Repair를 관리한다. |
| 8 | Module Assembly / Pre-commissioning | Skid, Package, Module을 조립하고 배관·전장·계장·Utility 연결 상태를 사전 점검한다. |
| 9 | 표면처리·도장·보존 | Blast, Coating, DFT, Curing, Preservation, Packing 기준을 적용한다. |
| 10 | 출하·운송·현장 반입 | Module 분해/보존/포장, 운송허가, 현장 반입, Lifting Plan과 보관상태를 관리한다. |
| 11 | 현장 설치·Tie-in | Foundation, Erection, Tie-in, Alignment, Field Welding과 현장 Interface를 연결한다. |
| 12 | Commissioning / SAT / 인계 | Loop Check, Cold/Hot Commissioning, SAT, Punch Close, As-built 문서와 교육을 완료한다. |

## 1.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 合同·需求基线 | 确认合同范围、性能条件、法规/安全条件、验收标准和项目基线。 |
| 2 | 基础设计 / FEED | 定义工艺流程、产能、Layout、主要设备、Utility、接口和设计基准。 |
| 3 | 详细设计 / 3D Model / IFC | 发布P&ID、3D模型、ISO图、结构/管道/电气仪表详细图和IFC图纸。 |
| 4 | 长周期物料·主要设备采购 | 管理压力容器、泵、阀门、电气仪表、特殊材料和外协件的采购、审批和交期。 |
| 5 | 材料入库·检验·项目齐套 | 确认MTC/CoC、Heat No.、Lot、保存状态，并按WBS/Module进行齐套。 |
| 6 | 管道Spool·钢结构·Skid制造 | 执行切割、加工、组对、焊接、尺寸检查和Spool/Skid制造。 |
| 7 | 车间NDT·压力·泄漏试验 | 管理RT/UT/PT/MT、Hydro/Pneumatic Test、Leak Test以及NCR/Repair。 |
| 8 | 模块组装 / 预调试 | 组装Skid、Package、Module，并预检查管道、电气、仪表、Utility连接状态。 |
| 9 | 表面处理·涂装·保存 | 执行喷砂、涂装、DFT、固化、保存和包装标准。 |
| 10 | 出货·运输·现场到货 | 管理模块拆分/保存/包装、运输许可、现场到货、吊装计划和保管状态。 |
| 11 | 现场安装·Tie-in | 连接Foundation、Erection、Tie-in、Alignment、现场焊接和现场接口。 |
| 12 | Commissioning / SAT / 交付 | 完成Loop Check、Cold/Hot Commissioning、SAT、Punch关闭、As-built文件和培训。 |

## 1.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항·설계 기준선 | 계약 요구사항, 설계 기준, 성능보증 조건과 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 설계 형상관리 | P&ID, 3D Model, ISO Drawing, MTO, WBS와 Module 번호 간 형상 일치를 관리한다. | 2,3 | process_step |
| 3 | 조달·Vendor 관리 | 장납기 장비와 핵심 자재의 Vendor Document, ITP, FAT, 납기 리스크를 추적한다. | 4 | process_step |
| 4 | 자재 추적·Kitting | MTC/CoC, Heat No., 자재 보존상태와 WBS별 Kitting 완전성을 확인한다. | 5 | process_step |
| 5 | 제작 품질 | Spool, Skid, Module 단위의 Fit-up, Welding, 치수검사, NDT 결과를 연결한다. | 6,7 | process_step |
| 6 | 시험·NCR | Hydro Test, Leak Test, NCR, Repair, Re-test 이력을 Module/Line No. 기준으로 추적한다. | 7 | process_step |
| 7 | 출하·보존 | 도장 사양, DFT, 환경조건, 보존상태와 출하 포장 단위의 일치 여부를 관리한다. | 9,10 | process_step |
| 8 | 현장·인계 | 현장 설치, Tie-in, Punch, Redline, As-built 변경을 최종 인계 문서와 연결한다. | 11,12 | process_step |
| 9 | 프로젝트 보안 | 프로젝트별 고객 IP, 설계자료, 공급사 문서와 현장 접근권한을 구분 관리한다. |  | industry |

## 1.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求·设计基线 | 合同需求、设计基准、性能保证条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 设计构型管理 | 管理P&ID、3D Model、ISO图、MTO、WBS与Module编号之间的构型一致性。 | 2,3 | process_step |
| 3 | 采购·Vendor管理 | 跟踪长周期设备和关键材料的Vendor Document、ITP、FAT和交期风险。 | 4 | process_step |
| 4 | 材料追踪·齐套 | 确认MTC/CoC、Heat No.、材料保存状态和按WBS齐套的完整性。 | 5 | process_step |
| 5 | 制造质量 | 连接Spool、Skid、Module单位的组对、焊接、尺寸检查和NDT结果。 | 6,7 | process_step |
| 6 | 测试·NCR | 按Module/Line No.追踪Hydro Test、Leak Test、NCR、Repair和Re-test履历。 | 7 | process_step |
| 7 | 出货·保存 | 管理涂装规格、DFT、环境条件、保存状态和出货包装单位的一致性。 | 9,10 | process_step |
| 8 | 现场·交付 | 将现场安装、Tie-in、Punch、Redline、As-built变更连接到最终交付文件。 | 11,12 | process_step |
| 9 | 项目安全 | 按项目区分管理客户IP、设计资料、供应商文件和现场访问权限。 |  | industry |

## 1.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id, WBS_id, drawing_revision, as_built_revision |
| 2 | Engineering | process |  |  | project_id, WBS_id, drawing_revision, as_built_revision |
| 3 | Engineering | process |  |  | project_id, WBS_id, drawing_revision, as_built_revision |
| 4 | Procurement | process |  |  | project_id, WBS_id, spool_id |
| 5 | Material | process |  |  | project_id, WBS_id, drawing_revision |
| 6 | Fabrication | process |  |  | project_id, WBS_id, material_heat_no |
| 7 | Quality Gate | gate |  | 6,8 | NDT_result, hydro_test_result, punch_item |
| 8 | Module | process |  |  | project_id, WBS_id, NDT_result |
| 9 | Preservation | process |  |  | project_id, WBS_id, hydro_test_result |
| 10 | Logistics | process |  |  | project_id, WBS_id, coating_DFT |
| 11 | Site | process |  |  | project_id, WBS_id, punch_item |
| 12 | Handover | process |  |  | project_id, WBS_id, commissioning_check |

## 1.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id, WBS_id, drawing_revision, as_built_revision |
| 2 | Engineering | process |  |  | project_id, WBS_id, drawing_revision, as_built_revision |
| 3 | Engineering | process |  |  | project_id, WBS_id, drawing_revision, as_built_revision |
| 4 | Procurement | process |  |  | project_id, WBS_id, spool_id |
| 5 | Material | process |  |  | project_id, WBS_id, drawing_revision |
| 6 | Fabrication | process |  |  | project_id, WBS_id, material_heat_no |
| 7 | Quality Gate | gate |  | 6,8 | NDT_result, hydro_test_result, punch_item |
| 8 | Module | process |  |  | project_id, WBS_id, NDT_result |
| 9 | Preservation | process |  |  | project_id, WBS_id, hydro_test_result |
| 10 | Logistics | process |  |  | project_id, WBS_id, coating_DFT |
| 11 | Site | process |  |  | project_id, WBS_id, punch_item |
| 12 | Handover | process |  |  | project_id, WBS_id, commissioning_check |

## 1.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | Cutting |
| 6 | 2 | Fit-up |
| 6 | 3 | Welding |
| 6 | 4 | Dimensional Check |
| 7 | 1 | NDT |
| 7 | 2 | Pressure Test |
| 7 | 3 | Leak Test |
| 7 | 4 | NCR/Repair |
| 12 | 1 | Loop Check |
| 12 | 2 | SAT |
| 12 | 3 | Punch Close |
| 12 | 4 | As-built Handover |

## 1.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | 切割 |
| 6 | 2 | 组对 |
| 6 | 3 | 焊接 |
| 6 | 4 | 尺寸检查 |
| 7 | 1 | NDT |
| 7 | 2 | 压力试验 |
| 7 | 3 | 泄漏试验 |
| 7 | 4 | NCR/维修 |
| 12 | 1 | Loop检查 |
| 12 | 2 | SAT |
| 12 | 3 | Punch关闭 |
| 12 | 4 | As-built交付 |

## 1.9 data_capture_points

```yaml
- project_id
- WBS_id
- module_id
- line_no
- spool_id
- drawing_revision
- material_heat_no
- weld_id
- NDT_result
- hydro_test_result
- coating_DFT
- punch_item
- commissioning_check
- as_built_revision
```


# 2. A02 — 주문형 산업기계·중장비

```yaml
subindustry_code: A02
legacy_slug: heavy_equipment
label_ko: 주문형 산업기계·중장비
label_zh: 定制工业机械·重型装备
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  주문형 산업기계·중장비는 고객 옵션, 대형 가공품, 용접 구조물, 유압·전장 통합, Software/Parameter Load, FAT가 결합된 ETO/ATO형 조립 프로젝트다.
routing_description_zh: >
  定制工业机械与重型装备是结合客户选项、大型加工件、焊接结构、液压/电气集成、软件/参数加载和FAT的ETO/ATO装配项目。
```

## 2.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 수주사양·Option 기준선 | 고객 요구, 성능, 용량, 설치조건, Option과 인수기준을 확정한다. |
| 2 | 기계설계·BOM·도면 Release | 3D 설계, EBOM/MBOM, 유압·공압·전장 도면과 가공도면을 Release한다. |
| 3 | 주요 구매품·외주품 조달 | 모터, 감속기, 베어링, 실린더, 제어기, 센서, 외주가공품의 납기와 승인상태를 관리한다. |
| 4 | 소재·가공품 입고검사 | 소재 규격, Heat No., 외주가공 치수, 표면상태와 성적서를 확인한다. |
| 5 | 절단·제관·용접 구조물 제작 | Frame, Base, Boom, Arm, Tank 등 구조물을 절단, Fit-up, 용접, 교정한다. |
| 6 | CNC·대형가공·정밀가공 | Machining Program, Tool, 치수·공차, 형상위치공차와 검사 결과를 관리한다. |
| 7 | 열처리·도장·표면처리 | 열처리, Shot Blast, 도장, 도금, 방청 등 후처리 조건과 외주 Certificate를 관리한다. |
| 8 | Sub Assembly | 기계 Submodule, 유압 Unit, 구동부, Jig, Cover, Guard를 조립한다. |
| 9 | 유압·공압·윤활 계통 조립 | Pump, Valve, Hose, Cylinder, Lubrication Line, Leak Check를 수행한다. |
| 10 | 전장·제어반·센서 배선 | Control Panel, PLC/HMI, Sensor, Cable, I/O, Safety Interlock을 연결한다. |
| 11 | Final Assembly / Alignment | Main Frame과 Submodule을 통합하고 Leveling, Alignment, Torque, Clearance를 확인한다. |
| 12 | Software·Parameter Load | PLC/HMI Program, Motion Parameter, Recipe, 고객 Option 값을 탑재한다. |
| 13 | Dry Run·Function Test | 무부하 구동, Safety, Interlock, Cycle 동작과 기능시험을 수행한다. |
| 14 | FAT·고객검수·Punch Close | 고객 Witness FAT, 성능시험, Punch List, 조건부 인수사항을 통제한다. |
| 15 | 분해·포장·출하·설치지원 | 분해포장, 보존, 설치 Manual, Spare Part, 현장 설치지원 자료를 준비한다. |

## 2.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 订单规格·选项基线 | 确认客户需求、性能、容量、安装条件、选项和验收标准。 |
| 2 | 机械设计·BOM·图纸发布 | 发布3D设计、EBOM/MBOM、液压/气动/电气图纸和加工图。 |
| 3 | 主要采购件·外协件采购 | 管理电机、减速机、轴承、油缸、控制器、传感器和外协加工件的交期与批准状态。 |
| 4 | 材料·加工件入库检验 | 确认材料规格、Heat No.、外协加工尺寸、表面状态和质量证明。 |
| 5 | 切割·铆焊·焊接结构件制作 | 对Frame、Base、Boom、Arm、Tank等结构件进行切割、组对、焊接和校正。 |
| 6 | CNC·大型加工·精密加工 | 管理Machining Program、Tool、尺寸公差、形位公差和检验结果。 |
| 7 | 热处理·涂装·表面处理 | 管理热处理、喷砂、涂装、电镀、防锈等后处理条件和外协证书。 |
| 8 | Sub Assembly | 组装机械子模块、液压单元、驱动部、治具、Cover和Guard。 |
| 9 | 液压·气动·润滑系统装配 | 安装Pump、Valve、Hose、Cylinder、Lubrication Line并执行Leak Check。 |
| 10 | 电气·控制柜·传感器布线 | 连接Control Panel、PLC/HMI、Sensor、Cable、I/O和Safety Interlock。 |
| 11 | Final Assembly / Alignment | 集成主机架和子模块，并确认Leveling、Alignment、Torque和Clearance。 |
| 12 | Software·Parameter Load | 加载PLC/HMI程序、Motion Parameter、Recipe和客户选项参数。 |
| 13 | Dry Run·Function Test | 执行空载运行、安全、Interlock、Cycle动作和功能测试。 |
| 14 | FAT·客户验收·Punch关闭 | 管理客户Witness FAT、性能测试、Punch List和条件验收事项。 |
| 15 | 拆解·包装·出货·安装支持 | 准备拆解包装、保存、安装手册、备件和现场安装支持资料。 |

## 2.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | Option 기준선 | 고객 Option, 성능조건, 설치조건이 설계·BOM·검사기준에 반영됐는지 확인한다. | 1,2 | process_step |
| 2 | 형상 일치 | EBOM, MBOM, 가공도면, 유압·전장도면, Software Revision 간 형상 일치를 관리한다. | 2,12 | process_step |
| 3 | 장납기·외주 | 대형 구매품과 외주가공품의 승인, 납기, 검사성적, 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 가공 이력 | Machine Program, Tool, 치수검사 결과를 Part Serial과 연결한다. | 5,6 | process_step |
| 5 | 유압·전장 통합 | 유압 Line, I/O, Cable, Safety Interlock을 장비 Serial 기준으로 검증한다. | 9,10 | process_step |
| 6 | FAT Gate | Dry Run, 기능시험, 고객 Witness FAT와 Punch Close 결과를 인수 기준과 연결한다. | 13,14 | process_step |
| 7 | 설치 지원 | 분해·포장 단위와 현장 설치 위치, Spare Part, Manual을 최종 출하 기준으로 관리한다. | 15 | process_step |

## 2.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 选项基线 | 确认客户选项、性能条件和安装条件已反映到设计、BOM和检验标准。 | 1,2 | process_step |
| 2 | 构型一致 | 管理EBOM、MBOM、加工图、液压/电气图和软件版本的一致性。 | 2,12 | process_step |
| 3 | 长交期·外协 | 跟踪大型采购件和外协加工件的批准、交期、检验报告和替代件应用。 | 3,4 | process_step |
| 4 | 加工履历 | 将Machine Program、Tool和尺寸检验结果连接到Part Serial。 | 5,6 | process_step |
| 5 | 液压·电气集成 | 按设备Serial验证液压Line、I/O、Cable和Safety Interlock。 | 9,10 | process_step |
| 6 | FAT Gate | 将Dry Run、功能测试、客户Witness FAT和Punch关闭结果连接到验收标准。 | 13,14 | process_step |
| 7 | 安装支持 | 按最终出货标准管理拆解包装单位、现场安装位置、备件和手册。 | 15 | process_step |

## 2.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Order | process |  |  | project_id, drawing_revision, software_revision |
| 2 | Engineering | process |  |  | project_id, drawing_revision, software_revision |
| 3 | Procurement | process |  |  | project_id, drawing_revision, software_revision |
| 4 | Incoming | process |  |  | project_id, work_order_id, drawing_revision |
| 5 | Fabrication | process |  |  | project_id, work_order_id, part_serial |
| 6 | Machining | process |  |  | project_id, work_order_id, material_heat_no |
| 7 | Surface | process |  |  | project_id, work_order_id, machine_program |
| 8 | Sub Assembly | process |  |  | project_id, work_order_id, tool_id |
| 9 | Hydraulic | process |  |  | project_id, work_order_id, weld_id |
| 10 | Electrical | process |  |  | project_id, work_order_id, hydraulic_line_id |
| 11 | Final Assembly | process |  |  | project_id, work_order_id, I_O_point |
| 12 | Software | process |  |  | project_id, work_order_id, software_revision |
| 13 | Test | process |  |  | project_id, work_order_id, FAT_result |
| 14 | Gate | gate |  | 11,12,13 | FAT_result, punch_item |
| 15 | Shipment | process |  |  | project_id, work_order_id |

## 2.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Order | process |  |  | project_id, drawing_revision, software_revision |
| 2 | Engineering | process |  |  | project_id, drawing_revision, software_revision |
| 3 | Procurement | process |  |  | project_id, drawing_revision, software_revision |
| 4 | Incoming | process |  |  | project_id, work_order_id, drawing_revision |
| 5 | Fabrication | process |  |  | project_id, work_order_id, part_serial |
| 6 | Machining | process |  |  | project_id, work_order_id, material_heat_no |
| 7 | Surface | process |  |  | project_id, work_order_id, machine_program |
| 8 | Sub Assembly | process |  |  | project_id, work_order_id, tool_id |
| 9 | Hydraulic | process |  |  | project_id, work_order_id, weld_id |
| 10 | Electrical | process |  |  | project_id, work_order_id, hydraulic_line_id |
| 11 | Final Assembly | process |  |  | project_id, work_order_id, I_O_point |
| 12 | Software | process |  |  | project_id, work_order_id, software_revision |
| 13 | Test | process |  |  | project_id, work_order_id, FAT_result |
| 14 | Gate | gate |  | 11,12,13 | FAT_result, punch_item |
| 15 | Shipment | process |  |  | project_id, work_order_id |

## 2.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | Rough Machining |
| 6 | 2 | Finish Machining |
| 6 | 3 | CMM Check |
| 11 | 1 | Leveling |
| 11 | 2 | Alignment |
| 11 | 3 | Torque Check |
| 14 | 1 | FAT Test |
| 14 | 2 | Customer Witness |
| 14 | 3 | Punch Close |

## 2.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | 粗加工 |
| 6 | 2 | 精加工 |
| 6 | 3 | CMM检查 |
| 11 | 1 | 找平 |
| 11 | 2 | 对中 |
| 11 | 3 | 扭矩检查 |
| 14 | 1 | FAT测试 |
| 14 | 2 | 客户见证 |
| 14 | 3 | Punch关闭 |

## 2.9 data_capture_points

```yaml
- project_id
- work_order_id
- equipment_serial
- option_code
- drawing_revision
- part_serial
- material_heat_no
- machine_program
- tool_id
- weld_id
- hydraulic_line_id
- I_O_point
- software_revision
- FAT_result
- punch_item
```


# 3. A03 — 반도체·디스플레이 제조장비

```yaml
subindustry_code: A03
legacy_slug: semi_equipment
label_ko: 반도체·디스플레이 제조장비
label_zh: 半导体·显示制造设备
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  반도체·디스플레이 장비는 Frame, Chamber, Vacuum/Gas, Motion, Electrical, Software, Particle 관리, FAT/SAT를 장비 Serial·Module Serial 기준으로 묶어야 한다.
routing_description_zh: >
  半导体/显示设备需要按设备Serial和Module Serial连接Frame、Chamber、Vacuum/Gas、Motion、Electrical、Software、Particle控制、FAT/SAT。
```

## 3.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객 URS·장비 Spec 기준선 | 고객 URS, 성능, Footprint, Utility, Clean 기준과 인수조건을 확정한다. |
| 2 | 기구·Chamber·Vacuum 설계 | Frame, Chamber, Vacuum, Gas, Motion, Thermal, Safety 구조를 설계한다. |
| 3 | BOM·도면·SW/Recipe Release | EBOM/MBOM, 도면, PLC/HMI, Recipe, SECS/GEM 요구를 Release한다. |
| 4 | 정밀부품·Chamber·가스부품 조달 | 정밀가공품, Chamber, Valve, MFC, Pump, Robot, Sensor의 납기와 승인상태를 관리한다. |
| 5 | Frame·Base·정밀가공품 제작 | Frame, Base, Plate, Bracket, Precision Part를 가공·검사한다. |
| 6 | Chamber·Vacuum·Gas Module 조립 | Chamber, Vacuum Line, Gas Box, Pump, Exhaust, Leak Check를 수행한다. |
| 7 | Motion·Robot·Handling 조립 | Stage, Robot, Load Port, Transfer Module, Alignment 구조를 조립한다. |
| 8 | 전장·제어·Safety Interlock | Control Panel, I/O, Cable, PLC, Safety Interlock을 연결한다. |
| 9 | Software·Recipe·SECS/GEM Load | HMI, Recipe, Motion Parameter, SECS/GEM, Alarm, Log 설정을 탑재한다. |
| 10 | Particle·Vacuum·Utility Qualification | Particle, Base Pressure, Leak Rate, Gas Flow, Temperature, Utility 조건을 검증한다. |
| 11 | FAT·Process Demo·고객검수 | FAT, Process Demo, Throughput, Repeatability, 고객 Witness를 수행한다. |
| 12 | 출하·설치·SAT | Clean Packing, 출하, 현장 설치, Hook-up, SAT와 인수자료를 완료한다. |

## 3.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 고객 URS·장비 Spec 기준선 | 确认客户URS、性能、Footprint、Utility、洁净标准和验收条件。 |
| 2 | 기구·Chamber·Vacuum 설계 | 设计Frame、Chamber、Vacuum、Gas、Motion、Thermal和Safety结构。 |
| 3 | BOM·도면·SW/Recipe Release | 发布EBOM/MBOM、图纸、PLC/HMI、Recipe和SECS/GEM要求。 |
| 4 | 정밀부품·Chamber·가스부품 조달 | 管理精密加工件、Chamber、Valve、MFC、Pump、Robot、Sensor的交期和批准状态。 |
| 5 | Frame·Base·정밀가공품 제작 | 加工和检查Frame、Base、Plate、Bracket和精密零件。 |
| 6 | Chamber·Vacuum·Gas Module 조립 | 组装Chamber、Vacuum Line、Gas Box、Pump、Exhaust并执行Leak Check。 |
| 7 | Motion·Robot·Handling 조립 | 组装Stage、Robot、Load Port、Transfer Module和Alignment结构。 |
| 8 | 전장·제어·Safety Interlock | 连接Control Panel、I/O、Cable、PLC和Safety Interlock。 |
| 9 | Software·Recipe·SECS/GEM Load | 加载HMI、Recipe、Motion Parameter、SECS/GEM、Alarm和Log设置。 |
| 10 | Particle·Vacuum·Utility Qualification | 验证Particle、Base Pressure、Leak Rate、Gas Flow、Temperature和Utility条件。 |
| 11 | FAT·Process Demo·고객검수 | 执行FAT、Process Demo、Throughput、Repeatability和客户Witness。 |
| 12 | 출하·설치·SAT | 完成Clean Packing、出货、现场安装、Hook-up、SAT和验收资料。 |

## 3.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항 기준선 | 반도체·디스플레이 제조장비의 고객 사양, 성능조건, 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 형상·Revision 관리 | 설계도면, BOM, 공정계획, Software/Parameter Revision의 일치성을 관리한다. | 2,3 | process_step |
| 3 | 조달·자재 추적 | 장납기품, 핵심 소재, 외주품의 승인, 납기, Lot/Serial과 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 제작·조립 이력 | 소재, Machine/Program, Tool/Jig, 작업자, 공정조건과 재작업 이력을 Serial/Module 기준으로 연결한다. | 5,9 | process_step |
| 5 | 검사 Gate | Gate 공정 #10의 검사·시험 결과, NCR, Repair, Re-test를 인수기준과 연결한다. | 10 | process_step |
| 6 | FAT/SAT·인수 | FAT/SAT, 고객 Witness, Punch Close, As-built 또는 최종 인수자료를 통제한다. | 11,12 | process_step |
| 7 | 보안·IP·접근권한 | 고객 IP, 방산·수출통제 자료, 공정 Recipe와 협력사 접근권한을 프로젝트별로 격리·감사한다. |  | industry |

## 3.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求基线 | 将半导体·显示制造设备的客户规格、性能条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 构型·版本管理 | 管理设计图纸、BOM、工艺计划和Software/Parameter Revision的一致性。 | 2,3 | process_step |
| 3 | 采购·材料追踪 | 跟踪长周期物料、关键材料、外协件的批准、交期、Lot/Serial和替代件应用。 | 3,4 | process_step |
| 4 | 制造·装配履历 | 按Serial/Module连接材料、Machine/Program、Tool/Jig、作业员、工艺条件和返工履历。 | 5,9 | process_step |
| 5 | 检验Gate | 将Gate工序#10的检验/测试结果、NCR、Repair、Re-test连接到验收标准。 | 10 | process_step |
| 6 | FAT/SAT·验收 | 控制FAT/SAT、客户Witness、Punch关闭、As-built或最终验收资料。 | 11,12 | process_step |
| 7 | 安全·IP·访问权限 | 按项目隔离并审计客户IP、防务/出口管制资料、工艺Recipe和合作方访问权限。 |  | industry |

## 3.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Specification | process |  |  | project_id, recipe_id, software_revision |
| 2 | Design | process |  |  | project_id, recipe_id, software_revision |
| 3 | Configuration | process |  |  | project_id, recipe_id, software_revision |
| 4 | Procurement | process |  |  | project_id, equipment_serial, vacuum_pump_serial |
| 5 | Fabrication | process |  |  | project_id, equipment_serial, gas_box_serial |
| 6 | Vacuum/Gas | process |  |  | project_id, equipment_serial, motion_axis_id |
| 7 | Motion | process |  |  | project_id, equipment_serial, particle_result |
| 8 | Electrical | process |  |  | project_id, equipment_serial, recipe_id |
| 9 | Software | process |  |  | project_id, equipment_serial, software_revision |
| 10 | Gate | gate |  | 6,7,8,9 | particle_result, SECSGEM_test, FAT_result, SAT_result |
| 11 | FAT | process |  |  | project_id, equipment_serial, FAT_result |
| 12 | SAT | process |  |  | project_id, equipment_serial, SAT_result |

## 3.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Specification | process |  |  | project_id, recipe_id, software_revision |
| 2 | Design | process |  |  | project_id, recipe_id, software_revision |
| 3 | Configuration | process |  |  | project_id, recipe_id, software_revision |
| 4 | Procurement | process |  |  | project_id, equipment_serial, vacuum_pump_serial |
| 5 | Fabrication | process |  |  | project_id, equipment_serial, gas_box_serial |
| 6 | Vacuum/Gas | process |  |  | project_id, equipment_serial, motion_axis_id |
| 7 | Motion | process |  |  | project_id, equipment_serial, particle_result |
| 8 | Electrical | process |  |  | project_id, equipment_serial, recipe_id |
| 9 | Software | process |  |  | project_id, equipment_serial, software_revision |
| 10 | Gate | gate |  | 6,7,8,9 | particle_result, SECSGEM_test, FAT_result, SAT_result |
| 11 | FAT | process |  |  | project_id, equipment_serial, FAT_result |
| 12 | SAT | process |  |  | project_id, equipment_serial, SAT_result |

## 3.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 10 | 1 | Inspection/Test |
| 10 | 2 | NCR Review |
| 10 | 3 | Repair/Re-test |
| 12 | 1 | Customer Acceptance |
| 12 | 2 | Punch Close |
| 12 | 3 | Handover |

## 3.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 10 | 1 | 检验/测试 |
| 10 | 2 | NCR评审 |
| 10 | 3 | 维修/复测 |
| 12 | 1 | 客户验收 |
| 12 | 2 | Punch关闭 |
| 12 | 3 | 交付 |

## 3.9 data_capture_points

```yaml
- project_id
- equipment_serial
- module_serial
- chamber_serial
- vacuum_pump_serial
- gas_box_serial
- motion_axis_id
- particle_result
- recipe_id
- software_revision
- SECSGEM_test
- FAT_result
- SAT_result
```


# 4. A04 — 배터리·태양광 제조장비

```yaml
subindustry_code: A04
legacy_slug: battery_equipment
label_ko: 배터리·태양광 제조장비
label_zh: 电池·光伏制造设备
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  배터리·태양광 장비는 Roll-to-Roll, Slot Die Coating, Dry Room, Formation, EL/IV Test, Recipe Matching과 FAT/SAT가 중심이다.
routing_description_zh: >
  电池/光伏设备以Roll-to-Roll、Slot Die Coating、Dry Room、Formation、EL/IV Test、Recipe Matching和FAT/SAT为核心。
```

## 4.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객 Spec·생산공정 기준선 | 전극, 조립, 화성, 검사 또는 태양광 Cell/Module 장비 범위를 확정한다. |
| 2 | 장비 Layout·공정 Concept 설계 | Roll-to-Roll, Coating, Dryer, Formation, EL/IV, Lamination 구조를 설계한다. |
| 3 | BOM·도면·Recipe Release | 기계·전장·제어 BOM, Recipe, 검사 기준과 FAT 조건을 Release한다. |
| 4 | 정밀 Module·주요부품 조달 | Roll, Slot Die, Dryer, Laser, Welding, Formation Channel, Test Fixture를 조달한다. |
| 5 | Frame·Roll·구동부 제작 | Frame, Roll, Drive, Tension Unit, Web Guide를 가공·조립한다. |
| 6 | Coating·Dryer·Press Module 조립 | Slot Die, Pump, Dryer, Calender, Slitter Module을 조립한다. |
| 7 | Dry Room·전해액·Safety 통합 | Dry Room Interface, Electrolyte Filling, Exhaust, Safety Interlock을 검증한다. |
| 8 | Formation·Aging·Test Channel 조립 | Formation/Aging Channel, Power Supply, Contact, Fixture를 조립한다. |
| 9 | 태양광 Cell·Module 장비 조립 | Stringer, Layup, Laminator, EL/IV, Framing 장비를 조립한다. |
| 10 | Recipe·Parameter·Data Interface Load | Coating Gap, Web Tension, Drying Temp, Test Program과 Interface를 탑재한다. |
| 11 | Sample Run·Process Qualification | 균일도, 두께, 불량, Throughput, Recipe Matching을 검증한다. |
| 12 | FAT·출하·SAT | 고객 FAT, Punch, Clean/Dry Packing, 현장 SAT와 인수자료를 완료한다. |

## 4.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 고객 Spec·생산공정 기준선 | 确认电极、装配、化成、检测或光伏Cell/Module设备范围。 |
| 2 | 장비 Layout·공정 Concept 설계 | 设计Roll-to-Roll、Coating、Dryer、Formation、EL/IV、Lamination结构。 |
| 3 | BOM·도면·Recipe Release | 发布机械/电气/控制BOM、Recipe、检验标准和FAT条件。 |
| 4 | 정밀 Module·주요부품 조달 | 采购Roll、Slot Die、Dryer、Laser、Welding、Formation Channel和Test Fixture。 |
| 5 | Frame·Roll·구동부 제작 | 加工和组装Frame、Roll、Drive、Tension Unit和Web Guide。 |
| 6 | Coating·Dryer·Press Module 조립 | 组装Slot Die、Pump、Dryer、Calender和Slitter Module。 |
| 7 | Dry Room·전해액·Safety 통합 | 验证Dry Room接口、Electrolyte Filling、Exhaust和Safety Interlock。 |
| 8 | Formation·Aging·Test Channel 조립 | 组装Formation/Aging Channel、Power Supply、Contact和Fixture。 |
| 9 | 태양광 Cell·Module 장비 조립 | 组装Stringer、Layup、Laminator、EL/IV和Framing设备。 |
| 10 | Recipe·Parameter·Data Interface Load | 加载Coating Gap、Web Tension、Drying Temp、Test Program和接口。 |
| 11 | Sample Run·Process Qualification | 验证均匀性、厚度、不良、Throughput和Recipe Matching。 |
| 12 | FAT·출하·SAT | 完成客户FAT、Punch、Clean/Dry Packing、现场SAT和验收资料。 |

## 4.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항 기준선 | 배터리·태양광 제조장비의 고객 사양, 성능조건, 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 형상·Revision 관리 | 설계도면, BOM, 공정계획, Software/Parameter Revision의 일치성을 관리한다. | 2,3 | process_step |
| 3 | 조달·자재 추적 | 장납기품, 핵심 소재, 외주품의 승인, 납기, Lot/Serial과 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 제작·조립 이력 | 소재, Machine/Program, Tool/Jig, 작업자, 공정조건과 재작업 이력을 Serial/Module 기준으로 연결한다. | 5,10 | process_step |
| 5 | 검사 Gate | Gate 공정 #11의 검사·시험 결과, NCR, Repair, Re-test를 인수기준과 연결한다. | 11 | process_step |
| 6 | FAT/SAT·인수 | FAT/SAT, 고객 Witness, Punch Close, As-built 또는 최종 인수자료를 통제한다. | 11,12 | process_step |
| 7 | 보안·IP·접근권한 | 고객 IP, 방산·수출통제 자료, 공정 Recipe와 협력사 접근권한을 프로젝트별로 격리·감사한다. |  | industry |

## 4.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求基线 | 将电池·光伏制造设备的客户规格、性能条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 构型·版本管理 | 管理设计图纸、BOM、工艺计划和Software/Parameter Revision的一致性。 | 2,3 | process_step |
| 3 | 采购·材料追踪 | 跟踪长周期物料、关键材料、外协件的批准、交期、Lot/Serial和替代件应用。 | 3,4 | process_step |
| 4 | 制造·装配履历 | 按Serial/Module连接材料、Machine/Program、Tool/Jig、作业员、工艺条件和返工履历。 | 5,10 | process_step |
| 5 | 检验Gate | 将Gate工序#11的检验/测试结果、NCR、Repair、Re-test连接到验收标准。 | 11 | process_step |
| 6 | FAT/SAT·验收 | 控制FAT/SAT、客户Witness、Punch关闭、As-built或最终验收资料。 | 11,12 | process_step |
| 7 | 安全·IP·访问权限 | 按项目隔离并审计客户IP、防务/出口管制资料、工艺Recipe和合作方访问权限。 |  | industry |

## 4.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | project_id, recipe_id |
| 2 | Design | process |  |  | project_id, recipe_id |
| 3 | Configuration | process |  |  | project_id, recipe_id |
| 4 | Procurement | process |  |  | project_id, equipment_serial, slot_die_id |
| 5 | Fabrication | process |  |  | project_id, equipment_serial, web_tension |
| 6 | Coating | process |  |  | project_id, equipment_serial, coating_gap |
| 7 | Dry Room | process |  |  | project_id, equipment_serial, coating_thickness |
| 8 | Formation | process |  |  | project_id, equipment_serial, drying_temperature |
| 9 | PV Module | process |  |  | project_id, equipment_serial, formation_channel_id |
| 10 | Software | process |  |  | project_id, equipment_serial, EL_result |
| 11 | Gate | gate |  | 6,8,9,10 | EL_result, IV_result, FAT_result, SAT_result |
| 12 | SAT | process |  |  | project_id, equipment_serial, recipe_id |

## 4.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | project_id, recipe_id |
| 2 | Design | process |  |  | project_id, recipe_id |
| 3 | Configuration | process |  |  | project_id, recipe_id |
| 4 | Procurement | process |  |  | project_id, equipment_serial, slot_die_id |
| 5 | Fabrication | process |  |  | project_id, equipment_serial, web_tension |
| 6 | Coating | process |  |  | project_id, equipment_serial, coating_gap |
| 7 | Dry Room | process |  |  | project_id, equipment_serial, coating_thickness |
| 8 | Formation | process |  |  | project_id, equipment_serial, drying_temperature |
| 9 | PV Module | process |  |  | project_id, equipment_serial, formation_channel_id |
| 10 | Software | process |  |  | project_id, equipment_serial, EL_result |
| 11 | Gate | gate |  | 6,8,9,10 | EL_result, IV_result, FAT_result, SAT_result |
| 12 | SAT | process |  |  | project_id, equipment_serial, recipe_id |

## 4.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 11 | 1 | Inspection/Test |
| 11 | 2 | NCR Review |
| 11 | 3 | Repair/Re-test |
| 12 | 1 | Customer Acceptance |
| 12 | 2 | Punch Close |
| 12 | 3 | Handover |

## 4.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 11 | 1 | 检验/测试 |
| 11 | 2 | NCR评审 |
| 11 | 3 | 维修/复测 |
| 12 | 1 | 客户验收 |
| 12 | 2 | Punch关闭 |
| 12 | 3 | 交付 |

## 4.9 data_capture_points

```yaml
- project_id
- equipment_serial
- module_serial
- roll_id
- slot_die_id
- web_tension
- coating_gap
- coating_thickness
- drying_temperature
- formation_channel_id
- EL_result
- IV_result
- recipe_id
- FAT_result
- SAT_result
```


# 5. A05 — 조선·해양플랜트

```yaml
subindustry_code: A05
legacy_slug: shipbuilding
label_ko: 조선·해양플랜트
label_zh: 船舶·海洋工程
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  조선·해양플랜트는 강재 전처리, 절단, 소조립, 블록, 탑재, 의장, 도장, 시운전이 Ship/Block/Zone 기준으로 연결된다.
routing_description_zh: >
  船舶/海洋工程按Ship/Block/Zone连接钢材预处理、切割、小组立、分段、搭载、舾装、涂装和试航。
```

## 5.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 계약·선급·기본사양 기준선 | 선급, Flag, 선주사양, 주요 장비, 인도일과 성능보증 조건을 확정한다. |
| 2 | 기본설계·상세설계·생산설계 | Hull, Outfitting, Piping, Electrical, Block 분할과 생산도면을 Release한다. |
| 3 | 강재·주요 기자재 조달 | 강재, 엔진, 발전기, Pump, Valve, Cable, Pipe와 장납기 기자재를 관리한다. |
| 4 | 강재 입고·전처리·Nesting | Plate/Beam Heat No., Shot Blast, Primer, Nesting 정보를 확인한다. |
| 5 | 절단·곡가공·소부재 제작 | NC Cutting, Bending, Marking, 소부재 제작을 수행한다. |
| 6 | 소조립·중조립 | Panel, Web, Girder, Unit 단위로 Fit-up, Welding, 치수검사를 수행한다. |
| 7 | Block Assembly | Block 단위 대조립, 용접, 치수검사, NDT와 보강재 설치를 수행한다. |
| 8 | Pre-outfitting·Pipe Spool | Block 내 Pipe Spool, Cable Tray, Equipment Seat, Outfitting Item을 선행 설치한다. |
| 9 | 도장·방청 | Block/Zone 도장, DFT, 환경조건, 보수도장을 관리한다. |
| 10 | Dock Erection·탑재 | Block을 Dock에서 탑재하고 Alignment, Erection Sequence, Crane 계획을 관리한다. |
| 11 | 선내 의장·전장·배관 연결 | Machinery, Piping, Cable, HVAC, Accommodation 의장을 연결한다. |
| 12 | Harbor Test·Sea Trial·인도 | Harbor Test, Sea Trial, Punch Close, 선급·선주 인수와 인도문서를 완료한다. |

## 5.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 계약·선급·기본사양 기준선 | 确认船级、船旗、船东规格、主要设备、交付期和性能保证条件。 |
| 2 | 기본설계·상세설계·생산설계 | 发布Hull、Outfitting、Piping、Electrical、Block划分和生产图。 |
| 3 | 강재·주요 기자재 조달 | 管理钢材、发动机、发电机、Pump、Valve、Cable、Pipe和长周期设备。 |
| 4 | 강재 입고·전처리·Nesting | 确认Plate/Beam Heat No.、Shot Blast、Primer和Nesting信息。 |
| 5 | 절단·곡가공·소부재 제작 | 执行NC Cutting、Bending、Marking和小构件制作。 |
| 6 | 소조립·중조립 | 按Panel、Web、Girder、Unit执行组对、焊接和尺寸检查。 |
| 7 | Block Assembly | 执行Block大组立、焊接、尺寸检查、NDT和加强材安装。 |
| 8 | Pre-outfitting·Pipe Spool | 在Block内预装Pipe Spool、Cable Tray、Equipment Seat和舾装件。 |
| 9 | 도장·방청 | 管理Block/Zone涂装、DFT、环境条件和修补涂装。 |
| 10 | Dock Erection·탑재 | 在船坞搭载Block并管理Alignment、Erection Sequence和Crane计划。 |
| 11 | 선내 의장·전장·배관 연결 | 连接Machinery、Piping、Cable、HVAC和Accommodation舾装。 |
| 12 | Harbor Test·Sea Trial·인도 | 完成Harbor Test、Sea Trial、Punch关闭、船级/船东验收和交付文件。 |

## 5.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항 기준선 | 조선·해양플랜트의 고객 사양, 성능조건, 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 형상·Revision 관리 | 설계도면, BOM, 공정계획, Software/Parameter Revision의 일치성을 관리한다. | 2,3 | process_step |
| 3 | 조달·자재 추적 | 장납기품, 핵심 소재, 외주품의 승인, 납기, Lot/Serial과 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 제작·조립 이력 | 소재, Machine/Program, Tool/Jig, 작업자, 공정조건과 재작업 이력을 Serial/Module 기준으로 연결한다. | 5,11 | process_step |
| 5 | 검사 Gate | Gate 공정 #12의 검사·시험 결과, NCR, Repair, Re-test를 인수기준과 연결한다. | 12 | process_step |
| 6 | FAT/SAT·인수 | FAT/SAT, 고객 Witness, Punch Close, As-built 또는 최종 인수자료를 통제한다. | 11,12 | process_step |
| 7 | 보안·IP·접근권한 | 고객 IP, 방산·수출통제 자료, 공정 Recipe와 협력사 접근권한을 프로젝트별로 격리·감사한다. |  | industry |

## 5.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求基线 | 将船舶·海洋工程的客户规格、性能条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 构型·版本管理 | 管理设计图纸、BOM、工艺计划和Software/Parameter Revision的一致性。 | 2,3 | process_step |
| 3 | 采购·材料追踪 | 跟踪长周期物料、关键材料、外协件的批准、交期、Lot/Serial和替代件应用。 | 3,4 | process_step |
| 4 | 制造·装配履历 | 按Serial/Module连接材料、Machine/Program、Tool/Jig、作业员、工艺条件和返工履历。 | 5,11 | process_step |
| 5 | 检验Gate | 将Gate工序#12的检验/测试结果、NCR、Repair、Re-test连接到验收标准。 | 12 | process_step |
| 6 | FAT/SAT·验收 | 控制FAT/SAT、客户Witness、Punch关闭、As-built或最终验收资料。 | 11,12 | process_step |
| 7 | 安全·IP·访问权限 | 按项目隔离并审计客户IP、防务/出口管制资料、工艺Recipe和合作方访问权限。 |  | industry |

## 5.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id |
| 2 | Engineering | process |  |  | project_id |
| 3 | Procurement | process |  |  | project_id |
| 4 | Steel Prep | process |  |  | project_id, ship_no, plate_heat_no |
| 5 | Cutting | process |  |  | project_id, ship_no, nesting_no |
| 6 | Sub Assembly | process |  |  | project_id, ship_no, weld_id |
| 7 | Block | process |  |  | project_id, ship_no, NDT_result |
| 8 | Outfitting | process |  |  | project_id, ship_no, pipe_spool_id |
| 9 | Paint | process |  |  | project_id, ship_no, outfitting_item |
| 10 | Dock | process |  |  | project_id, ship_no, paint_DFT |
| 11 | Integration | process |  |  | project_id, ship_no, dock_schedule |
| 12 | Gate | gate |  | 10,11 | NDT_result, sea_trial_result |

## 5.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id |
| 2 | Engineering | process |  |  | project_id |
| 3 | Procurement | process |  |  | project_id |
| 4 | Steel Prep | process |  |  | project_id, ship_no, plate_heat_no |
| 5 | Cutting | process |  |  | project_id, ship_no, nesting_no |
| 6 | Sub Assembly | process |  |  | project_id, ship_no, weld_id |
| 7 | Block | process |  |  | project_id, ship_no, NDT_result |
| 8 | Outfitting | process |  |  | project_id, ship_no, pipe_spool_id |
| 9 | Paint | process |  |  | project_id, ship_no, outfitting_item |
| 10 | Dock | process |  |  | project_id, ship_no, paint_DFT |
| 11 | Integration | process |  |  | project_id, ship_no, dock_schedule |
| 12 | Gate | gate |  | 10,11 | NDT_result, sea_trial_result |

## 5.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 12 | 1 | Customer Acceptance |
| 12 | 2 | Punch Close |
| 12 | 3 | Handover |

## 5.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 12 | 1 | 客户验收 |
| 12 | 2 | Punch关闭 |
| 12 | 3 | 交付 |

## 5.9 data_capture_points

```yaml
- project_id
- ship_no
- block_id
- zone_id
- plate_heat_no
- nesting_no
- weld_id
- NDT_result
- pipe_spool_id
- outfitting_item
- paint_DFT
- dock_schedule
- sea_trial_result
```


# 6. A06 — 항공우주·방산 시스템

```yaml
subindustry_code: A06
legacy_slug: aerospace_equipment
label_ko: 항공우주·방산 시스템
label_zh: 航空航天·防务系统
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  항공우주·방산은 MBD/MBSE, 형상관리, 소재·Serial 추적, Special Process, FAI, Qualification, 보안·수출통제를 공정과 연결해야 한다.
routing_description_zh: >
  航空航天/防务需要将MBD/MBSE、构型管理、材料/Serial追踪、特殊过程、FAI、Qualification、安全与出口管制连接到工艺。
```

## 6.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 계약·규격·보안 기준선 | 고객 규격, 군/항공 요구, 보안등급, 수출통제와 인수기준을 확정한다. |
| 2 | 시스템 설계·MBSE·MBD | System Architecture, Interface, MBD, Digital Thread 구조를 정의한다. |
| 3 | BOM·공정계획·형상 Release | EBOM/MBOM, Process Plan, Tooling, Inspection Plan과 Configuration을 Release한다. |
| 4 | 승인 소재·부품 조달 | 항공소재, 전자부품, COTS, 특수공정 외주와 공급망 진위성을 관리한다. |
| 5 | Part Fabrication / Machining | NC Program, Tool, Fixture, 소재 Heat, 치수·공차를 Part Serial에 연결한다. |
| 6 | Special Process | 열처리, 표면처리, 접착, 복합재, 적층제조 등 승인공정을 수행한다. |
| 7 | Sub Assembly | 구조체, 전장, 배관, Harness, Payload Submodule을 조립한다. |
| 8 | Final Assembly | 시스템 단위 통합, Torque, Alignment, Functional Check를 수행한다. |
| 9 | FAI·검사·NCR | AS9102형 FAI, CMM, NDT, 전기시험, NCR와 MRB 처리를 수행한다. |
| 10 | Qualification·환경시험 | Vibration, Thermal, EMI/EMC, Pressure, Reliability 시험을 수행한다. |
| 11 | 고객 수락·문서 Package | CoC, Test Report, As-built, 형상자료, 보안문서와 인수자료를 제출한다. |

## 6.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 계약·규격·보안 기준선 | 确认客户规范、军工/航空要求、安全等级、出口管制和验收标准。 |
| 2 | 시스템 설계·MBSE·MBD | 定义System Architecture、Interface、MBD和Digital Thread结构。 |
| 3 | BOM·공정계획·형상 Release | 发布EBOM/MBOM、Process Plan、Tooling、Inspection Plan和Configuration。 |
| 4 | 승인 소재·부품 조달 | 管理航空材料、电子部件、COTS、特殊工艺外协和供应链真实性。 |
| 5 | Part Fabrication / Machining | 将NC Program、Tool、Fixture、材料Heat、尺寸公差连接到Part Serial。 |
| 6 | Special Process | 执行热处理、表面处理、粘接、复合材料、增材制造等批准工艺。 |
| 7 | Sub Assembly | 组装结构件、电气、管路、Harness和Payload子模块。 |
| 8 | Final Assembly | 执行系统级集成、Torque、Alignment和Functional Check。 |
| 9 | FAI·검사·NCR | 执行AS9102型FAI、CMM、NDT、电气测试、NCR和MRB处理。 |
| 10 | Qualification·환경시험 | 执行Vibration、Thermal、EMI/EMC、Pressure和Reliability测试。 |
| 11 | 고객 수락·문서 Package | 提交CoC、Test Report、As-built、构型资料、安全文件和验收资料。 |

## 6.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항 기준선 | 항공우주·방산 시스템의 고객 사양, 성능조건, 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 형상·Revision 관리 | 설계도면, BOM, 공정계획, Software/Parameter Revision의 일치성을 관리한다. | 2,3 | process_step |
| 3 | 조달·자재 추적 | 장납기품, 핵심 소재, 외주품의 승인, 납기, Lot/Serial과 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 제작·조립 이력 | 소재, Machine/Program, Tool/Jig, 작업자, 공정조건과 재작업 이력을 Serial/Module 기준으로 연결한다. | 5,8 | process_step |
| 5 | 검사 Gate | Gate 공정 #9의 검사·시험 결과, NCR, Repair, Re-test를 인수기준과 연결한다. | 9 | process_step |
| 6 | FAT/SAT·인수 | FAT/SAT, 고객 Witness, Punch Close, As-built 또는 최종 인수자료를 통제한다. | 10,11 | process_step |
| 7 | 보안·IP·접근권한 | 고객 IP, 방산·수출통제 자료, 공정 Recipe와 협력사 접근권한을 프로젝트별로 격리·감사한다. |  | industry |

## 6.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求基线 | 将航空航天·防务系统的客户规格、性能条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 构型·版本管理 | 管理设计图纸、BOM、工艺计划和Software/Parameter Revision的一致性。 | 2,3 | process_step |
| 3 | 采购·材料追踪 | 跟踪长周期物料、关键材料、外协件的批准、交期、Lot/Serial和替代件应用。 | 3,4 | process_step |
| 4 | 制造·装配履历 | 按Serial/Module连接材料、Machine/Program、Tool/Jig、作业员、工艺条件和返工履历。 | 5,8 | process_step |
| 5 | 检验Gate | 将Gate工序#9的检验/测试结果、NCR、Repair、Re-test连接到验收标准。 | 9 | process_step |
| 6 | FAT/SAT·验收 | 控制FAT/SAT、客户Witness、Punch关闭、As-built或最终验收资料。 | 10,11 | process_step |
| 7 | 安全·IP·访问权限 | 按项目隔离并审计客户IP、防务/出口管制资料、工艺Recipe和合作方访问权限。 |  | industry |

## 6.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id, configuration_id, MBD_revision |
| 2 | Systems | process |  |  | project_id, configuration_id, MBD_revision |
| 3 | Configuration | process |  |  | project_id, configuration_id, MBD_revision |
| 4 | Procurement | process |  |  | project_id, configuration_id, MBD_revision |
| 5 | Fabrication | process |  |  | project_id, configuration_id, NC_program |
| 6 | Special Process | process |  |  | project_id, configuration_id, special_process_id |
| 7 | Sub Assembly | process |  |  | project_id, configuration_id, operator_cert |
| 8 | Final Assembly | process |  |  | project_id, configuration_id, FAI_result |
| 9 | FAI Gate | gate |  | 5,6,7,8 | FAI_result, qualification_result |
| 10 | Qualification | process |  |  | project_id, configuration_id, NCR_id |
| 11 | Handover | process |  |  | project_id, configuration_id, export_control_class |

## 6.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id, configuration_id, MBD_revision |
| 2 | Systems | process |  |  | project_id, configuration_id, MBD_revision |
| 3 | Configuration | process |  |  | project_id, configuration_id, MBD_revision |
| 4 | Procurement | process |  |  | project_id, configuration_id, MBD_revision |
| 5 | Fabrication | process |  |  | project_id, configuration_id, NC_program |
| 6 | Special Process | process |  |  | project_id, configuration_id, special_process_id |
| 7 | Sub Assembly | process |  |  | project_id, configuration_id, operator_cert |
| 8 | Final Assembly | process |  |  | project_id, configuration_id, FAI_result |
| 9 | FAI Gate | gate |  | 5,6,7,8 | FAI_result, qualification_result |
| 10 | Qualification | process |  |  | project_id, configuration_id, NCR_id |
| 11 | Handover | process |  |  | project_id, configuration_id, export_control_class |

## 6.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 9 | 1 | Inspection/Test |
| 9 | 2 | NCR Review |
| 9 | 3 | Repair/Re-test |
| 11 | 1 | Customer Acceptance |
| 11 | 2 | Punch Close |
| 11 | 3 | Handover |

## 6.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 9 | 1 | 检验/测试 |
| 9 | 2 | NCR评审 |
| 9 | 3 | 维修/复测 |
| 11 | 1 | 客户验收 |
| 11 | 2 | Punch关闭 |
| 11 | 3 | 交付 |

## 6.9 data_capture_points

```yaml
- project_id
- configuration_id
- part_serial
- material_heat_no
- MBD_revision
- NC_program
- special_process_id
- operator_cert
- FAI_result
- qualification_result
- NCR_id
- export_control_class
- security_level
```


# 7. A07 — 금형·치공구·전용기

```yaml
subindustry_code: A07
legacy_slug: mold_tooling_dedicated_machine
label_ko: 금형·치공구·전용기
label_zh: 模具·工装·专机
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  금형·치공구·전용기는 설계, 소재, CNC, 열처리, EDM/연마, 조립, Tryout, 수정 반복, 양산이관을 Loop로 표현해야 한다.
routing_description_zh: >
  模具/工装/专机应表达设计、材料、CNC、热处理、EDM/研磨、装配、试模、修模迭代和量产移交的循环。
```

## 7.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 제품사양·금형 요구 기준선 | 제품도, 수축률, Cavity, 수명, Cycle Time, 양산조건을 확정한다. |
| 2 | 금형·치공구 설계 | Parting, Runner/Gate, Cooling, Insert, Slide, Ejector와 Jig 구조를 설계한다. |
| 3 | 소재·표준품 조달 | 금형강, Mold Base, 표준부품, Hot Runner, Sensor, Cylinder를 조달한다. |
| 4 | Rough Machining | Mold Base, Core, Cavity, Plate를 황삭 가공한다. |
| 5 | 열처리·응력제거 | 열처리, Stress Relief, 경도검사와 변형을 관리한다. |
| 6 | Finish Machining·EDM·연마 | 정삭, EDM, WEDM, Grinding, Polishing을 수행한다. |
| 7 | 부품검사·Fit Check | Core/Cavity, Insert, Slide, Pin의 치수와 조립 간섭을 확인한다. |
| 8 | 금형 조립·배선·냉각 연결 | 금형 Assembly, Sensor, Hot Runner, 냉각회로, 유압·공압을 연결한다. |
| 9 | Tryout T0/T1 | 시사출 또는 시타발, Sample, 치수, 외관, Cycle, Mold Action을 확인한다. |
| 10 | 수정·보완 Loop | Tryout 결과에 따라 설계·가공·연마·조립을 반복 보완한다. |
| 11 | 고객승인·양산이관 | Sample 승인, 조건표, 보전기준, Spare Part와 양산이관 자료를 완료한다. |

## 7.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 제품사양·금형 요구 기준선 | 确认产品图、收缩率、Cavity、寿命、Cycle Time和量产条件。 |
| 2 | 금형·치공구 설계 | 设计Parting、Runner/Gate、Cooling、Insert、Slide、Ejector和Jig结构。 |
| 3 | 소재·표준품 조달 | 采购模具钢、Mold Base、标准件、Hot Runner、Sensor和Cylinder。 |
| 4 | Rough Machining | 对Mold Base、Core、Cavity、Plate进行粗加工。 |
| 5 | 열처리·응력제거 | 管理热处理、Stress Relief、硬度检查和变形。 |
| 6 | Finish Machining·EDM·연마 | 执行精加工、EDM、WEDM、Grinding和Polishing。 |
| 7 | 부품검사·Fit Check | 确认Core/Cavity、Insert、Slide、Pin的尺寸和装配干涉。 |
| 8 | 금형 조립·배선·냉각 연결 | 连接模具Assembly、Sensor、Hot Runner、冷却回路、液压/气动。 |
| 9 | Tryout T0/T1 | 执行试模/试冲，确认Sample、尺寸、外观、Cycle和Mold Action。 |
| 10 | 수정·보완 Loop | 根据试模结果循环修正设计、加工、研磨和装配。 |
| 11 | 고객승인·양산이관 | 完成样件批准、条件表、保养标准、备件和量产移交资料。 |

## 7.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항 기준선 | 금형·치공구·전용기의 고객 사양, 성능조건, 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 형상·Revision 관리 | 설계도면, BOM, 공정계획, Software/Parameter Revision의 일치성을 관리한다. | 2,3 | process_step |
| 3 | 조달·자재 추적 | 장납기품, 핵심 소재, 외주품의 승인, 납기, Lot/Serial과 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 제작·조립 이력 | 소재, Machine/Program, Tool/Jig, 작업자, 공정조건과 재작업 이력을 Serial/Module 기준으로 연결한다. | 5,8 | process_step |
| 5 | 검사 Gate | Gate 공정 #9의 검사·시험 결과, NCR, Repair, Re-test를 인수기준과 연결한다. | 9 | process_step |
| 6 | FAT/SAT·인수 | FAT/SAT, 고객 Witness, Punch Close, As-built 또는 최종 인수자료를 통제한다. | 10,11 | process_step |
| 7 | 보안·IP·접근권한 | 고객 IP, 방산·수출통제 자료, 공정 Recipe와 협력사 접근권한을 프로젝트별로 격리·감사한다. |  | industry |

## 7.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求基线 | 将模具·工装·专机的客户规格、性能条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 构型·版本管理 | 管理设计图纸、BOM、工艺计划和Software/Parameter Revision的一致性。 | 2,3 | process_step |
| 3 | 采购·材料追踪 | 跟踪长周期物料、关键材料、外协件的批准、交期、Lot/Serial和替代件应用。 | 3,4 | process_step |
| 4 | 制造·装配履历 | 按Serial/Module连接材料、Machine/Program、Tool/Jig、作业员、工艺条件和返工履历。 | 5,8 | process_step |
| 5 | 检验Gate | 将Gate工序#9的检验/测试结果、NCR、Repair、Re-test连接到验收标准。 | 9 | process_step |
| 6 | FAT/SAT·验收 | 控制FAT/SAT、客户Witness、Punch关闭、As-built或最终验收资料。 | 10,11 | process_step |
| 7 | 安全·IP·访问权限 | 按项目隔离并审计客户IP、防务/出口管制资料、工艺Recipe和合作方访问权限。 |  | industry |

## 7.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Requirement | process |  |  | project_id, drawing_revision |
| 2 | Design | process |  |  | project_id, drawing_revision |
| 3 | Procurement | process |  |  | project_id, drawing_revision |
| 4 | Machining | process |  |  | project_id, mold_id, drawing_revision |
| 5 | Heat Treat | process |  |  | project_id, mold_id, steel_heat_no |
| 6 | EDM/Finish | process |  |  | project_id, mold_id, NC_program |
| 7 | Inspection | process |  |  | project_id, mold_id, electrode_id |
| 8 | Assembly | process |  |  | project_id, mold_id, heat_treat_result |
| 9 | Tryout Gate | gate |  | 7,8,10 | heat_treat_result, sample_result |
| 10 | Correction Loop | process | Tryout Correction Loop |  | project_id, mold_id, tryout_no |
| 11 | Handover | process |  |  | project_id, mold_id, sample_result |

## 7.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Requirement | process |  |  | project_id, drawing_revision |
| 2 | Design | process |  |  | project_id, drawing_revision |
| 3 | Procurement | process |  |  | project_id, drawing_revision |
| 4 | Machining | process |  |  | project_id, mold_id, drawing_revision |
| 5 | Heat Treat | process |  |  | project_id, mold_id, steel_heat_no |
| 6 | EDM/Finish | process |  |  | project_id, mold_id, NC_program |
| 7 | Inspection | process |  |  | project_id, mold_id, electrode_id |
| 8 | Assembly | process |  |  | project_id, mold_id, heat_treat_result |
| 9 | Tryout Gate | gate |  | 7,8,10 | heat_treat_result, sample_result |
| 10 | Correction Loop | process | Tryout Correction Loop |  | project_id, mold_id, tryout_no |
| 11 | Handover | process |  |  | project_id, mold_id, sample_result |

## 7.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 9 | 1 | Inspection/Test |
| 9 | 2 | NCR Review |
| 9 | 3 | Repair/Re-test |
| 11 | 1 | Customer Acceptance |
| 11 | 2 | Punch Close |
| 11 | 3 | Handover |

## 7.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 9 | 1 | 检验/测试 |
| 9 | 2 | NCR评审 |
| 9 | 3 | 维修/复测 |
| 11 | 1 | 客户验收 |
| 11 | 2 | Punch关闭 |
| 11 | 3 | 交付 |

## 7.9 data_capture_points

```yaml
- project_id
- mold_id
- tooling_serial
- cavity_no
- drawing_revision
- steel_heat_no
- NC_program
- electrode_id
- heat_treat_result
- EDM_program
- tryout_no
- sample_result
- correction_action
- handover_status
```


# 8. A08 — 대형 구조물·특수 제작

```yaml
subindustry_code: A08
legacy_slug: large_structure_fabrication
label_ko: 대형 구조물·특수 제작
label_zh: 大型结构件·特殊制造
label_en: ""
label_ja: ""
routing: RT_PROJECT
expression_tier: P2_PROJECT_WBS
routing_description_ko: >
  대형 구조물·특수 제작은 Plate/Beam 소재, 절단, Fit-up, Welding, NDT, Coating, Trial Assembly, Site Erection을 Heat/Weld/Module 기준으로 연결한다.
routing_description_zh: >
  大型结构件/特殊制造按Heat/Weld/Module连接Plate/Beam材料、切割、组对、焊接、NDT、涂装、预拼装和现场安装。
```

## 8.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 계약·도면·제작 기준선 | 구조사양, 하중조건, 용접규격, 검사·도장 기준과 인수조건을 확정한다. |
| 2 | 상세도·Cutting Plan Release | Shop Drawing, Nesting, Cutting Plan, Weld Map과 검사계획을 Release한다. |
| 3 | Plate·Beam 입고·식별 | Plate/Beam Heat No., Mill Sheet, 규격, 표면상태와 보관위치를 확인한다. |
| 4 | 절단·개선·가공 | NC Cutting, Beveling, Drilling, Bending, Marking을 수행한다. |
| 5 | Fit-up·Tack Welding | 부재를 Jig/Fixture에 맞춰 조립하고 Fit-up Gap, Alignment를 확인한다. |
| 6 | Main Welding | WPS, 용접사 자격, 용접재 Lot, 예열·층간온도와 Weld ID를 관리한다. |
| 7 | NDT·치수검사 | UT/RT/MT/PT, 치수검사, 변형교정, NCR·Repair를 수행한다. |
| 8 | Surface Treatment·Coating | Blast, Primer, Coating, DFT, Curing, 환경조건을 관리한다. |
| 9 | Trial Assembly·Module화 | 대형 구조물을 Trial Assembly하고 Bolt Hole, Interface, Match Mark를 확인한다. |
| 10 | 출하·현장 반입 | 대형 운송, Lifting Point, 보존, 현장 반입과 Staging 위치를 관리한다. |
| 11 | Site Erection·Final Inspection | 현장 설치, Alignment, Bolt/Weld 연결, Final Inspection과 As-built를 완료한다. |

## 8.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 계약·도면·제작 기준선 | 确认结构规格、荷载条件、焊接规范、检验/涂装标准和验收条件。 |
| 2 | 상세도·Cutting Plan Release | 发布Shop Drawing、Nesting、Cutting Plan、Weld Map和检验计划。 |
| 3 | Plate·Beam 입고·식별 | 确认Plate/Beam Heat No.、Mill Sheet、规格、表面状态和保管位置。 |
| 4 | 절단·개선·가공 | 执行NC Cutting、Beveling、Drilling、Bending和Marking。 |
| 5 | Fit-up·Tack Welding | 将构件在Jig/Fixture上组对并确认Fit-up Gap和Alignment。 |
| 6 | Main Welding | 管理WPS、焊工资格、焊材Lot、预热/层间温度和Weld ID。 |
| 7 | NDT·치수검사 | 执行UT/RT/MT/PT、尺寸检查、变形矫正、NCR/Repair。 |
| 8 | Surface Treatment·Coating | 管理Blast、Primer、Coating、DFT、Curing和环境条件。 |
| 9 | Trial Assembly·Module화 | 对大型结构件进行预拼装并确认Bolt Hole、Interface和Match Mark。 |
| 10 | 출하·현장 반입 | 管理大型运输、Lifting Point、保存、现场到货和Staging位置。 |
| 11 | Site Erection·Final Inspection | 完成现场安装、Alignment、Bolt/Weld连接、Final Inspection和As-built。 |

## 8.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 요구사항 기준선 | 대형 구조물·특수 제작의 고객 사양, 성능조건, 인수기준을 프로젝트 기준선으로 고정한다. | 1,2 | process_step |
| 2 | 형상·Revision 관리 | 설계도면, BOM, 공정계획, Software/Parameter Revision의 일치성을 관리한다. | 2,3 | process_step |
| 3 | 조달·자재 추적 | 장납기품, 핵심 소재, 외주품의 승인, 납기, Lot/Serial과 대체품 적용을 추적한다. | 3,4 | process_step |
| 4 | 제작·조립 이력 | 소재, Machine/Program, Tool/Jig, 작업자, 공정조건과 재작업 이력을 Serial/Module 기준으로 연결한다. | 5,6 | process_step |
| 5 | 검사 Gate | Gate 공정 #7의 검사·시험 결과, NCR, Repair, Re-test를 인수기준과 연결한다. | 7 | process_step |
| 6 | FAT/SAT·인수 | FAT/SAT, 고객 Witness, Punch Close, As-built 또는 최종 인수자료를 통제한다. | 10,11 | process_step |
| 7 | 보안·IP·접근권한 | 고객 IP, 방산·수출통제 자료, 공정 Recipe와 협력사 접근권한을 프로젝트별로 격리·감사한다. |  | industry |

## 8.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 需求基线 | 将大型结构件·特殊制造的客户规格、性能条件和验收标准固定为项目基线。 | 1,2 | process_step |
| 2 | 构型·版本管理 | 管理设计图纸、BOM、工艺计划和Software/Parameter Revision的一致性。 | 2,3 | process_step |
| 3 | 采购·材料追踪 | 跟踪长周期物料、关键材料、外协件的批准、交期、Lot/Serial和替代件应用。 | 3,4 | process_step |
| 4 | 制造·装配履历 | 按Serial/Module连接材料、Machine/Program、Tool/Jig、作业员、工艺条件和返工履历。 | 5,6 | process_step |
| 5 | 检验Gate | 将Gate工序#7的检验/测试结果、NCR、Repair、Re-test连接到验收标准。 | 7 | process_step |
| 6 | FAT/SAT·验收 | 控制FAT/SAT、客户Witness、Punch关闭、As-built或最终验收资料。 | 10,11 | process_step |
| 7 | 安全·IP·访问权限 | 按项目隔离并审计客户IP、防务/出口管制资料、工艺Recipe和合作方访问权限。 |  | industry |

## 8.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id |
| 2 | Engineering | process |  |  | project_id |
| 3 | Material | process |  |  | project_id |
| 4 | Cutting | process |  |  | project_id, structure_id, beam_heat_no |
| 5 | Fit-up | process |  |  | project_id, structure_id, cutting_plan |
| 6 | Welding | process |  |  | project_id, structure_id, weld_id |
| 7 | Gate | gate |  | 5,6,8 | NDT_result, dimension_result, trial_assembly_result |
| 8 | Coating | process |  |  | project_id, structure_id, WPS_id |
| 9 | Trial Assembly | process |  |  | project_id, structure_id, NDT_result |
| 10 | Logistics | process |  |  | project_id, structure_id, dimension_result |
| 11 | Site | process |  |  | project_id, structure_id, coating_DFT |

## 8.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Contract | process |  |  | project_id |
| 2 | Engineering | process |  |  | project_id |
| 3 | Material | process |  |  | project_id |
| 4 | Cutting | process |  |  | project_id, structure_id, beam_heat_no |
| 5 | Fit-up | process |  |  | project_id, structure_id, cutting_plan |
| 6 | Welding | process |  |  | project_id, structure_id, weld_id |
| 7 | Gate | gate |  | 5,6,8 | NDT_result, dimension_result, trial_assembly_result |
| 8 | Coating | process |  |  | project_id, structure_id, WPS_id |
| 9 | Trial Assembly | process |  |  | project_id, structure_id, NDT_result |
| 10 | Logistics | process |  |  | project_id, structure_id, dimension_result |
| 11 | Site | process |  |  | project_id, structure_id, coating_DFT |

## 8.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 7 | 1 | Inspection/Test |
| 7 | 2 | NCR Review |
| 7 | 3 | Repair/Re-test |
| 11 | 1 | Customer Acceptance |
| 11 | 2 | Punch Close |
| 11 | 3 | Handover |

## 8.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 7 | 1 | 检验/测试 |
| 7 | 2 | NCR评审 |
| 7 | 3 | 维修/复测 |
| 11 | 1 | 客户验收 |
| 11 | 2 | Punch关闭 |
| 11 | 3 | 交付 |

## 8.9 data_capture_points

```yaml
- project_id
- structure_id
- module_id
- plate_heat_no
- beam_heat_no
- cutting_plan
- weld_id
- welder_id
- WPS_id
- NDT_result
- dimension_result
- coating_DFT
- trial_assembly_result
- site_erection_status
```



---

# 9. 변경 요약

| 코드 | 변경 요약 |
|---|---|
| A01 | EPC 공통 14단계가 아니라 FEED/IFC/Spool/Skid/Site/Commissioning 중심의 프로젝트 공정 표현으로 재작성 |
| A02 | 주문형 장비의 대형가공·유압·전장·Software·FAT 흐름을 별도 표현 |
| A03 | 반도체·디스플레이 장비의 Chamber/Vacuum/Gas/Particle/SECS-GEM/FAT/SAT 반영 |
| A04 | 배터리·태양광 장비의 R2R/Coating/Dry Room/Formation/EL-IV/Sample Run 반영 |
| A05 | 조선·해양플랜트의 Block/Dock/Outfitting/Paint/Sea Trial 공정 언어 반영 |
| A06 | 항공우주·방산의 MBD/MBSE/Special Process/FAI/Qualification/보안 추적 반영 |
| A07 | 기존 미정의 legacy_slug를 `mold_tooling_dedicated_machine`으로 제안하고 Tryout Correction Loop 명시 |
| A08 | Plate/Beam/Fit-up/Welding/NDT/Coating/Site Erection 중심 구조 반영 |

---

# 10. Self-check

```text
[x] A01~A08 전수, slug당 §N.1~§N.9 섹션 완비
[x] §0 오기 수정: control_points_ko/zh는 R2 자동생성임을 명시
[x] control_points_detail에 category 열 전건 작성
[x] step_expression ko/zh 행 수 = process_steps 행 수
[x] A산업 P2_PROJECT_WBS 표현: module + trace_keys 전 step 작성
[x] role=gate ≥1 전 slug 반영
[x] A07 loop_hint 반영
[x] trace_keys는 slug별 data_capture_points의 부분집합으로 작성
[x] ko/zh process step·step_expression·step_refs·scope 동형 작성
[x] en/ja 섹션·문단 없음
```

---

# 11. 참고 기준

- `A1_CH3_B_process_detail_datapack_refactor_instruction_2026-07-06.md`
- 기존 A산업 A1 Ch3 v0.1 데이터팩
- Step1.5 74개 세부산업 기준
- EPC/건설: 모듈화, 프리패브, BIM, 디지털 트윈, AI/로봇 기반 현장 가시화
- 반도체 장비: AI/HPC 투자에 따른 WFE·장비 수요, 고정밀 장비 검증, Recipe/Interface 관리
- 배터리 장비: 전극 제조 장비, 건식 전극, Slot-die coating 실시간 제어
- 조선: Shipyard 4.0, Pipe Spool 추적, 설계-작업장 Digital Thread
- 항공우주·방산: MBD/MBSE, Digital FAI, AS9102형 FAI, Qualification
- 금형·구조물: Conformal Cooling, 용접 자동화, AI 품질검사, Green Steel·소재 추적
