# A1 Ch3 C산업 공정상세 데이터팩 v0.3 — ko/zh (Enhanced)

> **대상 산업:** C. 전자·정밀 이산 제조 (High Mix / Job Shop + Assembly Line)  
> **작성일:** 2026-07-06  
> **목적:** A1 Ch3 `process_detail_v1.json` 백필 전 검토용 MD 정본 초안  
> **범위:** C01~C08, ko/zh만 작성. JSON·코드·스크립트 적용은 본 파일 범위 밖.  
> **작성 기준:** B산업 v0.3 리팩 지시서의 런타임 소비 필드(`module`, `role`, `gate_for`, `loop_hint`, `trace_keys`, `operations`, `category`)를 C산업에 적용.

## 0. 적용 원칙

| 항목 | 원칙 |
|---|---|
| 언어 | `ko`, `zh`만 작성. `label_en`, `label_ja`는 공백. |
| runtime target | A1 Ch3 pflow가 소비하는 표현 메타를 MD에 명시한다. |
| control_points | 별도 `control_points_ko/zh` bullet 작성 금지. `control_points_detail_ko/zh`에서 자동 생성 전제. |
| routing | C산업은 SMT/Consumer 일부는 `RT_LINE`, PCB·EMS·정밀모듈은 `RT_JOBSHOP` 중심으로 작성한다. |
| trace_keys | slug별 `data_capture_points`의 부분집합만 사용한다. |
| gate | 검사·시험·출하판정 단계는 `role: gate`와 `gate_for`를 명시한다. |
| en/ja | 본 MD에는 en/ja 공정·관리점 섹션을 작성하지 않는다. |

## 0.1 C산업 공통 해석

전자·정밀 이산 제조는 다품종·소량, 잦은 모델 전환, 고객별 BOM/Revision, SMT·조립·검사·캘리브레이션이 결합된 제조 영역이다. 단일 설비 효율보다 **BOM/ECN 정확성, 자재·Serial genealogy, 라인 전환 안정성, AOI/X-ray/ICT/FCT Gate, Firmware·Label 매칭**이 Ch3 공정도에서 더 중요하다.

## 0.2 slug별 변경 요약

| code | slug | routing | expression_tier | 핵심 표현 |
|---|---|---|---|---|
| C01 | `pcb_pcba` | RT_JOBSHOP | P9_PRECISION_JOBSHOP | Panel/Lot 기반 PCB Fab + E-test Gate |
| C02 | `smt_assembly` | RT_LINE | P3_LABOR_ASSEMBLY | SPI → Placement → Reflow → AOI/X-ray → ICT/FCT |
| C03 | `ems` | RT_JOBSHOP | P3_LABOR_ASSEMBLY | 고객 Program/ECN 격리 + Box-build genealogy |
| C04 | `electronic_modules` | RT_JOBSHOP | P3_LABOR_ASSEMBLY | 모듈 serial + 접착·체결·Calibration |
| C05 | `industrial_electronics` | RT_JOBSHOP | P3_LABOR_ASSEMBLY | 제어사양·Wiring·Firmware·Safety/FAT Gate |
| C06 | `telecom_equipment` | RT_JOBSHOP | P3_LABOR_ASSEMBLY | RF/Optical/Thermal + BER/EVM Gate |
| C07 | `consumer_electronics` | RT_LINE | P3_LABOR_ASSEMBLY | SKU/지역/Firmware/Calibration/Label 매칭 |
| C08 | `precision_modules` | RT_JOBSHOP | P3_LABOR_ASSEMBLY | Clean + Active Alignment loop + Stress Gate |


# 1. C01 — PCB 제조

```yaml
subindustry_code: C01
legacy_slug: pcb_pcba
label_ko: PCB 제조
label_zh: PCB制造
label_en: ""
label_ja: ""
routing: RT_JOBSHOP
expression_tier: P9_PRECISION_JOBSHOP
routing_description_ko: >
  PCB 제조는 CAM/DFM, 내층·적층·드릴·도금·외층·솔더마스크·표면처리·전기검사를 Lot/Panel 단위로 연결해야 한다.
routing_description_zh: >
  PCB制造需要将CAM/DFM、内层、压合、钻孔、电镀、外层、阻焊、表面处理和电测按Lot/Panel连接起来。
```

## 1.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | CAM·DFM·Gerber 기준선 | Gerber/ODB++/IPC-2581, Stack-up(층간 두께·유전율), Drill file, Impedance(임피던스 타겟값 ±10%), Panelization 기준을 확정한다. 고객 CAM data를 GenFlex/InCAM 등 CAM S/W로 수신하여 DFM Rule Check(Acid trap, annular ring, solder bridge)를 수행하며, AOI 기준 프로그램을 생성한다. Panel/Lot 단위 revision 관리가 Gate 기준이 된다. |
| 2 | 원자재·적층판 준비 | Laminate(IT-180/FR4/High-Tg), Copper foil(1/2oz~2oz, 저조도), Prepreg(1080/2116/7628), Core lot와 보관조건(온도 20±3℃, 습도 50±5%RH)을 확인한다. Lot/Batch별 Copper thickness, peel strength, resin content(%)를 검증하고, IPC-4101 규격 적합성을 확인한다. |
| 3 | 내층 이미지·노광·에칭 | Inner layer imaging(Dry film LDI 또는 직접묘화), develop, etch(염화동 에칭, pH 8.0~8.5, 온도 50±3℃), AOI(Orbotech/Optical Dynamics 등)로 line break, short, pinhole, under-etch를 판정한다. 층별 결함 분류(L/S ±10μm 기준) 후 재작업 이력을 panel_id에 기록한다. |
| 4 | 적층·라미네이션 | Layer stack, lay-up(Brown oxide 처리 후), press cycle(가열속도 2~5℃/min, 최대온도 180~200℃, 유지시간 60~120분, 압력 300~500psi), resin flow(%)와 registration(post-lamination x-ray target 측정, ±75μm)을 관리한다. Void 발생 시 해당 lot 폐기 또는 MRB 판정한다. |
| 5 | 드릴·디스미어 | CNC 드릴(Hitachi Via Mechanics/Schmoll 등, ±25μm 정밀도), laser drilling(CO₂/UV, blind via φ100~150μm), desmear(플라즈마 또는 습식, permanganate 에칭, 75~90℃). Drill wear(1,000~3,000 hit마다 교체), hole wall quality(IPC-600 Class 2/3), nailhead/overhang 여부를 관리한다. |
| 6 | 동도금·Via 형성 | Electroless copper(화학동, 두께 0.5~1.0μm) 후 electrolytic copper plating(전해동, 두께 20~35μm, 전류밀도 20~30ASF, 온도 25±2℃). Via filling(수직형 도금라인)으로 through-hole/via 도통성(저항 <1mΩ)과 thermal shock 내구성을 확보한다. Bath 분석(Cl⁻, Cu²⁺, H₂SO₄ 농도)은 4시간마다 수행한다. |
| 7 | 외층 이미지·패턴 도금·에칭 | Outer layer imaging(LDI, ±15μm 정밀도), pattern plating(Cu 25~35μm, Sn 5~8μm), etch factor(≥2.5), 최종 line/space(고밀도 50/50μm~75/75μm)를 관리한다. AOI로 short/open/necking을 검출하고 defect code를 등록한다. |
| 8 | 솔더마스크·실크·표면처리 | Solder mask(액상 PS/Photo Imageable, 두께 15~30μm, UV 경화 1,000~2,000mJ/cm²), legend printing(잉크 경화, 150℃ 30분). 표면처리는 HASL(260~270℃, 수평형), ENIG(Au 0.05~0.15μm, Ni 3~6μm, 온도 82℃, pH 4.5~5.0), OSP(액상 유기보호막, 40℃ 60~90초) 조건을 IPC-4552/4554 기준으로 관리한다. |
| 9 | 전기검사·임피던스 Gate | E-test(베드오브네일즈 또는 플라잉프로브, 200~500V 절연저항 측정), impedance coupon(TDR 측정, 타겟 ±5~10%), opens/shorts 판정. AOI로 solder mask coverage 확인, X-ray(적층 정렬) 보조 검사. Gate pass 조건 충족 시만 후속 공정 이동. Fail 시 MRB 회부 후 재작업 또는 폐기. |
| 10 | 최종검사·출하 | 외관(육안 + 10~40x 현미경), 치수(CCD 측정기 ±10μm), CoC, 포장(vacuum pack + desiccant, ESD bag), Label(고객 규격 lot/panel label)과 고객 규격 적합성을 확인한다. 출하검사 AQL 기준(AQL=0.65, MIL-STD-1916)에 따라 sampling 검증. |

## 1.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | CAM/DFM/Gerber基准 | 确认Gerber/ODB++/IPC-2581、叠构(层厚/介电常数)、钻孔文件、阻抗(目标值±10%)和拼板基准。用GenFlex/InCAM等CAM软件接收客户数据，执行DFM规则检查(Acid trap、annular ring、solder bridge)，生成AOI基准程序。以Panel/Lot为单位的版本管理作为Gate基准。 |
| 2 | 原材料/覆铜板准备 | 确认Laminate(IT-180/FR4/High-Tg)、铜箔(1/2oz~2oz、低粗度)、Prepreg(1080/2116/7628)、Core lot和存储条件(温度20±3℃、湿度50±5%RH)。按Lot/Batch验证铜厚、peel strength、树脂含量(%)，确认IPC-4101规格符合性。 |
| 3 | 内层成像/曝光/蚀刻 | 执行内层成像(干膜LDI或直接描绘)、显影、蚀刻(氯化铜蚀刻，pH 8.0~8.5，温度50±3℃)、AOI(Orbotech/Optical Dynamics等)判定line break、short、pinhole和under-etch。按层别缺陷分类(L/S ±10μm基准)后将返工履历记录到panel_id。 |
| 4 | 叠层/压合 | 管理Layer stack、lay-up(棕化处理后)、压合曲线(升温速度2~5℃/min、最高温度180~200℃、保温时间60~120分钟、压力300~500psi)、树脂流动(%)和对位(压合后x-ray target测量，±75μm)。发生void时对应lot报废或MRB判定。 |
| 5 | 钻孔/除胶渣 | CNC钻孔(Hitachi Via Mechanics/Schmoll等，±25μm精度)、激光钻孔(CO₂/UV，盲孔φ100~150μm)、除胶渣(等离子或湿式高锰酸盐蚀刻，75~90℃)。管理钻针磨耗(每1,000~3,000hit更换)、孔壁品质(IPC-600 Class 2/3)和nailhead/overhang。 |
| 6 | 铜电镀/Via形成 | 化学铜(沉铜，厚度0.5~1.0μm)后电解镀铜(厚度20~35μm，电流密度20~30ASF，温度25±2℃)。通过Via filling(垂直型电镀线)确保通孔/Via导通性(电阻<1mΩ)和热冲击耐久性。每4小时执行Bath分析(Cl⁻、Cu²⁺、H₂SO₄浓度)。 |
| 7 | 外层成像/图形电镀/蚀刻 | 外层成像(LDI，±15μm精度)、图形电镀(Cu 25~35μm，Sn 5~8μm)、蚀刻因子(≥2.5)、最终线宽线距(高密度50/50μm~75/75μm)。用AOI检出short/open/necking并登记缺陷代码。 |
| 8 | 阻焊/字符/表面处理 | 阻焊(液态PS/感光型，厚度15~30μm，UV固化1,000~2,000mJ/cm²)、字符(油墨固化，150℃ 30分钟)。按IPC-4552/4554标准管理HASL(260~270℃，水平型)、ENIG(Au 0.05~0.15μm，Ni 3~6μm，温度82℃，pH 4.5~5.0)、OSP(液态有机保护膜，40℃ 60~90秒)等条件。 |
| 9 | 电测/阻抗Gate | E-test(针床或飞针，200~500V绝缘电阻测量)、阻抗coupon(TDR测量，目标±5~10%)、开短路判定。AOI确认阻焊覆盖、X-ray辅助检查(叠层对位)。仅通过Gate条件后移入后续工序。Fail时转MRB后返工或报废。 |
| 10 | 终检/出货 | 确认外观(目视+10~40x显微镜)、尺寸(CCD测量仪±10μm)、CoC、包装(vacuum pack+desiccant、ESD bag)、标签(客户规格lot/panel标签)和客户规格符合性。出货检验按AQL标准(AQL=0.65，MIL-STD-1916)抽样验证。 |

## 1.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | DFM 기준선 | Gerber revision, Stack-up, impedance, panelization 변경을 승인 전 제조 투입하지 않는다. CAM tool에서 DFM Rule Check 결과를 리포트로 출력하여 설계·제조 승인을 획득한다. 측정 주기: NPI 및 ECO 발생 시 매번. 이상 시 ECR/ECO 프로세스로 회부. | 1 | process_step |
| 2 | 자재·Lot 추적 | Laminate, copper foil, prepreg lot를 panel_id와 연결해 field issue 시 역추적 가능하게 한다. 입고 시 IPC-4101 인증서와 peel strength(≥6lb/in), Tg 값을 검증하며, 배치별 SPC 관리. 측정 주기: Every Lot. 이상 시 자재 격리 → Supplier SCAR 발행. | 2,4 | process_step |
| 3 | 내층 품질 | Inner layer AOI defect와 재작업 이력을 panel/layer 단위로 남긴다. AOI 검사(Orbotech/Optical Dynamics)는 100% 전수 검사, defect code 분류(A-class→재작업, B-class→MRB). 측정 주기: Every Panel. 관리 기준: L/S ±10μm, short/open zero tolerance. | 3 | process_step |
| 4 | 적층 정합 | Press cycle, registration, post-lamination X-ray shift, resin flow, void 이슈를 적층 lot와 연결한다. X-ray target 측정(±75μm)으로 layer-to-layer 정합 검증. Void > IPC Class 기준 시 MRB. 측정 주기: Every Batch의 선행 3장 → 정상 시 Every 5th Lot. | 4 | process_step |
| 5 | 드릴·Via 품질 | Drill wear(1,000~3,000hit 교체 기준), hole wall quality(IPC-600 Class 2/3), desmear(permanganate 75~90℃), via reliability를 검사 결과와 연결한다. Microsection(시작/종료/고장 발생 시)으로 hole wall roughness ≤25μm 확인. 측정 주기: Every Drill Program 변경 시 + 주 1회 cross-section sampling. | 5,6 | process_step |
| 6 | 동도금 관리 | 도금 두께(20~35μm), 균일도(panel 내 ±10%), throwing power(T/P≥80%), bath 상태(Cu²⁺, Cl⁻, H₂SO₄ 농도)를 lot별로 관리한다. Bath 분석 4시간마다 수행. XRF 측정기로 동도금 두께 측정. 이상 시 bath 교체/보충 후 재검증. 측정 주기: Every Lot XRF + 4시간 Bath. | 6 | process_step |
| 7 | 외층 패턴 품질 | Line/space(고밀도 50/50μm~75/75μm), etch factor(≥2.5), solder bridge 가능성을 AOI defect code와 연결한다. AOI 전수 검사 + SEM cross-section(시작 lot 1장). 측정 주기: Every Panel AOI + Lot 시작 시 SEM. 이상 시 etch line 조건 조정 → 재작업. | 7,8 | process_step |
| 8 | 최종 Gate | E-test(open/short/절연저항), impedance coupon(TDR, 타겟 ±5~10%), appearance 판정 후 출하 승인과 CoC를 생성한다. Gate pass율 < 95% 시 전체 lot MRB Hold. 측정 주기: Every Panel E-test + Coupon별 Impedance. 이상 시 MRB → 재작업/Scrap 판정 → CoC 발행 전 재검증. | 9,10 | process_step |

## 1.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | DFM基准 | Gerber版本、叠构、阻抗和拼板变更在批准前不得投产。CAM工具输出DFM规则检查报告，获取设计/制造批准。测量周期：NPI及ECO发生时每次。异常时转ECR/ECO流程。 | 1 | process_step |
| 2 | 材料/Lot追踪 | 将覆铜板、铜箔、Prepreg lot与panel_id连接，便于现场问题逆向追溯。入库时验证IPC-4101证书、peel strength(≥6lb/in)和Tg值，按批次SPC管理。测量周期：Every Lot。异常时隔离材料→发出Supplier SCAR。 | 2,4 | process_step |
| 3 | 内层品质 | 以内层AOI缺陷和返工履历按panel/layer保留。AOI检查(Orbotech/Optical Dynamics)100%全检，缺陷代码分类(A-class→返工，B-class→MRB)。测量周期：Every Panel。管理基准：L/S ±10μm，short/open零容忍。 | 3 | process_step |
| 4 | 压合对位 | 将压合曲线、对位、压合后X-ray偏移、树脂流动和void问题连接到压合lot。X-ray target测量(±75μm)验证层间对位。Void超出IPC Class标准时MRB。测量周期：每批次前3张→正常后每5th Lot。 | 4 | process_step |
| 5 | 钻孔/Via品质 | 将钻针磨耗(1,000~3,000hit更换标准)、孔壁品质(IPC-600 Class 2/3)、除胶渣(高锰酸盐75~90℃)和via可靠性连接到检验结果。Microsection(开始/结束/故障发生时)确认hole wall roughness≤25μm。测量周期：每Drill Program变更+每周1次cross-section sampling。 | 5,6 | process_step |
| 6 | 铜电镀管理 | 按lot管理镀铜厚度(20~35μm)、均匀性(panel内±10%)、深镀能力(T/P≥80%)和药水状态(Cu²⁺、Cl⁻、H₂SO₄浓度)。每4小时执行Bath分析。用XRF测量仪测量镀铜厚度。异常时更换/补充Bath后重新验证。测量周期：Every Lot XRF+4小时Bath。 | 6 | process_step |
| 7 | 外层图形品质 | 将线宽线距(高密度50/50μm~75/75μm)、蚀刻因子(≥2.5)和焊桥风险连接到AOI缺陷代码。AOI全检+SEM cross-section(开始lot 1张)。测量周期：Every Panel AOI+Lot开始时SEM。异常时调整蚀刻线条件→返工。 | 7,8 | process_step |
| 8 | 最终Gate | E-test(open/short/绝缘电阻)、阻抗coupon(TDR，目标±5~10%)和外观判定后生成出货批准和CoC。Gate pass率<95%时全lot MRB Hold。测量周期：Every Panel E-test+Coupon别Impedance。异常时MRB→返工/Scrap判定→CoC发行前重新验证。 | 9,10 | process_step |

