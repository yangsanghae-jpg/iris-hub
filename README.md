# iris-hub

진도 점검 콘솔 (V2.5.3 사양). Streamlit 단일 사용자, 포트 8765.

## 무엇

알다 LLM Wiki v0.10.1 시각 디자인을 채택하되 내용물은 *진도 점검*. V2.5.1 Phase 0~5가 어디까지 왔는지, L4-K 시드(documents/chunks/fts) 측정값이 얼마인지, 다음 게이트가 무엇인지를 한 화면에 보인다. 운영 콘솔이 아니다.

## 가동

```bash
~/iris-local/venv/iris-hub/bin/streamlit run app.py \
    --server.port 8765 --server.address 127.0.0.1
```

브라우저: http://127.0.0.1:8765

## 사양

- [V2.5.3 부록](../docs/system/IRIS_V2.5.3_iris_hub_design_freeze_2026-06-05.md) — 본 콘솔 설계 동결
- [V2.5.3.1 부록](../docs/system/IRIS_V2.5.3.1_m2_m5_parity_2026-06-05.md) — M2/M5 동등 정책

## Phase 마킹 (CLI)

```bash
# 완료 마킹
python -m scripts.mark_phase done --version V2.6 --phase 1 \
    --note "001+002 적용, 5건 ingest"

# 진행 시작
python -m scripts.mark_phase start --version V2.6 --phase 2

# 우회 처리
python -m scripts.mark_phase skip --version V2.5 --phase 0.5 \
    --reason "m2-venv"
```

UI 마킹: 진척 탭의 각 Phase 행 옆 ⋮ 메뉴 (Streamlit 버튼).
