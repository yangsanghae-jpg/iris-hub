# B산업 반도체 제조 — A1 Ch3 런타임형 데이터팩 v0.2 (KO/ZH)

> 본 파일은 사용자가 제공한 B산업 런타임 보완 데이터팩을 기준으로, 2026년 반도체 산업 현황 반영 메모와 JSON 반영 검증 기준을 보강한 버전이다.  
> 적용 대상: `server/data/step3/process_detail_v1.json`의 B01~B08 slug.  
> 언어: 한국어/중국어만 작성. 영어/일본어 필드는 공백으로 유지한다.  
> 작성일: 2026-07-06.  


---


## 0. 점검 결론

기존 문법 MD는 “공정 표현 방향”을 정의한 문서이므로, 그 자체만으로는 A1 Ch3 화면을 대체할 수 없다. 현재 A1 Ch3는 다음 경로를 사용한다.

```text
Q1 선택
  ↓ legacy_slug
server/data/step3/process_detail_v1.json
  ↓ build_process_analysis()
client/src/ui/a1/1_1_process.js
  ↓
client/src/ui/a1/3_process_analysis.js
```

따라서 B산업 공정 표현 보정은 반드시 `process_detail_v1.json`의 slug별 데이터를 다음 필드까지 포함해 수정해야 한다.

| 필드 | 필요성 | 본 데이터팩 반영 |
|---|---|---|
| `legacy_slug` | Q1 선택값과 process_detail 조회 키 연결 | 포함 |
| `label_ko`, `label_zh`, `label_en`, `label_ja` | 화면 표시명 | ko/zh 작성, en/ja 공백 |
| `routing` | 기존 RT 코드 유지 | 포함 |
| `process_steps_detail_ko` | ELK 공정도 노드 | 포함 |
| `process_steps_detail_zh` | 중국어 공정도 노드 | 포함 |
| `control_points_ko` | 관리점 요약 bullet | 포함 |
| `control_points_zh` | 중국어 관리점 요약 | 포함 |
| `control_points_detail_ko` | 관리점-공정 연결선용 step_refs | 포함 |
| `control_points_detail_zh` | 중국어 관리점-공정 연결선용 step_refs | 포함 |
| `data_capture_points` | MES/데이터 수집 포인트 | 포함 |

---

## 1. B산업 적용 원칙

### 1.1 한국어

B산업은 하나의 Fab 통합 템플릿으로 표현하면 안 된다. B01~B06은 전공정 성격이 강하지만, B07은 패키징 공정, B08은 테스트 서비스 공정이다. 따라서 B07/B08에는 FEOL, Lithography, Etch, BEOL 같은 Fab 단계가 들어가면 안 된다.

- B01: Logic Foundry Fab — FEOL/MOL/BEOL 모듈형 라우팅
- B02: Memory Fab — Cell Array/Periphery/Stack 중심 라우팅
- B03: Analog/Mixed Signal — Device Option/Trim/특성검사 중심 라우팅
- B04: Power/Discrete — Epi/Frontside/Backside/Metallization 중심 라우팅
- B05: Optical Sensor — Pixel/CFA/Microlens/Optical Test 중심 라우팅
- B06: Compound Semiconductor — Substrate/Epi/Mesa/Ohmic/Gate 중심 라우팅
- B07: Assembly & Packaging — Wafer Prep/Die Attach/Bonding/Mold/Singulation 중심 라우팅
- B08: Test — Test Program/Setup/Probe/Final Test/Bin/Report 중심 라우팅

### 1.2 中文

B类产业不能使用单一Fab综合模板表达。B01~B06偏向晶圆制造或器件制造，但B07是封装组装流程，B08是测试服务流程。因此B07/B08不应出现FEOL、Lithography、Etch、BEOL等Fab阶段。

- B01：Logic Foundry Fab — FEOL/MOL/BEOL 模块化路线
- B02：Memory Fab — Cell Array/Periphery/Stack  중심路线
- B03：Analog/Mixed Signal — Device Option/Trim/参数测试 중심路线
- B04：Power/Discrete — Epi/Frontside/Backside/Metallization 중심路线
- B05：Optical Sensor — Pixel/CFA/Microlens/Optical Test 중심路线
- B06：Compound Semiconductor — Substrate/Epi/Mesa/Ohmic/Gate 중심路线
- B07：Assembly & Packaging — Wafer Prep/Die Attach/Bonding/Mold/Singulation 중심路线
- B08：Test — Test Program/Setup/Probe/Final Test/Bin/Report 중심路线

---

## 2. B01 — 로직·파운드리 / 逻辑·晶圆代工

```yaml
subindustry_code: B01
legacy_slug: logic_foundry
label_ko: 로직·파운드리
label_zh: 逻辑·晶圆代工
label_en: ""
label_ja: ""
routing: RT_REENTRANT
replacement_policy_ko: 기존 13단계를 FEOL/MOL/BEOL 모듈형 10단계로 교체한다. Lithography/Etch/Deposition/CMP는 독립 대단계가 아니라 각 모듈 내부 Operation으로 note에 표현한다.
replacement_policy_zh: 将现有13阶段改为FEOL/MOL/BEOL模块化10阶段。Lithography/Etch/Deposition/CMP不作为独立大阶段，而写入各模块note中。
```

### 2.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Lot Release | 고객, Node, Product, Lot, Wafer ID, Route, Mask set, FOUP 배정 조건을 등록한다. |
| 2 | FEOL — STI / Isolation | Pad Oxide/Nitride, Active Litho, STI Etch, Trench Fill, STI CMP로 소자 격리 구조를 형성한다. |
| 3 | FEOL — Well / Implant | N-Well/P-Well, Channel stop, Threshold 조정용 Implant와 Anneal을 수행한다. |
| 4 | FEOL — Gate / Source-Drain | High-k/Metal Gate, Gate Patterning, LDD, Spacer, S/D Implant, Activation Anneal, Silicide를 수행한다. |
| 5 | MOL — Contact / Local Interconnect | ILD Deposition/CMP, Contact Litho/Etch, Barrier/Liner, W Plug, Contact CMP를 수행한다. |
| 6 | BEOL — M1 / Via / Metal Stack | Low-k, Via, Metal Trench, Barrier/Seed, Cu Fill, Cu CMP를 Metal Layer별로 반복한다. |
| 7 | Final Layer — Passivation / Pad Open | Top Metal, Passivation, Pad Open Litho/Etch, Final Clean을 수행한다. |
| 8 | Inline Metrology / Defect Gate | CD, Overlay, Film, Defect, Electrical monitor를 공정 모듈별로 확인한다. |
| 9 | PCM/WAT / Wafer Sort | PCM/WAT, Probe, Test Program, Wafer Map, Bin 판정을 수행한다. |
| 10 | Yield Review / Wafer Out | Yield Review 후 Release, Hold, Rework, Scrap, Wafer Out을 결정한다. |