## 1.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | CAM | process |  |  | lot_id,panel_id,gerber_revision,customer_spec |
| 2 | Material | process |  |  | lot_id,material_lot,stackup_id |
| 3 | Inner Layer | process |  |  | panel_id,gerber_revision,line_space_result,defect_code |
| 4 | Lamination | process |  |  | panel_id,stackup_id,material_lot |
| 5 | Drill | process |  |  | panel_id,drill_program,defect_code |
| 6 | Plating | process |  |  | panel_id,plating_thickness,defect_code |
| 7 | Outer Layer | process |  |  | panel_id,line_space_result,defect_code |
| 8 | Finish | process |  |  | panel_id,soldermask_batch,surface_finish_result |
| 9 | Electrical Gate | gate |  | 3,4,5,6,7,8 | panel_id,impedance_result,etest_result,defect_code |
| 10 | Shipment | process |  |  | lot_id,panel_id,customer_spec,etest_result |

## 1.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | CAM | process |  |  | lot_id,panel_id,gerber_revision,customer_spec |
| 2 | Material | process |  |  | lot_id,material_lot,stackup_id |
| 3 | Inner Layer | process |  |  | panel_id,gerber_revision,line_space_result,defect_code |
| 4 | Lamination | process |  |  | panel_id,stackup_id,material_lot |
| 5 | Drill | process |  |  | panel_id,drill_program,defect_code |
| 6 | Plating | process |  |  | panel_id,plating_thickness,defect_code |
| 7 | Outer Layer | process |  |  | panel_id,line_space_result,defect_code |
| 8 | Finish | process |  |  | panel_id,soldermask_batch,surface_finish_result |
| 9 | Electrical Gate | gate |  | 3,4,5,6,7,8 | panel_id,impedance_result,etest_result,defect_code |
| 10 | Shipment | process |  |  | lot_id,panel_id,customer_spec,etest_result |

## 1.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 9 | 1 | E-test 판정 |
| 9 | 2 | Impedance coupon 확인 |
| 9 | 3 | MRB/Hold Release |
| 10 | 1 | CoC 생성 |
| 10 | 2 | 출하 Label 검증 |

## 1.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 9 | 1 | 电测判定 |
| 9 | 2 | 阻抗coupon确认 |
| 9 | 3 | MRB/Hold Release |
| 10 | 1 | 生成CoC |
| 10 | 2 | 出货标签验证 |

## 1.9 data_capture_points

```yaml
- lot_id
- panel_id
- gerber_revision
- material_lot
- stackup_id
- drill_program
- plating_thickness
- line_space_result
- soldermask_batch
- surface_finish_result
- impedance_result
- etest_result
- defect_code
- customer_spec
```

# 2. C02 — SMT·PCBA

```yaml
subindustry_code: C02
legacy_slug: smt_assembly
label_ko: SMT·PCBA
label_zh: SMT·PCBA
label_en: ""
label_ja: ""
routing: RT_LINE
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  SMT·PCBA는 Paste/SPI, Placement, Reflow, AOI/X-ray, ICT/FCT, 코팅·포장까지 라인 tact와 검사 Gate를 연결해야 한다.
routing_description_zh: >
  SMT/PCBA需要连接锡膏/SPI、贴装、回流、AOI/X-ray、ICT/FCT、涂覆和包装的线体节拍与检验Gate。
```

## 2.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | NPI·DFM·BOM 기준선 | BOM, AVL, PCB revision, stencil 설계(전해/레이저컷, 두께 0.1~0.15mm), placement program(Panasonic NPM/ASM SIPLACE/Samsung SM), fixture 설계, test coverage(ICT pin coverage ≥95%)를 확정한다. DFM Rule Check로 solder bridge/ tombstone risk 사전 차단. |
| 2 | 자재 수입·MSD·Kitting | Component lot(MLCC, IC, connector), feeder setup(8mm~44mm tape), MSD floor life(J-STD-033, Level 2a→168hr, Level 3→168hr, 초과 시 bake 125℃ 24hr), ESD(정전기 방지, 10⁶~10⁹Ω surface resistance)와 kit completeness(스캔 확인)를 관리한다. Lot별로 Moisture Barrier Bag(MBB) seal date를 track. |
| 3 | Stencil Printing·SPI | Solder paste lot(type 3/4 SAC305), stencil condition(전해연마 또는 나노코팅, aperture aspect ratio >0.66), printer setting(squeegee 속도 20~60mm/s, 압력 50~150N, gap 0mm), SPI(Koh Young 3D/ASM DEK)로 print offset(±50μm), volume(50~150%), height(paste height ratio 50~200%)를 100% 전수 측정. SPI fail 시 printer auto-clean/parameter adjust 후 재인쇄. |
| 4 | Pick & Place | 고속 칩 마운터(Panasonic NPM/ASM SIPLACE/Samsung EXCEDEN, 속도 40,000~120,000CPH)에서 feeder setup, nozzle(µm-level tip, 진공도 -60~-95kPa), placement program(component center XY ±30μm, θ ±0.1°)을 검증한다. Component barcode와 feeder position을 1:1 매칭하여 부품 혼입(Miss-pick) 방지. |
| 5 | Reflow | Profile 설정: 예열 150~200℃ 60~120초, soak 183℃ 이상 60~90초, peak 235~250℃(SAC305), cooling slope ≤4℃/s. 질소(N₂) 환경(산소농도 ≤1,000ppm) 적용. KIC/ECD 온도프로파일러로 board별 thermal history 저장(△T ≤5℃). 여유 시간 확보를 위한 Conveyor 속도 70~100cm/min. |
| 6 | AOI·X-ray Gate | Post-reflow AOI(Omron/Koh Young 3D, 10~20μm/pixel 해상도)로 missing, polarity, tombstone, bridge, solder volume을 100% 전수 검사. BGA/QFN/LGA 숨은 솔더조인트는 X-ray(AXI, Koh Young/Dage, 해상도 ≤10μm)로 void(%) 및 ball collapse 판정. Gate fail 시 repair(핫에어/진공 디솔더링)→재검사 loop. |
| 7 | THT·Selective Solder | 수삽: DIP, 커넥터, 대형 capacitor를 manual/workstation에서 삽입. Wave solder(flux spray, 예열 100~130℃, 솔더포 260~270℃, contact time 3~5초) 또는 selective solder(nozzle φ5~10mm, N₂ blanket, 솔더포 290~310℃) 적용. 작업자 bar-code scan으로 이력 관리. Touch-up 수리 인정 범위 정의. |
| 8 | ICT·FCT | ICT(Keysight/Teradyne, bed-of-nails, 1,000~5,000 test points)로 open/short, RLC 정밀 측정(±1% tolerance), diode polarity, IC power-on 확인. Flying probe(스페어 probe φ0.3~0.5mm, 128~512 pins)는 소량/다품종용. FCT(Keysight/National Instruments PXI)로 program download 후 기능 동작(ADC/DAC, 통신, 전원 sequence, LED) 검증. |
| 9 | Conformal Coating·Cure | 선택적 코팅(selective coating robot, Nordson/Asymtek, 속도 300~700mm/s, nozzle φ0.2~0.6mm) 또는 딥코팅. 코팅 두께 50~200μm(건조 후), coverage 100% 단자 제외, UV trace(형광제 첨가)로 검증. Cure: UV(1,000~3,000mJ/cm²) + 열(80℃ 30~60min). Masking tape 제거 확인(BGA/커넥터/POT 영역). |
| 10 | Final QA·Packing | Label(고객 spec, serial 2D barcode), serial 번호(고유 uni-serial 또는 MAC-based), customer packing spec(ESD tray/tube/tape&reel), 출하검사(AQL=0.65, MIL-STD-1916), COC, packing list. 최종 검사 스테이션에서 serial range, label count, 부자재(manual, accessory) 일치 확인. |

## 2.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | NPI/DFM/BOM基准 | 确认BOM、AVL、PCB版本、钢网设计(电解/激光切割，厚度0.1~0.15mm)、贴片程序(Panasonic NPM/ASM SIPLACE/Samsung SM)、治具设计、测试覆盖率(ICT pin coverage≥95%)。通过DFM规则检查预先阻断solder bridge/tombstone风险。 |
| 2 | 来料/MSD/Kitting | 管理元件lot(MLCC、IC、connector)、feeder setup(8mm~44mm tape)、MSD暴露时间(J-STD-033，Level 2a→168hr、Level 3→168hr，超时烘烤125℃ 24hr)、ESD(防静电，10⁶~10⁹Ω surface resistance)和套料齐套(扫码确认)。按Lot追踪Moisture Barrier Bag(MBB) seal date。 |
| 3 | 钢网印刷/SPI | 锡膏lot(type 3/4 SAC305)、钢网状态(电解抛光或纳米涂层，aperture aspect ratio>0.66)、印刷参数(squeegee速度20~60mm/s、压力50~150N、gap 0mm)、SPI(Koh Young 3D/ASM DEK)100%全测印刷偏移(±50μm)、体积(50~150%)和高度(50~200%)。SPI fail时自动清洗钢网/调整参数后重印。 |
| 4 | 贴片 | 高速贴片机(Panasonic NPM/ASM SIPLACE/Samsung EXCEDEN，速度40,000~120,000CPH)验证feeder setup、吸嘴(µm级tip，真空度-60~-95kPa)、贴片程序(component center XY ±30μm、θ ±0.1°)。将元件条码与feeder position一对一匹配防止错件。 |
| 5 | 回流焊 | Profile设定：预热150~200℃ 60~120秒、恒温183℃以上60~90秒、峰值235~250℃(SAC305)、冷却斜率≤4℃/s。氮气(N₂)环境(氧浓度≤1,000ppm)。用KIC/ECD温度记录仪保存每板thermal history(△T≤5℃)。传送速度70~100cm/min。 |
| 6 | AOI/X-ray Gate | 回流后AOI(Omron/Koh Young 3D，10~20μm/pixel分辨率)100%全检漏件、极性、立碑、连锡、锡量。BGA/QFN/LGA隐藏焊点用X-ray(AXI，Koh Young/Dage，分辨率≤10μm)判定void(%)和ball collapse。Gate fail时维修(热风/真空拆焊)→复检循环。 |
| 7 | 插件/选择焊 | 手插件：DIP、连接器、大电容在manual/workstation插入。波峰焊(flux喷涂、预热100~130℃、锡炉260~270℃、接触时间3~5秒)或选择焊(喷嘴φ5~10mm、N₂保护、锡炉290~310℃)。作业员扫码管理履历。定义补焊可接受范围。 |
| 8 | ICT/FCT | ICT(Keysight/Teradyne，针床式，1,000~5,000 test points)测量open/short、RLC(±1% tolerance)、二极管极性、IC上电确认。飞针(探针φ0.3~0.5mm，128~512 pins)用于小批量多品种。FCT(Keysight/National Instruments PXI)下载程序后验证功能(ADC/DAC、通信、电源时序、LED)。 |
| 9 | 三防漆/固化 | 选择性涂覆(selective coating robot，Nordson/Asymtek，速度300~700mm/s、喷嘴φ0.2~0.6mm)或浸涂。涂覆厚度50~200μm(干燥后)、coverage 100%端子除外、UV trace(荧光剂添加)验证。固化：UV(1,000~3,000mJ/cm²)+热(80℃ 30~60min)。确认masking tape去除(BGA/连接器/POT区域)。 |
| 10 | 终检/包装 | 标签(客户spec、serial 2D条码)、序列号(唯一uni-serial或MAC-based)、客户包装规格(ESD tray/tube/tape&reel)、出货检验(AQL=0.65、MIL-STD-1916)、COC、packing list。终检站确认serial range、标签数量和辅料(manual、accessory)一致。 |

## 2.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | NPI·BOM 기준 | BOM, AVL, PCB revision, stencil, program 불일치를 생산 전 차단한다. DFM Review 회의(ECN 시 매회) 후 WO Release 조건 충족 시만 생산 투입. 측정 주기: NPI/ECN 발생 시 매번. 이상 시 ECN Hold→재설계→재승인 loop. | 1 | process_step |
| 2 | 자재·MSD | Component lot, MSD floor life, feeder setup 오류를 board serial과 연결한다. MSD 만료일 초과 시 bake 125℃ 24hr 후 재검증, feeder setup은 scanner 1:1 매칭으로 검증. 측정 주기: Every Lot 입고 시 + 작업 전 scanner 확인. 이상 시 자재 격리 → Bake → 재사용 판정. | 2,4 | process_step |
| 3 | 인쇄 품질 | SPI volume(50~150%)/height(50~200%)/offset(±50μm) 이상을 리플로우 전 Hold 기준으로 사용한다. SPI 100% 전수 측정, Cpk≥1.33 관리. 3회 연속 Fail 시 stencil cleaning/stencil 교체. 측정 주기: Every Board(SPI 100% Inline). 이상 시 Auto-clean→재측정→stencil 검사. | 3 | process_step |
| 4 | 실장 품질 | Pick&place program, nozzle tip 상태, polarity, feeder miss를 AOI defect와 연결한다. 배치 불량(동일 feeder misspick 연속 3회) 발생 시 라인 Stop. 측정 주기: Every Board AOI. 이상 시 feeder 교체/보정→재검증. | 4,6 | process_step |
| 5 | 리플로우 이력 | Reflow profile(peak 235~250℃, soak 183℃ 60~90sec)과 paste lot를 board serial에 연결해 solder defect 분석에 사용한다. KIC/ECD profiler로 lot 시작·중간·종료별 profile 확인. △T >5℃ 시 재설정. 측정 주기: Lot 시작/변경 시 + 일 1회 정기. 이상 시 profile 재설정→재검사. | 5 | process_step |
| 6 | AOI/X-ray Gate | BGA/QFN hidden joint는 X-ray 판정으로 보완하고 gate 결과를 hold/release와 연결한다. AOI false call율 목표 ≤100PPM, X-ray sampling 비율(신규 BGA 100%, 양산 10~20%). 측정 주기: Every Board AOI + X-ray sampling per lot. 이상 시 MRB→repair/rework→gate 재판정. | 6 | process_step |
| 7 | 전기시험 Gate | ICT/FCT fail code, firmware version(Y/N 확인), calibration result를 board serial에 저장한다. ICT yield≥97%, FCT yield≥95% 관리 목표. 측정 주기: Every Board ICT+FCT. 이상 시 Diagnostic → Repair loop → Retest. | 8 | process_step |
| 8 | 출하 추적 | Label, serial(uni-serial/MAC), packing spec과 고객 출하 lot의 일치성을 검증한다. 출하 검사 AQL=0.65, serial range 중복/누락 zero tolerance. 측정 주기: Every Lot 출하 전 Sampling. 이상 시 전수 재검사 → label 재발행. | 10 | process_step |

## 2.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | NPI/BOM基准 | 在生产前阻断BOM、AVL、PCB版本、钢网和程序不一致。DFM Review会议(ECN时每次)后满足WO Release条件方可投产。测量周期：NPI/ECN发生时每次。异常时ECN Hold→重新设计→重新审批循环。 | 1 | process_step |
| 2 | 材料/MSD | 将元件lot、MSD暴露时间、feeder setup错误连接到板序列号。MSD过期时烘烤125℃ 24hr后重新验证，feeder setup通过scanner 1:1匹配验证。测量周期：Every Lot入库时+作业前scanner确认。异常时材料隔离→Bake→重新使用判定。 | 2,4 | process_step |
| 3 | 印刷品质 | 将SPI体积(50~150%)/高度(50~200%)/偏移(±50μm)异常作为回流前Hold依据。SPI 100%全测，Cpk≥1.33管理。连续3次Fail时钢网清洗/更换。测量周期：Every Board(SPI 100% Inline)。异常时Auto-clean→复测→钢网检查。 | 3 | process_step |
| 4 | 贴装品质 | 将贴片程序、吸嘴tip状态、极性和feeder miss连接到AOI缺陷。连续3次同feeder misspick时停止Line。测量周期：Every Board AOI。异常时更换feeder/校正→重新验证。 | 4,6 | process_step |
| 5 | 回流履历 | 将回流曲线(peak 235~250℃、soak 183℃ 60~90sec)和锡膏lot连接到板序列号，用于焊接缺陷分析。KIC/ECD profiler按lot开始、中间、结束确认profile。△T>5℃时重新设定。测量周期：Lot开始/变更时+每日1次定期。异常时重设profile→重新检查。 | 5 | process_step |
| 6 | AOI/X-ray Gate | BGA/QFN隐藏焊点用X-ray补充判定，并连接hold/release。AOI false call率目标≤100PPM，X-ray抽样比例(新BGA 100%、量产10~20%)。测量周期：Every Board AOI+X-ray每lot抽样。异常时MRB→repair/rework→Gate重新判定。 | 6 | process_step |
| 7 | 电测Gate | 将ICT/FCT fail code、固件版本(Y/N确认)和校准结果保存到板序列号。ICT yield≥97%、FCT yield≥95%管理目标。测量周期：Every Board ICT+FCT。异常时Diagnostic→Repair loop→Retest。 | 8 | process_step |
| 8 | 出货追踪 | 验证标签、序列号(uni-serial/MAC)、包装规格与客户出货lot一致。出货检验AQL=0.65，serial range重复/遗漏零容忍。测量周期：Every Lot出货前Sampling。异常时全数重新检查→重新发行标签。 | 10 | process_step |

