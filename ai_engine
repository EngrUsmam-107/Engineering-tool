import base64
import json
import re
import time

import streamlit as st
from groq import Groq

from utils import clean_text

TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"

SYSTEM_PROMPT = """
You are a careful Engineering Mechanics professor teaching beginner
Civil Engineering students.

Your output is for students, not programmers.

CORE RULES:
1. Solve the actual requested quantity completely. Never stop at an
   intermediate quantity. If the question asks for mass and you first
   calculate weight, continue until mass is calculated.
2. Recheck the problem statement, diagram, values, units, angles,
   directions, signs and relationships before calculating.
3. Never invent missing numerical data.
4. Use beginner-friendly textbook language.
5. Explain why a formula is being used.
6. Use one short equation per line.
7. NEVER use LaTeX in student-facing content.
8. NEVER use Python/programming syntax in student-facing content.
9. Use plain notation such as:
   ΣFx, ΣFy, ΣM, FA, FB, θ, ×, ÷, √, °.
10. For numerical work use:
    Formula → Substitution → Calculation → Result.
11. Check units, signs, trigonometry, equilibrium and arithmetic.
12. Never expose hidden reasoning or <think> content.
13. Keep paragraphs short. Prefer bullets, numbered steps and compact
    equation lines.
14. The final answer must directly answer every requested quantity.
"""

SCHEMA = """
{
  "topic": "short topic",
  "difficulty": "Beginner|Intermediate|Advanced",

  "problem_understanding":
    "2-3 short student-friendly sentences",

  "data_check": {
    "status": "verified|uncertain|insufficient",
    "notes": ["short notes"],
    "assumptions": ["only necessary assumptions"]
  },

  "given_data": ["short item"],
  "required": ["short item"],

  "fbd": {
    "applicable": true,
    "isolated_body": "Knot E",
    "isolated_label": "E",
    "axes_note": "+x right, +y up",
    "forces": [
      {
        "label": "TBE",
        "magnitude": "392.4",
        "unit": "N",
        "angle_deg": 30,
        "direction_text": "30° above +x",
        "known": true
      }
    ],
    "support_reactions": [],
    "confidence": "high|medium|low",
    "fbd_note": "short note"
  },

  "mechanics_model": {
    "relationships": ["short relationship"],
    "unknowns": ["mA"],
    "equations": ["ΣFy = 0"]
  },

  "concept":
    "name the concept and briefly explain why it applies",

  "steps": [
    {
      "title": "short teaching title",
      "explanation": "2 short teaching sentences",
      "formula": "one equation",
      "substitution": "one equation",
      "calculation": "one equation",
      "result": "one clear result"
    }
  ],

  "final_answers": ["complete answer to every requested quantity"],
  "engineering_check": ["short verification"],
  "key_learning_point": "one useful takeaway"
}
"""

VISION_PROMPT = """
You are an Engineering Mechanics professor and a careful
engineering-diagram analyst.

Inspect the uploaded image carefully before solving.

Identify:
- the actual question
- every numerical value
- labels
- arrowheads
- force directions
- cable directions
- pulley relationships
- angles
- supports
- the body or point that should be isolated

CRITICAL ENGINEERING RULES:
- Read arrowheads for force direction.
- Do not infer force direction only from member orientation.
- Measure angles counterclockwise from +x.
- Cable tension acts along the cable toward its connection.
- Weight acts downward.
- For a frictionless pulley with a single continuous cable,
  tension is uniform unless the diagram clearly says otherwise.
- Use only external forces acting on the isolated body in the FBD.
- If the question asks for mass, continue from weight to mass.
- Do not invent unclear values or directions.
- If a value or direction is uncertain, mark it uncertain.
- Verify the final result against the diagram.

Return compact but complete JSON only.
No Markdown.
No code fences.
No LaTeX.
No <think>.
"""

def get_client():
    try:
        key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return None
    return Groq(api_key=key)


def parse_json(raw):
    if not raw:
        raise ValueError("The AI returned an empty response.")

    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def encode_image(uploaded_file):
    mime = uploaded_file.type or "image/jpeg"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode()
    return f"data:{mime};base64,{encoded}"


def call_student_tool(instruction, level="Beginner", max_tokens=1400):
    client = get_client()

    if client is None:
        return (
            "GROQ_API_KEY is not configured. Add GROQ_API_KEY in "
            "Streamlit Cloud → Settings → Secrets."
        )

    prompt = f"""
Explanation level: {level}

{instruction}

STUDENT PRESENTATION RULES:
- Short paragraphs.
- Clear headings.
- Numbered steps.
- One equation per line.
- No LaTeX.
- No programming syntax.
- No JSON.
- No hidden reasoning.
"""

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.12,
            max_completion_tokens=max_tokens,
        )
        return clean_text(response.choices[0].message.content or "")
    except Exception as exc:
        return (
            "The tutor could not complete the request right now.\n\n"
            f"Reason: {clean_text(str(exc))}"
        )


def solve_typed(problem, level):
    client = get_client()

    if client is None:
        return {
            "error": (
                "GROQ_API_KEY is not configured. Add it in "
                "Streamlit Cloud → Settings → Secrets."
            )
        }

    prompt = f"""
Solve this Engineering Mechanics problem as a complete textbook
solution.

Problem:
{problem.strip()}

Return JSON using exactly this structure:
{SCHEMA}

Important:
- Check the given information first.
- Do not stop after an intermediate quantity.
- Calculate every requested unknown.
- Keep the solution complete but visually compact.
"""

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Explanation level: {level}\n{prompt}",
                },
            ],
            temperature=0.10,
            response_format={"type": "json_object"},
            max_completion_tokens=1800,
        )

        return parse_json(response.choices[0].message.content)

    except Exception as exc:
        # Safe fallback instead of crashing the app.
        fallback = call_student_tool(
            f"""
Solve this Engineering Mechanics problem completely:

{problem}

Give:
1. Problem Understanding
2. Given Data
3. Required
4. Concept Used
5. Step-by-Step Solution
6. Final Answer
7. Engineering Check
8. Key Learning Point

Make sure every requested quantity is calculated.
""",
            level,
            1500,
        )

        return {
            "fallback_text": fallback,
            "error_note": clean_text(str(exc)),
        }


def solve_image(uploaded_file, level):
    client = get_client()

    if client is None:
        return {
            "error": (
                "GROQ_API_KEY is not configured. Add it in "
                "Streamlit Cloud → Settings → Secrets."
            )
        }

    image_url = encode_image(uploaded_file)

    prompt = f"""
{VISION_PROMPT}

Explanation level: {level}

Return exactly this JSON structure:
{SCHEMA}

OUTPUT LIMIT:
Keep explanations compact enough to fit the model output limit,
but DO NOT omit the final answer or requested quantities.
"""

    # Keep the image response deliberately compact because vision-model
    # output-token limits can be much lower than text-model limits.
    for budget in (850, 700):
        try:
            response = client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.05,
                max_completion_tokens=budget,
            )

            return parse_json(response.choices[0].message.content)

        except Exception as exc:
            msg = str(exc).lower()

            if any(
                token in msg
                for token in (
                    "429",
                    "rate_limit",
                    "output tokens",
                    "tokens per minute",
                )
            ):
                time.sleep(1)
                continue

            return {"error": clean_text(str(exc))}

    return {
        "error": (
            "The diagram-reading model is temporarily limited by its "
            "output-token quota. Please try the image again shortly."
        )
    }
