"""탭 2: 데이터 — L4-K 시드 측정값 + 알다 격차 (V2.5.3 §3.3)"""
from __future__ import annotations

import streamlit as st

from src.measurements import measure


def _delta(gap: int) -> str:
    return f"{gap:+,}" if gap else "0"


def render() -> None:
    st.markdown("## 📦 L4-K 시드 상태")
    m = measure()

    if not m.db_exists:
        st.error(f"`_index.db`에 접근 불가: {m.db_path}")
        return

    # 핵심 카드 4개
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("documents", f"{m.documents_total:,}", _delta(m.documents_gap), delta_color="off")
    c2.metric("chunks", f"{m.chunks_total:,}")
    c3.metric("documents_fts", f"{m.fts_total:,}", _delta(m.fts_gap), delta_color="off")
    c4.metric("entity_aliases", f"{m.aliases_total:,}")

    st.caption("격차 = 현재 IRIS 값 − 알다 운영 입증값 (V2.5.2 §6.1)")

    st.divider()

    # 분포 3개
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Kind**")
        for k in ("source", "entity", "concept"):
            st.write(f"- {k}: **{m.kind_dist.get(k, 0)}**")
    with c2:
        st.markdown("**Origin**")
        for k in ("human", "ai", "hybrid"):
            st.write(f"- {k}: **{m.origin_dist.get(k, 0)}**")
    with c3:
        st.markdown("**Lane**")
        for k in ("bronze", "silver", "gold", "secure"):
            st.write(f"- {k}: **{m.lane_dist.get(k, 0)}**")

    st.divider()

    # K3 분류 진척
    st.markdown("**🎯 K3 매트릭스 키 부여**")
    c1, c2 = st.columns(2)
    c1.metric("industry+area 부여 docs", f"{m.matrix_keyed} / {m.documents_total}")
    if m.industry_dist:
        with c2:
            for k, n in sorted(m.industry_dist.items()):
                st.write(f"- industry={k}: **{n}**")

    st.divider()

    # 메타데이터
    st.markdown("**메타데이터**")
    c1, c2, c3 = st.columns(3)
    c1.write(f"📦 schema_version: **{m.schema_version}**")
    c2.write(f"🛡 integrity: **{m.integrity}**")
    c3.write(f"💾 db_size: **{m.db_size:,} bytes** ({m.db_size / 1024:.1f} KB)")

    st.write(f"🕐 last ingest (raw): `{m.last_ingest_raw}`")
    st.write(f"🕐 last ingest (ref): `{m.last_ingest_ref}`")

    # ─── 🔄 재처리 (K1~K3) ──────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔄 재처리 (raw → documents/chunks/FTS + classify)")
    st.caption(
        "raw 디스크 자료를 일괄로 인제스트·분류. 사람이 박은 시드 분류는 *덮어쓰기*. "
        "외부응답 격납소(_external/) 하위도 포함."
    )

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        run_all = st.button("🔄 전체 raw", use_container_width=True, key="rep_all")
    with rc2:
        run_ext = st.button("🔄 외부응답만", use_container_width=True, key="rep_ext")
    with rc3:
        run_null = st.button("🔄 NULL만 채움", use_container_width=True, key="rep_null",
                             help="이미 박힌 분류는 유지, NULL인 것만 추천값으로 채움")

    if run_all or run_ext or run_null:
        from src.reprocess import reprocess
        scope = "external" if run_ext else "all"
        only_null = run_null
        if run_null:
            scope = "all"

        with st.spinner(f"재처리 중 (scope={scope}, only_null={only_null})..."):
            r = reprocess(scope=scope, only_null=only_null)

        # 결과 카드
        rr1, rr2, rr3, rr4 = st.columns(4)
        rr1.metric("스캔", r.scanned)
        rr2.metric("upsert", r.upserted)
        rr3.metric("분류", r.classified)
        rr4.metric("빈 chunk", r.skipped_empty)

        if r.fts_counts:
            st.caption(f"FTS: {r.fts_counts}")

        if r.errors:
            with st.expander(f"⚠️ 오류 {len(r.errors)}건", expanded=True):
                for name, err in r.errors[:20]:
                    st.write(f"- `{name}` — {err}")
        else:
            st.success(f"✅ 완료 — {r.upserted}건 박힘 / {r.classified}건 분류 갱신")

        st.caption("💡 재처리 후 카드 숫자가 바뀌었는지 위에서 확인 (페이지 재로드)")