## 2.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | NPI | process |  |  | work_order_id,pcb_revision,placement_program |
| 2 | Material | process |  |  | work_order_id,component_lot,feeder_id,operator_id |
| 3 | Print | process |  |  | board_serial,stencil_id,paste_lot,SPI_result |
| 4 | Placement | process |  |  | board_serial,feeder_id,placement_program,component_lot |
| 5 | Reflow | process |  |  | board_serial,reflow_profile,paste_lot |
| 6 | Inspection Gate | gate |  | 3,4,5 | board_serial,AOI_result,Xray_result,defect_code |
| 7 | THT | process |  |  | board_serial,operator_id,defect_code |
| 8 | Electrical Test | gate |  | 6,7 | board_serial,ICT_result,FCT_result,firmware_version |
| 9 | Coating | process |  |  | board_serial,coating_batch,operator_id |
| 10 | Packing | process |  |  | work_order_id,board_serial,FCT_result |

## 2.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | NPI | process |  |  | work_order_id,pcb_revision,placement_program |
| 2 | Material | process |  |  | work_order_id,component_lot,feeder_id,operator_id |
| 3 | Print | process |  |  | board_serial,stencil_id,paste_lot,SPI_result |
| 4 | Placement | process |  |  | board_serial,feeder_id,placement_program,component_lot |
| 5 | Reflow | process |  |  | board_serial,reflow_profile,paste_lot |
| 6 | Inspection Gate | gate |  | 3,4,5 | board_serial,AOI_result,Xray_result,defect_code |
| 7 | THT | process |  |  | board_serial,operator_id,defect_code |
| 8 | Electrical Test | gate |  | 6,7 | board_serial,ICT_result,FCT_result,firmware_version |
| 9 | Coating | process |  |  | board_serial,coating_batch,operator_id |
| 10 | Packing | process |  |  | work_order_id,board_serial,FCT_result |

## 2.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | AOI 판정 |
| 6 | 2 | X-ray 확인 |
| 6 | 3 | Repair/MRB |
| 8 | 1 | ICT |
| 8 | 2 | FCT |
| 8 | 3 | Firmware/Calibration 확인 |

## 2.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | AOI判定 |
| 6 | 2 | X-ray确认 |
| 6 | 3 | 维修/MRB |
| 8 | 1 | ICT |
| 8 | 2 | FCT |
| 8 | 3 | 固件/校准确认 |

## 2.9 data_capture_points

```yaml
- work_order_id
- board_serial
- pcb_revision
- component_lot
- feeder_id
- stencil_id
- paste_lot
- SPI_result
- placement_program
- reflow_profile
- AOI_result
- Xray_result
- ICT_result
- FCT_result
- firmware_version
- coating_batch
- defect_code
- operator_id
```

# 3. C03 — EMS·OEM·ODM 생산

```yaml
subindustry_code: C03
legacy_slug: ems
label_ko: EMS·OEM·ODM 생산
label_zh: EMS·OEM·ODM生产
label_en: ""
label_ja: ""
routing: RT_JOBSHOP
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  EMS·OEM·ODM은 고객별 BOM/ECN, 프로그램 격리, SMT/Box-build, Config, Test, Label·출하를 고객 기준으로 분리 추적해야 한다.
routing_description_zh: >
  EMS/OEM/ODM需要按客户分离追踪BOM/ECN、项目隔离、SMT/Box-build、配置、测试、标签和出货。
```

## 3.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객수요·Program 기준선 | Forecast, PO, EDI(ASN/Invoice 전자교환), 고객 BOM(Rev control), 품질협약(QAA, AQL, defect classification, warranty), 접근권한(고객 portal data visibility)을 확정한다. Program code별로 ERP project/WBS code를 할당하고 고객 spec의 frozen BOM date를 적용한다. |
| 2 | NPI·DFx·ECN 관리 | DFM/DFT/DFA review(고객 설계팀과 공동), ECO/ECN(Rev letter tracking, effectivity date = lot split criteria), sample build(Engineering/DVT/PVT/MP gate), FAIR(First Article Inspection Report)를 관리한다. ECN 적용 시 신규 lot에 반영하고 기존 stock disposition을 확정한다. |
| 3 | 구매·고객자재·Kitting | Consigned material(고객 공급 자재, customer stock location), buy-sell material(EMS 조달), AVL 관리, 대체품(substitute part, 고객 승인 필수), 고객별 재고를 program_id/location으로 격리 관리한다. Kitting station에서 scanner로 kit completeness 100% 확인, 부족 시 shortage alert 발행. |
| 4 | SMT·PCBA 생산 | 고객별 line program(PCB panelization, stencil, placement, reflow, AOI/X-ray program), feeder setup kit, paste lot, AOI/X-ray 검사 이력을 board serial/고객 program 단위로 남긴다. 고객별 별도 SMT 라인 또는 physical segregation 불가 시 Changeover validation(첫 기판 3장 100% 검사) 수행. |
| 5 | Mechanical·Cable·Sub Assembly | Housing(플라스틱 사출/다이캐스팅), cable harness(cut/strip/crimp/connector insertion), thermal pad/grease 도포, gasket 압축, screw torque(Pneumatic screwdriver, 목표값 ±10%) 등 조립 이력을 unit serial에 저장. |
| 6 | Box Build·System Integration | PCBA, module(display/camera/battery/power), enclosure, accessory(manual, power cord, adapter)를 완제품 serial에 연결한다. 부자재 깜빡이(BOM mismatch) 방지를 위해 assembly station에서 serial scan시 목록 확인. |
| 7 | Configuration·Firmware | 국가/고객/SKU별 firmware(version 관리, checksum/MD5 검증), license key(일회성 activation file), parameter(통신 설정, 지역별 전압/주파수), MAC/IMEI 주입. 각 write 작업 후 checksum 또는 read-back 검증을 필수 수행. |
| 8 | ICT·FCT·ESS Gate | ICT(open/short/RLC/polarity), FCT(기능 동작, 전원 측정, 통신 loopback, program execution)에서 결과 저장. ESS(Burn-in: 45~70℃/8~72hr, Temperature cycling: -40~+85℃/10~50 cycles, Vibration: random 5~2,000Hz, 6G) 적용. 모든 test code, fail count, repair history를 unit serial에 저장 후 Gate 판정. |
| 9 | Customer QA·OBA | 고객별 OBA(Out-of-Box Audit, 일반 0.65 AQL / 중요 defect zero tolerance), AQL level(Critical→0, Major→0.65, Minor→1.0), audit 체크리스트(고객 portal 다운로드), defect code 분류, corrective action(8D report)를 program별로 관리. OBA reject 시 100% sort + corrective action 완료 후 재샘플링. |
| 10 | Packing·ASN·Shipment | Label(고객 spec, barcode, serial), carton(중량, dimension), pallet(standard GMA/EPAL), ASN(Advance Shipment Notice, EDI 856), customer portal upload(proforma invoice, packing list, test report), 출하승인(Shipping Release)을 수행. 화물 Tracking(National carrier, FEDEX/DHL/TNT) API 연동. |

## 3.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户需求/项目基准 | 确认Forecast、PO、EDI(ASN/Invoice电子交换)、客户BOM(版本控制)、质量协议(QAA、AQL、缺陷分类、保修)和访问权限(客户门户数据可见性)。按Program code分配ERP project/WBS code，应用客户spec的frozen BOM date。 |
| 2 | NPI/DFx/ECN管理 | 管理DFM/DFT/DFA review(与客户设计团队共同)、ECO/ECN(Rev letter tracking、effectivity date=lot split标准)、sample build(Engineering/DVT/PVT/MP gate)和FAIR(First Article Inspection Report)。ECN生效时反映到新lot，确定既有stock处置方案。 |
| 3 | 采购/客户料/Kitting | 分离管理客供料(客户供应材料、customer stock location)、买卖料(EMS采购)、AVL、替代料(客户批准必需)和客户级库存(program_id/location隔离)。Kitting工作站用scanner 100%确认kit completeness，短缺时发出shortage alert。 |
| 4 | SMT/PCBA生产 | 按board serial/客户program保存客户别line program(PCB拼板、钢网、贴片、回流、AOI/X-ray程序)、feeder setup kit、锡膏lot、AOI/X-ray检验履历。无法安排客户别独立SMT线或physical segregation时执行Changeover validation(首3片100%检查)。 |
| 5 | 机械/线缆/子装配 | 将Housing(塑料注塑/压铸)、cable harness(cut/strip/crimp/connector insertion)、导热垫/导热膏涂布、gasket压缩和螺丝扭矩(气动螺丝刀，目标值±10%)等装配履历保存到unit serial。 |
| 6 | 整机组装/系统集成 | 将PCBA、模组(display/camera/battery/power)、enclosure、辅料(manual、power cord、adapter)连接到成品序列号。组装工站通过serial scan确认物料清单，防止漏装。 |
| 7 | 配置/固件 | 按国家、客户、SKU写入firmware(版本管理，checksum/MD5验证)、license key(一次性activation file)、parameter(通信设定、地区电压/频率)、MAC/IMEI。每次写入后强制执行checksum或read-back验证。 |
| 8 | ICT/FCT/ESS Gate | 保存ICT(open/short/RLC/polarity)、FCT(功能动作、电源测量、通信loopback、program execution)结果。ESS(老化: 45~70℃/8~72hr、温度循环: -40~+85℃/10~50 cycles、振动: random 5~2,000Hz、6G)。将所有test code、fail count和repair history保存到unit serial后进行Gate判定。 |
| 9 | 客户QA/OBA | 按program管理客户别OBA(Out-of-Box Audit，一般0.65 AQL/关键缺陷零容忍)、AQL等级(Critical→0、Major→0.65、Minor→1.0)、audit检查表(客户门户下载)、缺陷代码分类和纠正措施(8D报告)。OBA reject时100% sort+纠正措施完成后重新抽样。 |
| 10 | 包装/ASN/出货 | 执行标签(客户spec、条码、serial)、外箱(重量、尺寸)、托盘(standard GMA/EPAL)、ASN(Advance Shipment Notice、EDI 856)、客户门户上传(proforma invoice、packing list、test report)和出货批准(Shipping Release)。货物Tracking(国家承运商、FEDEX/DHL/TNT)API对接。 |

## 3.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 고객 Program 기준 | 고객별 BOM, 품질협약, 접근권한, 자료 공개 범위를 program_id로 분리한다. WO 생성 시 program_id 기준 BOM/Route/Frozen Date를 Lock. 측정 주기: NPI/ECN/신규 고객 등록 시 매번. 이상 시 Program Data Review → Customer PM 승인. | 1 | process_step |
| 2 | ECN·NPI | ECN 적용 시점(effectivity date), 재고 소진(Stock disposition: use-up/return/scrap), sample 승인 상태(FAIR sign-off)를 WO release 조건에 연결한다. 측정 주기: ECN 발생 시 매번. 이상 시 ECN Hold → Customer 승인 후 해제. | 2 | process_step |
| 3 | 고객별 자재 격리 | Consigned material, customer stock, 대체품 사용 승인을 kit_id와 연결한다. Kit completeness는 scanner 100% 확인. 측정 주기: Every Kit(scan 기반). 이상 시 Shortage Alert → 구매 긴급발주. | 3 | process_step |
| 4 | SMT 품질 | SMT AOI/X-ray 결함을 고객 program과 board serial 기준으로 집계한다. 고객별 defect Pareto, FPY(First Pass Yield)를 MES 대시보드에 실시간 표시. 측정 주기: Every Board AOI/X-ray. 이상 시 Customer 8D Report 작성 → SMT Line 공정 파라미터 조정. | 4 | process_step |
| 5 | Box-build Genealogy | Board, cable, module, enclosure serial을 완제품 serial에 연결한다. Serial scan 누락 시 assembly station에서 alarm. 측정 주기: Every Unit(scan 기반). 이상 시 전수 재소급 scan 후 genealogy 재구축. | 5,6 | process_step |
| 6 | Configuration | Firmware, license, MAC/IMEI, 지역별 parameter를 serial 단위로 Lock한다. Write 후 read-back 또는 checksum 검증 필수. 측정 주기: Every Unit. 이상 시 재주입(Reprogram) 후 재검증. | 7 | process_step |
| 7 | Test Gate | ICT/FCT/ESS fail과 repair 이력을 출하 승인 전 gate에서 판정한다. Gate pass율 < 95% 시 program별 Quality Review. 측정 주기: Every Unit(FCT/ESS). 이상 시 MRB → Repair/Retest → Gate 재판정. | 8 | process_step |
| 8 | 출하·ASN | Label, carton, ASN(EDI 856), 고객 portal 업로드 상태를 shipment release와 연결한다. ASN EDI 전송 오류 시 수동 대응 SOP. 측정 주기: Every Shipment. 이상 시 ASN 재전송 → Customer Portal 확인. | 10 | process_step |

## 3.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 客户项目基准 | 以program_id分离客户BOM、质量协议、访问权限和资料公开范围。WO生成时按program_id锁定BOM/Route/Frozen Date。测量周期：NPI/ECN/新客户注册时每次。异常时Program Data Review→客户PM批准。 | 1 | process_step |
| 2 | ECN/NPI | 将ECN生效点(effectivity date)、库存消耗(Stock disposition: use-up/return/scrap)和样品批准状态(FAIR sign-off)连接到WO release条件。测量周期：ECN发生时每次。异常时ECN Hold→客户批准后解除。 | 2 | process_step |
| 3 | 客户物料隔离 | 将客供料、客户库存和替代料批准连接到kit_id。Kit completeness通过scanner 100%确认。测量周期：Every Kit(扫描基础)。异常时Shortage Alert→采购紧急下单。 | 3 | process_step |
| 4 | SMT品质 | 按客户program和board serial汇总SMT AOI/X-ray缺陷。在MES仪表盘实时显示客户别defect Pareto和FPY(First Pass Yield)。测量周期：Every Board AOI/X-ray。异常时编写客户8D报告→调整SMT线工艺参数。 | 4 | process_step |
| 5 | 整机Genealogy | 将Board、cable、module、enclosure序列号连接到成品序列号。serial scan遗漏时assembly station报警。测量周期：Every Unit(扫描基础)。异常时全数重新追溯scan后重建genalogy。 | 5,6 | process_step |
| 6 | 配置 | 按序列号锁定Firmware、license、MAC/IMEI和地区参数。写入后强制read-back或checksum验证。测量周期：Every Unit。异常时重新编程后重新验证。 | 7 | process_step |
| 7 | 测试Gate | 出货批准前在Gate判定ICT/FCT/ESS fail和维修履历。Gate pass率<95%时进行program别Quality Review。测量周期：Every Unit(FCT/ESS)。异常时MRB→Repair/Retest→Gate重新判定。 | 8 | process_step |
| 8 | 出货/ASN | 将标签、外箱、ASN(EDI 856)和客户门户上传状态连接到shipment release。ASN EDI发送错误时按手动应对SOP处理。测量周期：Every Shipment。异常时重新发送ASN→确认客户门户。 | 10 | process_step |

## 3.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Program | process |  |  | customer_id,program_id,BOM_revision |
| 2 | NPI | process |  |  | program_id,ECN_id,BOM_revision |
| 3 | Material | process |  |  | customer_id,material_lot,kit_id |
| 4 | SMT | process |  |  | work_order_id,board_serial,material_lot,defect_code |
| 5 | Sub Assembly | process |  |  | work_order_id,unit_serial,material_lot |
| 6 | Box Build | process |  |  | unit_serial,board_serial,kit_id |
| 7 | Config | process |  |  | unit_serial,firmware_version,MAC_IMEI |
| 8 | Test Gate | gate |  | 4,5,6,7 | unit_serial,test_result,burnin_result,defect_code |
| 9 | Customer QA | gate |  | 8 | customer_id,unit_serial,OBA_result,defect_code |
| 10 | Shipment | process |  |  | customer_id,unit_serial,label_id,ASN_id |

## 3.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Program | process |  |  | customer_id,program_id,BOM_revision |
| 2 | NPI | process |  |  | program_id,ECN_id,BOM_revision |
| 3 | Material | process |  |  | customer_id,material_lot,kit_id |
| 4 | SMT | process |  |  | work_order_id,board_serial,material_lot,defect_code |
| 5 | Sub Assembly | process |  |  | work_order_id,unit_serial,material_lot |
| 6 | Box Build | process |  |  | unit_serial,board_serial,kit_id |
| 7 | Config | process |  |  | unit_serial,firmware_version,MAC_IMEI |
| 8 | Test Gate | gate |  | 4,5,6,7 | unit_serial,test_result,burnin_result,defect_code |
| 9 | Customer QA | gate |  | 8 | customer_id,unit_serial,OBA_result,defect_code |
| 10 | Shipment | process |  |  | customer_id,unit_serial,label_id,ASN_id |

