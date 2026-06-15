"""탭: 📥 입력 — 사람이 *직관적으로* 데이터 박는 자리 (V2.5.3 §3.10 v0.1 정정).

A 패턴 (파일 drag&drop):
  - st.file_uploader → raw 폴더 저장 → raw_intake.main() 호출
  - 즉시 documents/chunks 박힘 + FTS 동기

C 패턴 (챗 응답 저장):
  - 텍스트박스에 OpenWebUI 응답 붙여넣기 + 메타 입력
  - .md 형식으로 raw 폴더 저장 → 같은 파이프라인

알다 v0.10.1 비유:
  알다 Codexian → 답 → vault 자동 저장
  IRIS → OpenWebUI 답 → 사용자가 *복붙*해 입력 탭에 → raw 저장
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import streamlit as st

# iris-system raw_intake import
IRIS_SYSTEM = Path("/Users/iris/Documents/0Dev/iris-system")
if str(IRIS_SYSTEM) not in sys.path:
    sys.path.insert(0, str(IRIS_SYSTEM))

RAW_DIR = IRIS_SYSTEM / "knowledge" / "raw"
INCLUDE_SUFFIXES = {".md", ".txt"}


def _run_raw_intake() -> tuple[bool, str]:
    """raw_intake.main() 호출. 출력 캡처."""
    from io import StringIO
    from contextlib import redirect_stdout, redirect_stderr

    try:
        from apps.ingest import raw_intake
    except Exception as e:
        return False, f"import 실패: {e}"

    buf_out, buf_err = StringIO(), StringIO()
    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = raw_intake.main()
        log = buf_out.getvalue() + buf_err.getvalue()
        if rc == 0:
            return True, log
        return False, f"rc={rc}\n{log}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _save_to_raw(filename: str, content: bytes | str) -> Path:
    """raw 폴더에 파일 저장. 충돌 시 timestamp suffix."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    target = RAW_DIR / filename
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = RAW_DIR / f"{stem}_{ts}{suffix}"
    target.write_bytes(content)
    return target


