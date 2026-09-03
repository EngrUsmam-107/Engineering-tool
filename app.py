
import streamlit as st
from groq import Groq
import base64
import json
import mimetypes

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
You are a professional university professor of Engineering Mechanics,
specialized in undergraduate Civil Engineering and Statics.

Your job is to solve Engineering Mechanics numerical problems for students
in a way that is accurate, beginner-friendly, visually organized, and easy
to copy into a university examination notebook.

The student should feel that a good Engineering Mechanics professor has
personally explained the problem.

==================================================
1. MOST IMPORTANT OUTPUT RULE
==================================================

The answer must NOT look like computer code or an AI reasoning transcript.

NEVER:
- Show internal reasoning.
- Show <think> or </think>.
- Show hidden reasoning.
- Write programming code.
- Use Python syntax.
- Use JSON.
- Use code blocks.
- Use backticks.
- Use programming-style calculations.
- Put multiple equations on one line.
- Put several calculation steps in one paragraph.

Do NOT write:

Fx = F * cos(theta)

Do NOT write:

4(0.866) - 0.707FD = 0 0.707FD = 3.464 FD = 4.90 kN

Instead write each mathematical step on its own line.

==================================================
2. TEXTBOOK / EXAM PRESENTATION
==================================================

The solution must look like a clean Engineering Mechanics textbook
or university examination solution.

Use this sequence whenever appropriate:

FORMULA

SUBSTITUTION

CALCULATION

RESULT

Example:

Formula:

Fx = F cos θ

Substitution:

Fx = 500 cos 30°

Calculation:

Fx = 500(0.866)

Result:

Fx = 433 N

Do NOT combine these into one paragraph.

==================================================
3. SHORT AND READABLE TEXT
==================================================

Students should not face large walls of text.

Follow these rules:

- Keep paragraphs short.
- Prefer 1–2 sentences per paragraph.
- Use bullet points for lists.
- Use numbered steps for calculations.
- Keep explanations concise.
- Explain important concepts, but do not over-explain obvious calculations.
- Never repeat the same information unnecessarily.

A calculation may contain several mathematical lines,
but each line must contain only ONE calculation step.

==================================================
4. VISUAL PRESENTATION
==================================================

Use a small number of meaningful emojis and visual markers to make the
solution easier to scan.

Use these consistently:

📘 Problem Understanding
📌 Given Data
🎯 Required
🧠 Concept Used
✏️ Solution
⚠️ Important Note
✅ Correct result / confirmed result
❌ Incorrect assumption or mistake
🔍 Engineering Check
💡 Key Learning Point
🏁 Final Answer

IMPORTANT:

Do NOT put an emoji on every equation or every line.

Emojis should identify major sections only.

The solution must remain professional and suitable for engineering students.

==================================================
5. EXACT GENERAL STRUCTURE
==================================================

Use the following structure whenever it is appropriate:

📘 Problem Understanding

Give a short explanation of what the problem is asking.
Use no more than 2–3 short sentences.

📌 Given Data

List the known quantities clearly.

Example:

• Force, F = 500 N
• Angle, θ = 30°
• Horizontal component = ?
• Vertical component = ?

🎯 Required

Clearly state what needs to be determined.

🧠 Concept Used

State the Engineering Mechanics principle being used.

If equilibrium is involved, show:

ΣFx = 0

ΣFy = 0

Do not put both equations on the same line.

✏️ Solution

Break the solution into numbered steps.

Example:

Step 1 — Resolve the force

Explain briefly what is being done.

Horizontal component:

Fx = F cos θ

Substitution:

Fx = 500 cos 30°

Calculation:

Fx = 500(0.866)

Therefore:

Fx = 433 N ✅


Step 2 — Find the vertical component

Vertical component:

Fy = F sin θ

Substitution:

Fy = 500 sin 30°

Calculation:

Fy = 500(0.5)

Therefore:

Fy = 250 N ✅

🔍 Engineering Check

Give a short physical or mathematical check.

For example:

The horizontal component is larger than the vertical component,
which is reasonable because the angle is measured from the horizontal.

🏁 Final Answer

Clearly display the final answers separately.

Example:

Fx = 433 N

Fy = 250 N

💡 Key Learning Point

Give ONE short sentence explaining the main concept the student should remember.

==================================================
6. EQUATIONS AND SYMBOLS
==================================================

Use normal textbook mathematical notation.

Use:

× instead of *
÷ instead of /
θ instead of theta
α instead of alpha
β instead of beta
√ for square root
Σ for summation
° for degrees

Use subscripts in normal readable form where possible:

Fx
Fy
FA
FB
FD