## 3.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 8 | 1 | ICT/FCT 판정 |
| 8 | 2 | ESS/Burn-in 확인 |
| 8 | 3 | Repair/MRB |
| 9 | 1 | OBA Sampling |
| 10 | 1 | ASN Upload |

## 3.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 8 | 1 | ICT/FCT判定 |
| 8 | 2 | ESS/老化确认 |
| 8 | 3 | 维修/MRB |
| 9 | 1 | OBA抽样 |
| 10 | 1 | ASN上传 |

## 3.9 data_capture_points

```yaml
- customer_id
- program_id
- work_order_id
- BOM_revision
- ECN_id
- material_lot
- kit_id
- board_serial
- unit_serial
- firmware_version
- MAC_IMEI
- test_result
- burnin_result
- OBA_result
- label_id
- ASN_id
- defect_code
```

# 4. C04 — 전자 모듈·부품 조립

```yaml
subindustry_code: C04
legacy_slug: electronic_modules
label_ko: 전자 모듈·부품 조립
label_zh: 电子模组·部件组装
label_en: ""
label_ja: ""
routing: RT_JOBSHOP
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  전자 모듈·부품 조립은 부품 Lot, PCBA, 하우징, 케이블, 접착·체결, 캘리브레이션을 모듈 Serial 단위로 묶어야 한다.
routing_description_zh: >
  电子模组/部件组装需要将部件Lot、PCBA、外壳、线缆、点胶/紧固和校准按模组序列号绑定。
```

## 4.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 모듈 사양·BOM 기준선 | 고객 사양(전기적/기계적/환경 spec), BOM(module BOM + sub-tier BOM), route version(assembly sequence revision), 검사 기준(module AOI/ICT 기준서), critical parameter(torque, gap, dispense volume, calibration target)를 확정한다. WO release 시 spec freeze date를 기준으로 모든 도면과 BOM revision을 Lock. |
| 2 | 부품 수입·Sub-kit | PCB(bare board), sensor(온도/압력/가속도), connector(D-sub/USB/HDMI/RJ45), cable(ribbon/coaxial/FPC), housing, adhesive(epoxy/silicone/acrylic, 보관 -10~40℃) lot와 보관조건을 확인한다. Sub-kit 구성은 PLC 기반 자동분류 시스템으로 kit tray 단위 준비. |
| 3 | PCBA·Sub Board 준비 | SMT board(전단계 SMT line 생산), firmware preload(MCU/FPGA program, checksum 확인), connector solder(수동/로봇 솔더링, 온도 350~400℃), board test(ICT/flying probe) 이력을 pcba_serial에 저장. PCBA lot과 module serial을 사전 매핑하여 추적성 확보. |
| 4 | Housing·기구 조립 | Housing(cutting/deburring, 알루미늄/플라스틱), bracket(스테인리스/galvanized steel), gasket(실리콘/NBR/CR, 압축률 25~40%), screw torque(digital torque wrench, 목표값 ±5%~±10%, M3~M6), fit/gap(Feeler gauge, 0.1~0.5mm)를 관리한다. 작업 후 torque calibration log를 module serial에 기록. |
| 5 | Cable·Connector Assembly | Cable harness(cut+crimp+insertion, terminal pull force ≥20N IPC/WHMA-A-620), terminal crimp(crimp height/width, pull force monitoring), connector lock(visual + tactile click 확인), continuity tester로 open/short 검증(1,000points/min). 모든 테스트 결과를 cable_serial에 저장. |
| 6 | Dispense·Bonding·Cure | Adhesive dispense(Nordson Asymtek/PVA, needle φ0.2~0.8mm, dispensing pressure 0.1~0.6MPa, 속도 10~50mm/s), dispense volume(무게 측정, 목표 ±10%), 위치 정밀도(±0.1mm), open time(adhesive별 5~30min), UV 경화(365~405nm, 500~4,000mJ/cm²) 또는 thermal cure(80~150℃, 30~120min) profile을 module serial에 저장. Shrinkage risk 평가. |
| 7 | Module Calibration | 전기(offset/gain, reference voltage, 0.05% accuracy standard), 센서(온도/압력/습도, multi-point calibration, NIST traceable standard), 위치(linear/rotary encoder, resolution 1μm), 출력(power, current, ±0.1% tolerance) parameter를 jig 기준으로 캘리브레이션한다. Jig calibration은 외부 교정기관 연 1회 인증. |
| 8 | Functional Test Gate | EOL functional test(전원 on/off, communication RS485/CAN/I2C/SPI, relay 동작, digital I/O), leakage(IP67/IP68 수밀, air pressure decay 0.5~2bar, 10~60sec), burn-in(온도 55~85℃, 4~48hr) 결과를 Gate로 판정한다. Test code별 pass/fail, 측정값, tolerance violation을 module serial에 저장. |
| 9 | Final Inspection | 외관(scratch, dent, contamination, color discrepancy under D65 light), barcode(verify grade ≥B, ISO 15415/15416), serial(고유 module serial, 중복 check), key parameter lock(calibration parameter write-protect, fuse/EFUSE), customer spec(치수, 중량, 표면처리)을 확인. |
| 10 | Packing·Shipment | ESD pack(ESD shielding bag, surface resistance 10⁶~10⁹Ω), tray(anti-static tray, insert foam, retention force), label(customer label format, GTIN/MAC/Serial 2D barcode), carton(package instruction per unit qty), shipment lot mapping(serial range per carton/pallet). |

## 4.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 模组规格/BOM基准 | 确认客户规格(电气/机械/环境spec)、BOM(module BOM+sub-tier BOM)、route version(组装序列版本)、检验标准(module AOI/ICT标准书)和关键参数(torque、gap、点胶量、校准目标)。WO release时按spec freeze date锁定所有图纸和BOM版本。 |
| 2 | 来料/Sub-kit | 确认PCB(bare board)、sensor(温度/压力/加速度)、connector(D-sub/USB/HDMI/RJ45)、cable(ribbon/coaxial/FPC)、housing、adhesive(环氧/硅胶/丙烯酸，存储-10~40℃)的lot和存储条件。Sub-kit通过PLC自动分拣系统以kit tray单位准备。 |
| 3 | PCBA/Sub Board准备 | 将SMT板(前道SMT线生产)、固件预载(MCU/FPGA程序，checksum确认)、连接器焊接(手动/机器人焊接，温度350~400℃)和板测(ICT/flying probe)履历保存到pcba_serial。预先映射PCBA lot与module serial以确保追溯性。 |
| 4 | 外壳/机构组装 | 管理Housing(cutting/deburring、铝/塑料)、bracket(不锈钢/镀锌钢)、gasket(硅胶/NBR/CR、压缩率25~40%)、螺丝扭矩(数字扭矩扳手，目标值±5%~±10%，M3~M6)、fit/gap(Feeler gauge，0.1~0.5mm)。作业后将torque calibration log记录到module serial。 |
| 5 | 线缆/连接器组装 | Cable harness(cut+crimp+insertion，端子拉拔力≥20N IPC/WHMA-A-620)、端子压接(压接高度/宽度、拉力监测)、connector lock(目视+触觉click确认)、continuity tester验证open/short(1,000points/min)。所有测试结果保存到cable_serial。 |
| 6 | 点胶/粘接/固化 | 胶水点胶(Nordson Asymtek/PVA、针头φ0.2~0.8mm、点胶压力0.1~0.6MPa、速度10~50mm/s)、点胶量(重量测量、目标±10%)、位置精度(±0.1mm)、open time(各胶水5~30min)、UV固化(365~405nm、500~4,000mJ/cm²)或热固化(80~150℃、30~120min)曲线保存到module serial。评估收缩风险。 |
| 7 | 模组校准 | 按治具基准校准电气(offset/gain、reference voltage，0.05%精度标准)、传感器(温度/压力/湿度，multi-point校准，NIST traceable标准)、位置(linear/rotary encoder，分辨率1μm)、输出(power、current，±0.1% tolerance)参数。治具校准由外部校准机构每年一次认证。 |
| 8 | 功能测试Gate | 用EOL功能测试(电源on/off、通信RS485/CAN/I2C/SPI、继电器动作、digital I/O)、泄漏(IP67/IP68水密，air pressure decay 0.5~2bar，10~60sec)和老化(温度55~85℃，4~48hr)结果进行Gate判定。将test code별 pass/fail、测量值和tolerance violation保存到module serial。 |
| 9 | 终检 | 确认外观(scratch、dent、contamination、D65光源下的颜色差异)、条码(verify grade≥B、ISO 15415/15416)、序列号(唯一module serial、重复检查)、关键参数锁定(calibration parameter write-protect、fuse/EFUSE)和客户spec(尺寸、重量、表面处理)。 |
| 10 | 包装/出货 | 确认ESD包装(ESD shielding bag，表面电阻10⁶~10⁹Ω)、托盘(anti-static tray、insert foam、retention force)、标签(客户标签格式、GTIN/MAC/Serial 2D条码)、外箱(每箱数量包装指示)和出货lot mapping(每个carton/pallet的serial range)。 |

## 4.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | BOM·Route 기준 | 모델별 route version, 검사 기준, critical parameter를 WO release 전 확정한다. BOM diff check로 revision 차이를 사전 탐지. 측정 주기: NPI/ECN 시 매회. 이상 시 Engineering review → spec update. | 1 | process_step |
| 2 | 부품 Genealogy | PCBA, housing, cable, adhesive lot를 module serial에 연결한다. 입고 검사시 scanner로 sub-kit 시리얼 등록. 측정 주기: Every Lot 입고 시 + Assembly scan. 이상 시 전수 재소급 → genealogy 재구축. | 2,3 | process_step |
| 3 | 기구 조립 | Torque(목표 ±5~10%), gap/flush(0.1~0.5mm), gasket 위치를 검사 결과와 연결한다. Digital torque wrench data auto-upload. 측정 주기: Every Unit(체결 torque). 이상 시 재조임 → Torque calibration 검증. | 4 | process_step |
| 4 | 케이블·압착 | Crimp force(crimp height monitoring), continuity, connector lock 누락을 serial 기준으로 관리한다. IPC/WHMA-A-620 Class 2 기준. 측정 주기: Every Cable(연속성)·Sampling(압착력 10ea/lot). 이상 시 재압착/재연결 → 샘플링 강화. | 5 | process_step |
| 5 | 접착·Cure | Dispense volume(목표 ±10%), 위치(±0.1mm), open time(5~30min), cure profile(UV mJ/cm²/온도℃/시간min)을 module serial에 저장한다. Adhesive pot life 관리. 측정 주기: Every Unit(volume/위치) + Batch 시작 시 cure profile. 이상 시 dispense parameter 조정 → 재작업. | 6 | process_step |
| 6 | Calibration | Calibration jig, offset, parameter lock과 station drift를 추적한다. Jig 교정 유효기간(연 1회) tracking. 측정 주기: Every Unit(Calibration) + Jig Daily self-check. 이상 시 Jig 재교정 → 전수 재보정. | 7 | process_step |
| 7 | Functional Gate | EOL fail code와 repair 후 retest 이력을 출하 전 판정한다. Gate yield < 90% 시 Line stop. 측정 주기: Every Unit(EOL Test). 이상 시 MRB → Repair/Retest → Gate 재판정. | 8 | process_step |
| 8 | 출하 추적 | ESD pack, tray, label과 serial range가 고객 사양과 일치하는지 확인한다. Label barcode grade ≥B (ISO 15415/15416). 측정 주기: Every Lot 출하 전. 이상 시 label 재발행 → 전수 재검증. | 10 | process_step |

## 4.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | BOM/Route基准 | 在WO release前确认型号别route version、检验标准和关键参数。通过BOM diff检查预先发现版本差异。测量周期：NPI/ECN时每次。异常时Engineering review→spec update。 | 1 | process_step |
| 2 | 部件Genealogy | 将PCBA、housing、cable、adhesive lot连接到module serial。入库检验时通过scanner登记sub-kit序列号。测量周期：Every Lot入库时+Assembly scan。异常时全数重新追溯→重建genealogy。 | 2,3 | process_step |
| 3 | 机构组装 | 将扭矩(目标±5~10%)、gap/flush(0.1~0.5mm)和gasket位置连接到检验结果。数字扭矩扳手数据自动上传。测量周期：Every Unit(紧固扭矩)。异常时重新拧紧→扭矩校准验证。 | 4 | process_step |
| 4 | 线缆/压接 | 按序列号管理Crimp force(压接高度监测)、导通和connector lock遗漏。IPC/WHMA-A-620 Class 2标准。测量周期：Every Cable(导通)·Sampling(压接力10ea/lot)。异常时重新压接/重新连接→加强抽样。 | 5 | process_step |
| 5 | 粘接/Cure | 将点胶量(目标±10%)、位置(±0.1mm)、open time(5~30min)和固化曲线(UV mJ/cm²/温度℃/时间min)保存到module serial。管理胶水pot life。测量周期：Every Unit(点胶量/位置)+批次开始固化曲线。异常时调整点胶参数→返工。 | 6 | process_step |
| 6 | 校准 | 追踪校准治具、offset、参数锁定和station drift。治具校准有效期(每年1次)跟踪。测量周期：Every Unit(校准)+Jig每日自检。异常时Jig重新校准→全数重新校准。 | 7 | process_step |
| 7 | 功能Gate | 出货前判定EOL fail code和维修后复测履历。Gate yield<90%时Line stop。测量周期：Every Unit(EOL Test)。异常时MRB→Repair/Retest→Gate重新判定。 | 8 | process_step |
| 8 | 出货追踪 | 确认ESD包装、托盘、标签和序列号范围符合客户规格。标签barcode grade≥B(ISO 15415/15416)。测量周期：Every Lot出货前。异常时重新发行标签→全数重新验证。 | 10 | process_step |

## 4.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | work_order_id,route_version |
| 2 | Material | process |  |  | material_lot,module_serial |
| 3 | PCBA | process |  |  | pcba_serial,module_serial |
| 4 | Mechanical | process |  |  | housing_serial,torque_result,module_serial |
| 5 | Cable | process |  |  | cable_serial,module_serial |
| 6 | Bonding | process |  |  | adhesive_lot,dispense_volume,cure_profile,module_serial |
| 7 | Calibration | process |  |  | module_serial,calibration_result,jig_id |
| 8 | Test Gate | gate |  | 3,4,5,6,7 | module_serial,functional_test_result,defect_code |
| 9 | Final QA | process |  |  | module_serial,calibration_result,functional_test_result |
| 10 | Shipment | process |  |  | module_serial,packing_label |

## 4.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | work_order_id,route_version |
| 2 | Material | process |  |  | material_lot,module_serial |
| 3 | PCBA | process |  |  | pcba_serial,module_serial |
| 4 | Mechanical | process |  |  | housing_serial,torque_result,module_serial |
| 5 | Cable | process |  |  | cable_serial,module_serial |
| 6 | Bonding | process |  |  | adhesive_lot,dispense_volume,cure_profile,module_serial |
| 7 | Calibration | process |  |  | module_serial,calibration_result,jig_id |
| 8 | Test Gate | gate |  | 3,4,5,6,7 | module_serial,functional_test_result,defect_code |
| 9 | Final QA | process |  |  | module_serial,calibration_result,functional_test_result |
| 10 | Shipment | process |  |  | module_serial,packing_label |

## 4.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 7 | 1 | Jig Check |
| 7 | 2 | Parameter Write |
| 7 | 3 | Calibration Lock |
| 8 | 1 | EOL Test |
| 8 | 2 | Repair/Re-test |

## 4.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 7 | 1 | 治具确认 |
| 7 | 2 | 参数写入 |
| 7 | 3 | 校准锁定 |
| 8 | 1 | EOL测试 |
| 8 | 2 | 维修/复测 |

## 4.9 data_capture_points

```yaml
- work_order_id
- module_serial
- route_version
- material_lot
- pcba_serial
- housing_serial
- cable_serial
- torque_result
- adhesive_lot
- dispense_volume
- cure_profile
- calibration_result
- jig_id
- functional_test_result
- defect_code
- packing_label
```

# 5. C05 — 산업전자·제어기기

```yaml
subindustry_code: C05
legacy_slug: industrial_electronics
label_ko: 산업전자·제어기기
label_zh: 工业电子·控制设备
label_en: ""
label_ja: ""
routing: RT_JOBSHOP
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  산업전자·제어기기는 제어반/드라이브/전원/PLC/센서 모듈의 BOM, Firmware, Parameter, Safety test, FAT를 serial 단위로 추적해야 한다.
routing_description_zh: >
  工业电子/控制设备需要按序列号追踪控制柜、驱动、电源、PLC、传感器模组的BOM、固件、参数、安全测试和FAT。
```

