# Autonomous BI Agent — Prototype

This is a minimal, local-first prototype that demonstrates **self-directed pattern discovery** and **policy-driven decision drafting**. It avoids dashboard reporting by ranking what matters and preparing actions for human approval.

## What’s included
- **Streamlit app**: `autonomous_bi_agent_app.py`
- **Policy file (inline)**: edit in the left sidebar as YAML ("vibe.yaml" semantics)
- **Architecture diagram**: `autonomous_bi_agent_architecture.png`
- **PRD**: `Autonomous_BI_Agent_PRD_Rohan_Kumar_Singh.docx`

## Run locally
```bash
pip install -r requirements.txt
streamlit run autonomous_bi_agent_app.py
```
Open http://localhost:8501, upload a CSV, select a metric, and review insight cards & drafted actions.

## Deploy (get a clickable link)
- **Streamlit Community Cloud**: Push these files to a public GitHub repo, then import in Streamlit Cloud and set entrypoint to `autonomous_bi_agent_app.py`.
- **Azure App Service**: Containerize or use Gunicorn with `streamlit` (behind reverse proxy). Ensure `requirements.txt` is present.

## Notes
- No data leaves your machine in local mode.
- The prototype uses a **vibe-style YAML policy** to steer the agent (objectives, thresholds, allowed actions). In production, keep this file signed & versioned and enforce RBAC + audit.
