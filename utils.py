import base64
import html
import json
import re
import streamlit as st


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


def clean(value):
    """Convert model notation into readable textbook notation."""
    if value is None:
        return ""

    text = str(value)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S)
    text = text.replace("```json", "").replace("```", "")

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

    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("$", "").replace("`", "")
    text = re.sub(r"_\{([^{}]+)\}", r"\1", text)
    text = re.sub(r"\^\{([^{}]+)\}", r"^\1", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\b([A-Za-z])_([A-Za-z0-9]+)\b", r"\1\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def display_equation(value):
    text = clean(value)
    if not text:
        return

    safe = html.escape(text)
    st.markdown(
        f'<div class="equation">{safe}</div>',
        unsafe_allow_html=True,
    )


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


def show_list(items, prefix="•"):
    if not isinstance(items, list):
        items = [items]

    for item in items:
        if clean(item):
            st.write(f"{prefix} {clean(item)}")


def normalized_angle(value):
    try:
        if value is None or value == "":
            return None
        return float(value) % 360
    except (TypeError, ValueError):
        return None


def force_label(item):
    if not isinstance(item, dict):
        return clean(item)

    label = clean(item.get("label", "F")) or "F"
    magnitude = clean(item.get("magnitude", ""))
    unit = clean(item.get("unit", ""))

    if magnitude:
        return f"{label} = {magnitude} {unit}".strip()

    return label
