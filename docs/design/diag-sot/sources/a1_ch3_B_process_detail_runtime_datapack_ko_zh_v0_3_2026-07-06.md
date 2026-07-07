
# B산업 A1 Ch3 공정분석 런타임형 데이터팩 v0.3
## 반도체 / Wafer Fab·Package·Test — 한국어·중국어

> 작성 기준: 2026-07-06  
> 대상: B01~B08  
> 목적: `process_detail_v1.json` 반영 전 검토용 MD 데이터팩  
> 적용 기준: `A1_CH3_B_process_detail_datapack_refactor_instruction_2026-07-06.md`의 v0.3 authoring 규격  
> 언어: 한국어 / 중국어만 작성. `label_en`, `label_ja`는 공백. en/ja 공정·관리점 섹션 작성 금지.  
> 작업 범위: MD 데이터팩 작성만. JSON·코드·변환 스크립트 수정 없음.

---

## 0. 작성 원칙

```yaml
industry_code: B
industry_name_ko: 반도체
industry_name_zh: 半导体
expression_tier: P3_PFLOW
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

### 0.2 B산업 공통 표현 규칙

| 코드 | 세부산업 | legacy_slug | routing | preset_id | 핵심 표현 단위 |
|---|---|---|---|---|---|
| B01 | 로직 파운드리 | `logic_foundry` | RT_REENTRANT | `reentrant_module_v1` | FEOL / MEOL / BEOL / Inline Gate / WAT·Sort |
| B02 | 메모리 DRAM·NAND | `memory_dram_nand` | RT_REENTRANT | `reentrant_module_v1` | Cell / Array / 3D Stack / Redundancy / Sort |
| B03 | 아날로그·혼합신호 IC | `analog_mixed` | RT_REENTRANT | `reentrant_module_v1` | Device / Passive / Trim / Characterization |
| B04 | 전력반도체·디스크리트 | `power_discrete` | RT_BATCH | `batch_process_v1` | Frontside / Backside / Probe / Reliability |
| B05 | 광학·이미지센서 | `optical_sensor` | RT_REENTRANT | `reentrant_module_v1` | Pixel / Readout / Optical Stack / Image Test |
| B06 | 화합물반도체 | `compound_semi` | RT_BATCH | `batch_process_v1` | Epi / Mesa / Ohmic / Gate / RF·DC Probe |
| B07 | 반도체 조립·패키징 | `assembly_packaging` | RT_BATCH | `packaging_linear_v1` | Die Prep / Attach / Interconnect / Mold / Final Test |
| B08 | 반도체 테스트 서비스 | `test` | RT_BATCH | `test_service_v1` | Program / Tester / Handler·Prober / STDF / Bin |

### 0.3 산업 현황 반영 메모

```yaml
trend_reflection_ko:
  B01: FEOL/MEOL/BEOL 모듈화, Inline Metrology, Yield Disposition, 고객별 공정·수율 정보 보안, Digital Twin 전면 배포(NVIDIA Omniverse), AI Agent 기반 R2R 제어, APC/FDC 고도화
  B02: 3D NAND 수직 적층, 고종횡비 계측, HBM/Package 인계, Redundancy Repair, 실시간 스케줄링(RTS) 최적화, AI 기반 장비 예측 정비
  B03: 고전압·저잡음·정밀 Passive, Trim/Fuse, Characterization과 고객 Grade, Laser Trim 자동화, Parametric 분포 AI 분석
  B04: Backside Thinning/Metal, BV/Rds(on)/Leakage, 전력 신뢰성 샘플 관리, SiC/GaN 공정 자동화, Batch Recipe 중앙 관리
  B05: Pixel Defect, Color Filter/Microlens, Optical/Electrical 동시 Bin 관리, Recipe-less AI 검사 도입, 엣지 AI 기반 실시간 결함 탐지
  B06: Epi 품질, Reactor/Run 추적, RF/DC Probe, SiC/GaN/GaAs/InP 소재별 이력, MOCVD/MBE Reactor AI 모니터링
  B07: Die genealogy, Die attach, Wire/Flip-chip interconnect, Mold, X-ray/Warpage, Final Test, SCARA 로봇·머신 비전 통합, Lights-out 패키징 팹
  B08: Test Program Revision, Tester/Socket/Probe 이력, STDF, Retest/Hold, 고객 데이터 보안, CIM 2.0 기반 데이터 사일로 해소
trend_reflection_zh:
  B01: FEOL/MEOL/BEOL模块化、Inline Metrology、Yield Disposition、客户工艺/良率信息安全、Digital Twin全面部署(NVIDIA Omniverse)、AI Agent R2R控制、APC/FDC升级
  B02: 3D NAND垂直堆叠、高深宽比量测、HBM/Package交接、Redundancy Repair、实时调度(RTS)优化、AI设备预测维护
  B03: 高压/低噪声/精密Passive、Trim/Fuse、Characterization与客户Grade、Laser Trim自动化、Parametric分布AI分析
  B04: Backside减薄/金属化、BV/Rds(on)/Leakage、功率可靠性样本管理、SiC/GaN工艺自动化、Batch Recipe中央管理
  B05: Pixel Defect、Color Filter/Microlens、Optical/Electrical Bin协同管理、Recipe-less AI检测、边缘AI实时缺陷检测
  B06: Epi质量、Reactor/Run追踪、RF/DC Probe、SiC/GaN/GaAs/InP材料履历、MOCVD/MBE Reactor AI监控
  B07: Die genealogy、Die attach、Wire/Flip-chip interconnect、Mold、X-ray/Warpage、Final Test、SCARA机器人/机器视觉集成、Lights-out封装工厂
  B08: Test Program版本、Tester/Socket/Probe履历、STDF、Retest/Hold、客户数据安全、CIM 2.0数据孤岛消除
```

---

# 1. B01 — 로직 파운드리

```yaml
subindustry_code: B01
legacy_slug: logic_foundry
label_ko: 로직 파운드리
label_zh: 逻辑晶圆代工
label_en: ""
label_ja: ""
routing: RT_REENTRANT
preset_id: reentrant_module_v1
expression_tier: P3_PFLOW_REENTRANT
routing_description_ko: >
  로직 파운드리는 FEOL/MEOL/BEOL이 반복 진입되는 Wafer Fab 구조다. Ch3는 Litho/Etch/CMP를 독립 대단계로 과도하게 펼치기보다 Module, Gate, Rework/Loop, Inline Metrology를 중심으로 표현한다. 2026년 기준, 디지털 트윈(NVIDIA Omniverse 기반)과 AI Agent 기반 R2R 제어가 전 공정에 확대 적용 중이며, SECS/GEM 기반 EAP로 실시간 장비 데이터를 수집·분석한다.
routing_description_zh: >
  逻辑晶圆代工是FEOL/MEOL/BEOL反复进入的晶圆厂流程。Ch3不应把Litho/Etch/CMP过度拆成独立大阶段，而应以Module、Gate、返工/循环和Inline Metrology为中心表达。2026年起基于NVIDIA Omniverse的Digital Twin和AI Agent的R2R控制已全面部署，通过SECS/GEM协议的EAP实时采集设备数据。
```

## 1.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Wafer Start | 제품·공정 Flow, Mask Set, Route Revision, Lot Priority와 Wafer 투입 조건을 확정한다. MES(예: Siemens Opcenter, SAP ME)에서 Route·Mask 일치성을 검증하고, Lot ID 기준 Wafer Start 장비(예: DISCO DFG3640 Grinder 또는 DNS/SCREEN Coater)에 투입 명령을 내린다. 장비·Recipe Lock을 확인하고 Lot 단위 Serial/Lot Number를 생성한다. |
| 2 | FEOL Module 1 — STI / Isolation | Pad Oxide(LPCVD Furnace, 780~850℃), Nitride Deposition(LPCVD SiN, 750℃), Trench Lithography(ASML NXT/DUV Scanner, CD Target), Trench Etch(Lam Research Kiyo / Tokyo Electron, 고밀도 플라즈마 식각기), HDP·CVD Fill(Applied Materials, 200~400nm), STI CMP(Applied Materials Mirra/EBARA, Oxide Removal 300~500nm)를 통해 소자 격리 구조를 형성한다. Trench CD·Profile은 CD-SEM(Hitachi)으로 Lot당 샘플링 계측한다. |
| 3 | FEOL Module 2 — Well / Channel / Gate | Well Implant(Applied Materials VIISta / Axcelis, Energy 200~600keV, Dose 1e13~1e14 /cm²), Channel Engineering Implant, Gate Stack Formation(Furnace Oxidation 900~1050℃ or ALD High-k HfO₂, 2~3nm), Poly-Si Deposition(LPCVD 620℃), Gate Litho/Etch(ASML Scanner + Lam Etcher, CD 7~5nm), Spacer Deposition(Nitride ALD/CVD)과 Anneal 조건을 관리한다. Gate CD는 Lot당 Inline CD-SEM으로 관리하며, Target 대비 3σ 편차 <2nm를 유지한다. |
| 4 | FEOL Module 3 — Source/Drain / Contact | S/D Extension Implant, HALO/Pocket Implant, Activation RTP(Rapid Thermal Processing, Applied Materials Centura, 1000~1050℃ Spike Anneal), Silicide Formation(NiPt/Ti, RTP 400~500℃), Contact Etch(Lam Versys / TEL, Oxide/Nitride 선택비>15:1), Contact Fill(CVD W / ALD Barrier TiN)와 접촉저항(Rc <10Ω·μm²)을 관리한다. Contact Resistance는 Kelvin 구조 PCM으로 WAT 단계에서 검증한다. |
| 5 | MEOL Module — Local Interconnect | Contact/Via Etch & Fill, Local Interconnect Metal Deposition(CVD/ALD TiN Barrier, CVD W Plug), Metal CMP(Applied Materials Reflexion, Cu/Low-k)를 통해 소자와 금속층을 연결한다. 각층 Via Resistance는 4-Point Probe 방식으로 Inline 계측하며, CMP 후 Oxide 두께 균일도는 Ellipsometer(KLA-Tencor Aleris)로 Lot당 3~5점 측정한다. |
| 6 | BEOL Module — Metal Stack Loop | Metal Layer별 Litho(ASML NXE/EUV Scanner, Overlay <3nm → 2nm 이하 공정), Low-k Dielectric Etch(Lam Kiyo / TEL, CD Bias <1nm), Cu Barrier/Seed(PVD/ALD TaN/Cu), Cu ECD(Applied Materials, 전해도금 0.5~2A/dm²), Cu CMP(Applied Materials Reflexion / Ebara, Cu Thinning 100~300nm)가 반복되며 층간 Overlay, CD, Cu Void Defect, Sheet Resistance(Rs)를 관리한다. Overlay는 KLA Archer 또는 ASML YieldStar로 Layer당 전체 Field 측정한다. 14~2nm 공정에서 BEOL Loop는 8~15회 반복된다. |
| 7 | Top Metal / Pad / Passivation | Top Metal(Al or Cu, PVD 1~4μm), Pad Open Litho/Etch, Passivation Deposition(SiN/SiON PECVD 300~400℃), Bond Pad Surface Defect 검사(Optical Microscope + SEM Review, KLA / AMAT)를 통해 보호막 결함과 Pad 상태를 관리한다. Passivation Pin Hole은 Voltage Contrast SEM으로 검출한다. |
| 8 | Inline Metrology Gates — CD / Overlay / Defect | 핵심 Module 후 CD-SEM(Hitachi CG5000 / Applied Materials, Gate Poly CD·Metal CD 계측), Overlay(ASML YieldStar / KLA Archer, 각 층간 정렬 오차), Film Thickness Ellipsometer, Defect Inspection(KLA 29xx/39xx Brightfield / AMAT UVision, Dense Pattern 결함 검출), Electrical Monitor(In-line Rs/Ψ Probe)를 Gate로 판정한다. Spec 이탈 시 SECS/GEM 기반 자동 Hold → FDC(Fault Detection & Classification) 원인 분석 → MRB 흐름으로 전환된다. |
| 9 | Electrical Test — PCM/WAT / Wafer Sort | PCM/WAT(Parametric Test, Agilent 4070 Series / Keysight, 온도 25~85℃, Vt, Idsat, Rc, Rs, Leakage), Wafer Sort(Probe Card Contact, Teradyne Ultraflex / Advantest 93K, Speed Bin), Bin Map을 통해 전기적 특성과 Die 등급을 판정한다. WAT Test Key는 각 Shot 내 PCM 영역에서 Lot당 전수 측정하며, Wafer Sort는 Tester / Handler / Probe Card 조합으로 Die당 전수 테스트한다. Yield Management System(YMS, Synopsys / PDF Solutions)에 Bin 결과를 실시간 업로드한다. |
| 10 | Disposition — Yield Review / Wafer Out | 수율(Yield Loss Code별 분석, Bin Map 패턴, Spatial Signature), 불량 패턴(KLA Defect Map Overlay), Hold/Release(MRB 회의, 고객 통보 필요성), Scrap/Rework 기준, 고객 출하 조건을 검토하고 Wafer Out을 처리한다. YMS Dashboard에서 Lot·Wafer·Module별 수율을 종합 분석하며, 최종 Disposition Code를 MES에 기록한다. |

## 1.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Wafer Start | 确认产品/工艺Flow、Mask Set、Route版本、Lot优先级和Wafer投入条件。MES(如Siemens Opcenter、SAP ME)验证Route/Mask一致性，向Wafer Start设备(如DISCO DFG3640 Grinder或DNS/SCREEN Coater)发出投入指令。确认设备/Recipe锁定后生成Lot级Serial/Lot Number。 |
| 2 | FEOL Module 1 — STI / Isolation | 通过Pad Oxide(LPCVD Furnace，780~850℃)、Nitride Deposition(LPCVD SiN，750℃)、Trench Lithography(ASML NXT/DUV Scanner，CD Target)、Trench Etch(Lam Research Kiyo/Tokyo Electron高密度等离子刻蚀机)、HDP·CVD Fill(Applied Materials，200~400nm)、STI CMP(Applied Materials Mirra/EBARA，Oxide去除300~500nm)形成器件隔离结构。Trench CD/Profile用CD-SEM(Hitachi)按Lot抽样量测。 |
| 3 | FEOL Module 2 — Well / Channel / Gate | 管理Well Implant(Applied Materials VIISta/Axcelis，Energy 200~600keV，Dose 1e13~1e14/cm²)、Channel Engineering Implant、Gate Stack Formation(Furnace Oxidation 900~1050℃或ALD High-k HfO₂，2~3nm)、Poly-Si Deposition(LPCVD 620℃)、Gate Litho/Etch(ASML Scanner+Lam Etcher，CD 7~5nm)、Spacer Deposition(Nitride ALD/CVD)和Anneal条件。Gate CD按Lot用Inline CD-SEM管理，目标3σ偏差<2nm。 |
| 4 | FEOL Module 3 — Source/Drain / Contact | 管理S/D Extension Implant、HALO/Pocket Implant、Activation RTP(Rapid Thermal Processing，Applied Materials Centura，1000~1050℃ Spike Anneal)、Silicide Formation(NiPt/Ti，RTP 400~500℃)、Contact Etch(Lam Versys/TEL，Oxide/Nitride选择比>15:1)、Contact Fill(CVD W/ALD Barrier TiN)和接触电阻(Rc<10Ω·μm²)。Contact Resistance通过WAT阶段Kelvin结构PCM验证。 |
| 5 | MEOL Module — Local Interconnect | 通过Contact/Via Etch&Fill、Local Interconnect Metal Deposition(CVD/ALD TiN Barrier，CVD W Plug)、Metal CMP(Applied Materials Reflexion，Cu/Low-k)连接器件和金属层。每层Via Resistance用4-Point Probe方式Inline量测，CMP后Oxide厚度均匀性用Ellipsometer(KLA-Tencor Aleris)按Lot测3~5点。 |
| 6 | BEOL Module — Metal Stack Loop | 按Metal Layer反复执行Litho(ASML NXE/EUV Scanner，Overlay<3nm→2nm以下工艺)、Low-k Dielectric Etch(Lam Kiyo/TEL，CD Bias<1nm)、Cu Barrier/Seed(PVD/ALD TaN/Cu)、Cu ECD(Applied Materials，电镀0.5~2A/dm²)、Cu CMP(Applied Materials Reflexion/Ebara，Cu减薄100~300nm)。管理层间Overlay、CD、Cu Void Defect和Sheet Resistance(Rs)。Overlay用KLA Archer或ASML YieldStar按Layer全Field测量。14~2nm工艺中BEOL Loop重复8~15次。 |
| 7 | Top Metal / Pad / Passivation | 管理Top Metal(Al或Cu，PVD 1~4μm)、Pad Open Litho/Etch、Passivation Deposition(SiN/SiON PECVD 300~400℃)、Bond Pad Surface Defect检查(Optical Microscope+SEM Review，KLA/AMAT)和保护膜缺陷及Pad状态。Passivation Pin Hole用Voltage Contrast SEM检测。 |
| 8 | Inline Metrology Gates — CD / Overlay / Defect | 在关键Module后以CD-SEM(Hitachi CG5000/Applied Materials，Gate Poly CD·Metal CD量测)、Overlay(ASML YieldStar/KLA Archer，各层间对准误差)、Film Thickness Ellipsometer、Defect Inspection(KLA 29xx/39xx Brightfield/AMAT UVision，Dense Pattern缺陷检测)、Electrical Monitor(In-line Rs/Ψ Probe)作为Gate判定。超Spec时通过SECS/GEM自动Hold→FDC(Fault Detection&Classification)原因分析→MRB流程处理。 |
| 9 | Electrical Test — PCM/WAT / Wafer Sort | 通过PCM/WAT(Parametric Test，Agilent 4070 Series/Keysight，温度25~85℃，Vt、Idsat、Rc、Rs、Leakage)、Wafer Sort(Probe Card Contact，Teradyne Ultraflex/Advantest 93K，Speed Bin)、Bin Map判定电性和Die等级。WAT Test Key按Shot内PCM区域Lot全测，Wafer Sort用Tester/Handler/Probe Card组合对Die全测。Bin结果实时上传Yield Management System(YMS，Synopsys/PDF Solutions)。 |
| 10 | Disposition — Yield Review / Wafer Out | 复核良率(Yield Loss Code分析、Bin Map图形、Spatial Signature)、缺陷图形(KLA Defect Map叠加)、Hold/Release(MRB会议、客户通知必要性)、Scrap/Rework标准和客户出货条件，完成Wafer Out。YMS Dashboard综合分析Lot/Wafer/Module级良率，最终Disposition Code写入MES。 |

## 1.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Route·Mask·Revision 기준선 | Wafer Start 전 제품·Route·Mask Set·공정 Revision의 일치성을 확인해야 한다. 측정 방법: MES(Opcenter/SAP) 자동 비교 검증. 관리 주기: Lot 투입 시점(Every Lot). 이상 시 조치: 불일치 시 Lot Hold → Route Engineer 검토 → 수정 후 Release. | 1 | process_step | Route Control |
| 2 | FEOL Module별 Recipe Lock | Implant, Gate, Contact 계열 공정은 Recipe·Chamber·PM상태가 Lot 투입 전 Lock되어야 한다. 측정 장비: APC/R2R 시스템(Applied Materials / Synopsys) + EAP SECS/GEM 통신. 관리 주기: Recipe 변경 시마다(Real-time). 이상 시 조치: Recipe Lock Violation → FDC Alarm → Equipment Engineer 긴급 검토 → Lot 투입 차단. | 2,3,4 | process_step | FEOL Recipe Control |
| 3 | BEOL Metal Loop 관리 | Metal Layer 반복 공정은 Layer별 Reticle, CD, Overlay, CMP 결과를 층 단위로 추적해야 한다. 측정 장비/방법: Overlay(ASML YieldStar/KLA Archer), CD(Hitachi CG5000). 관리 주기: Layer당 전수(Every Layer). 이상 시 조치: Overlay > Spec → Auto Hold → Reticle Inspection / Recipe Adjust → Re-measure. | 6 | process_step | BEOL Loop Control |
| 4 | Inline Gate 판정 | CD/Overlay/Defect/Film 결과가 Spec을 벗어나면 자동 Hold와 MRB 흐름으로 연결해야 한다. 측정 장비: KLA 29xx Brightfield, AMAT UVision Defect Inspection, CD-SEM, Ellipsometer. 관리 주기: Module 완료 후 Lot당 샘플링(Every Module). 이상 시 조치: Auto Hold → FDC 패턴 분석(장비 이상 vs 공정 이상) → Scrap/Rework/Release 결정. | 8 | process_step | Inline Quality Gate |
| 5 | PCM/WAT와 Sort 연계 | PCM/WAT 결과와 Wafer Sort Bin Map을 연결해 전기적 불량 패턴을 분석해야 한다. 측정 장비: Keysight 4070 Series(Parametric), Teradyne Ultraflex/Advantest 93K(Sort). 관리 주기: Every Lot. 이상 시 조치: WAT-Sort Correlation 분석 → Low Yield Lot Hold → PCM Test Key 검증 → Bin Map Spatial Signature 분석 → MRB. | 9 | process_step | Electrical Yield |
| 6 | Yield Review와 Disposition | 수율 저하 Lot은 Hold, Release, Scrap, Rework, Customer Notice 기준으로 판정해야 한다. 측정 방법: YMS(Synopsys/PDF Solutions) 대시보드 분석, Bin Map + Defect Map Overlay 검토. 관리 주기: Lot 종료 시점마다(Every Lot). 이상 시 조치: Yield Threshold 이하 → MRB 회의 소집 → 고객 통보 판단 → Disposition Code(Scrap/Rework/Release w/ downgrade) 결정. | 10 | process_step | Disposition |
| 7 | Wafer Genealogy | Lot-Wafer-Route-Equipment-Chamber-Recipe 이력을 Die 등급과 연결해야 한다. 측정 방법: MES + EAP 데이터 자동 수집, Genealogy DB(Oracle / PostgreSQL) 조회. 관리 주기: Real-time(장비 작업 완료 시마다). 이상 시 조치: 추적 불가 능 Lot → Full Hold → Data Reconciliation 후 Release. | 1,2,3,4,5,6,7,9 | process_step | Genealogy |
| 8 | 고객별 공정 보안 | Foundry 고객별 Mask, Recipe, Yield 정보 접근권한을 분리해야 한다. 측정 방법: IAM(Identity & Access Management) Audit Log 분석. 관리 주기: 정기적(월/분기 Audit). 이상 시 조치: 무단 접근 감지 → 접근 차단 + 보안 사고 보고서 작성. |  | industry | Customer Data Security |

## 1.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Route·Mask·Revision基线 | Wafer Start前必须确认产品、Route、Mask Set和工艺版本一致。测量方法：MES(Opcenter/SAP)自动比对验证。管理周期：Lot投入时(Every Lot)。异常处理：不一致时Lot Hold→Route Engineer审核→修正后Release。 | 1 | process_step | Route Control |
| 2 | FEOL Module Recipe锁定 | Implant、Gate、Contact类工序在Lot投入前必须锁定Recipe、Chamber和PM状态。测量设备：APC/R2R系统(Applied Materials/Synopsys)+EAP SECS/GEM通信。管理周期：Recipe变更时(Real-time)。异常处理：Recipe Lock Violation→FDC Alarm→设备工程师紧急审核→阻止Lot投入。 | 2,3,4 | process_step | FEOL Recipe Control |
| 3 | BEOL Metal Loop管理 | Metal Layer循环工序必须按层追踪Reticle、CD、Overlay和CMP结果。测量设备/方法：Overlay(ASML YieldStar/KLA Archer)、CD(Hitachi CG5000)。管理周期：每层全数(Every Layer)。异常处理：Overlay>Spec→Auto Hold→Reticle Inspection/Recipe Adjust→重新量测。 | 6 | process_step | BEOL Loop Control |
| 4 | Inline Gate判定 | CD/Overlay/Defect/Film结果超出Spec时，应自动连接Hold和MRB流程。测量设备：KLA 29xx Brightfield、AMAT UVision Defect Inspection、CD-SEM、Ellipsometer。管理周期：Module完成后每Lot抽样(Every Module)。异常处理：Auto Hold→FDC图形分析(设备异常vs工艺异常)→Scrap/Rework/Release判定。 | 8 | process_step | Inline Quality Gate |
| 5 | PCM/WAT与Sort联动 | 需将PCM/WAT结果与Wafer Sort Bin Map连接，分析电性不良图形。测量设备：Keysight 4070 Series(Parametric)、Teradyne Ultraflex/Advantest 93K(Sort)。管理周期：Every Lot。异常处理：WAT-Sort Correlation分析→Low Yield Lot Hold→PCM Test Key验证→Bin Map Spatial Signature分析→MRB。 | 9 | process_step | Electrical Yield |
| 6 | Yield Review与Disposition | 低良率Lot应按Hold、Release、Scrap、Rework、Customer Notice标准判定。测量方法：YMS(Synopsys/PDF Solutions)仪表板分析、Bin Map+Defect Map叠加审核。管理周期：Lot结束时(Every Lot)。异常处理：Yield低于阈值→MRB会议召集→客户通知判断→Disposition Code(Scrap/Rework/Downgrade Release)确定。 | 10 | process_step | Disposition |
| 7 | Wafer Genealogy | 需把Lot-Wafer-Route-Equipment-Chamber-Recipe履历与Die等级连接。测量方法：MES+EAP数据自动采集、Genealogy DB(Oracle/PostgreSQL)查询。管理周期：Real-time(设备作业完成时)。异常处理：追溯不可行Lot→Full Hold→Data Reconciliation后Release。 | 1,2,3,4,5,6,7,9 | process_step | Genealogy |
| 8 | 客户工艺数据安全 | Foundry需按客户隔离Mask、Recipe和Yield信息访问权限。测量方法：IAM(Identity&Access Management)审计日志分析。管理周期：定期(月/季度审计)。异常处理：检测到未授权访问→阻断访问+安全事件报告。 |  | industry | Customer Data Security |

## 1.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, product_id, route_rev, mask_set_id |
| 2 | FEOL | process |  |  | lot_id, wafer_id, recipe_id, equipment_id, chamber_id |
| 3 | FEOL | process |  |  | recipe_id, equipment_id, chamber_id, reticle_id, spc_rule |
| 4 | FEOL | process |  |  | recipe_id, equipment_id, chamber_id, cd_result, spc_rule |
| 5 | MEOL | process |  |  | recipe_id, equipment_id, film_thickness, cd_result |
| 6 | BEOL | process | Metal Stack Loop |  | recipe_id, equipment_id, reticle_id, cd_result, overlay_result |
| 7 | Passivation | process |  |  | recipe_id, equipment_id, film_thickness, defect_map |
| 8 | Inline Gate | gate |  | 2,3,4,5,6,7 | cd_result, overlay_result, film_thickness, defect_map, spc_rule, hold_code |
| 9 | Electrical Test | process |  |  | pcm_result, wat_result, wafer_sort_bin, defect_map |
| 10 | Disposition | process |  |  | yield_loss_code, hold_code, mrb_disposition, wafer_sort_bin |

## 1.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, product_id, route_rev, mask_set_id |
| 2 | FEOL | process |  |  | lot_id, wafer_id, recipe_id, equipment_id, chamber_id |
| 3 | FEOL | process |  |  | recipe_id, equipment_id, chamber_id, reticle_id, spc_rule |
| 4 | FEOL | process |  |  | recipe_id, equipment_id, chamber_id, cd_result, spc_rule |
| 5 | MEOL | process |  |  | recipe_id, equipment_id, film_thickness, cd_result |
| 6 | BEOL | process | Metal Stack Loop |  | recipe_id, equipment_id, reticle_id, cd_result, overlay_result |
| 7 | Passivation | process |  |  | recipe_id, equipment_id, film_thickness, defect_map |
| 8 | Inline Gate | gate |  | 2,3,4,5,6,7 | cd_result, overlay_result, film_thickness, defect_map, spc_rule, hold_code |
| 9 | Electrical Test | process |  |  | pcm_result, wat_result, wafer_sort_bin, defect_map |
| 10 | Disposition | process |  |  | yield_loss_code, hold_code, mrb_disposition, wafer_sort_bin |

## 1.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | Pad Oxide Growth |
| 2 | 2 | Nitride Deposition |
| 2 | 3 | Trench Lithography / Etch |
| 2 | 4 | Trench Fill |
| 2 | 5 | STI CMP |

## 1.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 2 | 1 | Pad Oxide生长 |
| 2 | 2 | Nitride沉积 |
| 2 | 3 | Trench光刻/刻蚀 |
| 2 | 4 | Trench填充 |
| 2 | 5 | STI CMP |

## 1.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - product_id
  - route_rev
  - mask_set_id
  - recipe_id
  - equipment_id
  - chamber_id
  - reticle_id
  - cd_result
  - overlay_result
  - film_thickness
  - defect_map
  - spc_rule
  - hold_code
  - pcm_result
  - wat_result
  - wafer_sort_bin
  - yield_loss_code
  - mrb_disposition
```

