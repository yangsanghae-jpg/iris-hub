"""탭: 📦 데이터 — L4-K 시드 상태 (V2.6.2.4 한국어화 + 시각화)"""
from __future__ import annotations

import html
import streamlit as st

from src.measurements import measure

# ─── 카테고리별 색상 팔레트 ───────────────────────────────────────────
_PALETTE = {
    "source": "#5fa8ff", "entity": "#7ed6a3", "concept": "#c596ff",
    "human": "#5fa8ff", "ai": "#7ed6a3", "hybrid": "#c596ff",
    "folder_load": "#ffb86b",
    "bronze": "#cd7f32", "silver": "#c0c0c0", "gold": "#ffd166",
    "reference": "#5fa8ff", "secure": "#f08585",
    # 산업 (A~H + null)
    "A": "#5fa8ff", "B": "#7ed6a3", "C": "#ffb86b", "D": "#c596ff",
    "E": "#f08585", "F": "#ffd166", "G": "#a0e7e5", "H": "#fbb1bd",
    "(null)": "#666",
}
# 카테고리 한글 라벨 — 오역 우려 시 한국어(영어) 표기
_LABEL = {
    "source": "원본",
    "entity": "엔티티(entity)",
    "concept": "개념(concept)",
    "human": "사람",
    "ai": "AI",
    "hybrid": "혼합(hybrid)",
    "folder_load": "폴더로딩(folder_load)",
    "bronze": "bronze (동)",
    "silver": "silver (은)",
    "gold": "gold (금)",
    "reference": "참조(reference)",
    "secure": "보안(secure)",
}

_CSS = """
<style>
.inv-sec { font-size:0.78em; font-weight:600; color:#888;
           letter-spacing:.5px; margin:14px 0 6px 0;
           text-transform:none; }
.inv-bar {
  display:flex; height:26px; border-radius:6px; overflow:hidden;
  background:rgba(120,120,120,0.10); border:1px solid rgba(120,120,120,0.18);
}
.inv-bar-seg {
  height:100%; display:flex; align-items:center; justify-content:flex-start;
  padding:0 9px; color:#fff; font-size:0.78em; font-weight:500;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  text-shadow: 0 1px 1px rgba(0,0,0,0.45);
}
.inv-zeros { font-size:0.78em; color:#888; margin-top:5px; }
.inv-zeros span { margin-right:10px; }

.inv-prog-wrap {
  position:relative; height:28px; background:rgba(120,120,120,0.10);
  border:1px solid rgba(120,120,120,0.18); border-radius:6px; overflow:hidden;
}
.inv-prog-fill {
  position:absolute; left:0; top:0; bottom:0;
  background: linear-gradient(90deg, #7ed6a3 0%, #5fa8ff 100%);
}
.inv-prog-text {
  position:absolute; inset:0; display:flex; align-items:center;
  justify-content:center; font-size:0.85em; font-weight:600;
  color:#fff; text-shadow: 0 1px 2px rgba(0,0,0,0.6);
}

.inv-meta-line { font-size:0.82em; color:#888; }
.inv-meta-line code { font-size:0.95em; padding:0 4px; background:rgba(120,120,120,0.12);
                      border-radius:3px; color:#bbb; }
</style>
"""


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _stacked_bar(items: list[tuple[str, int]]) -> str:
    """100% 가로 stacked bar — 0인 카테고리는 zero-row로 분리."""
    nonzero = [(k, v) for k, v in items if v > 0]
    zeros = [k for k, v in items if v == 0]
    total = sum(v for _, v in nonzero) or 1

    segs = []
    for k, v in nonzero:
        pct = v / total * 100
        color = _PALETTE.get(k, "#888")
        label_ko = _LABEL.get(k, k or "(null)")
        # 작은 segment는 카운트만, 큰 segment는 라벨+카운트+%
        if pct >= 12:
            inner = f"{html.escape(label_ko)} <b>{v:,}</b> · {pct:.0f}%"
        elif pct >= 5:
            inner = f"<b>{v:,}</b>"
        else:
            inner = "·"
        segs.append(
            f"<div class='inv-bar-seg' "
            f"style='flex:{v} 0 0; background:{color};' "
            f"title='{html.escape(label_ko)}: {v:,} ({pct:.1f}%)'>{inner}</div>"
        )

    bar = f"<div class='inv-bar'>{''.join(segs)}</div>" if nonzero else \
          "<div class='inv-bar'><div class='inv-bar-seg' style='flex:1; color:#888;'>(데이터 없음)</div></div>"

    if zeros:
        zlabels = " ".join(
            f"<span>○ {html.escape(_LABEL.get(k, k))}</span>" for k in zeros
        )
        bar += f"<div class='inv-zeros'>{zlabels}</div>"
    return bar


