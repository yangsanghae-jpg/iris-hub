"""client/dev/antd_iframe_probe.py — Task A go/no-go gate probe.

Smallest possible standalone Streamlit script to check whether the AntD v5
mockup (antd_pptx_mock.html) renders correctly inside a Streamlit
`st.components.v1.html` sandboxed iframe, versus a plain browser tab.

This file is NOT wired into app.py and does NOT touch src/tabs/pptx.py.
Run it in isolation:

    streamlit run client/dev/antd_iframe_probe.py --server.port 8599

Then open http://localhost:8599 and compare against opening
antd_pptx_mock.html directly (file://) in a plain browser tab.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AntD iframe probe", layout="wide")

st.title("AntD × iris-hub PPT mockup — iframe probe (Task A gate)")
st.caption(
    "Go/no-go check: does antd_pptx_mock.html render identically inside "
    "Streamlit's sandboxed components.html iframe as it does in a plain "
    "browser tab? Look for missing styles, blank areas, or console errors "
    "(open browser devtools on this page)."
)

_html_path = Path(__file__).parent / "antd_pptx_mock.html"
html = _html_path.read_text(encoding="utf-8")

components.html(html, height=1550, scrolling=True)