---

# 2. B02 — 메모리 DRAM·NAND

```yaml
subindustry_code: B02
legacy_slug: memory_dram_nand
label_ko: 메모리 DRAM·NAND
label_zh: 存储器DRAM·NAND
label_en: ""
label_ja: ""
routing: RT_REENTRANT
preset_id: reentrant_module_v1
expression_tier: P3_PFLOW_REENTRANT
routing_description_ko: >
  메모리 Fab은 Cell Array, Periphery, 3D Stack, Redundancy, Wafer Sort와 제품 등급화가 핵심이다. 3D NAND는 수직 적층·고종횡비 Etch·Channel Hole·Staircase·Bonding 계열 계측이 중요하다. 2026년 기준 DRAM은 EUV 적용 레이어 확대, NAND는 400단 이상 V-NAND 적층이 진행 중이며, AI 기반 실시간 스케줄링(RTS)과 장비 예측 정비로 OEE 극대화를 추구한다.
routing_description_zh: >
  存储器Fab以Cell Array、Periphery、3D Stack、Redundancy、Wafer Sort和产品分级为核心。3D NAND特别强调垂直堆叠、高深宽比刻蚀、Channel Hole、Staircase和Bonding相关量测。2026年DRAM扩大EUV层数，NAND推进400+层V-NAND堆叠，通过AI实时调度(RTS)和设备预测维护追求OEE最大化。
```

## 2.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Memory Product Start | DRAM/NAND 제품군, Density, Layer 수, Route, Mask, Lot Priority를 확정하고 Wafer를 투입한다. MES에서 제품군별 고유 Route·Test Recipe 매핑을 검증하고, AMHS(OHT, Daifuku / Murata)가 FOUP을 최초 장비로 자동 이송한다. Lot Number 기준 Serial 추적을 시작하며, DRAM(DDR5/LPDDR5/HBM)과 NAND(TLC/QLC/400단) 제품군별로 Baseline Recipe가 구분된다. |
| 2 | Periphery CMOS Formation | Decoder, Sense Amp, Peripheral Logic 등 주변회로(Core CMOS) 소자 형성 조건을 관리한다. Gate Oxide Furnace(850~950℃), Poly/Metal Gate, Implant(Axcelis / Applied Materials, 저에너지 고전류), Contact 형성 등 FEOL에 준하는 공정을 사용한다. Vt, Leakage 등 Periphery Parametric Spec을 Lot 단위로 관리하며, CD-SEM(Hitachi CG)으로 게이트 CD를 계측한다. |
| 3 | Cell Array Formation | DRAM Capacitor(Access Transistor + MIS/MIM Capacitor, High-k ZAZ/ZrO₂-Al₂O₃-ZrO₂ ALD, 400~500℃) 또는 NAND Cell Array 계열 핵심 구조를 형성한다. DRAM은 Cell Capacitor CD 및 Capacitance(Cell CAP >20fF/cell), NAND는 Cell Vt 분포를 Lot·Wafer 단위로 관리한다. Cell Array Litho는 ASML NXT/EUV Scanner, Etch는 Lam/TEL 고밀도 식각 장비를 사용한다. |
| 4 | 3D Stack / Channel Hole Module | 3D NAND의 Oxide/Nitride Stack(ONON 반복 Deposition, LPCVD/PECVD 600~800℃, Layer 수 200~400+), High Aspect Ratio Etch(Channel Hole 직경 60~100nm, Depth 5~10μm, Lam/TEL HAR Etcher), Channel Fill(Poly-Si Channel, CVD), Staircase Formation(Staircase Litho + CDE, 20~40 step)을 관리한다. HAR Profile은 SEM/TEM Cross-section으로 Layer별 샘플링 계측하고, Channel Hole CD 및 Void 여부를 Inline Defect Inspection으로 확인한다. |
| 5 | Interconnect / Contact / Plug | Cell·Periphery 연결을 위한 Contact(W Plug CVD), Plug(Poly-Si), Metal(Cu or W), Via(Cu Dual Damascene)와 저항 특성을 관리한다. Contact Resistance는 Kelvin PCM 구조로 WAT에서 검증하며, Sheet Resistance는 4-Point Probe로 Inline 계측한다. Cu CMP는 Applied Materials Reflexion / Ebara 장비를 사용한다. |
| 6 | Array·Stack Inline Gate | CD(Hitachi CG5000), Overlay(ASML YieldStar), Film Thickness( Ellipsometer KLA Aleris), Defect(KLA Brightfield / AMAT UVision), High Aspect Ratio 계측(HAR SEM/OCD) 결과를 Gate로 판정한다. DRAM Cell Capacitor CD와 NAND Channel Hole CD가 Spec 이탈 시 FDC 원인 분석 → 자동 Hold → MRB 흐름으로 연결된다. |
| 7 | Redundancy / Repair Data Generation | 불량 Cell/Block 분석(Fuse Repair Circuit, Laser Repair Equipment, KLA / Hitachi), Redundancy Map 생성, Repair Code를 생성한다. DRAM은 Row/Column Redundancy, NAND는 Block Replacement 방식이다. Repair Code는 Wafer Sort 결과와 연동하여 생성되며, Laser Fuse Blowing(DSM / Electro Scientific Industries)으로 물리적 Repair를 실행한다. |
| 8 | Wafer Sort / Electrical Test | Wafer Sort(Teradyne J750 / Advantest T5503, 온도 -40~125℃), Probe Card Contact, Speed/Retention/Leakage Test(Screen Bin, Speed Bin, Retention 시간), Bin Map을 생성한다. DRAM은 Refresh Time, Row Hammer, Retention 특성, NAND는 Program/Erase Cycle, Read Disturb, Retention 특성을 핵심 Test Item으로 관리한다. Bin 결과는 YMS에 실시간 수집된다. |
| 9 | Package / HBM Handoff | Known Good Die(KGD, Wafer Sort에서 Grade A/B/C로 분류), Stack/Package 투입 조건, HBM(HBM4 기준 16~24Hi Stack)·MCP(Multi-Chip Package) 등 후공정 인계 데이터를 만든다. Die Grade Map, Wafer Map, Laser Mark Code를 Package Assembly(MCP/HBM 라인)에 전달하고, 인계 데이터의 무결성은 ECC/Checksum으로 검증한다. |
| 10 | Yield Analysis / Product Grade | Layer·Cell·Block·Die 기준 수율 손실(Memory Cell Failure Bit Count, Row/Column Fail, Block Fail)과 제품 Grade(Speed Grade: DDR5-4800/5600/6400, NAND Grade: pSLC/MLC/TLC/QLC, HBM Bandwidth Grade)를 확정한다. YMS(Synopsys / PDF)에서 Layer별·Die별 수율 분석과 Spatial Signature 분석을 통해 Yield Loss Root Cause를 식별한다. |

## 2.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Memory Product Start | 确认DRAM/NAND产品族、Density、Layer数、Route、Mask和Lot优先级后投入Wafer。MES验证产品族专属Route/Test Recipe映射，AMHS(OHT，Daifuku/Murata)将FOUP自动运送至初设备。以Lot Number开始Serial追踪，按产品族(DRAM DDR5/LPDDR5/HBM、NAND TLC/QLC/400层)区分Baseline Recipe。 |
| 2 | Periphery CMOS Formation | 管理Decoder、Sense Amp、Peripheral Logic等外围电路(核心CMOS)器件形成条件。使用Gate Oxide Furnace(850~950℃)、Poly/Metal Gate、Implant(Axcelis/Applied Materials，低能高电流)、Contact形成等接近FEOL的工艺。按Lot管理Vt、Leakage等Periphery Parametric Spec，用CD-SEM(Hitachi CG)量测Gate CD。 |
| 3 | Cell Array Formation | 形成DRAM Capacitor(Access Transistor+MIS/MIM Capacitor，High-k ZAZ/ZrO₂-Al₂O₃-ZrO₂ ALD，400~500℃)或NAND Cell Array核心结构。DRAM管理Cell Capacitor CD和Capacitance(Cell CAP>20fF/cell)，NAND管理Cell Vt分布(按Lot/Wafer)。Cell Array Litho用ASML NXT/EUV Scanner，Etch用Lam/TEL高密度刻蚀机。 |
| 4 | 3D Stack / Channel Hole Module | 管理3D NAND的Oxide/Nitride Stack(ONON循环沉积，LPCVD/PECVD 600~800℃，层数200~400+)、高深宽比刻蚀(Channel Hole直径60~100nm，深度5~10μm，Lam/TEL HAR刻蚀机)、Channel Fill(Poly-Si Channel，CVD)、Staircase Formation(Staircase Litho+CDE，20~40 step)。HAR Profile用SEM/TEM截面按Layer抽样量测，Channel Hole CD和Void通过Inline Defect Inspection确认。 |
| 5 | Interconnect / Contact / Plug | 管理Cell与Periphery连接所需的Contact(W Plug CVD)、Plug(Poly-Si)、Metal(Cu或W)、Via(Cu Dual Damascene)及电阻特性。Contact Resistance通过WAT的Kelvin PCM结构验证，Sheet Resistance用4-Point Probe Inline量测。Cu CMP使用Applied Materials Reflexion/Ebara设备。 |
| 6 | Array·Stack Inline Gate | 以CD(Hitachi CG5000)、Overlay(ASML YieldStar)、Film Thickness(Ellipsometer KLA Aleris)、Defect(KLA Brightfield/AMAT UVision)、高深宽比量测(HAR SEM/OCD)结果作为Gate判定。DRAM Cell Capacitor CD和NAND Channel Hole CD超Spec时连接FDC原因分析→自动Hold→MRB流程。 |
| 7 | Redundancy / Repair Data Generation | 分析不良Cell/Block(Fuse Repair Circuit，Laser Repair设备，KLA/Hitachi)，生成Redundancy Map和Repair Code。DRAM使用Row/Column Redundancy，NAND使用Block Replacement方式。Repair Code与Wafer Sort结果联动生成，通过Laser Fuse Blowing(DSM/Electro Scientific Industries)执行物理Repair。 |
| 8 | Wafer Sort / Electrical Test | 执行Wafer Sort(Teradyne J750/Advantest T5503，温度-40~125℃)、Probe Card Contact、Speed/Retention/Leakage Test(Screen Bin、Speed Bin、Retention时间)、Bin Map。DRAM测试Refresh Time、Row Hammer、Retention特性，NAND测试Program/Erase Cycle、Read Disturb、Retention特性。Bin结果实时采集至YMS。 |
| 9 | Package / HBM Handoff | 形成Known Good Die(KGD，Wafer Sort按Grade A/B/C分类)、Stack/Package投入条件和HBM(HBM4标准16~24Hi Stack)/MCP(Multi-Chip Package)等后工序交接数据。Die Grade Map、Wafer Map、Laser Mark Code传送至Package Assembly(MCP/HBM产线)，交接数据完整性通过ECC/Checksum验证。 |
| 10 | Yield Analysis / Product Grade | 按Layer、Cell、Block、Die分析良率损失(Memory Cell Failure Bit Count、Row/Column Fail、Block Fail)并确定产品等级(Speed Grade：DDR5-4800/5600/6400、NAND Grade：pSLC/MLC/TLC/QLC、HBM Bandwidth Grade)。YMS(Synopsys/PDF)按Layer/Die分析良率和Spatial Signature，定位Yield Loss Root Cause。 |

## 2.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Cell/Array 구조 관리 | Memory Cell 구조는 Density·Layer·Mask 기준으로 공정 조건과 계측 기준이 달라진다. 측정 장비/방법: DRAM Cell Capacitor CD는 OCD Optical Critical Dimension(KLA / Nanometrics), NAND Channel Hole CD는 CD-SEM(Hitachi CG) / HAR SEM. 관리 주기: Layer별 샘플링(Every Layer). 이상 시 조치: CD Spec 이탈 → APC Feed-back으로 Etch/CMP 조건 자동 보정 → 보정 후 재계측. | 3,4 | process_step | Cell / Array Control |
| 2 | 3D Stack 반복 관리 | Layer 적층, Channel Hole, Staircase 공정은 반복 Loop와 고종횡비 계측을 추적해야 한다. 측정 장비/방법: HAR Profile(TEM Cross-section, OCD), Film Stack Thickness(Ellipsometer, KLA). 관리 주기: NAND 4~8 Layer마다 샘플링(Periodic Sampling). 이상 시 조치: Void / Taper Angle 이상 → Stack Deposition 조건 조정(Nitride/Oxide 비율, 온도, Pressure) + Etch Recipe 조정. | 4 | process_step | 3D Stack Control |
| 3 | Inline Gate 판정 | Stack·Array 계측결과가 Spec을 벗어나면 Hold와 원인 분석으로 연결해야 한다. 측정 장비: KLA 39xx Brightfield, AMAT UVision, CD-SEM, Ellipsometer. 관리 주기: Module 완료 시 Lot당(Every Module). 이상 시 조치: Auto Hold → FDC 이상 패턴 분석 → 장비·Recipe 원인 식별 → Scrap/Rework/Release 결정. | 6 | process_step | Inline Gate |
| 4 | Redundancy Repair 관리 | 불량 Cell/Block, Repair Code, Redundancy Map은 Wafer Sort 결과와 연결해야 한다. 측정 장비/방법: Laser Fuse Repair System(DSM / ESI), Repair Code 자동 생성 SW. 관리 주기: Wafer Sort 후 Every Lot. 이상 시 조치: Repair Coverage 부족 Lot → Repair Algorithm 검증 → 추가 Redundancy 할당 → 재Sort. | 7,8 | process_step | Redundancy |
| 5 | Die Grade 판정 | Wafer Sort Bin과 전기특성 결과로 Package 투입 가능 Die를 분류해야 한다. 측정 방법: Teradyne/Advantest Tester Bin 결과 + YMS Bin Table 매핑. 관리 주기: Sort 종료 시 Every Lot. 이상 시 조치: Bin Error / Mis-grade → Bin Limit 재검증 → 재Sort 또는 Manual Grade 조정. | 8,9,10 | process_step | Product Grading |
| 6 | Layer별 결함 패턴 | 3D NAND는 Layer 위치별 결함·Void·Profile 편차를 분리 분석해야 한다. 측정 방법: KLA Defect Inspection + SEM Review + TEM Cross-section, OCD Profile 분석. 관리 주기: 샘플링 주기(주 1회 또는 Layer 32~64층 단위). 이상 시 조치: 특정 Layer 결함 집중 → 해당 Layer 공정 조건(Deposition/Etch) 재설정 → Full Stack 재검증. | 4,6,10 | process_step | Layer Defect Analysis |
| 7 | HBM/Package 인계 | HBM 또는 고급 Package 투입 시 KGD, Die Grade, Wafer Map을 후공정에 정확히 인계해야 한다. 측정 방법: MES-Package Interface 자동 데이터 전송, ECC/Checksum 검증. 관리 주기: 인계 시점마다(Every Handoff). 이상 시 조치: 데이터 불일치 → 인계 중단 → Data Reconciliation → 재전송. | 9 | process_step | Package Handoff |
| 8 | Memory Genealogy | Lot-Wafer-Layer-Equipment-Recipe-Test 결과를 제품 Grade까지 연결해야 한다. 측정 방법: MES + EAP + YMS 통합 데이터 조회. 관리 주기: Real-time. 이상 시 조치: 추적 불가 → Genealogy 보강 → Full Hold. | 1,2,3,4,5,6,8,10 | process_step | Genealogy |