### 2.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Lot Release | 登记客户、Node、Product、Lot、Wafer ID、Route、Mask set与FOUP分配条件。 |
| 2 | FEOL — STI / Isolation | 通过Pad Oxide/Nitride、Active Litho、STI Etch、Trench Fill、STI CMP形成器件隔离结构。 |
| 3 | FEOL — Well / Implant | 执行N-Well/P-Well、Channel stop、阈值调整Implant与Anneal。 |
| 4 | FEOL — Gate / Source-Drain | 执行High-k/Metal Gate、Gate Patterning、LDD、Spacer、S/D Implant、Activation Anneal、Silicide。 |
| 5 | MOL — Contact / Local Interconnect | 执行ILD Deposition/CMP、Contact Litho/Etch、Barrier/Liner、W Plug、Contact CMP。 |
| 6 | BEOL — M1 / Via / Metal Stack | 按Metal Layer重复Low-k、Via、Metal Trench、Barrier/Seed、Cu Fill、Cu CMP。 |
| 7 | Final Layer — Passivation / Pad Open | 执行Top Metal、Passivation、Pad Open Litho/Etch、Final Clean。 |
| 8 | Inline Metrology / Defect Gate | 按工艺模块确认CD、Overlay、Film、Defect、Electrical monitor。 |
| 9 | PCM/WAT / Wafer Sort | 执行PCM/WAT、Probe、Test Program、Wafer Map、Bin判定。 |
| 10 | Yield Review / Wafer Out | Yield Review后决定Release、Hold、Rework、Scrap、Wafer Out。 |

### 2.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| 고객·제품·Node별 Wafer ID, Route, Mask set, 허용 설비군과 Release 조건을 검증한다. | [1] | process_step |
| STI, Well, Gate, S/D, Silicide의 CD, Overlay, Implant 조건과 열처리 조건을 모듈별로 연결한다. | [2,3,4] | process_step |
| Contact, Via, Metal의 Resistance, Void, Seam, Barrier/Seed, Cu CMP 이상을 추적한다. | [5,6] | process_step |
| Passivation, Pad Open, Final Clean의 Crack, Pad Open, Contamination을 확인한다. | [7] | process_step |
| CD, Overlay, Film, Defect map을 Step, Tool, Chamber, Recipe와 연결한다. | [8] | process_step |
| PCM/WAT, Wafer Sort, Test Program, Probe Card, Wafer Map, Bin을 연결한다. | [9,10] | process_step |
| Lot별 Route step, Split/Merge, Rework, Hold, Skip 상태를 전 공정에서 일관되게 추적한다. | [1,10] | common |
| Wafer slot, Chamber, Recipe, Reticle, Chemical batch genealogy를 공정실적과 연결한다. | [1,2,3,4,5,6,8] | common |

### 2.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 验证客户、产品、Node별 Wafer ID、Route、Mask set、允许设备群与Release条件。 | [1] | process_step |
| 按模块关联STI、Well、Gate、S/D、Silicide的CD、Overlay、Implant条件与热处理条件。 | [2,3,4] | process_step |
| 跟踪Contact、Via、Metal的Resistance、Void、Seam、Barrier/Seed、Cu CMP异常。 | [5,6] | process_step |
| 确认Passivation、Pad Open、Final Clean的Crack、Pad Open、Contamination。 | [7] | process_step |
| 将CD、Overlay、Film、Defect map与Step、Tool、Chamber、Recipe连接。 | [8] | process_step |
| 关联PCM/WAT、Wafer Sort、Test Program、Probe Card、Wafer Map、Bin。 | [9,10] | process_step |
| 全流程一致追踪Lot별 Route step、Split/Merge、Rework、Hold、Skip状态。 | [1,10] | common |
| 将Wafer slot、Chamber、Recipe、Reticle、Chemical batch genealogy与工艺实绩连接。 | [1,2,3,4,5,6,8] | common |

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - route_step
  - equipment_id
  - chamber_id
  - recipe_id
  - reticle_id
  - carrier_id
  - q_time
  - cd_overlay_result
  - defect_map
  - wat_result
  - wafer_map
```

---

## 3. B02 — 메모리 DRAM·NAND / 存储器 DRAM·NAND

```yaml
subindustry_code: B02
legacy_slug: memory_dram_nand
label_ko: 메모리 DRAM·NAND
label_zh: 存储器 DRAM·NAND
label_en: ""
label_ja: ""
routing: RT_REENTRANT
replacement_policy_ko: 기존 Fab 통합 16단계를 Memory Cell/Array, Periphery, 3D Stack, Interconnect, Wafer Sort 중심으로 재구성한다.
replacement_policy_zh: 将现有Fab综合16阶段重构为Memory Cell/Array、Periphery、3D Stack、Interconnect、Wafer Sort 중심流程。
```

### 3.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Memory Lot Release | 제품군(DRAM/NAND/HBM), Node, Mask set, Route, Wafer ID를 등록한다. |
| 2 | Periphery / CMOS Module | 주변회로용 Well, Isolation, Gate, S/D, Contact를 형성한다. |
| 3 | Memory Cell Array Formation | DRAM Capacitor 또는 NAND Cell/Channel 구조를 형성한다. |
| 4 | 3D Stack / Wordline / Bitline Module | 3D NAND Stack, Wordline, Bitline, Contact hole 등 Cell 연결 구조를 형성한다. |
| 5 | Contact / Interconnect / Passivation | Contact, Via, Metal, Passivation으로 Array와 Periphery를 연결한다. |
| 6 | Inline Metrology / Defect Gate | Cell profile, Overlay, CD, Film, Defect, Electrical monitor를 확인한다. |
| 7 | PCM/WAT / Wafer Sort | Memory parametric, redundancy, repair, Wafer Map, Die grade를 확정한다. |
| 8 | Wafer Thinning / TSV / HBM Interface | HBM 또는 고급 패키지 적용 제품은 Thinning, TSV, bonding interface를 준비한다. |
| 9 | Die Sort / KGD Handoff | Known Good Die를 선별하고 Package 또는 HBM 조립으로 이관한다. |
| 10 | Yield Review / Excursion Closure | Cell fail, Array fail, Parametric fail을 분석하고 출하·Hold·Rework를 결정한다. |

### 3.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Memory Lot Release | 登记产品族(DRAM/NAND/HBM)、Node、Mask set、Route、Wafer ID。 |
| 2 | Periphery / CMOS Module | 形成外围电路用Well、Isolation、Gate、S/D、Contact。 |
| 3 | Memory Cell Array Formation | 形成DRAM Capacitor或NAND Cell/Channel结构。 |
| 4 | 3D Stack / Wordline / Bitline Module | 形成3D NAND Stack、Wordline、Bitline、Contact hole等Cell连接结构。 |
| 5 | Contact / Interconnect / Passivation | 通过Contact、Via、Metal、Passivation连接Array与Periphery。 |
| 6 | Inline Metrology / Defect Gate | 确认Cell profile、Overlay、CD、Film、Defect、Electrical monitor。 |
| 7 | PCM/WAT / Wafer Sort | 确定Memory parametric、redundancy、repair、Wafer Map、Die grade。 |
| 8 | Wafer Thinning / TSV / HBM Interface | HBM或先进封装产品准备Thinning、TSV、bonding interface。 |
| 9 | Die Sort / KGD Handoff | 筛选Known Good Die并移交Package或HBM组装。 |
| 10 | Yield Review / Excursion Closure | 分析Cell fail、Array fail、Parametric fail，并决定出货、Hold、Rework。 |

### 3.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| DRAM/NAND/HBM별 Route, Mask set, 공정 Option과 허용 설비군을 검증한다. | [1] | process_step |
| Periphery CMOS와 Memory Cell Array의 공정 조건과 계측 결과를 분리 관리한다. | [2,3] | process_step |
| 3D Stack, Wordline, Bitline, Contact hole의 Profile, CD, Overlay를 관리한다. | [4] | process_step |
| Contact, Via, Metal, Passivation의 저항, 단락, 개방, 결함을 추적한다. | [5] | process_step |
| Defect map, Cell fail pattern, Film, CD, Overlay를 Step/Chamber/Recipe와 연결한다. | [6,10] | process_step |
| Wafer Sort, Redundancy, Repair, Die grade, Wafer Map을 동일 Die 기준으로 승계한다. | [7,9] | process_step |
| HBM 적용 제품은 TSV, Thinning, Warpage, Bonding Interface 조건을 관리한다. | [8] | process_step |
| Lot-Wafer-Die-Package 간 genealogy를 유지한다. | [1,7,8,9] | common |

### 3.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 验证DRAM/NAND/HBM별 Route、Mask set、工艺Option与允许设备群。 | [1] | process_step |
| 分开管理Periphery CMOS与Memory Cell Array的工艺条件和量测结果。 | [2,3] | process_step |
| 管理3D Stack、Wordline、Bitline、Contact hole的Profile、CD、Overlay。 | [4] | process_step |
| 跟踪Contact、Via、Metal、Passivation的电阻、短路、开路、缺陷。 | [5] | process_step |
| 将Defect map、Cell fail pattern、Film、CD、Overlay与Step/Chamber/Recipe连接。 | [6,10] | process_step |
| 以同一Die为基准继承Wafer Sort、Redundancy、Repair、Die grade、Wafer Map。 | [7,9] | process_step |
| HBM产品管理TSV、Thinning、Warpage、Bonding Interface条件。 | [8] | process_step |
| 维护Lot-Wafer-Die-Package genealogy。 | [1,7,8,9] | common |

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - die_id
  - product_family
  - route_step
  - equipment_id
  - recipe_id
  - reticle_id
  - cd_overlay_result
  - defect_map
  - cell_fail_map
  - redundancy_repair_result
  - wafer_sort_bin
  - die_grade
```