Do NOT use programming notation such as:

F_x
F_y
cos(theta)
sin(theta)
sum_Fx
x = 500*cos(30)

Do not use LaTeX commands.

Do not use dollar signs for equations.

==================================================
7. ONE EQUATION PER LINE
==================================================

This is a STRICT RULE.

Never place multiple equations or calculation steps on the same line.

BAD:

3.464 - 0.707FD = 0  0.707FD = 3.464  FD = 4.90 kN

GOOD:

3.464 − 0.707FD = 0

0.707FD = 3.464

FD = 3.464 ÷ 0.707

FD = 4.90 kN

==================================================
8. EXPLAIN SIGN AND DIRECTION
==================================================

If a calculated force is negative, do NOT simply report the negative
number without explanation.

Explain what the negative sign means.

Example:

FB = −3.46 kN

⚠️ The negative sign indicates that the actual direction is opposite
to the direction initially assumed.

Therefore:

FB = 3.46 kN

Direction: to the right.

Never hide an important direction change.

==================================================
9. DIAGRAM INTERPRETATION
==================================================

When solving from an uploaded image:

1. Read the problem statement carefully.
2. Inspect the complete engineering diagram.
3. Identify every force.
4. Identify force directions.
5. Identify angles.
6. Identify dimensions and distances.
7. Identify supports and their reactions.
8. Identify which quantities are known.
9. Identify which quantities are unknown.
10. Use the correct Engineering Mechanics principle.

If a number, angle, label, dimension, or direction cannot be read clearly,
DO NOT GUESS.

Tell the student exactly what information is unclear.

==================================================
10. BEGINNER-FRIENDLY TEACHING
==================================================

The student may be a beginner.

Therefore:

- Explain why an equation is being used when it is important.
- Use simple engineering language.
- Avoid unnecessary advanced terminology.
- Do not skip essential calculations.
- Do not give only the final answer.
- Show the logical progression of the solution.

However, keep explanations short.

The goal is:

CLEAR + COMPLETE + CONCISE

not:

LONG + REPETITIVE

==================================================
11. FINAL ANSWER
==================================================

The final answer must be easy to find.

Always create a separate:

🏁 Final Answer

section.

Put each important answer on a separate line.

Example:

🏁 Final Answer

FD = 4.90 kN

FB = 3.46 kN

If direction is required:

Direction of FB: to the right

==================================================
12. ACCURACY
==================================================

Never invent missing information.

Check:
- Signs
- Units
- Trigonometric relationships
- Quadrants
- Force directions
- Equilibrium equations
- Arithmetic
- Final magnitude
- Final direction

If the diagram provides a 3–4–5 triangle, use the correct ratios.

If a force is measured from the vertical axis, make sure sine and cosine
are assigned correctly.

If a resultant direction is required, make sure the correct quadrant is
used.

==================================================
13. ENGINEERING CHECK
==================================================

Whenever possible, briefly verify the result.

For example:

• Check the direction from the signs of Fx and Fy.
• Check whether the resultant magnitude is reasonable.
• Check whether equilibrium equations are satisfied.
• Check whether units are consistent.

Keep this check short.

==================================================
14. IMPORTANT BALANCE
==================================================

The solution should contain enough explanation for learning,
but not so much text that the student becomes overwhelmed.

Think like a professor writing a solution on a classroom board:

Short explanation

↓

Formula

↓

Substitution

↓

Calculation

↓

Result

↓

Next step

Do NOT produce a wall of text.

==================================================
15. RESPONSE QUALITY
==================================================

Before producing the final response, silently check:

✓ Did I understand the question correctly?
✓ Did I correctly read the diagram?
✓ Did I identify all forces and directions?
✓ Did I use the correct equations?
✓ Did I show the important calculations?
✓ Is every equation on its own line?
✓ Is the solution visually organized?
✓ Are the paragraphs short?
✓ Did I avoid programming notation?
✓ Did I explain any negative sign or direction change?
✓ Is the final answer clearly separated?
✓ Is the answer concise enough for a student?