## 2.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Cell/Array结构管理 | Memory Cell结构会随Density、Layer和Mask改变工艺条件和量测标准。测量设备/方法：DRAM Cell Capacitor CD=OCD Optical Critical Dimension(KLA/Nanometrics)、NAND Channel Hole CD=CD-SEM(Hitachi CG)/HAR SEM。管理周期：每层抽样(Every Layer)。异常处理：CD超Spec→APC Feed-back自动修正Etch/CMP条件→修正后重新量测。 | 3,4 | process_step | Cell / Array Control |
| 2 | 3D Stack循环管理 | Layer堆叠、Channel Hole、Staircase工序必须追踪循环Loop和高深宽比量测。测量设备/方法：HAR Profile(TEM截面、OCD)、Film Stack厚度(Ellipsometer，KLA)。管理周期：NAND每4~8层抽样(Periodic Sampling)。异常处理：Void/Taper Angle异常→调整Stack Deposition条件(Nitride/Oxide比、温度、Pressure)+Etch Recipe调整。 | 4 | process_step | 3D Stack Control |
| 3 | Inline Gate判定 | Stack/Array量测超Spec时，应连接Hold和原因分析。测量设备：KLA 39xx Brightfield、AMAT UVision、CD-SEM、Ellipsometer。管理周期：Module完成时每Lot(Every Module)。异常处理：Auto Hold→FDC异常图形分析→设备/Recipe原因识别→Scrap/Rework/Release判定。 | 6 | process_step | Inline Gate |
| 4 | Redundancy Repair管理 | 不良Cell/Block、Repair Code、Redundancy Map需与Wafer Sort结果连接。测量设备/方法：Laser Fuse Repair System(DSM/ESI)、Repair Code自动生成SW。管理周期：Wafer Sort后Every Lot。异常处理：Repair Coverage不足Lot→Repair Algorithm验证→追加Redundancy分配→重Sort。 | 7,8 | process_step | Redundancy |
| 5 | Die Grade判定 | 通过Wafer Sort Bin和电性结果分类可投入Package的Die。测量方法：Teradyne/Advantest Tester Bin结果+YMS Bin Table映射。管理周期：Sort结束时Every Lot。异常处理：Bin Error/Mis-grade→Bin Limit重新验证→重Sort或Manual Grade调整。 | 8,9,10 | process_step | Product Grading |
| 6 | 按Layer缺陷图形分析 | 3D NAND必须按Layer位置区分缺陷、Void和Profile偏差。测量方法：KLA Defect Inspection+SEM Review+TEM截面、OCD Profile分析。管理周期：抽样周期(每周1次或每Layer 32~64层)。异常处理：特定Layer缺陷集中→调整该Layer Deposition/Etch条件→Full Stack重新验证。 | 4,6,10 | process_step | Layer Defect Analysis |
| 7 | HBM/Package交接 | 投入HBM或高级Package时，必须向后工序准确交接KGD、Die Grade和Wafer Map。测量方法：MES-Package Interface自动数据传输、ECC/Checksum验证。管理周期：每次交接(Every Handoff)。异常处理：数据不一致→中断交接→Data Reconciliation→重发。 | 9 | process_step | Package Handoff |
| 8 | Memory Genealogy | 需把Lot-Wafer-Layer-Equipment-Recipe-Test结果连接到产品等级。测量方法：MES+EAP+YMS集成数据查询。管理周期：Real-time。异常处理：不可追溯→Genealogy补充→Full Hold。 | 1,2,3,4,5,6,8,10 | process_step | Genealogy |

## 2.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, product_family, density_code, layer_count |
| 2 | Periphery | process |  |  | recipe_id, equipment_id, chamber_id, cd_result |
| 3 | Cell Array | process |  |  | recipe_id, equipment_id, film_thickness, defect_map |
| 4 | 3D Stack | process | Layer / Stack Loop |  | layer_count, recipe_id, equipment_id, har_profile, film_thickness |
| 5 | Interconnect | process |  |  | recipe_id, equipment_id, cd_result, overlay_result |
| 6 | Gate | gate |  | 2,3,4,5 | defect_map, cd_result, overlay_result, film_thickness, har_profile, bond_void_map |
| 7 | Repair | process |  |  | repair_code, redundancy_map, defect_map |
| 8 | Sort | process |  |  | wafer_sort_bin, die_grade, defect_map |
| 9 | Handoff | process |  |  | wafer_sort_bin, die_grade, product_family |
| 10 | Yield | process |  |  | die_grade, wafer_sort_bin, repair_code, redundancy_map |

## 2.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, product_family, density_code, layer_count |
| 2 | Periphery | process |  |  | recipe_id, equipment_id, chamber_id, cd_result |
| 3 | Cell Array | process |  |  | recipe_id, equipment_id, film_thickness, defect_map |
| 4 | 3D Stack | process | Layer / Stack Loop |  | layer_count, recipe_id, equipment_id, har_profile, film_thickness |
| 5 | Interconnect | process |  |  | recipe_id, equipment_id, cd_result, overlay_result |
| 6 | Gate | gate |  | 2,3,4,5 | defect_map, cd_result, overlay_result, film_thickness, har_profile, bond_void_map |
| 7 | Repair | process |  |  | repair_code, redundancy_map, defect_map |
| 8 | Sort | process |  |  | wafer_sort_bin, die_grade, defect_map |
| 9 | Handoff | process |  |  | wafer_sort_bin, die_grade, product_family |
| 10 | Yield | process |  |  | die_grade, wafer_sort_bin, repair_code, redundancy_map |

## 2.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | ONON Stack Deposition |
| 4 | 2 | Channel Hole Etch |
| 4 | 3 | Channel Fill |
| 4 | 4 | Staircase Formation |

## 2.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
| 4 | 1 | ONON Stack沉积 |
| 4 | 2 | Channel Hole刻蚀 |
| 4 | 3 | Channel填充 |
| 4 | 4 | Staircase形成 |

## 2.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - product_family
  - density_code
  - layer_count
  - route_rev
  - mask_set_id
  - recipe_id
  - equipment_id
  - chamber_id
  - cd_result
  - overlay_result
  - film_thickness
  - defect_map
  - har_profile
  - bond_void_map
  - repair_code
  - redundancy_map
  - wafer_sort_bin
  - die_grade
```

---

# 3. B03 — 아날로그·혼합신호 IC

```yaml
subindustry_code: B03
legacy_slug: analog_mixed
label_ko: 아날로그·혼합신호 IC
label_zh: 模拟·混合信号IC
label_en: ""
label_ja: ""
routing: RT_REENTRANT
preset_id: reentrant_module_v1
expression_tier: P3_PFLOW_REENTRANT
routing_description_ko: >
  아날로그·혼합신호 IC는 고전압/저잡음/정밀 소자, Passive, Trim, Characterization이 중요하다. 디지털 로직보다 Parametric 분포와 제품별 Option 관리가 더 크게 작용한다. 2026년 기준 Laser Trim 자동화와 AI 기반 Parametric 분포 분석이 확대 도입되고 있으며, 고객별 Trim Code·Characterization 데이터 보안이 강화되고 있다.
routing_description_zh: >
  模拟/混合信号IC强调高压、低噪声、精密器件、Passive、Trim和Characterization。相比数字逻辑，更重视Parametric分布和产品选项管理。2026年Laser Trim自动化和AI Parametric分布分析正在扩大应用，客户Trim Code/Characterization数据安全持续加强。
```

## 3.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Option Baseline | 제품 Option(Op-Amp/ADC/DAC/Power Mgmt 등), Voltage Rating(5V/12V/30V/100V+), Mask, Trim 방식(Laser Trim / eFuse), Test 조건을 기준선으로 확정한다. MES에서 제품 Option별 Route, Test Program, Trim Recipe를 매핑하며, Voltage Rating에 따라 Process Flow(고전압/저전압 구간 분리)가 달라진다. Lot ID 기준으로 제품 Family·Option·Voltage Class를 Serial Tracking Key로 설정한다. |
| 2 | Device Isolation / Well Formation | Isolation(LOCOS / STI, Trench Depth 0.3~2μm), Well(고전압 N/P-Well, Drive-in 1100~1200℃), High Voltage Device 영역(DMOS 구조, Extended Drain, RESURF)을 형성한다. 고전압 영역은 별도의 Well Drive-in 조건과 Mask Layer(고전약 Isolation)가 필요하다. Trench CD는 CD-SEM(Hitachi)으로, Junction Depth는 SIMS(Secondary Ion Mass Spectrometry)로 Lot당 샘플링 검증한다. |
| 3 | Precision Device Formation | BJT(NPN/PNP, 베타 이득 50~500, 온도 계수 <0.3%/℃), LDMOS(Rds(on) <1mΩ·mm², BVdss 10~100V), CMOS(저잡음, 1/f Noise <1μV²/Hz), Diode(Zener / Schottky, Breakdown 정밀도 ±2%) 등 아날로그 핵심 소자를 형성한다. 각 소자별 Layout Matching 구조(Common Centroid, Interdigitation)를 적용하며, Parametric 특성은 WAT에서 검증한다. |
| 4 | Passive Component Formation | Resistor(Poly / Diffusion / Thin Film, Sheet Resistance 100~2kΩ/sq, TCR <50ppm/℃), Capacitor(MIM / PIP, Capacitance Density 1~5fF/μm²), Inductor(Spiral Cu, L 1~100nH, Q-factor >10), Matching 구조를 형성하고 공정 편차를 관리한다. 정밀 Passive의 Matching 비율(Ratio 정밀도 <0.1%)은 Area Scaling과 Dummy Pattern으로 확보하며, Sheet Resistance는 4-Point Probe로 필드별 계측한다. |
| 5 | Interconnect / Thick Metal | Low Resistance Metal(Ti/Al-Cu/TiN, PVD, 두께 0.5~4μm), Thick Metal(Top Cu 2~6μm, 전류 밀도 >1MA/cm²), Pad(Bond Pad Al, 50~100μm), Shield 구조(Copper Shield Layer, Noise 차폐)를 형성한다. Thick Metal의 전류 밀도와 Sheet Resistance는 Inline 4-Point Probe로 계측하며, Stress Voiding 방지를 위한 Anneal 조건(400℃, 30min)을 관리한다. |
| 6 | Inline Parametric Metrology | Vt(Threshold Voltage), Sheet Resistance(Rs, 각 Passive Layer), Capacitance(Capacitance Matching, C-V Curve), Leakage(Junction Leakage, Gate Leakage <1pA/μm²), Matching(Vt Matching σ<3mV for Pair) 결과를 계측한다. Keysight B1500A / Keithley 4200A Semiconductor Parameter Analyzer로 Lot당 정밀 계측하며, MSA(Measurement System Analysis)를 주기적으로 수행한다. |
| 7 | Fuse / Trim / Calibration Prep | Fuse(Poly / Metal Fuse, Cut 조건 1~5A), eFuse(전기적 Programming, I=10~50mA, V=3~6V), Laser Trim(IR Laser, Spot Size 2~5μm, Trim 정밀도 <0.1%), Calibration Code 생성 조건을 준비한다. Trim Code는 Wafer 측정 결과(Multibit Trim DAC / Resistor Ladder)를 기반으로 자동 생성되며, EEPROM/OTP Memory에 저장된다. |
| 8 | Wafer Probe / Trim Execution | Wafer Probe에서 Trim을 실행하고 전기적 Spec 충족 여부를 확인한다. Teradyne J750 / Advantest T2000 Tester에서 Probe Card Contact 후, Parametric 측정 → Trim Code 산출 → Laser Trim(ESO / Trumpf) 또는 eFuse Programming 실행 → Post-Trim 검증 순서로 진행된다. Trim 결과의 Die 단위 저장(Bin Code + Trim Code + Post-Trim 값)은 MES DB에 기록된다. |
| 9 | Characterization / Reliability Sample | 온도(-40~150℃)·전압·Noise(Power Spectrum Density 1/f Noise)·Drift(Temperature Drift, Aging Drift)·ESD(HBM 2~8kV, CDM 500~2000V)·Latch-up 샘플 특성을 검증한다. Characterization은 ATE(Advantest / Teradyne) + Temperature Chamber 조합으로 3개 온도 포인트에서 진행하며, ESD/Latch-up은 Thermo / KeyTek 장비로 Lot당 샘플링(5~15 DIE / Lot) 수행한다. 결과는 Characterization Report로 발행된다. |
| 10 | Yield Review / Product Bin | Parametric 분포(SPC Chart, CpK >1.33), Trim 결과(Trim Success Rate, Post-Trim Accuracy), Bin(Bin1/2/3, Yield %), 고객 Grade(Industrial/Automotive/Consumer)를 확정한다. YMS Dashboard에서 Lot·Wafer·Die 단위 Parametric 분포와 Trim 결과를 통합 분석하고, 최종 Bin Table에 따라 출하·재검사·Scrap을 결정한다. |

## 3.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Option Baseline | 确认产品Option(Op-Amp/ADC/DAC/Power Mgmt等)、Voltage Rating(5V/12V/30V/100V+)、Mask、Trim方式(Laser Trim/eFuse)、Test条件基线。MES按产品Option映射Route、Test Program和Trim Recipe，Voltage Rating决定Process Flow(高/低压区段分离)。以Lot ID设置产品Family/Option/Voltage Class为Serial Tracking Key。 |
| 2 | Device Isolation / Well Formation | 形成Isolation(LOCOS/STI，Trench Depth 0.3~2μm)、Well(高压N/P-Well，Drive-in 1100~1200℃)、高压器件区域(DMOS结构、Extended Drain、RESURF)。高压区域需要独立的Well Drive-in条件和Mask Layer(高压Isolation)。Trench CD用CD-SEM(Hitachi)量测，Junction Depth用SIMS(Secondary Ion Mass Spectrometry)按Lot抽样验证。 |
| 3 | Precision Device Formation | 形成BJT(NPN/PNP，Beta增益50~500，温度系数<0.3%/℃)、LDMOS(Rds(on)<1mΩ·mm²，BVdss 10~100V)、CMOS(低噪声，1/f Noise<1μV²/Hz)、Diode(Zener/Schottky，Breakdown精度±2%)等模拟核心器件。各器件应用Layout Matching结构(Common Centroid、Interdigitation)，Parametric特性在WAT验证。 |
| 4 | Passive Component Formation | 形成Resistor(Poly/Diffusion/Thin Film，Sheet Resistance 100~2kΩ/sq，TCR<50ppm/℃)、Capacitor(MIM/PIP，Capacitance Density 1~5fF/μm²)、Inductor(Spiral Cu，L 1~100nH，Q-factor>10)、Matching结构并管理工艺偏差。精密Passive的Matching比(Ratio精度<0.1%)通过Area Scaling和Dummy Pattern实现，Sheet Resistance用4-Point Probe按Field量测。 |
| 5 | Interconnect / Thick Metal | 形成Low Resistance Metal(Ti/Al-Cu/TiN，PVD，厚度0.5~4μm)、Thick Metal(Top Cu 2~6μm，电流密度>1MA/cm²)、Pad(Bond Pad Al，50~100μm)、Shield结构(Copper Shield Layer，噪声屏蔽)。Thick Metal的电流密度和Sheet Resistance用Inline 4-Point Probe量测，管理Stress Voiding防止用Anneal条件(400℃、30min)。 |
| 6 | Inline Parametric Metrology | 量测Vt(Threshold Voltage)、Sheet Resistance(Rs，各Passive Layer)、Capacitance(Capacitance Matching，C-V Curve)、Leakage(Junction Leakage，Gate Leakage<1pA/μm²)、Matching(Vt Matching σ<3mV for Pair)。用Keysight B1500A/Keithley 4200A Semiconductor Parameter Analyzer按Lot精密量测，定期执行MSA(Measurement System Analysis)。 |
| 7 | Fuse / Trim / Calibration Prep | 准备Fuse(Poly/Metal Fuse，Cut条件1~5A)、eFuse(电性Programming，I=10~50mA，V=3~6V)、Laser Trim(IR Laser，Spot Size 2~5μm，Trim精度<0.1%)、Calibration Code生成条件。Trim Code基于Wafer测量结果(Multibit Trim DAC/Resistor Ladder)自动生成，存储于EEPROM/OTP Memory。 |
| 8 | Wafer Probe / Trim Execution | 在Wafer Probe执行Trim并确认电性Spec达成。Teradyne J750/Advantest T2000 Tester上Probe Card Contact后，按Parametric测量→Trim Code计算→Laser Trim(ESO/Trumpf)或eFuse Programming→Post-Trim验证顺序执行。Die级Trim结果(Bin Code+Trim Code+Post-Trim值)记录在MES DB。 |
| 9 | Characterization / Reliability Sample | 验证温度(-40~150℃)、电压、Noise(Power Spectrum Density 1/f Noise)、Drift(Temperature Drift、Aging Drift)、ESD(HBM 2~8kV、CDM 500~2000V)、Latch-up样本特性。Characterization在ATE(Advantest/Teradyne)+Temperature Chamber组合下在3个温度点进行，ESD/Latch-up用Thermo/KeyTek设备按Lot抽样(5~15 DIE/Lot)。结果发布为Characterization Report。 |
| 10 | Yield Review / Product Bin | 确定Parametric分布(SPC Chart，CpK>1.33)、Trim结果(Trim Success Rate、Post-Trim Accuracy)、Bin(Bin1/2/3、Yield%)、客户Grade(Industrial/Automotive/Consumer)。YMS Dashboard综合Lot/Wafer/Die级Parametric分布和Trim结果，按最终Bin Table决定出货、重测或Scrap。 |

## 3.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Option 기준 관리 | Analog/Mixed 제품은 동일 Family라도 전압·Option·Trim 방식에 따라 Route와 Test 조건이 달라진다. 측정 방법: MES Opcenter에서 Product Option Code → Route 매핑 자동 검증. 관리 주기: Lot Release 시(Every Lot). 이상 시 조치: Option-Route 불일치 → Lot Hold → Product Engineer 검토 → Route 수정. | 1 | process_step | Product Option |
| 2 | 정밀 Passive 편차 | Resistor/Capacitor Matching과 Sheet Resistance 분포를 제품별 Spec으로 관리해야 한다. 측정 장비/방법: 4-Point Probe(CDE / Napson) Rs 계측, C-V Meter(Keysight B1500A) Capacitance Matching 계측. 관리 주기: Lot당(Every Lot). 이상 시 조치: Matching Ratio >Spec → 공정 조건(Deposition Uniformity / Etch Bias) 조정 → Test Vehicle로 재검증. | 4,6 | process_step | Passive Matching |
| 3 | Parametric Gate | Vt, Leakage, Capacitance, Matching 결과가 Spec을 벗어나면 Lot Hold와 분석을 수행해야 한다. 측정 장비: Keysight B1500A / Keithley 4200A Parameter Analyzer. 관리 주기: Module 완료 시 Lot당(Every Lot). 이상 시 조치: Parametric Fail → Auto Hold → FDC 분석 → 공정 조정(Implant Dose / Anneal 조건 변경) → 재계측. | 6 | process_step | Parametric Gate |
| 4 | Trim Code 추적 | Trim 실행 전후 값과 Fuse 결과를 Die 단위로 저장해야 한다. 측정 방법: Tester Bin Log + MES DB 연동. 관리 주기: Die 단위(Every Die). 이상 시 조치: Trim Code 누락 / 오류 → 해당 Die Scrap 또는 Manual Retrim. | 7,8 | process_step | Trim / Fuse |
| 5 | Characterization 샘플링 | 온도·전압·Noise·Drift 특성 검증 샘플을 Lot 이력과 연결해야 한다. 측정 장비: ATE(Advantest T2000) + Temperature Chamber, ESD Simulator(Thermo). 관리 주기: Lot별 샘플링(5~15 Die / Lot). 이상 시 조치: Characterization Fail → Lot 전체 Hold → 원인 분석(Process Variation / Wafer Position) → Scrap or Rework. | 9 | process_step | Characterization |
| 6 | 고객 Grade 분리 | 동일 Wafer에서도 고객별 Grade와 Bin 조건이 달라질 수 있다. 측정 방법: YMS Bin Table별 Grade 매핑, 고객별 출하 Spec 분리. 관리 주기: Lot 종료 시(Every Lot). 이상 시 조치: Grade Mis-match → Bin Limit 재검증 → 고객별 Release 조건 재확인. | 10 | process_step | Customer Grade |
| 7 | Reliability 연계 | ESD, Latch-up, HTOL 등 신뢰성 샘플 결과를 Wafer·Lot 이력과 연결해야 한다. 측정 장비: HTOL Chamber(THERMO), ESD Simulator(KeyTek), Latch-up Tester. 관리 주기: Lot별 샘플링(Every Lot). 이상 시 조치: Reliability Fail → Lot 전체 Hold → Design/Layout/Process Review → 제품 Qualification 재검토. | 9,10 | process_step | Reliability |
| 8 | Analog Genealogy | Device, Passive, Trim, Test 데이터를 Die 등급까지 연결해야 한다. 측정 방법: MES + YMS 통합 데이터 조회. 관리 주기: Real-time. 이상 시 조치: 추적 불가 → Data Reconciliation → Genealogy 보강. | 1,3,4,6,8,10 | process_step | Genealogy |

## 3.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Option基准管理 | Analog/Mixed产品即使同Family，也会因电压、Option、Trim方式改变Route和Test条件。测量方法：MES Opcenter中Product Option Code→Route映射自动验证。管理周期：Lot Release时(Every Lot)。异常处理：Option-Route不一致→Lot Hold→Product Engineer审核→Route修正。 | 1 | process_step | Product Option |
| 2 | 精密Passive偏差 | 必须按产品Spec管理Resistor/Capacitor Matching和Sheet Resistance分布。测量设备/方法：4-Point Probe(CDE/Napson)Rs量测、C-V Meter(Keysight B1500A)Capacitance Matching量测。管理周期：每Lot(Every Lot)。异常处理：Matching Ratio>Spec→调整工艺条件(Deposition Uniformity/Etch Bias)→用Test Vehicle重新验证。 | 4,6 | process_step | Passive Matching |
| 3 | Parametric Gate | Vt、Leakage、Capacitance、Matching结果超Spec时，应执行Lot Hold和分析。测量设备：Keysight B1500A/Keithley 4200A Parameter Analyzer。管理周期：Module完成时每Lot(Every Lot)。异常处理：Parametric Fail→Auto Hold→FDC分析→工艺调整(Implant Dose/Anneal条件变更)→重新量测。 | 6 | process_step | Parametric Gate |
| 4 | Trim Code追踪 | 必须按Die保存Trim执行前后值和Fuse结果。测量方法：Tester Bin Log+MES DB联动。管理周期：每Die(Every Die)。异常处理：Trim Code缺失/错误→该Die Scrap或Manual Retrim。 | 7,8 | process_step | Trim / Fuse |
| 5 | Characterization抽样 | 需把温度、电压、Noise、Drift特性验证样本与Lot履历连接。测量设备：ATE(Advantest T2000)+Temperature Chamber、ESD Simulator(Thermo)。管理周期：每Lot抽样(5~15 Die/Lot)。异常处理：Characterization Fail→Lot全Hold→原因分析(Process Variation/Wafer Position)→Scrap or Rework。 | 9 | process_step | Characterization |
| 6 | 客户Grade区分 | 同一Wafer也可能因客户不同而适用不同Grade和Bin条件。测量方法：YMS Bin Table Grade映射、客户出货Spec分离。管理周期：Lot结束时(Every Lot)。异常处理：Grade不匹配→Bin Limit重新验证→客户Release条件再确认。 | 10 | process_step | Customer Grade |
| 7 | Reliability联动 | ESD、Latch-up、HTOL等可靠性样本结果需与Wafer/Lot履历连接。测量设备：HTOL Chamber(THERMO)、ESD Simulator(KeyTek)、Latch-up Tester。管理周期：每Lot抽样(Every Lot)。异常处理：Reliability Fail→Lot全Hold→Design/Layout/Process Review→产品Qualification重新评估。 | 9,10 | process_step | Reliability |
| 8 | Analog Genealogy | 需把Device、Passive、Trim、Test数据连接到Die等级。测量方法：MES+YMS集成数据查询。管理周期：Real-time。异常处理：不可追溯→Data Reconciliation→Genealogy补充。 | 1,3,4,6,8,10 | process_step | Genealogy |

## 3.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, product_option, voltage_rating, route_rev |
| 2 | Device | process |  |  | recipe_id, equipment_id, chamber_id, mask_set_id |
| 3 | Device | process |  |  | recipe_id, equipment_id, voltage_rating, leakage_result |
| 4 | Passive | process |  |  | sheet_resistance, capacitance_result, matching_index |
| 5 | Interconnect | process |  |  | recipe_id, equipment_id, chamber_id |
| 6 | Parametric Gate | gate |  | 2,3,4,5 | parametric_result, sheet_resistance, capacitance_result, leakage_result, matching_index |
| 7 | Trim Prep | process |  |  | trim_code, fuse_result, product_option |
| 8 | Probe / Trim | process |  |  | wafer_probe_bin, trim_code, fuse_result, parametric_result |
| 9 | Characterization | process |  |  | char_result, reliability_sample_id, customer_grade |
| 10 | Yield | process |  |  | wafer_probe_bin, customer_grade, char_result |

## 3.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, product_option, voltage_rating, route_rev |
| 2 | Device | process |  |  | recipe_id, equipment_id, chamber_id, mask_set_id |
| 3 | Device | process |  |  | recipe_id, equipment_id, voltage_rating, leakage_result |
| 4 | Passive | process |  |  | sheet_resistance, capacitance_result, matching_index |
| 5 | Interconnect | process |  |  | recipe_id, equipment_id, chamber_id |
| 6 | Parametric Gate | gate |  | 2,3,4,5 | parametric_result, sheet_resistance, capacitance_result, leakage_result, matching_index |
| 7 | Trim Prep | process |  |  | trim_code, fuse_result, product_option |
| 8 | Probe / Trim | process |  |  | wafer_probe_bin, trim_code, fuse_result, parametric_result |
| 9 | Characterization | process |  |  | char_result, reliability_sample_id, customer_grade |
| 10 | Yield | process |  |  | wafer_probe_bin, customer_grade, char_result |

## 3.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 3.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 3.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - product_option
  - voltage_rating
  - route_rev
  - mask_set_id
  - recipe_id
  - equipment_id
  - chamber_id
  - parametric_result
  - sheet_resistance
  - capacitance_result
  - leakage_result
  - matching_index
  - trim_code
  - fuse_result
  - wafer_probe_bin
  - char_result
  - reliability_sample_id
  - customer_grade
```

