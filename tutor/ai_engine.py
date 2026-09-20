import json
import re
import time

from groq import Groq
import streamlit as st

from .utils import clean, encode_image, parse_json


TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.8-27b"


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


SOLUTION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "topic",
        "difficulty",
        "problem_understanding",
        "data_check",
        "given_data",
        "required",
        "fbd",
        "mechanics_model",
        "concept",
        "steps",
        "final_answers",
        "engineering_check",
        "key_learning_point"
    ],
    "properties": {
        "topic": {
            "type": "string"
        },
        "difficulty": {
            "type": "string"
        },
        "problem_understanding": {
            "type": "string"
        },
        "data_check": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "status",
                "notes",
                "assumptions"
            ],
            "properties": {
                "status": {
                    "type": "string"
                },
                "notes": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "assumptions": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },
        "given_data": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "required": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "fbd": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "applicable",
                "isolated_body",
                "isolated_label",
                "axes_note",
                "forces",
                "support_reactions",
                "confidence",
                "fbd_note"
            ],
            "properties": {
                "applicable": {
                    "type": "boolean"
                },
                "isolated_body": {
                    "type": "string"
                },
                "isolated_label": {
                    "type": "string"
                },
                "axes_note": {
                    "type": "string"
                },
                "forces": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "label",
                            "magnitude",
                            "unit",
                            "angle_deg",
                            "direction_text",
                            "known"
                        ],
                        "properties": {
                            "label": {
                                "type": "string"
                            },
                            "magnitude": {
                                "type": "string"
                            },
                            "unit": {
                                "type": "string"
                            },
                            "angle_deg": {
                                "type": "number"
                            },
                            "direction_text": {
                                "type": "string"
                            },
                            "known": {
                                "type": "boolean"
                            }
                        }
                    }
                },
                "support_reactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "label",
                            "magnitude",
                            "unit",
                            "angle_deg",
                            "direction_text",
                            "known"
                        ],
                        "properties": {
                            "label": {
                                "type": "string"
                            },
                            "magnitude": {
                                "type": "string"
                            },
                            "unit": {
                                "type": "string"
                            },
                            "angle_deg": {
                                "type": "number"
                            },
                            "direction_text": {
                                "type": "string"
                            },
                            "known": {
                                "type": "boolean"
                            }
                        }
                    }
                },
                "confidence": {
                    "type": "string"
                },
                "fbd_note": {
                    "type": "string"
                }
            }
        },
        "mechanics_model": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "relationships",
                "unknowns",
                "equations"
            ],
            "properties": {
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "unknowns": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "equations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },
        "concept": {
            "type": "string"
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title",
                    "explanation",
                    "formula",
                    "substitution",
                    "calculation",
                    "result"
                ],
                "properties": {
                    "title": {
                        "type": "string"
                    },
                    "explanation": {
                        "type": "string"
                    },
                    "formula": {
                        "type": "string"
                    },
                    "substitution": {
                        "type": "string"
                    },
                    "calculation": {
                        "type": "string"
                    },
                    "result": {
                        "type": "string"
                    }
                }
            }
        },
        "final_answers": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "engineering_check": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "key_learning_point": {
            "type": "string"
        }
    }
}


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


