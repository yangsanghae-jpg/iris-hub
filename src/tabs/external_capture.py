"""탭: 🌐 외부응답 — GPT/Gemini/Claude 등 외부 LLM 응답을 *보이는 그대로* 박는 자리.

설계 원칙 (사용자 합의, 2026-06-15):
  - 본문 변형 X. 카피→붙여넣기 그대로 보존.
  - 관리 단위 = "이벤트" (출처 + 이벤트명 + 본문 + 시각).
  - 분류는 *사후* 작업이라 본 탭에서 강요하지 않음.
  - 기존 `📥 입력` 탭은 손대지 않음 — 본 탭은 *별도 자리*.

저장 위치:
  iris-system/knowledge/raw/_external/<source>/<slug>_<ts>.md
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import streamlit as st


IRIS_SYSTEM = Path("/Users/iris/Documents/0Dev/iris-system")
if str(IRIS_SYSTEM) not in sys.path:
    sys.path.insert(0, str(IRIS_SYSTEM))

EXTERNAL_DIR = IRIS_SYSTEM / "knowledge" / "raw" / "_external"

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

def render() -> None:
    st.markdown("## 🌐 외부응답")
    st.caption(
        "GPT, Gemini, Claude 등 외부 LLM 응답을 *보이는 그대로* 박는 자리. "
        "본문 변형 없이 보존. 분류·정제는 사후."
    )

    if not EXTERNAL_DIR.exists():
        try:
            EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
            st.success(f"✅ 저장 자리 신설: `{EXTERNAL_DIR}`")
        except Exception as e:
            st.error(f"저장 자리 생성 실패: {e}")
            return

    # ─── 새 이벤트 박기 ───────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📥 새 이벤트 박기")

    c1, c2 = st.columns([3, 1])
    with c1:
        title = st.text_input(
            "이벤트명 *",
            placeholder="예: MES 핵심 개념 정리 v3",
            key="ext_title",
        )
    with c2:
        source = st.selectbox("출처", SOURCES, index=0, key="ext_source")

    prompt = st.text_input(
        "원본 질의 (선택)",
        placeholder="예: MES 핵심 개념을 7장 분량으로 정리해줘",
        key="ext_prompt",
    )

    body = st.text_area(
        "답변 본문 * (markdown 그대로 붙여넣기)",
        height=600,
        placeholder="여기에 GPT/Gemini/Claude 답변을 그대로 붙여넣기...",
        key="ext_body",
    )

    if st.button(
        "💾 저장",
        type="primary",
        disabled=not (title and body),
        use_container_width=True,
        key="ext_save_btn",
    ):
        try:
            target = _save_event(
                title=title.strip(),
                source=source,
                body=body,
                prompt=prompt.strip() if prompt else None,
            )
            st.success(f"✅ 저장: `{target.relative_to(IRIS_SYSTEM)}`")
            st.caption("💡 인제스트는 별도 (다음 사이클에서 결정). 본문은 안전하게 박혔음.")
        except Exception as e:
            st.error(f"❌ 저장 실패: {e}")

    # ─── 최근 이벤트 ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📁 최근 박힌 이벤트")

    recent = _list_recent(n=10)
    if not recent:
        st.caption("아직 박힌 이벤트가 없음.")
        return

    st.caption(f"총 {len(recent)}건 (최근순). 클릭해서 미리보기.")
    for item in recent:
        with st.expander(
            f"**{item['title']}**  ·  *{item['source']}*  ·  "
            f"{item['mtime'].strftime('%Y-%m-%d %H:%M')}  ·  "
            f"{item['size']:,} bytes",
            expanded=False,
        ):
            try:
                preview = item["path"].read_text(encoding="utf-8")
                st.code(preview[:2000] + ("..." if len(preview) > 2000 else ""),
                        language="markdown")
                st.caption(f"경로: `{item['path']}`")
            except Exception as e:
                st.caption(f"읽기 실패: {e}")
