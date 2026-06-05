"""탭 4·5·6 placeholder — v1에서 도착 (V2.5.3 §3.1)"""
import streamlit as st


def render_insights() -> None:
    st.markdown("## 📊 인사이트")
    st.info("📍 **v1에서 도착** — Grafana iframe (KPI/fallback율). V2.5.1 §11.6: 관측은 Grafana 한 곳 정책 유지.")
    st.markdown(
        "현재 가동된 Grafana는 [http://127.0.0.1:3030](http://127.0.0.1:3030) 에서 직접 접근."
    )


def render_wiki() -> None:
    st.markdown("## 📚 위키")
    st.info("📍 **v1에서 도착** — broken_links, orphan_pages, duplicate_candidates 직접 표시.")
    st.markdown("현재는 `curl http://127.0.0.1:8081/wiki/lint`로 직접 호출 가능 (wiki server 가동 시).")


def render_settings() -> None:
    st.markdown("## ⚙️ 설정")
    st.info("📍 **v1에서 도착** — lane 필터, secure 토글, 모델 선택.")