## 5.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 고객·제어사양 기준선 | I/O list(DI/DO/AI/AO 수량, signal type 24VDC/120VAC/4-20mA), control logic(PID/sequence/PLC program architecture), safety level(SIL1~3 per IEC 61508, PL per ISO 13849), communication protocol(Profinet/EtherCAT/Modbus TCP/OPC-UA), cabinet layout(실물 배치도, cooling/ventilation, IP rating)을 확정한다. |
| 2 | BOM·Panel 설계 Release | Electrical drawing(회로도 EPLAN/AutoCAD Electrical), wiring list(신호표, cable ID, ferrule marking), terminal plan(PLC I/O assignment), firmware/parameter baseline을 Release한다. Drawing revision을 ERP BOM과 동기화하고 EPLAN ↔ ERP Interface(Wire List Publish)로 자재 일치성 검증. |
| 3 | 자재·전장품 입고 | PLC(CPU, I/O module, communication module, serial 등록), drive(servo/VFD, 전력 rating), power supply(AC/DC 24V, 5V, redundancy module), relay(전자접촉기/보조계전기, coil voltage), terminal(Spring clamp/Screw type, push-in), sensor(proximity/pressure/temperature) lot와 인증서(CE/UL/CCC)를 입고 검사에서 확인. |
| 4 | PCBA·Control Module 조립 | Board assembly(DIN rail mounting, board-to-board connector), module mounting(backplane 연결, plug-in module lock), solder(manual solder station Weller/JBC, 350~400℃, 무연 솔더 SnAgCu), conformal coating 이력(silicone/acrylic, 두께 50~150μm)을 unit serial에 저장. |
| 5 | Panel Wiring·Harness | Wiring(wire cut/strip/ferrule, 0.5~2.5mm², wire color per DIN VDE 0293), ferrule(crimping tool with force monitoring, pull force ≥50N), terminal torque(Phoenix/Weidmuller terminal, 디지털 드라이버, 0.5~1.2Nm), cable label(heat shrink/laser, wire number marking per wiring list), continuity(1,000V megohmmeter, 절연저항 ≥5MΩ). |
| 6 | Firmware·Parameter Download | PLC/drive firmware(version check, SIEMENS TIA Portal/Allen Bradley Studio 5000/Mitsubishi GX Works를 통해 download), parameter(IP address, subnet mask, gateway, PID gain, motor parameter, recipe selection), license(activation key, dongle serial)를 unit serial에 기록한다. |
| 7 | Safety·Electrical Test Gate | Hi-pot(AC 1,500~2,500V/1min, leakage current ≤5mA, IEC 60204-1), insulation(500V, insulation resistance ≥5MΩ, Class I equipment 기준), grounding(ground continuity <0.1Ω, 접지저항 측정기 Fluke 1625), interlock(도어 스위치/라이트커튼 작동 확인), e-stop(비상정지 회로, dual channel 모두 확인, response time <100ms), EMC(radiation/conducted emission, IEC 61000-6-4) 측정. 모든 test 결과로 Gate 판정. |
| 8 | Functional Test·Simulation | I/O simulation(DI/DO/AI/AO 각 채널 순차 테스트, PLC simulation software로 sequence logic 검증), communication(PROFINET/EtherCAT ping test, data exchange 확인, response time <1ms), control sequence(engineer가 정의한 순차제어 시나리오 기반 시뮬레이션), alarm logic(alarm/fault 조건 입력 시 HMI 표시 + alarm log 저장 확인). |
| 9 | FAT·Customer Acceptance | 고객 FAT(factory acceptance test, FAT protocol 기반, 고객 engineer 입회, 1~3일), deviation(minor/major/critical classification, Major 이상은 FAT 중단), punch item(close date tracking, punch list), document package(전기 도면 as-built, test report, calibration certificate, O&M manual, spare parts list)를 관리한다. |
| 10 | Packing·Site Handover | Panel protection(PE film + corner protector + wooden crate, shock/vibration indicator 부착), spare parts(documented baseline, serial mapping), O&M 문서(2 sets, hardcopy + PDF), 현장 설치 자료( mounting drawing, foundation bolt spec, cable entry layout)와 함께 출하. Site installation support 계약 시 field service report 연결. |

## 5.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 客户/控制规格基准 | 确认I/O list(DI/DO/AI/AO数量，signal type 24VDC/120VAC/4-20mA)、控制逻辑(PID/sequence/PLC program architecture)、安全等级(SIL1~3 per IEC 61508、PL per ISO 13849)、通信协议(Profinet/EtherCAT/Modbus TCP/OPC-UA)和柜体布局(实物布置图、cooling/ventilation、IP等级)。 |
| 2 | BOM/盘柜设计Release | Release电气图(EPLAN/AutoCAD Electrical)、接线表(信号表、cable ID、ferrule marking)、端子计划(PLC I/O assignment)、固件/参数基准。将Drawing revision与ERP BOM同步，通过EPLAN↔ERP Interface(Wire List Publish)验证材料一致性。 |
| 3 | 物料/电气件入库 | 确认PLC(CPU、I/O module、communication module、serial登记)、drive(伺服/VFD、功率等级)、power supply(AC/DC 24V、5V、redundancy module)、relay(电磁接触器/辅助继电器、线圈电压)、terminal(Spring clamp/Screw type、push-in)、sensor(接近/压力/温度)的lot和证书(CE/UL/CCC)。 |
| 4 | PCBA/控制模组组装 | 将板装配(DIN rail安装、board-to-board connector)、模组安装(背板连接、plug-in module锁紧)、焊接(手动焊接台Weller/JBC、350~400℃、无铅焊料SnAgCu)和三防漆履历(silicone/acrylic、厚度50~150μm)保存到unit serial。 |
| 5 | 盘柜接线/Harness | 确认接线(wire cut/strip/ferrule、0.5~2.5mm²、wire color per DIN VDE 0293)、冷压端子(带力监测的压接工具，拉拔力≥50N)、端子扭矩(Phoenix/Weidmuller端子、数字螺丝刀、0.5~1.2Nm)、线号(热缩/激光、按接线表编号)和导通(1,000V兆欧表、绝缘电阻≥5MΩ)。 |
| 6 | 固件/参数下载 | 将PLC/drive firmware(版本确认，通过SIEMENS TIA Portal/Allen Bradley Studio 5000/Mitsubishi GX Works下载，checksum验证)、parameter(IP address、subnet mask、gateway、PID gain、motor parameter、recipe selection)和license(activation key、dongle serial)记录到unit serial。 |
| 7 | 安全/电气测试Gate | 判定耐压(AC 1,500~2,500V/1min、leakage current≤5mA、IEC 60204-1)、绝缘(500V、绝缘电阻≥5MΩ、Class I设备标准)、接地(ground continuity<0.1Ω、接地电阻测试仪Fluke 1625)、联锁(门开关/光幕确认)、急停(dual channel确认、response time<100ms)和EMC(radiation/conducted emission、IEC 61000-6-4)。所有测试结果进行Gate判定。 |
| 8 | 功能测试/仿真 | I/O仿真(DI/DO/AI/AO各通道顺序测试，PLC simulation软件验证sequence logic)、通信(PROFINET/EtherCAT ping test、确认data exchange、response time<1ms)、控制顺序(基于engineer定义的顺序控制场景仿真)和报警逻辑(报警/故障条件输入时HMI显示+报警log保存确认)。 |
| 9 | FAT/客户验收 | 管理客户FAT(factory acceptance test、基于FAT protocol、客户engineer见证、1~3天)、偏差(minor/major/critical分类、Major以上FAT中断)、punch item(close date tracking、punch list)和文档包(电气竣工图as-built、test report、校准证书、O&M manual、spare parts list)。 |
| 10 | 包装/现场交付 | 出货盘柜防护(PE膜+角保护+木箱、shock/vibration indicator安装)、备件(documented baseline、serial mapping)、O&M文档(2套、hardcopy+PDF)和现场安装资料(mounting drawing、foundation bolt spec、cable entry layout)。现场安装支持合同时连接field service report。 |

## 5.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 제어사양 기준 | I/O, protocol, safety level, cabinet layout 변경을 project_id와 도면 revision으로 통제한다. EPLAN drawing revision과 ERP BOM 간 mismatch 방지. 측정 주기: Project Kickoff 및 CR(Change Request) 발생 시. 이상 시 Project Change Order → Customer 승인. | 1 | process_step |
| 2 | 도면·BOM Release | Electrical drawing, wiring list, terminal plan과 BOM revision 불일치를 차단한다. EPLAN ↔ ERP Interface 자동 비교. 측정 주기: Release 전 ECR 시마다. 이상 시 Drawing revision update → 재승인. | 2 | process_step |
| 3 | 전장품 추적 | PLC, drive, power, sensor serial과 인증서를 unit serial에 연결한다. 입고 시 serial 및 certificate scan. 측정 주기: Every Lot 입고 시. 이상 시 자재 격리 → Supplier SCAR. | 3,4 | process_step |
| 4 | Wiring 품질 | Terminal torque(0.5~1.2Nm), ferrule(pull force ≥50N), cable label, continuity(≥5MΩ) 결과를 station별로 기록한다. Digital screwdriver data auto-upload. 측정 주기: Every Unit(Wiring station). 이상 시 재배선 → station별 교육. | 5 | process_step |
| 5 | Firmware·Parameter | Firmware(checksum 검증), parameter set, IP, license를 임의 변경하지 못하게 Lock한다. Download 후 read-back verification. 측정 주기: Every Unit. 이상 시 재 Download → 재검증. | 6 | process_step |
| 6 | Safety Gate | Hi-pot(누설전류 ≤5mA), insulation(≥5MΩ), grounding(<0.1Ω), interlock, E-stop(dual channel) 결과가 Gate 기준을 만족해야 한다. 측정 주기: Every Unit. 이상 시 설계 검토 → Safety circuit 재확인. | 7 | process_step |
| 7 | Functional Test | I/O simulation, alarm sequence, communication fail을 test result로 저장한다. 각 channel별 pass/fail 기록. 측정 주기: Every Unit. 이상 시 Program logic 수정 → 재시험. | 8 | process_step |
| 8 | FAT·문서 | FAT deviation(punch list close), document package(drawing as-built, O&M manual, test report), spare parts list 완료 전 출하를 제한한다. 측정 주기: Project별 FAT 완료 시. 이상 시 Punch close → Customer 재확인 후 출하 승인. | 9,10 | process_step |

## 5.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 控制规格基准 | 用project_id和图纸版本控制I/O、protocol、safety level和柜体布局变更。防止EPLAN drawing revision与ERP BOM不匹配。测量周期：Project Kickoff及CR(Change Request)发生时。异常时Project Change Order→客户批准。 | 1 | process_step |
| 2 | 图纸/BOM Release | 阻断电气图、接线表、端子计划和BOM版本不一致。EPLAN↔ERP Interface自动比较。测量周期：Release前ECR时每次。异常时Drawing revision update→重新批准。 | 2 | process_step |
| 3 | 电气件追踪 | 将PLC、drive、power、sensor序列号和证书连接到unit serial。入库时scan serial及certificate。测量周期：Every Lot入库时。异常时隔离材料→Supplier SCAR。 | 3,4 | process_step |
| 4 | 接线品质 | 按station记录端子扭矩(0.5~1.2Nm)、冷压端子(拉拔力≥50N)、线号和导通(≥5MΩ)结果。数字螺丝刀数据自动上传。测量周期：Every Unit(Wiring station)。异常时重新接线→station别培训。 | 5 | process_step |
| 5 | 固件/参数 | 锁定Firmware(checksum验证)、parameter set、IP和license，防止任意变更。下载后read-back verification。测量周期：Every Unit。异常时重新下载→重新验证。 | 6 | process_step |
| 6 | Safety Gate | 耐压(漏电流≤5mA)、绝缘(≥5MΩ)、接地(<0.1Ω)、联锁和急停(dual channel)结果必须满足Gate标准。测量周期：Every Unit。异常时设计审查→Safety circuit重新确认。 | 7 | process_step |
| 7 | 功能测试 | 将I/O仿真、报警顺序和通信失败保存为test result。记录各channel pass/fail。测量周期：Every Unit。异常时修改Program logic→重新测试。 | 8 | process_step |
| 8 | FAT/文档 | FAT偏差(punch list close)、文档包(drawing as-built、O&M manual、test report)和备件清单未完成前限制出货。测量周期：Project别FAT完成时。异常时Punch close→客户重新确认后出货批准。 | 9,10 | process_step |

## 5.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | project_id,BOM_revision,drawing_revision |
| 2 | Design | process |  |  | project_id,BOM_revision,drawing_revision |
| 3 | Material | process |  |  | component_lot,PLC_serial,drive_serial |
| 4 | Module | process |  |  | unit_serial,component_lot |
| 5 | Wiring | process |  |  | unit_serial,wiring_check_result,torque_result |
| 6 | Config | process |  |  | unit_serial,firmware_version,parameter_set |
| 7 | Safety Gate | gate |  | 4,5,6 | unit_serial,safety_test_result |
| 8 | Function | process |  |  | unit_serial,functional_test_result |
| 9 | FAT Gate | gate |  | 7,8 | unit_serial,FAT_result,punch_status |
| 10 | Handover | process |  |  | unit_serial,document_package |

## 5.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | project_id,BOM_revision,drawing_revision |
| 2 | Design | process |  |  | project_id,BOM_revision,drawing_revision |
| 3 | Material | process |  |  | component_lot,PLC_serial,drive_serial |
| 4 | Module | process |  |  | unit_serial,component_lot |
| 5 | Wiring | process |  |  | unit_serial,wiring_check_result,torque_result |
| 6 | Config | process |  |  | unit_serial,firmware_version,parameter_set |
| 7 | Safety Gate | gate |  | 4,5,6 | unit_serial,safety_test_result |
| 8 | Function | process |  |  | unit_serial,functional_test_result |
| 9 | FAT Gate | gate |  | 7,8 | unit_serial,FAT_result,punch_status |
| 10 | Handover | process |  |  | unit_serial,document_package |

## 5.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 7 | 1 | Hi-pot/Insulation |
| 7 | 2 | Interlock/E-stop |
| 8 | 1 | I/O Simulation |
| 9 | 1 | FAT Punch Review |
| 9 | 2 | Customer Sign-off |

## 5.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 7 | 1 | 耐压/绝缘 |
| 7 | 2 | 联锁/急停 |
| 8 | 1 | I/O仿真 |
| 9 | 1 | FAT Punch评审 |
| 9 | 2 | 客户签字 |

## 5.9 data_capture_points

```yaml
- project_id
- unit_serial
- BOM_revision
- drawing_revision
- component_lot
- PLC_serial
- drive_serial
- firmware_version
- parameter_set
- wiring_check_result
- torque_result
- safety_test_result
- functional_test_result
- FAT_result
- punch_status
- document_package
```

# 6. C06 — 통신·네트워크 장비

```yaml
subindustry_code: C06
legacy_slug: telecom_equipment
label_ko: 통신·네트워크 장비
label_zh: 通信·网络设备
label_en: ""
label_ja: ""
routing: RT_JOBSHOP
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  통신·네트워크 장비는 RF/High-speed PCBA, 광모듈, Thermal, Firmware, RF calibration, BER/EVM, Burn-in을 serial 단위로 연결해야 한다.
routing_description_zh: >
  通信/网络设备需要按序列号连接RF/高速PCBA、光模块、散热、固件、RF校准、BER/EVM和老化。
```

## 6.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 제품·지역·규격 기준선 | RF band(Sub-6GHz/mmWave 28/39/60GHz, 5G NR FR1/FR2), network protocol(5G SA/NSA/LTE/WiFi6E/7, 10G/25G/100G Ethernet), region certification(FCC/CE/IC/KC/CCC/RCM/BSMI, 각국의 RF spurious/emission limit), security configuration(secure boot, TPM 2.0, hardware security module, encryption key)을 확정한다. SKU별 region code mapping table로 firmware/label/logistics 속성 관리. |
| 2 | High-speed PCBA | BGA(0.4~0.8mm pitch, 1,000~4,000 balls), QFN(thermal pad via array), impedance control(50Ω single-ended, 100Ω differential, ±5%), high-speed connector(SFP+/QSFP28/QSFP56, PCIe Gen4/5), shielding pad(EMI shielding Can/finger)와 reflow profile(peak 245±5℃ vacuum reflow, void <5% via X-ray)을 관리한다. 고주파 PCB 재료(Rogers 4350B/Megtron 6/FR4 고속 등급)로 Dk/Df 관리. |
| 3 | RF·Optical Submodule 조립 | RF shield(자석별 캔 솔더링 / 클립 타입), antenna(PCB printed antenna / chip antenna / 외부 antenna connector), optical transceiver(SFP+/QSFP28/CFP2, 10km/40km/80km, TX power/RX sensitivity spec), fiber connector(LC/SC/MPO, insertion loss <0.3dB, return loss >50dB)와 module serial을 1:1 매칭하여 광모듈 교체 이력 추적. |
| 4 | Thermal·Mechanical Assembly | Heat sink(알루미늄/구리, fin height, base flatness ≤100μm), thermal pad(3W~10W/mK, 0.5~2.0mm thickness), fan(2-wire/3-wire/4-wire PWM, 40~120mm airflow 5~150CFM), enclosure(알루미늄 다이캐스트, IP30~65), torque(screw M3/M4, 0.5~1.2Nm, ±10%), airflow path(CFD simulation 기반, hot spot <85℃ junction temp)를 관리한다. |
| 5 | Firmware·Security Provisioning | Firmware(VxWorks/Linux/u-boot, version tracking SHA256 checksum), bootloader(secure boot chain, signature verification RSA2048), key/certificate(X.509 device certificate, pre-provisioned private key, TPM 2.0 초기화), MAC address(범용 unique 48bit, OUI 기준 block 할당), SN(생산순서기반 serial number 체계), region config(regulatory domain, channel list, max TX power)를 주입한다. Write 후 반드시 read-back 또는 hash 검증. |
| 6 | RF Calibration·Alignment | RF power(TX power calibration, ±0.5dBm accuracy, power detector reading), frequency(LO frequency locking, PLL phase noise 측정 -80dBc/Hz @10kHz), EVM(256QAM/1024QAM EVM ≤1.5%~3%, vector signal analyzer Keysight/R&S), gain(rx_gain/tx_gain per band step, LNA/mixer/PA chain calibration), antenna path(antenna port switching, VSWR <1.5:1 per band)를 Keysight/R&S jig 환경에서 대역별로 보정한다. |
| 7 | Optical·Network Test Gate | BER(Bit Error Rate, PRBS31 패턴, BER < 1E-12, error count 0 over 60sec), optical power(TX average power, RX average power, OMA per IEEE 802.3), throughput(IETF RFC 2544, 100% line rate 60초, zero frame loss, latency ≤10μS), protocol compatibility(IPv4/IPv6/PTP/MPLS/segment routing header parsing)를 Gate로 판정한다. |
| 8 | Burn-in·Aging | Temperature chamber(온도 55~85℃, ramp rate 5~10℃/min, humidity 10~90%RH), traffic load(실제 network traffic profile 기반, port utilization 80~100%), failure log(serial console log capture, kernel panic/warning/exception monitoring, SEU/SEL 감지), intermittent fault(온도 변화에 따른 재현성 확인, retry loop, marginal bit detection)를 장시간(8~168hr) 시험한다. |
| 9 | Final QA·Certification Check | Regulatory label(FCC ID/CE/IC 등 규제 mark, 고객별 위치 규정 준수), security config(secure boot enabled, TPM activated, no debug port open, factory reset functional), test report(calibration record, BER/power report), customer requirements(cosmetic, accessory completeness, packaging spec)를 검증한다. |
| 10 | Packing·RMA Link | Serial(unit serial), MAC address, accessory(power cord, SFP+/DAC/AOC cable, rack mount kit), label(shipping label, regulatory label, serial barcode), RMA baseline(unit factory data → RMA cloud DB upload for field return, firmware MAC calibration baseline matching, warranty start date trigger at first boot). |

