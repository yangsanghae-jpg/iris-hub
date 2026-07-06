"""탭: 🔧 진단툴 — git 기준 마이그레이션 진도 자동 평가."""
from __future__ import annotations

from collections import defaultdict
from html import escape

import streamlit as st

from src import diagnosis_migration as dm
from src.config import DIAGNOSIS_TOOL_GITHUB
from src.diagnosis_git import format_git_date
from src.diagnosis_eval import evaluate_all
from src.diagnosis_measurements import measure_diagnosis
from src.ui_kit import hub_pagebar, hub_section

_CSS = """
<style>
.flow-row {
  display:grid;
  gap:8px;
  align-items:stretch;
  margin:12px 0 10px 0;
}
.flow-row.migration {
  grid-template-columns:minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr) 22px minmax(0, 1fr);
}
.flow-card {
  position:relative;
  min-height:118px;
  border:1px solid rgba(47,128,196,0.18);
  border-radius:14px;
  padding:14px 15px 13px 15px;
  background:linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%);
  box-shadow:0 8px 22px rgba(16,24,40,0.045);
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  gap:8px;
  min-width:0;
  overflow:hidden;
}
.flow-card::before {
  content:"";
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:3px;
  background:linear-gradient(90deg, #2f80c4, rgba(47,128,196,0.35));
}
.flow-card.alert {
  border-color:rgba(240,68,56,0.34);
  background:linear-gradient(180deg, #fffafa 0%, #fff5f5 100%);
}
.flow-card.alert::before { background:linear-gradient(90deg, #f04438, rgba(240,68,56,0.35)); }
.flow-card.empty {
  border-color:rgba(152,162,179,0.22);
  background:linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
}
.flow-card.empty::before { background:linear-gradient(90deg, #98a2b3, rgba(152,162,179,0.18)); }
.flow-card.active {
  border-color:rgba(47,128,196,0.40);
  background:linear-gradient(180deg, #f7fbff 0%, #eef7ff 100%);
  box-shadow:0 10px 26px rgba(47,128,196,0.10);
}
.flow-card h4 {
  margin:0;
  font-size:0.88rem;
  line-height:1.25;
  font-weight:780;
  color:#172033;
  letter-spacing:-0.01em;
}
.flow-card .stage-id {
  display:inline-flex;
  width:max-content;
  max-width:100%;
  padding:3px 7px;
  border-radius:999px;
  background:rgba(47,128,196,0.08);
  color:#2f80c4;
  font-size:0.66rem;
  line-height:1;
  font-weight:800;
  letter-spacing:0.04em;
  text-transform:uppercase;
}
.flow-card.empty .stage-id { background:rgba(152,162,179,0.10); color:#667085; }
.flow-card.alert .stage-id { background:rgba(240,68,56,0.10); color:#d92d20; }
.flow-card .big {
  font-size:1.95rem;
  font-weight:850;
  line-height:1;
  color:#101828;
  letter-spacing:-0.045em;
}
.flow-card .unit {
  font-size:0.78rem;
  color:#667085;
  margin-left:5px;
  font-weight:750;
  letter-spacing:-0.01em;
}
.flow-card .sub {
  font-size:0.74rem;
  line-height:1.45;
  color:#667085;
}
.flow-arrow {
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:1.25rem;
  color:#98a2b3;
  min-width:0;
}
.flow-console-note {
  display:flex;
  align-items:center;
  gap:10px;
  margin:6px 0 12px 0;
  padding:9px 11px;
  border:1px solid rgba(47,128,196,0.14);
  border-radius:11px;
  background:rgba(47,128,196,0.045);
  color:#475467;
  font-size:0.78rem;
  line-height:1.45;
}
.flow-console-note strong { color:#172033; font-weight:800; }
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
  white-space:normal !important;
}
.hub-pagebar-title-row {
  align-items:center !important;
  min-height:28px;
}
.hub-pill {
  border:1px solid rgba(18,183,106,0.18);
  box-shadow:0 4px 10px rgba(18,183,106,0.08);
}
div[data-testid="stButton"] > button {
  min-height:36px;
  border-radius:10px;
  border-color:rgba(47,128,196,0.20);
  box-shadow:0 3px 10px rgba(16,24,40,0.035);
  font-weight:760;
}
div[data-testid="stButton"] > button:hover {
  border-color:rgba(47,128,196,0.48);
  background:rgba(47,128,196,0.045);
}
.dt-toolbar {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom:10px;
}
.dt-source-line {
  color:var(--hub-muted);
  font-size:12px;
  margin:-4px 0 12px 0;
}
.dt-source-line a {
  color:var(--hub-accent);
  font-weight:700;
  text-decoration:none;
}
.dt-git-grid,
.dt-next-grid {
  display:grid;
  grid-template-columns:1.2fr 0.8fr;
  gap:12px;
  margin-bottom:12px;
}
.dt-git-panel,
.dt-next-panel,
.dt-items-panel {
  border:1px solid var(--hub-border);
  border-radius:12px;
  background:var(--hub-panel);
  overflow:hidden;
}
.dt-panel-head {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  padding:10px 12px;
  border-bottom:1px solid var(--hub-border-soft);
}
.dt-panel-title {
  color:var(--hub-ink);
  font-size:13px;
  font-weight:850;
}
.dt-panel-subtitle {
  margin-top:2px;
  color:var(--hub-muted-2);
  font-size:11px;
}
.dt-panel-body {
  padding:12px;
}
.dt-git-metrics {
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:8px;
}
.dt-git-metric,
.dt-next-card {
  padding:10px 11px;
  border:1px solid var(--hub-border-soft);
  border-radius:10px;
  background:var(--hub-panel-soft);
}
.dt-git-metric span,
.dt-next-card span {
  display:block;
  color:var(--hub-muted);
  font-size:11px;
  font-weight:750;
}
.dt-git-metric strong {
  display:block;
  margin-top:4px;
  color:var(--hub-ink);
  font-size:20px;
  line-height:1.05;
  font-weight:850;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.dt-git-caption,
.dt-next-detail {
  margin-top:9px;
  color:var(--hub-muted-2);
  font-size:11px;
  line-height:1.45;
}
.dt-action-list {
  display:grid;
  gap:8px;
}
.dt-action-link {
  display:block;
  padding:10px 11px;
  border:1px solid var(--hub-border);
  border-radius:10px;
  background:var(--hub-panel-soft);
  color:var(--hub-ink) !important;
  font-size:12px;
  font-weight:850;
  text-decoration:none !important;
}
.dt-action-link:hover {
  border-color:var(--hub-accent);
  background:rgba(47, 128, 196, 0.08);
}
.dt-pill {
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  padding:3px 7px;
  font-size:10px;
  font-weight:850;
  white-space:nowrap;
}
.dt-pill-ok,
.dt-pill-success,
.dt-pill-verified {
  background:rgba(18, 183, 106, 0.10);
  color:var(--hub-success);
}
.dt-pill-failure {
  background:rgba(240, 68, 56, 0.10);
  color:var(--hub-danger);
}
.dt-pill-pending {
  background:rgba(47, 128, 196, 0.10);
  color:var(--hub-accent);
}
.dt-pill-blocked,
.dt-pill-neutral {
  background:var(--hub-panel-soft);
  color:var(--hub-muted);
  border:1px solid var(--hub-border-soft);
}
.dt-filter-shell {
  padding:10px 12px;
  border-bottom:1px solid var(--hub-border-soft);
  background:var(--hub-panel-soft);
}
.dt-phase-hdr {
  color:var(--hub-muted);
  font-size:11px;
  font-weight:850;
  letter-spacing:0.04em;
  text-transform:uppercase;
  padding:12px 12px 7px 12px;
}
.dt-item-row {
  display:grid;
  grid-template-columns:44px minmax(0, 1fr) 110px;
  gap:12px;
  align-items:flex-start;
  padding:11px 12px;
  border-top:1px solid var(--hub-border-soft);
}
.dt-item-id {
  color:var(--hub-ink);
  font-size:13px;
  font-weight:850;
}
.dt-item-title {
  color:var(--hub-ink);
  font-size:13px;
  font-weight:800;
}
.dt-gate,
.dt-detail {
  display:block;
  margin-top:4px;
  color:var(--hub-muted-2);
  font-size:11px;
  line-height:1.45;
}
.dt-evidence {
  margin-top:8px;
}
.dt-evidence summary {
  color:var(--hub-accent);
  cursor:pointer;
  font-size:11px;
  font-weight:800;
}
.dt-evidence-line {
  color:var(--hub-muted);
  font-size:11px;
  line-height:1.45;
  margin-top:4px;
}
.dt-next-card strong {
  display:block;
  margin-top:4px;
  color:var(--hub-ink);
  font-size:13px;
  line-height:1.35;
}
.dt-next-card + .dt-next-card {
  margin-top:8px;
}
.dt-empty-note,
.dt-warning-note {
  padding:10px 11px;
  border:1px solid var(--hub-border-soft);
  border-radius:10px;
  background:var(--hub-panel-soft);
  color:var(--hub-muted);
  font-size:12px;
  line-height:1.45;
}
.dt-warning-note {
  border-color:rgba(240, 68, 56, 0.25);
  background:rgba(240, 68, 56, 0.06);
  color:var(--hub-danger);
}
@media (max-width: 900px) {
  .dt-git-grid,
  .dt-next-grid,
  .dt-git-metrics {
    grid-template-columns:1fr;
  }
  .dt-item-row {
    grid-template-columns:36px minmax(0, 1fr);
  }
  .dt-item-row .dt-pill {
    grid-column:2;
    justify-self:start;
  }
}
</style>
"""