---

## 4. B03 — 아날로그·혼성신호 / 模拟·混合信号

```yaml
subindustry_code: B03
legacy_slug: analog_mixed
label_ko: 아날로그·혼성신호
label_zh: 模拟·混合信号
label_en: ""
label_ja: ""
routing: RT_REENTRANT
replacement_policy_ko: 기존 Fab 통합 흐름에 BCD, HV, RF, Passive, Trim, 특성검사 단계를 추가해 Analog/Mixed Signal 공정으로 재구성한다.
replacement_policy_zh: 在原Fab综合流程基础上加入BCD、HV、RF、Passive、Trim、参数测试阶段，重构为模拟/混合信号工艺。
```

### 4.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Product Option Release | PMIC, RF, ADC/DAC, BCD, HV Option과 Mask set, Route를 등록한다. |
| 2 | Isolation / Well / HV Device Module | Deep Well, Isolation, HV LDMOS/BCD 관련 구조를 형성한다. |
| 3 | Gate / Source-Drain / Device Module | CMOS, BJT, DMOS, RF Device의 Gate, S/D, Contact 구조를 형성한다. |
| 4 | Passive / Capacitor / Resistor Module | MIM Capacitor, Poly Resistor, Precision Resistor, Inductor 등 수동소자를 형성한다. |
| 5 | Trim / Fuse / Option Structure | Laser/eFuse/OTP/Trim 구조와 제품 옵션 구분 구조를 형성한다. |
| 6 | Contact / BEOL / Top Metal | Contact, Via, Metal, Thick Top Metal, Pad 구조를 형성한다. |
| 7 | Passivation / Pad / Probe Prep | Passivation, Pad Open, Probe 가능 상태를 만든다. |
| 8 | Inline / Parametric Metrology | Vt, Ron, Breakdown, Cap/Res, RF 특성, CD/Overlay를 확인한다. |
| 9 | WAT / Trim / Wafer Sort | WAT, Trim, Test Program, Wafer Sort, Bin을 수행한다. |
| 10 | Characterization / Yield Review | 온도·전압·주파수 조건별 특성 분석 후 출하 판정을 수행한다. |

### 4.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Product Option Release | 登记PMIC、RF、ADC/DAC、BCD、HV Option、Mask set与Route。 |
| 2 | Isolation / Well / HV Device Module | 形成Deep Well、Isolation、HV LDMOS/BCD相关结构。 |
| 3 | Gate / Source-Drain / Device Module | 形成CMOS、BJT、DMOS、RF Device的Gate、S/D、Contact结构。 |
| 4 | Passive / Capacitor / Resistor Module | 形成MIM Capacitor、Poly Resistor、Precision Resistor、Inductor等无源器件。 |
| 5 | Trim / Fuse / Option Structure | 形成Laser/eFuse/OTP/Trim结构与产品选项区分结构。 |
| 6 | Contact / BEOL / Top Metal | 形成Contact、Via、Metal、Thick Top Metal、Pad结构。 |
| 7 | Passivation / Pad / Probe Prep | 完成Passivation、Pad Open，形成可Probe状态。 |
| 8 | Inline / Parametric Metrology | 确认Vt、Ron、Breakdown、Cap/Res、RF特性、CD/Overlay。 |
| 9 | WAT / Trim / Wafer Sort | 执行WAT、Trim、Test Program、Wafer Sort、Bin。 |
| 10 | Characterization / Yield Review | 按温度、电压、频率条件分析特性并执行出货判定。 |

### 4.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| 제품별 BCD/HV/RF Option, Mask set, 공정 Option과 Route를 검증한다. | [1] | process_step |
| HV, BCD, DMOS, BJT, RF Device의 Breakdown, Leakage, Ron 조건을 관리한다. | [2,3,8] | process_step |
| MIM, Resistor, Inductor 등 수동소자의 두께, 면저항, 매칭 특성을 관리한다. | [4,8] | process_step |
| Trim, Fuse, OTP 구조와 Test Program Revision을 제품 Option과 연결한다. | [5,9] | process_step |
| Top Metal, Pad, Passivation의 Probe 가능성, Pad damage, Crack을 확인한다. | [6,7] | process_step |
| 온도·전압·주파수별 특성검사 결과를 Wafer Sort와 Yield Review에 연결한다. | [9,10] | process_step |
| Analog 특성 불량을 공정 Step, 설비, Recipe, Mask Revision과 연결한다. | [8,10] | common |

### 4.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 验证产品별BCD/HV/RF Option、Mask set、工艺Option与Route。 | [1] | process_step |
| 管理HV、BCD、DMOS、BJT、RF Device的Breakdown、Leakage、Ron条件。 | [2,3,8] | process_step |
| 管理MIM、Resistor、Inductor等无源器件的厚度、方阻、匹配特性。 | [4,8] | process_step |
| 将Trim、Fuse、OTP结构与Test Program Revision和产品Option连接。 | [5,9] | process_step |
| 确认Top Metal、Pad、Passivation的可Probe性、Pad damage、Crack。 | [6,7] | process_step |
| 将温度、电压、频率条件下的特性测试结果连接到Wafer Sort和Yield Review。 | [9,10] | process_step |
| 将Analog特性不良与工艺Step、设备、Recipe、Mask Revision连接。 | [8,10] | common |

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - route_step
  - device_option
  - mask_set
  - recipe_id
  - equipment_id
  - parametric_result
  - trim_code
  - fuse_result
  - wafer_sort_bin
  - characterization_result