def _progress(numer: int, denom: int, label: str) -> str:
    pct = (numer / denom * 100) if denom else 0
    return (
        f"<div class='inv-prog-wrap'>"
        f"<div class='inv-prog-fill' style='width:{pct:.1f}%;'></div>"
        f"<div class='inv-prog-text'>{label} · <b>{numer:,}</b> / {denom:,} "
        f"({pct:.1f}%)</div>"
        f"</div>"
    )


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    m = measure()

    if not m.db_exists:
        st.error(f"`_index.db`에 접근 불가: {m.db_path}")
        return

    # ─── 핵심 지표 4개 ────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("문서 (documents)", _fmt_int(m.documents_total),
              f"{m.documents_gap:+,}" if m.documents_gap else None,
              delta_color="off")
    c2.metric("청크 (chunks)", _fmt_int(m.chunks_total))
    c3.metric("검색인덱스 (documents_fts)", _fmt_int(m.fts_total),
              f"{m.fts_gap:+,}" if m.fts_gap else None,
              delta_color="off")
    c4.metric("엔티티 별칭 (entity_aliases)", _fmt_int(m.aliases_total))
    st.caption("격차 = 현재 − 알다 운영 입증값 (V2.5.2 §6.1)")

    # ─── 분포 3개 (stacked bar) ──────────────────────────────────────
    # Kind
    st.markdown("<div class='inv-sec'>📦 종류 (Kind)</div>", unsafe_allow_html=True)
    kind_known = ["source", "entity", "concept"]
    kind_items = [(k, m.kind_dist.get(k, 0)) for k in kind_known]
    kind_items += [(k, v) for k, v in m.kind_dist.items() if k not in kind_known]
    st.markdown(_stacked_bar(kind_items), unsafe_allow_html=True)

    # Origin
    st.markdown("<div class='inv-sec'>🌱 출처 (Origin)</div>", unsafe_allow_html=True)
    origin_known = ["human", "ai", "hybrid", "folder_load"]
    origin_items = [(k, m.origin_dist.get(k, 0)) for k in origin_known]
    origin_items += [(k, v) for k, v in m.origin_dist.items() if k not in origin_known]
    st.markdown(_stacked_bar(origin_items), unsafe_allow_html=True)

    # Lane
    st.markdown("<div class='inv-sec'>🛤 레인 (Lane)</div>", unsafe_allow_html=True)
    lane_known = ["bronze", "silver", "gold", "reference", "secure"]
    lane_items = [(k, m.lane_dist.get(k, 0)) for k in lane_known]
    lane_items += [(k, v) for k, v in m.lane_dist.items() if k not in lane_known]
    st.markdown(_stacked_bar(lane_items), unsafe_allow_html=True)

    # ─── K3 매트릭스 + 산업 분포 ─────────────────────────────────────
    st.markdown(
        "<div class='inv-sec'>🎯 K3 매트릭스 — 산업·영역(industry·area) 동시 부여 비율</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        _progress(m.matrix_keyed, m.documents_total, "분류 완료"),
        unsafe_allow_html=True,
    )

    if m.industry_dist:
        st.markdown(
            "<div class='inv-sec'>🏭 산업 (industry) 분포</div>",
            unsafe_allow_html=True,
        )
        # industry 정렬 — null 맨 뒤
        items = sorted(
            m.industry_dist.items(),
            key=lambda x: (x[0] in ("(null)", None, ""), x[0] or ""),
        )
        items_norm = [(k or "(null)", v) for k, v in items]
        st.markdown(_stacked_bar(items_norm), unsafe_allow_html=True)

    # ─── K2 분석 진척 ────────────────────────────────────────────────
    try:
        from src import document_meta as dm
        ms = dm.stats()
        if ms["total"] > 0:
            st.markdown(
                "<div class='inv-sec'>🤖 K2 분석 진척 (document_meta)</div>",
                unsafe_allow_html=True,
            )
            llm_n = ms["total"] - ms["fallback"]
            st.markdown(
                _stacked_bar([
                    ("LLM 분석", llm_n),
                    ("규칙 기반(fallback)", ms["fallback"]),
                ]),
                unsafe_allow_html=True,
            )
            if ms["by_classifier"]:
                ver_str = " · ".join(
                    f"`{v}` <b>{n:,}</b>" for v, n in sorted(ms["by_classifier"].items())
                )
                st.markdown(
                    f"<div style='font-size:0.78em;color:#888;margin-top:5px;'>"
                    f"분류기 버전(classifier_version): {ver_str}</div>",
                    unsafe_allow_html=True,
                )
    except Exception:
        pass

    # ─── 메타데이터 한 줄 ────────────────────────────────────────────
    raw_ts = (m.last_ingest_raw or "—").replace("T", " ")[:16]
    ref_ts = (m.last_ingest_ref or "—").replace("T", " ")[:16]
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='inv-meta-line'>"
        f"스키마(schema) <code>{m.schema_version}</code> · "
        f"무결성(integrity) <code>{m.integrity}</code> · "
        f"DB 크기 <code>{m.db_size / 1024:.0f} KB</code> · "
        f"마지막 인제스트(ingest) — 원본(raw) <code>{raw_ts}</code> · "
        f"참조(ref) <code>{ref_ts}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ─── 재처리 ──────────────────────────────────────────────────────
    st.divider()
    with st.expander("🔄 재처리 (raw → 인제스트·분류·검색인덱스)", expanded=False):
        st.caption(
            "원본(raw) 디스크 자료를 일괄 인제스트·분류. 사람이 박은 시드 분류는 *덮어쓰기*. "
            "외부응답 격납소(_external/) 하위도 포함."
        )

        col_tog, col_health = st.columns([1, 2])
        with col_tog:
            use_k2 = st.toggle(
                "🤖 K2 분석 (deep LLM)", value=True, key="rep_use_k2",
                help="자료당 5~30초 — 정확하지만 느림"
            )
        with col_health:
            if use_k2:
                try:
                    from src import llm
                    statuses = llm.health_all()
                    parts = []
                    for role, h in statuses.items():
                        icon = "🟢" if h.get("ok") else "🔴"
                        parts.append(f"{icon} {role}: <code>{h['model']}</code>")
                    st.markdown(
                        "<div style='font-size:0.82em;color:#aaa;'>"
                        + "  ·  ".join(parts) + "</div>",
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.caption(f"⚠️ 모델 점검 실패: {e}")

        b1, b2, b3 = st.columns(3)
        run_all  = b1.button("📂 전체 원본",   use_container_width=True, key="rep_all")
        run_ext  = b2.button("🌐 외부응답만",  use_container_width=True, key="rep_ext")
        run_null = b3.button("🕳 빈칸만 채움", use_container_width=True, key="rep_null",
                             help="이미 박힌 분류는 유지, NULL인 자리만 채움")

        if run_all or run_ext or run_null:
            from src.reprocess import reprocess
            scope = "external" if run_ext else "all"
            only_null = bool(run_null)

            with st.spinner(
                f"재처리 중… 범위={scope} · K2={'켬' if use_k2 else '끔'}"
            ):
                r = reprocess(scope=scope, only_null=only_null, use_k2=use_k2)

            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("스캔", r.scanned)
            rc2.metric("저장 (upsert)", r.upserted)
            rc3.metric("분류", r.classified)
            rc4.metric("빈 청크 건너뜀", r.skipped_empty)

            if r.fts_counts:
                st.caption(f"검색인덱스(FTS): {r.fts_counts}")

            if r.errors:
                with st.expander(f"⚠️ 오류 {len(r.errors)}건", expanded=True):
                    for name, err in r.errors[:20]:
                        st.write(f"- `{name}` — {err}")
            else:
                st.success(
                    f"✅ {r.upserted:,}건 저장 · {r.classified:,}건 분류 갱신"
                )

    # ─── Obsidian 동기화 ─────────────────────────────────────────────
    with st.expander("📚 Obsidian 동기화 (iris-mirror)", expanded=False):
        from src import obsidian_sync as osync

        # mirror 현황 조회 — 디렉토리 존재 + .md 카운트 + 최근 sync 시각
        existing = 0
        latest_sync: str | None = None
        if osync.MIRROR_ROOT.exists():
            mds = list(osync.MIRROR_ROOT.glob("*.md"))
            # README.md 제외
            existing = sum(1 for p in mds if p.name != "README.md")
            # mtime 가장 최근 .md의 frontmatter에서 iris_synced_at 추출
            data_mds = [p for p in mds if p.name != "README.md"]
            if data_mds:
                newest = max(data_mds, key=lambda p: p.stat().st_mtime)
                latest_sync = osync._read_synced_at(newest)

        st.caption(
            f"📂 위치: `{osync.MIRROR_ROOT}` · "
            f"현재 박힌 mirror `.md` **{existing:,}**건 · "
            f"마지막 sync: <code>{(latest_sync or '—').replace('T',' ')[:16]}</code>",
            unsafe_allow_html=True,
        )
        st.caption(
            "💡 **단방향 export** — 정본은 SQLite, Obsidian은 거울. "
            "사용자 편집은 다음 sync에 *덮어씌워짐*. "
            "기록은 격납소 밖에서 wikilink로 참조."
        )

        sb1, sb2 = st.columns(2)
        sync_changed = sb1.button(
            "🔄 변경분만 동기화",
            use_container_width=True, key="osync_changed",
            help="K2 재분석 또는 신규 자료만 다시 씀 (증분, 빠름)",
        )
        sync_force = sb2.button(
            "🔁 전체 다시 쓰기",
            use_container_width=True, key="osync_force",
            help="변경 여부 무시하고 모든 자료 .md를 다시 씀 (느림)",
        )

        if sync_changed or sync_force:
            with st.spinner(
                f"Obsidian mirror 동기화 중… "
                f"{'전체 강제' if sync_force else '변경분'}"
            ):
                sr = osync.sync_all(force=bool(sync_force))

            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("스캔", sr.scanned)
            sc2.metric("작성", sr.written)
            sc3.metric("변경 없음 (skip)", sr.skipped)
            sc4.metric("오류", len(sr.errors))

            if sr.errors:
                with st.expander(f"⚠️ 오류 {len(sr.errors)}건", expanded=True):
                    for doc_id, err in sr.errors[:20]:
                        st.write(f"- `{doc_id}` — {err}")
            else:
                if sr.written > 0:
                    st.success(
                        f"✅ {sr.written:,}건 작성 · {sr.skipped:,}건 변경 없음"
                    )
                else:
                    st.info(
                        f"🟢 모든 자료가 최신 상태 — {sr.skipped:,}건 skip"
                    )
