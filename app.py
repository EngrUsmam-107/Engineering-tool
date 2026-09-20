import streamlit as st

from ai_engine import (
    solve_typed,
    solve_image,
    call_student_tool,
)
from ui import show_solution, render_app_styles, render_header

st.set_page_config(
    page_title="Engineering Mechanics AI Tutor",
    page_icon="🏗️",
    layout="centered",
    initial_sidebar_state="expanded",
)

render_app_styles()
render_header()

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "practice_problem" not in st.session_state:
    st.session_state.practice_problem = ""
if "practice_feedback" not in st.session_state:
    st.session_state.practice_feedback = ""

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎓 Student Settings")
    level = st.selectbox(
        "Explanation level",
        ["Beginner", "Standard", "Exam"],
        index=0,
    )

    st.markdown("### How the tutor works")
    st.write("1. 🔍 Checks the information")
    st.write("2. 📐 Builds the mechanics model")
    st.write("3. 🖊️ Draws an FBD when reliable")
    st.write("4. ✏️ Solves step by step")
    st.write("5. 🔎 Checks the result")
    st.write("6. 💡 Teaches the takeaway")

    st.divider()
    st.caption(
        "Learning aid only. Verify important engineering work with "
        "your textbook, instructor, or standard reference."
    )

mode = st.segmented_control(
    "Choose your learning mode",
    ["🚀 Solve", "✅ Check", "🧠 Learn", "🎯 Practice"],
    default="🚀 Solve",
)

# ------------------------------------------------------------
# SOLVE MODE
# ------------------------------------------------------------
if mode == "🚀 Solve":
    st.markdown("## 🚀 Solve an Engineering Mechanics Problem")

    input_mode = st.radio(
        "How do you want to provide the problem?",
        ["✍️ Type it", "📷 Upload a question"],
        horizontal=True,
    )

    if input_mode == "✍️ Type it":
        problem = st.text_area(
            "Problem statement",
            height=180,
            placeholder=(
                "Example: A particle is in equilibrium under three "
                "concurrent forces. Determine the unknown force."
            ),
        )

        if st.button(
            "🚀 Solve & Explain",
            type="primary",
            use_container_width=True,
        ):
            if not problem.strip():
                st.warning("Please enter a problem first.")
            else:
                with st.spinner(
                    "Understanding → checking data → solving → verifying..."
                ):
                    result = solve_typed(problem, level)
                show_solution(result)

    else:
        uploaded = st.file_uploader(
            "Upload a clear Engineering Mechanics question",
            type=["jpg", "jpeg", "png"],
            help=(
                "Include the complete diagram, labels, values, angles, "
                "and arrowheads."
            ),
        )

        if uploaded:
            st.image(
                uploaded,
                caption="Your uploaded question",
                use_container_width=True,
            )
            st.caption(
                "Tip: include the complete diagram and all labels. "
                "A clear crop normally gives better diagram analysis."
            )

        if st.button(
            "📐 Analyze, Solve & Teach",
            type="primary",
            use_container_width=True,
        ):
            if uploaded is None:
                st.warning("Please upload a question image first.")
            else:
                with st.spinner(
                    "Reading diagram → checking data → building FBD → "
                    "solving → checking..."
                ):
                    result = solve_image(uploaded, level)
                show_solution(result)

# ------------------------------------------------------------
# CHECK MODE
# ------------------------------------------------------------
elif mode == "✅ Check":
    st.markdown("## ✅ Check My Answer")
    st.caption(
        "Find the first important mistake instead of simply rewriting "
        "your entire solution."
    )

    question = st.text_area(
        "Original question",
        height=150,
        placeholder="Paste the question here.",
    )
    student_work = st.text_area(
        "Your working / answer",
        height=190,
        placeholder="Paste your equations and final answer here.",
    )

    if st.button(
        "🔎 Check My Work",
        type="primary",
        use_container_width=True,
    ):
        if not question.strip() or not student_work.strip():
            st.warning("Please enter both the question and your work.")
        else:
            instruction = f"""
Review this Engineering Mechanics student's work.

Question:
{question}

Student work:
{student_work}

Give a concise but useful tutoring response with these sections:
1. Verdict
2. What you did correctly
3. First mistake, if any
4. Corrected step
5. Correct final answer
6. Why this matters

Use beginner-friendly textbook language.
Put each equation on its own line.
Do not use LaTeX, programming syntax, JSON, or code.
"""
            with st.spinner(
                "Checking setup, equations, arithmetic and final answer..."
            ):
                out = call_student_tool(instruction, level, 1500)

            st.markdown("### 🔎 Tutor Feedback")
            st.markdown(out)