```

---

## 5. B04 — 전력·디스크리트 / 功率·分立器件

```yaml
subindustry_code: B04
legacy_slug: power_discrete
label_ko: 전력·디스크리트
label_zh: 功率·分立器件
label_en: ""
label_ja: ""
routing: RT_BATCH
replacement_policy_ko: 기존 Fab 통합 16단계를 Power Device 고유의 Epi, Trench/Gate, Frontside Metal, Backside Thinning/Metal, Wafer Probe 중심으로 교체한다.
replacement_policy_zh: 将原Fab综合16阶段替换为Power Device特有的Epi、Trench/Gate、Frontside Metal、Backside Thinning/Metal、Wafer Probe流程。
```

### 5.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Wafer / Epi Substrate Incoming | Si, SiC, Epi wafer, 두께, 저항, 결정 결함, 공급사 Lot을 확인한다. |
| 2 | Epi / Drift Layer Formation | 전력소자 특성에 필요한 Epi/Drift layer 두께, 도핑, 균일도를 형성한다. |
| 3 | Frontside Isolation / Body / Well | Body, Well, Isolation, Field oxide 등 Frontside 기초 구조를 만든다. |
| 4 | Trench / Gate / Source Module | Trench MOS, Gate oxide, Poly/Metal gate, Source implant와 Contact를 형성한다. |
| 5 | Frontside Metallization / Passivation | Al/Cu Metal, Pad, Passivation, Edge termination 관련 구조를 형성한다. |
| 6 | Backgrind / Wafer Thinning | 전류 경로와 패키지 두께 조건에 맞춰 Backgrind와 Wafer thinning을 수행한다. |
| 7 | Backside Implant / Backside Metal | Backside implant, Anneal, Ti/Ni/Ag 등 Backside metal을 형성한다. |
| 8 | Wafer Probe / Electrical Test | Breakdown, Leakage, Ron, Vf, Gate charge 등 전기특성을 Wafer 상태에서 검사한다. |
| 9 | Dicing / Die Sort Handoff | Wafer dicing, Die grade, Good die 선별 후 패키징으로 이관한다. |
| 10 | Yield Review / Lot Disposition | 전기특성, 결함, Backside 품질 기준으로 Release, Hold, Scrap을 결정한다. |

### 5.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Wafer / Epi Substrate Incoming | 确认Si、SiC、Epi wafer的厚度、电阻、晶体缺陷与供应商Lot。 |
| 2 | Epi / Drift Layer Formation | 形成满足功率器件特性的Epi/Drift layer厚度、掺杂与均匀性。 |
| 3 | Frontside Isolation / Body / Well | 形成Body、Well、Isolation、Field oxide等Frontside基础结构。 |
| 4 | Trench / Gate / Source Module | 形成Trench MOS、Gate oxide、Poly/Metal gate、Source implant与Contact。 |
| 5 | Frontside Metallization / Passivation | 形成Al/Cu Metal、Pad、Passivation、Edge termination相关结构。 |
| 6 | Backgrind / Wafer Thinning | 按电流路径和封装厚度要求执行Backgrind与Wafer thinning。 |
| 7 | Backside Implant / Backside Metal | 形成Backside implant、Anneal、Ti/Ni/Ag等Backside metal。 |
| 8 | Wafer Probe / Electrical Test | 在Wafer状态检查Breakdown、Leakage、Ron、Vf、Gate charge等电特性。 |
| 9 | Dicing / Die Sort Handoff | 执行Wafer dicing、Die grade、Good die筛选并移交封装。 |
| 10 | Yield Review / Lot Disposition | 基于电特性、缺陷、Backside质量决定Release、Hold、Scrap。 |

### 5.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| Epi wafer의 두께, 저항, 결함, 공급사 Lot과 승인상태를 확인한다. | [1,2] | process_step |
| Drift layer, Body, Well, Trench, Gate oxide 조건이 Breakdown과 Ron에 미치는 영향을 연결한다. | [2,3,4,8] | process_step |
| Edge termination, Passivation, Pad 구조의 전계 집중·신뢰성 위험을 관리한다. | [5] | process_step |
| Backgrind 두께, Wafer bow, Crack, Chipping, Backside metal adhesion을 관리한다. | [6,7] | process_step |
| Wafer Probe의 Breakdown, Leakage, Ron, Vf, Gate charge 결과를 Die grade에 연결한다. | [8,9,10] | process_step |
| Frontside/Backside 공정 이력을 Die 단위로 승계한다. | [1,5,6,7,9] | common |

### 5.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 确认Epi wafer的厚度、电阻、缺陷、供应商Lot与批准状态。 | [1,2] | process_step |
| 关联Drift layer、Body、Well、Trench、Gate oxide条件对Breakdown和Ron的影响。 | [2,3,4,8] | process_step |
| 管理Edge termination、Passivation、Pad结构的电场集中和可靠性风险。 | [5] | process_step |
| 管理Backgrind厚度、Wafer bow、Crack、Chipping、Backside metal adhesion。 | [6,7] | process_step |
| 将Wafer Probe的Breakdown、Leakage、Ron、Vf、Gate charge结果连接到Die grade。 | [8,9,10] | process_step |
| 以Die为单位继承Frontside/Backside工艺履历。 | [1,5,6,7,9] | common |

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - epi_lot
  - substrate_resistivity
  - thickness_result
  - route_step
  - equipment_id
  - recipe_id
  - backside_metal_lot
  - electrical_probe_result
  - die_grade
  - wafer_map
```

---

## 6. B05 — 이미지센서·광반도체 / 图像传感器·光半导体

```yaml
subindustry_code: B05
legacy_slug: optical_sensor
label_ko: 이미지센서·광반도체
label_zh: 图像传感器·光半导体
label_en: ""
label_ja: ""
routing: RT_REENTRANT
replacement_policy_ko: 기존 Fab 통합 16단계를 Pixel/Photodiode, Color Filter, Microlens, Optical Wafer Test 중심으로 교체한다.
replacement_policy_zh: 将原Fab综合16阶段替换为Pixel/Photodiode、Color Filter、Microlens、Optical Wafer Test中心流程。
```

### 6.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Sensor Lot Release | Sensor 제품, Pixel size, Optical stack, Route, Mask set, Wafer ID를 등록한다. |
| 2 | Photodiode / Pixel Formation | Photodiode, Transfer Gate, Isolation, Pinned structure 등 Pixel 구조를 형성한다. |
| 3 | Readout / CMOS Device Module | Readout 회로, Logic, Analog device, Contact 구조를 형성한다. |
| 4 | BEOL / Light Path Interconnect | Metal routing, Shielding, Passivation, Optical opening을 형성한다. |
| 5 | Color Filter Array / Black Matrix | CFA, Black matrix, 색상 패턴, 균일도와 정렬을 형성·검사한다. |
| 6 | Microlens / Optical Stack | Microlens, Planarization, Optical coating, Focus 특성을 형성한다. |
| 7 | Pad Open / Final Passivation | Probe Pad, Final passivation, Contamination control을 완료한다. |
| 8 | Optical / Electrical Wafer Test | Dark current, PRNU, QE, Defect pixel, Electrical parametric을 검사한다. |
| 9 | Wafer Map / Sensor Bin | Pixel defect map, Optical bin, Electrical bin, Wafer Map을 생성한다. |
| 10 | Yield Review / Wafer Out | 광학·전기 특성 기준으로 Release, Hold, Scrap, Wafer Out을 결정한다. |

### 6.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Wafer Start / Sensor Lot Release | 登记Sensor产品、Pixel size、Optical stack、Route、Mask set、Wafer ID。 |
| 2 | Photodiode / Pixel Formation | 形成Photodiode、Transfer Gate、Isolation、Pinned structure等Pixel结构。 |
| 3 | Readout / CMOS Device Module | 形成Readout电路、Logic、Analog device、Contact结构。 |
| 4 | BEOL / Light Path Interconnect | 形成Metal routing、Shielding、Passivation、Optical opening。 |
| 5 | Color Filter Array / Black Matrix | 形成并检查CFA、Black matrix、颜色图案、均匀度与对准。 |
| 6 | Microlens / Optical Stack | 形成Microlens、Planarization、Optical coating、Focus特性。 |
| 7 | Pad Open / Final Passivation | 完成Probe Pad、Final passivation、Contamination control。 |
| 8 | Optical / Electrical Wafer Test | 检查Dark current、PRNU、QE、Defect pixel、Electrical parametric。 |
| 9 | Wafer Map / Sensor Bin | 生成Pixel defect map、Optical bin、Electrical bin、Wafer Map。 |
| 10 | Yield Review / Wafer Out | 按光学/电气特性决定Release、Hold、Scrap、Wafer Out。 |

