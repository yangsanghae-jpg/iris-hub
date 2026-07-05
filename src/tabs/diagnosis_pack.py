"""탭: 🛠 진단툴 관리 — dx_* SoT 그리드·검증·리빌드 (DIAGNOSIS_PACK_MGMT_TAB_DESIGN §2)."""
from __future__ import annotations

import json
from html import escape

import pandas as pd
import streamlit as st

from src.config import DIAGNOSIS_TOOL_GITHUB
from src.diagnosis_git import format_git_date, resolve_diagnosis_repo
from src.store import db, dx, dx_apply, dx_export, dx_import, dx_preview, dx_validate
from src.ui_kit import hub_pagebar, hub_section

SECTIONS = [
    "dashboard",
    "sub_industry",
    "profile",
    "routing",
    "codes",
    "preview",
    "apply",
]


def render() -> None:
    db.ensure_schema()
    if "dx_pack_section" not in st.session_state:
        st.session_state.dx_pack_section = "dashboard"

    repo = resolve_diagnosis_repo()
    meta = dx.latest_import()
    status = _status_label(repo, meta)

    hub_pagebar(
        "진단툴 관리",
        "Pack SoT",
        "DB 중심으로 Ch1 산업·라우팅·카탈로그를 편집하고 diagnosis-tool 팩을 리빌드합니다.",
        status,
    )

    cols = st.columns([1, 4])
    with cols[0]:
        _render_nav()
    with cols[1]:
        _render_actions(repo, meta)
        section = st.session_state.dx_pack_section
        if section == "dashboard":
            _section_dashboard()
        elif section == "sub_industry":
            _section_sub_industry()
        elif section == "profile":
            _section_profile()
        elif section == "routing":
            _section_routing()
        elif section == "codes":
            _section_codes()
        elif section == "preview":
            _section_preview(repo)
        elif section == "apply":
            _section_apply(repo)


def _status_label(repo, meta) -> str:
    if meta is None:
        return "미임포트"
    dirty = "dirty" if repo and repo.dirty else "clean"
    return f"imported · {dirty}"


def _render_nav() -> None:
    hub_section("섹션", level="page")
    labels = {
        "dashboard": "▸ 대시보드",
        "sub_industry": "▸ 하위산업",
        "profile": "▸ 프로필",
        "routing": "▸ 라우팅",
        "codes": "▸ 코드 카탈로그",
        "preview": "▸ 미리보기",
        "apply": "▸ 적용/이력",
    }
    for key, label in labels.items():
        if st.button(
            label,
            key=f"dx_nav_{key}",
            type="primary" if st.session_state.dx_pack_section == key else "secondary",
            use_container_width=True,
        ):
            st.session_state.dx_pack_section = key
            st.rerun()


def _render_actions(repo, meta) -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("JSON→DB 임포트", type="primary", use_container_width=True):
            _run_import(repo)
    with c2:
        if st.button("검증", use_container_width=True):
            _run_validate()
    with c3:
        if st.button("미리보기", use_container_width=True):
            st.session_state.dx_pack_section = "preview"
            st.rerun()
    with c4:
        if st.button("적용(리빌드)", use_container_width=True):
            _run_apply()

    if meta:
        st.caption(
            f"최근 임포트: {format_git_date(meta.imported_at)} · "
            f"branch={meta.source_branch or '—'} · commit={(meta.source_commit or '—')[:7]}"
        )
    st.markdown(
        f"<div class='dt-source-line'>정본: "
        f"<a href='{escape(DIAGNOSIS_TOOL_GITHUB)}' target='_blank'>{escape(DIAGNOSIS_TOOL_GITHUB)}</a>"
        f"{(' · clone: ' + escape(str(repo.root))) if repo else ' · clone 없음'}"
        f"</div>",
        unsafe_allow_html=True,
    )


def _run_import(repo) -> None:
    try:
        if repo:
            result = dx_import.import_from_repo(repo)
        else:
            st.error("diagnosis-tool clone 없음 — DIAGNOSIS_TOOL_GIT 설정 필요")
            return
    except Exception as exc:
        st.error(f"임포트 실패: {exc}")
        return
    st.success(
        f"임포트 완료 — 산업 {result.industries}, 하위산업 {result.sub_industries}, "
        f"라우팅 {result.routing_packs}, 코드 {result.codes}, Q수치 {result.question_metrics}"
    )
    for w in result.warnings[:5]:
        st.warning(w)