## 6.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 产品/地区/规格基准 | 确认RF频段(Sub-6GHz/mmWave 28/39/60GHz、5G NR FR1/FR2)、网络协议(5G SA/NSA/LTE/WiFi6E/7、10G/25G/100G Ethernet)、地区认证(FCC/CE/IC/KC/CCC/RCM/BSMI、各国RF spurious/emission limit)和安全配置(secure boot、TPM 2.0、hardware security module、encryption key)。通过SKU别region code mapping table管理firmware/label/logistics属性。 |
| 2 | 高速PCBA | 管理BGA(0.4~0.8mm pitch，1,000~4,000 balls)、QFN(thermal pad via array)、阻抗控制(50Ω single-ended、100Ω differential、±5%)、高速连接器(SFP+/QSFP28/QSFP56、PCIe Gen4/5)、屏蔽焊盘(EMI屏蔽Can/finger)和回流profile(peak 245±5℃真空回流、void<5% by X-ray)。使用高频PCB材料(Rogers 4350B/Megtron 6/FR4高速等级)管理Dk/Df。 |
| 3 | RF/光学子模组组装 | 进行RF shield(磁铁型Can焊接/夹扣型)、天线(PCB印刷天线/chip天线/外部天线连接器)、光模块(SFP+/QSFP28/CFP2、10km/40km/80km、TX power/RX sensitivity spec)和光纤连接器(LC/SC/MPO、insertion loss<0.3dB、return loss>50dB)与module serial一对一匹配，追踪光模块更换履历。 |
| 4 | 散热/机构组装 | 管理散热片(铝/铜、fin height、base flatness≤100μm)、导热垫(3W~10W/mK、0.5~2.0mm厚度)、风扇(2-wire/3-wire/4-wire PWM、40~120mm风量5~150CFM)、外壳(铝合金压铸、IP30~65)、扭矩(螺丝M3/M4、0.5~1.2Nm、±10%)和风道(基于CFD仿真、hot spot<85℃ junction temp)。 |
| 5 | 固件/安全写入 | 写入Firmware(VxWorks/Linux/u-boot、版本追踪SHA256 checksum)、bootloader(secure boot chain、signature verification RSA2048)、key/certificate(X.509设备证书、pre-provisioned私钥、TPM 2.0初始化)、MAC地址(全球唯一48bit、OUI标准block分配)、SN(生产顺序serial number体系)和地区配置(regulatory domain、channel list、max TX power)。写入后强制read-back或hash验证。 |
| 6 | RF校准/对准 | 在Keysight/R&S治具环境中按频段校正RF power(TX power校准、±0.5dBm精度、power detector reading)、frequency(LO频率锁定、PLL相位噪声测量-80dBc/Hz@10kHz)、EVM(256QAM/1024QAM EVM≤1.5%~3%、vector signal analyzer Keysight/R&S)、gain(rx_gain/tx_gain per band step、LNA/mixer/PA chain校准)和antenna path(antenna port切换、VSWR<1.5:1 per band)。 |
| 7 | 光学/网络测试Gate | 用BER(Bit Error Rate、PRBS31模式、BER<1E-12、error count 0 over 60sec)、optical power(TX平均功率、RX平均功率、OMA per IEEE 802.3)、throughput(IETF RFC 2544、100% line rate 60秒、zero frame loss、latency≤10μS)和protocol compatibility(IPv4/IPv6/PTP/MPLS/segment routing header parsing)进行Gate判定。 |
| 8 | 老化/Aging | 长时间测试温度箱(温度55~85℃、ramp rate 5~10℃/min、湿度10~90%RH)、traffic load(基于real network traffic profile、port utilization 80~100%)、failure log(serial console log capture、kernel panic/warning/exception监测、SEU/SEL检测)和间歇性故障(温度变化复现性确认、retry loop、marginal bit detection)，持续8~168hr。 |
| 9 | 终检/认证确认 | 验证法规标签(FCC ID/CE/IC等法规mark、客户别位置规定遵守)、安全配置(secure boot enabled、TPM activated、no debug port open、factory reset functional)、测试报告(calibration record、BER/power report)和客户要求(外观、附件完整、包装规格)。 |
| 10 | 包装/RMA连接 | 连接Serial(unit serial)、MAC address、附件(power cord、SFP+/DAC/AOC cable、rack mount kit)、标签(shipping label、regulatory label、serial barcode)和RMA baseline(unit工厂数据→RMA cloud DB上传用于售后、firmware MAC calibration baseline匹配、warranty start date于首次开机时触发)。 |

## 6.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 규격·지역 기준 | RF band, protocol, certification, security configuration을 region/SKU별로 Lock한다. Region code mapping table 관리. 측정 주기: NPI/신규 region 추가 시. 이상 시 Engineering Change → Certification 재획득. | 1 | process_step |
| 2 | High-speed PCBA | Impedance(TDR, 50Ω/100Ω ±5%), BGA void(X-ray, <5%), high-speed connector 결함을 pcba_serial과 연결한다. Vacuum reflow 적용. 측정 주기: Every Panel(Impedance coupon) + X-ray sampling per lot. 이상 시 Reflow profile 조정 → 재검증. | 2 | process_step |
| 3 | RF·광모듈 추적 | Optical transceiver(TX power, RX sensitivity, serial), antenna, RF shield serial과 module 위치를 추적한다. 광모듈 교체 시 history log 기록. 측정 주기: Every Unit(scan 기준). 이상 시 Module 교체/Return → Supplier 분석. | 3 | process_step |
| 4 | Thermal 조립 | Thermal pad lot(3~10W/mK), torque(0.5~1.2Nm ±10%), airflow path(CFD simulation), fan serial을 unit serial에 연결한다. Hot spot 온도 junction <85℃ 검증. 측정 주기: Every Unit. 이상 시 Thermal rework → 재조립 → 재시험. | 4 | process_step |
| 5 | Security Provisioning | Firmware(SHA256 checksum), certificate(X.509, RSA2048), key, MAC write 실패를 재작업 없이 출하하지 않는다. Read-back verification. 측정 주기: Every Unit. 이상 시 재주입 → 재검증. | 5 | process_step |
| 6 | RF Calibration | EVM(256QAM ≤1.5%, 1024QAM ≤3%), gain, frequency(-80dBc/Hz @10kHz), RF power(±0.5dBm) 결과와 jig 상태(self-cal daily)를 함께 저장한다. 측정 주기: Every Unit + Jig Daily Self-cal. 이상 시 Jig 재교정 → 전수 재보정. | 6 | process_step |
| 7 | Network Gate | BER(<1E-12), throughput(100% line rate, zero loss), protocol compatibility fail을 Gate에서 Hold 처리한다. 1차 fail 시 retest 1회 허용. 측정 주기: Every Unit. 이상 시 Diagnostics → Hardware/Software debug → Gate 재판정. | 7 | process_step |
| 8 | Burn-in·RMA | Burn-in failure(온도 55~85℃, 8~168hr failure log), RMA baseline(초기 factory data)을 serial 단위로 연결해 field failure 분석에 사용한다. 측정 주기: Every Unit(Burn-in) + RMA 발생 시. 이상 시 FA(Field Analysis) → Design/Firmware corrective action. | 8,10 | process_step |

## 6.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 规格/地区基准 | 按region/SKU锁定RF频段、协议、认证和安全配置。管理Region code mapping table。测量周期：NPI/新增region时。异常时Engineering Change→重新获取认证。 | 1 | process_step |
| 2 | 高速PCBA | 将阻抗(TDR、50Ω/100Ω ±5%)、BGA void(X-ray、<5%)和高速连接器缺陷连接到pcba_serial。应用真空回流。测量周期：Every Panel(阻抗coupon)+X-ray每lot抽样。异常时调整Reflow profile→重新验证。 | 2 | process_step |
| 3 | RF/光模组追踪 | 追踪光模块(TX power、RX sensitivity、serial)、天线和RF shield序列号和模组位置。光模块更换时记录history log。测量周期：Every Unit(扫描基础)。异常时Module更换/Return→Supplier分析。 | 3 | process_step |
| 4 | 散热组装 | 将导热垫lot(3~10W/mK)、扭矩(0.5~1.2Nm ±10%)、风道(CFD仿真)和风扇序列号连接到unit serial。验证hot spot温度junction<85℃。测量周期：Every Unit。异常时Thermal返工→重新组装→重新测试。 | 4 | process_step |
| 5 | 安全写入 | Firmware(SHA256 checksum)、certificate(X.509、RSA2048)、key、MAC写入失败不得不返工直接出货。Read-back verification。测量周期：Every Unit。异常时重新写入→重新验证。 | 5 | process_step |
| 6 | RF校准 | 同时保存EVM(256QAM≤1.5%、1024QAM≤3%)、gain、frequency(-80dBc/Hz@10kHz)、RF power(±0.5dBm)结果和治具状态(daily self-cal)。测量周期：Every Unit+Jig每日自检。异常时Jig重新校准→全数重新校准。 | 6 | process_step |
| 7 | 网络Gate | 在Gate对BER(<1E-12)、throughput(100% line rate、zero loss)和protocol compatibility fail进行Hold。首次fail允许retest 1次。测量周期：Every Unit。异常时Diagnostics→Hardware/Software debug→Gate重新判定。 | 7 | process_step |
| 8 | 老化/RMA | 按序列号连接Burn-in failure(温度55~85℃、8~168hr failure log)和RMA baseline(初始factory data)，用于现场失效分析。测量周期：Every Unit(Burn-in)+RMA发生时。异常时FA(Field Analysis)→Design/Firmware corrective action。 | 8,10 | process_step |

## 6.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | unit_serial,BOM_revision,RF_band |
| 2 | PCBA | process |  |  | pcba_serial,BOM_revision |
| 3 | RF/Optical | process |  |  | unit_serial,optical_module_serial,RF_band |
| 4 | Thermal | process |  |  | unit_serial,thermal_pad_lot,torque_result |
| 5 | Provisioning | process |  |  | unit_serial,firmware_version,security_key_id,MAC_address |
| 6 | RF Calibration | process |  |  | unit_serial,RF_calibration_result,EVM_result |
| 7 | Network Gate | gate |  | 3,5,6 | unit_serial,BER_result,throughput_result,EVM_result |
| 8 | Burn-in | process |  |  | unit_serial,burnin_result |
| 9 | Certification | gate |  | 7,8 | unit_serial,cert_label,burnin_result |
| 10 | Shipment | process |  |  | unit_serial,MAC_address,RMA_baseline |

## 6.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | unit_serial,BOM_revision,RF_band |
| 2 | PCBA | process |  |  | pcba_serial,BOM_revision |
| 3 | RF/Optical | process |  |  | unit_serial,optical_module_serial,RF_band |
| 4 | Thermal | process |  |  | unit_serial,thermal_pad_lot,torque_result |
| 5 | Provisioning | process |  |  | unit_serial,firmware_version,security_key_id,MAC_address |
| 6 | RF Calibration | process |  |  | unit_serial,RF_calibration_result,EVM_result |
| 7 | Network Gate | gate |  | 3,5,6 | unit_serial,BER_result,throughput_result,EVM_result |
| 8 | Burn-in | process |  |  | unit_serial,burnin_result |
| 9 | Certification | gate |  | 7,8 | unit_serial,cert_label,burnin_result |
| 10 | Shipment | process |  |  | unit_serial,MAC_address,RMA_baseline |

## 6.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | RF Jig Check |
| 6 | 2 | Calibration Write |
| 7 | 1 | BER/EVM Test |
| 7 | 2 | Throughput Test |
| 9 | 1 | Certification Label Check |

## 6.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | RF治具确认 |
| 6 | 2 | 校准写入 |
| 7 | 1 | BER/EVM测试 |
| 7 | 2 | Throughput测试 |
| 9 | 1 | 认证标签确认 |

## 6.9 data_capture_points

```yaml
- unit_serial
- pcba_serial
- BOM_revision
- RF_band
- optical_module_serial
- thermal_pad_lot
- torque_result
- firmware_version
- security_key_id
- MAC_address
- RF_calibration_result
- EVM_result
- BER_result
- throughput_result
- burnin_result
- cert_label
- RMA_baseline
```

# 7. C07 — 소비자전자·가전

```yaml
subindustry_code: C07
legacy_slug: consumer_electronics
label_ko: 소비자전자·가전
label_zh: 消费电子·家电
label_en: ""
label_ja: ""
routing: RT_LINE
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  소비자전자·가전은 SKU/색상/국가별 BOM, SMT, 모듈 조립, Firmware, Calibration, Aging, 외관, Label을 라인 tact와 연결해야 한다.
routing_description_zh: >
  消费电子/家电需要将SKU/颜色/国家别BOM、SMT、模组组装、固件、校准、老化、外观和标签与产线节拍连接。
```

## 7.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 수요·SKU·지역 기준선 | SKU(product model + variation), color(UNI code 참조, white/black/gold/silver 등), plug type(A/C/G/I 등 국가별 형상), language(UI language pack), label(energy label/recycling/regulatory per country), firmware region(OTA region lock), 생산순서(SKU changeover 최소화 sequence optimization)를 확정한다. MES에서 SKU별 BOM/Route/Program auto-select 적용. |
| 2 | Material Kitting | PCB(PCBA board, panel 단위), display(liquid crystal/OLED, cell/모듈, size, resolution), battery(Li-ion/LiPo, 전압 3.7~7.2V, 용량 2,000~10,000mAh, UN38.3 인증), motor,vibrator, camera module(sensor resolution, AF/OIS), speaker(폴리곤/woofer/tweeter), housing(플라스틱 사출/금속 CNC) 등 kit completeness를 scanner+tray 기반 100% 확인. |
| 3 | SMT·PCBA | PCBA 생산(C02 SMT 라인 연계), AOI(X-ray 보조), ICT(bed-of-nails or flying probe) 결과를 board serial에 연결한다. 소비자가전용 고속 라인(40~50 라인, 120,000CPH 급)에서 SKU 전환 시 Changeover kit 교체(5~15분)로 tact loss 최소화. |
| 4 | Main Assembly | Housing 결합(Snap-fit/ultrasonic welding/adhesive bonding), screw(자동 screwdriver multi-spindle, M1.6~M3, torque 0.3~1.0Nm), adhesive(핫멜트/PSA tape/UV cure), gasket(스폰지/rubber, 압축률 30~50%), display assembly(backlight/diffuser/bezel, pressure roller, bubble ≤0.1mm), 배터리 조립(connector lock, FPC routing), camera/speaker assembly(lens cap, contact spring, acoustic seal)을 automated robotic cell에서 tact time 10~30초로 수행. |
| 5 | Firmware Download | SKU/region firmware(SWD/JTAG/UART interface, SPI flash/eMMC/NAND, download time 30~120초), language pack(번역 resource files, NLS(National Language Support) image), calibration table(lens shading correction, white balance, speaker EQ curve, battery fuel gauge table), device ID(unique hardware ID, TPM/SE initialized)를 factory test mode에서 주입. Download 완료 후 checksum / signature verify. |
| 6 | Calibration | Touch(projected capacitive, multi-touch 10-point, linearity self-cal + jig calibration, sensitivity <1mm), camera(AWB/AF/AE calibration, color chart(24patch Gretag Macbeth 기준), lens shading correction, OIS calibration), sensor(accelerometer/gyroscope/magnetometer, 6-axis fusion, offset/gain/sensitivity), motor(vibration pattern, speed/amplitude linearity), audio(speaker sensitivity ±1dB, microphone sensitivity, SNR >60dB, THD <1%), RF(WiFi/BT, TX power, RSSI, channel list) calibration을 각 calibration station에서 수행. |
| 7 | Functional Test·Aging Gate | FCT(SMART 테스트 시나리오, 전원 on/off cycle, charging 5V~20V PD, communication BT/WiFi/NFC/USB, safety short circuit protection OCP/OVP, speaker/camera/vibration 기능 동작), aging(온도 45~65℃, 2~8hr, 풀 power 상태, battery charging cycle, display pattern burn-in, failure rate monitoring) 결과로 Gate 판정. Gate yield < 92% 시 라인 정지. |
| 8 | Cosmetic Inspection | Scratch(depth gauge, 0.05mm 이하 ACC, 0.1mm 이하 Rej), gap/flush(Feeler gauge, 0.1~0.3mm, flush ±0.2mm), color(spectrophotometer, color difference ΔE <1.5 under D65 light), contamination(dust/foreign particle, critical area zero tolerance), cosmetic defect code 분류(Minor/Major/Critical). Automated vision system(Line scan camera 5μm/pixel, 700~1,200mm/min)으로 100% 전수 검사. |
| 9 | Packing·Label | IMEI/SN(각 단말기 GSM Association unique, MAC address와 매칭), energy label(MEPS per country, efficiency class), country label(regulatory marking, importer info, recycling symbol), accessory(charger, cable, earphone, manual, SIM eject tool, case), carton(Standard Brown Box or Retail Ready Pack, barcode label per country retailer). 모든 label은 vision 검증 시스템(OCR+OCV, ISO 15416 grade ≥B) 확인. |
| 10 | Palletizing·Shipment | Pallet(standard Europallet/GMA pallet, layer pattern 최적화, securing strap + corner protector), shipment lot(고객 주문별 serial range 할당, lot ID와 customer PO 매핑), ASN(EDI 856, 각 pallet/carton serial detail, GTIN, quantity), customer order fulfillment(order line 100% check, back-order zero), 출하승인(release flag, delivery note, tax invoice)을 WMS/ERP와 연동. |

