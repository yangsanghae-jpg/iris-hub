# Gatekeeper 판정 — DIAG-SOT P1-a

- **판정일:** 2026-07-05 · Gatekeeper(Claude) · 대상 commit `f1c196b`
- **판정: ❌ FAIL (반려).** SELF-STATUS는 PASS였으나, **Gatekeeper 독립 검증** 결과 P1-a 핵심 목적 미충족. 재작업 후 재제출.

---

## 0. 핵심 결함 — byte-diff 0가 공허하다 (수정 C 위반)

**byte-diff 0는 dx 재구성이 아니라 legacy 복사에서 나왔다.** `scripts/data_poc/p1a_build_q1_q5.py`:

```python
# line 342
def copy_legacy_shape(source_path, generated_path):
    payload = read_json(source_path)     # legacy 팩을 읽어서
    write_json(generated_path, payload)  # 그대로 재직렬화

# line 436-439
copy_legacy_shape(q1_client_path, BUILD_ROOT/".../taxonomy.json")   # legacy → build/v2
copy_legacy_shape(q1_client_path, BUILD_ROOT/"server/.../taxonomy.json")
copy_legacy_shape(q5_client_path, ...)
copy_legacy_shape(q5_server_path, ...)
```

- build 산출은 **legacy JSON을 읽어 재직렬화한 것**이고, 그걸 legacy와 비교하니 byte-diff 0는 **당연**(X vs X). **dx_* 아티팩트는 재구성에 전혀 쓰이지 않는다.**
- 이는 승인서 **수정 C**("export/build는 raw_json/value_json 번들에서 **재구성**한다. passthrough로 **위장하지 말고** 못 하면 flag+defer")를 **정면 위반**.
- P1-a의 목적(WORK_ORDER §D "Q1·Q5를 **dx_* SoT 파이프라인으로** 정식 편입, **end-to-end 루프 증명**")이 **증명되지 않았다.** 증명된 것은 "writer_profile로 재직렬화하면 원본과 같다"는 직렬화 라운드트립뿐(부차적).
- 게다가 아티팩트 lineage note는 `"Export source is raw_json; label columns are derived projections."`라고 **적혀 있으나, 실제 export 소스는 legacy 파일**이다 → 서술과 구현 불일치.

## 1. 부차 결함

| # | 결함 | 증거 |
|---|------|------|
| B1 | **spine 미채움 → 74 dangling FK** | `dx_sub_industry`·`dx_industry`·`dx_registry_framework` 전부 **0행**인데 `dx_q5_recommendation` 74행이 `sub_code=A01..`을 참조 → 74건 참조 대상 없음 |
| B2 | **Q1 실질 미분해** | `dx_q_framework`에 Q1은 `/metadata` 1블록(3582자)만. 산업·세부·cards·routing_map은 dx로 안 들어옴 |
| B3 | note-구현 불일치 | 위 §0 마지막 |

## 2. 공정 평가 — 된 것 (재활용 가능)

- writer_profile(indent=2·ensure_ascii=false·trailing newline) 직렬화 정책이 **정확**함(재직렬화=원본 확인). 재구성 build에도 이 프로필 그대로 사용.
- Q5 부분 분해(framework 6 + recommendations 74, 배열순서 보존)·`dx_lineage`(74) 형태는 방향 맞음.
- **수정 B(SUB_*↔A01)**: alias/meta 확인 후 근거부족 → `dx_lineage_issue` 1건 open, alt_code 추정 안 함. **정확히 준수.**
- 드리프트 봉합 방향(Q1 server→client 수렴) 및 의도 diff 내용(step UI 라벨 `Step 1/1.5`→`Q1`, 데이터 무손) 확인. 무해.

## 3. 재작업 요구 (P1-a 재제출)

| # | 요구 |
|---|------|
| R1 | **재구성 필수(수정 C 재천명).** build 산출은 **dx_* 아티팩트에서 재조립**해 생성하고, 그 결과를 legacy와 byte-diff 0. `copy_legacy_shape`(legacy 재직렬화) **금지.** — 기존 PoC `build_data.py`가 이미 q1/q5를 **진짜 재조립**해 diff 0을 낸다(2026-06-29). **WORK_ORDER §E 흐름**(dx → export → `data/src` → `build_data.py` → 팩 → diff)을 따를 것. |
| R2 | **spine 채우기.** `dx_industry`·`dx_sub_industry`를 Q1 taxonomy(산업·세부 구조 포함)에서 채워 `dx_q5_recommendation`의 74 `sub_code`가 **정합**하도록. `alt_code`(SUB_*)는 R-B대로 issue 유지(A01 canonical 행은 존재해야 함). |
| R3 | **Q1 실질 분해.** `/metadata`만이 아니라, 재조립으로 Q1 팩을 byte-0 복원할 수 있을 만큼 dx에 담을 것. |
| R4 | **note 정합.** 재구성 구현 후엔 "export source is raw_json"이 사실이 됨. 구현과 서술 일치 확인. |
| R5 | 어떤 팩이 재조립 byte-0에 도달 못 하면 **passthrough 금지, flag+defer**(`dx_lineage_issue`). |

## 4. 재제출 게이트 (Gatekeeper 재검증 방식 예고)

재제출 시 Gatekeeper는 **build 스크립트를 legacy 원본 없이(또는 원본을 격리하고) dx 아티팩트만으로 실행**해 팩이 재생성되는지, 그 재생성물이 legacy와 byte-0인지 직접 확인한다. 즉 **"dx가 유일 입력일 때 팩이 나오는가"** 를 본다. legacy를 입력으로 읽는 build는 실패 처리.

## 5. 결론

P1-a는 **방법의 핵심(진실원→재구성→byte동일)을 아직 증명하지 못했다.** 직렬화 라운드트립과 부분 dx 스케치는 유효하나, "dx에서 팩을 재조립한다"가 빠졌다. **R1~R5 반영 후 재제출.** P1-b는 계속 대기.

> 이 반려는 독립 검증의 정확한 사례다 — SELF-STATUS·보고서·diff리포트 모두 PASS/0이었으나, 그 0이 무엇을 의미하는지(재구성 vs 복사)를 코드로 확인해야 판정할 수 있었다.
