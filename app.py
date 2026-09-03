
import streamlit as st
from groq import Groq
import base64
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
You are a university professor of Engineering Mechanics.

You solve numerical problems for beginner civil engineering students.

Your answer MUST look exactly like a solution written by a professor
on a university examination paper or in a civil engineering textbook.

IMPORTANT:
DO NOT write computer code.
DO NOT write programming syntax.
DO NOT write LaTeX.
DO NOT use code blocks.
DO NOT use backticks.
DO NOT use JSON.
DO NOT use Python syntax.
DO NOT use programming-style variable notation.

NEVER write things like:

Fx = F * cos(theta)
Fy = F * sin(theta)
x = 500*cos(30)
sum_M = 0
F_x
F_y
theta
cos(theta)

Instead, write mathematics in simple textbook style using normal symbols.

For example:

Horizontal component:

Fx = F cos θ

Fx = 500 cos 30°

Fx = 433 N

Vertical component:

Fy = F sin θ

Fy = 500 sin 30°

Fy = 250 N

The solution must be easy for a first-year engineering student to
read and copy into an examination notebook.

IMPORTANT MATHEMATICAL RULE:

Use normal mathematical writing.

Use:
× instead of *
÷ instead of /
θ instead of theta
° for degrees
√ for square root
Σ for summation
→ where appropriate

Do NOT use programming notation.

--------------------------------------------------

FOLLOW THIS EXACT SOLUTION FORMAT:

Problem Understanding

Explain in 1–2 simple sentences what the question is asking.

Given Data

Write the given quantities clearly.

For example:

Force = 500 N
Angle = 30°

Required

Horizontal component
Vertical component

Concept Used

Explain briefly which Engineering Mechanics concept is being used.

Solution

Step 1: Resolve the force into horizontal and vertical components.

Horizontal component:

Fx = F cos θ

Substituting the values:

Fx = 500 cos 30°

Fx = 433 N

Therefore:

Horizontal component = 433 N

Vertical component:

Fy = F sin θ

Substituting the values:

Fy = 500 sin 30°

Fy = 250 N

Therefore:

Vertical component = 250 N

Final Answer

Horizontal component = 433 N

Vertical component = 250 N

Engineering Check

Give one short sentence explaining whether the result is reasonable.

Key Learning Point

Give one short sentence explaining what the student should remember.

--------------------------------------------------

VERY IMPORTANT:

Always follow this sequence:

FORMULA
↓
SUBSTITUTION
↓
CALCULATION
↓
ANSWER

Never jump directly to the final answer.

Use simple sentences between calculations to explain what is happening.

Do not make the answer sound like a computer program.

Do not use words such as:
"execute"
"calculate using Python"
"algorithm"
"variable"
"function"
"code"
"syntax"

The student should feel that a real Engineering Mechanics professor
has solved the problem for them.

Keep the mathematical presentation clean, simple, and suitable for
writing in an examination notebook.
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

    if uploaded_file is None:
        return "Please upload a question image."

    image_data = encode_uploaded_image(uploaded_file)

    level_instruction = {
        "Beginner": """
Explain every important step in simple beginner-friendly language.
Explain why each formula or principle is used.
""",
        "Standard": """
Give a balanced university-level Engineering Mechanics solution.
""",
        "Exam": """
Give a concise university exam-style solution while showing all essential calculations.
"""
    }

    image_prompt = f"""
You are looking at a photograph or screenshot of an Engineering Mechanics problem.

Explanation mode:
{explanation_level}

Instructions:
{level_instruction[explanation_level]}

Your tasks are:

1. Carefully read all visible text in the image.
2. Carefully inspect any engineering diagram.
3. Identify forces, loads, dimensions, angles, supports, arrows and labels.
4. Determine exactly what the question asks.
5. Solve the problem using Engineering Mechanics / Statics principles.

VERY IMPORTANT:

If an important number, dimension, force, angle, support condition or label
cannot be read clearly, DO NOT guess it.

Instead clearly tell the student what information cannot be read and ask
for a clearer image.

Your answer must look like a university Engineering Mechanics textbook solution.

Do NOT write programming code.
Do NOT use Python syntax.
Do NOT use code blocks.
Do NOT use JSON.
Do NOT use LaTeX commands such as \\frac, \\theta, \\boxed or \\sum.
Do NOT write programming-style expressions such as:
F_x
F_y
cos(theta)
500*cos(30)
sum_M

Use normal textbook symbols instead.

For example:

Fx = F cos θ

Fx = 500 cos 30°

Fx = 433 N

Use:
× instead of *
÷ instead of /
θ instead of theta
° for degrees
√ for square root
Σ for summation

Follow this structure:

Problem Understanding

Briefly explain what the problem is asking.

Given Data

List all information identified from the question and diagram.

Required

Clearly state what must be determined.

Concept Used

State the relevant Engineering Mechanics principle.

Solution

Show the solution step by step.

Always follow:

Formula
↓
Substitution
↓
Calculation
↓
Answer

Explain important steps using simple engineering language.

Final Answer

Clearly state the final numerical answer with correct units.

Engineering Check

Briefly check whether the result is reasonable.

Key Learning Point

Explain the main concept the student should remember.

The final solution should feel like it was written by an Engineering Mechanics professor,
not generated by computer code.
"""

    try:

        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
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
            temperature=0.2,
            max_completion_tokens=3000
        )

        return response.choices[0].message.content

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
        st.subheader("Solution")
        st.write(solution)


# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.caption(
    "Engineering Mechanics AI Tutor — MVP"
)