## 7.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 需求/SKU/地区基准 | 确认SKU(产品型号+variation)、颜色(UNI代码参考、white/black/gold/silver等)、插头类型(A/C/G/I等国别形状)、语言(UI语言包)、标签(能效标签/回收/法规per country)、固件地区(OTA地区锁)和生产顺序(SKU切换最少化sequence优化)。MES根据SKU自动选择BOM/Route/Program。 |
| 2 | Material Kitting | 确认PCB(PCBA板、panel单位)、display(LCD/OLED、cell/模组、尺寸、分辨率)、battery(Li-ion/LiPo、电压3.7~7.2V、容量2,000~10,000mAh、UN38.3认证)、motor/vibrator、camera模块(sensor分辨率、AF/OIS)、speaker(锥盆/woofer/tweeter)和housing(塑料注塑/金属CNC)等齐套，通过scanner+tray基础100%确认。 |
| 3 | SMT/PCBA | 将PCBA生产(C02 SMT线联动)、AOI(X-ray辅助)、ICT(针床或飞针)结果连接到board serial。消费电子专用高速线(40~50工站、120,000CPH级)在SKU切换时更换Changeover kit(5~15分钟)以最小化tact损失。 |
| 4 | Main Assembly | 在automated robotic cell中以tact time 10~30秒执行：外壳结合(Snap-fit/超声波焊接/胶粘剂bonding)、螺丝(自动螺丝刀multi-spindle、M1.6~M3、扭矩0.3~1.0Nm)、胶水(热熔胶/PSA tape/UV cure)、gasket(海绵/rubber、压缩率30~50%)、显示屏组装(背光/diffuser/bezel、pressure roller、bubble≤0.1mm)、电池组装(connector lock、FPC routing)、摄像头/喇叭组装(lens cap、contact spring、acoustic seal)。 |
| 5 | 固件下载 | 在工厂测试模式下写入SKU/地区固件(SWD/JTAG/UART接口、SPI flash/eMMC/NAND、下载时间30~120秒)、语言包(翻译资源文件、NLS image)、校准表(lens shading correction、white balance、speaker EQ曲线、battery fuel gauge table)和device ID(唯一hardware ID、TPM/SE初始化)。下载完成后checksum/signature verify。 |
| 6 | 校准 | 在各校准工站执行：触摸(projected capacitive、multi-touch 10点、linearity self-cal+jig校准、灵敏度<1mm)、摄像头(AWB/AF/AE校准、24patch色卡Gretag Macbeth标准、lens shading correction、OIS校准)、传感器(accelerometer/gyroscope/magnetometer、6轴融合、offset/gain/sensitivity)、马达(vibration pattern、speed/amplitude linearity)、音频(speaker灵敏度±1dB、麦克风灵敏度、SNR>60dB、THD<1%)和RF(WiFi/BT、TX power、RSSI、channel list)校准。 |
| 7 | 功能测试/Aging Gate | 用FCT(SMART测试场景、电源on/off cycle、充电5V~20V PD、通信BT/WiFi/NFC/USB、安全短路保护OCP/OVP、speaker/camera/vibration功能动作)和老化(温度45~65℃、2~8hr、满power状态、battery charging cycle、display pattern burn-in、failure rate monitoring)结果进行Gate判定。Gate yield<92%时停止线体。 |
| 8 | 外观检验 | Scratch(深度规、0.05mm以下ACC、0.1mm以下Rej)、gap/flush(Feeler gauge、0.1~0.3mm、flush±0.2mm)、颜色(分光光度计、D65光源下色差ΔE<1.5)、污染(灰尘/异物、关键区域零容忍)、外观缺陷代码分类(Minor/Major/Critical)。自动视觉系统(Line scan相机5μm/pixel、700~1,200mm/min)100%全检。 |
| 9 | 包装/标签 | 验证IMEI/SN(每终端GSM Association unique、与MAC address匹配)、能效标签(MEPS per country、efficiency class)、国家标签(法规mark、进口商信息、回收标志)、附件(charger、cable、earphone、manual、SIM eject tool、case)和外箱(Standard Brown Box或Retail Ready Pack、per country零售商barcode label)。所有标签通过vision验证系统(OCR+OCV、ISO 15416 grade≥B)确认。 |
| 10 | 码垛/出货 | 连接Pallet(standard Europallet/GMA pallet、layer pattern最优化、securing strap+角保护)、shipment lot(客户订单别serial range分配、lot ID与customer PO映射)、ASN(EDI 856、每pallet/carton serial detail、GTIN、quantity)、客户订单fulfillment(order line 100%确认、back-order零容忍)和出货批准(release flag、delivery note、tax invoice)，与WMS/ERP联动。 |

## 7.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | SKU·지역 기준 | 색상, 국가, label, plug, firmware가 서로 맞지 않는 조합을 차단한다. MES auto-select BOM/Route/Program으로 SKU mismatch 방지. 측정 주기: WO 생성 시마다. 이상 시 SKU Configuration Review → Line Re-setup. | 1 | process_step |
| 2 | Kitting 정확성 | Kit completeness와 substitute material 사용 여부를 SKU/WO 기준으로 확인한다. Scanner 100% scan + 부족 시 shortage alert. 측정 주기: Every Kit(scan). 이상 시 Shortage 긴급 발주 → Kitting 재구성. | 2 | process_step |
| 3 | PCBA 추적 | Board serial, component lot(MLCC/IC/connector), AOI/ICT 결과를 unit serial과 연결한다. Changeover 시 첫 3장 100% AOI + ICT. 측정 주기: Every Board(AOI) + ICT sampling(첫 3장 100%, 이후 전수). 이상 시 Changeover Validation → SMT parameter 조정. | 3,4 | process_step |
| 4 | 모듈 조립 | Screw torque(0.3~1.0Nm), adhesive cure(UV/thermal), gap/flush(0.1~0.3mm ±0.2mm), 모듈 serial scan 누락을 관리한다. 자동 torque monitoring. 측정 주기: Every Unit(torque sensor). 이상 시 재조립 → torque calibration. | 4 | process_step |
| 5 | Firmware·Device ID | Firmware(checksum verify), device ID(unique), region config mismatch를 function test 전에 차단한다. Download 후 read-back. 측정 주기: Every Unit. 이상 시 재 Download → 재검증. | 5 | process_step |
| 6 | Calibration | Calibration yield와 station drift를 SKU/model별로 모니터링한다. Jig daily self-cal. 측정 주기: Every Unit(Cal) + Jig daily self-check. 이상 시 Jig recalibration → 금일 생산분 전수 재보정. | 6 | process_step |
| 7 | Functional Gate | FCT/aging fail과 repair 후 retest 이력을 Gate에서 판정한다. Gate yield < 92% 시 Line stop + Quality Review. 측정 주기: Every Unit(FCT/Aging). 이상 시 MRB → Repair/Retest → Gate 재판정. | 7 | process_step |
| 8 | 외관·Label | Cosmetic defect code(scratch ≤0.05mm, gap ≤0.3mm, ΔE <1.5), IMEI/SN, country label, packing label 일치성을 확인한다. Label vision 검증 grade ≥B. 측정 주기: Every Unit (Cosmetic vision 100%) + Label sampling per carton. 이상 시 전수 재검사 → label 재발행. | 8,9 | process_step |

## 7.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | SKU/地区基准 | 阻断颜色、国家、标签、插头、固件不匹配的组合。MES auto-select BOM/Route/Program防止SKU mismatch。测量周期：WO生成时每次。异常时SKU Configuration Review→Line Re-setup。 | 1 | process_step |
| 2 | Kitting准确性 | 按SKU/WO确认齐套和替代料使用状态。Scanner 100%扫描+短缺时shortage alert。测量周期：Every Kit(扫描)。异常时Shortage紧急下单→Kitting重新配置。 | 2 | process_step |
| 3 | PCBA追踪 | 将Board serial、component lot(MLCC/IC/connector)、AOI/ICT结果连接到unit serial。换线时首3片100% AOI+ICT。测量周期：Every Board(AOI)+ICT sampling(首3片100%、之后全数)。异常时Changeover Validation→调整SMT参数。 | 3,4 | process_step |
| 4 | 模组组装 | 管理螺丝扭矩(0.3~1.0Nm)、胶水固化(UV/thermal)、gap/flush(0.1~0.3mm±0.2mm)和模组serial scan遗漏。自动torque monitoring。测量周期：Every Unit(torque sensor)。异常时重新组装→torque calibration。 | 4 | process_step |
| 5 | 固件/Device ID | 在功能测试前阻断Firmware(checksum verify)、device ID(unique)和region config mismatch。下载后read-back。测量周期：Every Unit。异常时重新下载→重新验证。 | 5 | process_step |
| 6 | 校准 | 按SKU/model监控校准良率和station drift。Jig daily self-cal。测量周期：Every Unit(Cal)+Jig每日自检。异常时Jig recalibration→当日生产全数重新校准。 | 6 | process_step |
| 7 | 功能Gate | 在Gate判定FCT/aging fail和维修后复测履历。Gate yield<92%时Line stop+Quality Review。测量周期：Every Unit(FCT/Aging)。异常时MRB→Repair/Retest→Gate重新判定。 | 7 | process_step |
| 8 | 外观/标签 | 确认外观缺陷代码(scratch≤0.05mm、gap≤0.3mm、ΔE<1.5)、IMEI/SN、国家标签和包装标签一致。Label vision验证grade≥B。测量周期：Every Unit(外观vision 100%)+每carton标签sampling。异常时全数重新检查→重新发行标签。 | 8,9 | process_step |

## 7.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | SKU Plan | process |  |  | work_order_id,SKU_id,color_code,region_code |
| 2 | Kitting | process |  |  | kit_id,component_lot,SKU_id |
| 3 | PCBA | process |  |  | board_serial,component_lot |
| 4 | Assembly | process |  |  | unit_serial,board_serial,component_lot |
| 5 | Firmware | process |  |  | unit_serial,firmware_version,device_id,region_code |
| 6 | Calibration | process |  |  | unit_serial,calibration_result |
| 7 | Functional Gate | gate |  | 3,4,5,6 | unit_serial,FCT_result,aging_result |
| 8 | Cosmetic | process |  |  | unit_serial,cosmetic_defect_code,color_code |
| 9 | Packing | process |  |  | unit_serial,label_id,carton_id |
| 10 | Shipment | process |  |  | pallet_id,ASN_id,work_order_id |

## 7.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | SKU Plan | process |  |  | work_order_id,SKU_id,color_code,region_code |
| 2 | Kitting | process |  |  | kit_id,component_lot,SKU_id |
| 3 | PCBA | process |  |  | board_serial,component_lot |
| 4 | Assembly | process |  |  | unit_serial,board_serial,component_lot |
| 5 | Firmware | process |  |  | unit_serial,firmware_version,device_id,region_code |
| 6 | Calibration | process |  |  | unit_serial,calibration_result |
| 7 | Functional Gate | gate |  | 3,4,5,6 | unit_serial,FCT_result,aging_result |
| 8 | Cosmetic | process |  |  | unit_serial,cosmetic_defect_code,color_code |
| 9 | Packing | process |  |  | unit_serial,label_id,carton_id |
| 10 | Shipment | process |  |  | pallet_id,ASN_id,work_order_id |

## 7.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | Station Self-check |
| 6 | 2 | Calibration Write |
| 7 | 1 | FCT |
| 7 | 2 | Aging |
| 9 | 1 | Label Match |

## 7.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 6 | 1 | 工站自检 |
| 6 | 2 | 校准写入 |
| 7 | 1 | FCT |
| 7 | 2 | 老化 |
| 9 | 1 | 标签匹配 |

## 7.9 data_capture_points

```yaml
- line_id
- work_order_id
- SKU_id
- color_code
- region_code
- kit_id
- component_lot
- board_serial
- unit_serial
- firmware_version
- device_id
- calibration_result
- FCT_result
- aging_result
- cosmetic_defect_code
- label_id
- carton_id
- pallet_id
- ASN_id
```

# 8. C08 — 정밀·광전자 모듈

```yaml
subindustry_code: C08
legacy_slug: precision_modules
label_ko: 정밀·광전자 모듈
label_zh: 精密·光电子模组
label_en: ""
label_ja: ""
routing: RT_JOBSHOP
expression_tier: P3_LABOR_ASSEMBLY
routing_description_ko: >
  정밀·광전자 모듈은 청정도, Active Alignment, 접착·Cure, 광/전기 Calibration, 환경시험을 고가 모듈 Serial 단위로 추적해야 한다.
routing_description_zh: >
  精密/光电子模组需要按高价值模组序列号追踪洁净度、Active Alignment、粘接/固化、光/电校准和环境试验。
```

## 8.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | 제품·광학 사양 기준선 | Optical path(laser diode→lens→sensor/fiber coupling design), sensor(CMOS/CCD/InGaAs/APD, pixel size, quantum efficiency, dark current), lens(aspherical/telecentric/wide-angle, EFL, FOV, MTF spec), actuator(VCM/Piezo/SMA, stroke, hysteresis), coupling efficiency(≥50~80%, spec per application, coupling loss budget), alignment tolerance(±0.5~5μm translation, ±0.01~0.1° tilt, active alignment target spec)를 확정한다. |
| 2 | 정밀 부품 입고·청정관리 | Lens(optical grade glass/plastic, AR coating, scratch-dig 40-20 per MIL-PRF-13830), sensor(wafer-level package / ceramic LCC, dark signal non-uniformity spec), laser(laser diode VCSEL/EEL, wavelength tolerance ±1nm, class 1M/3R safety), fiber(single mode/multi-mode, APC/PC polish, insertion loss spec), actuator(VCM/Piezo, stroke spec ±10%), housing(금속/세라믹/액상폴리머 precision mold, dimension ±10μm) lot와 particle 조건(Class 1,000~10,000 cleanroom, particle count ≥0.5μm ≤100/ft³, ≥5μm ≤0/ft³)을 확인한다. |
| 3 | 세정·Pre-alignment | Particle removal(IPA/isopropyl alcohol ultrasonic bath 5~15min, N₂ blow dry, 60℃ dry oven), plasma/UV cleaning(O₂ plasma 30~60초, UV ozone 10~30초, 표면에너지 증가로 접착력 향상), datum setup(mechanical jig reference, optical alignment camera calibration grid), pre-alignment(visual alignment guide under microscope 10~50x, rough positioning ±10~50μm)를 clean bench(Class 100~1,000) 내에서 수행한다. |
| 4 | Sub-module Assembly | Sensor(CMOS/CCD/APD, die attach silver epoxy/au-tin solder, wire bonding Au/Al φ25~50μm, N₂ purge), lens barrel(barrel thread/friction fit/adhesive bond, lens-spacer-lens sequence), actuator(VCM housing assembly, suspension wire yoke/magnet), fiber(fiber ferrule, ceramic sleeve, inside housing alignment sleeve), PCB(FPC/circuit board, ACF bonding/soldering), housing(레이저 용접/UV adhesive/sealing cover)를 sub-module serial 기준으로 조립한다. |
| 5 | Active Alignment | Focus(lens barrel z-axis motion, point spread function(PSF) 측정, depth of field 고려, optimal focus position 검색), tilt(lens/sensor relative tilt, θx/θy 조정, ±0.01~0.1°), coupling(laser-fiber or fiber-detector coupling, x/y/z 고분해능 piezo stage 0.1~1μm resolution, power meter real-time monitoring), optical axis(zero reference alignment, collimation test, centration error <10μm), MTF/BER/power 실시간 측정(positioner가 6-axis hexapod + piezo stage) 후 고정. Active alignment loop은 목표값 도달 시까지 반복(Alignment Loop). |
| 6 | Adhesive Dispense·UV/Thermal Cure | Adhesive lot(UV-cure epoxy / thermal-cure silicone / hybrid UV+thermal, 보관 조건, pot life, expiration), dispense volume(nanoliter~microliter 정밀 디스펜서, needle φ0.1~0.5mm, valve jetting system, 무게 monitoring, target ±5%), UV dose(365~405nm, 500~5,000mJ/cm², radiometer 측정, intensity 100~1,000mW/cm²), thermal cure(80~150℃, 30~120min, oven uniformity ±2℃), shrinkage risk(post-cure dimensional shift, stress relaxation, alignment shift compensation)를 관리한다. |
| 7 | Electrical·Optical Calibration | Current(laser diode bias current/drive current, I-L curve measurement, threshold current I_th monitoring), power(optical output power, mW, calibrated photodiode, ±0.1dB accuracy), focus(auto-focus actuator stroke, close-loop position sensor calibration, hysteresis compensation), color(RGB channel gain/offset, white balance matrix, color temperature correction D65), signal integrity(eye diagram, jitter, rise/fall time, SNR), temperature compensation(온도 센서 lookup table calibration, power auto-adjust over -40~+85℃). |
| 8 | Environmental Stress Gate | Thermal cycling(-40~+85℃, 10~200 cycles, ramp rate 10~15℃/min, dwell 15~30min, per JEDEC JESD22-A104), humidity(85℃/85%RH, 100~500hr biased, per JEDEC JESD22-A101), vibration(sine sweep 5~500Hz 2G/random 5~2,000Hz 6G, 30min/axis, per MIL-STD-883 Method 2007), burn-in(55~85℃, 48~168hr, active operation, 전력 인가) 후 optical/electrical shift(MTF shift ≤5%, power drop ≤0.5dB, focus shift ≤2μm, dark current 증가 ≤10%)를 Gate로 판정한다. |
| 9 | Final Inspection·Clean Pack | Particle(microscope 50~200x, critical surface Class 100 기준), cosmetic(scratch/dig per MIL-PRF-13830, 40-20, coating pin hole, color uniformity), optical performance(MTF, power, FOV, distortion test, autocollimator/interferometer), barcode(laser mark/inkjet, ISO grade ≥B, 2D data matrix), clean pack(Class 1000 cleanroom, ESD clean bag + desiccant + N₂ flush + vacuum seal)을 확인한다. |
| 10 | Shipment·Field Feedback Link | High-value scrap(unit cost >$100, MRB 회부, 분석 리포팅, design/manufacturing corrective action), RMA/field failure(module serial로 factory data pull, alignment pre/post shift 비교, failure mode classification, 8D report), module serial history(full genealogy + test data + calibration data archive, lifetime traceable)를 연결한다. |

