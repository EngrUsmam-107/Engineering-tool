import json
import re
import time

from groq import Groq
import streamlit as st

from .utils import clean, encode_image, parse_json


TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"


def get_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception as exc:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it in Streamlit Cloud → Settings → Secrets."
        ) from exc

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is empty.")

    return Groq(api_key=api_key)


TEXT_SYSTEM = """
You are a careful Engineering Mechanics professor teaching beginner Civil Engineering students.
Your output is for students, not programmers.

RULES:
1. Solve the actual requested quantity completely. Never stop at an intermediate value.
   If the question asks for mass and you calculate weight first, continue to mass.
2. Verify the given data, units, directions, angles, signs, and relationships before calculating.
3. Never invent missing numerical data. If something essential is missing, state it clearly.
4. Use beginner-friendly textbook language. Explain WHY a formula is used.
5. Present each equation on its own line.
6. Use plain textbook notation such as ΣFx, ΣFy, ΣM, FA, FB, θ, ×, ÷, √, °.
7. Do not use LaTeX, Markdown math, Python, JSON, code, or programming syntax in student-facing fields.
8. Each numerical step should follow Formula → Substitution → Calculation → Result.
9. Check units, signs, quadrant/direction, trigonometry, equilibrium, and arithmetic.
10. Do not expose hidden reasoning or <think> content.
"""


SCHEMA = """
{
  "topic":"short topic",
  "difficulty":"Beginner|Intermediate|Advanced",
  "problem_understanding":"2-3 short student-friendly sentences",
  "data_check":{
    "status":"verified|uncertain|insufficient",
    "notes":["short notes"],
    "assumptions":["only necessary assumptions"]
  },
  "given_data":["short item"],
  "required":["short item"],
  "fbd":{
    "applicable":true,
    "isolated_body":"Knot E",
    "isolated_label":"E",
    "axes_note":"+x right, +y up",
    "forces":[
      {
        "label":"TBE",
        "magnitude":"392.4",
        "unit":"N",
        "angle_deg":30,
        "direction_text":"30° above +x",
        "known":true
      }
    ],
    "support_reactions":[],
    "confidence":"high|medium|low",
    "fbd_note":"short note"
  },
  "mechanics_model":{
    "relationships":["short relationship"],
    "unknowns":["mA"],
    "equations":["ΣFy = 0"]
  },
  "concept":"name the concept and briefly explain why it applies",
  "steps":[
    {
      "title":"short teaching title",
      "explanation":"2 short teaching sentences",
      "formula":"one equation",
      "substitution":"one equation",
      "calculation":"one equation",
      "result":"one clear result"
    }
  ],
  "final_answers":["complete answer to every requested quantity"],
  "engineering_check":["short verification"],
  "key_learning_point":"one useful takeaway"
}
"""


VISION_SYSTEM = """
You are an Engineering Mechanics professor and a careful engineering-diagram analyst.

First inspect the uploaded image. Identify the actual problem, labels, values,
angles, arrowheads, cables, pulleys, supports, and the body/point that should be isolated.

CRITICAL ENGINEERING RULES:
- Read arrowheads for force direction; do not infer direction merely from member orientation.
- Measure force angle counterclockwise from +x:
  right=0°, up=90°, left=180°, down=270°.
- Cable tension acts along the cable toward its connection.
- Weight acts downward.
- For a frictionless pulley with a single continuous cable, tension is uniform unless
  the diagram explicitly indicates otherwise.
- Do not invent unclear values or directions. Mark uncertainty in data_check.
- Use only forces external to the isolated body in the FBD.
- If a requested quantity is mass, continue from weight to mass.
- Return compact but complete JSON.
- No Markdown, no code fences, no <think>, no LaTeX.
"""


VISION_PROMPT = VISION_SYSTEM + "\nReturn exactly this structure:\n" + SCHEMA


def call_text(prompt, level="Beginner", max_tokens=1400):
    client = get_client()

    full = (
        f"Explanation level: {level}\n\n"
        f"{prompt}\n\n"
        "Return ONLY the requested student-facing content."
    )

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": TEXT_SYSTEM},
                {"role": "user", "content": full},
            ],
            temperature=0.15,
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return (
            "Unable to complete this request right now. "
            f"Please try again. ({clean(exc)})"
        )


def solve_typed(problem, level):
    client = get_client()

    prompt = f"""
Convert and solve this Engineering Mechanics problem as a structured textbook solution.

Problem:
{problem.strip()}

Return JSON using this exact structure:
{SCHEMA}
"""

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": TEXT_SYSTEM},
                {
                    "role": "user",
                    "content": f"Explanation level: {level}\n{prompt}",
                },
            ],
            temperature=0.12,
            response_format={"type": "json_object"},
            max_completion_tokens=1800,
        )

        return parse_json(response.choices[0].message.content)

    except Exception as exc:
        text = call_text(problem, level, max_tokens=1600)
        return {
            "fallback_text": text,
            "error_note": clean(exc),
        }


def solve_image(uploaded_file, level):
    client = get_client()
    image_url = encode_image(uploaded_file)

    prompt = (
        VISION_PROMPT
        + f"\nExplanation level: {level}"
        + "\nKeep fields concise enough for the model output limit, "
          "but include every requested result."
    )

    # Keep below the previously observed 1000-output-token Groq limit.
    for budget in (900, 780):
        try:
            response = client.chat.completions.create(
                model=VISION_MODEL,
                reasoning_effort="none",
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
                temperature=0.10,
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

            return {"error": clean(exc)}

    return {
        "error": (
            "The diagram-reading model is temporarily limited by its "
            "output-token quota. Please try the image again shortly."
        )
    }


def call_student_tool(instruction, level="Beginner", max_tokens=1400):
    return call_text(instruction, level, max_tokens=max_tokens)
