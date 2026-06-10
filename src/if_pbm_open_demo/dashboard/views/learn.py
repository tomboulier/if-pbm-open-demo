"""Learn page: the self-correcting SQL training track.

Renders the exercises from :mod:`if_pbm_open_demo.training` and validates
attempts against the known ground truth, with progressive hints and a
revealable reference solution.
"""

from __future__ import annotations

import streamlit as st

from ...training import EXERCISES, Exercise, Feedback, check_attempt
from .. import data, theme

_LEVEL_LABELS = {
    1: "Level 1 · Explore",
    2: "Level 2 · Indicators",
    3: "Level 3 · Challenge",
}


def _progress() -> set[str]:
    solved: set[str] = st.session_state.setdefault("learn_solved", set())
    return solved


def _render_exercise(exercise: Exercise) -> None:
    solved = _progress()
    done = exercise.key in solved
    badge = "✅" if done else "⬜"
    with st.container(key=f"card-ex-{exercise.key}"):
        st.markdown(f"#### {badge} {exercise.title}")
        st.markdown(exercise.statement)

        sql = st.text_area(
            "Your SQL",
            value=exercise.starter_sql,
            height=190,
            key=f"learn_sql_{exercise.key}",
        )
        run_col, hint_col, solution_col = st.columns([1, 1, 1])
        with run_col:
            submitted = st.button(
                "Check my answer", type="primary", key=f"learn_run_{exercise.key}"
            )
        with hint_col:
            hint_count = st.session_state.setdefault(f"learn_hints_{exercise.key}", 0)
            if hint_count < len(exercise.hints) and st.button(
                f"Hint ({hint_count}/{len(exercise.hints)} used)",
                key=f"learn_hint_{exercise.key}",
            ):
                st.session_state[f"learn_hints_{exercise.key}"] = hint_count + 1
                st.rerun()
        with solution_col:
            show_solution = st.toggle("Show solution", key=f"learn_sol_{exercise.key}")

        for i in range(st.session_state[f"learn_hints_{exercise.key}"]):
            st.info(f"Hint {i + 1}: {exercise.hints[i]}")
        if show_solution:
            st.code(exercise.solution_sql, language="sql")

        if submitted:
            checked = check_attempt(data.db_path(), exercise, sql)
            st.session_state[f"learn_fb_{exercise.key}"] = checked
            if checked.ok:
                solved.add(exercise.key)
            # Rerun so the badge and the progress bar above reflect the result.
            st.rerun()

        feedback: Feedback | None = st.session_state.get(f"learn_fb_{exercise.key}")
        if feedback is not None:
            if feedback.ok:
                st.success(feedback.message)
            else:
                st.error(feedback.message)
                if feedback.expected_shape and feedback.got_shape:
                    st.caption(
                        f"Expected shape {feedback.expected_shape}, "
                        f"got {feedback.got_shape}."
                    )


def render() -> None:
    """Render the training track."""
    theme.banner(
        "Learn · data science on a clinical warehouse",
        "Write the SQL behind the If-PBM indicators yourself. Every answer is "
        "checked against the known ground truth of the synthetic warehouse.",
    )
    solved = _progress()
    st.progress(
        len(solved) / len(EXERCISES),
        text=f"{len(solved)} / {len(EXERCISES)} exercises solved",
    )
    st.caption(
        "Tip: keep the Warehouse explorer open in another tab to inspect "
        "tables while you work."
    )

    current_level: int | None = None
    for exercise in EXERCISES:
        if exercise.level != current_level:
            current_level = exercise.level
            st.markdown(f"### {_LEVEL_LABELS.get(current_level, current_level)}")
        _render_exercise(exercise)
        st.markdown("")