---

# 4. B04 — 전력반도체·디스크리트

```yaml
subindustry_code: B04
legacy_slug: power_discrete
label_ko: 전력반도체·디스크리트
label_zh: 功率半导体·分立器件
label_en: ""
label_ja: ""
routing: RT_BATCH
preset_id: batch_process_v1
expression_tier: P3_PFLOW_BATCH
routing_description_ko: >
  전력반도체는 Frontside Device, Backside Grinding/Metallization, Wafer Probe, Thermal/Reliability 특성이 중요하다. Batch 공정·로트 조건·Backside 이력을 분리 추적해야 한다. 2026년 기준 SiC/GaN 전력반도체 공정 자동화가 가속화되고 있으며, Batch Recipe 중앙 관리와 실시간 장비 상태 모니터링이 확대되고 있다.
routing_description_zh: >
  功率半导体强调Frontside器件、Backside减薄/金属化、Wafer Probe、热与可靠性特性。必须区分追踪Batch工艺、Lot条件和Backside履历。2026年SiC/GaN功率半导体工艺自动化加速推进，Batch Recipe中央管理和实时设备状态监控持续扩大。
```

## 4.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Device Type Baseline | MOSFET, IGBT, Diode, SiC/GaN 여부와 전압·전류 등급(600V/1200V/1700V, 10~200A), Wafer 사양(6"/8"/SiC 150mm), Wafer Thickness(표준 500~675μm → Backgrind 후 100~200μm)를 확정한다. MES에서 Device Type별 Route·Test Spec·Reliability Plan을 매핑하고, Lot Number 기준 Batch ID를 생성한다. SiC 제품은 Substrate Type(Conductive/Semi-insulating)과 Crystal Quality를 Baseline으로 관리한다. |
| 2 | Frontside Oxide / Implant | Gate Oxide(Thermal Oxidation, Furnace 1000~1100℃, 두께 50~200nm), Body/Source Implant(Boron/Phosphorus, High Energy 100~500keV + High Current), JTE/Guard Ring(Junction Termination Extension, Edge Termination) 등 Frontside 구조를 형성한다. Ion Implanter(Axcelis / AMAT VIISta)로 Dose 관리(1e12~1e15/cm²)하며, Oxide Quality는 C-V 및 Qbd(Charge-to-Breakdown)로 Batch당 평가한다. |
| 3 | Trench / Gate / Poly Module | Trench Etch(Lam Kiyo / TEL, Trench Depth 2~10μm, Width 0.5~3μm), Gate Oxide(Thick Oxide/Thin Gate Oxide 선택, 500~1000Å for Trench Gate), Poly-Si Fill(LPCVD 620℃), Etchback(Dry Etch or CMP) 조건을 관리한다. Trench CD 및 Profile은 Cross-section SEM(CD-SEM Hitachi)으로 Lot당 샘플링 계측하며, Trench Bottom Oxide Thickness는 Ellipsometer로 Batch당 검증한다. |
| 4 | Source / Contact / Front Metal | Source Contact(Ti/Al, Silicide Formation RTP 400~600℃), Barrier(TiN/TiW, PVD), Front Metal(Al-Cu / Cu, PVD 두께 2~5μm), Passivation(SiN PECVD + Pi-SOG, 500nm~2μm)과 접촉저항(Contact Resistance <1e-5 Ω·cm²)을 관리한다. Contact Resistance는 TLM(Transmission Line Model) PCM 구조로 WAT에서 검증한다. |
| 5 | Wafer Thinning / Backgrind | Wafer Backgrind(Mechanical Grinder, DISCO DFG8541 / TOKYO SEIMITSU, Target Thickness 100~200μm, Thickness Uniformity ±3μm), Stress Relief(Release 연삭 + Dry Polish), Wafer Thickness 측정(Contact / Non-contact Probe, Keyence / Micro-Epsilon), Bow/Warp 측정(Flatness Tester, ADE / KLA)을 관리한다. SiC Wafer(경질, 6H/4H-SiC)는 Backgrind Feed Rate를 Si 대비 1/3 이하로 낮춰 균열을 방지한다. |
| 6 | Backside Implant / Metal | Backside Implant(Drain Contact용, P+ or N+, High Energy / Low Dose), Anneal(RTP 900~1000℃, Dopant Activation), Back Metal Stack(Ti/Ni/Ag, Sputter/Evaporation, 0.5~5μm, Solderable Contact)과 접합 특성(Specific Contact Resistance <1e-4 Ω·cm²)을 관리한다. Backside Adhesion은 Tape Test/Shear Test로 샘플링 검증한다. |
| 7 | Inline / Visual Gate | 전면·후면 결함(Optical Microscope, KLA Defect Inspection, Surface Particle Counter), 금속막(Visual Inspection, Metal Coverage SEM), Wafer Thickness(Contact Probe), Bow/Warp(Flatness Tester)를 Gate로 판정한다. 결함 Spec 이탈 시 Auto Hold → FDC 분석 → Scrap/Rework(Non-conforming Wafer는 Backgrind/Polish 재실시 가능) 결정. |
| 8 | Wafer Probe / Parametric Test | BV(Breakdown Voltage, 600~1700V 기준, Keysight B1506A / Keithley 2410, Leakage <1μA), Rds(on)(<10~100mΩ, on-resistance), Vf(Diode Forward Voltage), Leakage(Off-state Leakage <10μA at Rated Vds), Gate Charge(Qg, JEDEC Standard) 등 전기특성을 Wafer Probe로 판정한다. Probe Card(High Voltage Probe, Shielded Kelvin Contact)는 장비(TEL / Tokyo Electron Prober)에 장착되어 테스트된다. |
| 9 | Reliability / Burn-in Sample | HTRB(High Temperature Reverse Bias, 150℃, 80% Vbr, 1000h), HTGB(High Temperature Gate Bias, 150℃, Vgs max, 1000h), Power Cycle(ΔTj >100℃, 10000~100000 cycle), Surge(IEC 61000-4-5) 등 신뢰성 샘플을 선정(Device Type·Voltage Class별 5~25개/Lot)하고 결과를 연결한다. Reliability Chamber(ESPEC / Thermotron)에서 가속 수명 테스트가 진행된다. |
| 10 | Yield Review / Backend Handoff | Die Grade(Bin1~4, Voltage Class 별), Wafer Map(Bin Map + Electrical Result Map), Backside 이력(Backgrind 조건, Back Metal ID), Package 투입 기준(Die Thickness > Min, < Max, Bow Limit)을 확정한다. YMS Dashboard에서 Probe Bin 결과 + Reliability 결과를 통합 분석하고, 제품 출하 사양서(Product Spec Sheet)를 발행한다. |

## 4.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Device Type Baseline | 确认MOSFET、IGBT、Diode、SiC/GaN类型以及电压/电流等级(600V/1200V/1700V、10~200A)、Wafer规格(6"/8"/SiC 150mm)、Wafer Thickness(标准500~675μm→Backgrind后100~200μm)。MES按Device Type映射Route/Test Spec/Reliability Plan，以Lot Number生成Batch ID。SiC产品同时管理Substrate Type(Conductive/Semi-insulating)和Crystal Quality为Baseline。 |
| 2 | Frontside Oxide / Implant | 形成Gate Oxide(Thermal Oxidation，Furnace 1000~1100℃，厚度50~200nm)、Body/Source Implant(Boron/Phosphorus，High Energy 100~500keV+High Current)、JTE/Guard Ring(Junction Termination Extension，Edge Termination)等Frontside结构。Ion Implanter(Axcelis/AMAT VIISta)管理Dose(1e12~1e15/cm²)，Oxide Quality用C-V及Qbd(Charge-to-Breakdown)按Batch评估。 |
| 3 | Trench / Gate / Poly Module | 管理Trench Etch(Lam Kiyo/TEL，Trench Depth 2~10μm，Width 0.5~3μm)、Gate Oxide(Thick Oxide/Thin Gate Oxide选择，500~1000Å for Trench Gate)、Poly-Si Fill(LPCVD 620℃)、Etchback(Dry Etch or CMP)条件。Trench CD和Profile用Cross-section SEM(CD-SEM Hitachi)按Lot抽样量测，Trench Bottom Oxide Thickness用Ellipsometer按Batch验证。 |
| 4 | Source / Contact / Front Metal | 管理Source Contact(Ti/Al，Silicide Formation RTP 400~600℃)、Barrier(TiN/TiW，PVD)、Front Metal(Al-Cu/Cu，PVD厚度2~5μm)、Passivation(SiN PECVD+Pi-SOG，500nm~2μm)和接触电阻(Contact Resistance<1e-5 Ω·cm²)。Contact Resistance通过TLM(Transmission Line Model)PCM结构在WAT验证。 |
| 5 | Wafer Thinning / Backgrind | 管理Wafer Backgrind(Mechanical Grinder，DISCO DFG8541/TOKYO SEIMITSU，Target Thickness 100~200μm，Thickness Uniformity±3μm)、Stress Relief(Release研磨+Dry Polish)、Wafer厚度测量(Contact/Non-contact Probe，Keyence/Micro-Epsilon)、Bow/Warp测量(Flatness Tester，ADE/KLA)。SiC Wafer(硬质、6H/4H-SiC)的Backgrind Feed Rate需降至Si的1/3以下以防止裂纹。 |
| 6 | Backside Implant / Metal | 管理Backside Implant(Drain Contact用，P+ or N+，High Energy/Low Dose)、Anneal(RTP 900~1000℃，Dopant Activation)、Back Metal Stack(Ti/Ni/Ag，Sputter/Evaporation，0.5~5μm，Solderable Contact)及接合特性(Specific Contact Resistance<1e-4 Ω·cm²)。Backside Adhesion用Tape Test/Shear Test抽样验证。 |
| 7 | Inline / Visual Gate | 以正面/背面缺陷(Optical Microscope、KLA Defect Inspection、Surface Particle Counter)、金属膜(Visual Inspection、Metal Coverage SEM)、Wafer Thickness(Contact Probe)、Bow/Warp(Flatness Tester)作为Gate判定。缺陷超Spec时Auto Hold→FDC分析→Scrap/Rework决定(Non-conforming Wafer可重新Backgrind/Polish)。 |
| 8 | Wafer Probe / Parametric Test | 通过Wafer Probe判定BV(Breakdown Voltage，600~1700V标准，Keysight B1506A/Keithley 2410，Leakage<1μA)、Rds(on)(<10~100mΩ，on-resistance)、Vf(Diode Forward Voltage)、Leakage(Off-state Leakage<10μA at Rated Vds)、Gate Charge(Qg，JEDEC Standard)等电性。Probe Card(High Voltage Probe，Shielded Kelvin Contact)安装在设备(TEL/Tokyo Electron Prober)上执行测试。 |
| 9 | Reliability / Burn-in Sample | 选择HTRB(High Temperature Reverse Bias，150℃，80% Vbr，1000h)、HTGB(High Temperature Gate Bias，150℃，Vgs max，1000h)、Power Cycle(ΔTj>100℃，10000~100000 cycle)、Surge(IEC 61000-4-5)等可靠性样本(Device Type/Voltage Class 5~25个/Lot)并连接结果。Reliability Chamber(ESPEC/Thermotron)执行加速寿命测试。 |
| 10 | Yield Review / Backend Handoff | 确定Die Grade(Bin1~4、按Voltage Class)、Wafer Map(Bin Map+Electrical Result Map)、Backside履历(Backgrind条件、Back Metal ID)、Package投入标准(Die Thickness>Min、<Max、Bow Limit)。YMS Dashboard综合Probe Bin结果+Reliability结果分析，发布产品出货规格书(Product Spec Sheet)。 |

## 4.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | 전압·전류 등급 기준 | 전력반도체는 Device Type과 Voltage/Current Class별 공정조건·Test Spec이 다르다. 측정 방법: MES에서 Device Type 코드 → Route·Test Spec 매핑 자동 검증. 관리 주기: Lot Release 시(Every Lot). 이상 시 조치: Class 불일치 → Lot Hold → Design Engineer 검토 → Route·Spec 재매핑. | 1 | process_step | Device Class |
| 2 | Frontside Batch 조건 | Oxide, Implant, Trench 공정은 Batch·Chamber 조건을 Lot 단위로 Lock해야 한다. 측정 장비/방법: APC/R2R 시스템 + FDC(Applied Materials / Synopsys)의 Chamber Condition 모니터링. 관리 주기: Lot 투입 전(Every Batch). 이상 시 조치: Chamber PM Overdue 또는 Condition Violation → Equipment Hold → PM 완료 후 Release. | 2,3,4 | process_step | Frontside Batch |
| 3 | Backside 이력 관리 | Backgrind, Backside Metal, Wafer Thickness, Bow/Warp 이력은 Package·신뢰성과 연결해야 한다. 측정 장비: DISCO Backgrinder Inline Thickness Gauge, KLA Flatness Tester, Keyence Laser Profiler. 관리 주기: Wafer 단위(Every Wafer). 이상 시 조치: Bow/Warp >Spec → Backgrind 조건 조정(Feed Rate, Chuck Temp) → 재처리. | 5,6,10 | process_step | Backside Control |
| 4 | Inline/Visual Gate | 전면·후면 결함과 두께·Warp 결과는 후속 Probe 투입 전 Gate로 판정해야 한다. 측정 장비: KLA Brightfield Defect Inspection, Optical Microscope, SEM Review, Contact/Non-contact Thickness Probe. 관리 주기: Backside Module 완료 시(Every Lot). 이상 시 조치: Visual Defect High / Thickness Out-of-Spec → Auto Hold → Scrap 또는 Rework(Backgrind 재실시). | 7 | process_step | Visual / Inline Gate |
| 5 | 전기특성 판정 | BV, Rds(on), Leakage 등 핵심 Parametric 결과로 Die Grade를 결정해야 한다. 측정 장비: Keysight B1506A Power Device Analyzer / Keithley 2410 SourceMeter, TEL Prober. 관리 주기: Die 단위(Every Die). 이상 시 조치: Parametric Fail → Bin 분류(Scrap/Retest/Downgrade) → 저수율 Lot는 MRB. | 8,10 | process_step | Electrical Test |
| 6 | 신뢰성 샘플 연결 | HTRB/HTGB/Power Cycle 샘플을 Lot·Device Class·Probe 결과와 연결해야 한다. 측정 장비: ESPEC / Thermotron Reliability Chamber, Power Cycle Tester. 관리 주기: Lot별 샘플링(5~25 Die/Lot). 이상 시 조치: Reliability Fail(HTRB Leakage 증가, Power Cycle Crack) → Lot 전체 Hold → Root Cause 분석 후 Disposition. | 9 | process_step | Reliability |
| 7 | Batch Genealogy | Batch ID, Recipe, Equipment, Backside 조건을 Die Grade까지 연결해야 한다. 측정 방법: MES + EAP 데이터 통합 조회. 관리 주기: Real-time. 이상 시 조치: 추적 불가 → Data 보강 → Full Hold. | 2,3,5,6,8,10 | process_step | Batch Genealogy |