def _render_html(html: str) -> None:
    """Render static HTML without Markdown code-block interpretation."""
    if hasattr(st, "html"):
        st.html(html)
        return
    st.markdown(html, unsafe_allow_html=True)


def _flow_card(*, stage_id: str, title: str, big: str, unit: str = "", sub: str = "", active: bool = False, alert: bool = False, empty: bool = False) -> str:
    card_class = "flow-card"
    if alert:
        card_class += " alert"
    elif active:
        card_class += " active"
    elif empty:
        card_class += " empty"
    big_html = f"<div class='big'>{escape(big)}<span class='unit'>{escape(unit)}</span></div>" if unit else f"<div class='big'>{escape(big)}</div>"
    return (
        f"<div class='{card_class}'>"
        f"<div class='stage-id'>{escape(stage_id)}</div>"
        f"<h4>{escape(title)}</h4>"
        f"{big_html}"
        f"<div class='sub'>{escape(sub)}</div>"
        f"</div>"
    )


def _flow_arrow() -> str:
    return "<div class='flow-arrow'>→</div>"


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    meta = dm.load_migration_meta()
    items = dm.load_migration_items()

    repo, evals = _cached_evaluate(tuple(it.key for it in items))
    snap = measure_diagnosis()
    github_url = meta.get("github") or DIAGNOSIS_TOOL_GITHUB

    hub_pagebar(
        "진단툴",
        "Migration Control",
        f"{meta.get('version', '')} · git HEAD 기준으로 데이터 마이그레이션 진도를 자동 평가합니다.",
        "Git Verified",
    )
    _render_html(
        f"<div class='dt-source-line'>정본: <a href='{escape(github_url)}' target='_blank' rel='noopener noreferrer'>{escape(github_url)}</a></div>"
    )

    if st.button("git 기준 재평가", type="primary"):
        st.cache_data.clear()
        st.rerun()

    status_counts = _migration_status_counts(items, evals)
    _render_migration_flow(repo or snap.repo, snap, status_counts)

    hub_section("Git 스냅샷")
    _render_git_header(repo or snap.repo, snap)
    hub_section("마이그레이션 현황")
    _render_summary(status_counts)
    _render_items(items, evals)
    hub_section("다음 작업")
    _render_next(items, evals)


