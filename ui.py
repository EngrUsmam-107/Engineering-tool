import html
import math

import matplotlib.pyplot as plt
import streamlit as st

from utils import clean_text, force_label, normalized_angle


def render_app_styles():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 1050px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.5rem;
            border-radius: 24px;
            border: 1px solid rgba(128,128,128,.22);
            background: linear-gradient(
                135deg,
                rgba(120,120,120,.13),
                rgba(120,120,120,.035)
            );
            margin-bottom: 1rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.15rem;
        }

        .hero p {
            margin: .45rem 0 0;
            opacity: .78;
            font-size: 1rem;
        }

        .pill {
            display: inline-block;
            padding: .28rem .65rem;
            margin: .6rem .3rem 0 0;
            border-radius: 999px;
            border: 1px solid rgba(128,128,128,.25);
            font-size: .78rem;
        }

        .section-card {
            border: 1px solid rgba(128,128,128,.20);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin: .7rem 0;
            background: rgba(127,127,127,.035);
        }

        .equation {
            text-align: center;
            font-size: 1.08rem;
            font-weight: 600;
            padding: .72rem .8rem;
            margin: .45rem 0;
            background: rgba(127,127,127,.075);
            border: 1px solid rgba(127,127,127,.20);
            border-radius: 12px;
            overflow-x: auto;
            white-space: normal;
        }

        .answer-card {
            border: 1px solid rgba(80,160,100,.35);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            background: rgba(80,160,100,.07);
            margin: .8rem 0;
        }

        .step-number {
            display: inline-block;
            min-width: 2rem;
            padding: .2rem .45rem;
            margin-right: .35rem;
            border-radius: 999px;
            background: rgba(127,127,127,.14);
            text-align: center;
            font-weight: 700;
        }

        div[data-testid="stTabs"] button {
            font-weight: 650;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="hero">
          <h1>🏗️ Engineering Mechanics AI Tutor</h1>
          <p>Understand → model → visualize → solve → verify → learn.</p>
          <span class="pill">📐 Engineering Mechanics</span>
          <span class="pill">🧠 AI Tutor</span>
          <span class="pill">📷 Diagram Analysis</span>
          <span class="pill">🎓 Student Mode</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_list(items, prefix="•"):
    if not isinstance(items, list):
        items = [items]

    for item in items:
        text = clean_text(item)
        if text:
            st.write(f"{prefix} {text}")


def display_equation(value):
    text = clean_text(value)

    if not text:
        return

    st.markdown(
        f'<div class="equation">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def show_data_check(data_check):
    if not isinstance(data_check, dict):
        return

    status = clean_text(
        data_check.get("status", "")
    ).lower()

    if status == "verified":
        st.success("✅ Data status: Verified")
    elif status == "uncertain":
        st.warning(
            "⚠️ Data status: Uncertain — review the notes before relying "
            "on the result."
        )
    elif status == "insufficient":
        st.error("❗ Data status: Insufficient information")

    show_list(data_check.get("notes", []))

    assumptions = data_check.get("assumptions", [])
    if assumptions:
        st.markdown("**Assumptions used:**")
        show_list(assumptions)


def render_fbd(fbd):
    if not isinstance(fbd, dict):
        return

    if not fbd.get("applicable"):
        return

    confidence = clean_text(
        fbd.get("confidence", "low")
    ).lower()

    items = []

    for group in ("forces", "support_reactions"):
        group_items = fbd.get(group, [])

        if isinstance(group_items, list):
            items.extend(
                item
                for item in group_items
                if isinstance(item, dict)
                and normalized_angle(item.get("angle_deg")) is not None
            )

    st.markdown("### 📐 Free-Body Diagram")

    if confidence == "low":
        st.warning(
            "The force geometry is uncertain, so the visual FBD is "
            "not drawn automatically. Review the extracted force list."
        )
    elif not items:
        st.info(
            "No reliable force directions were returned, so the visual "
            "FBD was skipped."
        )
    else:
        fig, ax = plt.subplots(figsize=(8.2, 5.8))

        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-1.55, 1.55)
        ax.set_ylim(-1.45, 1.45)

        # Isolated point.
        ax.scatter([0], [0], s=240, zorder=5)

        isolated = clean_text(
            fbd.get("isolated_label", "O")
        ) or "O"

        ax.text(
            0,
            -0.15,
            isolated,
            ha="center",
            va="top",
            fontweight="bold",
        )

        # Small coordinate axes.
        ax.annotate(
            "",
            xy=(1.35, -1.12),
            xytext=(0.65, -1.12),
            arrowprops=dict(
                arrowstyle="->",
                linewidth=1.3,
            ),
        )
        ax.text(1.40, -1.12, "+x", va="center")

        ax.annotate(
            "",
            xy=(0.65, -0.42),
            xytext=(0.65, -1.12),
            arrowprops=dict(
                arrowstyle="->",
                linewidth=1.3,
            ),
        )
        ax.text(
            0.65,
            -0.32,
            "+y",
            ha="center",
        )

        radius = 1.02

        for item in items:
            angle = normalized_angle(
                item.get("angle_deg")
            )

            a = math.radians(angle)
            dx = radius * math.cos(a)
            dy = radius * math.sin(a)

            ax.annotate(
                "",
                xy=(dx, dy),
                xytext=(0, 0),
                arrowprops=dict(
                    arrowstyle="->",
                    linewidth=2.0,
                ),
            )

            label = clean_text(
                item.get("label", "F")
            ) or "F"

            lx = 1.14 * math.cos(a)
            ly = 1.14 * math.sin(a)

            ax.text(
                lx,
                ly,
                label,
                ha="center",
                va="center",
                fontweight="bold",
            )

        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.caption(
        clean_text(
            fbd.get("axes_note", "+x right, +y up")
        )
    )

    st.markdown(
        "**Forces acting on the isolated body:**"
    )

    if not items:
        show_list(
            fbd.get("forces", []),
            prefix="•",
        )

    for item in items:
        label = force_label(item)
        direction = clean_text(
            item.get("direction_text", "")
        )

        angle = normalized_angle(
            item.get("angle_deg")
        )

        extra = (
            f" — {direction}"
            if direction
            else ""
        )

        if angle is not None:
            extra += (
                f" ({angle:.0f}° from +x)"
            )

        st.write(f"• {label}{extra}")

    if fbd.get("fbd_note"):
        st.caption(
            "✏️ " + clean_text(fbd["fbd_note"])
        )


def display_fallback_text(text):
    if not text:
        st.error("No usable solution was returned.")
        return

    st.markdown(clean_text(text))


def show_solution(data):
    if not isinstance(data, dict):
        st.error(
            "The AI returned an invalid solution format."
        )
        return

    if data.get("error"):
        st.error(clean_text(data["error"]))
        return

    if data.get("fallback_text"):
        st.warning(
            "The structured response was unavailable, so a cleaned "
            "textbook solution is shown instead."
        )
        display_fallback_text(
            data["fallback_text"]
        )
        return

    st.progress(
        1.0,
        text="Solution complete",
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📘 Understand",
            "📐 Model & FBD",
            "✏️ Solve",
            "🏁 Check & Learn",
        ]
    )

    with tab1:
        st.markdown(
            "### 📘 Problem Understanding"
        )

        st.write(
            clean_text(
                data.get(
                    "problem_understanding",
                    "",
                )
            )
        )

        left, right = st.columns(2)

        with left:
            st.markdown(
                "### 📌 Given Data"
            )
            show_list(
                data.get(
                    "given_data",
                    [],
                )
            )

        with right:
            st.markdown(
                "### 🎯 Required"
            )
            show_list(
                data.get(
                    "required",
                    [],
                )
            )

        st.markdown(
            "### 🔍 Data Check"
        )
        show_data_check(
            data.get(
                "data_check",
                {},
            )
        )

    with tab2:
        model = data.get(
            "mechanics_model",
            {},
        )

        st.markdown(
            "### 🧩 Mechanics Model"
        )

        if isinstance(model, dict):
            if model.get("relationships"):
                st.markdown(
                    "**Key relationships**"
                )
                show_list(
                    model["relationships"]
                )

            if model.get("unknowns"):
                unknowns = ", ".join(
                    clean_text(x)
                    for x in model["unknowns"]
                )
                st.markdown(
                    f"**Unknowns:** {unknowns}"
                )

            if model.get("equations"):
                st.markdown(
                    "**Governing equations**"
                )

                for equation in model["equations"]:
                    display_equation(
                        equation
                    )

        render_fbd(
            data.get("fbd", {})
        )

        st.markdown(
            "### 🧠 Concept Used"
        )

        st.write(
            clean_text(
                data.get(
                    "concept",
                    "",
                )
            )
        )

    with tab3:
        st.markdown(
            "### ✏️ Step-by-Step Solution"
        )

        steps = data.get(
            "steps",
            [],
        )

        if not steps:
            st.warning(
                "No calculation steps were returned."
            )

        for index, step in enumerate(
            steps,
            1,
        ):
            if not isinstance(
                step,
                dict,
            ):
                continue

            title = clean_text(
                step.get(
                    "title",
                    f"Step {index}",
                )
            )

            st.markdown(
                f"""
                <div class="section-card">
                    <h4>
                        <span class="step-number">
                            {index}
                        </span>
                        {html.escape(title)}
                    </h4>
                </div>
                """,
                unsafe_allow_html=True,
            )

            explanation = clean_text(
                step.get(
                    "explanation",
                    "",
                )
            )

            if explanation:
                st.write(
                    explanation
                )

            fields = [
                (
                    "formula",
                    "📐 Formula",
                ),
                (
                    "substitution",
                    "🔢 Substitution",
                ),
                (
                    "calculation",
                    "🧮 Calculation",
                ),
            ]

            for key, label in fields:
                value = step.get(key)

                if value:
                    st.markdown(
                        f"**{label}**"
                    )
                    display_equation(
                        value
                    )

            result = clean_text(
                step.get(
                    "result",
                    "",
                )
            )

            if result:
                st.success(
                    "✅ " + result
                )

    with tab4:
        st.markdown(
            "### 🏁 Final Answer"
        )

        answers = data.get(
            "final_answers",
            [],
        )

        if not isinstance(
            answers,
            list,
        ):
            answers = [answers]

        for answer in answers:
            answer = clean_text(
                answer
            )

            if answer:
                st.markdown(
                    f"""
                    <div class="answer-card">
                        <strong>
                            ✅ {html.escape(answer)}
                        </strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            "### 🔎 Engineering Check"
        )

        checks = data.get(
            "engineering_check",
            [],
        )

        if checks:
            for check in checks:
                st.success(
                    "✓ " + clean_text(check)
                )
        else:
            st.info(
                "No separate engineering check "
                "was returned."
            )

        st.markdown(
            "### 💡 Key Learning Point"
        )

        st.info(
            clean_text(
                data.get(
                    "key_learning_point",
                    "",
                )
            )
        )
