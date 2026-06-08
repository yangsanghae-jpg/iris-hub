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
