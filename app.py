import streamlit as st
from groq import Groq
import base64
import json
import html

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------

st.set_page_config(
    page_title="Engineering Mechanics AI Tutor — V3",
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
# IMAGE QUESTION SOLVER — V3
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

V3 GOAL:
Do not only solve the question.
First understand the mechanics model and build a Free-Body-Diagram analysis.

Your tasks:
1. Read the complete problem statement.
2. Inspect the complete engineering diagram.
3. Detect the most likely Engineering Mechanics topic.
4. Estimate the difficulty as Beginner, Intermediate, or Advanced.
5. Identify the body, particle, joint, member, beam, or system that should be isolated.
6. Identify every external force acting on the isolated body.
7. Identify support reactions, cable tensions, weights, applied loads, and relevant angles.
8. State useful x-y axes for the FBD.
9. Explain the FBD in short student-friendly language.
10. Determine all known and unknown quantities.
11. Select the correct Engineering Mechanics principle.
12. Solve the problem accurately.
13. Check the final result.

IMPORTANT:
Return ONLY valid JSON.
Do not return Markdown.
Do not return code.
Do not return code fences.
Do not return <think>.
Do not write anything before or after the JSON.

Use EXACTLY this structure:

{{
    "topic": "Short topic name",

    "difficulty": "Beginner, Intermediate, or Advanced",

    "problem_understanding": "Maximum 2 short sentences explaining the problem.",

    "given_data": [
        "Known quantity 1",
        "Known quantity 2"
    ],

    "required": [
        "Unknown quantity 1",
        "Unknown quantity 2"
    ],

    "fbd": {{
        "isolated_body": "What body, point, joint, member, beam, or system should be isolated",
        "axes": "Recommended positive x and y directions",
        "forces": [
            "Force 1 — magnitude if known — direction — where it acts",
            "Force 2 — magnitude if known — direction — where it acts"
        ],
        "support_reactions": [
            "Reaction 1",
            "Reaction 2"
        ],
        "fbd_note": "One or two short sentences explaining what the student should draw"
    }},

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

- Never invent a force, angle, support, dimension, or label that is not visible or logically implied.
- If something important is unclear, explicitly say it is unclear.
- For the FBD, include only EXTERNAL forces on the isolated body.
- Do not include forces that are internal to the isolated body.
- For a pin support, use two reaction components when appropriate.
- For a roller support, use one reaction normal to the contact surface when appropriate.
- For a cable, tension acts along the cable.
- For weight, use W = mg downward through the center of gravity when applicable.
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
            temperature=0.4,
            max_completion_tokens=4000
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as error:
        return {
            "error": f"An error occurred while reading the image: {error}"
        }

# -----------------------------
# TEXT CLEANER
# -----------------------------

def clean_equation(text):

    if text is None:
        return ""

    text = str(text)

    replacements = {
        r"\times": "×",
        r"\cdot": "×",
        "imes": "×",
        r"\div": "÷",
        "div": "÷",
        r"\sqrt": "√",
        r"\Sigma": "Σ",
        "Sigma": "Σ",
        r"\theta": "θ",
        r"\alpha": "α",
        r"\beta": "β",
        r"\sin": "sin",
        r"\cos": "cos",
        r"\tan": "tan",
        r"\pm": "±",
        r"\geq": "≥",
        r"\leq": "≤",
        r"\neq": "≠",
        "$": "",
        "`": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("_{", "")
    text = text.replace("{", "")
    text = text.replace("}", "")
    text = text.replace("\\", "")

    text = text.replace("F_Ay", "FAy")
    text = text.replace("F_Dy", "FDy")
    text = text.replace("F_A", "FA")
    text = text.replace("F_B", "FB")
    text = text.replace("F_C", "FC")
    text = text.replace("F_D", "FD")
    text = text.replace("F_x", "Fx")
    text = text.replace("F_y", "Fy")

    return " ".join(text.split())

# -----------------------------
# EQUATION DISPLAY
# -----------------------------

def display_equation(equation):

    equation = html.escape(clean_equation(equation))

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:20px;
            font-weight:500;
            padding:12px 16px;
            margin:8px 0;
            background-color:rgba(255,255,255,0.06);
            color:inherit;
            border:1px solid rgba(255,255,255,0.15);
            border-radius:8px;
        ">
            {equation}
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# FBD INTELLIGENCE DISPLAY — V3
# -----------------------------

def display_fbd_analysis(fbd):

    if not fbd:
        return

    st.markdown("### 🧩 Free-Body Diagram Analysis")

    if fbd.get("isolated_body"):
        st.markdown("**1. Isolate**")
        st.write(clean_equation(fbd["isolated_body"]))

    if fbd.get("axes"):
        st.markdown("**2. Choose Axes**")
        st.write(clean_equation(fbd["axes"]))

    if fbd.get("forces"):
        st.markdown("**3. External Forces**")
        for force in fbd["forces"]:
            st.write("• " + clean_equation(force))

    if fbd.get("support_reactions"):
        reactions = [
            item for item in fbd["support_reactions"]
            if item and clean_equation(item).lower() not in ["none", "not applicable", "n/a"]
        ]

        if reactions:
            st.markdown("**4. Support Reactions**")
            for reaction in reactions:
                st.write("• " + clean_equation(reaction))

    if fbd.get("fbd_note"):
        st.info("✏️ " + clean_equation(fbd["fbd_note"]))

# -----------------------------
# VISUAL IMAGE SOLUTION — V3
# -----------------------------

def display_visual_solution(solution):

    if not solution:
        st.error("No solution was generated.")
        return

    if solution.get("error"):
        st.error(solution["error"])
        return

    # V3 quick classification
    topic = clean_equation(solution.get("topic", "Engineering Mechanics"))
    difficulty = clean_equation(solution.get("difficulty", ""))

    if difficulty:
        st.caption(f"Detected topic: {topic}  •  Difficulty: {difficulty}")
    else:
        st.caption(f"Detected topic: {topic}")

    if solution.get("problem_understanding"):
        st.markdown("### 📘 Problem Understanding")
        st.write(clean_equation(solution["problem_understanding"]))

    if solution.get("given_data"):
        st.markdown("### 📌 Given Data")
        for item in solution["given_data"]:
            st.write("• " + clean_equation(item))

    if solution.get("required"):
        st.markdown("### 🎯 Required")
        required = solution["required"]

        if isinstance(required, list):
            for item in required:
                st.write("• " + clean_equation(item))
        else:
            st.write(clean_equation(required))

    # V3 flagship feature
    display_fbd_analysis(solution.get("fbd"))

    if solution.get("concept"):
        st.markdown("### 🧠 Concept Used")
        st.write(clean_equation(solution["concept"]))

    if solution.get("concept_equations"):
        for equation in solution["concept_equations"]:
            display_equation(equation)

    if solution.get("steps"):
        st.markdown("### ✏️ Solution")

        for step in solution["steps"]:

            if step.get("title"):
                st.markdown(f"#### {clean_equation(step['title'])}")

            if step.get("explanation"):
                st.write(clean_equation(step["explanation"]))

            if step.get("equations"):
                for equation in step["equations"]:
                    display_equation(equation)

            if step.get("result"):
                st.markdown(f"**✅ {clean_equation(step['result'])}**")

    if solution.get("engineering_check"):
        st.markdown("### 🔍 Engineering Check")

        checks = solution["engineering_check"]

        if isinstance(checks, list):
            for check in checks:
                st.write("✅ " + clean_equation(check))
        else:
            st.write("✅ " + clean_equation(checks))

    if solution.get("final_answers"):
        st.markdown("### 🏁 Final Answer")

        answers = solution["final_answers"]

        if isinstance(answers, list):
            for answer in answers:
                st.success(clean_equation(answer))
        else:
            st.success(clean_equation(answers))

    if solution.get("key_learning_point"):
        st.markdown("### 💡 Key Learning Point")
        st.info(clean_equation(solution["key_learning_point"]))

# -----------------------------
# USER INTERFACE
# -----------------------------

st.title("🏗️ Engineering Mechanics AI Tutor")

st.write(
    "Type an Engineering Mechanics problem or upload a question photo "
    "for a step-by-step solution."
)

st.caption("V3 — Statics Tutor + Free-Body Diagram Intelligence")

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

        with st.spinner("Analyzing mechanics model and solving..."):

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
                st.subheader("✏️ Solution")
                st.markdown(solution)

# -----------------------------
# FOOTER
# -----------------------------

st.divider()
st.caption("Engineering Mechanics AI Tutor — V3")
