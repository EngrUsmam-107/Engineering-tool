import base64
import html
import json
import math
import re
import time
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st
from groq import Groq

# ============================================================
# ENGINEERING MECHANICS AI TUTOR — FINAL STUDENT RELEASE
# ============================================================
# Product goal:
# A student-facing Engineering Mechanics tutor that converts a typed
# or photographed question into a clear, exam-ready engineering solution,
# with structured data, equations, checks, and a deterministic FBD graphic.
# ============================================================

st.set_page_config(
    page_title="Engineering Mechanics AI Tutor",
    page_icon="🏗️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# THEME / BRANDING
# -----------------------------

st.markdown(
    """
    <style>
    .main .block-container {max-width: 980px; padding-top: 1.6rem; padding-bottom: 3rem;}
    .hero {
        padding: 1.2rem 1.3rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(127,127,127,.10), rgba(127,127,127,.03));
        margin-bottom: 1rem;
    }
    .hero h1 {margin: 0 0 .25rem 0; font-size: 2rem;}
    .hero p {margin: .25rem 0 0 0; opacity: .82;}
    .badge {
        display:inline-block; padding:.25rem .55rem; border-radius:999px;
        border:1px solid rgba(128,128,128,.25); font-size:.78rem; margin-right:.35rem;
    }
    .section-card {
        border: 1px solid rgba(128,128,128,.20);
        border-radius: 14px;
        padding: .8rem 1rem;
        margin: .65rem 0;
        background: rgba(127,127,127,.045);
    }
    .small-muted {opacity:.72; font-size:.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🏗️ Engineering Mechanics AI Tutor</h1>
      <p>Understand the problem → identify the forces → build the FBD → solve → check.</p>
      <div style="margin-top:.65rem">
        <span class="badge">Statics</span>
        <span class="badge">Step-by-step</span>
        <span class="badge">FBD</span>
        <span class="badge">Exam-ready</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# API CLIENT
# -----------------------------

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("GROQ_API_KEY is not configured. Add it to Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"

# -----------------------------
# TEXT CLEANING / FORMATTING
# -----------------------------

_LATEX_REPLACEMENTS = {
    r"\times": "×",
    r"\cdot": "×",
    r"\div": "÷",
    r"\sqrt": "√",
    r"\Sigma": "Σ",
    r"\theta": "θ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\sin": "sin",
    r"\cos": "cos",
    r"\tan": "tan",
    r"\pm": "±",
    r"\geq": "≥",
    r"\leq": "≤",
    r"\neq": "≠",
}


def clean_equation(value):
    if value is None:
        return ""
    text = str(value)
    for old, new in _LATEX_REPLACEMENTS.items():
        text = text.replace(old, new)

    # Common malformed / programming-style output.
    text = text.replace("imes", "×")
    text = re.sub(r"\bdiv\b", "÷", text)
    text = text.replace("Sigma", "Σ")
    text = text.replace("theta", "θ")
    text = text.replace("alpha", "α")
    text = text.replace("beta", "β")

    # Remove math wrappers and simple LaTeX grouping/subscripts.
    text = text.replace("$", "").replace("`", "")
    text = text.replace("_{", "").replace("^ {", "")
    text = text.replace("{", "").replace("}", "")
    text = text.replace("\\", "")

    # Engineering notation: F_Ay -> FAy, M_O -> MO, etc.
    text = re.sub(r"\b([A-Za-z])_([A-Za-z])([A-Za-z0-9]*)\b", r"\1\2\3", text)
    text = re.sub(r"\b([A-Za-z])_([A-Za-z0-9]+)\b", r"\1\2", text)

    return " ".join(text.split())


def display_equation(equation):
    eq = html.escape(clean_equation(equation))
    if not eq:
        return
    st.markdown(
        f"""
        <div style="text-align:center;font-size:1.08rem;font-weight:600;
                    padding:.7rem .8rem;margin:.45rem 0;
                    background:rgba(127,127,127,.08);
                    border:1px solid rgba(127,127,127,.22);
                    border-radius:10px;overflow-x:auto;">
            {eq}
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_json_loads(raw):
    if not raw:
        raise ValueError("The model returned an empty response.")
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)

# -----------------------------
# TEXT SOLVER
# -----------------------------

TEXT_SYSTEM_PROMPT = """
You are a university Engineering Mechanics professor for Civil Engineering students.
Solve only the student's mechanics problem.

Student-facing rules:
- Never show hidden reasoning, chain-of-thought, code, JSON, <think>, or markdown code fences.
- Be accurate, concise, beginner-friendly, and exam-ready.
- Use these headings when relevant: Problem Understanding, Given Data, Required,
  Concept Used, Solution, Engineering Check, Final Answer, Key Learning Point.
- One equation/calculation step per line.
- Use textbook notation: ΣFx, ΣFy, ΣMO, FA, FB, θ, ×, ÷, √, °.
- Do not use LaTeX commands or programming notation.
- State assumptions clearly; never invent missing data.
- Check signs, units, direction, trigonometry, equilibrium, and arithmetic.
"""


def solve_typed_problem(problem, level):
    level_text = {
        "Beginner": "Explain the main idea simply and show all essential calculation steps.",
        "Standard": "Use a balanced university-level explanation with essential steps.",
        "Exam": "Use concise exam-style working while keeping every essential equation and result.",
    }[level]

    prompt = f"""
Explanation level: {level}
Style instruction: {level_text}

Problem:
{problem.strip()}
"""

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": TEXT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_completion_tokens=1400,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"Unable to solve this problem right now.\n\nError: {exc}"

# -----------------------------
# VISION / STRUCTURED SOLVER
# -----------------------------

VISION_PROMPT = """
You are a university Engineering Mechanics professor and engineering-diagram analyst.
Analyze the uploaded mechanics question and produce a compact, accurate student solution.

CRITICAL DIAGRAM RULES:
1. Identify the actual isolated body/point from the original image. Copy its label exactly when readable.
2. Read arrowheads, not just member/cable orientation, to determine force direction.
3. Do not invent unclear values, labels, angles, supports, or forces.
4. For each force, give angle_deg measured counterclockwise from +x:
   right=0, up=90, left=180, down=270.
5. Example: 60° above +x = 60; 45° below +x = 315.
6. Cable tension acts along its cable toward the cable connection.
7. Weight acts downward when a weight is present.
8. Include only external forces on the isolated body.
9. For a particle/knot FBD, all force arrows start at the isolated point.
10. If a direction cannot be determined confidently from the image, set angle_deg to null and explain it briefly.
11. Do not claim an automatic FBD is reliable when required direction data is missing.

OUTPUT:
Return ONLY valid JSON. No markdown. No code fences. No <think>.
Keep the JSON compact enough to stay below a strict 1000 output-token/minute limit.
Use at most 4 solution steps and short strings.

Exact schema:
{
  "topic":"short topic",
  "difficulty":"Beginner|Intermediate|Advanced",
  "problem_understanding":"max 2 short sentences",
  "given_data":["item"],
  "required":["item"],
  "fbd":{
    "applicable":true,
    "isolated_body":"short description",
    "isolated_label":"O",
    "axes_note":"+x right, +y up",
    "forces":[
      {"label":"FA","magnitude":"4","unit":"kN","angle_deg":60,"direction_text":"60° above +x","known":true}
    ],
    "support_reactions":[],
    "confidence":"high|medium|low",
    "fbd_note":"short note"
  },
  "concept":"short concept",
  "concept_equations":["ΣFx = 0","ΣFy = 0"],
  "steps":[
    {"title":"short title","explanation":"max 1 short sentence","equations":["one equation"],"result":"short result"}
  ],
  "final_answers":["short answer"],
  "engineering_check":["short check"],
  "key_learning_point":"one short sentence"
}

FORMAT RULES:
- One equation per equations-list item.
- Use ×, ÷, Σ, √, θ, °.
- Never output LaTeX.
- Never output F_x, F_{Ay}, cos(theta), 500*cos(30), or similar programming notation.
- If a force is unknown, leave magnitude empty and known=false.
"""


def encode_image(uploaded_file):
    data = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    mime = uploaded_file.type or "image/jpeg"
    return f"data:{mime};base64,{data}"


def solve_image_problem(uploaded_file, level):
    image_url = encode_image(uploaded_file)
    prompt = VISION_PROMPT + f"\nExplanation level: {level}"

    # The account currently reports a 1000-token output/minute limit.
    # Two safe ceilings are used; retry only on likely token/rate errors.
    for budget in (800, 700):
        try:
            response = client.chat.completions.create(
                model=VISION_MODEL,
                reasoning_effort="none",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.15,
                max_completion_tokens=budget,
            )
            return safe_json_loads(response.choices[0].message.content)
        except Exception as exc:
            message = str(exc).lower()
            if any(token in message for token in ("429", "rate_limit", "output tokens", "tokens per minute")):
                time.sleep(1)
                continue
            return {"error": f"Image analysis failed: {exc}"}

    return {
        "error": (
            "The image solver is temporarily limited by the AI service's output-token quota. "
            "Please try again shortly."
        )
    }

# -----------------------------
# FBD GRAPHICS
# -----------------------------

def angle_number(value):
    try:
        if value is None or value == "":
            return None
        return float(value) % 360
    except (TypeError, ValueError):
        return None


def compact_force_label(force):
    label = clean_equation(force.get("label", "F"))
    magnitude = clean_equation(force.get("magnitude", ""))
    unit = clean_equation(force.get("unit", ""))
    if magnitude:
        return f"{label} = {magnitude} {unit}".strip()
    return label


def fbd_vectors(fbd):
    vectors = []
    if not isinstance(fbd, dict):
        return vectors

    for group in ("forces", "support_reactions"):
        items = fbd.get(group, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            angle = angle_number(item.get("angle_deg"))
            if angle is None:
                continue
            vectors.append(
                {
                    "label": compact_force_label(item),
                    "angle": angle,
                    "direction": clean_equation(item.get("direction_text", "")),
                }
            )
    return vectors


def render_fbd(fbd):
    if not isinstance(fbd, dict) or not fbd.get("applicable", True):
        return None

    vectors = fbd_vectors(fbd)
    if not vectors:
        return None

    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    ax.set_aspect("equal")
    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.45, 1.45)
    ax.axis("off")

    isolated = clean_equation(fbd.get("isolated_label", "")) or "O"
    body = clean_equation(fbd.get("isolated_body", ""))

    # Particle / joint.
    ax.scatter([0], [0], s=240, zorder=5)
    ax.text(0, -0.16, isolated, ha="center", va="top", fontsize=12, fontweight="bold")

    # +x / +y reference axes.
    ox, oy = 0.72, -1.02
    ax.annotate("", xy=(1.32, oy), xytext=(ox, oy), arrowprops=dict(arrowstyle="->", linewidth=1.4))
    ax.text(1.38, oy, "+x", va="center", fontsize=10)
    ax.annotate("", xy=(ox, -0.40), xytext=(ox, oy), arrowprops=dict(arrowstyle="->", linewidth=1.4))
    ax.text(ox, -0.32, "+y", ha="center", fontsize=10)

    # Draw up to 8 forces using their actual extracted angles.
    for force in vectors[:8]:
        angle = math.radians(force["angle"])
        dx, dy = math.cos(angle), math.sin(angle)
        length = 0.94
        sx, sy = 0.10 * dx, 0.10 * dy
        ex, ey = length * dx, length * dy

        ax.annotate(
            "",
            xy=(ex, ey),
            xytext=(sx, sy),
            arrowprops=dict(arrowstyle="->", linewidth=2.2),
        )

        radius = 1.13
        lx, ly = radius * dx, radius * dy
        ha = "left" if lx > 0.15 else "right" if lx < -0.15 else "center"
        va = "bottom" if ly > 0.15 else "top" if ly < -0.15 else "center"
        ax.text(lx, ly, force["label"], ha=ha, va=va, fontsize=9.5, fontweight="bold")

    ax.set_title(
        f"Free-Body Diagram — {isolated}",
        fontsize=14,
        fontweight="bold",
        pad=10,
    )
    if body and body.lower() != isolated.lower():
        ax.text(0, 1.27, body, ha="center", va="center", fontsize=9)

    fig.tight_layout()
    return fig


def display_fbd(fbd):
    if not isinstance(fbd, dict):
        return

    st.markdown("### 📐 Free-Body Diagram")

    confidence = clean_equation(fbd.get("confidence", ""))
    vectors = fbd_vectors(fbd)

    # Only show a graphical FBD when the required direction data exists.
    if vectors and confidence.lower() != "low":
        fig = render_fbd(fbd)
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.caption("The diagram is generated from the force directions extracted from the uploaded figure.")
    else:
        st.info("A reliable automatic FBD could not be drawn from the detected geometry, so the force analysis is shown below instead.")

    isolated_body = clean_equation(fbd.get("isolated_body", ""))
    if isolated_body:
        st.markdown(f"**Isolate:** {isolated_body}")

    axes = clean_equation(fbd.get("axes_note", ""))
    if axes:
        st.markdown(f"**Axes:** {axes}")

    forces = fbd.get("forces", [])
    if isinstance(forces, list) and forces:
        st.markdown("**External Forces**")
        for force in forces:
            if not isinstance(force, dict):
                continue
            line = compact_force_label(force)
            direction = clean_equation(force.get("direction_text", ""))
            angle = angle_number(force.get("angle_deg"))
            if direction:
                line += f" — {direction}"
            if angle is not None:
                line += f" ({angle:.0f}° from +x)"
            st.write("• " + line)

    reactions = fbd.get("support_reactions", [])
    if isinstance(reactions, list) and reactions:
        st.markdown("**Support Reactions**")
        for reaction in reactions:
            if not isinstance(reaction, dict):
                continue
            line = compact_force_label(reaction)
            direction = clean_equation(reaction.get("direction_text", ""))
            angle = angle_number(reaction.get("angle_deg"))
            if direction:
                line += f" — {direction}"
            if angle is not None:
                line += f" ({angle:.0f}° from +x)"
            st.write("• " + line)

    note = clean_equation(fbd.get("fbd_note", ""))
    if note:
        st.caption("✏️ " + note)

# -----------------------------
# STRUCTURED SOLUTION DISPLAY
# -----------------------------

def display_solution(data):
    if not isinstance(data, dict):
        st.error("No usable solution was returned.")
        return
    if data.get("error"):
        st.error(data["error"])
        return

    topic = clean_equation(data.get("topic", "Engineering Mechanics"))
    difficulty = clean_equation(data.get("difficulty", ""))
    st.caption(" • ".join(x for x in (topic, difficulty) if x))

    if data.get("problem_understanding"):
        st.markdown("### 📘 Problem Understanding")
        st.write(clean_equation(data["problem_understanding"]))

    if data.get("given_data"):
        st.markdown("### 📌 Given Data")
        for item in data["given_data"]:
            st.write("• " + clean_equation(item))

    if data.get("required"):
        st.markdown("### 🎯 Required")
        required = data["required"] if isinstance(data["required"], list) else [data["required"]]
        for item in required:
            st.write("• " + clean_equation(item))

    display_fbd(data.get("fbd"))

    if data.get("concept"):
        st.markdown("### 🧠 Concept Used")
        st.write(clean_equation(data["concept"]))

    equations = data.get("concept_equations", [])
    if isinstance(equations, list):
        for equation in equations:
            display_equation(equation)

    steps = data.get("steps", [])
    if isinstance(steps, list) and steps:
        st.markdown("### ✏️ Solution")
        for number, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            title = clean_equation(step.get("title", "")) or f"Step {number}"
            st.markdown(f"#### {number}. {title}")
            explanation = clean_equation(step.get("explanation", ""))
            if explanation:
                st.write(explanation)
            eqs = step.get("equations", [])
            if isinstance(eqs, list):
                for equation in eqs:
                    display_equation(equation)
            result = clean_equation(step.get("result", ""))
            if result:
                st.success("✅ " + result)

    checks = data.get("engineering_check", [])
    if checks:
        st.markdown("### 🔍 Engineering Check")
        checks = checks if isinstance(checks, list) else [checks]
        for check in checks:
            st.write("✅ " + clean_equation(check))

    answers = data.get("final_answers", [])
    if answers:
        st.markdown("### 🏁 Final Answer")
        answers = answers if isinstance(answers, list) else [answers]
        for answer in answers:
            st.success(clean_equation(answer))

    learning = clean_equation(data.get("key_learning_point", ""))
    if learning:
        st.markdown("### 💡 Key Learning Point")
        st.info(learning)

# -----------------------------
# UI
# -----------------------------

with st.sidebar:
    st.markdown("## 🎓 Student Settings")
    level = st.radio("Explanation level", ["Beginner", "Standard", "Exam"], index=0)
    st.markdown("### What this tutor does")
    st.write("• Understands statics problems")
    st.write("• Extracts force directions from photos")
    st.write("• Builds a deterministic FBD graphic when reliable")
    st.write("• Solves step-by-step")
    st.write("• Checks units and equilibrium")
    st.caption("Always verify engineering results against your textbook, instructor, or original diagram.")

level = st.radio(
    "How should the solution be explained?",
    ["Beginner", "Standard", "Exam"],
    horizontal=True,
    index=0,
)

input_mode = st.radio(
    "Choose input",
    ["Type a question", "Upload a question photo"],
    horizontal=True,
)

problem = ""
uploaded_image = None

if input_mode == "Type a question":
    problem = st.text_area(
        "Engineering Mechanics problem",
        height=190,
        placeholder=(
            "Example: A particle is acted on by three concurrent forces. "
            "Find the unknown force required for equilibrium."
        ),
    )
else:
    uploaded_image = st.file_uploader(
        "Upload a clear Engineering Mechanics question",
        type=["jpg", "jpeg", "png"],
        help="Crop the question so the diagram, labels, angles, and values are easy to read.",
    )
    if uploaded_image is not None:
        st.image(uploaded_image, caption="Question image", use_container_width=True)

st.markdown("<div class='small-muted'>Tip: For diagram questions, include the full figure and all labels in the photo.</div>", unsafe_allow_html=True)

solve_clicked = st.button("🚀 Solve Problem", type="primary", use_container_width=True)

if solve_clicked:
    if input_mode == "Type a question":
        if not problem.strip():
            st.warning("Please enter an Engineering Mechanics problem.")
        else:
            with st.spinner("Solving and checking the mechanics..."):
                answer = solve_typed_problem(problem, level)
            st.divider()
            st.markdown("## ✏️ Solution")
            st.markdown(answer)
    else:
        if uploaded_image is None:
            st.warning("Please upload a question image.")
        else:
            with st.spinner("Reading the diagram, identifying forces, and solving..."):
                answer = solve_image_problem(uploaded_image, level)
            st.divider()
            display_solution(answer)

st.divider()
st.markdown(
    "<div style='text-align:center;opacity:.65;font-size:.82rem'>Engineering Mechanics AI Tutor • Student Edition</div>",
    unsafe_allow_html=True,
)
