"""Shared UI helpers for iris-hub Streamlit tabs."""
from __future__ import annotations

from html import escape
from typing import Literal, Sequence, Union

import streamlit as st


SectionLevel = Literal["page", "sub"]
KpiRow = tuple[str, str, str]
BarRow = tuple[str, Union[int, float]]
KeyValueRow = tuple[str, str]


def hub_section(text: str, *, level: SectionLevel = "sub") -> None:
    """Render a consistent, compact section heading across hub tabs."""
    if level == "page":
        st.markdown(f"#### {escape(text)}")
        return

    st.markdown(
        f"<div class='hub-section'>{escape(text)}</div>",
        unsafe_allow_html=True,
    )


def hub_pagebar(title: str, label: str, description: str, status: str) -> None:
    """Render the compact page header used by dashboard-style tabs."""
    st.markdown(
        f"""
<div class="hub-pagebar">
  <div>
    <div class="hub-pagebar-title-row">
      <h1 class="hub-pagebar-title">{escape(title)}</h1>
      <span class="hub-pagebar-label">{escape(label)}</span>
    </div>
    <p class="hub-pagebar-desc">{escape(description)}</p>
  </div>
  <span class="hub-pill">{escape(status)}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def hub_kpi_grid(rows: Sequence[KpiRow]) -> None:
    """Render compact KPI cards in one row."""
    cards = []
    for label, value, caption in rows:
        cards.append(
            f"""
<div class="hub-kpi-card">
  <div class="hub-kpi-row">
    <span class="hub-kpi-label">{escape(label)}</span>
    <span class="hub-kpi-value">{escape(value)}</span>
  </div>
  <div class="hub-kpi-caption">{escape(caption)}</div>
</div>
"""
        )
    st.markdown(f"<div class='hub-kpi-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def hub_bar_rows(rows: Sequence[BarRow]) -> str:
    """Return compact horizontal percentage bars as HTML."""
    html_parts = []
    for label, value in rows:
        normalized_value = max(0.0, min(float(value), 100.0))
        html_parts.append(
            f"""
<div class="hub-bar-row">
  <div class="hub-bar-label-row">
    <span>{escape(label)}</span>
    <strong class="hub-bar-value">{normalized_value:.0f}%</strong>
  </div>
  <div class="hub-mini-track"><div class="hub-mini-fill" style="width:{normalized_value:.1f}%"></div></div>
</div>
"""
        )
    return "".join(html_parts)


def hub_key_value_rows(rows: Sequence[KeyValueRow]) -> str:
    """Return compact readiness/status rows as HTML."""
    return "".join(
        f"""
<div class="hub-readiness-row">
  <span>{escape(label)}</span>
  <strong class="hub-ok">{escape(value)}</strong>
</div>
"""
        for label, value in rows
    )


def hub_panel(title: str, body_html: str, *, subtitle: str | None = None) -> str:
    """Return a compact panel as HTML for mostly static dashboard content."""
    subtitle_html = (
        f"<div class='hub-panel-subtitle'>{escape(subtitle)}</div>" if subtitle else ""
    )
    return f"""
<div class="hub-panel">
  <div class="hub-panel-head">
    <div class="hub-panel-title">{escape(title)}</div>
    {subtitle_html}
  </div>
  <div class="hub-panel-body">{body_html}</div>
</div>
"""


def hub_two_col(left_html: str, right_html: str) -> None:
    """Render two compact panels/blocks in the standard dashboard grid."""
    st.markdown(
        f"<div class='hub-two-col'>{left_html}{right_html}</div>",
        unsafe_allow_html=True,
    )


def hub_equal_col(left_html: str, right_html: str) -> None:
    """Render equal-width compact panels/blocks."""
    st.markdown(
        f"<div class='hub-equal-col'>{left_html}{right_html}</div>",
        unsafe_allow_html=True,
    )