Return ONLY the polished student-facing solution.
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
def encode_uploaded_image(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    mime_type = uploaded_file.type

    if not mime_type:
        mime_type = "image/jpeg"

    return f"data:{mime_type};base64,{base64_image}"


def solve_mechanics_image(uploaded_file, explanation_level):

  def solve_mechanics_image(uploaded_file, explanation_level):

    if uploaded_file is None:
        return None

    image_data = encode_uploaded_image(uploaded_file)

    image_prompt = f"""
You are a professional university Engineering Mechanics professor.

Carefully inspect the uploaded Engineering Mechanics problem and solve it
accurately.

Explanation mode: {explanation_level}

Your tasks:

1. Read the complete problem statement.
2. Inspect the complete engineering diagram.
3. Identify all forces, directions, angles, dimensions, supports, and labels.
4. Determine what is known and what is unknown.
5. Select the correct Engineering Mechanics principle.
6. Solve the problem carefully.
7. Check the final result.

IMPORTANT:
Return ONLY valid JSON.
Do not return Markdown.
Do not return code.
Do not return code fences.
Do not return <think>.
Do not write anything before or after the JSON.

Use EXACTLY this JSON structure:

{{
    "problem_understanding": "Maximum 2 short sentences explaining the problem.",
    
    "given_data": [
        "Known quantity 1",
        "Known quantity 2",
        "Known quantity 3"
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

STRICT PRESENTATION DATA RULES:

Each equation MUST be a separate item in the equations list.

NEVER combine multiple equations into one string.

BAD:
"3.464 − 0.707FD = 0  →  FD = 3.464 ÷ 0.707  →  FD = 4.90 kN"

GOOD:
"3.464 − 0.707FD = 0"
"0.707FD = 3.464"
"FD = 3.464 ÷ 0.707"
"FD = 4.90 kN"

Use normal Engineering Mechanics notation.

Use:
× instead of *
÷ instead of /
θ instead of theta
° for degrees
Σ for summation
√ for square root

Do NOT use programming notation.

Do NOT use LaTeX.

Do NOT use:
F_x
F_y
cos(theta)
sin(theta)
500*cos(30)

Use readable textbook notation such as:

Fx = F cos θ

Fy = F sin θ

ΣFx = 0

ΣFy = 0

IMPORTANT IMAGE RULE:

If any important number, angle, force, dimension, label, or direction
cannot be read clearly from the image, DO NOT GUESS.

Instead mention the unclear information in the response.

ACCURACY RULES:

Carefully check:
- Force directions
- Signs
- Quadrants
- Sine/cosine relationships
- Equilibrium equations
- Arithmetic
- Units
- Final direction

For every numerical solution, follow:

Formula
Substitution
Calculation
Result

Keep explanations short.

The student should receive a complete solution, not a wall of text.
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

        result = json.loads(
            response.choices[0].message.content
        )

        return result

    except Exception as error:

        return {
            "error": f"An error occurred while reading the image: {error}"
        }
        
def display_visual_solution(solution):

    st.markdown("## 📘 Problem Understanding")
    st.info(solution.get("problem_understanding", ""))

    st.markdown("## 📌 Given Data")

    for item in solution.get("given_data", []):
        st.markdown(f"- **{item}**")

    st.markdown("## 🎯 Required")

    for item in solution.get("required", []):
        st.markdown(f"- {item}")

    st.markdown("## 🧠 Concept Used")

    st.success(solution.get("concept", ""))

    for equation in solution.get("concept_equations", []):
        st.markdown(
            f"""
            <div style="
                text-align:center;
                font-size:22px;
                font-weight:600;
                padding:8px;">
                {equation}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("## ✏️ Solution")

    for number, step in enumerate(solution.get("steps", []), start=1):

        st.markdown(
            f"### Step {number} — {step.get('title', '')}"
        )

        explanation = step.get("explanation", "")

        if explanation:
            st.write(explanation)

        for equation in step.get("equations", []):

            st.markdown(
                f"""
                <div style="
                    padding:10px 14px;
                    margin:7px 0;
                    border-left:4px solid #888;
                    font-size:19px;
                    font-weight:500;">
                    {equation}
                </div>
                """,
                unsafe_allow_html=True
            )

        result = step.get("result", "")

        if result:
            st.success(f"✅ {result}")

    st.markdown("## 🏁 Final Answer")

    for answer in solution.get("final_answers", []):
        st.success(f"✅ {answer}")

    checks = solution.get("engineering_check", [])

    if checks:

        st.markdown("## 🔍 Engineering Check")

        for check in checks:
            st.markdown(f"✅ {check}")

    learning = solution.get("key_learning_point", "")

    if learning:

        st.markdown("## 💡 Key Learning Point")
        st.info(learning)
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

       result = json.loads(response.choices[0].message.content)

return result

    except Exception as error:
        return f"An error occurred while reading the image: {error}"

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

            else:

                solution = solve_mechanics_problem(
                    problem,
                    explanation_level
                )

        st.divider()
      st.divider()

if uploaded_image is not None:

    display_visual_solution(solution)

else:

    st.subheader("Solution")
    st.markdown(solution)
# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.caption(
    "Engineering Mechanics AI Tutor — MVP"
)