def _run_validate() -> None:
    result = dx_validate.validate()
    st.session_state.dx_validation = result
    if result.ok:
        st.success(f"검증 통과 — 경고 {result.warning_count}건")
    else:
        st.error(f"검증 실패 — 오류 {result.error_count}건, 경고 {result.warning_count}건")
    for issue in result.errors[:10]:
        st.error(f"[{issue.code}] {issue.message}")
    for issue in result.warnings[:10]:
        st.warning(f"[{issue.code}] {issue.message}")


def _run_apply() -> None:
    result = dx_apply.apply_rebuild()
    if result.ok:
        st.success(f"적용 완료 — commit {result.commit_sha[:7] if result.commit_sha else '—'}")
        st.code("\n".join(result.files or []))
    else:
        st.error(result.error or "적용 실패")


def _section_dashboard() -> None:
    hub_section("커버리지 대시보드")
    counts = dx.count_rows()
    st.markdown(
        f"산업 **{counts['dx_industry']}** · 하위산업 **{counts['dx_sub_industry']}** · "
        f"프로필항목 **{counts['dx_profile_item']}** · 코드 **{counts['dx_code']}**"
    )

    matrix = dx.coverage_matrix()
    if not matrix:
        st.info("Q2~Q5 수치 데이터 없음 — step 파일 임포트 후 표시됩니다.")
        return

    rows = []
    industries = sorted({r["industry_code"] for r in matrix})
    questions = ["Q2", "Q3", "Q4", "Q5_REC", "Q5_MGMT"]
    lookup = {(r["industry_code"], r["question"]): r for r in matrix}
    for ind in industries:
        row = {"산업": ind}
        for q in questions:
            cell = lookup.get((ind, q))
            if cell:
                filled, total = cell["filled"], cell["total"]
                mark = " 🔴" if filled < total else ""
                row[q] = f"{filled}/{total}{mark}"
            else:
                row[q] = "—"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    gaps = dx.coverage_gaps()
    if gaps:
        hub_section("누락 셀")
        gap_rows = [
            {
                "산업": g["industry_code"],
                "하위산업": g["canon_code"],
                "질문": g["question"],
            }
            for g in gaps[:30]
        ]
        st.dataframe(pd.DataFrame(gap_rows), use_container_width=True, hide_index=True)


def _section_sub_industry() -> None:
    hub_section("하위산업 · 브릿지")
    conn = db.get_conn()
    try:
        subs = dx.list_sub_industries(conn)
        rows = []
        for sub in subs:
            bridges = dx.list_sub_bridges(conn, sub["id"])
            rows.append({
                "id": sub["id"],
                "industry": sub["industry_code"],
                "canon_code": sub["canon_code"],
                "label_ko": sub["label_ko"],
                "A01": ", ".join(bridges.get("A01", [])) or "—",
                "ch1name": ", ".join(bridges.get("ch1name", [])) or "—",
                "step5name": ", ".join(bridges.get("step5name", [])) or "—",
                "SUB": ", ".join(bridges.get("SUB", [])) or "—",
            })
    finally:
        conn.close()

    if not rows:
        st.info("데이터 없음 — 먼저 임포트하세요.")
        return

    edited = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        disabled=["id", "A01", "ch1name", "step5name", "SUB"],
        key="dx_sub_editor",
    )
    if st.button("하위산업 저장", key="dx_sub_save"):
        conn = db.get_conn()
        try:
            for _, row in edited.iterrows():
                conn.execute(
                    "UPDATE dx_sub_industry SET industry_code=?, canon_code=?, ord=? WHERE id=?",
                    (row["industry"], row["canon_code"], row.get("ord"), row["id"]),
                )
            conn.commit()
            st.success("저장됨")
        finally:
            conn.close()


