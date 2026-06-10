"""Platform entry point: multipage navigation built from the registry.

Run with ``streamlit run`` (the CLI's ``dashboard`` command does it). Pages:

- Dashboard: overview + one page per indicator, generated from the registry.
- Method: real-versus-synthetic calibration.
- Data science: warehouse explorer and the self-correcting training track.
"""

from __future__ import annotations

import streamlit as st

from if_pbm_open_demo.dashboard import data, theme
from if_pbm_open_demo.dashboard.views import (
    calibration,
    explorer,
    indicator,
    learn,
    overview,
)
from if_pbm_open_demo.registry import INDICATORS


def main() -> None:
    """Configure the app and run the navigation."""
    st.set_page_config(
        page_title="If-PBM Open Platform",
        page_icon="🩸",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.inject_theme()

    if not data.db_path().exists():
        st.warning(f"No database at `{data.db_path()}`. Run `if-pbm-demo demo` first.")
        st.stop()

    indicator_pages = {
        ind.key: st.Page(
            indicator.make_page(ind),
            title=f"{ind.key} · {ind.short_label}",
            icon=ind.icon,
            url_path=ind.key.lower(),
        )
        for ind in INDICATORS
    }
    # Overview KPI cards link to these pages (st.page_link needs the objects).
    st.session_state["page_refs"] = indicator_pages

    navigation = st.navigation(
        {
            "Dashboard": [
                st.Page(
                    overview.render,
                    title="Overview",
                    icon="🏠",
                    url_path="overview",
                    default=True,
                ),
                *indicator_pages.values(),
            ],
            "Method": [
                st.Page(
                    calibration.render,
                    title="Real vs synthetic",
                    icon="🎯",
                    url_path="calibration",
                ),
            ],
            "Data science": [
                st.Page(
                    explorer.render,
                    title="Warehouse explorer",
                    icon="🗄️",
                    url_path="explorer",
                ),
                st.Page(learn.render, title="Learn", icon="🎓", url_path="learn"),
            ],
        }
    )
    navigation.run()


if __name__ == "__main__":
    main()