VISION_PROMPT = """
You are an expert Engineering Mechanics professor teaching civil engineering students.

Analyze the uploaded engineering problem carefully and solve it completely.

IMPORTANT ENGINEERING CHECKS:

1. Read every numerical value directly from the image.
2. Read every force arrowhead carefully.
3. Do NOT assume that a member direction is automatically the force direction.
4. Determine the actual direction of every force from the arrowhead.
5. Interpret angles exactly as drawn.
6. Convert all angles to standard mathematical direction angles measured counterclockwise from +x.
7. Check the quadrant of every force.
8. Check whether an angle is measured from the x-axis or y-axis.
9. For a 3-4-5 triangle, use the correct component signs according to its quadrant.
10. Weight acts downward.
11. Cable tension acts along the cable away from the isolated point.
12. A frictionless pulley with one continuous cable has equal tension on both sides.
13. Isolate the correct particle, ring, knot, body, or member.
14. Include only external forces acting on the isolated body.
15. Do not invent values that cannot be read from the image.
16. If something is genuinely unclear, mark the data as uncertain.
17. Before solving, mentally verify the extracted data and force directions.
18. After solving, check equilibrium, signs, units, and arithmetic.
19. If the question asks for mass, do not stop at weight. Continue:
    mass = weight / g
20. If the question asks for resultant force, calculate BOTH magnitude and direction.
21. If the question asks for a reaction, calculate the actual requested reaction completely.

TEACHING REQUIREMENTS:

- Explain the problem clearly.
- Do not give an unnecessarily short answer.
- Explain why each equation is being used.
- Use Formula → Substitution → Calculation → Result.
- Give enough explanation for a beginner civil engineering student to understand the solution.
- Do not expose hidden reasoning.
- Do not use Markdown math.
- Do not use LaTeX.
- Do not use programming syntax.
- Equations must be plain textbook notation such as:
  ΣFx = 0
  ΣFy = 0
  FRx = F1x + F2x
  FR = √(FRx² + FRy²)
- Return ONLY the structured solution requested by the JSON schema.
"""


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

    prompt = f"""
You are solving an Engineering Mechanics problem for a civil engineering student.

Problem:

{problem}

Explanation level:
{level}

Solve the problem completely.

IMPORTANT:

- Verify the given information first.
- Identify the correct mechanics principle.
- Define unknowns.
- Show equations clearly.
- Explain why each equation is used.
- Show Formula → Substitution → Calculation → Result.
- Never stop at an intermediate quantity.
- If mass is requested, continue from weight to mass.
- If resultant is requested, provide magnitude AND direction.
- Check units.
- Check signs.
- Check arithmetic.
- Perform an engineering verification at the end.
- Use plain textbook notation.
- Do not use LaTeX.
- Do not use programming language.
- Do not expose hidden reasoning.

Return ONLY the JSON object matching the supplied schema.
"""

    try:

        response = client.chat.completions.create(

            model=TEXT_MODEL,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.08,

            reasoning_effort="none",

            max_completion_tokens=2200,

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "engineering_mechanics_solution",
                    "strict": True,
                    "schema": SOLUTION_JSON_SCHEMA
                }
            }
        )

        content = response.choices[0].message.content

        if not content:
            return {
                "error": "The AI returned an empty solution."
            }

        return json.loads(content)

    except Exception as exc:

        error_text = str(exc)

        if "429" in error_text or "rate_limit" in error_text.lower():
            return {
                "error":
                "The AI service is temporarily rate-limited. "
                "Please wait a few seconds and try again."
            }

        return {
            "error":
            "The solution could not be generated correctly. "
            "Please try the problem again."
        }


def solve_image(uploaded_file, level):
    image_url = encode_image(uploaded_file)

    prompt = f"""
{VISION_PROMPT}

Explanation level:
{level}

Produce a complete student-facing Engineering Mechanics solution.

The uploaded image is the primary source of truth.

Before producing the answer, carefully verify:

- numerical values
- force labels
- arrow directions
- angles
- quadrants
- x/y components
- requested quantity
- units
- final arithmetic

Do not stop at an intermediate quantity.

For example:
If the problem asks for mass and you calculate weight,
continue to calculate mass.

If the problem asks for a resultant,
calculate both magnitude and direction.

Return only the JSON object matching the supplied schema.
"""

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",

            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],

            temperature=0.05,

            reasoning_effort="none",

            max_completion_tokens=2200,

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "engineering_mechanics_solution",
                    "strict": True,
                    "schema": SOLUTION_JSON_SCHEMA
                }
            }
        )

        content = response.choices[0].message.content

        if not content:
            return {
                "error": "The AI returned an empty solution."
            }

        return json.loads(content)

    except Exception as exc:

        error_text = str(exc)

        # Friendly handling for Groq quota/rate errors
        if "429" in error_text or "rate_limit" in error_text.lower():
            return {
                "error":
                "The AI service is temporarily rate-limited. "
                "Please wait a few seconds and try the image again."
            }

        # Structured-output failure
        if "json_validate_failed" in error_text.lower():
            return {
                "error":
                "The diagram was understood, but the structured solution "
                "could not be formatted correctly. Please try the image again."
            }

        # Model/API problem
        if "model_not_found" in error_text.lower():
            return {
                "error":
                "The selected Groq model is unavailable. "
                "Check the model name in the app configuration."
            }

        return {
            "error":
            "Unable to analyze this question right now. "
            "Please check that the uploaded image is clear and contains "
            "the complete problem diagram."
        }