### 6.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| Pixel size, Optical stack, Mask set, Sensor option을 Lot release 단계에서 검증한다. | [1] | process_step |
| Photodiode, Transfer Gate, Isolation 조건을 Dark current와 Defect pixel 결과에 연결한다. | [2,8,9] | process_step |
| Readout CMOS와 Analog 특성 결과를 Wafer Sort와 연결한다. | [3,8] | process_step |
| BEOL Metal과 Optical opening이 광 경로, Shielding, Crosstalk에 미치는 영향을 관리한다. | [4] | process_step |
| CFA, Black matrix, Microlens의 Alignment, Uniformity, Particle을 관리한다. | [5,6] | process_step |
| Optical bin, Electrical bin, Pixel defect map을 Wafer Map과 Yield Review에 연결한다. | [8,9,10] | process_step |

### 6.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 在Lot release阶段验证Pixel size、Optical stack、Mask set、Sensor option。 | [1] | process_step |
| 将Photodiode、Transfer Gate、Isolation条件与Dark current和Defect pixel结果连接。 | [2,8,9] | process_step |
| 将Readout CMOS与Analog特性结果连接到Wafer Sort。 | [3,8] | process_step |
| 管理BEOL Metal与Optical opening对光路、Shielding、Crosstalk的影响。 | [4] | process_step |
| 管理CFA、Black matrix、Microlens的Alignment、Uniformity、Particle。 | [5,6] | process_step |
| 将Optical bin、Electrical bin、Pixel defect map连接到Wafer Map与Yield Review。 | [8,9,10] | process_step |

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - pixel_size
  - optical_stack_id
  - route_step
  - equipment_id
  - recipe_id
  - cfa_lot
  - microlens_lot
  - dark_current_result
  - qe_result
  - pixel_defect_map
  - optical_bin
  - electrical_bin
```

---

## 7. B06 — 화합물 반도체 / 化合物半导体

```yaml
subindustry_code: B06
legacy_slug: compound_semi
label_ko: 화합물 반도체
label_zh: 化合物半导体
label_en: ""
label_ja: ""
routing: RT_BATCH
replacement_policy_ko: 기존 Fab 통합 16단계를 Substrate, Epitaxy, Mesa/Isolation, Ohmic Contact, Gate/Schottky, Passivation, Backside, Wafer Probe 중심으로 교체한다.
replacement_policy_zh: 将原Fab综合16阶段替换为Substrate、Epitaxy、Mesa/Isolation、Ohmic Contact、Gate/Schottky、Passivation、Backside、Wafer Probe流程。
```

### 7.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Substrate Incoming / Lot Release | SiC, GaN, GaAs, InP 등 기판 Lot, 결정 결함, 방향성, 두께를 확인한다. |
| 2 | Epitaxy Growth | MOCVD/MBE/Epi 성장으로 Buffer, Channel, Barrier, Cap layer를 형성한다. |
| 3 | Mesa / Isolation | Mesa etch, Ion isolation, Surface cleaning으로 소자 간 격리 구조를 만든다. |
| 4 | Ohmic Contact Formation | Source/Drain 또는 Cathode/Anode Ohmic metal, Anneal, Contact resistance를 관리한다. |
| 5 | Gate / Schottky / Field Plate | Gate metal, Schottky contact, Field plate, Gate recess 등 핵심 전극 구조를 형성한다. |
| 6 | Passivation / Surface Protection | SiN/oxide passivation, Surface trap, Leakage, Reliability 관련 보호막을 형성한다. |
| 7 | Frontside / Backside Metallization | Frontside pad, Backside thinning, Via, Backside metal을 제품 구조에 따라 수행한다. |
| 8 | Wafer Probe / RF·DC Test | DC, RF, Breakdown, Leakage, Gain, Frequency 특성을 Wafer 상태에서 검사한다. |
| 9 | Die Singulation / Visual Inspection | Dicing, Chipping, Crack, Metal peel, 외관 검사를 수행한다. |
| 10 | Yield Review / Package Handoff | Probe 결과, 결함, 전기·RF 특성 기준으로 Package 이관 또는 Hold를 결정한다. |

### 7.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Substrate Incoming / Lot Release | 确认SiC、GaN、GaAs、InP等基板Lot、晶体缺陷、取向、厚度。 |
| 2 | Epitaxy Growth | 通过MOCVD/MBE/Epi生长形成Buffer、Channel、Barrier、Cap layer。 |
| 3 | Mesa / Isolation | 通过Mesa etch、Ion isolation、Surface cleaning形成器件隔离结构。 |
| 4 | Ohmic Contact Formation | 管理Source/Drain或Cathode/Anode Ohmic metal、Anneal、Contact resistance。 |
| 5 | Gate / Schottky / Field Plate | 形成Gate metal、Schottky contact、Field plate、Gate recess等核心电极结构。 |
| 6 | Passivation / Surface Protection | 形成SiN/oxide passivation等与Surface trap、Leakage、Reliability相关的保护膜。 |
| 7 | Frontside / Backside Metallization | 按产品结构执行Frontside pad、Backside thinning、Via、Backside metal。 |
| 8 | Wafer Probe / RF·DC Test | 在Wafer状态检查DC、RF、Breakdown、Leakage、Gain、Frequency特性。 |
| 9 | Die Singulation / Visual Inspection | 执行Dicing、Chipping、Crack、Metal peel、外观检查。 |
| 10 | Yield Review / Package Handoff | 按Probe结果、缺陷、电气/RF特性决定Package移交或Hold。 |

### 7.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| Substrate Lot, 결정 결함, Epi wafer 조건을 제품 성능과 연결한다. | [1,2] | process_step |
| Epitaxy thickness, composition, doping, defect density를 관리한다. | [2] | process_step |
| Mesa depth, Isolation leakage, Surface residue를 관리한다. | [3] | process_step |
| Ohmic contact resistance, Anneal 조건, Metal adhesion을 관리한다. | [4] | process_step |
| Gate/Schottky/Field plate 구조를 Breakdown, RF gain, Leakage 결과와 연결한다. | [5,8] | process_step |
| Passivation 품질과 Surface trap, Current collapse, Reliability 결과를 연결한다. | [6,8] | process_step |
| Backside thinning, Via, Backside metal의 저항과 Crack 위험을 관리한다. | [7,9] | process_step |
| RF/DC Probe 결과를 Die grade와 Package Handoff에 연결한다. | [8,10] | process_step |

### 7.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 将Substrate Lot、晶体缺陷、Epi wafer条件与产品性能连接。 | [1,2] | process_step |
| 管理Epitaxy thickness、composition、doping、defect density。 | [2] | process_step |
| 管理Mesa depth、Isolation leakage、Surface residue。 | [3] | process_step |
| 管理Ohmic contact resistance、Anneal条件、Metal adhesion。 | [4] | process_step |
| 将Gate/Schottky/Field plate结构与Breakdown、RF gain、Leakage结果连接。 | [5,8] | process_step |
| 将Passivation质量与Surface trap、Current collapse、Reliability结果连接。 | [6,8] | process_step |
| 管理Backside thinning、Via、Backside metal的电阻与Crack风险。 | [7,9] | process_step |
| 将RF/DC Probe结果连接到Die grade与Package Handoff。 | [8,10] | process_step |

```yaml
data_capture_points:
  - lot_id
  - wafer_id
  - substrate_lot
  - epi_run_id
  - epi_thickness
  - epi_composition
  - route_step
  - equipment_id
  - recipe_id
  - contact_resistance
  - rf_test_result
  - dc_probe_result
  - die_grade