def _migration_status_counts(items, evals) -> dict[str, int]:
    counts = {"pending": 0, "success": 0, "failure": 0, "verified": 0, "blocked": 0}
    for item in items:
        status_value = evals[item.key].status
        counts[status_value] = counts.get(status_value, 0) + 1
    return counts


def _render_migration_flow(repo, snap, counts: dict[str, int]) -> None:
    git_big = repo.branch if repo else "Missing"
    git_sub = f"HEAD {repo.head_short}" if repo else "로컬 clone 연결 필요"
    data_src = f"{snap.tracked_data_src:,}"
    done_count = counts.get("success", 0) + counts.get("verified", 0)
    blocked_count = counts.get("blocked", 0)
    failed_count = counts.get("failure", 0)
    cards = [
        _flow_card(stage_id="① git", title="정본 확인", big=git_big, sub=git_sub, active=bool(repo and repo.remote_ok), alert=not bool(repo and repo.remote_ok)),
        _flow_arrow(),
        _flow_card(stage_id="② data/src", title="데이터 추적", big=data_src, unit="files", sub="tracked migration source", empty=(snap.tracked_data_src == 0)),
        _flow_arrow(),
        _flow_card(stage_id="③ 완료", title="검증 통과", big=f"{done_count:,}", unit="items", sub="success + verified", active=(done_count > 0)),
        _flow_arrow(),
        _flow_card(stage_id="④ 보완", title="차단·실패", big=f"{blocked_count + failed_count:,}", unit="items", sub=f"blocked {blocked_count:,} · failure {failed_count:,}", alert=(blocked_count + failed_count > 0)),
    ]
    _render_html("<div class='flow-row migration'>" + "".join(cards) + "</div>")


