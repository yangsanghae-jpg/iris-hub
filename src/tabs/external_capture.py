"""탭: 🌐 외부응답 — GPT/Gemini/Claude 등 외부 LLM 응답을 *보이는 그대로* 박는 자리.

설계 원칙 (사용자 합의, 2026-06-15):
  - 본문 변형 X. 카피→붙여넣기 그대로 보존.
  - 관리 단위 = "이벤트" (출처 + 이벤트명 + 본문 + 시각).
  - 분류는 *사후* 작업이라 본 탭에서 강요하지 않음 — 단 저장 시 자동 추천.
  - 기존 `📥 입력` 탭은 손대지 않음 — 본 탭은 *별도 자리*.

저장 위치:
  iris-system/knowledge/raw/_external/<source>/<slug>_<ts>.md

저장 후 흐름 (사용자 합의 2026-06-15):
  1. raw .md 파일 박기 (frontmatter + body)
  2. classify.suggest_classification() 으로 industry/area/level 추천
  3. raw_intake 헬퍼 함수로 documents/chunks/FTS 박기 (1건만)
  4. classify 결과를 documents UPDATE (industry/area/level)
"""
from __future__ import annotations

import datetime as dt
import re
import sqlite3
import sys
from pathlib import Path

import streamlit as st


IRIS_SYSTEM = Path("/Users/iris/Documents/0Dev/iris-system")
if str(IRIS_SYSTEM) not in sys.path:
    sys.path.insert(0, str(IRIS_SYSTEM))

EXTERNAL_DIR = IRIS_SYSTEM / "knowledge" / "raw" / "_external"
DB_PATH = IRIS_SYSTEM / "knowledge" / "_index.db"

SOURCES = [
    "chatgpt",
    "gemini",
    "claude",
    "perplexity",
    "grok",
    "copilot",
    "mistral",
    "openwebui-chat",
    "manual-note",
    "meeting-memo",
    "other",
]


# ─── 유틸 ────────────────────────────────────────────────────────────────────