## 4.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | 电压/电流等级基准 | 功率半导体按Device Type和Voltage/Current Class使用不同工艺条件和Test Spec。测量方法：MES中Device Type代码→Route/Test Spec映射自动验证。管理周期：Lot Release时(Every Lot)。异常处理：Class不一致→Lot Hold→Design Engineer审核→Route/Spec重新映射。 | 1 | process_step | Device Class |
| 2 | Frontside Batch条件 | Oxide、Implant、Trench工序需按Lot锁定Batch/Chamber条件。测量设备/方法：APC/R2R系统+FDC(Applied Materials/Synopsys)的Chamber Condition监控。管理周期：Lot投入前(Every Batch)。异常处理：Chamber PM超期或Condition Violation→Equipment Hold→PM完成后Release。 | 2,3,4 | process_step | Frontside Batch |
| 3 | Backside履历管理 | Backgrind、Backside Metal、Wafer Thickness、Bow/Warp履历需连接Package和可靠性。测量设备：DISCO Backgrinder Inline Thickness Gauge、KLA Flatness Tester、Keyence Laser Profiler。管理周期：Wafer级(Every Wafer)。异常处理：Bow/Warp>Spec→调整Backgrind条件(Feed Rate、Chuck Temp)→重新处理。 | 5,6,10 | process_step | Backside Control |
| 4 | Inline/Visual Gate | 正面/背面缺陷和Thickness/Warp结果必须在Probe投入前作为Gate判定。测量设备：KLA Brightfield Defect Inspection、Optical Microscope、SEM Review、Contact/Non-contact Thickness Probe。管理周期：Backside Module完成时(Every Lot)。异常处理：Visual Defect高/Thickness Out-of-Spec→Auto Hold→Scrap或Rework(重新Backgrind)。 | 7 | process_step | Visual / Inline Gate |
| 5 | 电性判定 | 通过BV、Rds(on)、Leakage等核心Parametric结果决定Die Grade。测量设备：Keysight B1506A Power Device Analyzer/Keithley 2410 SourceMeter、TEL Prober。管理周期：每Die(Every Die)。异常处理：Parametric Fail→Bin分类(Scrap/Retest/Downgrade)→低良率Lot提交MRB。 | 8,10 | process_step | Electrical Test |
| 6 | 可靠性样本连接 | HTRB/HTGB/Power Cycle样本需与Lot、Device Class和Probe结果连接。测量设备：ESPEC/Thermotron Reliability Chamber、Power Cycle Tester。管理周期：每Lot抽样(5~25 Die/Lot)。异常处理：Reliability Fail(HTRB Leakage增加、Power Cycle Crack)→Lot全Hold→Root Cause分析后Disposition。 | 9 | process_step | Reliability |
| 7 | Batch Genealogy | 需把Batch ID、Recipe、Equipment和Backside条件连接到Die Grade。测量方法：MES+EAP数据集成查询。管理周期：Real-time。异常处理：不可追溯→Data补充→Full Hold。 | 2,3,5,6,8,10 | process_step | Batch Genealogy |

## 4.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, device_type, voltage_class, current_class |
| 2 | Frontside | batch |  |  | batch_id, recipe_id, equipment_id, oxide_thickness |
| 3 | Frontside | batch |  |  | recipe_id, equipment_id, frontside_cd, batch_id |
| 4 | Frontside | batch |  |  | recipe_id, equipment_id, frontside_cd |
| 5 | Backside | batch |  |  | wafer_thickness, bow_warp, equipment_id, batch_id |
| 6 | Backside | batch |  |  | backside_metal_id, recipe_id, equipment_id, batch_id |
| 7 | Gate | gate |  | 2,3,4,5,6 | visual_defect_map, wafer_thickness, bow_warp, oxide_thickness |
| 8 | Probe | process |  |  | probe_result, bv_result, rdson_result, leakage_result |
| 9 | Reliability | process |  |  | reliability_sample_id, device_type, voltage_class |
| 10 | Handoff | process |  |  | die_grade, probe_result, backside_metal_id |

## 4.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, device_type, voltage_class, current_class |
| 2 | Frontside | batch |  |  | batch_id, recipe_id, equipment_id, oxide_thickness |
| 3 | Frontside | batch |  |  | recipe_id, equipment_id, frontside_cd, batch_id |
| 4 | Frontside | batch |  |  | recipe_id, equipment_id, frontside_cd |
| 5 | Backside | batch |  |  | wafer_thickness, bow_warp, equipment_id, batch_id |
| 6 | Backside | batch |  |  | backside_metal_id, recipe_id, equipment_id, batch_id |
| 7 | Gate | gate |  | 2,3,4,5,6 | visual_defect_map, wafer_thickness, bow_warp, oxide_thickness |
| 8 | Probe | process |  |  | probe_result, bv_result, rdson_result, leakage_result |
| 9 | Reliability | process |  |  | reliability_sample_id, device_type, voltage_class |
| 10 | Handoff | process |  |  | die_grade, probe_result, backside_metal_id |

## 4.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 4.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 4.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - device_type
  - voltage_class
  - current_class
  - recipe_id
  - equipment_id
  - batch_id
  - frontside_cd
  - oxide_thickness
  - wafer_thickness
  - bow_warp
  - backside_metal_id
  - visual_defect_map
  - probe_result
  - bv_result
  - rdson_result
  - leakage_result
  - reliability_sample_id
  - die_grade
```

---

# 5. B05 — 광학·이미지센서

```yaml
subindustry_code: B05
legacy_slug: optical_sensor
label_ko: 광학·이미지센서
label_zh: 光学·图像传感器
label_en: ""
label_ja: ""
routing: RT_REENTRANT
preset_id: reentrant_module_v1
expression_tier: P3_PFLOW_REENTRANT
routing_description_ko: >
  광학·이미지센서는 Pixel Array, Color Filter/Microlens, Optical Stack, Dark/White Pixel, Optical/Electrical Test가 핵심이다. Ch3는 광학 결함과 전기 Bin을 함께 표현해야 한다. 2026년 기준 Recipe-less AI 검사와 엣지 AI 기반 실시간 결함 탐지 기술이 도입되어 AOI 공정의 패러다임을 변화시키고 있다.
routing_description_zh: >
  光学/图像传感器以Pixel Array、Color Filter/Microlens、Optical Stack、Dark/White Pixel和光电测试为核心。Ch3需要同时表达光学缺陷和电性Bin。2026年Recipe-less AI检测和边缘AI实时缺陷检测技术正在引入，改变AOI工序的范式。
```

## 5.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Sensor Baseline | Sensor Type(CMOS Image Sensor, CCD, SPAD, ToF Sensor), Pixel Size(0.5~5μm), Optical Stack(BSI/FSI, RGB/IR/RGBW CFA), Mask, Test 조건을 확정한다. MES에서 Sensor Type별 Route·Optical Stack Recipe·Test Program을 매핑한다. BSI(Backside Illumination)와 FSI(Frontside Illumination)는 공정 흐름이 크게 달라지므로 Lot ID와 함께 Sensor Architecture Code를 Tracking Key로 설정한다. |
| 2 | Pixel Array Formation | Photodiode(Pinned Photodiode, Implant Profile 최적화), Transfer Gate(핵심 노이즈 특성, Charge Transfer Efficiency), Isolation(Deep Trench Isolation, DT Pixel Separation) 등 Pixel Array 구조를 형성한다. Pixel CD(0.5~5μm)는 CD-SEM(Hitachi)으로, Photodiode Junction Depth는 SIMS로 검증한다. Pixel Fill Factor 및 Dark Current 특성은 소자 설계 값 기준으로 Lot당 샘플링 평가한다. |
| 3 | Readout / Peripheral Circuit | ADC(Column ADC / Single-slope ADC, 10~14bit, Conversion Rate), Timing(Readout Timing Generator, Row/Column Decoder), Readout Circuit(Correlated Double Sampling CDS), Peripheral Device를 형성한다. Readout Noise(RMS <3e- for High-end Sensor)는 ATE로 Wafer Sort 단계에서 검증하며, Timing Jitter는 Oscilloscope(Tektronix DPO70000)로 측정한다. |
| 4 | Interconnect / Passivation | Cu/W Metal, Via(Tungsten Plug, Cu Dual Damascene), Passivation(SiN/SiON, PECVD 300~400℃), Bond Pad 구조를 형성한다. BSI Sensor는 Backside Passivation과 Anti-reflection Coating(ARC, SiON / SiO₂)을 추가로 형성한다. Metal Stack의 Sheet Resistance는 4-Point Probe로 Layer별 관리하며, Passivation Pin Hole은 Voltage Contrast SEM으로 검출한다. |
| 5 | Color Filter Array | Color Filter(RGB/Bayer, RCCC, RYYB 등 CFA 패턴, Dye계 / Pigment계, Spin Coating 두께 1~3μm), Pattern(Photolithography, Stepper / Scanner 정렬 ±0.2μm), Cure(Post-bake 200~250℃), Color Uniformity(Chromaticity x,y 좌표, ΔE <1)를 관리한다. Color Filter Spectrum은 Spectrophotometer(Ocean Optics / Konica Minolta)로 파장 400~700nm 전 영역 측정하며, Color Mixing / Bleeding은 광학 현미경(High-power) 검사로 확인한다. |
| 6 | Microlens / Optical Stack | Microlens(Photoresist Reflow or Gray-tone Litho, 곡률 반경 1~5μm, Focal Length 정밀도 <0.1μm), Planarization(Bottom ARC, Spin-on-Glass, 0.5~2μm), IR Filter 계열(Cut-off Filter, IR Absorption Layer, 700~1100nm 차단) 광학 Stack을 형성한다. Microlens Alignment와 Focal Length는 Confocal Microscope / White Light Interferometer(Zygo / Bruker)로 검증하며, 광 투과율은 Integrating Sphere Spectrophotometer로 측정한다. |
| 7 | Inline Optical Metrology | Film Thickness(Ellipsometer, KLA Aleris, 각 Optical Layer 두께 ±2%), Alignment(Overlay Microscope / BoX Alignment, Alignment <0.3μm), Defect(Optical Microscope, KLA Brightfield, Pixel Defect 검출), Color Uniformity(CIE xy Chromaticity, RGB Spectral 분포), Pixel Defect(Dark Current <10 e-/s, White Pixel Count <10ppm)를 계측한다. |
| 8 | Optical / Electrical Gate | Dark Current(Dark Image, Integration Time 1~30ms, Median DN), White Pixel(Column/Cluster White, Count Limit), Sensitivity(Responsivity, mV/lux·s), Electrical Bin(ADC Noise, Readout Rate, Timing Error)을 Gate로 판정한다. Optical Test Equipment(Image Sensor Test System, Hamamatsu / JAI)와 Electrical ATE(Advantest / Teradyne)가 연동된 Hybrid Test가 수행된다. Gate Fail 시 Lot Hold → Pixel Defect Map 분석 → 공정 조정(Implant / Etch 조건)으로 이어진다. |
| 9 | Wafer Sort / Image Test | Wafer Sort(Teradyne J750 / Advantest T2000 + Image Sensor Tester, 온도 25~85℃), Image Test(Dark Image, Bright Image, Uniformity, Defect Map)를 수행하고 Pixel Defect Map과 Bin(Bin1 Full Spec / Bin2 Minor Defect / Bin3 Optical Fail / Bin4 Electrical Fail)을 생성한다. Optical/Electrical 통합 Bin Map은 YMS에 전송되며, 고객별 Defect 허용치 기준으로 재분류 가능하다. |
| 10 | Yield Review / Customer Grade | 광학·전기 Bin(Dark/White Pixel Count, Sensitivity Grade, ADC Bin Grade), 고객 Grade(Automotive/Consumer/Industrial, Defect 허용 기준 상이), 출하 조건(Reel / Tray, Taping)을 확정한다. YMS Dashboard에서 Optical Defect Spatial Map + Electrical Bin Overlay 분석을 통해 Yield Loss Root Cause(광학 Stack 불량, Pixel Array Defect, Readout 회로 이상)를 정밀 진단한다. |

## 5.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Lot Release / Sensor Baseline | 确认Sensor Type(CMOS Image Sensor、CCD、SPAD、ToF Sensor)、Pixel Size(0.5~5μm)、Optical Stack(BSI/FSI、RGB/IR/RGBW CFA)、Mask、Test条件。MES按Sensor Type映射Route/Optical Stack Recipe/Test Program。BSI(Backside Illumination)和FSI(Frontside Illumination)的工艺流差异大，以Lot ID和Sensor Architecture Code设为Tracking Key。 |
| 2 | Pixel Array Formation | 形成Photodiode(Pinned Photodiode，Implant Profile优化)、Transfer Gate(核心噪声特性，Charge Transfer Efficiency)、Isolation(Deep Trench Isolation，DT Pixel Separation)等Pixel Array结构。Pixel CD(0.5~5μm)用CD-SEM(Hitachi)量测，Photodiode Junction Depth用SIMS验证。Pixel Fill Factor和Dark Current特性按设计值每Lot抽样评估。 |
| 3 | Readout / Peripheral Circuit | 形成ADC(Column ADC/Single-slope ADC，10~14bit，Conversion Rate)、Timing(Readout Timing Generator，Row/Column Decoder)、Readout Circuit(Correlated Double Sampling CDS)、Peripheral器件。Readout Noise(RMS<3e- for High-end Sensor)在Wafer Sort阶段用ATE验证，Timing Jitter用Oscilloscope(Tektronix DPO70000)测量。 |
| 4 | Interconnect / Passivation | 形成Cu/W Metal、Via(Tungsten Plug，Cu Dual Damascene)、Passivation(SiN/SiON，PECVD 300~400℃)、Bond Pad结构。BSI Sensor额外形成Backside Passivation和Anti-reflection Coating(ARC，SiON/SiO₂)。Metal Stack的Sheet Resistance按Layer用4-Point Probe管理，Passivation Pin Hole用Voltage Contrast SEM检测。 |
| 5 | Color Filter Array | 管理Color Filter(RGB/Bayer、RCCC、RYYB等CFA图形、Dye系/Pigment系、Spin Coating厚度1~3μm)、Pattern(Photolithography、Stepper/Scanner对准±0.2μm)、Cure(Post-bake 200~250℃)、Color Uniformity(Chromaticity x,y坐标，ΔE<1)。Color Filter Spectrum用Spectrophotometer(Ocean Optics/Konica Minolta)在波长400~700nm全区域测量，Color Mixing/Bleeding用光学显微镜(High-power)检查确认。 |
| 6 | Microlens / Optical Stack | 形成Microlens(Photoresist Reflow或Gray-tone Litho，曲率半径1~5μm，Focal Length精度<0.1μm)、Planarization(Bottom ARC、Spin-on-Glass、0.5~2μm)、IR Filter系列(Cut-off Filter、IR Absorption Layer、700~1100nm阻挡)光学Stack。Microlens Alignment和Focal Length用Confocal Microscope/White Light Interferometer(Zygo/Bruker)验证，光透过率用Integrating Sphere Spectrophotometer测量。 |
| 7 | Inline Optical Metrology | 量测Film Thickness(Ellipsometer，KLA Aleris，各Optical Layer厚度±2%)、Alignment(Overlay Microscope/BoX Alignment，Alignment<0.3μm)、Defect(Optical Microscope、KLA Brightfield、Pixel Defect检测)、Color Uniformity(CIE xy Chromaticity、RGB Spectral分布)、Pixel Defect(Dark Current<10 e-/s、White Pixel Count<10ppm)。 |
| 8 | Optical / Electrical Gate | 以Dark Current(Dark Image、Integration Time 1~30ms、Median DN)、White Pixel(Column/Cluster White、Count Limit)、Sensitivity(Responsivity、mV/lux·s)、Electrical Bin(ADC Noise、Readout Rate、Timing Error)作为Gate判定。Optical Test Equipment(Image Sensor Test System、Hamamatsu/JAI)与Electrical ATE(Advantest/Teradyne)联动的Hybrid Test执行。Gate Fail时Lot Hold→Pixel Defect Map分析→工艺调整(Implant/Etch条件)。 |
| 9 | Wafer Sort / Image Test | 执行Wafer Sort(Teradyne J750/Advantest T2000+Image Sensor Tester，温度25~85℃)、Image Test(Dark Image、Bright Image、Uniformity、Defect Map)并生成Pixel Defect Map和Bin(Bin1 Full Spec/Bin2 Minor Defect/Bin3 Optical Fail/Bin4 Electrical Fail)。Optical/Electrical集成Bin Map发送YMS，可按客户Defect允许标准重新分类。 |
| 10 | Yield Review / Customer Grade | 确定光学/电性Bin(Dark/White Pixel Count、Sensitivity Grade、ADC Bin Grade)、客户Grade(Automotive/Consumer/Industrial，Defect允许标准不同)、出货条件(Reel/Tray、Taping)。YMS Dashboard通过Optical Defect Spatial Map+Electrical Bin Overlay分析，精确定位Yield Loss Root Cause(光学Stack不良、Pixel Array缺陷、Readout电路异常)。 |

## 5.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Pixel Array 관리 | Pixel Defect, Dark Current, White Pixel 결과를 Pixel 구조와 연결해야 한다. 측정 장비/방법: Image Sensor Test System(Hamamatsu / JAI) + Dark Box 측정, EMVA 1288 Standard. 관리 주기: Wafer Sort 시(Every Lot). 이상 시 조치: Pixel Defect Cluster → Photodiode Implant / DTI 조건 재검토 → Test Vehicle 검증. | 2,7,8 | process_step | Pixel Quality |
| 2 | Color Filter/Microlens 이력 | Color Filter Lot와 Microlens Lot를 Wafer·Bin 결과와 연결해야 한다. 측정 장비/방법: Spectrophotometer(Ocean Optics) Color Spectrum 검증, Confocal Microscope Microlens Profile 계측. 관리 주기: Optical Stack Layer별 샘플링(Every Layer). 이상 시 조치: Color Offset / Focal Shift → CFA/Microlens Recipe 조정 → 재계측. | 5,6,10 | process_step | Optical Stack |
| 3 | Optical/Electrical Gate | 광학 특성과 전기 Bin이 모두 Spec을 만족해야 후속 출하가 가능하다. 측정 장비: Hybrid Test System(Optical + ATE 통합), KLA Defect Inspection. 관리 주기: Module 완료 시 Lot당(Every Lot). 이상 시 조치: Gate Fail → Pixel Defect + ADC Noise 분석 → Root Cause 식별(광학 vs 전기) → 각각 Recipe 조정. | 8,9 | process_step | Optical / Electrical Gate |
| 4 | Customer Grade 판정 | 고객별 Sensor Grade, Defect 허용치, Image Test 조건을 분리해야 한다. 측정 방법: YMS Bin Table별 Grade 매핑, 고객 Spec Sheet 대조. 관리 주기: Lot 종료 시(Every Lot). 이상 시 조치: Grade Mis-classification → Bin Limit 재검증 → 고객 QA 승인 재획득. | 10 | process_step | Customer Grade |

## 5.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Pixel Array管理 | 需把Pixel Defect、Dark Current、White Pixel结果与Pixel结构连接。测量设备/方法：Image Sensor Test System(Hamamatsu/JAI)+Dark Box测量、EMVA 1288 Standard。管理周期：Wafer Sort时(Every Lot)。异常处理：Pixel Defect Cluster→Photodiode Implant/DTI条件重新评估→Test Vehicle验证。 | 2,7,8 | process_step | Pixel Quality |
| 2 | Color Filter/Microlens履历 | 需把Color Filter Lot和Microlens Lot连接到Wafer/Bin结果。测量设备/方法：Spectrophotometer(Ocean Optics)Color Spectrum验证、Confocal Microscope Microlens Profile量测。管理周期：Optical Stack每层抽样(Every Layer)。异常处理：Color Offset/Focal Shift→CFA/Microlens Recipe调整→重新量测。 | 5,6,10 | process_step | Optical Stack |
| 3 | Optical/Electrical Gate | 光学特性和电性Bin均满足Spec后才可进入出货流程。测量设备：Hybrid Test System(Optical+ATE集成)、KLA Defect Inspection。管理周期：Module完成时每Lot(Every Lot)。异常处理：Gate Fail→Pixel Defect+ADC Noise分析→Root Cause识别(光学vs电性)→分别Recipe调整。 | 8,9 | process_step | Optical / Electrical Gate |
| 4 | Customer Grade判定 | 需按客户区分Sensor Grade、缺陷允许值和Image Test条件。测量方法：YMS Bin Table Grade映射、客户Spec Sheet对照。管理周期：Lot结束时(Every Lot)。异常处理：Grade误分类→Bin Limit重新验证→客户QA批准重新获取。 | 10 | process_step | Customer Grade |

## 5.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, sensor_type, pixel_size |
| 2 | Pixel | process |  |  | recipe_id, equipment_id, reticle_id, pixel_defect_map |
| 3 | Readout | process |  |  | recipe_id, equipment_id, electrical_bin |
| 4 | Interconnect | process |  |  | recipe_id, equipment_id, film_thickness |
| 5 | Optical Stack | process |  |  | color_filter_lot, film_thickness, defect_map |
| 6 | Optical Stack | process |  |  | microlens_lot, film_thickness, defect_map |
| 7 | Optical Metrology | process |  |  | pixel_defect_map, film_thickness, defect_map |
| 8 | Gate | gate |  | 2,3,4,5,6,7 | dark_current, white_pixel_count, optical_bin, electrical_bin, pixel_defect_map |
| 9 | Sort | process |  |  | wafer_sort_bin, optical_bin, electrical_bin, pixel_defect_map |
| 10 | Yield | process |  |  | customer_grade, optical_bin, electrical_bin, wafer_sort_bin |

## 5.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, sensor_type, pixel_size |
| 2 | Pixel | process |  |  | recipe_id, equipment_id, reticle_id, pixel_defect_map |
| 3 | Readout | process |  |  | recipe_id, equipment_id, electrical_bin |
| 4 | Interconnect | process |  |  | recipe_id, equipment_id, film_thickness |
| 5 | Optical Stack | process |  |  | color_filter_lot, film_thickness, defect_map |
| 6 | Optical Stack | process |  |  | microlens_lot, film_thickness, defect_map |
| 7 | Optical Metrology | process |  |  | pixel_defect_map, film_thickness, defect_map |
| 8 | Gate | gate |  | 2,3,4,5,6,7 | dark_current, white_pixel_count, optical_bin, electrical_bin, pixel_defect_map |
| 9 | Sort | process |  |  | wafer_sort_bin, optical_bin, electrical_bin, pixel_defect_map |
| 10 | Yield | process |  |  | customer_grade, optical_bin, electrical_bin, wafer_sort_bin |

## 5.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 5.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 5.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - sensor_type
  - pixel_size
  - recipe_id
  - equipment_id
  - reticle_id
  - pixel_defect_map
  - dark_current
  - white_pixel_count
  - color_filter_lot
  - microlens_lot
  - film_thickness
  - optical_bin
  - electrical_bin
  - wafer_sort_bin
  - defect_map
  - customer_grade
```