@st.cache_data(ttl=60)
def _cached_evaluate(_keys: tuple[str, ...]):
    items = dm.load_migration_items()
    return evaluate_all(items)


def _render_git_header(repo, snap) -> None:
    github = DIAGNOSIS_TOOL_GITHUB

    if repo is None:
        _render_html(
            f"""
<div class="dt-git-panel">
  <div class="dt-panel-head">
    <div>
      <div class="dt-panel-title">Git 스냅샷</div>
      <div class="dt-panel-subtitle">로컬 clone 연결 필요</div>
    </div>
    <span class="dt-pill dt-pill-failure">Missing</span>
  </div>
  <div class="dt-panel-body">
    <div class="dt-warning-note">{escape(github)} 의 로컬 clone을 찾을 수 없습니다.</div>
    <div class="dt-git-caption">clone 후 iris-hub와 형제 경로에 두거나 DIAGNOSIS_TOOL_GIT 환경변수로 경로를 지정하세요.</div>
  </div>
</div>
"""
        )
        st.code(f"git clone {github}.git", language="bash")
        return

    remote_status = "Git Verified" if repo.remote_ok else "Remote Check"
    remote_status_class = "dt-pill-ok" if repo.remote_ok else "dt-pill-failure"
    working_tree_status = "dirty" if repo.dirty else "clean"
    push_label = format_git_date(repo.last_push_iso)
    if repo.unpushed_commits > 0:
        push_label = f"{push_label} (+{repo.unpushed_commits})"

    remote_warning = ""
    if not repo.remote_ok:
        remote_warning = f"""
<div class="dt-warning-note">origin이 정본과 다릅니다. 기대: {escape(github)} · 실제: {escape(repo.remote_url or '—')}</div>
"""

    _render_html(
        f"""
<div class="dt-git-grid">
  <div class="dt-git-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">Git 스냅샷</div>
        <div class="dt-panel-subtitle">branch, HEAD, push, working tree를 한 번에 확인합니다.</div>
      </div>
      <span class="dt-pill {remote_status_class}">{remote_status}</span>
    </div>
    <div class="dt-panel-body">
      {remote_warning}
      <div class="dt-git-metrics">
        <div class="dt-git-metric"><span>branch</span><strong>{escape(repo.branch)}</strong></div>
        <div class="dt-git-metric"><span>HEAD</span><strong>{escape(repo.head_short)}</strong></div>
        <div class="dt-git-metric"><span>최근 푸시</span><strong>{escape(push_label)}</strong></div>
        <div class="dt-git-metric"><span>최근 커밋</span><strong>{escape(format_git_date(repo.last_commit_iso))}</strong></div>
        <div class="dt-git-metric"><span>data/src</span><strong>{snap.tracked_data_src:,}</strong></div>
        <div class="dt-git-metric"><span>working tree</span><strong>{escape(working_tree_status)}</strong></div>
      </div>
      <div class="dt-git-caption">clone: {escape(str(repo.root))} · origin: {escape(repo.remote_url or '—')} · 로컬 커밋: {escape(format_git_date(repo.last_commit_iso))}</div>
    </div>
  </div>
  <div class="dt-git-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">진입점</div>
        <div class="dt-panel-subtitle">정본 확인과 재평가 액션을 분리합니다.</div>
      </div>
      <span class="dt-pill dt-pill-neutral">Actions</span>
    </div>
    <div class="dt-panel-body">
      <div class="dt-action-list">
        <a class="dt-action-link" href="{escape(github)}" target="_blank" rel="noopener noreferrer">GitHub 정본 열기</a>
      </div>
      <div class="dt-git-caption">완성(푸시)일: {escape(format_git_date(repo.last_push_iso))}{' · 미푸시 ' + str(repo.unpushed_commits) + '건' if repo.unpushed_commits else ''}</div>
    </div>
  </div>
</div>
"""
    )


