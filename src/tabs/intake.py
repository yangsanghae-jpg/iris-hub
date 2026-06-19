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

from src.config import IRIS_RAW_PATH

# V2.6.3.3: iris-knowledge로 경로 단일화. legacy IRIS_SYSTEM·sys.path hack 제거.
RAW_DIR = IRIS_RAW_PATH
INCLUDE_SUFFIXES = {".md", ".txt"}


def _run_raw_intake() -> tuple[bool, str]:
    """raw_intake.main() 호출. 출력 캡처."""
    from io import StringIO
    from contextlib import redirect_stdout, redirect_stderr

    try:
        from src.ingest import raw_intake
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
    """(B) 폴더 로딩 섹션 — 스캔 + 트리 선택 + 인제스트 + 결과 저장."""
    from collections import defaultdict
    from src import folder_load

    # ── 다이얼로그 결과를 위젯에 prepop (위젯 인스턴스 *전*에) ─────────
    # 위젯 키(fl_folder/fl_dest)와 다이얼로그 결과 키를 분리해야 위젯 인스턴스 후 잠김 회피.
    if st.session_state.pop("_fl_folder_prefill", None):
        st.session_state["fl_folder"] = st.session_state.pop("_fl_folder_prefill_value")
    if st.session_state.pop("_fl_dest_prefill", None):
        st.session_state["fl_dest"] = st.session_state.pop("_fl_dest_prefill_value")

    # ── 소스 폴더 ─────────────────────────────────────────────────
    st.markdown("**📂 소스 폴더**")
    sc1, sc2, sc3 = st.columns([4, 1.2, 1])
    with sc1:
        st.text_input(
            "소스 폴더 경로",
            placeholder="[폴더 선택]으로 고르거나 직접 붙여넣기",
            key="fl_folder",
            label_visibility="collapsed",
        )
    with sc2:
        if st.button("📁 폴더 선택", use_container_width=True, key="fl_pick_src"):
            picked = _pick_folder_dialog(
                prompt="인덱싱할 소스 폴더 선택",
                default=st.session_state.get("fl_folder", ""),
            )
            if picked:
                st.session_state["_fl_folder_prefill"] = True
                st.session_state["_fl_folder_prefill_value"] = picked
                st.rerun()
    with sc3:
        recursive = st.checkbox("하위 포함", value=True, key="fl_recursive")

    folder_str = st.session_state.get("fl_folder", "")

    # ── 결과 저장 폴더 + 옵션 ──────────────────────────────────────
        # V2.6.3.9 — archive 우선. 기본값 자동, 사용자 override만 허용.
    from src.config import IRIS_KNOWLEDGE_ARCHIVE
    st.markdown("**📦 archive 루트 폴더**")
    st.caption(
        f"📦 기본 위치: `{IRIS_KNOWLEDGE_ARCHIVE}` "
        "(V2.6.3.9 — 원본 + content.md + manifest.json 카피 저장. 비워두면 기본 위치 사용)",
    )
    dc1, dc2, dc3, dc4 = st.columns([4, 1.2, 1, 1])
    with dc1:
        st.text_input(
            "archive 루트",
            placeholder="비워두면 기본 (3-archive/). 다른 위치 박고 싶을 때만 입력.",
            key="fl_dest",
            label_visibility="collapsed",
        )
    with dc2:
        if st.button("📁 폴더 선택", use_container_width=True, key="fl_pick_dest"):
            picked = _pick_folder_dialog(
                prompt="archive 루트 폴더 선택 (대안 위치)",
                default=st.session_state.get("fl_dest", "")
                or str(IRIS_KNOWLEDGE_ARCHIVE),
            )
            if picked:
                st.session_state["_fl_dest_prefill"] = True
                st.session_state["_fl_dest_prefill_value"] = picked
                st.rerun()
    with dc3:
        lane = st.selectbox("lane", ["reference", "bronze"], index=0, key="fl_lane",
                             help="reference / bronze — 인덱싱 후 K3 매트릭스에서 승급",
                             label_visibility="collapsed")
    with dc4:
        st.caption(
            "🔄 분류는 🔄 흐름 탭에서",
            help="V2.6.3.8 — 입력 탭은 *대기열 enqueue*만. K2 분류는 흐름 탭의 묶음/개별/선택 처리에서.",
        )
    use_k2 = False  # V2.6.3.8 — 입력 단계에서 K2 호출하지 않음

    dest_str = st.session_state.get("fl_dest", "")

    if not folder_str:
        st.info("📂 위에서 폴더를 선택하면 하위 파일이 트리로 표시됩니다.")
        return

    # ── 스캔 ────────────────────────────────────────────────────
    scan = folder_load.scan_folder(folder_str, recursive=recursive)
    if scan.total == 0:
        st.warning(f"파일 없음 또는 폴더 없음: `{scan.folder}`")
        return

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전체", scan.total)
    m2.metric("⏳ 미등록", scan.pending_count,
              help="DB에 path로 박힌 적 없는 파일 — 이번 인덱싱 대상")
    m3.metric("📚 DB 등록됨", scan.processed_count,
              help="이전에 인덱싱되어 documents.path로 박혀 있는 파일. "
                   "🔄 강제 재파싱 켜야 다시 박힘.")
    with m4:
        force = st.checkbox("🔄 강제 재파싱", value=False, key="fl_force",
                             help="DB 등록됨도 다시 박음")

    # ── 트리 뷰: 디렉터리별 expander + 체크박스 ────────────────────
    # 디렉터리 → 파일들 그룹화. 디렉터리 키는 scan.folder 기준 상대경로.
    by_dir: dict[str, list[folder_load.FileEntry]] = defaultdict(list)
    for e in scan.entries:
        rel_dir = str(e.path.relative_to(scan.folder).parent)
        by_dir[rel_dir].append(e)

    dirs_sorted = sorted(by_dir.keys(), key=lambda d: (d != ".", d))

    # ── 일괄 선택/해제 + 인덱싱 버튼 (트리 위 sticky 위치) ─────────
    selected_count = sum(
        1 for e in scan.entries
        if st.session_state.get(f"fl_sel_{e.path}", (force or not e.processed))
    )

    top_c1, top_c2, top_c3, top_c4 = st.columns([1, 1, 1.6, 2.4])
    with top_c1:
        if st.button("전체 선택", use_container_width=True, key="fl_sel_all"):
            for e in scan.entries:
                st.session_state[f"fl_sel_{e.path}"] = True
            st.rerun()
    with top_c2:
        if st.button("전체 해제", use_container_width=True, key="fl_sel_none"):
            for e in scan.entries:
                st.session_state[f"fl_sel_{e.path}"] = False
            st.rerun()
    with top_c3:
        st.metric("✋ 선택", selected_count, label_visibility="collapsed")
        st.caption(f"✋ 선택 **{selected_count}**건")
    with top_c4:
        run = st.button(
            f"📥 선택한 {selected_count}건 인덱싱",
            type="primary",
            disabled=(selected_count == 0),
            use_container_width=True,
            key="fl_run",
        )

    st.caption(
        "💡 미등록(⏳)은 기본 선택, DB 등록됨(📚)은 기본 해제. "
        "🔄 강제 재파싱을 켜면 DB 등록됨도 자동 선택."
    )

    selected_paths: list[Path] = []

    for d in dirs_sorted:
        entries = by_dir[d]
        pending_n = sum(1 for e in entries if not e.processed)
        done_n = len(entries) - pending_n
        # 라벨: 디렉터리 / 대기·처리됨 카운트
        label_dir = "(루트)" if d == "." else d
        header = f"📂 **{label_dir}** — ⏳ {pending_n} · ✅ {done_n}"

        with st.expander(header, expanded=(pending_n > 0)):
            # 디렉터리 단위 일괄 토글
            tc1, tc2, _ = st.columns([1, 1, 4])
            with tc1:
                if st.button("이 폴더 선택", key=f"fl_dir_sel_{d}", use_container_width=True):
                    for e in entries:
                        if force or not e.processed:
                            st.session_state[f"fl_sel_{e.path}"] = True
                    st.rerun()
            with tc2:
                if st.button("이 폴더 해제", key=f"fl_dir_clr_{d}", use_container_width=True):
                    for e in entries:
                        st.session_state[f"fl_sel_{e.path}"] = False
                    st.rerun()

            for e in sorted(entries, key=lambda x: (x.processed, x.path.name)):
                key = f"fl_sel_{e.path}"
                # 기본값: 대기는 체크, 처리됨은 force일 때만 체크
                if key not in st.session_state:
                    st.session_state[key] = (force or not e.processed)
                size_kb = round(e.size / 1024, 1)
                mtime = dt.datetime.fromtimestamp(e.mtime).strftime("%Y-%m-%d %H:%M")
                status = "✅" if e.processed else "⏳"
                # 처리됨은 회색 톤으로
                fname = e.path.name
                if e.processed:
                    label = f"{status} :gray[{fname}] · :gray[{size_kb}KB · {mtime}]"
                else:
                    label = f"{status} **{fname}** · :gray[{size_kb}KB · {mtime}]"

                if st.checkbox(label, key=key):
                    selected_paths.append(e.path)

    # ── 인덱싱 실행 (버튼은 위 sticky 위치) ─────────────────────────
    if run:
        # 진행 가시화 — progress bar + 상태 라인
        progress = st.progress(0.0, text="준비 중...")
        status_box = st.empty()
        log_lines: list[str] = []

        def _on_progress(i: int, total: int, status: str, fpath: str) -> None:
            pct = i / total if total else 1.0
            name = Path(fpath).name
            icon = {
                "staging": "📥", "parsing": "🔍", "classifying": "🏷️",
                "archiving": "📦", "done": "✅",
                "skip-empty": "⊘", "skip-already": "↪", "error": "❌",
            }.get(status, "·")
            progress.progress(min(pct, 1.0), text=f"[{i}/{total}] {icon} {status} — {name}")
            if status in ("done", "error", "skip-empty", "skip-already"):
                log_lines.append(f"{icon} [{i}/{total}] {name} — {status}")
                status_box.code("\n".join(log_lines[-15:]), language=None)

        result = folder_load.ingest_paths(
            selected_paths,
            lane=lane,
            force=force,
            archive_root=Path(dest_str) if dest_str else None,
            use_k2=use_k2,
            on_progress=_on_progress,
        )
        progress.progress(1.0, text=f"완료 ({len(selected_paths)}건)")

        if result.ok:
            msg = (
                f"✅ 인덱싱 완료 — UPSERT {result.upserted} · "
                f"분류 {result.classified} · "
                f"빈본문 skip {result.skipped_empty} · "
                f"이미 처리 skip {result.skipped_already}"
            )
            if dest_str:
                msg += f" · archive 저장 {result.archived}건 (work_id={result.work_id})"
            st.success(msg)
        else:
            st.error(f"⚠️ 일부 실패 — {len(result.errors)}건")
            with st.expander(f"실패 상세 ({len(result.errors)})"):
                for name, err in result.errors[:50]:
                    st.code(f"{name}: {err}")

        # 건별 결과 표 (작업 추적용)
        with st.expander(f"📋 건별 결과 ({len(result.files)}건)", expanded=False):
            for fr in result.files:
                if fr.error:
                    st.write(f"❌ `{fr.source.name}` — {fr.error}")
                elif fr.skipped_reason:
                    st.write(f"⊘ `{fr.source.name}` — skip ({fr.skipped_reason})")
                else:
                    line = (
                        f"✅ `{fr.source.name}` · {fr.chunks} chunks · "
                        f"{fr.classifier or 'rule'} · "
                        f"{fr.industry or '?'}/{fr.area or '?'}"
                    )
                    if fr.archive_dir:
                        line += f" → `{fr.archive_dir.relative_to(Path(dest_str)) if dest_str else fr.archive_dir}`"
                    st.write(line)

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
    st.caption(".md / .txt / .pdf / .pptx / .docx 파일을 *raw 폴더에 직접 박기*. 여러 개 한 번에 가능.")

    uploaded = st.file_uploader(
        "파일 끌어다 놓기 또는 클릭해서 선택",
        type=["md", "txt", "pdf", "pptx", "docx"],
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

    # ─── (B) 📁 폴더 로딩 — 외부 폴더 경로 일괄 인덱싱 ─────────────
    st.divider()
    st.markdown("### (B) 📁 폴더 로딩 — 외부 자료 일괄 인덱싱")
    st.caption(
        "V2.6.3.10 지원 포맷: **.md · .txt · .pdf · .pptx · .docx**. "
        "원본은 3-archive로 카피 보존되고, content.md로 자동 변환됩니다. "
        "변환 안 되는 포맷은 skip-unsupported."
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
        "`cd ~/Documents/1Dev/iris-hub && make build-faiss`"
    )
