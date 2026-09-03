import streamlit as st
from groq import Groq
import base64
import json

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
# SYSTEM PROMPT — TYPED QUESTIONS
# -----------------------------

SYSTEM_PROMPT = """
You are a professional university professor of Engineering Mechanics,
specialized in undergraduate Civil Engineering and Statics.

Your job is to solve Engineering Mechanics numerical problems accurately,
beginner-friendly, and in a clean university-examination style.

The answer must be student-facing. Never show internal reasoning,
<think>, code, JSON, code fences, or programming syntax.

Use this structure whenever appropriate:

📘 Problem Understanding
📌 Given Data
🎯 Required
🧠 Concept Used
✏️ Solution
🔍 Engineering Check
🏁 Final Answer
💡 Key Learning Point

For numerical calculations, follow:

Formula
Substitution
Calculation
Result

Put ONE mathematical step on each line.
Keep explanations short and clear.
Use normal textbook notation such as:
Fx, Fy, FA, FB, FD, ΣFx, ΣFy, θ, α, β, ×, ÷, √, °.

Do not use programming notation such as:
F_x
F_y
cos(theta)
sin(theta)
500*cos(30)

Do not use LaTeX commands or dollar signs.

Never invent missing information.
State assumptions when necessary.
If a calculated force is negative, explain that the actual direction
is opposite to the assumed direction.

Always check signs, units, force directions, trigonometry, equilibrium,
arithmetic, and final direction.

The goal is:
CLEAR + COMPLETE + CONCISE
"""

# -----------------------------
# TYPED QUESTION SOLVER
# -----------------------------

def solve_mechanics_problem(problem, explanation_level):

    if not problem.strip():
        return "Please enter an Engineering Mechanics numerical problem."

    level_instruction = {
        "Beginner": """
Explain every important step in simple language.
Assume the student is still learning the topic.
Briefly explain why important formulas are selected.
""",
        "Standard": """
Give a balanced university-level solution.
Explain important reasoning without unnecessary detail.
""",
        "Exam": """
Give a concise exam-style solution.
Show all essential equations and calculations.
Keep explanations short.
"""
    }

    user_prompt = f"""
Student explanation mode: {explanation_level}

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
# IMAGE ENCODING
# -----------------------------

def encode_uploaded_image(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    mime_type = uploaded_file.type or "image/jpeg"

    return f"data:{mime_type};base64,{base64_image}"

# -----------------------------
# IMAGE QUESTION SOLVER
# -----------------------------

def solve_mechanics_image(uploaded_file, explanation_level):

    if uploaded_file is None:
        return None

    image_data = encode_uploaded_image(uploaded_file)

    image_prompt = f"""
You are a professional university professor of Engineering Mechanics,
specialized in undergraduate Civil Engineering and Statics.

Carefully inspect the uploaded Engineering Mechanics question and diagram.

Explanation mode: {explanation_level}

Your tasks:
1. Read the complete problem statement.
2. Inspect the complete engineering diagram.
3. Identify all forces, directions, angles, dimensions, supports, and labels.
4. Determine all known and unknown quantities.
5. Select the correct Engineering Mechanics principle.
6. Solve the problem accurately.
7. Check the final result.

IMPORTANT:
Return ONLY valid JSON.
Do not return Markdown.
Do not return code.
Do not return code fences.
Do not return <think>.
Do not write anything before or after the JSON.

Use EXACTLY this structure:

{{
    "problem_understanding": "Maximum 2 short sentences explaining the problem.",

    "given_data": [
        "Known quantity 1",
        "Known quantity 2"
    ],

    "required": [
        "Unknown quantity 1",
        "Unknown quantity 2"
    ],

    "concept": "Short explanation of the Engineering Mechanics concept.",

    "concept_equations": [
        "ΣFx = 0",
        "ΣFy = 0"
    ],

    "steps": [
        {{
            "title": "Short step title",
            "explanation": "Maximum 1 or 2 short sentences.",
            "equations": [
                "First equation",
                "Second equation",
                "Third equation"
            ],
            "result": "Final result of this step"
        }}
    ],

    "final_answers": [
        "Final answer 1",
        "Final answer 2"
    ],

    "engineering_check": [
        "Short verification statement",
        "Another short verification statement"
    ],

    "key_learning_point": "One short sentence."
}}

STRICT RULES:

