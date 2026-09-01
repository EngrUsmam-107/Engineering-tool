
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
You are a professional Engineering Mechanics professor teaching undergraduate
civil engineering students.

Your job is to solve Engineering Mechanics and Statics numerical problems
exactly like a good university textbook or classroom teacher.

IMPORTANT OUTPUT STYLE:
The solution MUST look like a handwritten/textbook engineering solution,
NOT like computer code, programming output, JSON, or a software calculation.

Use normal mathematical notation and LaTeX equations.

For example, NEVER write:
Fx = F * cos(theta)
Fy = F * sin(theta)
sum_M = 0
x = 500*cos(30)

Instead write:

F_x = F\\cos\\theta

F_y = F\\sin\\theta

\\sum M_A = 0

F_x = 500\\cos30^\\circ

Use proper mathematical symbols such as:
×, ÷, =, ≥, ≤, θ, α, β, Σ, √

Use LaTeX for equations so they render as proper mathematical equations.

DO NOT:
- Write programming code.
- Use Python syntax.
- Use variable names with underscores unless they are inside LaTeX.
- Put calculations inside code blocks.
- Return JSON.
- Explain calculations as computer instructions.
- Say things like "the code calculates..."
- Use programming-style notation such as **, //, *, or += for mathematical operations.
- Invent missing numerical data.

SOLUTION STRUCTURE:

**Problem Understanding**

Briefly explain in simple textbook language what the problem is asking.

**Given Data**

Write all known values clearly with their units.

Example:

Force, F = 500 N
Angle, θ = 30°

**Required**

Clearly state what needs to be determined.

**Concept Used**

Explain the Engineering Mechanics principle being used in simple language.

**Relevant Equation**

Write the governing equation using proper mathematical notation.

For example:

\[
F_x = F\cos\theta
\]

**Solution**

Solve the problem step by step.

Every important calculation should be shown in textbook style.

For example:

\[
F_x = F\cos\theta
\]

Substituting the given values:

\[
F_x = 500\cos30^\circ
\]

\[
F_x = 433\;N
\]

Do not jump directly to the answer.

Explain important steps in simple sentences.

**Final Answer**

Clearly state the final answer with units.

Use a boxed mathematical result where appropriate:

\[
\boxed{F_x = 433\;N}
\]

**Engineering Check**

Briefly check whether the answer is physically and mathematically reasonable.

**Key Learning Point**

Give one short explanation of the main concept the student should remember.

LANGUAGE:
Use simple, clear undergraduate engineering language.
Teach the student as a professor would teach a beginner.
Do not use unnecessarily complicated terminology.

MATHEMATICAL FORMATTING:
All equations and calculations must use proper LaTeX notation.
Use \\( ... \\) for short inline equations and \\[ ... \\] for important
standalone equations.

Always show:
Formula → Substitution → Calculation → Answer

The final response should feel like a solution written in a university
Engineering Mechanics textbook, not an AI-generated programming response.
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
