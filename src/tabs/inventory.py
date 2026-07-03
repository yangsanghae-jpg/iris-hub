"""탭: 📦 데이터 — L4-K 시드 상태 (V2.6.2.4 한국어화 + 시각화)"""
from __future__ import annotations

import html
import streamlit as st

from src.store import vault as store_vault
from src.ui_kit import (
    hub_bar_rows,
    hub_key_value_rows,
    hub_kpi_grid,
    hub_pagebar,
    hub_panel,
    hub_two_col,
)

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
.inv-meta-line {
  margin-top:10px;
  padding:10px 12px;
  border:1px solid rgba(47,128,196,0.14);
  border-radius:11px;
  background:rgba(47,128,196,0.045);
  font-size:0.82rem;
  line-height:1.5;
  color:#475467;
}
.inv-meta-line code {
  font-size:0.88rem;
  padding:1px 5px;
  background:rgba(47,128,196,0.08);
  border:1px solid rgba(47,128,196,0.12);
  border-radius:5px;
  color:#344054;
}
.inv-split-body {
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
}
.inv-mini-title {
  margin-bottom:8px;
  font-size:0.72rem;
  font-weight:850;
  color:#2f80c4;
  letter-spacing:0.04em;
  text-transform:uppercase;
}
.inv-note-stack {
  display:grid;
  gap:8px;
}
.inv-note-row {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  padding:9px 10px;
  border:1px solid rgba(47,128,196,0.12);
  border-radius:10px;
  background:linear-gradient(180deg, #ffffff 0%, #f9fbfd 100%);
  color:#475467;
  font-size:0.8rem;
}
.inv-note-row strong {
  color:#172033;
  font-weight:800;
  white-space:nowrap;
}
.hub-pagebar {
  min-height:82px;
  overflow:visible !important;
  margin-top:10px !important;
  margin-bottom:14px !important;
  padding-top:16px !important;
  padding-bottom:16px !important;
  border-color:rgba(47,128,196,0.18) !important;
  background:linear-gradient(135deg, #ffffff 0%, #f7fbff 100%) !important;
  box-shadow:0 10px 28px rgba(16,24,40,0.055);
}
.hub-pagebar-title {
  font-size:1.32rem !important;
  line-height:1.28 !important;
  color:#101828 !important;
}
.hub-pagebar-desc {
  line-height:1.5 !important;
  overflow:visible !important;
}
.hub-pagebar-title-row {
  align-items:center !important;
  min-height:28px;
}
.hub-pill {
  border:1px solid rgba(18,183,106,0.18);
  box-shadow:0 4px 10px rgba(18,183,106,0.08);
}
.hub-kpi-card,
.hub-panel {
  border-color:rgba(47,128,196,0.16) !important;
  box-shadow:0 8px 22px rgba(16,24,40,0.045);
}
.hub-kpi-card {
  background:linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%) !important;
}
.hub-panel {
  background:linear-gradient(180deg, #ffffff 0%, #fbfdff 100%) !important;
}
.hub-panel-head {
  background:rgba(47,128,196,0.035);
}
.hub-panel-title {
  color:#172033 !important;
  letter-spacing:-0.01em;
}
.hub-bar {
  height:30px !important;
  border-radius:10px !important;
}
.hub-bar-seg {
  font-size:0.75rem !important;
  font-weight:800 !important;
}
.hub-mini-track {
  height:9px !important;
}
@media (max-width: 980px) {
  .inv-split-body,
  .hub-two-col,
  .hub-equal-col,
  .hub-kpi-grid {
    grid-template-columns:1fr !important;
  }
}
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
            f"<div class='hub-bar-seg' "
            f"style='flex:{v} 0 0; background:{color};' "
            f"title='{html.escape(label_ko)}: {v:,} ({pct:.1f}%)'>{inner}</div>"
        )

    bar = f"<div class='hub-bar'>{''.join(segs)}</div>" if nonzero else \
          "<div class='hub-bar'><div class='hub-bar-seg' style='flex:1; color:#888;'>(데이터 없음)</div></div>"

    if zeros:
        zlabels = " ".join(
            f"<span>○ {html.escape(_LABEL.get(k, k))}</span>" for k in zeros
        )
        bar += f"<div class='hub-zeros'>{zlabels}</div>"
    return bar


def _progress(numer: int, denom: int, label: str) -> str:
    pct = (numer / denom * 100) if denom else 0
    return (
        f"<div class='hub-prog-wrap'>"
        f"<div class='hub-prog-fill' style='width:{pct:.1f}%;'></div>"
        f"<div class='hub-prog-text'>{label} · <b>{numer:,}</b> / {denom:,} "
        f"({pct:.1f}%)</div>"
        f"</div>"
    )


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    s = store_vault.db_stats()

    if not s.db_exists:
        st.error("볼트 DB가 아직 없습니다. `python -m scripts.init_vault` 로 초기화하세요.")
        return

    dist = store_vault.doc_distribution()

    hub_pagebar(
        "데이터",
        "Inventory",
        "문서, 청크, 검색 인덱스, 분류 상태를 압축된 운영 지표로 확인합니다.",
        "DB Ready" if s.documents else "빈 볼트",
    )
    hub_kpi_grid([
        ("Documents", _fmt_int(s.documents), "active + quarantine"),
        ("Chunks", _fmt_int(s.chunks), "indexed units"),
        ("FTS", _fmt_int(s.fts), "search ready" if s.fts else "empty"),
        ("Concepts", _fmt_int(s.concepts), f"{_fmt_int(s.aliases)} aliases"),
    ])

    # S3-R3: 흐름에서 이관된 처리 큐 현황 관측 (명령은 흐름, 관측은 데이터).
    q = store_vault.queue_snapshot()
    hub_kpi_grid([
        ("대기", _fmt_int(q.pending), "K2 미분석"),
        ("처리중", _fmt_int(q.processing), "in progress"),
        ("완료", _fmt_int(q.done), "K2 done"),
        ("실패", _fmt_int(q.failed), "fail_count>0"),
    ])

    distribution_panel = hub_panel(
        "분류 분포",
        (
            "<div class='inv-split-body'>"
            "<div><div class='inv-mini-title'>Channel</div>"
            + _stacked_bar(sorted(dist.by_channel.items(), key=lambda item: -item[1])[:6])
            + "</div>"
            "<div><div class='inv-mini-title'>Status</div>"
            + _stacked_bar(sorted(dist.by_status.items(), key=lambda item: -item[1])[:6])
            + "</div>"
            "</div>"
        ),
        subtitle="채널과 큐레이션 상태의 현재 비율",
    )
    index_panel = hub_panel(
        "인덱스 상태",
        hub_key_value_rows([
            ("Schema", str(s.schema_version)),
            ("Integrity", s.integrity),
            ("FTS", "Ready" if s.fts else "Empty"),
            ("Concepts", "Ready" if s.concepts else "Empty"),
        ]),
        subtitle="검색과 지식저장소 readiness",
    )
    hub_two_col(distribution_panel, index_panel)

    def _pct(n: int) -> float:
        return n / s.documents * 100 if s.documents else 0

    progress_rows = [
        ("① extract", _pct(s.extract_done)),
        ("② classify", _pct(s.classify_done)),
        ("③ summarize", _pct(s.summarize_done)),
        ("K2 완주", _pct(s.k2_done)),
    ]
    progress_panel = hub_panel(
        "K2 분석 진척",
        hub_bar_rows(progress_rows),
        subtitle="분류와 분석 파이프라인의 현재 커버리지",
    )
    actions_panel = hub_panel(
        "빠른 액션",
        """
<div class="hub-action-grid">
  <button class="hub-action-button primary">재처리 큐로 보내기</button>
  <button class="hub-action-button">Obsidian 동기화</button>
  <button class="hub-action-button">원본 폴더 열기</button>
</div>
""",
    )
    hub_two_col(progress_panel, actions_panel)

    st.markdown(
        f"<div class='inv-meta-line'>"
        f"DB <code>{s.db_size_mb:.1f} MB</code> · "
        f"분류 완료 <code>{_fmt_int(s.classified)}</code> · "
        f"재처리·Obsidian 동기화는 흐름 탭에서 실행"
        f"</div>",
        unsafe_allow_html=True,
    )

    # S4: 개념 후보 — 정규화 미매칭 개념의 사람 승인 표면 (concepts.yaml 등록/기각).
    from src.store import knowledge as store_knowledge
    cands = store_knowledge.list_candidates(n=15)
    st.divider()
    st.subheader("🧩 개념 후보")
    if cands:
        st.caption("정규화 미매칭 개념 — doc_count 순. 사전(concepts.yaml) 등록 or 기각 대상.")
        st.dataframe(
            {
                "후보": [c["sample"] or c["raw_norm"] for c in cands],
                "문서수": [c["doc_count"] for c in cands],
                "최근": [(c["last_seen"] or "")[:10] for c in cands],
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("개념 후보 없음 — 미매칭 개념이 쌓이면 여기서 사전 등록/기각합니다.")

    # S3-R2: 인사이트 탭 흡수 — 관측 백엔드 상태·telemetry·Grafana 링크를 데이터 탭 하위로.
    st.divider()
    st.subheader("🔭 관측")
    st.caption("Grafana 중심 관측 백엔드 상태와 K5 telemetry 현황 (구 인사이트 탭 통합).")
    from src.tabs import placeholders
    placeholders.render_observability_section()