```

---

## 8. B07 — 반도체 패키징 / 半导体封装

```yaml
subindustry_code: B07
legacy_slug: assembly_packaging
label_ko: 반도체 패키징
label_zh: 半导体封装
label_en: ""
label_ja: ""
routing: RT_BATCH
replacement_policy_ko: 기존 Fab 통합 16단계를 전면 폐기한다. FEOL/Lithography/Etch/BEOL 표현을 제거하고 Package Assembly 라우팅으로 교체한다.
replacement_policy_zh: 全面废弃原Fab综合16阶段。删除FEOL/Lithography/Etch/BEOL表达，替换为Package Assembly路线。
```

### 8.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Wafer / Substrate / Leadframe Incoming | Wafer, KGD, Substrate, Leadframe, EMC, Underfill, Solder ball의 Lot과 보관조건을 확인한다. |
| 2 | Wafer Backgrind / Thinning | Package 두께 조건에 맞춰 Backgrind, Tape mount, Wafer thinning을 수행한다. |
| 3 | Dicing / Die Sort / Kitting | Saw/Laser dicing, Die pick, KGD 확인, Package type별 Kit를 구성한다. |
| 4 | Die Attach / Flip Chip Attach | Epoxy, Solder, Flux, Bond force, 온도, 위치 정렬 조건으로 Die를 부착한다. |
| 5 | Wire Bond / Bump / Hybrid Bonding | 제품 유형에 따라 Wire bond, Flip chip, Bump, Hybrid bonding을 수행한다. |
| 6 | Underfill / Molding / Encapsulation | Underfill, Mold, Cure, Lid/TIM, Void, Delamination을 관리한다. |
| 7 | Marking / Post Mold Cure / Plating | Marking, PMC, Lead finish, Ball attach, Surface finish를 수행한다. |
| 8 | Singulation / Package Forming | Saw singulation, Trim/Form, Ball inspect, Package 외형을 완성한다. |
| 9 | Package Inspection / Reliability Screening | AOI, X-ray, SAT, Warpage, Coplanarity, MSL, Reliability screening을 수행한다. |
| 10 | Final Test / Packing / Ship | Final Test, Bin, Label, Dry pack, CoC, 고객 데이터 인계를 수행한다. |

### 8.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Wafer / Substrate / Leadframe Incoming | 确认Wafer、KGD、Substrate、Leadframe、EMC、Underfill、Solder ball的Lot与保存条件。 |
| 2 | Wafer Backgrind / Thinning | 按Package厚度要求执行Backgrind、Tape mount、Wafer thinning。 |
| 3 | Dicing / Die Sort / Kitting | 执行Saw/Laser dicing、Die pick、KGD确认，并按Package type构成Kit。 |
| 4 | Die Attach / Flip Chip Attach | 按Epoxy、Solder、Flux、Bond force、温度、位置对准条件贴装Die。 |
| 5 | Wire Bond / Bump / Hybrid Bonding | 根据产品类型执行Wire bond、Flip chip、Bump、Hybrid bonding。 |
| 6 | Underfill / Molding / Encapsulation | 管理Underfill、Mold、Cure、Lid/TIM、Void、Delamination。 |
| 7 | Marking / Post Mold Cure / Plating | 执行Marking、PMC、Lead finish、Ball attach、Surface finish。 |
| 8 | Singulation / Package Forming | 执行Saw singulation、Trim/Form、Ball inspect，完成Package外形。 |
| 9 | Package Inspection / Reliability Screening | 执行AOI、X-ray、SAT、Warpage、Coplanarity、MSL、Reliability screening。 |
| 10 | Final Test / Packing / Ship | 执行Final Test、Bin、Label、Dry pack、CoC、客户数据移交。 |

### 8.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| Wafer, Die, Substrate, Leadframe, EMC, Underfill, Solder ball Lot과 보관조건을 확인한다. | [1] | process_step |
| Backgrind 두께, Warpage, Crack, Tape 이력과 Wafer Map 승계를 관리한다. | [2,3] | process_step |
| Die ID, KGD, Package Kit, Substrate ID를 Package genealogy로 연결한다. | [3,4,5] | process_step |
| Die attach, Flip chip, Wire bond, Hybrid bonding의 위치, 힘, 온도, 시간 조건을 추적한다. | [4,5] | process_step |
| Underfill, Mold, Cure 조건과 Void, Delamination, Warpage 결과를 연결한다. | [6,9] | process_step |
| Marking, Ball attach, Singulation, Trim/Form의 외관·치수·손상 기준을 관리한다. | [7,8,9] | process_step |
| Final Test Bin, Dry pack, Label, CoC와 고객 출하 데이터를 연결한다. | [10] | process_step |
| Wafer Map의 Die 좌표가 Package ID, Test Result, Ship Lot까지 승계되는지 검증한다. | [1,3,10] | common |

### 8.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 确认Wafer、Die、Substrate、Leadframe、EMC、Underfill、Solder ball Lot与保存条件。 | [1] | process_step |
| 管理Backgrind厚度、Warpage、Crack、Tape履历与Wafer Map继承。 | [2,3] | process_step |
| 将Die ID、KGD、Package Kit、Substrate ID连接为Package genealogy。 | [3,4,5] | process_step |
| 追踪Die attach、Flip chip、Wire bond、Hybrid bonding的位置、力、温度、时间条件。 | [4,5] | process_step |
| 关联Underfill、Mold、Cure条件与Void、Delamination、Warpage结果。 | [6,9] | process_step |
| 管理Marking、Ball attach、Singulation、Trim/Form的外观、尺寸、损伤标准。 | [7,8,9] | process_step |
| 将Final Test Bin、Dry pack、Label、CoC与客户出货数据连接。 | [10] | process_step |
| 验证Wafer Map的Die坐标是否继承到Package ID、Test Result、Ship Lot。 | [1,3,10] | common |

```yaml
data_capture_points:
  - wafer_id
  - die_id
  - package_id
  - substrate_id
  - leadframe_lot
  - emc_lot
  - underfill_lot
  - route_step
  - equipment_id
  - bonding_recipe
  - mold_recipe
  - xray_result
  - sat_result
  - final_test_bin
  - ship_lot