def _section_profile() -> None:
    hub_section("프로필 (default/sub)")
    conn = db.get_conn()
    try:
        industries = [r["code"] for r in dx.list_industries(conn)]
    finally:
        conn.close()
    if not industries:
        st.info("산업 데이터 없음")
        return

    industry = st.selectbox("산업", industries, key="dx_prof_ind")
    conn = db.get_conn()
    try:
        profiles = dx.list_profiles(conn, industry)
        scopes = [p["scope"] for p in profiles] or ["default"]
    finally:
        conn.close()

    scope = st.selectbox("프로필 scope", scopes, key="dx_prof_scope")
    conn = db.get_conn()
    try:
        prof = conn.execute(
            "SELECT id FROM dx_profile WHERE industry_code=? AND scope=?",
            (industry, scope),
        ).fetchone()
        if not prof:
            st.info("프로필 없음")
            return
        profile_id = prof["id"]
        items = dx.list_profile_items(conn, profile_id)
        default_items = {}
        if scope != "default":
            def_prof = conn.execute(
                "SELECT id FROM dx_profile WHERE industry_code=? AND scope='default'",
                (industry,),
            ).fetchone()
            if def_prof:
                for row in dx.list_profile_items(conn, def_prof["id"]):
                    default_items[(row["block"], row["code"])] = row["weight"]
    finally:
        conn.close()

    rows = []
    for item in items:
        key = (item["block"], item["code"])
        delta = ""
        if scope != "default" and key in default_items:
            dw = default_items[key]
            if item["weight"] is not None and dw is not None and item["weight"] != dw:
                delta = f"Δ {item['weight'] - dw:+.2f}"
        rows.append({
            "profile_id": profile_id,
            "block": item["block"],
            "code": item["code"],
            "weight": item["weight"],
            "ord": item["ord"],
            "delta": delta,
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _section_routing() -> None:
    hub_section("라우팅 팩")
    conn = db.get_conn()
    try:
        packs = dx.list_routing_packs(conn)
        for pack in packs:
            st.markdown(f"**{pack['routing_code']}** · {pack['flow_style'] or '—'}")
            effects = dx.list_routing_effects(conn, pack["routing_code"])
            if effects:
                st.dataframe(
                    pd.DataFrame([dict(e) for e in effects]),
                    use_container_width=True,
                    hide_index=True,
                )
    finally:
        conn.close()


def _section_codes() -> None:
    hub_section("코드 카탈로그")
    kind = st.selectbox(
        "kind",
        ["mvp", "modules", "direction", "kpi", "전체"],
        key="dx_code_kind",
    )
    conn = db.get_conn()
    try:
        codes = dx.list_codes(conn, None if kind == "전체" else kind)
        rows = [dict(c) for c in codes]
    finally:
        conn.close()
    if not rows:
        st.info("코드 없음")
        return
    edited = st.data_editor(
        pd.DataFrame(rows)[["kind", "code", "status", "label_ko"]],
        use_container_width=True,
        hide_index=True,
        key="dx_code_editor",
    )
    if st.button("코드 저장", key="dx_code_save"):
        conn = db.get_conn()
        try:
            for _, row in edited.iterrows():
                dx.upsert_code(conn, row["kind"], row["code"], row["status"])
            conn.commit()
            st.success("저장됨")
        finally:
            conn.close()


def _section_preview(repo) -> None:
    hub_section("Ch1 compose 미리보기")
    conn = db.get_conn()
    try:
        industries = [r["code"] for r in dx.list_industries(conn)]
        subs = [r["canon_code"] for r in dx.list_sub_industries(conn)]
        routings = [r["routing_code"] for r in dx.list_routing_packs(conn)]
    finally:
        conn.close()

    if not industries:
        st.info("임포트 후 미리보기 가능")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        industry = st.selectbox("산업", industries, key="dx_prev_ind")
    with c2:
        sub = st.selectbox("하위산업", subs or ["—"], key="dx_prev_sub")
    with c3:
        routing = st.selectbox("라우팅", routings or ["—"], key="dx_prev_rt")

    if st.button("▶ 미리보기 실행", type="primary"):
        if not repo:
            st.error("diagnosis-tool clone 필요")
            return
        result = dx_preview.preview_ch1_compose(industry, sub, routing, repo_root=repo.root)
        if result.ok:
            st.json(result.blocks)
        else:
            st.error(result.error)
            if result.raw:
                st.code(result.raw)


def _section_apply(repo) -> None:
    hub_section("적용 / 이력")
    validation = st.session_state.get("dx_validation") or dx_validate.validate()
    st.markdown(
        f"검증: **{'통과' if validation.ok else '실패'}** · "
        f"오류 {validation.error_count} · 경고 {validation.warning_count}"
    )

    msg = st.text_input("커밋 메시지", value="pack rebuild: iris-hub dx_* export")
    if st.button("적용 → git 커밋", type="primary"):
        _run_apply()

    hub_section("리빌드 미리보기 (파일 목록)")
    export = dx_export.export_ch1()
    st.code("\n".join(export.paths) or "(없음)")

    hub_section("적용 이력")
    logs = dx_apply.list_apply_log()
    if not logs:
        st.caption("이력 없음")
        return
    for log in logs:
        files = json.loads(log["files_json"] or "[]")
        st.markdown(
            f"**{format_git_date(log['applied_at'])}** · "
            f"`{log['commit_sha'][:7] if log['commit_sha'] else '—'}` · "
            f"{log['message']} ({len(files)} files)"
        )
