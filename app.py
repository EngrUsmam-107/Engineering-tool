import base64
import html
import json
import math
import re
import time

import matplotlib.pyplot as plt
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Engineering Mechanics AI Tutor", page_icon="🏗️", layout="centered")

st.markdown("""
<style>
.main .block-container{max-width:1000px;padding-top:1.5rem;padding-bottom:3rem}
.hero{padding:1.35rem;border:1px solid rgba(128,128,128,.22);border-radius:20px;background:linear-gradient(135deg,rgba(127,127,127,.11),rgba(127,127,127,.035));margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{opacity:.78;margin:.3rem 0 0}
.badge{display:inline-block;padding:.25rem .55rem;border-radius:999px;border:1px solid rgba(128,128,128,.25);font-size:.78rem;margin:.55rem .25rem 0 0}
.card{border:1px solid rgba(128,128,128,.20);border-radius:14px;padding:.8rem 1rem;margin:.6rem 0;background:rgba(127,127,127,.045)}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🏗️ Engineering Mechanics AI Tutor</h1>
<p>Verify the data → model the mechanics → build the FBD → solve → check → learn.</p>
<span class="badge">V3 Engineering Intelligence</span><span class="badge">V4 Student Tools</span><span class="badge">Statics</span><span class="badge">FBD</span>
</div>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("GROQ_API_KEY is not configured. Add it in Streamlit Cloud → Settings → Secrets.")
    st.stop()

client = Groq(api_key=API_KEY)
TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"

REPL = {
    r"\\times":"×", r"\\cdot":"×", r"\\div":"÷", r"\\sqrt":"√", r"\\Sigma":"Σ",
    r"\\theta":"θ", r"\\alpha":"α", r"\\beta":"β", r"\\gamma":"γ", r"\\sin":"sin",
    r"\\cos":"cos", r"\\tan":"tan", r"\\pm":"±", r"\\geq":"≥", r"\\leq":"≤", r"\\neq":"≠",
}

def clean(value):
    if value is None: return ""
    text = str(value)
    for a,b in REPL.items(): text=text.replace(a,b)
    text=text.replace("imes","×").replace("Sigma","Σ").replace("theta","θ").replace("alpha","α").replace("beta","β")
    text=text.replace("$","").replace("`","").replace("_{","").replace("}","").replace("{","").replace("\\","")
    text=re.sub(r"\b([A-Za-z])_([A-Za-z])([A-Za-z0-9]*)\b",r"\1\2\3",text)
    text=re.sub(r"\b([A-Za-z])_([A-Za-z0-9]+)\b",r"\1\2",text)
    return " ".join(text.split())

def eq(value):
    text=html.escape(clean(value))
    if text:
        st.markdown(f'<div style="text-align:center;font-size:1.08rem;font-weight:600;padding:.68rem .8rem;margin:.4rem 0;background:rgba(127,127,127,.08);border:1px solid rgba(127,127,127,.22);border-radius:10px;overflow-x:auto">{text}</div>',unsafe_allow_html=True)

def parse_json(raw):
    if not raw: raise ValueError("Empty AI response")
    raw=raw.strip()
    if raw.startswith("```"):
        raw=re.sub(r"^```(?:json)?\s*","",raw,flags=re.I); raw=re.sub(r"\s*```$","",raw)
    return json.loads(raw)

def encode_image(f):
    return f"data:{f.type or 'image/jpeg'};base64,{base64.b64encode(f.getvalue()).decode()}"

TEXT_SYSTEM = """
You are an Engineering Mechanics professor teaching beginner Civil Engineering students.
Return a complete, correct, student-facing answer. Do NOT reveal hidden reasoning.
Before calculating, verify the given data and identify whether anything is missing or inconsistent.
Never invent a value, direction, angle, support, or relationship. If information is insufficient, say exactly what is missing.
Always finish every requested quantity. If an intermediate quantity is found (for example weight), continue to the requested quantity (for example mass).
Use textbook notation: ΣFx, ΣFy, ΣMO, FA, FB, θ, ×, ÷, √, °. No LaTeX, code, or programming notation.
Show equations one line at a time. Prefer Formula → Substitution → Calculation → Result.
Check units, signs, force directions, trigonometry, equilibrium and arithmetic.
"""

VISION_SYSTEM = """
You are an Engineering Mechanics professor AND a careful engineering-diagram analyst.
Analyze the uploaded image first. Do not solve until the diagram's data, labels, geometry, arrowheads, angles and cable/support relationships have been checked.
CRITICAL: read arrowheads for actual force direction; do not infer direction only from a member's visual orientation. Copy the isolated point/body label exactly when readable. Never invent unclear information.
For each force use angle_deg measured counterclockwise from +x: right 0, up 90, left 180, down 270; 60° above +x is 60; 45° below +x is 315.
Cable tension acts along the cable toward the connection. Weight acts downward. Include external forces only.
If the diagram is unclear, mark the relevant angle/direction/value null or uncertain and explain it in data_check.
Most important: finish the requested quantity. Never stop at an intermediate result such as weight when mass is requested.
Return ONLY valid JSON, compact enough for a strict 1000 output-token/minute limit. No markdown, code fences, <think>, or LaTeX.
"""

SCHEMA = """
{
"topic":"short topic",
"difficulty":"Beginner|Intermediate|Advanced",
"problem_understanding":"1-2 short sentences",
"data_check":{"status":"verified|uncertain|insufficient","notes":["short verification note"],"assumptions":["only if needed"]},
"given_data":["short item"],
"required":["short item"],
"fbd":{"applicable":true,"isolated_body":"Knot E","isolated_label":"E","axes_note":"+x right, +y up","forces":[{"label":"TBE","magnitude":"392.4","unit":"N","angle_deg":30,"direction_text":"30° above +x","known":true}],"support_reactions":[],"confidence":"high|medium|low","fbd_note":"short note"},
"mechanics_model":{"relationships":["short relationship"],"unknowns":["mA"],"equations":["ΣFy = 0"]},
"concept":"short concept",
"steps":[{"title":"short title","explanation":"short teaching sentence","formula":"one equation","substitution":"one equation","calculation":"one equation","result":"final step result"}],
"final_answers":["complete requested answer"],
"engineering_check":["short check"],
"key_learning_point":"one useful sentence"
}
"""

VISION_PROMPT = VISION_SYSTEM + "\nReturn this exact JSON structure:\n" + SCHEMA

def solve_typed(problem, level):
    prompt=f"""Explanation level: {level}
Problem:
{problem.strip()}

Return a complete solution. If it is a calculation, do not stop at intermediate values; answer every item under Required."""
    try:
        r=client.chat.completions.create(model=TEXT_MODEL,messages=[{"role":"system","content":TEXT_SYSTEM},{"role":"user","content":prompt}],temperature=.15,max_completion_tokens=1600)
        return r.choices[0].message.content
    except Exception as e:
        return f"Unable to solve right now. Error: {e}"

def solve_image(f, level):
    image_url=encode_image(f)
    prompt=VISION_PROMPT+f"\nExplanation level: {level}\nKeep every field short but complete."
    for budget in (800,700):
        try:
            r=client.chat.completions.create(model=VISION_MODEL,reasoning_effort="none",messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":image_url}}]}],response_format={"type":"json_object"},temperature=.12,max_completion_tokens=budget)
            return parse_json(r.choices[0].message.content)
        except Exception as e:
            msg=str(e).lower()
            if any(x in msg for x in ("429","rate_limit","output tokens","tokens per minute")):
                time.sleep(1); continue
            return {"error":str(e)}
    return {"error":"The image solver is temporarily limited by the AI service output-token quota. Please try again shortly."}

def angle(v):
    try:
        if v is None or v=="": return None
        return float(v)%360
    except: return None

def force_label(x):
    if not isinstance(x,dict): return clean(x)
    a=clean(x.get("label","F")); m=clean(x.get("magnitude","")); u=clean(x.get("unit",""))
    return f"{a} = {m} {u}".strip() if m else a

def vectors(fbd):
    out=[]
    if not isinstance(fbd,dict): return out
    for group in ("forces","support_reactions"):
        for x in fbd.get(group,[]) if isinstance(fbd.get(group,[]),list) else []:
            if isinstance(x,dict) and angle(x.get("angle_deg")) is not None:
                out.append((force_label(x),angle(x.get("angle_deg"))))
    return out

def render_fbd(fbd):
    vs=vectors(fbd)
    if not vs: return None
    fig,ax=plt.subplots(figsize=(8.4,6.1)); ax.set_aspect("equal"); ax.set_xlim(-1.6,1.6); ax.set_ylim(-1.4,1.4); ax.axis("off")
    label=clean(fbd.get("isolated_label","O")) or "O"
    ax.scatter([0],[0],s=240,zorder=5); ax.text(0,-.16,label,ha="center",va="top",fontweight="bold")
    ax.annotate("",xy=(1.25,-1.0),xytext=(.65,-1.0),arrowprops=dict(arrowstyle="->",linewidth=1.4)); ax.text(1.31,-1.0,"+x",va="center")
    ax.annotate("",xy=(.65,-.38),xytext=(.65,-1.0),arrowprops=dict(arrowstyle="->",linewidth=1.4)); ax.text(.65,-.30,"+y",ha="center")
    for lab,a in vs[:8]:
        r=math.radians(a); dx,dy=math.cos(r),math.sin(r); L=.95
        ax.annotate("",xy=(L*dx,L*dy),xytext=(.10*dx,.10*dy),arrowprops=dict(arrowstyle="->",linewidth=2.2))
        lx,ly=1.12*dx,1.12*dy; ha="left" if lx>.15 else "right" if lx<-.15 else "center"; va="bottom" if ly>.15 else "top" if ly<-.15 else "center"
        ax.text(lx,ly,lab,ha=ha,va=va,fontweight="bold",fontsize=9)
    ax.set_title(f"Free-Body Diagram — {label}",fontweight="bold",pad=10); fig.tight_layout(); return fig

def display_fbd(fbd):
    if not isinstance(fbd,dict): return
    st.markdown("### 📐 Free-Body Diagram")
    vs=vectors(fbd); conf=clean(fbd.get("confidence",""))
    if vs and conf.lower()!="low":
        fig=render_fbd(fbd); st.pyplot(fig,use_container_width=True); plt.close(fig)
        st.caption("FBD arrows are drawn from the directions extracted from the uploaded diagram.")
    else: st.info("Automatic FBD drawing was withheld because reliable direction data was not available.")
    if fbd.get("isolated_body"): st.markdown("**Isolate:** "+clean(fbd["isolated_body"]))
    if fbd.get("axes_note"): st.markdown("**Axes:** "+clean(fbd["axes_note"]))
    for group,title in (("forces","External Forces"),("support_reactions","Support Reactions")):
        items=fbd.get(group,[])
        if isinstance(items,list) and items:
            st.markdown("**"+title+"**")
            for x in items:
                if not isinstance(x,dict): continue
                s=force_label(x); d=clean(x.get("direction_text","")); a=angle(x.get("angle_deg"))
                if d: s += " — "+d
                if a is not None: s += f" ({a:.0f}° from +x)"
                st.write("• "+s)
    if fbd.get("fbd_note"): st.caption("✏️ "+clean(fbd["fbd_note"]))

def display_structured(d):
    if not isinstance(d,dict): st.error("No usable solution returned."); return
    if d.get("error"): st.error(d["error"]); return
    if d.get("problem_understanding"): st.markdown("### 📘 Problem Understanding"); st.write(clean(d["problem_understanding"]))
    dc=d.get("data_check",{})
    if isinstance(dc,dict):
        st.markdown("### 🔍 Data Check")
        status = clean(dc.get("status", "")).lower()
        if status == "verified":
            st.success("Data status: Verified")
        elif status == "uncertain":
            st.warning("Data status: Uncertain")
        elif status == "insufficient":
            st.error("Data status: Insufficient information")
        else:
            st.info("Data status: " + (status.title() if status else "Not specified"))
        for x in dc.get("notes",[]): st.write("• "+clean(x))
        for x in dc.get("assumptions",[]): st.write("• Assumption: "+clean(x))
    if d.get("given_data"):
        st.markdown("### 📌 Given Data")
        for x in d["given_data"]: st.write("• "+clean(x))
    if d.get("required"):
        st.markdown("### 🎯 Required")
        for x in (d["required"] if isinstance(d["required"],list) else [d["required"]]): st.write("• "+clean(x))
    display_fbd(d.get("fbd"))
    mm=d.get("mechanics_model",{})
    if isinstance(mm,dict) and (mm.get("relationships") or mm.get("unknowns") or mm.get("equations")):
        st.markdown("### 🧩 Mechanics Model")
        for x in mm.get("relationships",[]): st.write("• "+clean(x))
        if mm.get("unknowns"): st.write("Unknowns: "+", ".join(clean(x) for x in mm["unknowns"]))
        for x in mm.get("equations",[]): eq(x)
    if d.get("concept"): st.markdown("### 🧠 Concept Used"); st.write(clean(d["concept"]))
    steps=d.get("steps",[])
    if steps:
        st.markdown("### ✏️ Solution")
        for i,s in enumerate(steps,1):
            if not isinstance(s,dict): continue
            st.markdown(f"#### {i}. {clean(s.get('title','Step'))}")
            if s.get("explanation"): st.write(clean(s["explanation"]))
            for key,title in (("formula","Formula"),("substitution","Substitution"),("calculation","Calculation"),("result","Result")):
                if s.get(key):
                    if key=="result": st.success("✅ "+clean(s[key]))
                    else: st.caption(title); eq(s[key])
    if d.get("engineering_check"):
        st.markdown("### 🔎 Engineering Check")
        for x in d["engineering_check"]: st.write("✅ "+clean(x))
    if d.get("final_answers"):
        st.markdown("### 🏁 Final Answer")
        for x in (d["final_answers"] if isinstance(d["final_answers"],list) else [d["final_answers"]]): st.success(clean(x))
    if d.get("key_learning_point"): st.markdown("### 💡 Key Learning Point"); st.info(clean(d["key_learning_point"]))

def v4_call(instruction, level="Beginner"):
    prompt=f"Explanation level: {level}\n{instruction}\nUse beginner-friendly textbook language. No hidden reasoning."
    try:
        r=client.chat.completions.create(model=TEXT_MODEL,messages=[{"role":"system","content":TEXT_SYSTEM},{"role":"user","content":prompt}],temperature=.2,max_completion_tokens=1200)
        return r.choices[0].message.content
    except Exception as e: return f"Unable to complete this tool right now. Error: {e}"

with st.sidebar:
    st.markdown("## 🎓 Student Settings")
    level=st.selectbox("Explanation level",["Beginner","Standard","Exam"],index=0)
    st.markdown("### V3 checks")
    st.write("• Verifies extracted data first")
    st.write("• Models forces and relationships")
    st.write("• Uses actual diagram directions for FBD")
    st.write("• Finishes requested quantities")
    st.markdown("### V4 tools")
    st.write("• Check My Answer")
    st.write("• Teach Me This")
    st.write("• Practice Problem")
    st.caption("AI output is a learning aid. Verify important engineering work against your textbook/instructor.")

mode=st.radio("Choose a tool",["🚀 Solve Problem","✅ Check My Answer","🧠 Teach Me This","🎯 Practice Problem"],horizontal=True)

if mode=="🚀 Solve Problem":
    input_mode=st.radio("Input",["Type a question","Upload a question photo"],horizontal=True)
    if input_mode=="Type a question":
        problem=st.text_area("Engineering Mechanics problem",height=190,placeholder="Example: A particle is in equilibrium under three concurrent forces. Find the unknown force.")
        if st.button("🚀 Solve + Check",type="primary",use_container_width=True):
            if not problem.strip(): st.warning("Please enter a problem.")
            else:
                with st.spinner("Checking data, modeling the mechanics, solving and verifying..."):
                    raw=solve_typed(problem,level)
                st.divider(); st.markdown("## 📘 Solution"); st.markdown(raw)
    else:
        f=st.file_uploader("Upload a clear mechanics question",type=["jpg","jpeg","png"],help="Include the complete diagram, labels, angles and values.")
        if f: st.image(f,caption="Question image",use_container_width=True)
        if st.button("🚀 Analyze + Solve",type="primary",use_container_width=True):
            if not f: st.warning("Please upload a question image.")
            else:
                with st.spinner("Reading the diagram → verifying data → building FBD → solving..."):
                    data=solve_image(f,level)
                st.divider(); display_structured(data)

elif mode=="✅ Check My Answer":
    st.markdown("### Check your own solution")
    q=st.text_area("Question",height=140,placeholder="Paste the original mechanics question here.")
    a=st.text_area("Your answer / working",height=180,placeholder="Paste your calculation, equations and final answer here.")
    if st.button("✅ Check My Answer",type="primary",use_container_width=True):
        if not q.strip() or not a.strip(): st.warning("Enter both the question and your solution.")
        else:
            with st.spinner("Checking your setup, equations, arithmetic and final answer..."):
                out=v4_call(f"Question:\n{q}\n\nStudent solution:\n{a}\n\nReview it. Start with Verdict: Correct / Partly Correct / Incorrect. Then identify the first error if any, explain why, show the corrected step, and give the correct final answer. Do not unnecessarily rewrite correct work.",level)
            st.divider(); st.markdown("### 🔎 Feedback"); st.markdown(out)

elif mode=="🧠 Teach Me This":
    st.markdown("### Learn a concept before solving")
    topic=st.text_input("What do you want to learn?",placeholder="e.g., equilibrium of a particle, free-body diagrams, moments")
    if st.button("🧠 Teach Me",type="primary",use_container_width=True):
        if not topic.strip(): st.warning("Enter a topic.")
        else:
            with st.spinner("Preparing a student-friendly lesson..."):
                out=v4_call(f"Teach this Engineering Mechanics topic: {topic}. Structure it as: What it means; Why it matters; Key rule/equations; one very simple example; common mistake; one quick self-test question. Keep equations on separate lines.",level)
            st.divider(); st.markdown("### 📚 Mini Lesson"); st.markdown(out)

else:
    st.markdown("### Practice without seeing the answer first")
    topic=st.text_input("Practice topic",placeholder="e.g., concurrent force equilibrium, moments, truss basics")
    difficulty=st.selectbox("Difficulty",["Beginner","Standard","Challenge"],index=0)
    if st.button("🎯 Generate Practice Problem",type="primary",use_container_width=True):
        if not topic.strip(): st.warning("Enter a topic.")
        else:
            with st.spinner("Creating a practice problem..."):
                out=v4_call(f"Create one original Engineering Mechanics practice problem on {topic} at {difficulty} level. Give only: Problem, Given, Required, and a Hint. Do not give the solution yet.",level)
            st.session_state.practice_problem=out
    if st.session_state.get("practice_problem"):
        st.divider(); st.markdown("### 📝 Your Practice Problem"); st.markdown(st.session_state.practice_problem)
        student=st.text_area("Your solution",height=170,key="practice_answer")
        if st.button("Check Practice Solution",use_container_width=True):
            with st.spinner("Checking your practice work..."):
                out=v4_call(f"Here is the generated practice problem:\n{st.session_state.practice_problem}\n\nStudent solution:\n{student}\n\nCheck the solution carefully. State what is correct, identify the first error if any, correct it, and give the final answer. Do not expose hidden reasoning.",level)
            st.markdown("### 🔎 Practice Feedback"); st.markdown(out)

st.divider(); st.caption("Engineering Mechanics AI Tutor • V3 Engineering Intelligence + V4 Student Tools")
