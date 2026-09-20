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
10. NEVER stop after finding individual force components when the problem asks for a resultant.
11. For a resultant-force problem, ALWAYS continue in this exact order:
    a) Resolve every force into Fx and Fy.
    b) Add all x-components to obtain FRx.
    c) Add all y-components to obtain FRy.
    d) Calculate resultant magnitude:
       FR = √(FRx² + FRy²)
    e) Calculate the resultant direction.
    f) Determine the correct quadrant from the signs of FRx and FRy.
    g) State the final resultant magnitude AND direction clearly.
12. The final answer must directly answer every quantity requested in the original question.
13. Never present only intermediate component values as the final answer.
14. For direction, do not use tan⁻¹(FRy/FRx) blindly. Check the signs of FRx and FRy and report the physically correct quadrant/direction.
15. For every requested resultant, show:
    Component equations → component values → FRx/FRy → magnitude → direction → final answer.
    RESULTANT-FORCE COMPLETION RULE:

If the problem asks for the resultant force, equivalent force, magnitude of resultant,
direction of resultant, or resultant magnitude and direction, the solution is incomplete
unless BOTH of these are calculated:

1. Resultant magnitude:
FR = √(FRx² + FRy²)

2. Resultant direction:
θ = tan⁻¹(FRy / FRx)

Then verify the quadrant using the signs of FRx and FRy.

The final answer must explicitly state:
"Resultant force = ___ N"
"Direction = ___° ___"

Do not end the solution at:
Fx1, Fy1, Fx2, Fy2
or
FRx, FRy.
Those are intermediate results only.
"""


SOLUTION_JSON_SCHEMA = {
    "steps": {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "title",
            "explanation",
            "equations",
            "result"
        ],
        "properties": {
            "title": {
                "type": "string"
            },
            "explanation": {
                "type": "string"
            },
            "equations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "label",
                        "expression"
                    ],
                    "properties": {
                        "label": {
                            "type": "string"
                        },
                        "expression": {
                            "type": "string"
                        }
                    }
                }
            },
            "result": {
                "type": "string"
            }
        }
    }
}
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
        "mechanics_model":{
    "relationships":["short relationship"],
    "unknowns":["FR"],
    "equations":["ΣFx = 0 or FRx = Fx1 + Fx2 + ...",
                 "ΣFy = 0 or FRy = Fy1 + Fy2 + ..."],
    "resultant_required":true
},
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
       "steps":[
    {
        "step_number":1,
        "title":"short teaching title",
        "explanation":"2-3 clear student-friendly sentences explaining why this step is needed",
        "formula":"one equation only",
        "substitution":"one equation only",
        "calculation":"one equation only",
        "result":"one clear result"
    }
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
         "completion": {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "requested_quantities",
        "solved_quantities",
        "complete"
    ],
    "properties": {
        "requested_quantities": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "solved_quantities": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "complete": {
            "type": "boolean"
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
SOLUTION COMPLETION RULE:

Before solving, identify exactly what the question asks for.

Create a mental checklist of every requested quantity.

Examples:

If the question asks:
"Determine the resultant force"

you MUST calculate:
1. x-component of resultant
2. y-component of resultant
3. magnitude of resultant
4. direction of resultant

If the question asks:
"Determine the magnitude and direction of the resultant"

you MUST provide BOTH magnitude AND direction.

If the question asks for a mass:
1. calculate the required force/weight if necessary
2. then calculate mass
3. give mass as the final requested answer

If the question asks for an unknown force:
1. determine its components if required
2. solve its magnitude
3. solve its direction if requested

NEVER stop after an intermediate calculation.

A component calculation is NOT a final answer when the problem asks for a resultant.

The final answer must directly answer the wording of the original question.
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
FORCE DESCRIPTION RULE:

Never describe a force using a compressed sentence if a beginner could misunderstand it.

Instead of:

"F1 = 500 N — 30° above +x"

write the information conceptually as:

"Force F₁ has a magnitude of 500 N."

"F₁ acts 30° above the positive x-axis."

"Therefore, F₁ lies in the first quadrant."

For each force explain:

1. magnitude
2. direction
3. reference axis
4. quadrant
5. component signs

Example:

Force F₁:
Magnitude = 500 N
Direction = 30° above +x
Quadrant = First quadrant
Fx₁ = positive
Fy₁ = positive
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
