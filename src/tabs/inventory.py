"""탭: 📦 데이터 — L4-K 시드 상태 (V2.6.2.2 압축 리디자인)"""
from __future__ import annotations

import streamlit as st

from src.measurements import measure

_CSS = """
<style>
.inv-dist-row { display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 8px 0; }
.inv-chip {
  background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
  border-radius:12px; padding:2px 10px; font-size:0.83em; white-space:nowrap;
}
.inv-chip b { color:#e0e0e0; }
.inv-chip.dim { opacity:0.55; }
.inv-sec { font-size:0.8em; text-transform:uppercase; letter-spacing:.5px;
           color:#888; margin:12px 0 4px 0; }
</style>
"""


def _chips(items: list[tuple[str, int]], highlight_zero: bool = True) -> str:
    parts = []
    for k, v in items:
        cls = "inv-chip" + (" dim" if (highlight_zero and v == 0) else "")
        parts.append(f"<span class='{cls}'>{k or '(null)'} <b>{v:,}</b></span>")
    return "<div class='inv-dist-row'>" + "".join(parts) + "</div>"


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    m = measure()

    if not m.db_exists:
        st.error(f"`_index.db`에 접근 불가: {m.db_path}")
        return

    # ─── 핵심 4개 metric ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("documents", f"{m.documents_total:,}",
              f"{m.documents_gap:+,}" if m.documents_gap else None, delta_color="off")
    c2.metric("chunks", f"{m.chunks_total:,}")
    c3.metric("documents_fts", f"{m.fts_total:,}",
              f"{m.fts_gap:+,}" if m.fts_gap else None, delta_color="off")
    c4.metric("entity_aliases", f"{m.aliases_total:,}")
    st.caption("격차 = 현재 − 알다 운영 입증값 (V2.5.2 §6.1)")

    # ─── 분포 3열 (chips) ─────────────────────────────────────────────
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("<div class='inv-sec'>Kind</div>", unsafe_allow_html=True)
        known = [("source", m.kind_dist.get("source", 0)),
                 ("entity", m.kind_dist.get("entity", 0)),
                 ("concept", m.kind_dist.get("concept", 0))]
        extra = [(k, v) for k, v in m.kind_dist.items() if k not in ("source","entity","concept")]
        st.markdown(_chips(known + extra), unsafe_allow_html=True)
    with d2:
        st.markdown("<div class='inv-sec'>Origin</div>", unsafe_allow_html=True)
        known = [("human", m.origin_dist.get("human", 0)),
                 ("ai", m.origin_dist.get("ai", 0)),
                 ("hybrid", m.origin_dist.get("hybrid", 0))]
        extra = [(k, v) for k, v in m.origin_dist.items() if k not in ("human","ai","hybrid")]
        st.markdown(_chips(known + extra), unsafe_allow_html=True)
    with d3:
        st.markdown("<div class='inv-sec'>Lane</div>", unsafe_allow_html=True)
        known = [("bronze", m.lane_dist.get("bronze", 0)),
                 ("silver", m.lane_dist.get("silver", 0)),
                 ("gold", m.lane_dist.get("gold", 0)),
                 ("ref", m.lane_dist.get("reference", 0)),
                 ("secure", m.lane_dist.get("secure", 0))]
        extra = [(k, v) for k, v in m.lane_dist.items()
                 if k not in ("bronze","silver","gold","reference","secure")]
        st.markdown(_chips(known + extra), unsafe_allow_html=True)

    # ─── K3 + K2 메타 한 줄 ──────────────────────────────────────────
    st.divider()
    ka, kb = st.columns([1, 2])
    with ka:
        st.metric("🎯 K3 matrix", f"{m.matrix_keyed} / {m.documents_total}",
                  help="industry+area 동시 부여된 documents")
    with kb:
        if m.industry_dist:
            ind_line = " · ".join(
                f"{k or '(null)'}:{n}" for k, n in sorted(m.industry_dist.items())
            )
            st.markdown(f"<div class='inv-sec'>Industry 분포</div>"
                        f"<div style='font-size:0.9em;color:#ccc;padding-top:6px;'>{ind_line}</div>",
                        unsafe_allow_html=True)

    # K2 분석 진척 인라인 (document_meta 있을 때만)
    try:
        from src import document_meta as dm
        ms = dm.stats()
        if ms["total"] > 0:
            llm_n = ms["total"] - ms["fallback"]
            ver_str = " · ".join(
                f"`{v}`:{n}" for v, n in sorted(ms["by_classifier"].items())
            ) if ms["by_classifier"] else "—"
            st.caption(
                f"🤖 K2 meta: **{ms['total']}** 건 · LLM {llm_n} · fallback {ms['fallback']} · {ver_str}"
            )
    except Exception:
        pass

    # ─── 메타데이터 한 줄 ────────────────────────────────────────────
    raw_ts = (m.last_ingest_raw or "—").replace("T", " ")[:16]
    ref_ts = (m.last_ingest_ref or "—").replace("T", " ")[:16]
    st.caption(
        f"schema `{m.schema_version}` · integrity `{m.integrity}` · "
        f"{m.db_size / 1024:.0f} KB · "
        f"raw {raw_ts} · ref {ref_ts}"
    )

    # ─── 재처리 ──────────────────────────────────────────────────────
    st.divider()
    with st.expander("🔄 재처리 (raw → K1·K2·K3·FTS)", expanded=False):
        st.caption(
            "raw 디스크 자료를 일괄 인제스트·분류. 사람이 박은 시드 분류는 *덮어쓰기*. "
            "_external/ 하위 포함."
        )

        # K2 토글 + 모델 상태를 같은 행에
        col_tog, col_health = st.columns([1, 2])
        with col_tog:
            use_k2 = st.toggle("🤖 K2 LLM", value=True, key="rep_use_k2",
                               help="deep LLM 본문 분석 — 정확하나 자료당 5~30초")
        with col_health:
            if use_k2:
                try:
                    from src import llm
                    statuses = llm.health_all()
                    parts = []
                    for role, h in statuses.items():
                        icon = "🟢" if h.get("ok") else "🔴"
                        parts.append(f"{icon} `{h['model']}`")
                    st.caption("  ·  ".join(parts))
                except Exception as e:
                    st.caption(f"⚠️ {e}")

        # 버튼 3개
        b1, b2, b3 = st.columns(3)
        run_all  = b1.button("전체 raw",    use_container_width=True, key="rep_all")
        run_ext  = b2.button("외부응답만",  use_container_width=True, key="rep_ext")
        run_null = b3.button("NULL만 채움", use_container_width=True, key="rep_null",
                             help="이미 박힌 분류는 유지, NULL인 것만 채움")

        if run_all or run_ext or run_null:
            from src.reprocess import reprocess
            scope = "external" if run_ext else "all"
            only_null = bool(run_null)

            with st.spinner(f"재처리 중… scope={scope} K2={'on' if use_k2 else 'off'}"):
                r = reprocess(scope=scope, only_null=only_null, use_k2=use_k2)

            # 결과 컴팩트
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("스캔", r.scanned)
            rc2.metric("upsert", r.upserted)
            rc3.metric("분류", r.classified)
            rc4.metric("빈 chunk", r.skipped_empty)

            if r.fts_counts:
                st.caption(f"FTS {r.fts_counts}")

            if r.errors:
                with st.expander(f"⚠️ 오류 {len(r.errors)}건", expanded=True):
                    for name, err in r.errors[:20]:
                        st.write(f"- `{name}` — {err}")
            else:
                st.success(f"✅ {r.upserted}건 박힘 · {r.classified}건 분류 갱신")
