# Engineering Mechanics AI Tutor

## Repository structure

    app.py
    requirements.txt
    tutor/
        __init__.py
        ai_engine.py
        ui.py
        utils.py

The Streamlit entry point is `app.py`.

The tutor package contains:
- `ai_engine.py`: Groq models, prompts, solving and image analysis
- `ui.py`: Streamlit presentation and FBD visualization
- `utils.py`: text/equation cleaning and helper functions

Add `GROQ_API_KEY` in Streamlit Cloud Secrets.