```

---

## 9. B08 — 반도체 테스트 / 半导体测试

```yaml
subindustry_code: B08
legacy_slug: test
label_ko: 반도체 테스트
label_zh: 半导体测试
label_en: ""
label_ja: ""
routing: RT_BATCH
replacement_policy_ko: 기존 Fab 통합 16단계를 전면 폐기한다. 테스트 산업은 Test Program, Setup, Probe/Final Test, Burn-in, Bin, Report 흐름으로 표현한다.
replacement_policy_zh: 全面废弃原Fab综合16阶段。测试产业应表达为Test Program、Setup、Probe/Final Test、Burn-in、Bin、Report流程。
```

### 9.1 process_steps_detail_ko

| # | step | note |
|---|---|---|
| 1 | Test Request / Program Release | 고객 Test spec, Test Program, Revision, Device, Package, Lot 조건을 등록한다. |
| 2 | Probe Card / Socket / Load Board Setup | Wafer Probe 또는 Final Test에 필요한 Probe card, Socket, Load board, Handler 조건을 준비한다. |
| 3 | Incoming Wafer / Package Check | Wafer Map, Package ID, Ship Lot, 수량, 외관, 보관조건을 확인한다. |
| 4 | Wafer Probe / CP Test | Wafer 상태에서 Contact, Parametric, Functional, Bin test를 수행한다. |
| 5 | Final Test / FT | Package 상태에서 Tester, Handler, Socket 조건으로 Functional, Speed, Power test를 수행한다. |
| 6 | Burn-in / Reliability Screening | Burn-in, HTOL, Temperature cycling, Stress screening을 수행한다. |
| 7 | Retest / Correlation / Characterization | Retest, Golden sample, Correlation, 온도·전압 조건별 Characterization을 수행한다. |
| 8 | Bin / Yield / Failure Review | Bin, Yield, Fail item, Test time, Tester correlation을 분석한다. |
| 9 | Report / Customer Data Handoff | STDF, Summary report, Wafer Map, Bin data, CoC, 고객 포맷 데이터를 생성한다. |
| 10 | Packing / Ship / Data Archive | Label, Packing, 출하 승인, Test data archive, 고객 데이터 접근권한을 관리한다. |

### 9.2 process_steps_detail_zh

| # | step | note |
|---|---|---|
| 1 | Test Request / Program Release | 登记客户Test spec、Test Program、Revision、Device、Package、Lot条件。 |
| 2 | Probe Card / Socket / Load Board Setup | 准备Wafer Probe或Final Test所需Probe card、Socket、Load board、Handler条件。 |
| 3 | Incoming Wafer / Package Check | 确认Wafer Map、Package ID、Ship Lot、数量、外观、保存条件。 |
| 4 | Wafer Probe / CP Test | 在Wafer状态执行Contact、Parametric、Functional、Bin test。 |
| 5 | Final Test / FT | 在Package状态通过Tester、Handler、Socket执行Functional、Speed、Power test。 |
| 6 | Burn-in / Reliability Screening | 执行Burn-in、HTOL、Temperature cycling、Stress screening。 |
| 7 | Retest / Correlation / Characterization | 执行Retest、Golden sample、Correlation、温度/电压条件Characterization。 |
| 8 | Bin / Yield / Failure Review | 分析Bin、Yield、Fail item、Test time、Tester correlation。 |
| 9 | Report / Customer Data Handoff | 生成STDF、Summary report、Wafer Map、Bin data、CoC、客户格式数据。 |
| 10 | Packing / Ship / Data Archive | 管理Label、Packing、出货批准、Test data archive、客户数据权限。 |

### 9.3 control_points_detail_ko

| text | step_refs | scope |
|---|---|---|
| Test Program, Revision, 고객 Spec, Device/Package 조건의 일치를 검증한다. | [1] | process_step |
| Probe card, Socket, Load board, Handler, Tester의 조합과 교정상태를 확인한다. | [2,4,5] | process_step |
| Incoming Wafer Map 또는 Package ID가 Test 결과와 동일 단위로 연결되는지 확인한다. | [3,4,5] | process_step |
| CP/FT의 Bin, Parametric, Functional, Speed, Power 결과를 Lot/Die/Package 단위로 저장한다. | [4,5,8] | process_step |
| Burn-in과 Reliability Screening 조건, 시간, 온도, Fail 이력을 관리한다. | [6] | process_step |
| Retest, Correlation, Characterization 결과와 Tester/Socket 편차를 분석한다. | [7,8] | process_step |
| STDF, Wafer Map, Bin summary, 고객 Report와 CoC를 출하 데이터와 연결한다. | [9,10] | process_step |
| 고객별 Test Program, 수율 데이터, Failure data 접근권한을 분리한다. | [1,9,10] | industry |

### 9.4 control_points_detail_zh

| text | step_refs | scope |
|---|---|---|
| 验证Test Program、Revision、客户Spec、Device/Package条件的一致性。 | [1] | process_step |
| 确认Probe card、Socket、Load board、Handler、Tester组合与校准状态。 | [2,4,5] | process_step |
| 确认Incoming Wafer Map或Package ID是否与Test结果按同一单位连接。 | [3,4,5] | process_step |
| 按Lot/Die/Package保存CP/FT的Bin、Parametric、Functional、Speed、Power结果。 | [4,5,8] | process_step |
| 管理Burn-in与Reliability Screening条件、时间、温度、Fail履历。 | [6] | process_step |
| 分析Retest、Correlation、Characterization结果与Tester/Socket偏差。 | [7,8] | process_step |
| 将STDF、Wafer Map、Bin summary、客户Report与CoC连接到出货数据。 | [9,10] | process_step |
| 隔离客户별Test Program、Yield data、Failure data访问权限。 | [1,9,10] | industry |

```yaml
data_capture_points:
  - customer_lot_id
  - wafer_id
  - die_id
  - package_id
  - test_program_id
  - test_program_revision
  - tester_id
  - handler_id
  - probe_card_id
  - socket_id
  - load_board_id
  - test_temperature
  - bin_code
  - stdf_file
  - yield_summary
  - failure_code
  - retest_result
```

---

## 10. process_detail_v1.json 반영 지시

### 10.1 필수 반영

```text
server/data/step3/process_detail_v1.json
  industries.B.subs.logic_foundry
  industries.B.subs.memory_dram_nand
  industries.B.subs.analog_mixed
  industries.B.subs.power_discrete
  industries.B.subs.optical_sensor
  industries.B.subs.compound_semi
  industries.B.subs.assembly_packaging
  industries.B.subs.test