---

# 6. B06 — 화합물반도체

```yaml
subindustry_code: B06
legacy_slug: compound_semi
label_ko: 화합물반도체
label_zh: 化合物半导体
label_en: ""
label_ja: ""
routing: RT_BATCH
preset_id: batch_process_v1
expression_tier: P3_PFLOW_BATCH
routing_description_ko: >
  화합물반도체는 Epi 품질이 수율을 좌우하며, Mesa, Gate, Ohmic Contact, RF/DC Probe가 핵심이다. Substrate·Epi·Reactor·Run 단위 추적이 중요하다. 2026년 기준 MOCVD/MBE Reactor의 AI 모니터링 및 예측 정비 솔루션이 본격 도입되어 Epi 품질 안정화와 장비 가동률 향상에 기여하고 있다.
routing_description_zh: >
  化合物半导体的Epi质量直接决定良率，Mesa、Gate、Ohmic Contact和RF/DC Probe是核心。必须追踪Substrate、Epi、Reactor和Run维度。2026年MOCVD/MBE Reactor的AI监控和预测维护方案正式引入，助力Epi质量稳定化和设备稼动率提升。
```

## 6.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Substrate Receive / Qualification | SiC(6H/4H-SiC, Conductive/Semi-insulating, 100/150mm), GaN(Free-standing GaN / Si(111) / Sapphire Template), GaAs(Semi-insulating / Conductive, 100/150mm), InP(Fe-doped, 50~100mm) 등 기판 ID, Orientation(Off-cut 0~4°), 결함 수준(EPD Etch Pit Density <5000/cm², Micropipe Density SiC <1/cm²)을 확인한다. Substrate Quality는 PL(Photoluminescence) Mapping과 XRT(X-ray Topography)로 Lot당 수입 검사한다. 각 기판에 Unique Substrate ID를 Laser Mark하여 추적성을 확보한다. |
| 2 | Epitaxy Growth | MOCVD(Aixtron / Veeco, GaN: 1000~1100℃, GaAs: 650~750℃, Pressure 50~1000mbar) / MBE(Riber / Veeco Gen930, UHV 10^-10 Torr) / Epi Run, Epitaxial Layer 두께(0.5~10μm), 조성(AlGaAs / InGaAs / GaN HEMT 구조, Composition ±1%), 결함 밀도(Cross-hatch, Oval Defect, Stacking Fault <100/cm²), Reactor 상태(Showerhead Temp Uniformity ±1℃, Gas Flow MFC Calibration)를 관리한다. Epi Run ID와 Reactor ID를 기준으로 Batch 이력을 생성하며, In-situ Reflectance Monitoring(LayTec / k-Space Associates)으로 실시간 성장 두께를 모니터링한다. |
| 3 | Epi Characterization Gate | PL(Photoluminescence, Wavelength Peak·FWHM, Lot당 Mapping), XRD(High Resolution X-ray Diffraction, Film Composition·Strain·Crystallinity, Ω-2θ Scan + RSM), Thickness Map(FTIR / Reflectometry, 두께 균일도 <3%), Defect Density(Nomadic / PL Mapping Defect Count)로 Epi 품질을 Gate 판정한다. Spec 이탈 시 Epi Wafer Auto Hold → Reactor Condition Review → Epi Run Parameter 조정(Gas Flow Ratio V/III, Temperature) → 재성장 또는 Scrap 결정. |
| 4 | Mesa / Isolation | Mesa Etch(ICP-RIE Dry Etch, Oxford / STS / Samco, GaN/ GaAs Etch Rate 100~500nm/min, Profile Angle 60~90°), Isolation Implant(H⁺, He⁺ or N⁺, Energy 50~300keV, Dose 1e12~1e15/cm²), Surface Damage 관리(Post-etch Anneal / Wet Treatment)와 CD(CD-SEM Hitachi, <0.5μm 정밀도)를 관리한다. Mesa Sidewall Profile은 SEM Cross-section으로 Lot당 샘플링 검증하며, Etch Damage Depth는 PL Intensity 변화로 평가한다. |
| 5 | Ohmic Contact Formation | Ohmic Metal(Ti/Al/Ni/Au for GaN HEMT, AuGe/Ni/Au for GaAs, Sputter / E-beam Evaporation), Anneal(RTP 700~900℃, N₂ Ambient, 30~120s, Ohmic Contact Formation), Contact Resistance(TLM PCM, Rc <0.5 Ω·mm for GaN, <0.1 Ω·mm for GaAs)와 표면 상태(Optical Microscope, AFM Surface Roughness <5nm)를 관리한다. |
| 6 | Gate / Schottky Formation | Gate Length(0.1~1μm, E-beam Litho / Stepper, Gate CD 정밀도 ±10%), Schottky Contact(Ni/Au Gate metal, E-beam Evaporation, Schottky Barrier Height ~0.8~1.0eV for GaN), Threshold Voltage(Vth 정밀도 ±50mV), Gate Leakage(<10μA/mm at Vgs) 조건을 관리한다. Gate Length는 CD-SEM / SEM Cross-section으로 Lot당 검증하며, Schottky 특성은 Forward I-V / Reverse Breakdown 측정으로 평가한다. |
| 7 | Passivation / Field Plate | Passivation(SiN / Al₂O₃ / SiO₂, PECVD/ALD 200~400℃, 두께 50~500nm), Field Plate(Field Plate 구조, Gate 확장 금속, Off-state Breakdown 향상, Air Bridge 구조용 Photo-resist), Reliability 구조를 형성한다. Passivation Coverage는 SEM Cross-section으로 평가하며, Field Plate Breakdown Voltage는 TLP(Transmission Line Pulse) 또는 DC I-V 측정으로 검증한다. |
| 8 | RF/DC Probe Gate | RF S-parameter(S-parameter Vector Network Analyzer VNA, Keysight / Rohde & Schwarz, 0.1~110GHz, ft, fmax, S21 Gain), DC I-V(Idsat, Gm Peak, Vth, Ron, Leakage, Keysight B1500A), Leakage(Gate Leakage, Buffer Leakage, Substrate Leakage), Breakdown(Off-state Breakdown, Three-terminal Breakdown) 결과를 Gate로 판정한다. Probe Station(Cascade / MPI)에 RF Probe(GSG, 100~250μm Pitch)를 장착하여 On-wafer 측정한다. Gate Fail 시 Auto Hold → Mesa/Ohmic/Gate 공정 Reciepe 검토 → MRB. |
| 9 | Reliability Sample / Burn-in | HTOL(High Temperature Operating Life, 150~250℃, Bias Stress, 1000h), HTRB(High Temperature Reverse Bias, 150℃, 80% Vbr, 1000h), RF Stress(RF Overdrive, 24~168h, Gain Drift 모니터링), Power Cycle(ΔTj, 1000~10000 cycle) 샘플을 선정한다. Reliability Chamber(ESPEC / Thermotron) + RF Stress Fixture를 사용하며, Lot별 Device Type·Material System 기준 5~15개 Die / Lot로 샘플링한다. |
| 10 | Yield Review / Backend Handoff | Die Grade(Bin1~4, RF Performance Grade: High / Mid / Low Gain, DC Grade: Pass / Fail), Wafer Map(RF Gain Map, DC Idsat Map, Spatial Uniformity), Package 투입 조건(Dicing 전 두께, Backside Via / Ground 요구사항)을 확정한다. YMS Dashboard에서 Probe Bin + Reliability 결과를 통합 분석하며, 제품 출하 증명서(CoA, Certificate of Analysis)를 발행한다. |

## 6.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Substrate Receive / Qualification | 确认SiC(6H/4H-SiC、Conductive/Semi-insulating、100/150mm)、GaN(Free-standing GaN/Si(111)/Sapphire Template)、GaAs(Semi-insulating/Conductive、100/150mm)、InP(Fe-doped、50~100mm)等衬底ID、Orientation(Off-cut 0~4°)、缺陷水平(EPD Etch Pit Density<5000/cm²、Micropipe Density SiC<1/cm²)。Substrate Quality用PL(Photoluminescence) Mapping和XRT(X-ray Topography)按Lot进行入厂检验。每个衬底用Laser Mark定位Unique Substrate ID以确保可追溯性。 |
| 2 | Epitaxy Growth | 管理MOCVD(Aixtron/Veeco、GaN：1000~1100℃、GaAs：650~750℃、Pressure 50~1000mbar)/MBE(Riber/Veeco Gen930、UHV 10^-10 Torr)/Epi Run、Epitaxial Layer厚度(0.5~10μm)、组分(AlGaAs/InGaAs/GaN HEMT结构、Composition±1%)、缺陷密度(Cross-hatch、Oval Defect、Stacking Fault<100/cm²)、Reactor状态(Showerhead Temp Uniformity±1℃、Gas Flow MFC Calibration)。以Epi Run ID和Reactor ID为基准生成Batch履历，用In-situ Reflectance Monitoring(LayTec/k-Space Associates)实时监控生长厚度。 |
| 3 | Epi Characterization Gate | 通过PL(Photoluminescence、Wavelength Peak·FWHM、每Lot Mapping)、XRD(High Resolution X-ray Diffraction、Film Composition·Strain·Crystallinity、Ω-2θ Scan+RSM)、Thickness Map(FTIR/Reflectometry、厚度均匀性<3%)、Defect Density(Nomadic/PL Mapping Defect Count)判定Epi质量Gate。超Spec时Epi Wafer Auto Hold→Reactor Condition Review→Epi Run参数调整(Gas Flow Ratio V/III、Temperature)→重新生长或Scrap决定。 |
| 4 | Mesa / Isolation | 管理Mesa Etch(ICP-RIE Dry Etch、Oxford/STS/Samco、GaN/GaAs Etch Rate 100~500nm/min、Profile Angle 60~90°)、Isolation Implant(H⁺、He⁺或N⁺、Energy 50~300keV、Dose 1e12~1e15/cm²)、Surface Damage管理(Post-etch Anneal/Wet Treatment)和CD(CD-SEM Hitachi、<0.5μm精度)。Mesa Sidewall Profile用SEM截面按Lot抽样验证，Etch Damage Depth通过PL Intensity变化评估。 |
| 5 | Ohmic Contact Formation | 管理Ohmic Metal(Ti/Al/Ni/Au for GaN HEMT、AuGe/Ni/Au for GaAs、Sputter/E-beam Evaporation)、Anneal(RTP 700~900℃、N₂ Ambient、30~120s、Ohmic Contact Formation)、Contact Resistance(TLM PCM、Rc<0.5 Ω·mm for GaN、<0.1 Ω·mm for GaAs)和表面状态(Optical Microscope、AFM Surface Roughness<5nm)。 |
| 6 | Gate / Schottky Formation | 管理Gate Length(0.1~1μm、E-beam Litho/Stepper、Gate CD精度±10%)、Schottky Contact(Ni/Au Gate metal、E-beam Evaporation、Schottky Barrier Height~0.8~1.0eV for GaN)、Threshold Voltage(Vth精度±50mV)、Gate Leakage(<10μA/mm at Vgs)条件。Gate Length用CD-SEM/SEM截面按Lot验证，Schottky特性通过Forward I-V/Reverse Breakdown评估。 |
| 7 | Passivation / Field Plate | 形成Passivation(SiN/Al₂O₃/SiO₂、PECVD/ALD 200~400℃、厚度50~500nm)、Field Plate(Field Plate结构、Gate扩展金属、Off-state Breakdown改善、Air Bridge结构用Photo-resist)、Reliability结构。Passivation Coverage用SEM截面评估，Field Plate Breakdown Voltage用TLP(Transmission Line Pulse)或DC I-V测量验证。 |
| 8 | RF/DC Probe Gate | 以RF S-parameter(S-parameter Vector Network Analyzer VNA、Keysight/Rohde & Schwarz、0.1~110GHz、ft、fmax、S21 Gain)、DC I-V(Idsat、Gm Peak、Vth、Ron、Leakage、Keysight B1500A)、Leakage(Gate Leakage、Buffer Leakage、Substrate Leakage)、Breakdown(Off-state Breakdown、Three-terminal Breakdown)结果作为Gate判定。Probe Station(Cascade/MPI)安装RF Probe(GSG、100~250μm Pitch)执行On-wafer测量。Gate Fail时Auto Hold→Mesa/Ohmic/Gate工艺Recipe审核→MRB。 |
| 9 | Reliability Sample / Burn-in | 选择HTOL(High Temperature Operating Life、150~250℃、Bias Stress、1000h)、HTRB(High Temperature Reverse Bias、150℃、80% Vbr、1000h)、RF Stress(RF Overdrive、24~168h、Gain Drift监控)、Power Cycle(ΔTj、1000~10000 cycle)样本。使用Reliability Chamber(ESPEC/Thermotron)+RF Stress Fixture，按Lot Device Type/Material System选5~15个Die/Lot抽样。 |
| 10 | Yield Review / Backend Handoff | 确定Die Grade(Bin1~4、RF Performance Grade：High/Mid/Low Gain、DC Grade：Pass/Fail)、Wafer Map(RF Gain Map、DC Idsat Map、Spatial Uniformity)、Package投入条件(Dicing前厚度、Backside Via/Ground要求)。YMS Dashboard综合Probe Bin+Reliability结果分析，发布产品出货证明书(CoA、Certificate of Analysis)。 |

## 6.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Epi Run 관리 | Epi Run, Reactor, Thickness, Composition, Defect Density가 수율의 선행 인자다. 측정 장비: PL Mapping(Nanometrics / Accent), XRD(Bede / Bruker D8), FTIR Thickness Gauge, Nomadic Defect Inspection. 관리 주기: Run 단위(Every Run). 이상 시 조치: Epi Quality Fail → Epi Wafer Scrap → Reactor PM Status 확인 → MFC Calibration → Recipe Parameter 조정 후 재Run. | 2,3 | process_step | Epi Control |
| 2 | Substrate 추적 | Substrate ID와 Material System을 Die Grade까지 연결해야 한다. 측정 방법: Substrate Laser Mark Reader + MES 연동, PL/XRT 수입 검사 결과. 관리 주기: Substrate 수입 시(Every Substrate). 이상 시 조치: Substrate Quality Low(EPD Micropipe High) → 반품 또는 저등급 제품 전용. | 1,10 | process_step | Substrate Genealogy |
| 3 | RF/DC Probe Gate | RF/DC 측정 결과가 Spec을 벗어나면 Hold와 원인 분석으로 연결해야 한다. 측정 장비: Keysight PNA-X VNA(0.1~67GHz)/Rohde & Schwarz ZVA110, Keysight B1500A DC Analyzer, Cascade / MPI RF Probe Station. 관리 주기: Die 단위(Every Die). 이상 시 조치: RF Gain Low / DC Fail → Auto Hold → Mesa/Gate/Ohmic 조건 검증 → MRB. | 8 | process_step | Probe Gate |
| 4 | Ohmic/Gate 핵심 특성 | Ohmic Resistance와 Gate Length는 전기성능과 신뢰성의 핵심 관리항목이다. 측정 장비: TLM PCM(Keysight B1500A), CD-SEM(Hitachi), SEM Cross-section, AFM. 관리 주기: Lot당 샘플링(Every Lot). 이상 시 조치: Rc >Spec / Gate CD Offset → Anneal 조건(Gas, Temp, Time) 또는 Litho Recipe 조정 → 재검증. | 5,6,8 | process_step | Device Parameter |

## 6.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Epi Run管理 | Epi Run、Reactor、Thickness、Composition、Defect Density是良率先行因子。测量设备：PL Mapping(Nanometrics/Accent)、XRD(Bede/Bruker D8)、FTIR Thickness Gauge、Nomadic Defect Inspection。管理周期：每Run(Every Run)。异常处理：Epi Quality Fail→Epi Wafer Scrap→Reactor PM Status确认→MFC Calibration→Recipe参数调整后重新Run。 | 2,3 | process_step | Epi Control |
| 2 | Substrate追踪 | 需把Substrate ID和Material System连接到Die Grade。测量方法：Substrate Laser Mark Reader+MES联动、PL/XRT入厂检验结果。管理周期：Substrate入厂时(Every Substrate)。异常处理：Substrate Quality Low(EPD Micropipe High)→退货或专用低等级产品。 | 1,10 | process_step | Substrate Genealogy |
| 3 | RF/DC Probe Gate | RF/DC测量结果超Spec时，应连接Hold和原因分析。测量设备：Keysight PNA-X VNA(0.1~67GHz)/Rohde & Schwarz ZVA110、Keysight B1500A DC Analyzer、Cascade/MPI RF Probe Station。管理周期：每Die(Every Die)。异常处理：RF Gain Low/DC Fail→Auto Hold→Mesa/Gate/Ohmic条件验证→MRB。 | 8 | process_step | Probe Gate |
| 4 | Ohmic/Gate核心特性 | Ohmic Resistance和Gate Length是电性与可靠性的核心管理项。测量设备：TLM PCM(Keysight B1500A)、CD-SEM(Hitachi)、SEM截面、AFM。管理周期：每Lot抽样(Every Lot)。异常处理：Rc>Spec/Gate CD Offset→调整Anneal条件(Gas、Temp、Time)或Litho Recipe→重新验证。 | 5,6,8 | process_step | Device Parameter |

## 6.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, substrate_id, material_system |
| 2 | Epi | batch |  |  | epi_run_id, reactor_id, thickness_map, composition_result, defect_density |
| 3 | Epi Gate | gate |  | 2 | thickness_map, composition_result, defect_density, epi_run_id |
| 4 | Mesa | batch |  |  | recipe_id, equipment_id, mesa_cd |
| 5 | Ohmic | batch |  |  | recipe_id, equipment_id, ohmic_resistance |
| 6 | Gate | batch |  |  | recipe_id, equipment_id, gate_length |
| 7 | Passivation | batch |  |  | recipe_id, equipment_id, defect_density |
| 8 | Probe Gate | gate |  | 4,5,6,7 | rf_probe_result, dc_probe_result, ohmic_resistance, gate_length |
| 9 | Reliability | process |  |  | reliability_sample_id, material_system, die_grade |
| 10 | Handoff | process |  |  | die_grade, wafer_sort_bin, rf_probe_result, dc_probe_result |

## 6.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Start | process |  |  | lot_id, wafer_id, substrate_id, material_system |
| 2 | Epi | batch |  |  | epi_run_id, reactor_id, thickness_map, composition_result, defect_density |
| 3 | Epi Gate | gate |  | 2 | thickness_map, composition_result, defect_density, epi_run_id |
| 4 | Mesa | batch |  |  | recipe_id, equipment_id, mesa_cd |
| 5 | Ohmic | batch |  |  | recipe_id, equipment_id, ohmic_resistance |
| 6 | Gate | batch |  |  | recipe_id, equipment_id, gate_length |
| 7 | Passivation | batch |  |  | recipe_id, equipment_id, defect_density |
| 8 | Probe Gate | gate |  | 4,5,6,7 | rf_probe_result, dc_probe_result, ohmic_resistance, gate_length |
| 9 | Reliability | process |  |  | reliability_sample_id, material_system, die_grade |
| 10 | Handoff | process |  |  | die_grade, wafer_sort_bin, rf_probe_result, dc_probe_result |

## 6.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 6.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 6.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - substrate_id
  - material_system
  - epi_run_id
  - reactor_id
  - recipe_id
  - equipment_id
  - thickness_map
  - composition_result
  - defect_density
  - mesa_cd
  - ohmic_resistance
  - gate_length
  - rf_probe_result
  - dc_probe_result
  - wafer_sort_bin
  - reliability_sample_id
  - die_grade