def _slug(s: str, maxlen: int = 50) -> str:
    """이벤트명 → 파일명 안전 슬러그. 공백·특수문자는 _, 한글·영숫자는 유지."""
    s = s.strip()
    s = re.sub(r"[^\w가-힣\-]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:maxlen] or "event"


def _now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _build_frontmatter(*, title: str, source: str, prompt: str | None = None) -> str:
    """YAML frontmatter — 본문 보존이 본질이라 키는 최소만."""
    lines = ["---", f"title: {title}", f"source: {source}", f"captured_at: {_now_iso()}"]
    if prompt and prompt.strip():
        # 줄바꿈 있는 prompt는 YAML block 스타일로
        if "\n" in prompt:
            lines.append("prompt: |")
            for ln in prompt.splitlines():
                lines.append(f"  {ln}")
        else:
            lines.append(f"prompt: {prompt.strip()}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _save_event(*, title: str, source: str, body: str, prompt: str | None = None) -> Path:
    """raw/_external/<source>/<slug>_<ts>.md 로 저장."""
    target_dir = EXTERNAL_DIR / source
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{_slug(title)}_{ts}.md"
    target = target_dir / fname
    md = _build_frontmatter(title=title, source=source, prompt=prompt) + body.rstrip() + "\n"
    target.write_text(md, encoding="utf-8")
    return target


def _ingest_one(path: Path, *, industry: str | None, area: str | None,
                level: str | None) -> dict:
    """1건 인제스트 — raw_intake 내부 함수 직접 사용.

    raw_intake.main()은 RAW_DIR 루트만 읽기 때문에 _external/<source>/ 하위
    파일은 자동으로 안 들어감. 본 헬퍼가 1건만 정확히 박아준다.

    반환: {"ok": bool, "doc_id": str | None, "chunks": int, "error": str | None}
    """
    try:
        from apps.ingest.raw_intake import (
            doc_id_for, parse_frontmatter, split_chunks, upsert_raw_doc,
        )
        from apps.ingest.fts_sync import rebuild_all
    except Exception as e:
        return {"ok": False, "doc_id": None, "chunks": 0,
                "error": f"raw_intake import 실패: {e}"}

    if not DB_PATH.exists():
        return {"ok": False, "doc_id": None, "chunks": 0,
                "error": f"DB 없음: {DB_PATH}"}

    try:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        title = meta.get("title") or path.stem
        chunks = split_chunks(body)
        if not chunks:
            return {"ok": False, "doc_id": None, "chunks": 0,
                    "error": "본문 chunk 0개"}

        doc_id = doc_id_for(path)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            upsert_raw_doc(conn, doc_id, path, title, chunks)

            # classify 결과 UPDATE — raw_intake가 박아준 NULL을 덮어씀
            if any(v is not None for v in (industry, area, level)):
                conn.execute(
                    "UPDATE documents SET industry=?, area=?, level=? "
                    "WHERE doc_id=?",
                    (industry, area, level, doc_id),
                )

            # FTS 동기 (raw_intake.main이 끝에 호출하던 것)
            rebuild_all(conn)
            conn.commit()
        finally:
            conn.close()

        return {"ok": True, "doc_id": doc_id, "chunks": len(chunks),
                "error": None}
    except Exception as e:
        return {"ok": False, "doc_id": None, "chunks": 0,
                "error": f"{type(e).__name__}: {e}"}


def _list_recent(n: int = 10) -> list[dict]:
    """최근 박힌 이벤트 N개 — mtime 내림차순."""
    if not EXTERNAL_DIR.exists():
        return []
    files: list[Path] = []
    for src_dir in EXTERNAL_DIR.iterdir():
        if not src_dir.is_dir():
            continue
        for p in src_dir.glob("*.md"):
            files.append(p)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict] = []
    for p in files[:n]:
        try:
            head = p.read_text(encoding="utf-8")
            title = ""
            source = p.parent.name
            for line in head.splitlines()[:10]:
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    break
            out.append({
                "path": p,
                "title": title or p.stem,
                "source": source,
                "mtime": dt.datetime.fromtimestamp(p.stat().st_mtime),
                "size": p.stat().st_size,
            })
        except Exception:
            continue
    return out


# ─── UI ──────────────────────────────────────────────────────────────────────

def _form_keys() -> dict[str, str]:
    """위젯 키 — 저장마다 reset_counter 증가로 새 키 생성.

    Streamlit은 위젯 인스턴스화 후 같은 key의 session_state를 직접 수정 못 함.
    저장 후 폼을 비우려면 *새 위젯*을 만들어야 하므로 키 자체를 바꾼다.
    """
    n = st.session_state.get("ext_reset_counter", 0)
    return {
        "title":  f"ext_title_{n}",
        "prompt": f"ext_prompt_{n}",
        "body":   f"ext_body_{n}",
        "source": f"ext_source_{n}",
    }


def _bump_form() -> None:
    """저장 직후 호출 — 다음 rerun에서 위젯 키가 새로 만들어져 빈 상태."""
    st.session_state["ext_reset_counter"] = st.session_state.get("ext_reset_counter", 0) + 1


def render() -> None:
    st.markdown("## 🌐 외부응답")
    st.caption(
        "GPT, Gemini, Claude 등 외부 LLM 응답을 *보이는 그대로* 박는 자리. "
        "본문 변형 없이 보존. 분류·정제는 사후."
    )

    if not EXTERNAL_DIR.exists():
        try:
            EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            st.error(f"저장 자리 생성 실패: {e}")
            return

    # 저장 자리 안내 + 폴더 열기
    c_path1, c_path2 = st.columns([4, 1])
    with c_path1:
        st.caption(f"📂 저장 위치: `{EXTERNAL_DIR}`")
    with c_path2:
        if st.button("📁 폴더 열기", key="ext_open_folder", use_container_width=True):
            import subprocess
            subprocess.Popen(["open", str(EXTERNAL_DIR)])

    # 직전 저장 결과 (rerun 후에도 유지)
    if "ext_last_saved" in st.session_state:
        last = st.session_state["ext_last_saved"]
        st.success(
            f"✅ **저장 완료** — `{last['filename']}`  ·  "
            f"{last['source']}  ·  {last['size']:,} bytes"
        )

        # 분류 추천 + 인제스트 결과
        with st.expander("🔖 자동 분류 + 인덱싱 결과", expanded=False):
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("industry", last.get("industry") or "—")
            cc2.metric("area", last.get("area") or "—")
            cc3.metric("level", last.get("level") or "—")
            cc4.metric("chunks", last.get("ingest_chunks", 0))

            kws = last.get("keywords", [])
            if kws:
                st.caption("키워드: " + " · ".join(f"`{k}`" for k in kws))

            if last.get("ingest_ok"):
                st.caption(
                    "🟢 documents/chunks/FTS에 박힘 — 그래프·인사이트 탭에서 보임"
                )
            else:
                err = last.get("ingest_error") or "알 수 없음"
                st.warning(f"⚠️ 인제스트 실패 (raw .md는 보존됨): {err}")

    # ─── 새 이벤트 박기 ───────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📥 새 이벤트 박기")

    keys = _form_keys()
    c1, c2 = st.columns([3, 1])
    with c1:
        title = st.text_input(
            "이벤트명 *",
            placeholder="예: MES 핵심 개념 정리 v3",
            key=keys["title"],
        )
    with c2:
        source = st.selectbox("출처", SOURCES, index=0, key=keys["source"])

    prompt = st.text_input(
        "원본 질의 (선택)",
        placeholder="예: MES 핵심 개념을 7장 분량으로 정리해줘",
        key=keys["prompt"],
    )

    body = st.text_area(
        "답변 본문 * (markdown 그대로 붙여넣기)",
        height=600,
        placeholder="여기에 GPT/Gemini/Claude 답변을 그대로 붙여넣기...",
        key=keys["body"],
    )

    if st.button(
        "💾 저장",
        type="primary",
        disabled=not (title and body),
        use_container_width=True,
        key="ext_save_btn",
    ):
        try:
            # 1. raw .md 박기
            target = _save_event(
                title=title.strip(),
                source=source,
                body=body,
                prompt=prompt.strip() if prompt else None,
            )

            # 2. classify 추천 (즉시, 결정성 보장)
            try:
                from src.classify import suggest_classification
                clf = suggest_classification(title.strip(), body)
            except Exception:
                clf = {"industry": None, "area": None, "level": None,
                       "keywords": [], "confidence": {}}

            # 3. raw_intake 헬퍼로 1건 인제스트 (DB documents/chunks/FTS)
            ing = _ingest_one(
                target,
                industry=clf.get("industry"),
                area=clf.get("area"),
                level=clf.get("level"),
            )

            # 4. 저장 결과를 session_state에 박기 — rerun 후 success 배너로 표시
            st.session_state["ext_last_saved"] = {
                "filename": target.name,
                "source": source,
                "size": target.stat().st_size,
                "path": str(target),
                "industry": clf.get("industry"),
                "area": clf.get("area"),
                "level": clf.get("level"),
                "keywords": clf.get("keywords", []),
                "ingest_ok": ing.get("ok", False),
                "ingest_chunks": ing.get("chunks", 0),
                "ingest_error": ing.get("error"),
            }
            # 입력 필드 비움 + 화면 갱신
            _bump_form()
            st.toast(f"✅ {target.name} 저장됨", icon="💾")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 저장 실패: {e}")

    # ─── 최근 이벤트 ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📁 최근 박힌 이벤트")

    recent = _list_recent(n=10)
    if not recent:
        st.caption("아직 박힌 이벤트가 없음.")
        return

    st.caption(f"총 {len(recent)}건 (최근순). 펼치면 마크다운 렌더링으로 보여요.")
    for idx, item in enumerate(recent):
        with st.expander(
            f"**{item['title']}**  ·  *{item['source']}*  ·  "
            f"{item['mtime'].strftime('%Y-%m-%d %H:%M')}  ·  "
            f"{item['size']:,} bytes",
            expanded=False,
        ):
            try:
                full_text = item["path"].read_text(encoding="utf-8")
                # frontmatter 분리 (앞쪽 --- ... --- 블록)
                meta_block, body_block = "", full_text
                if full_text.startswith("---\n"):
                    parts = full_text[4:].split("\n---\n", 1)
                    if len(parts) == 2:
                        meta_block, body_block = parts[0], parts[1]

                # 메타 정보 (compact)
                if meta_block:
                    with st.expander("🔖 메타 (frontmatter)", expanded=False):
                        st.code(meta_block, language="yaml")

                # 본문 — 두 모드: 미리보기(렌더링) / 원본(raw)
                tab_render, tab_raw = st.tabs(["✨ 미리보기", "📝 원본"])
                with tab_render:
                    st.markdown(body_block.strip())
                with tab_raw:
                    st.code(body_block.strip(), language="markdown")

                # 액션
                ca1, ca2 = st.columns([1, 4])
                with ca1:
                    if st.button("📁 폴더에서 열기", key=f"ext_open_{idx}",
                                 use_container_width=True):
                        import subprocess
                        subprocess.Popen(["open", "-R", str(item["path"])])
                with ca2:
                    st.caption(f"경로: `{item['path']}`")
            except Exception as e:
                st.caption(f"읽기 실패: {e}")