```

각 slug에 대해 다음 필드를 반드시 생성 또는 교체한다.

```json
{
  "label_ko": "",
  "label_zh": "",
  "label_en": "",
  "label_ja": "",
  "routing": "RT_REENTRANT 또는 RT_BATCH",
  "process_steps_detail_ko": [
    { "step": "", "note": "" }
  ],
  "process_steps_detail_zh": [
    { "step": "", "note": "" }
  ],
  "control_points_ko": [],
  "control_points_zh": [],
  "control_points_detail_ko": [
    { "text": "", "step_refs": [], "scope": "process_step" }
  ],
  "control_points_detail_zh": [
    { "text": "", "step_refs": [], "scope": "process_step" }
  ],
  "data_capture_points": []
}
```

### 10.2 주의사항

- B07/B08에는 FEOL, Lithography, Etch, BEOL 단계가 들어가면 안 된다.
- B01은 Lithography/Etch/Deposition/CMP를 독립 대단계로 두지 말고 FEOL/MOL/BEOL 각 단계의 note에 흡수한다.
- B02는 DRAM/NAND/HBM을 모두 포괄하되 Cell Array, 3D Stack, Redundancy/Repair, Die grade를 반드시 포함한다.
- B03은 Analog 특성상 Device Option, Passive, Trim, Characterization을 포함한다.
- B04는 Frontside/Backside 공정 분리를 명확히 한다.
- B05는 Optical stack, CFA, Microlens, Pixel defect map을 포함한다.
- B06은 Substrate/Epi/Mesa/Ohmic/Gate/Passivation/Backside 구조를 포함한다.

---

## 11. UI 수정 판단

| 항목 | 필요성 | 판단 |
|---|---|---|
| `process_analysis.py` 수정 | 낮음 | 스키마가 동일하면 수정 불필요 |
| `process_detail_v1.json` 수정 | 필수 | 본 데이터팩의 핵심 반영 대상 |
| RT 배지 숨김 | 선택 | 공정도에서 RT_REENTRANT/RT_BATCH가 방해되면 UI 옵션으로 숨김 |
| 다중 lane / 중첩 모듈 UI | 선택 | 1차는 note로 충분, 2차 고도화 시 FEOL/MOL/BEOL lane 지원 |
| Q2 라우팅 수정 | 불필요 | A1 Ch3는 Q1 slug 기준으로 고정 |

---

## 12. 우선순위

| 우선순위 | 대상 | 이유 |
|---|---|---|
| 1 | B07, B08 | 현재 Fab 16단계가 들어가면 명백히 잘못 보임 |
| 2 | B01, B06 | 도메인 경험자가 표현 편차를 가장 빨리 인지할 가능성 큼 |
| 3 | B02, B04, B05 | Fab 공통 구조 위에 세부소자 특화 모듈 필요 |
| 4 | B03 | Analog 특화 Option/Trim/특성검사 보완 |

---


---

## 부록 A. 2026년 산업 현황 반영 메모

```yaml
trend_reflection_ko:
  B01_logic_foundry:
    - AI/HPC 수요로 선단 Logic, Advanced Node, EUV/High-NA, Backside Power, GAA/FinFET 계열 공정의 중요성이 커지고 있다.
    - 공정 표현은 Lithography/Etch/Deposition/CMP를 일렬 나열하기보다 FEOL/MOL/BEOL Module 내부 Operation으로 표시해야 한다.
  B02_memory_dram_nand:
    - HBM, DDR5/LPDDR, 3D NAND 고단화와 AI 메모리 수요가 Memory Fab의 핵심 흐름이다.
    - Cell Array, Periphery, 3D Stack, Redundancy/Repair, Die Grade가 공정 표현에 반드시 반영되어야 한다.
  B03_analog_mixed:
    - PMIC, BCD, HV, RF, Sensor Interface 수요가 계속 유지되며, 특성검사·Trim·Device Option 관리가 중요하다.
    - Logic Fab와 동일한 전공정 문법이 아니라 Device Option과 Parametric Characterization 중심으로 표현해야 한다.
  B04_power_discrete:
    - 전기차, 재생에너지, 전력변환 수요로 SiC/GaN 및 전력소자 공정 중요성이 높다.
    - Epi/Drift Layer, Trench/Gate, Frontside/Backside Metallization, Wafer Probe가 표현의 중심이다.
  B05_optical_sensor:
    - 자동차, 모바일, 산업비전, AR/VR, AI Edge 장치에서 이미지센서와 광반도체 수요가 지속된다.
    - Pixel, Photodiode, CFA, Microlens, Optical Wafer Test와 Pixel Defect Map을 Fab 공정과 별도로 강조해야 한다.
  B06_compound_semi:
    - SiC/GaN 전력반도체, RF GaAs/GaN, InP 광소자 등 화합물 반도체가 고성장 영역이다.
    - Substrate/Epi/Mesa/Ohmic/Gate/Passivation/Backside 구조가 일반 CMOS Fab 문법보다 우선한다.
  B07_assembly_packaging:
    - AI/HPC 칩의 대형화, Chiplet, 2.5D/3D, Hybrid Bonding, HBM으로 Advanced Packaging 중요성이 크게 상승하고 있다.
    - FEOL/Lithography/Etch/BEOL 용어를 제거하고 Wafer Prep, Die Attach, Bonding, Mold, Singulation, Final Test 중심으로 표현해야 한다.
  B08_test:
    - 고성능·고복잡도 반도체 증가로 Probe Card, Socket, Load Board, Tester Correlation, STDF/수율 데이터 관리가 중요해지고 있다.
    - Test 산업은 제조 공정이 아니라 Test Program, Setup, Probe/FT, Burn-in, Bin, Report/Data Handoff 흐름으로 표현해야 한다.

trend_reflection_zh:
  B01_logic_foundry:
    - 受AI/HPC需求推动，先进Logic、Advanced Node、EUV/High-NA、Backside Power、GAA/FinFET相关工艺重要性上升。
    - 工艺表达不应把Lithography/Etch/Deposition/CMP简单线性排列，而应放入FEOL/MOL/BEOL模块内部。
  B02_memory_dram_nand:
    - HBM、DDR5/LPDDR、3D NAND高层数化与AI存储需求是Memory Fab的核心趋势。
    - Cell Array、Periphery、3D Stack、Redundancy/Repair、Die Grade必须反映在工艺表达中。
  B03_analog_mixed:
    - PMIC、BCD、HV、RF、Sensor Interface需求持续存在，参数测试、Trim、Device Option管理非常重要。
    - 不应使用与Logic Fab完全相同的前道语法，而应突出Device Option与Parametric Characterization。
  B04_power_discrete:
    - 电动汽车、可再生能源、电力转换需求推动SiC/GaN与功率器件工艺重要性提升。
    - Epi/Drift Layer、Trench/Gate、Frontside/Backside Metallization、Wafer Probe是表达核心。
  B05_optical_sensor:
    - 汽车、移动设备、工业视觉、AR/VR、AI Edge设备持续推动图像传感器与光半导体需求。
    - 应突出Pixel、Photodiode、CFA、Microlens、Optical Wafer Test和Pixel Defect Map。
  B06_compound_semi:
    - SiC/GaN功率半导体、RF GaAs/GaN、InP光器件等化合物半导体属于高增长领域。
    - Substrate/Epi/Mesa/Ohmic/Gate/Passivation/Backside结构优先于一般CMOS Fab表达。
  B07_assembly_packaging:
    - AI/HPC芯片大型化、Chiplet、2.5D/3D、Hybrid Bonding、HBM显著提升Advanced Packaging重要性。
    - 应删除FEOL/Lithography/Etch/BEOL表达，改为Wafer Prep、Die Attach、Bonding、Mold、Singulation、Final Test流程。
  B08_test:
    - 高性能、高复杂度半导体增加，使Probe Card、Socket、Load Board、Tester Correlation、STDF/Yield Data管理更加重要。
    - 测试产业应表达为Test Program、Setup、Probe/FT、Burn-in、Bin、Report/Data Handoff流程，而不是制造Fab流程。
```

## 부록 B. 반영 기준 요약

```yaml
runtime_validation_ko:
  - 본 데이터팩은 문서용 문법 설명이 아니라 A1 Ch3 런타임 반영을 목표로 한다.
  - slug별 `process_steps_detail_ko/zh`, `control_points_detail_ko/zh`, `data_capture_points`를 반드시 `process_detail_v1.json`에 반영해야 한다.
  - B07/B08은 기존 Fab 통합 16단계를 사용하면 안 된다.
  - 영어/일어 필드는 공백 유지가 원칙이다.
runtime_validation_zh:
  - 本数据包目标不是文档说明，而是A1 Ch3运行时数据反映。
  - 必须将各slug的 `process_steps_detail_ko/zh`、`control_points_detail_ko/zh`、`data_capture_points` 反映到 `process_detail_v1.json`。
  - B07/B08不得继续使用原Fab综合16阶段。
  - 英文/日文字段原则上保持空白。
```


## 13. 한 줄 요약

본 데이터팩은 기존 문법 MD를 A1 Ch3 런타임에 반영하기 위한 보완본이다. 핵심은 B01~B08의 `process_detail_v1.json`을 slug별로 직접 교체하고, 특히 B07/B08에서 Fab 통합 템플릿을 제거하여 Package/Test 고유 라우팅으로 바꾸는 것이다.