```

---

# 7. B07 — 반도체 조립·패키징

```yaml
subindustry_code: B07
legacy_slug: assembly_packaging
label_ko: 반도체 조립·패키징
label_zh: 半导体组装·封装
label_en: ""
label_ja: ""
routing: RT_BATCH
preset_id: packaging_linear_v1
expression_tier: P3_PFLOW_PACKAGING_LINEAR
routing_description_ko: >
  패키징은 Wafer를 기능 제품으로 전환하는 후공정이며 Backgrind, Dicing, Die Attach, Bonding/Flip Chip, Mold, Mark, Singulation, Final Test가 중심이다. Fab FEOL 용어는 사용하지 않는다. 2026년 기준 CoWoS, HBM Stack, Chiplet Heterogeneous Integration의 수요 폭발로 첨단 패키징 자동화가 가속화되고 있으며, SCARA 로봇·머신 비전·엣지 AI가 각 공정에 통합되어 Lights-out 팹을 목표로 하고 있다.
routing_description_zh: >
  封装是把Wafer转换为功能产品的后工序，核心包括Backgrind、Dicing、Die Attach、Bonding/Flip Chip、Mold、Mark、Singulation和Final Test。不使用Fab FEOL术语。2026年CoWoS、HBM Stack、Chiplet异构集成需求爆发驱动先进封装自动化加速，SCARA机器人、机器视觉、边缘AI集成到各工序，目标实现Lights-out工厂。
```

## 7.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Wafer Receive / Map Import | Wafer Map(KGD Map, Wafer Sort Bin Map, Fab Yield Data), KGD(Known Good Die 정보), 고객 Lot, Package 사양(FC-BGA / WLCSP / SiP / CoWoS / HBM Stack)을 수신한다. MES에서 Wafer Map 파일(STDF / XML / Binary Format)을 수신·해석하여 Die Grade와 Defect Map 정보를 Package Lot DB에 로딩한다. ECC 검증으로 데이터 무결성을 확인하며, 수신 완료 시 Package Lot ID를 생성한다. |
| 2 | Backgrind / Wafer Mount | Wafer를 목표 두께로 연삭(DISCO DFG8541 / Tokyo Seimitsu, Si Backgrind 50~100μm, SiC 100~200μm, Thickness Uniformity ±2μm)하고 Tape Mount 상태(UV Release Tape / Dicing Tape, Adhesion Force, Tape Tension, Void <0.5%)를 관리한다. Inline Thickness Gauge(DISCO / Keyence)로 전 영역 측정하며, 보호 Tape Lamination 공정에서 Particle Contamination을 방지한다. |
| 3 | Dicing / Saw | Saw Program(Blade 타입: Hub Blade / Hubless, Diamond Grit Size), Blade 상태(Blade Condition, Dressing, Kerf Width), Chipping(Backside Chipping <5μm, Frontside Chipping <2μm), Die ID와 Dicing Map을 생성한다. DISCO DAD6361 / DFG3641 Dicing Saw로 절단하며, Die Shear Strength로 Dicing Quality를 샘플링 검증한다. Stealth Dicing(레이저 내부 개질) 공정도 최근 Thin Die(<50μm)에서 사용된다. |
| 4 | Die Attach / Flip Chip Attach | Die를 Leadframe(SOIC / QFP / TO), Substrate(FC-BGA / Si Interposer), Interposer(Silicon Interposer, CoWoS 구조)에 부착하고 BLT(Bond Line Thickness, 10~50μm, ±5μm), Void(Void Area <2% per Die, X-ray 검증), Placement(Placement 정밀도 ±5~15μm, Die Tilt <1°)를 관리한다. Die Bonder(ASM AD838, BESI ESEC2009, Yamaha YRP)와 Flip Chip Bonder(ASM / BESI, Flux Dipping, Reflow Soldering)가 사용된다. Die Attach Material(Epoxy / Solder Paste / DAF)의 Lot 번호와 Cure Profile(150~200℃ / Reflow Profile)을 추적한다. |
| 5 | Wire Bond / Interconnect | Wire Bond(Au Wire 0.8~1.5mil, Cu Wire 1.0~2.0mil, Loop Height 100~300μm), Ribbon Bond(Power Package용 Al Ribbon, 두께 50~500μm), Flip Chip Reflow(Thermal Compression Bonding TCB / Mass Reflow, Bump Shear Strength >50g/bump) 등 Interconnect 조건을 관리한다. Wire Bonder(K&S ICON Pro, Shinkawa UTC-5000, Wire Pull/Ball Shear Strength는 Lot당 SPC 샘플링)로 Bond Program ID와 Wire Lot 번호를 추적한다. |
| 6 | Molding / Encapsulation | Mold Compound Lot(EMC, Epoxy Molding Compound / Liquid Molding, Filler Size 10~75μm), Transfer Mold 조건(Mold Temp 175±5℃, Transfer Pressure 30~100kgf/cm², Cure Time 60~180s), Cure(Post Mold Cure 175℃, 4~8h), Void(Void Detection X-ray / SAT, Void <1% area), Delamination(SAM, C-SAM 결함 <5%), Package Warpage(Warpage <50μm, Shadow Moire / Laser Profiler)를 관리한다. TOWA / Yamada / ASM Molding Press 장비 사용, Mold Die ID 추적. |
| 7 | Marking / Singulation | Laser Mark(Laser Type: Fiber / CO₂, Mark Depth <10μm, Legibility OCR Grade A), Trace Code(2D Data Matrix / QR Code, Lot·Wafer·Die 정보 포함), Trim/Form(Lead Forming, Dam Bar Cutting, Burr <30μm), Singulation(Saw / Router / Punch, Package Saw Kerf Loss <100μm)과 외관(Vision Inspection, Package Package Crack, Burr, Contamination)을 관리한다. Mark Reader(Cognex / Keyence)로 Code Readability를 실시간 검증한다. |
| 8 | Inspection Gate — AOI/X-ray/Warpage | AOI(Automated Optical Inspection, Viscom / Omron / Koh Young, 3D Solder Inspection, Component Presence, Alignment), X-ray(Nordson / Phoenix, Bump Void, Solder Joint, Wire Loop, Die Shift, Resolution <5μm), Warpage(Shadow Moire / Laser Triangulation, Warpage <50μm at RT, <100μm at Reflow Temp 260℃), SAM(Scanning Acoustic Microscopy, Delamination, Void, Crack, C-SAM Mode) 등 검사 결과를 Gate로 판정한다. Gate Fail 시 Auto Hold → Inspect 이미지 분석 → 공정 조건(X-ray Void → Reflow Profile / Mold Pressure) 조정 → 재검사. |
| 9 | Final Test / Burn-in | Final Test(ATE, Advantest T5503 / Teradyne J750, Open/Short, Functional Test, Speed / Power Test, Parametric Test), Burn-in(Burn-in Chamber, 85~125℃, Dynamic Bias, 24~168h, Voltage/Current Stress), Bin(Hot/Hot Retention / Cold Bin, Hard Bin / Soft Bin), Open/Short, Functional 결과를 확정한다. Handler(Delta Design / Advantest / Seiko Epson, Tri-temp -40~150℃)가 Package를 Tester Interface에 자동 이송하며, Burn-in Board(BIB)의 Socket Contact 이력을 추적한다. |
| 10 | Packing / Shipment | Reel(Tape & Reel, Qty per Reel, EIA-481 표준), Tray(JEDEC Tray / Matrix Tray, Qty per Tray), Label(고객 Label 포맷, Serial, Lot Info 포함, Barcode / RFID), 고객 Lot 기준, CoC(Certificate of Conformance), Packing Slip과 출하 이력(ASN Advance Ship Notice, EDI / Web Portal 전송)을 확정한다. Packing Vision System으로 Reel/Tray 내 Package 수량·방향·Mark 적합성을 자동 검증한다. |

## 7.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Wafer Receive / Map Import | 接收Wafer Map(KGD Map、Wafer Sort Bin Map、Fab Yield Data)、KGD(Known Good Die信息)、客户Lot、Package规格(FC-BGA/WLCSP/SiP/CoWoS/HBM Stack)。MES接收解析Wafer Map文件(STDF/XML/Binary Format)，将Die Grade和Defect Map信息加载至Package Lot DB。ECC验证数据完整性，接收完成时生成Package Lot ID。 |
| 2 | Backgrind / Wafer Mount | 将Wafer研磨到目标厚度(DISCO DFG8541/Tokyo Seimitsu、Si Backgrind 50~100μm、SiC 100~200μm、Thickness Uniformity±2μm)并管理Tape Mount状态(UV Release Tape/Dicing Tape、Adhesion Force、Tape Tension、Void<0.5%)。Inline Thickness Gauge(DISCO/Keyence)全区域测量，保护Tape Lamination工序防止Particle污染。 |
| 3 | Dicing / Saw | 生成Saw Program(Blade类型：Hub Blade/Hubless、Diamond Grit Size)、Blade状态(Blade Condition、Dressing、Kerf Width)、Chipping(Backside Chipping<5μm、Frontside Chipping<2μm)、Die ID和Dicing Map。用DISCO DAD6361/DFG3641 Dicing Saw切割，Die Shear Strength抽样验证Dicing Quality。Stealth Dicing(激光内部改性)工艺也用于薄Die(<50μm)。 |
| 4 | Die Attach / Flip Chip Attach | 把Die贴装到Leadframe(SOIC/QFP/TO)、Substrate(FC-BGA/Si Interposer)、Interposer(Silicon Interposer、CoWoS结构)并管理BLT(Bond Line Thickness，10~50μm，±5μm)、Void(Void Area<2% per Die，X-ray验证)、Placement(Placement精度±5~15μm、Die Tilt<1°)。使用Die Bonder(ASM AD838、BESI ESEC2009、Yamaha YRP)和Flip Chip Bonder(ASM/BESI、Flux Dipping、Reflow Soldering)。追踪Die Attach Material(Epoxy/Solder Paste/DAF)的Lot编号和Cure Profile(150~200℃/Reflow Profile)。 |
| 5 | Wire Bond / Interconnect | 管理Wire Bond(Au Wire 0.8~1.5mil、Cu Wire 1.0~2.0mil、Loop Height 100~300μm)、Ribbon Bond(Power Package用Al Ribbon、厚度50~500μm)、Flip Chip Reflow(Thermal Compression Bonding TCB/Mass Reflow、Bump Shear Strength>50g/bump)等互连条件。Wire Bonder(K&S ICON Pro、Shinkawa UTC-5000，Wire Pull/Ball Shear Strength按Lot SPC抽样)追踪Bond Program ID和Wire Lot编号。 |
| 6 | Molding / Encapsulation | 管理Mold Compound Lot(EMC、Epoxy Molding Compound/Liquid Molding、Filler Size 10~75μm)、Transfer Mold条件(Mold Temp 175±5℃、Transfer Pressure 30~100kgf/cm²、Cure Time 60~180s)、Cure(Post Mold Cure 175℃、4~8h)、Void(Void Detection X-ray/SAT、Void<1% area)、Delamination(SAM、C-SAM缺陷<5%)、Package Warpage(Warpage<50μm、Shadow Moire/Laser Profiler)。使用TOWA/Yamada/ASM Molding Press设备，追踪Mold Die ID。 |
| 7 | Marking / Singulation | 管理Laser Mark(Laser Type：Fiber/CO₂、Mark Depth<10μm、Legibility OCR Grade A)、Trace Code(2D Data Matrix/QR Code、含Lot/Wafer/Die信息)、Trim/Form(Lead Forming、Dam Bar Cutting、Burr<30μm)、Singulation(Saw/Router/Punch、Package Saw Kerf Loss<100μm)和外观(Vision Inspection、Package Crack、Burr、Contamination)。Mark Reader(Cognex/Keyence)实时验证Code Readability。 |
| 8 | Inspection Gate — AOI/X-ray/Warpage | 以AOI(Automated Optical Inspection、Viscom/Omron/Koh Young、3D Solder Inspection、Component Presence、Alignment)、X-ray(Nordson/Phoenix、Bump Void、Solder Joint、Wire Loop、Die Shift、Resolution<5μm)、Warpage(Shadow Moire/Laser Triangulation、Warpage<50μm at RT、<100μm at Reflow Temp 260℃)、SAM(Scanning Acoustic Microscopy、Delamination、Void、Crack、C-SAM Mode)等检查结果作为Gate判定。Gate Fail时Auto Hold→Inspect图像分析→工艺条件(X-ray Void→Reflow Profile/Mold Pressure)调整→重新检查。 |
| 9 | Final Test / Burn-in | 执行Final Test(ATE、Advantest T5503/Teradyne J750、Open/Short、Functional Test、Speed/Power Test、Parametric Test)、Burn-in(Burn-in Chamber、85~125℃、Dynamic Bias、24~168h、Voltage/Current Stress)、Bin(Hot/Hot Retention/Cold Bin、Hard Bin/Soft Bin)、Open/Short、Functional结果。Handler(Delta Design/Advantest/Seiko Epson、Tri-temp -40~150℃)自动将Package运至Tester Interface，追踪Burn-in Board(BIB)的Socket Contact履历。 |
| 10 | Packing / Shipment | 确定Reel(Tape&Reel、Qty per Reel、EIA-481标准)、Tray(JEDEC Tray/Matrix Tray、Qty per Tray)、Label(客户Label格式、含Serial、Lot Info、Barcode/RFID)、客户Lot基准、CoC(Certificate of Conformance)、Packing Slip和出货履历(ASN Advance Ship Notice、EDI/Web Portal传输)。Packing Vision System自动验证Reel/Tray内Package数量/方向/Mark适配性。 |

## 7.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Die Genealogy | Wafer Map, Die ID, Package Lot를 출하 단위까지 연결해야 한다. 측정 방법: MES + Package DB 통합, Laser Mark + Barcode Reader 조회. 관리 주기: Real-time(공정 단계 완료 시마다). 이상 시 조치: Genealogy 불일치 → Lot Hold → Data Reconciliation → 수동 수정 또는 Scrap. | 1,3,4,10 | process_step | Die Genealogy |
| 2 | Package 소재 Lot 추적 | Substrate, Leadframe, Wire, Bump, Mold Compound Lot를 Package Lot와 연결해야 한다. 측정 방법: MES Material Lot Tracking, Barcode Scan at 각 공정. 관리 주기: 소재 투입 시점마다(Every Lot Transition). 이상 시 조치: Material Lot 누락 / 불일치 → 해당 Package Lot Hold → 창고 재고 확인 → 소재 Lot 재할당. | 4,5,6 | process_step | Material Trace |
| 3 | X-ray/Warpage Gate | Bond, Mold 이후 X-ray, Warpage, Void 결과를 Gate로 판정해야 한다. 측정 장비/방법: X-ray(Nordson DAGE / Phoenix, 2D/3D CT), SAM(Hitachi / Sonix C-SAM), Shadow Moire(Akamai / Insidix), Laser Profiler(Keyence). 관리 주기: Lot당 샘플링(5~25ea/Lot). 이상 시 조치: X-ray Void >2% / SAM Delamination >5% / Warpage >Spec → Auto Hold → 공정 조건 조정(Reflow Profile / Mold Temp/Pressure) → 재검사. | 8 | process_step | Inspection Gate |
| 4 | Final Test Bin 관리 | Final Test Bin과 Package Grade를 고객 Lot 단위로 확정해야 한다. 측정 장비: Advantest T5503 / Teradyne J750 ATE + Handler(Delta Design / Advantest). 관리 주기: Die 단위(Every Die). 이상 시 조치: Bin Fail > Threshold → Tester / Socket / Contact 검증 → GRR( Gage R&R) 분석 → 공정 조건 수정. | 9,10 | process_step | Final Test |

## 7.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Die Genealogy | 需把Wafer Map、Die ID、Package Lot连接到出货单位。测量方法：MES+Package DB集成、Laser Mark+Barcode Reader查询。管理周期：Real-time(工序步骤完成时)。异常处理：Genealogy不一致→Lot Hold→Data Reconciliation→手动修正或Scrap。 | 1,3,4,10 | process_step | Die Genealogy |
| 2 | Package材料Lot追踪 | 需把Substrate、Leadframe、Wire、Bump、Mold Compound Lot连接到Package Lot。测量方法：MES Material Lot Tracking、各工序Barcode扫描。管理周期：材料投入时(Every Lot Transition)。异常处理：Material Lot缺失/不一致→该Package Lot Hold→仓库库存确认→Material Lot重新分配。 | 4,5,6 | process_step | Material Trace |
| 3 | X-ray/Warpage Gate | Bond、Mold后需以X-ray、Warpage、Void结果作为Gate判定。测量设备/方法：X-ray(Nordson DAGE/Phoenix、2D/3D CT)、SAM(Hitachi/Sonix C-SAM)、Shadow Moire(Akamai/Insidix)、Laser Profiler(Keyence)。管理周期：每Lot抽样(5~25ea/Lot)。异常处理：X-ray Void>2%/SAM Delamination>5%/Warpage>Spec→Auto Hold→工艺条件调整(Reflow Profile/Mold Temp/Pressure)→重新检查。 | 8 | process_step | Inspection Gate |
| 4 | Final Test Bin管理 | 需按客户Lot确定Final Test Bin和Package Grade。测量设备：Advantest T5503/Teradyne J750 ATE+Handler(Delta Design/Advantest)。管理周期：每Die(Every Die)。异常处理：Bin Fail>Threshold→Tester/Socket/Contact验证→GRR分析→工艺条件修正。 | 9,10 | process_step | Final Test |

## 7.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Receive | process |  |  | lot_id, wafer_id, customer_lot |
| 2 | Die Prep | batch |  |  | wafer_id, die_id, dicing_map |
| 3 | Die Prep | batch |  |  | dicing_map, die_id |
| 4 | Attach | batch |  |  | die_id, substrate_lot, leadframe_lot, die_attach_material_lot |
| 5 | Interconnect | batch |  |  | bond_program_id, wire_lot, bump_lot, die_id |
| 6 | Mold | batch |  |  | mold_compound_lot, warpage_result, package_lot |
| 7 | Mark / Singulation | process |  |  | mark_code, package_lot |
| 8 | Inspection | gate |  | 4,5,6,7 | xray_result, warpage_result, mark_code, package_lot |
| 9 | Final Test | process |  |  | final_test_bin, package_grade, package_lot |
| 10 | Shipment | process |  |  | customer_lot, package_grade, mark_code |

## 7.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Receive | process |  |  | lot_id, wafer_id, customer_lot |
| 2 | Die Prep | batch |  |  | wafer_id, die_id, dicing_map |
| 3 | Die Prep | batch |  |  | dicing_map, die_id |
| 4 | Attach | batch |  |  | die_id, substrate_lot, leadframe_lot, die_attach_material_lot |
| 5 | Interconnect | batch |  |  | bond_program_id, wire_lot, bump_lot, die_id |
| 6 | Mold | batch |  |  | mold_compound_lot, warpage_result, package_lot |
| 7 | Mark / Singulation | process |  |  | mark_code, package_lot |
| 8 | Inspection | gate |  | 4,5,6,7 | xray_result, warpage_result, mark_code, package_lot |
| 9 | Final Test | process |  |  | final_test_bin, package_grade, package_lot |
| 10 | Shipment | process |  |  | customer_lot, package_grade, mark_code |

## 7.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 7.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 7.9 data_capture_points

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - die_id
  - package_lot
  - substrate_lot
  - leadframe_lot
  - dicing_map
  - die_attach_material_lot
  - bond_program_id
  - wire_lot
  - bump_lot
  - mold_compound_lot
  - xray_result
  - warpage_result
  - mark_code
  - final_test_bin
  - package_grade
  - customer_lot
```

---

# 8. B08 — 반도체 테스트 서비스

```yaml
subindustry_code: B08
legacy_slug: test
label_ko: 반도체 테스트 서비스
label_zh: 半导体测试服务
label_en: ""
label_ja: ""
routing: RT_BATCH
preset_id: test_service_v1
expression_tier: P3_PFLOW_TEST_SERVICE
routing_description_ko: >
  테스트 서비스는 고객 Program, Tester/Handler/Probe Card, STDF, Bin, Retest, Data Security가 중심이다. 제조공정보다 Test Program Revision과 장비·Socket·Probe 이력 관리가 중요하다. 2026년 기준 CIM 2.0 개념이 등장하여 AI 대형 언어 모델과 에이전트 기술이 CIM에 통합되어 데이터 사일로 해소와 통합 로그 분석이 가능해졌으며, 고객 데이터 보안 및 접근 제어가 더욱 강화되고 있다.
routing_description_zh: >
  测试服务以客户Program、Tester/Handler/Probe Card、STDF、Bin、Retest和数据安全为核心。相比制造工序，更重视Test Program版本和设备/Socket/Probe履历管理。2026年CIM 2.0概念兴起，AI大语言模型和智能体技术集成到CIM中，实现了数据孤岛消除和统一日志分析，客户数据安全及访问控制持续加强。
```

## 8.1 process_steps_detail_ko

