"""Warehouse explorer: canonical tables and a free SQL playground.

This page deliberately exposes the canonical schema (the input port): it is
the teaching surface of the platform. BI pages never read these tables.
"""

from __future__ import annotations

import streamlit as st

from .. import data, theme

_TABLE_BLURBS = {
    "patient": "One row per patient (demographics only).",
    "surgery": "One row per surgery: specialty and date. The cohort spine.",
    "consultation": (
        "Pre-anesthesia consultations: PBM check-up done, anemia / iron "
        "deficiency detected, correction given (drives IR1 and IR2)."
    ),
    "lab": "Lab results; post-operative hemoglobin drives IR5.",
    "transfusion": (
        "RBC units with delivery timestamps; episodes (units < 1 h apart) "
        "drive IR3, transfused patients drive IR4."
    ),
    "period": (
        "The reporting calendar: If-PBM trimesters are rolling three-month "
        "windows, not calendar quarters, so they must be joined by date range."
    ),
}

_EXAMPLES = {
    "Surgeries per specialty": (
        "SELECT specialty, count(*) AS n_surgeries\n"
        "FROM surgery\nGROUP BY specialty\nORDER BY n_surgeries DESC"
    ),
    "Surgeries per trimester": (
        "SELECT pd.period, count(*) AS n_surgeries\n"
        "FROM surgery s\n"
        "JOIN period pd ON s.surgery_date BETWEEN pd.start_date AND pd.end_date\n"
        "GROUP BY pd.period\nORDER BY pd.period"
    ),
    "Transfused patients (IR4 numerator idea)": (
        "SELECT s.specialty, count(DISTINCT t.surgery_id) AS transfused\n"
        "FROM transfusion t\n"
        "JOIN surgery s ON s.surgery_id = t.surgery_id\n"
        "GROUP BY s.specialty"
    ),
}


def render() -> None:
    """Render the explorer page."""
    theme.banner(
        "Warehouse explorer",
        "The canonical schema of the synthetic clinical data warehouse: "
        "browse the tables, then query them freely (read-only DuckDB SQL).",
    )
    path = str(data.db_path())

    counts = data.table_counts(path).set_index("table_name")["rows_"]
    columns = st.columns(3)
    for i, (table, blurb) in enumerate(_TABLE_BLURBS.items()):
        with columns[i % 3], st.container(key=f"card-table-{table}"):
            st.markdown(f"#### `{table}`")
            st.markdown(blurb)
            st.caption(f"{int(counts.get(table, 0)):,} rows")

    st.markdown("")
    with st.container(key="card-preview"):
        st.markdown("#### Table preview")
        table = st.selectbox("Table", list(_TABLE_BLURBS), key="explorer_table")
        st.dataframe(
            data.table_preview(path, table),
            width="stretch",
            hide_index=True,
        )

    st.markdown("")
    with st.container(key="card-playground"):
        st.markdown("#### SQL playground")
        example = st.selectbox(
            "Start from an example", ["(blank)", *list(_EXAMPLES)], key="sql_example"
        )
        default_sql = _EXAMPLES.get(example, "SELECT * FROM surgery LIMIT 10")
        sql = st.text_area("Query", value=default_sql, height=160, key="sql_query")
        if st.button("Run query", type="primary"):
            try:
                result = data.run_user_query(path, sql)
            except Exception as exc:  # noqa: BLE001 - surfaced to the learner
                st.error(f"Query failed: {exc}")
            else:
                st.dataframe(result, width="stretch", hide_index=True)
                st.caption(f"{len(result):,} rows")