def _render_summary(counts: dict[str, int]) -> None:
    cards = [
        _flow_card(stage_id="pending", title="진입 대기", big=str(counts.get("pending", 0)), unit="items", sub="ready to enter", active=(counts.get("pending", 0) > 0)),
        _flow_arrow(),
        _flow_card(stage_id="success", title="완료", big=str(counts.get("success", 0)), unit="items", sub="completed", empty=(counts.get("success", 0) == 0)),
        _flow_arrow(),
        _flow_card(stage_id="failure", title="실패", big=str(counts.get("failure", 0)), unit="items", sub="needs work", alert=(counts.get("failure", 0) > 0)),
        _flow_arrow(),
        _flow_card(stage_id="blocked", title="차단", big=str(counts.get("blocked", 0)), unit="items", sub=f"verified {counts.get('verified', 0)}", alert=(counts.get("blocked", 0) > 0)),
    ]
    _render_html("<div class='flow-row migration'>" + "".join(cards) + "</div>")


def _render_items(items, evals) -> None:
    phase_filter = st.selectbox(
        "Phase 필터",
        ["전체"] + sorted({it.phase for it in items}, key=_phase_sort_key),
        label_visibility="collapsed",
    )

    by_phase: dict[str, list] = defaultdict(list)
    for it in items:
        if phase_filter != "전체" and it.phase != phase_filter:
            continue
        by_phase[it.phase].append(it)

    phase_sections = []
    for phase in sorted(by_phase.keys(), key=_phase_sort_key):
        rows = "".join(_render_row_html(it, evals[it.key]) for it in by_phase[phase])
        phase_sections.append(f'<div class="dt-phase-hdr">Phase {escape(phase)}</div>{rows}')

    st.markdown(
        f"""
<div class="dt-items-panel">
  <div class="dt-panel-head">
    <div>
      <div class="dt-panel-title">마이그레이션 항목</div>
      <div class="dt-panel-subtitle">게이트, 상태, 근거를 phase 단위로 확인합니다.</div>
    </div>
    <span class="dt-pill dt-pill-neutral">{len(by_phase)} phases</span>
  </div>
  <div class="dt-filter-shell">현재 필터: <strong>{escape(phase_filter)}</strong></div>
  {''.join(phase_sections)}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_row_html(it, ev) -> str:
    status_label = dm.STATUS_LABEL.get(ev.status, ev.status)
    status_class = f"dt-pill-{escape(ev.status)}"
    gate_html = f'<span class="dt-gate">게이트: {escape(it.gate)}</span>' if it.gate else ""
    evidence_html = ""
    if ev.evidence:
        evidence_lines = "".join(
            f'<div class="dt-evidence-line">{escape(line)}</div>'
            for line in ev.evidence
        )
        evidence_html = f"""
<details class="dt-evidence">
  <summary>근거 {len(ev.evidence)}건</summary>
  {evidence_lines}
</details>
"""

    return f"""
<div class="dt-item-row">
  <div class="dt-item-id">{escape(str(it.id))}</div>
  <div>
    <div class="dt-item-title">{escape(it.title)}</div>
    {gate_html}
    <span class="dt-detail">{escape(ev.detail)}</span>
    {evidence_html}
  </div>
  <span class="dt-pill {status_class}">{escape(status_label)}</span>
</div>
"""


def _render_next(items, evals) -> None:
    ready = [it for it in items if evals[it.key].status == "pending"]
    failed = [it for it in items if evals[it.key].status == "failure"]
    blocked = [it for it in items if evals[it.key].status == "blocked"]

    ready_body = _render_next_cards(ready[:8], evals, "진입 가능") or "<div class='dt-empty-note'>진입 가능한 대기 항목 없음.</div>"
    failed_body = _render_next_cards(failed, evals, "재작업 필요") or "<div class='dt-empty-note'>실패 항목 없음.</div>"
    blocked_body = _render_blocked_cards(blocked, evals) or "<div class='dt-empty-note'>선행 미충족 항목 없음.</div>"

    st.markdown(
        f"""
<div class="dt-next-grid">
  <div class="dt-next-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">다음 작업</div>
        <div class="dt-panel-subtitle">즉시 진입 가능 항목과 실패 항목을 먼저 봅니다.</div>
      </div>
      <span class="dt-pill dt-pill-pending">{len(ready)} ready</span>
    </div>
    <div class="dt-panel-body">
      {failed_body if failed else ready_body}
    </div>
  </div>
  <div class="dt-next-panel">
    <div class="dt-panel-head">
      <div>
        <div class="dt-panel-title">차단 항목</div>
        <div class="dt-panel-subtitle">선행 조건 미충족으로 대기 중인 항목입니다.</div>
      </div>
      <span class="dt-pill dt-pill-blocked">{len(blocked)} blocked</span>
    </div>
    <div class="dt-panel-body">{blocked_body}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_next_cards(items, evals, label: str) -> str:
    return "".join(
        f"""
<div class="dt-next-card">
  <span>{escape(label)} · Phase {escape(it.phase)} · {escape(str(it.id))}</span>
  <strong>{escape(it.title)}</strong>
  <div class="dt-next-detail">{escape(evals[it.key].detail)}</div>
</div>
"""
        for it in items
    )


def _render_blocked_cards(items, evals) -> str:
    cards = []
    for it in items[:8]:
        unmet = [
            dependency_key for dependency_key in it.depends
            if evals.get(dependency_key) and evals[dependency_key].status not in ("success", "verified")
        ]
        cards.append(
            f"""
<div class="dt-next-card">
  <span>blocked · Phase {escape(it.phase)} · {escape(str(it.id))}</span>
  <strong>{escape(it.title)}</strong>
  <div class="dt-next-detail">선행 미충족: {escape(', '.join(unmet) or '—')}</div>
</div>
"""
        )
    return "".join(cards)


def _phase_sort_key(phase: str) -> tuple:
    try:
        return (0, float(phase))
    except ValueError:
        return (1, phase)