| # | step | note |
|---:|---|---|
| 1 | Customer Lot Receive | 고객 Lot ID, Wafer/Package 수량(6"/8"/12" Wafer 또는 Tray/Reel Package), Test Spec(고객 Test Specification, Limit 조건, 전압/전류/온도 조건), Program Revision(테스트 프로그램 버전 관리), 보안권한(Access Group, 고객별 격리)을 수신한다. MES에서 고객 Lot를 시스템에 등록하고 Wafer ID / Package ID 바코드 스캔으로 입고 검사를 수행하며, Lot 단위 Customer Serial Number를 생성한다. |
| 2 | Test Program / Setup Review | Test Program(Revision, Source Code Version Control, Git / Perforce 기반 관리), Test Limit(Bin Limit, Parametric Limit, Guard Band), Bin Table(Bin Description, Hard/Soft Bin 매핑, Retest 조건), Loadboard(DUT Board, PCB Layer Stack, Signal Integrity), Socket(Test Socket, Contact Pin, Spring Pin Force, Contact Resistance <10mΩ), Probe Card(Probe Needle, Membrane / Vertical, Over Travel, Cleaning Cycle) 조건을 확인한다. Program Revision은 고객 승인 후 System Lock되며, 변경 시 ECR(Engineering Change Request) 프로세스를 거친다. |
| 3 | Equipment Assignment | Tester(Advantest 93K / V93000, Teradyne Ultraflex / J750, Tester Head, Pin Electronics), Handler(Delta Design / Advantest / MultiTest, Tri-temp -55~175℃, Index Time <1s), Prober(Tokyo Electron TEL / Cascade, Wafer Chuck Temp -55~175℃, Wafer Prober Alignment <5μm), Temperature 조건(Room / Hot / Cold, ±0.5℃ 정밀도)과 장비 상태(PM Schedule, Calibration Status, Last Preventive Maintenance Date)를 배정한다. 장비 이력 관리 시스템에서 Tester·Handler·Prober의 가용 상태를 실시간 조회하여 할당한다. |
| 4 | Setup / Correlation Run | Golden Unit(Golden Device / Reference Sample, 고객 제공 또는 사내 선정, Traceability 확보), Correlation(Chamber-to-Chamber, Tester-to-Tester, Handler-to-Handler Variance, Spec 대비 Delta <5%), GRR(Gage Repeatability & Reproducibility, Gauge R&R <10%, KPI), Limit Check(Limit Validation, Bin Verification, Stress Test)와 Setup 승인(Engineering Approval / QA Approval)을 수행한다. Correlation Report는 고객 포털에 업로드되며 승인 완료 시 Test Execution Ready 플래그가 설정된다. |
| 5 | Wafer Probe / Package Test | Wafer Probe(TEL Prober + Advantest / Teradyne Tester, Probe Card Contact, Step & Repeat, Touchdown Accuracy) 또는 Package Final Test(Handler + Tester, Tri-temp, Contact Check, Continuity Test)를 실행하고 Raw Data(STDF Standard Test Data Format, Binary Log, 각 Die/Package 단위 결과)를 수집한다. 테스트 중 Fail 발생 시 Immediate Retest(Immediate Retry 1~3회) 정책을 적용하며, 모든 Raw Test Data는 STDF 파일로 Tester HDD → MES 서버로 자동 전송된다. |
| 6 | Bin Classification | Hard Bin(Functional Fail, 특정 Test Item Fail, Scrap 또는 Downgrade), Soft Bin(Parametric Limit Margin, Retest 가능, Sort 결과에 따른 Temp Bin), Fail Code(FAIL의 원인이 되는 Test Item Code, Classification Code), Parametric 결과(Vt, Idsat, Leakage 등 Bin 결정 요소)를 분류한다. Bin Classification Logic은 고객 Bin Table 기준으로 MES에서 자동 처리되며, Bin Yield Summary는 YMS로 실시간 전송된다. |
| 7 | Retest / Hold Gate | Retest 조건(First Fail Site만 Retest / 전체 Retest, Retest Limit 회수 설정, Low Yield Threshold <70%), Low Yield(Threshold 기반 Lot Hold, 고객 통보 필요성), 이상 Bin(Unknown Bin, Guard Band Fail, Non-visual Fail), 장비 이상(Tester Error Log, Handler Jam, Probe Mark Abnormal, Over-current Alarm)을 Gate로 판정한다. Gate Fail 시 Lot Auto Hold → Equipment Engineer / Test Engineer 검토 → 고객 승인 Retest 또는 Scrap. |
| 8 | STDF / Data Review | STDF File(Single STDF / Merged STDF, 파일 크기 관리, ECC 검증), Summary(Yield %, Bin Distribution Map, Parametric Distribution 자동 생성), Yield(Yield by Lot / Wafer / Tester별 분석, Yield Trend Chart), Tester Log(Tester Alarm, Setup Change Log, Recipe Change History, Error Code), Alarm(Fail Action, Equipment Alarm, Test Time Outlier)을 검토한다. EDA SW(Exensio / PDF Solutions DataPower / YieldInsights)로 STDF를 자동 파싱하여 Dashboard 가시화하며, 고객 Data Portal을 통해 실시간 조회할 수 있다. |
| 9 | Customer Report / CoA | 고객 포맷 Report(Custom Report Format, 고객별 Header/Footer, 필드 매핑), CoA(Certificate of Analysis / Certificate of Conformance, 규제 충족 (RoHS / REACH 등)), Wafer Map(Bin Map, Parametric Map, Pass/Fail Map) 또는 Lot Summary(Lot Yield, Bin %, Shipment 정보)를 생성한다. Report는 고객 포털(Web UI / SFTP / EDI)에 자동 게시되며, PDF / CSV / XML 3가지 포맷을 지원한다. |
| 10 | Packing / Data Delivery | 출하 Lot(Reel / Tray / Wafer Box, Quantity), Label(고객 Label Format, Lot / Serial / Date Code, 2D Data Matrix / Barcode), 전자파일(STDF + Report + Wafer Map, FTP / SFTP / 클라우드 전송), 접근권한(Access Group, Data Encryption, 고객별 격리 스토리지)과 데이터 전달 상태(Delivery Confirmation, 다운로드 완료 추적)를 확정한다. |

## 8.2 process_steps_detail_zh

| # | step | note |
|---:|---|---|
| 1 | Customer Lot Receive | 接收客户Lot ID、Wafer/Package数量(6"/8"/12" Wafer或Tray/Reel Package)、Test Spec(客户Test Specification、Limit条件、电压/电流/温度条件)、Program Revision(测试程序版本管理)、安全权限(Access Group、客户隔离)。MES将客户Lot注册至系统，通过Wafer ID/Package ID Barcode扫描执行入库检查，按Lot生成Customer Serial Number。 |
| 2 | Test Program / Setup Review | 确认Test Program(Revision、Source Code版本控制、Git/Perforce管理)、Test Limit(Bin Limit、Parametric Limit、Guard Band)、Bin Table(Bin Description、Hard/Soft Bin映射、Retest条件)、Loadboard(DUT Board、PCB Layer Stack、Signal Integrity)、Socket(Test Socket、Contact Pin、Spring Pin Force、Contact Resistance<10mΩ)、Probe Card(Probe Needle、Membrane/Vertical、Over Travel、Cleaning Cycle)条件。Program Revision经客户批准后System Lock，变更需ECR(Engineering Change Request)流程。 |
| 3 | Equipment Assignment | 分配Tester(Advantest 93K/V93000、Teradyne Ultraflex/J750、Tester Head、Pin Electronics)、Handler(Delta Design/Advantest/MultiTest、Tri-temp -55~175℃、Index Time<1s)、Prober(Tokyo Electron TEL/Cascade、Wafer Chuck Temp -55~175℃、Wafer Prober Alignment<5μm)、Temperature条件(Room/Hot/Cold、±0.5℃精度)和设备状态(PM Schedule、Calibration Status、Last Preventive Maintenance Date)。设备履历管理系统实时查询Tester/Handler/Prober的可用状态进行分配。 |
| 4 | Setup / Correlation Run | 执行Golden Unit(Golden Device/Reference Sample、客户提供或内部选定、确保Traceability)、Correlation(Chamber-to-Chamber、Tester-to-Tester、Handler-to-Handler Variance、Spec对比Delta<5%)、GRR(Gage Repeatability&Reproducibility、Gauge R&R<10%、KPI)、Limit Check(Limit Validation、Bin Verification、Stress Test)和Setup批准(Engineering Approval/QA Approval)。Correlation Report上传客户Portal，批准完成时设置Test Execution Ready标志。 |
| 5 | Wafer Probe / Package Test | 执行Wafer Probe(TEL Prober+Advantest/Teradyne Tester、Probe Card Contact、Step&Repeat、Touchdown Accuracy)或Package Final Test(Handler+Tester、Tri-temp、Contact Check、Continuity Test)并采集Raw Data(STDF Standard Test Data Format、Binary Log、各Die/Package级结果)。测试中Fail发生时应用Immediate Retest(Immediate Retry 1~3次)策略，所有Raw Test Data按STDF文件从Tester HDD自动发送至MES服务器。 |
| 6 | Bin Classification | 分类Hard Bin(Functional Fail、特定Test Item Fail、Scrap或Downgrade)、Soft Bin(Parametric Limit Margin、可Retest、Sort结果按Temp Bin)、Fail Code(FAIL原因为Test Item Code、Classification Code)、Parametric结果(Vt、Idsat、Leakage等Bin决定因素)。Bin Classification Logic按客户Bin Table在MES自动处理，Bin Yield Summary实时发送YMS。 |
| 7 | Retest / Hold Gate | 以Retest条件(仅First Fail Site Retest/全Retest、Retest Limit次数设定、Low Yield Threshold<70%)、Low Yield(Threshold基Lot Hold、客户通知必要性)、异常Bin(Unknown Bin、Guard Band Fail、Non-visual Fail)、设备异常(Tester Error Log、Handler Jam、Probe Mark Abnormal、Over-current Alarm)作为Gate判定。Gate Fail时Lot Auto Hold→Equipment Engineer/Test Engineer审核→客户批准Retest或Scrap。 |
| 8 | STDF / Data Review | 复核STDF File(单STDF/Merged STDF、文件大小管理、ECC验证)、Summary(Yield%、Bin Distribution Map、Parametric Distribution自动生成)、Yield(按Lot/Wafer/Tester Yield分析、Yield Trend Chart)、Tester Log(Tester Alarm、Setup Change Log、Recipe Change History、Error Code)、Alarm(Fail Action、Equipment Alarm、Test Time Outlier)。EDA SW(Exensio/PDF Solutions DataPower/YieldInsights)自动解析STDF实现Dashboard可视化，可通过客户Data Portal实时查询。 |
| 9 | Customer Report / CoA | 生成客户格式Report(Custom Report Format、客户Header/Footer、字段映射)、CoA(Certificate of Analysis/Certificate of Conformance、法规符合性RoHS/REACH等)、Wafer Map(Bin Map、Parametric Map、Pass/Fail Map)或Lot Summary(Lot Yield、Bin%、Shipment信息)。Report自动发布至客户Portal(Web UI/SFTP/EDI)，支持PDF/CSV/XML三种格式。 |
| 10 | Packing / Data Delivery | 确认出货Lot(Reel/Tray/Wafer Box、Quantity)、Label(客户Label格式、Lot/Serial/Date Code、2D Data Matrix/Barcode)、电子文件(STDF+Report+Wafer Map、FTP/SFTP/云传输)、访问权限(Access Group、Data Encryption、客户隔离存储)和数据交付状态(Delivery Confirmation、下载完成追踪)。 |

## 8.3 control_points_detail_ko

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Program Revision Lock | 고객 Test Program과 Limit, Bin Table Revision을 실행 전 Lock해야 한다. 측정 방법: MES + Version Control System(Git / Perforce) 자동 비교, Revision Hash 검증. 관리 주기: Test Setup 시(Every Setup). 이상 시 조치: Program Revision 불일치 → Setup Hold → 고객 승인 재획득 → 변경 내역 Audit Trail 기록. | 2,4 | process_step | Program Control |
| 2 | Tester·Socket·Probe 이력 | Tester, Handler, Prober, Probe Card, Socket, Loadboard 이력을 Test 결과와 연결해야 한다. 측정 장비/방법: MES Equipment Tracking, Contact Resistance 측정, Probe Mark Inspection(Cyclical). 관리 주기: 장비 사용 시마다(Every Touchdown / Every Insertion). 이상 시 조치: Socket Contact Resistance >Spec / Probe Mark Abnormal → Socket/Probe Card 교체 → 재Correlation. | 3,5,8 | process_step | Equipment Trace |
| 3 | Retest/Hold Gate | Retest와 Low Yield 조건은 고객 승인 및 Hold 기준과 연결해야 한다. 측정 방법: MES Retest Logic 자동 판정, Yield Threshold 기반 Hold Flag. 관리 주기: Test Batch 종료 시(Every Lot). 이상 시 조치: Low Yield(Spec 대비 <70%) → Auto Hold → Test Engineer 분석 → 고객 승인 Retest Plan 수립. | 7 | process_step | Retest / Hold Gate |
| 4 | STDF 데이터 관리 | STDF 파일, Summary, Yield, Bin Code를 고객 Report와 연결해야 한다. 측정 방법: EDA SW(Exensio / PDF Solutions) 자동 Parsing, STDF Signature 검증. 관리 주기: Test 종료 시(Every Lot). 이상 시 조치: STDF Parse Error / File 손상 → Tester Log 확인 → 재전송 요청 → 고객 Data 재전달. | 5,8,9 | process_step | STDF Data |
| 5 | 고객별 접근권한 | 고객별 Test Program, STDF, Yield Data 접근권한을 분리해야 한다. 측정 방법: IAM Audit Log, File System Permission Check. 관리 주기: 정기적(월/분기 Audit). 이상 시 조치: 무단 접근 감지 → 접근 차단 + 보안 사고 보고 → 접근 권한 재설정. |  | industry | Customer Data Security |

## 8.4 control_points_detail_zh

| # | text | detail | step_refs | scope | category |
|---:|---|---|---|---|---|
| 1 | Program Revision锁定 | 客户Test Program、Limit、Bin Table版本需在执行前锁定。测量方法：MES+Version Control System(Git/Perforce)自动比对、Revision Hash验证。管理周期：Test Setup时(Every Setup)。异常处理：Program Revision不一致→Setup Hold→客户批准重新获取→变更内容记录Audit Trail。 | 2,4 | process_step | Program Control |
| 2 | Tester/Socket/Probe履历 | 需把Tester、Handler、Prober、Probe Card、Socket、Loadboard履历与测试结果连接。测量设备/方法：MES Equipment Tracking、Contact Resistance测量、Probe Mark Inspection(Cyclical)。管理周期：设备使用每次(Every Touchdown/Every Insertion)。异常处理：Socket Contact Resistance>Spec/Probe Mark Abnormal→Socket/Probe Card更换→重新Correlation。 | 3,5,8 | process_step | Equipment Trace |
| 3 | Retest/Hold Gate | Retest和Low Yield条件需连接客户批准和Hold标准。测量方法：MES Retest Logic自动判定、Yield Threshold基Hold Flag。管理周期：Test Batch结束时(Every Lot)。异常处理：Low Yield(Spec对比<70%)→Auto Hold→Test Engineer分析→客户批准Retest Plan制定。 | 7 | process_step | Retest / Hold Gate |
| 4 | STDF数据管理 | 需把STDF文件、Summary、Yield、Bin Code连接到客户Report。测量方法：EDA SW(Exensio/PDF Solutions)自动解析、STDF Signature验证。管理周期：Test结束时(Every Lot)。异常处理：STDF Parse Error/文件损坏→Tester Log确认→重新传输请求→客户Data重新发送。 | 5,8,9 | process_step | STDF Data |
| 5 | 客户访问权限 | 需按客户隔离Test Program、STDF和Yield Data访问权限。测量方法：IAM Audit Log、File System Permission Check。管理周期：定期(月/季度审计)。异常处理：检测到未授权访问→阻断访问+安全事件报告→访问权限重置。 |  | industry | Customer Data Security |

## 8.5 step_expression_ko

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Receive | process |  |  | customer_lot, lot_id, wafer_id, device_id, access_group |
| 2 | Program | process |  |  | test_program_id, program_rev, loadboard_id, socket_id, probe_card_id |
| 3 | Equipment | process |  |  | tester_id, handler_id, prober_id, temperature_condition |
| 4 | Setup | process |  |  | test_program_id, program_rev, tester_id, socket_id |
| 5 | Test | batch |  |  | tester_id, handler_id, prober_id, stdf_file, bin_code |
| 6 | Bin | process |  |  | bin_code, yield_result, stdf_file |
| 7 | Hold Gate | gate |  | 5,6 | retest_flag, yield_result, hold_code, bin_code |
| 8 | Data Review | process |  |  | stdf_file, yield_result, tester_id |
| 9 | Report | process |  |  | stdf_file, access_group, shipment_lot |
| 10 | Delivery | process |  |  | shipment_lot, access_group, customer_lot |

## 8.6 step_expression_zh

| # | module | role | loop_hint | gate_for | trace_keys |
|---:|---|---|---|---|---|
| 1 | Receive | process |  |  | customer_lot, lot_id, wafer_id, device_id, access_group |
| 2 | Program | process |  |  | test_program_id, program_rev, loadboard_id, socket_id, probe_card_id |
| 3 | Equipment | process |  |  | tester_id, handler_id, prober_id, temperature_condition |
| 4 | Setup | process |  |  | test_program_id, program_rev, tester_id, socket_id |
| 5 | Test | batch |  |  | tester_id, handler_id, prober_id, stdf_file, bin_code |
| 6 | Bin | process |  |  | bin_code, yield_result, stdf_file |
| 7 | Hold Gate | gate |  | 5,6 | retest_flag, yield_result, hold_code, bin_code |
| 8 | Data Review | process |  |  | stdf_file, yield_result, tester_id |
| 9 | Report | process |  |  | stdf_file, access_group, shipment_lot |
| 10 | Delivery | process |  |  | shipment_lot, access_group, customer_lot |

## 8.7 operations_ko

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 8.8 operations_zh

| step_ref | seq | name |
|---:|---:|---|
|  |  |  |

## 8.9 data_capture_points

```yaml
data_capture_points:
  - customer_lot
  - lot_id
  - wafer_id
  - device_id
  - test_program_id
  - program_rev
  - tester_id
  - handler_id
  - prober_id
  - probe_card_id
  - socket_id
  - loadboard_id
  - temperature_condition
  - stdf_file
  - bin_code
  - retest_flag
  - yield_result
  - hold_code
  - access_group
  - shipment_lot
```

---

# 9. v0.3 self-check

```text
[x] B01~B08 전수, slug당 §N.1~§N.9 섹션 완비
[x] §0 오기 수정: control_points_ko/zh는 R2 자동생성임을 명시
[x] control_points_detail에 category 열 전건 작성
[x] step_expression ko/zh 행 수 = process_steps 행 수
[x] preset reentrant_module_v1 slug(B01~B03,B05): role=gate ≥1, module ≥3
[x] preset batch slug(B04,B06): module + trace_keys 전 step
[x] B07/B08: trace_keys 전 step, Fab FEOL 독립 대단계 0건
[x] B08: industry scope 1건 보존
[x] trace_keys ⊆ data_capture_points (slug별)
[x] ko/zh 동형 검증 완료
[x] en/ja 섹션·문단 없음
[x] process_steps_detail: 각 step별 장비명·관리파라미터·추적포인트·Gate포인트·대표제품 보강 완료
[x] control_points_detail: 측정장비/방법·관리주기·이상시조치 3항목 보강 완료
[x] routing_description: 2024~2026년 트렌드 정보 반영 완료 (디지털트윈·AI Agent·CIM 2.0·Lights-out 팹 등)
```

# 10. slug별 변경 요약

| code | legacy_slug | v0.3 보강 핵심 |
|---|---|---|
| B01 | logic_foundry | 파일럿 기준 FEOL Module/BEOL Loop/Inline Gate/PCM-WAT/Disposition 동기화. 각 step별 장비(ASML Scanner, Lam/TEL Etcher, AMAT CMP), 온도·압력·CD 파라미터, SECS/GEM 자동 Hold 체계, DMAIC FDC 분석 보강. control_points에 측정 장비·주기·이상 조치 3항목 보강. |
| B02 | memory_dram_nand | 3D Stack Loop, Array Gate, Redundancy, HBM/Package Handoff 추가. Layer 200~400+ ONON Stack, HAR Etch CD 60~100nm, DRAM DDR5 및 NAND QLC/TLC 제품 사례, RTS 스케줄링 최적화 반영. |
| B03 | analog_mixed | Passive Matching, Parametric Gate, Trim/Fuse, Characterization 추가. 고전압/저잡음 Device, BJT/LDMOS/Precision Passive, Laser Trim 자동화, ESD/Latch-up 샘플링 구체화. |
| B04 | power_discrete | Frontside/Backside Batch, Wafer Probe Gate, Reliability Sample 추가. SiC/GaN Backgrind Feed Rate, BV 600~1700V Probe, HTRB/HTGB/Power Cycle Chamber 조건 보강. |
| B05 | optical_sensor | Pixel/Readout/Optical Stack, Optical/Electrical Gate 추가. BSI/FSI Stack, CFA RGB Color Spectrum, Microlens Reflow, Hybrid Test(Hamamatsu+ATE) 시스템 반영. |
| B06 | compound_semi | Epi Run, Epi Gate, Mesa/Ohmic/Gate, RF/DC Probe Gate 추가. MOCVD/MBE Reactor, PL/XRD Epi Gate, VNA RF Probe(0.1~110GHz) 조건, GaN/GaAs/SiC/InP 소재별 Rc Spec 보강. |
| B07 | assembly_packaging | Die genealogy, material trace, inspection gate, final test flow 추가. CoWoS/HBM 첨단 패키징, TCB/Flip Chip, X-ray/SAM/Shadow Moire 검사, SCARA 로봇·머신 비전 Lights-out 팹 방향성 반영. |
| B08 | test | Program Revision, Tester/Socket/Probe trace, STDF, Retest/Hold, 고객 접근권한 유지. Advantest 93K/Teradyne/J750 장비 상세, STDF Data Flow, CIM 2.0 데이터 통합 방향성 반영. |