- Each equation must be a separate item in the equations list.
- Never combine multiple calculation steps into one string.
- Use one equation per line.
- Use normal textbook notation.
- Use × instead of *
- Use ÷ instead of /
- Use θ instead of theta
- Use ° for degrees
- Use Σ for summation
- Use √ for square root
- Do not use LaTeX.
- Do not use programming notation such as F_x, F_y, cos(theta), sin(theta), or 500*cos(30).
- Do not guess any unclear number, angle, force, dimension, label, or direction.
- If important information is unreadable, clearly state what is unclear.
- Follow Formula → Substitution → Calculation → Result.
- Keep explanations concise.
- Make the solution complete enough for a beginner to learn from.
"""

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            reasoning_effort="none",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": image_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_completion_tokens=4000
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as error:
        return {
            "error": f"An error occurred while reading the image: {error}"
        }

# -----------------------------
# VISUAL IMAGE SOLUTION
# -----------------------------

def display_visual_solution(solution):

   def clean_equation(text):
    """Convert common LaTeX/programming-style notation into clean textbook notation."""

    if not isinstance(text, str):
        return str(text)

    replacements = {
        r"\times": " × ",
        r"\cdot": " × ",
        r"\div": " ÷ ",
        r"\sqrt": "√",
        r"\Sigma": "Σ",
        r"\theta": "θ",
        r"\alpha": "α",
        r"\beta": "β",
        r"\sin": "sin",
        r"\cos": "cos",
        r"\tan": "tan",
        "imes": "×",
        "div": "÷",
        "Sigma": "Σ",
        "_{": "",
        "}": "",
        "$": "",
        "`": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("\\", "")

    text = text.replace("F_Ay", "FAy")
    text = text.replace("F_Dy", "FDy")
    text = text.replace("F_A", "FA")
    text = text.replace("F_B", "FB")
    text = text.replace("F_C", "FC")
    text = text.replace("F_D", "FD")
    text = text.replace("F_x", "Fx")
    text = text.replace("F_y", "Fy")

    text = " ".join(text.split())

    return text.strip()


def display_equation(equation):
    """Display one equation in a clean textbook style."""

    equation = clean_equation(equation)

    st.markdown(
        f"""
        <div style="
            text-align: center;
            font-size: 20px;
            font-weight: 500;
            padding: 10px 14px;
            margin: 7px 0;
            border-left: 4px solid #888;
            background-color: rgba(128,128,128,0.06);
            overflow-x: auto;
        ">
            {equation}
        </div>
        """,
        unsafe_allow_html=True
    )


def display_visual_solution(solution):

    if not isinstance(solution, dict):
        st.error("The image solution could not be displayed.")
        return

    if solution.get("error"):
        st.error(solution["error"])
        return

    st.markdown("## 📘 Problem Understanding")

    understanding = solution.get("problem_understanding", "")

    if understanding:
        st.info(understanding)

    st.markdown("## 📌 Given Data")

    for item in solution.get("given_data", []):
        st.markdown(f"- **{clean_equation(item)}**")

    st.markdown("## 🎯 Required")

    for item in solution.get("required", []):
        st.markdown(f"- {clean_equation(item)}")

    st.markdown("## 🧠 Concept Used")

    concept = solution.get("concept", "")

    if concept:
        st.success(concept)

    concept_equations = solution.get("concept_equations", [])

    if concept_equations:
        st.markdown("### Governing Equations")

        for equation in concept_equations:
            display_equation(equation)

    st.markdown("## ✏️ Solution")

    for number, step in enumerate(
        solution.get("steps", []),
        start=1
    ):

        title = step.get("title", f"Step {number}")

        st.markdown(
            f"### Step {number} — {clean_equation(title)}"
        )

        explanation = step.get("explanation", "")

        if explanation:
            st.write(explanation)

        for equation in step.get("equations", []):
            display_equation(equation)

        result = step.get("result", "")

        if result:
            st.success(
                f"✅ {clean_equation(result)}"
            )

    final_answers = solution.get("final_answers", [])

    if final_answers:
        st.markdown("## 🏁 Final Answer")

        for answer in final_answers:
            st.success(
                f"✅ {clean_equation(answer)}"
            )

    checks = solution.get("engineering_check", [])

    if checks:
        st.markdown("## 🔍 Engineering Check")

        for check in checks:
            st.markdown(
                f"✅ {clean_equation(check)}"
            )

    learning = solution.get("key_learning_point", "")

    if learning:
        st.markdown("## 💡 Key Learning Point")
        st.info(learning)
# -----------------------------
# USER INTERFACE
# -----------------------------

st.title("🏗️ Engineering Mechanics AI Tutor")

st.write(
    "Enter an Engineering Mechanics numerical problem "
    "or upload a question photo to receive a step-by-step solution."
)

st.caption("MVP — Engineering Mechanics / Statics")

explanation_level = st.radio(
    "Explanation Level",
    ["Beginner", "Standard", "Exam"],
    horizontal=True
)

problem = st.text_area(
    "Enter your numerical problem",
    height=220,
    placeholder="""Example:

A simply supported beam AB has a span of 6 m.
A point load of 12 kN acts 2 m from support A.

Find the reactions at supports A and B.
"""
)

st.write("### Or upload a question photo")

uploaded_image = st.file_uploader(
    "Upload an Engineering Mechanics question",
    type=["jpg", "jpeg", "png"]
)

if uploaded_image is not None:
    st.image(
        uploaded_image,
        caption="Uploaded Question",
        use_container_width=True
    )

# -----------------------------
# SOLVE BUTTON
# -----------------------------

if st.button(
    "Solve Problem",
    type="primary",
    use_container_width=True
):

    if not problem.strip() and uploaded_image is None:

        st.warning(
            "Please type a problem or upload a question photo."
        )

    else:

        with st.spinner("Analyzing and solving the problem..."):

            if uploaded_image is not None:

                solution = solve_mechanics_image(
                    uploaded_image,
                    explanation_level
                )

                st.divider()
                display_visual_solution(solution)

            else:

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