def _build_md(*, title: str, source: str, body: str,
              industry: str = "", area: str = "", level: str = "") -> str:
    """frontmatter + 본문 .md 생성."""
    lines = ["---"]
    lines.append(f"title: {title}")
    if industry: lines.append(f"industry: {industry}")
    if area: lines.append(f"area: {area}")
    if level: lines.append(f"level: {level}")
    lines.append(f"source: {source}")
    lines.append(f"captured_at: {dt.datetime.now().isoformat(timespec='seconds')}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    return "\n".join(lines)


def _pick_folder_dialog(prompt: str = "폴더 선택", default: str = "") -> str | None:
    """macOS Finder 폴더 선택 다이얼로그. POSIX 경로 반환. 취소면 None.

    Streamlit은 서버 프로세스가 떠 있는 호스트에서 osascript 실행 — M2/M5 둘 다 macOS라 OK.
    """
    import shlex
    import subprocess

    default_clause = f' default location "{default}"' if default else ""
    script = (
        f'POSIX path of (choose folder with prompt "{prompt}"{default_clause})'
    )
    try:
        out = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        st.warning(f"폴더 선택 다이얼로그 실행 실패: {e}")
        return None
    if out.returncode != 0:
        # 사용자가 취소(-128)한 경우는 조용히 None
        return None
    picked = out.stdout.strip()
    return picked or None


def _render_folder_load() -> None:
    """(B) 폴더 로딩 섹션 — 스캔 + 선택 + 인제스트 + 결과 저장."""
    import pandas as pd
    from src import folder_load

    # ── 소스 폴더 ─────────────────────────────────────────────────
    if "fl_folder" not in st.session_state:
        st.session_state["fl_folder"] = ""

    sc1, sc2, sc3 = st.columns([3, 1, 1])
    with sc1:
        st.text_input(
            "📂 소스 폴더",
            placeholder="아래 [폴더 선택]으로 고르거나 직접 붙여넣기",
            key="fl_folder",
        )
    with sc2:
        if st.button("📁 폴더 선택", use_container_width=True, key="fl_pick_src"):
            picked = _pick_folder_dialog(
                prompt="인덱싱할 소스 폴더 선택",
                default=st.session_state.get("fl_folder", ""),
            )
            if picked:
                st.session_state["fl_folder"] = picked
                st.rerun()
    with sc3:
        recursive = st.checkbox("하위 포함", value=True, key="fl_recursive")

    folder_str = st.session_state["fl_folder"]

    # ── 결과 저장 폴더 + 옵션 ──────────────────────────────────────
    if "fl_dest" not in st.session_state:
        st.session_state["fl_dest"] = ""

    dc1, dc2, dc3, dc4 = st.columns([3, 1, 1, 1])
    with dc1:
        st.text_input(
            "💾 결과 저장 폴더 (선택, 비우면 DB만)",
            placeholder="비워두면 원본 위치만 인덱싱, 사본 저장 X",
            key="fl_dest",
        )
    with dc2:
        if st.button("📁 폴더 선택", use_container_width=True, key="fl_pick_dest"):
            picked = _pick_folder_dialog(
                prompt="결과 저장 폴더 선택",
                default=st.session_state.get("fl_dest", "")
                or "/Users/iris/Documents/0Dev",
            )
            if picked:
                st.session_state["fl_dest"] = picked
                st.rerun()
    with dc3:
        lane = st.selectbox("lane", ["reference", "bronze"], index=0, key="fl_lane",
                             help="reference = 원본 경로 그대로 (No-Copy)")
    with dc4:
        use_k2 = st.checkbox("🤖 K2 분류", value=False, key="fl_use_k2",
                              help="LLM 분류 (5~30초/건). 끄면 규칙 매칭.")

    dest_str = st.session_state["fl_dest"]

    if not folder_str:
        st.info("📂 폴더 경로를 입력하면 파일 리스트가 표시됩니다.")
        return

    scan = folder_load.scan_folder(folder_str, recursive=recursive)
    if scan.total == 0:
        st.warning(f"파일 없음 또는 폴더 없음: `{scan.folder}`")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("전체 파일", scan.total)
    m2.metric("✅ 처리됨", scan.processed_count)
    m3.metric("⏳ 대기", scan.pending_count)

    # 강제 재파싱 옵션
    force = st.checkbox("🔄 강제 재파싱 (이미 처리된 파일도 다시 박음)",
                        value=False, key="fl_force")

    # ── 파일 테이블: 체크박스 + 처리됨/대기 표시 ─────────────────────
    # 처리됨/대기 분리해서 보여줌. 처리됨은 expander 안에 (시각적으로 연하게).
    pending = [e for e in scan.entries if not e.processed]
    done = [e for e in scan.entries if e.processed]

    def _to_rows(entries, default_select: bool):
        return [{
            "선택": default_select,
            "파일": str(e.path.relative_to(scan.folder)),
            "크기(KB)": round(e.size / 1024, 1),
            "수정일": dt.datetime.fromtimestamp(e.mtime).strftime("%Y-%m-%d %H:%M"),
            "doc_id": (e.last_doc_id or "")[:12],
        } for e in entries]

    column_config = {
        "선택": st.column_config.CheckboxColumn(required=False),
        "파일": st.column_config.TextColumn(disabled=True, width="large"),
        "크기(KB)": st.column_config.NumberColumn(disabled=True),
        "수정일": st.column_config.TextColumn(disabled=True),
        "doc_id": st.column_config.TextColumn(disabled=True),
    }

    # 대기 — 위에, 기본 체크
    selected_pending: list[Path] = []
    if pending:
        st.markdown(f"**⏳ 대기 ({len(pending)})**")
        df_p = pd.DataFrame(_to_rows(pending, default_select=True))
        edited_p = st.data_editor(
            df_p, column_config=column_config,
            hide_index=True, use_container_width=True, key="fl_editor_pending",
        )
        selected_pending = [
            pending[i].path for i, sel in enumerate(edited_p["선택"].tolist()) if sel
        ]
    else:
        st.success("⏳ 대기 0건 — 새 파일이 없습니다.")

    # 처리됨 — expander 안에 (회색 캡션으로 *연하게* 표현). 강제 재파싱일 때만 기본 체크.
    selected_done: list[Path] = []
    if done:
        with st.expander(f"✅ 처리됨 ({len(done)}) — 펼쳐서 강제 재파싱 대상 선택", expanded=False):
            st.caption("이미 박힌 파일들. 강제 재파싱 켜면 기본 체크됨.")
            df_d = pd.DataFrame(_to_rows(done, default_select=force))
            edited_d = st.data_editor(
                df_d, column_config=column_config,
                hide_index=True, use_container_width=True, key="fl_editor_done",
            )
            selected_done = [
                done[i].path for i, sel in enumerate(edited_d["선택"].tolist()) if sel
            ]

    selected_paths = selected_pending + selected_done

    # ── 액션 ─────────────────────────────────────────────────────
    a1, a2 = st.columns([1, 3])
    with a1:
        run = st.button(
            f"📥 선택한 {len(selected_paths)}개 인덱싱",
            type="primary",
            disabled=not selected_paths,
            use_container_width=True,
            key="fl_run",
        )
    with a2:
        st.caption(
            "💡 처리됨(연한 행)은 기본 체크 해제. 강제 재파싱을 켜면 처리됨도 다시 박힘."
        )

    if run:
        with st.spinner(f"인덱싱 중 ({len(selected_paths)}건)..."):
            result = folder_load.ingest_paths(
                selected_paths,
                lane=lane,
                force=force,
                dest_dir=Path(dest_str) if dest_str else None,
                use_k2=use_k2,
            )

        if result.ok:
            st.success(
                f"✅ 인덱싱 완료 — UPSERT {result.upserted} · "
                f"분류 {result.classified} · 빈본문 skip {result.skipped_empty}"
                + (f" · 결과 폴더 복사 {result.saved_copies}" if dest_str else "")
            )
        else:
            st.error(f"⚠️ 일부 실패 — {len(result.errors)}건")
            with st.expander(f"실패 상세 ({len(result.errors)})"):
                for name, err in result.errors[:50]:
                    st.code(f"{name}: {err}")

        if result.fts_counts:
            st.caption(f"FTS rebuild: {result.fts_counts}")


def render() -> None:
    st.markdown("## 📥 입력")
    st.caption(
        "사람이 *직관적으로* 지식을 박는 자리. raw 폴더에 떨어지면 "
        "자동으로 K1 인제스트 → documents · chunks · FTS · 그래프 갱신."
    )

    if not RAW_DIR.exists():
        st.error(f"raw 디렉터리 없음: {RAW_DIR}")
        return

    # 사이드 정보
    files_now = sorted(p.name for p in RAW_DIR.iterdir() if p.is_file())
    st.caption(f"📁 raw/ 현재 파일 {len(files_now)}개")
    with st.expander("현재 raw/ 파일 목록", expanded=False):
        for f in files_now:
            st.code(f)

    # ─── (A) 파일 업로드 패턴 ─────────────────────────────────────────
    st.divider()
    st.markdown("### (A) 📂 파일 업로드 — drag & drop")
    st.caption(".md / .txt 파일을 *raw 폴더에 직접 박기*. 여러 개 한 번에 가능.")

    uploaded = st.file_uploader(
        "파일 끌어다 놓기 또는 클릭해서 선택",
        type=["md", "txt"],
        accept_multiple_files=True,
        key="intake_files",
    )

    if uploaded:
        st.markdown(f"**업로드 대기: {len(uploaded)}개**")
        for f in uploaded:
            st.write(f"- `{f.name}` ({f.size:,} bytes)")

        if st.button("📥 raw 폴더에 저장 + 인제스트 실행", type="primary", use_container_width=True):
            saved = []
            for f in uploaded:
                target = _save_to_raw(f.name, f.read())
                saved.append(target)
            st.success(f"✅ raw 폴더 저장 {len(saved)}개")

            with st.spinner("K1 인제스트 실행 중 (raw_intake.main)..."):
                ok, log = _run_raw_intake()

            if ok:
                st.success("✅ 인제스트 완료. 그래프 탭으로 가서 새로고침해보세요.")
            else:
                st.error(f"❌ 인제스트 실패\n```\n{log[:1000]}\n```")
                return

            with st.expander("실행 로그", expanded=False):
                st.code(log[-3000:])

            st.info("💡 다음: `make build-faiss`로 시맨틱 인덱스 갱신 (별도 명령, 1~2분)")

    # ─── (B) 📁 폴더 로딩 — 외부 폴더 경로 그대로 인덱싱 ─────────────
    st.divider()
    st.markdown("### (B) 📁 폴더 로딩 — 외부 자료 일괄 인덱싱")
    st.caption(
        "진단툴 산출물 등 *외부 폴더 경로 그대로* 인덱싱. 원본은 복사하지 않음 (No-Copy)."
    )
    _render_folder_load()

    # ─── (C) 텍스트 붙여넣기 패턴 — 챗 응답 저장 ─────────────────────
    st.divider()
    st.markdown("### (C) 📝 텍스트 붙여넣기 — 챗 응답·메모 저장")
    st.caption("OpenWebUI 챗 답변, 회의 메모, 외부 자료를 *수동 복붙*해 raw로 박기.")

    c1, c2 = st.columns([2, 1])
    with c1:
        title = st.text_input("제목 *", placeholder="예: MES 핵심 개념 정리", key="intake_title")
    with c2:
        source = st.selectbox(
            "출처",
            ["openwebui-chat", "manual-note", "meeting-memo", "external-doc", "other"],
            index=0,
            key="intake_source",
        )

    cm1, cm2, cm3 = st.columns(3)
    with cm1:
        industry = st.text_input("industry", placeholder="A/B/C/...", key="intake_industry")
    with cm2:
        area = st.text_input("area", placeholder="planning/strategy/...", key="intake_area")
    with cm3:
        level = st.text_input("level", placeholder="default", key="intake_level")

    body = st.text_area(
        "본문 (markdown 허용) *",
        height=300,
        placeholder="여기에 챗 응답 또는 노트 붙여넣기...",
        key="intake_body",
    )

    if st.button("📥 .md 생성 후 저장 + 인제스트", type="primary",
                 disabled=not (title and body), key="intake_paste_btn",
                 use_container_width=True):
        # 파일명: 제목 → slug + 날짜
        safe_title = "".join(c if c.isalnum() or c in "-_가-힣" else "_" for c in title)[:50]
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{ts}.md"

        md_content = _build_md(
            title=title, source=source, body=body,
            industry=industry, area=area, level=level,
        )
        target = _save_to_raw(filename, md_content)
        st.success(f"✅ 저장: `{target.name}`")

        with st.spinner("K1 인제스트 실행 중..."):
            ok, log = _run_raw_intake()

        if ok:
            st.success("✅ 인제스트 완료. 🕸️ 그래프 탭에서 새 노드 확인 가능.")
        else:
            st.error(f"❌ 인제스트 실패\n```\n{log[:1000]}\n```")

        with st.expander("실행 로그", expanded=False):
            st.code(log[-3000:])

    # ─── 하단 안내 ───────────────────────────────────────────────────
    st.divider()
    st.markdown("### 💡 다음 단계 (자동화 후보)")
    st.markdown("""
- **(B) 위키 직접 편집** — `wiki/*.md` 인라인 에디터
- **(D) 외부 에디터 watch** — VS Code에서 `wiki/`·`raw/` 편집 → 자동 인덱싱
- **(E) K6 Curate** — 챗 로그 → wiki 자동 정제 (V2.6 후반)
- **OpenWebUI plugin** — 응답에 *"IRIS 저장"* 버튼 직접 박기 (큰 작업)
    """)
    st.caption(
        "💡 시맨틱 검색 갱신: 인제스트 후 터미널에서 "
        "`cd ~/Documents/0Dev/iris-system && make build-faiss`"
    )