# ------------------------------------------------------------
# LEARN MODE
# ------------------------------------------------------------
elif mode == "🧠 Learn":
    st.markdown("## 🧠 Learn a Concept")

    topic = st.text_input(
        "What do you want to understand?",
        placeholder=(
            "e.g. equilibrium of a particle, FBDs, moments, friction"
        ),
    )

    if st.button(
        "🧠 Teach Me",
        type="primary",
        use_container_width=True,
    ):
        if not topic.strip():
            st.warning("Enter a topic first.")
        else:
            instruction = f"""
Teach this Engineering Mechanics topic:

{topic}

Use this structure:
1. What it means
2. Why it matters
3. Main rule/equations
4. A tiny worked example
5. Common student mistake
6. One quick self-test

Keep the explanation engaging, beginner-friendly and textbook-like.
Put every equation on its own line.
Do not use LaTeX, code, JSON, or programming notation.
"""
            with st.spinner("Building your mini-lesson..."):
                out = call_student_tool(instruction, level, 1400)

            st.markdown("### 📚 Mini Lesson")
            st.markdown(out)

# ------------------------------------------------------------
# PRACTICE MODE
# ------------------------------------------------------------
else:
    st.markdown("## 🎯 Practice Mode")

    topic = st.text_input(
        "Practice topic",
        placeholder=(
            "e.g. concurrent force equilibrium, moments, friction"
        ),
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Beginner", "Standard", "Challenge"],
        index=0,
    )

    if st.button(
        "🎯 Generate Practice Problem",
        type="primary",
        use_container_width=True,
    ):
        if not topic.strip():
            st.warning("Enter a topic first.")
        else:
            instruction = f"""
Create one original Engineering Mechanics practice problem on
{topic} at {difficulty} difficulty.

Give only:
Problem
Given
Required
Hint

Do not reveal the solution.
Use clean textbook notation.
Do not use LaTeX or code.
"""
            with st.spinner("Creating a practice problem..."):
                st.session_state.practice_problem = call_student_tool(
                    instruction,
                    level,
                    900,
                )
                st.session_state.practice_feedback = ""

    if st.session_state.practice_problem:
        st.markdown("### 📝 Your Practice Problem")
        st.markdown(st.session_state.practice_problem)

        student_answer = st.text_area(
            "Your solution",
            height=190,
            key="practice_answer",
            placeholder="Show your equations and final answer.",
        )

        if st.button(
            "🔎 Check Practice Solution",
            use_container_width=True,
        ):
            if not student_answer.strip():
                st.warning("Write your solution first.")
            else:
                instruction = f"""
Practice problem:
{st.session_state.practice_problem}

Student solution:
{student_answer}

Check it carefully.
State what is correct.
Identify the first important mistake, if any.
Show the corrected step.
Give the final answer.

Use clean textbook language.
Do not use LaTeX, code, JSON, or programming notation.
"""
                with st.spinner("Checking your practice work..."):
                    st.session_state.practice_feedback = call_student_tool(
                        instruction,
                        level,
                        1400,
                    )

        if st.session_state.practice_feedback:
            st.markdown("### 🔎 Practice Feedback")
            st.markdown(st.session_state.practice_feedback)

st.divider()
st.caption(
    "Engineering Mechanics AI Tutor • Student learning tool • "
    "Verify important engineering work independently."
)
