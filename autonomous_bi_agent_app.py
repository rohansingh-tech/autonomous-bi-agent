
# Autonomous BI Agent — Minimal Prototype (Streamlit)
# Author: Rohan Kumar Singh
# Run: streamlit run autonomous_bi_agent_app.py

import streamlit as st
import pandas as pd
import yaml
from io import StringIO
from datetime import datetime

# Optional ML tools; if missing, degrade gracefully
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import KMeans
    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False

st.set_page_config(page_title="Autonomous BI Agent (v1)", layout="wide")
st.title("Autonomous Business Intelligence Agent (v1)")
st.caption("Self-directed pattern discovery and decision drafting — policy-driven via vibe.yaml")

with st.sidebar:
    st.header("1) Policy — vibe.yaml")
    default_policy = """
objectives:
  primary_metric: conversion_rate
  direction: increase  # increase|decrease
constraints:
  disallow:
    - delete_records
    - send_external_email
  approvals_required: true
thresholds:
  anomaly_confidence:
    high: 0.8
    medium: 0.6
  impact_minimum: 0.02  # 2% relative change
actions:
  - draft_alert
  - draft_task
ranking:
  weight_impact: 0.7
  weight_confidence: 0.3
"""
    policy_text = st.text_area("Edit policy (vibe.yaml)", value=default_policy, height=300)
    try:
        policy = yaml.safe_load(policy_text) or {}
        st.success("Policy parsed successfully.")
    except Exception as e:
        st.error(f"Policy error: {e}")
        policy = {}

st.header("2) Data Upload")
upload = st.file_uploader("Upload CSV (include metric columns, optional segment/date columns)", type=["csv"]) 

if upload is not None:
    df = pd.read_csv(upload)
    st.write("Preview:")
    st.dataframe(df.head(20), use_container_width=True)

    numeric_cols = df.select_dtypes(include=['int64','float64']).columns.tolist()
    if not numeric_cols:
        st.warning("No numeric columns found; please upload a dataset with metrics.")
    else:
        metric = st.selectbox("Primary metric", numeric_cols, index=min(0, len(numeric_cols)-1))
        seg_cols = st.multiselect("Segment columns (optional)", [c for c in df.columns if c not in numeric_cols])

        st.header("3) Pattern Discovery")
        results = []
        if SKLEARN_OK and len(df) >= 20:
            # Isolation Forest anomaly score
            iso = IsolationForest(random_state=42, contamination='auto')
            try:
                X = df[numeric_cols].fillna(df[numeric_cols].median())
                iso.fit(X)
                scores = -iso.decision_function(X)  # higher => more anomalous
                df['anomaly_score'] = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
                st.line_chart(df[['anomaly_score']])
                st.caption("Anomaly score (normalized): higher indicates unusual points across numeric features.")
            except Exception as e:
                st.warning(f"Anomaly detection skipped: {e}")
        else:
            st.info("sklearn not available or too few rows — skipping advanced anomaly detection.")
            df['anomaly_score'] = 0.0

        # Simple impact proxy: relative change vs median for the chosen metric
        if metric in df.columns:
            try:
                base = df[metric].median() if df[metric].median() != 0 else (df[metric].abs().median() + 1e-9)
                df['impact_proxy'] = (df[metric] - base) / (abs(base) + 1e-9)
            except Exception:
                df['impact_proxy'] = 0.0
        else:
            df['impact_proxy'] = 0.0

        # Rank insights (row-level as a proxy). In practice, aggregate by segment/time windows.
        w_impact = policy.get('ranking', {}).get('weight_impact', 0.7)
        w_conf = policy.get('ranking', {}).get('weight_confidence', 0.3)
        df['score'] = w_impact * df['impact_proxy'].abs() + w_conf * df['anomaly_score']

        # Decision drafting based on thresholds
        thr = policy.get('thresholds', {})
        ac = thr.get('anomaly_confidence', {})
        high, med = ac.get('high', 0.8), ac.get('medium', 0.6)
        impact_min = thr.get('impact_minimum', 0.02)

        def band(x):
            if x >= high: return 'High'
            if x >= med: return 'Medium'
            return 'Low'
        df['confidence_band'] = df['anomaly_score'].apply(band)

        # Build insight cards
        st.header("4) Insight Cards")
        top_n = st.slider("How many insights?", 1, 10, 5)
        top = df.sort_values('score', ascending=False).head(top_n)

        for idx, row in top.iterrows():
            with st.container(border=True):
                st.subheader(f"Insight #{idx}")
                st.write({
                    'metric': metric,
                    'value': float(row.get(metric, 0.0)) if metric in df.columns else None,
                    'impact_proxy': float(row['impact_proxy']),
                    'anomaly_score': float(row['anomaly_score']),
                    'confidence': row['confidence_band']
                })
                # Proposed actions
                actions = policy.get('actions', ['draft_alert', 'draft_task'])
                proposals = []
                if abs(row['impact_proxy']) >= impact_min:
                    if 'draft_alert' in actions:
                        proposals.append("Alert: Potential shift detected in {metric}. Please review attached rows and confidence band.")
                    if 'draft_task' in actions:
                        proposals.append("Task: Investigate drivers for the shift; segment analysis and validate data quality.")
                else:
                    proposals.append("Observation only: below impact threshold; monitoring continues.")

                st.markdown("**Proposed actions (drafts):**")
                for p in proposals:
                    st.write("- " + p.format(metric=metric))

        st.header("5) Audit & Export")
        ts = datetime.utcnow().isoformat()
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download annotated data (CSV)", csv, file_name=f"annotated_{ts}.csv", mime="text/csv")

else:
    st.info("Upload a CSV to begin. Include at least one numeric metric column.")

st.divider()
st.caption("Note: This prototype runs locally and does not transmit data. For production, add connectors, RBAC, and audit logging.")
