
import streamlit as st
from groq import Groq


# -----------------------------
# PAGE CONFIGURATION
# -----------------------------

st.set_page_config(
    page_title="Engineering Mechanics AI Tutor",
    page_icon="🏗️",
    layout="centered"
)


# -----------------------------
# GROQ API KEY
# -----------------------------

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=GROQ_API_KEY)


# -----------------------------
# SYSTEM PROMPT
# -----------------------------

SYSTEM_PROMPT = """
You are an Engineering Mechanics tutor specialized in undergraduate Statics.

Your goal is to help engineering students understand numerical problems
step by step instead of only giving them the final answer.

Always structure your response using these sections:

## Problem Understanding

Briefly explain what needs to be determined.

## Given Data

List all known quantities clearly with units.

## Concept Used

Identify the Engineering Mechanics topic and physical principle being used.

## Equations

Show the relevant equations.

## Step-by-Step Solution

Solve the numerical carefully.

Explain why important equations and steps are being used.

## Final Answer

Clearly state the final numerical answer with units.

## Engineering Check

Check whether the result is mathematically and physically reasonable.

## Key Learning Point

Explain the main concept the student should learn from the problem.

Important rules:

- Do not skip important calculation steps.
- Never invent missing numerical information.
- If important information is missing, clearly tell the student what is missing.
- State assumptions explicitly.
- Maintain correct units throughout the solution.
- Use beginner-friendly undergraduate engineering language.
- Focus primarily on Engineering Mechanics and Statics.
- Do not pretend a result is verified if you are uncertain.
"""


# -----------------------------
# SOLVER FUNCTION
# -----------------------------

def solve_mechanics_problem(problem, explanation_level):

    if not problem.strip():
        return "Please enter an Engineering Mechanics numerical problem."

    level_instruction = {

        "Beginner": """
Explain every important step in simple language.
Assume the student is still learning the topic.
Explain why formulas are selected.
""",

        "Standard": """
Give a balanced university-level solution.
Explain important reasoning while avoiding unnecessary detail.
""",

        "Exam": """
Give a concise exam-style solution.
Show all essential equations and calculations,
but keep explanations short.
"""
    }

    user_prompt = f"""
Student explanation mode: {explanation_level}

Instructions:

{level_instruction[explanation_level]}

Problem:

{problem}
"""

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as error:

        return f"""
An error occurred while solving the problem.

Please try again.

Technical error:

{str(error)}
"""


# -----------------------------
# USER INTERFACE
# -----------------------------

st.title("🏗️ Engineering Mechanics AI Tutor")

st.write(
    "Enter an Engineering Mechanics numerical problem "
    "and receive a step-by-step explanation."
)

st.caption(
    "MVP — Engineering Mechanics / Statics"
)


explanation_level = st.radio(
    "Explanation Level",
    ["Beginner", "Standard", "Exam"],
    horizontal=True
)


problem = st.text_area(
    "Enter your numerical problem",

    height=220,

    placeholder="""
Example:

A simply supported beam AB has a span of 6 m.
A point load of 12 kN acts 2 m from support A.

Find the reactions at supports A and B.
"""
)


solve_button = st.button(
    "Solve Problem",
    type="primary",
    use_container_width=True
)


if solve_button:

    if not problem.strip():

        st.warning("Please enter a problem first.")

    else:

        with st.spinner("Solving the problem..."):

            solution = solve_mechanics_problem(
                problem,
                explanation_level
            )

        st.divider()

        st.subheader("Solution")

        st.markdown(solution)


# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.caption(
    "Engineering Mechanics AI Tutor — MVP"
)