## 8.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | 产品/光学规格基准 | 确认Optical path(laser diode→lens→sensor/fiber coupling design)、sensor(CMOS/CCD/InGaAs/APD、pixel size、quantum efficiency、dark current)、lens(aspherical/telecentric/wide-angle、EFL、FOV、MTF spec)、actuator(VCM/Piezo/SMA、stroke、hysteresis)、coupling efficiency(≥50~80%、spec per application、coupling loss budget)和对准公差(±0.5~5μm translation、±0.01~0.1° tilt、active alignment target spec)。 |
| 2 | 精密部件入库/洁净管理 | 确认Lens(optical grade glass/plastic、AR coating、scratch-dig 40-20 per MIL-PRF-13830)、sensor(wafer-level package/ceramic LCC、暗信号非均匀性spec)、laser(laser diode VCSEL/EEL、波长公差±1nm、class 1M/3R安全)、fiber(single mode/multi-mode、APC/PC polish、insertion loss spec)、actuator(VCM/Piezo、stroke spec±10%)、housing(金属/陶瓷/液态聚合物精密模具、尺寸±10μm)的lot和particle条件(Class 1,000~10,000 cleanroom、particle count≥0.5μm≤100/ft³、≥5μm≤0/ft³)。 |
| 3 | 清洗/预对准 | 在clean bench(Class 100~1,000)内执行particle removal(IPA/isopropyl alcohol超声波槽5~15min、N₂吹干、60℃干燥箱)、plasma/UV清洗(O₂ plasma 30~60秒、UV ozone 10~30秒、表面能增加提高粘接力)、datum setup(机械治具reference、光学校准相机网格)和预对准(显微镜10~50x目视引导、粗定位±10~50μm)。 |
| 4 | 子模组装配 | 按sub-module serial基准组装Sensor(CMOS/CCD/APD、die attach银环氧/au-tin焊料、wire bonding Au/Al φ25~50μm、N₂ purge)、lens barrel(barrel thread/friction fit/adhesive bond、lens-spacer-lens序列)、actuator(VCM housing装配、suspension wire yoke/magnet)、fiber(fiber ferrule、ceramic sleeve、housing内alignment sleeve)、PCB(FPC/circuit board、ACF bonding/soldering)和housing(激光焊接/UV adhesive/sealing cover)。 |
| 5 | Active Alignment | 实时测量后固定：Focus(lens barrel z-axis motion、PSF测量、depth of field考量、optimal focus position搜索)、tilt(lens/sensor relative tilt、θx/θy调整、±0.01~0.1°)、coupling(laser-fiber或fiber-detector耦合、x/y/z高分辨率piezo stage 0.1~1μm分辨率、power meter实时监测)、optical axis(zero reference对准、collimation测试、centration error<10μm)和MTF/BER/power(positioner使用6-axis hexapod+piezo stage)。Active alignment循环至达成目标值(Alignment Loop)。 |
| 6 | 点胶/UV热固化 | 管理胶水lot(UV固化环氧/热固化硅胶/混合UV+热、保存条件、pot life、expiration)、点胶量(nanoliter~microliter精密点胶机、针头φ0.1~0.5mm、valve jetting系统、重量监测、target±5%)、UV dose(365~405nm、500~5,000mJ/cm²、radiometer测量、intensity 100~1,000mW/cm²)、热固化(80~150℃、30~120min、烘箱均匀性±2℃)和收缩风险(固化后尺寸偏移、应力松弛、对准位移补偿)。 |
| 7 | 电气/光学校准 | 校正Current(laser diode bias current/drive current、I-L曲线测量、threshold current I_th监测)、power(optical output power、mW、校准photodiode、±0.1dB精度)、focus(auto-focus actuator stroke、close-loop position sensor校准、hysteresis补偿)、color(RGB channel gain/offset、white balance matrix、color temperature correction D65)、signal integrity(eye diagram、jitter、rise/fall time、SNR)和温度补偿(温度传感器lookup table校准、-40~+85℃功率自动调整)。 |
| 8 | 环境应力Gate | 用Thermal cycling(-40~+85℃、10~200 cycles、ramp rate 10~15℃/min、dwell 15~30min、per JEDEC JESD22-A104)、湿度(85℃/85%RH、100~500hr biased、per JEDEC JESD22-A101)、振动(sine sweep 5~500Hz 2G/random 5~2,000Hz 6G、30min/axis、per MIL-STD-883 Method 2007)和老化(55~85℃、48~168hr、active operation、通电)后的光学/电气shift(MTF shift≤5%、power drop≤0.5dB、focus shift≤2μm、dark current增加≤10%)进行Gate判定。 |
| 9 | 终检/Clean Pack | 确认Particle(显微镜50~200x、critical surface Class 100标准)、外观(scratch/dig per MIL-PRF-13830、40-20、coating pin hole、color uniformity)、光学性能(MTF、power、FOV、distortion test、autocollimator/interferometer)、条码(laser mark/inkjet、ISO grade≥B、2D data matrix)和洁净包装(Class 1000 cleanroom、ESD洁净袋+desiccant+N₂ flush+vacuum seal)。 |
| 10 | 出货/现场反馈连接 | 将高价值报废(unit cost>$100、MRB移交、分析报告、design/manufacturing corrective action)、RMA/现场失效(按module serial拉取factory数据、alignment前后shift比较、failure mode分类、8D报告)和module serial history(全genealogy+test data+calibration data归档、lifetime traceable)连接。 |

## 8.3 control_points_detail_ko

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 광학 사양 기준 | Optical path, tolerance(±0.5~5μm, ±0.01~0.1°), performance target를 product_spec_id로 고정한다. NPI 시 spec review. 측정 주기: NPI/고객 spec 변경 시. 이상 시 Engineering Change → Design Review → 재승인. | 1 | process_step |
| 2 | 청정·Particle | Particle count(0.5μm ≤100/ft³, 5μm ≤0/ft³ Class 1,000), cleaning lot(IPA/plasma batch), 작업환경 상태를 module serial과 연결한다. Cleanroom 환경 모니터링(매일). 측정 주기: Every Lot(Cleaning) + 매일 환경 monitoring. 이상 시 Cleaning process 재검증 → 설비 점검. | 2,3 | process_step |
| 3 | Sub-module Genealogy | Sensor(CMOS/CCD/APD wafer lot, die ID), lens(optical glass/plastic batch), laser/fiber(VCSEL/EEL serial), housing serial을 module serial에 묶는다. Die attach/bonding 이력 포함. 측정 주기: Every Assembly(scan, vision). 이상 시 Module 전수 재소급 → genealogy 재구축. | 4 | process_step |
| 4 | Active Alignment | Alignment offset(±0.5~5μm, ±0.01~0.1°), coupling efficiency(≥spec), focus/tilt 결과를 반복 보정 loop로 저장한다. 6-axis hexapod + piezo stage positioner 사용. 측정 주기: Every Module(Active Alignment loop). 이상 시 Parameter 조정 → 재 Alignment → 수율 분석. | 5 | process_step |
| 5 | 접착·Cure | Adhesive volume(target ±5%, nanoliter precision), 위치(±0.1mm), UV dose(500~5,000mJ/cm²), cure profile(80~150℃, 30~120min)과 shrinkage risk(post-cure shift compensation)를 관리한다. 측정 주기: Every Module(volume/cure) + Adhesive batch 시작 시. 이상 시 Dispense parameter 조정 → 재작업. | 6 | process_step |
| 6 | Calibration | 광/전기 calibration result(±0.1dB power, eye diagram, SNR, color matrix)와 jig/station drift(daily self-cal + annual external cal)를 추적한다. 측정 주기: Every Module + Jig Daily self-check. 이상 시 Jig 재교정 → 해당 모듈 전수 재보정. | 7 | process_step |
| 7 | Stress Gate | 환경시험 후 shift가 기준(MTF shift ≤5%, power drop ≤0.5dB, focus shift ≤2μm, dark current ≤10%)을 초과하면 Hold/MRB로 전환한다. 측정 주기: Every Module(Stress test). 이상 시 MRB → Root Cause 분석 → Design/Process corrective action. | 8 | process_step |
| 8 | Field Feedback | 고가 scrap(unit cost >$100, MRB), RMA, field failure를 module serial history와 연결한다. Factory baseline data 비교로 failure mode 분류. 측정 주기: RMA/Field Failure 발생 시마다 + 월간 통계 분석. 이상 시 8D Report → Design/Firmware/Process 수정. | 10 | process_step |

## 8.4 control_points_detail_zh

| # | category | text | step_refs | scope |
|---:|---|---|---|---|
| 1 | 光学规格基准 | 用product_spec_id固定Optical path、公差(±0.5~5μm、±0.01~0.1°)和性能目标。NPI时spec review。测量周期：NPI/客户spec变更时。异常时Engineering Change→Design Review→重新批准。 | 1 | process_step |
| 2 | 洁净/Particle | 将particle count(0.5μm≤100/ft³、5μm≤0/ft³ Class 1,000)、cleaning lot(IPA/plasma batch)和作业环境状态连接到module serial。Cleanroom环境监测(每日)。测量周期：Every Lot(Cleaning)+每日环境监测。异常时Cleaning process重新验证→设备点检。 | 2,3 | process_step |
| 3 | 子模组Genealogy | 将Sensor(CMOS/CCD/APD wafer lot、die ID)、lens(optical glass/plastic batch)、laser/fiber(VCSEL/EEL serial)和housing serial绑定到module serial。包含Die attach/bonding履历。测量周期：Every Assembly(scan、vision)。异常时Module全数重新追溯→重建genealogy。 | 4 | process_step |
| 4 | Active Alignment | 将alignment offset(±0.5~5μm、±0.01~0.1°)、coupling efficiency(≥spec)、focus/tilt结果保存为循环校正记录。使用6-axis hexapod+piezo stage positioner。测量周期：Every Module(Active Alignment循环)。异常时调整参数→重新Alignment→良率分析。 | 5 | process_step |
| 5 | 粘接/Cure | 管理胶量(target±5%、nanoliter精度)、位置(±0.1mm)、UV dose(500~5,000mJ/cm²)、固化曲线(80~150℃、30~120min)和收缩风险(固化后偏移补偿)。测量周期：Every Module(点胶量/固化)+Adhesive批次开始时。异常时调整点胶参数→返工。 | 6 | process_step |
| 6 | 校准 | 追踪光/电校准结果(±0.1dB power、eye diagram、SNR、color matrix)和治具/工站漂移(daily self-cal+annual external cal)。测量周期：Every Module+Jig每日自检。异常时Jig重新校准→对应模组全数重新校准。 | 7 | process_step |
| 7 | Stress Gate | 环境试验后的shift超过基准(MTF shift≤5%、power drop≤0.5dB、focus shift≤2μm、dark current≤10%)时转为Hold/MRB。测量周期：Every Module(Stress test)。异常时MRB→Root Cause分析→Design/Process corrective action。 | 8 | process_step |
| 8 | Field Feedback | 将高价值报废(unit cost>$100、MRB)、RMA和现场失效连接到module serial history。通过Factory baseline数据比较进行failure mode分类。测量周期：RMA/Field Failure发生时每次+月度统计分析。异常时8D Report→Design/Firmware/Process修改。 | 10 | process_step |

## 8.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | module_serial,product_spec_id |
| 2 | Material Clean | process |  |  | sensor_serial,lens_serial,housing_lot,particle_count |
| 3 | Pre-align | process |  |  | module_serial,cleaning_lot,particle_count |
| 4 | Sub Assembly | process |  |  | module_serial,sensor_serial,lens_serial,fiber_serial |
| 5 | Active Alignment | process | Alignment Loop |  | module_serial,alignment_offset,coupling_efficiency,MTF_result |
| 6 | Bonding | process |  |  | module_serial,adhesive_lot,dispense_volume,UV_dose,cure_profile |
| 7 | Calibration | process |  |  | module_serial,calibration_result,coupling_efficiency |
| 8 | Stress Gate | gate |  | 5,6,7 | module_serial,stress_test_result,shift_result |
| 9 | Final QA | process |  |  | module_serial,final_inspection_result,particle_count |
| 10 | Field Link | process |  |  | module_serial,RMA_id,final_inspection_result |

## 8.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Spec | process |  |  | module_serial,product_spec_id |
| 2 | Material Clean | process |  |  | sensor_serial,lens_serial,housing_lot,particle_count |
| 3 | Pre-align | process |  |  | module_serial,cleaning_lot,particle_count |
| 4 | Sub Assembly | process |  |  | module_serial,sensor_serial,lens_serial,fiber_serial |
| 5 | Active Alignment | process | Alignment Loop |  | module_serial,alignment_offset,coupling_efficiency,MTF_result |
| 6 | Bonding | process |  |  | module_serial,adhesive_lot,dispense_volume,UV_dose,cure_profile |
| 7 | Calibration | process |  |  | module_serial,calibration_result,coupling_efficiency |
| 8 | Stress Gate | gate |  | 5,6,7 | module_serial,stress_test_result,shift_result |
| 9 | Final QA | process |  |  | module_serial,final_inspection_result,particle_count |
| 10 | Field Link | process |  |  | module_serial,RMA_id,final_inspection_result |

## 8.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 5 | 1 | Pre-measure |
| 5 | 2 | Position Correction |
| 5 | 3 | Optical Verify |
| 8 | 1 | Thermal/Humidity Test |
| 8 | 2 | Shift Review |

## 8.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 5 | 1 | 预测量 |
| 5 | 2 | 位置校正 |
| 5 | 3 | 光学确认 |
| 8 | 1 | 温湿度测试 |
| 8 | 2 | Shift评审 |

## 8.9 data_capture_points

```yaml
- module_serial
- product_spec_id
- sensor_serial
- lens_serial
- laser_serial
- fiber_serial
- housing_lot
- cleaning_lot
- particle_count
- alignment_offset
- coupling_efficiency
- MTF_result
- adhesive_lot
- dispense_volume
- UV_dose
- cure_profile
- calibration_result
- stress_test_result
- shift_result
- final_inspection_result
- RMA_id
```

# 9. 제출 전 self-check

```text
[x] C01~C08 전수, slug당 §N.1~§N.9 섹션 완비
[x] control_points_detail에 category 열 전건 작성
[x] step_expression ko/zh 행 수 = process_steps 행 수
[x] role=gate slug별 1건 이상 또는 검사 Gate 명시
[x] trace_keys ⊆ data_capture_points
[x] ko/zh step_expression #, role, gate_for, trace_keys 동형
[x] en/ja 섹션·문단 없음
[ ] JSON 변환 dry-run은 별도 지시 후 수행
```

# 10. JSON 반영 시 주의

- `process_steps_detail_en/ja=[]`, `control_points_en=[]` 등 legacy 언어 필드는 변환 스크립트에서 강제 비움.
- C04 `legacy_slug: electronic_modules`는 현재 참조표에서 `None`이므로 JSON 반영 전 taxonomy slug 확정 필요.
- C01 `legacy_slug: pcb_pcba`는 기존 참조상 PCB 제조와 PCBA가 혼재되어 있으므로, 실제 UI 명칭이 PCB Fab인지 PCBA 포함인지 최종 확인 필요.
