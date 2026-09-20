import html
import re


REPLACEMENTS = {
    r"\\times": "×",
    r"\\cdot": "×",
    r"\\div": "÷",
    r"\\sqrt": "√",
    r"\\Sigma": "Σ",
    r"\\theta": "θ",
    r"\\alpha": "α",
    r"\\beta": "β",
    r"\\gamma": "γ",
    r"\\sin": "sin",
    r"\\cos": "cos",
    r"\\tan": "tan",
    r"\\pm": "±",
    r"\\geq": "≥",
    r"\\leq": "≤",
    r"\\neq": "≠",
}


def clean_text(value):
    """
    Convert common LaTeX/programming-style notation into
    clean student-facing textbook notation.
    """
    if value is None:
        return ""

    text = str(value)

    # Remove hidden reasoning.
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.I | re.S,
    )

    # Remove code fences.
    text = re.sub(
        r"```(?:json|python|text|markdown)?",
        "",
        text,
        flags=re.I,
    )

    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    replacements = {
        "imes": "×",
        "cdot": "×",
        "div": "÷",
        "Sigma": "Σ",
        "theta": "θ",
        "alpha": "α",
        "beta": "β",
        "gamma": "γ",
        "sqrt": "√",
        "\\%": "%",
        "\\,": " ",
        "\\!": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("\\left", "")
    text = text.replace("\\right", "")
    text = text.replace("$", "")
    text = text.replace("`", "")

    # Common malformed LaTeX.
    text = re.sub(r"\\text\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"_\{([^{}]+)\}", r"\1", text)
    text = re.sub(r"\^\{([^{}]+)\}", r"^\1", text)

    # Common plain-text artifacts.
    text = text.replace("times", "×")
    text = text.replace("÷", "÷")
    text = text.replace(" deg", "°")

    # Remove remaining braces.
    text = text.replace("{", "")
    text = text.replace("}", "")

    # Convert simple variable subscripts.
    text = re.sub(
        r"\b([A-Za-z])_([A-Za-z0-9]+)\b",
        r"\1\2",
        text,
    )

    # Normalize whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def safe_html(value):
    return html.escape(clean_text(value))


def normalized_angle(value):
    try:
        if value is None or value == "":
            return None
        return float(value) % 360
    except (TypeError, ValueError):
        return None


def force_label(item):
    if not isinstance(item, dict):
        return clean_text(item)

    label = clean_text(item.get("label", "F")) or "F"
    magnitude = clean_text(item.get("magnitude", ""))
    unit = clean_text(item.get("unit", ""))

    if magnitude:
        return f"{label} = {magnitude} {unit}".strip()

    return label
