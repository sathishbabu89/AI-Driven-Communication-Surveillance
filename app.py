
import streamlit as st
import pandas as pd
import json
import re
from dotenv import load_dotenv
import os

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

# ---------------------------
# Environment Setup
# ---------------------------
load_dotenv()

llm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
    temperature=0
)

# ---------------------------
# Risk Matrix
# ---------------------------
RISK_WEIGHTS = {
    "Secrecy": 4,
    "Market Manipulation/Misconduct": 5,
    "Market Bribery": 5,
    "Change in Communication": 3,
    "Complaints": 2,
    "Employee Ethics": 3
}

# ---------------------------
# Helper Functions
# ---------------------------
def split_sentences(text: str):
    # Use real lookbehind (not HTML-escaped)
    sentences = re.split(r'(?<=[.!?])\s+', text or "")
    return [{"line_id": i + 1, "text": s} for i, s in enumerate(sentences) if s.strip()]

def build_prompt(subject, body, sentences):
    sentence_block = "\n".join([f"{s['line_id']}. {s['text']}" for s in sentences])

    return f"""
You are a compliance surveillance assistant for a bank.

Analyze the email below and return ONLY valid JSON.

Tasks:
1. Decide if the email is non-compliant (true/false)
2. Assign ONE category from:
   - Secrecy
   - Market Manipulation/Misconduct
   - Market Bribery
   - Change in Communication
   - Complaints
   - Employee Ethics
3. Explain the reason
4. Identify the sentence line_ids that caused concern

Email Subject:
{subject}

Email Content:
{body}

Sentences:
{sentence_block}

Return JSON in this format:
{{
  "is_non_compliant": true/false,
  "category": "...",
  "reason": "...",
  "evidence_line_ids": [1,2]
}}
""".strip()

def analyze_email(subject, body):
    sentences = split_sentences(body)
    prompt = build_prompt(subject or "", body or "", sentences)

    # You can also use llm.invoke(prompt) without HumanMessage
    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        # Remove code fences if present
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
        raw = raw.strip()
        # In case of accidental prefix before JSON
        json_start = raw.find("{")
        if json_start > 0:
            raw = raw[json_start:]
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "is_non_compliant": False,
            "category": "Unknown",
            "reason": "Model response could not be parsed",
            "evidence_line_ids": []
        }

    return result, sentences

def calculate_priority(category):
    return RISK_WEIGHTS.get(category, 1)

# ---------------------------
# Streamlit UI (Two-Column Layout)
# ---------------------------
st.set_page_config(page_title="AI Communication Surveillance", layout="wide")
st.title("📧 AI-Driven Communication Surveillance (POC)")

uploaded_file = st.file_uploader("Upload Raw Email Excel File", type=["xlsx"])

if uploaded_file:
    # Use explicit engine for xlsx
    df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.success(f"{len(df)} emails loaded")

    # Create two columns: left for guided workflow, right for outputs
    left_col, right_col = st.columns([0.95, 1.05])

    # LEFT: Guided progress & explainer
    with left_col:
        st.subheader("🧭 Guided workflow")
        status = st.status("Initializing compliance analysis...", expanded=True)
        progress_bar = st.progress(0)

    # RIGHT: Results & summary placeholders
    with right_col:
        st.subheader("📊 Results & Summary")
        table_placeholder = st.empty()
        chart_placeholder = st.empty()

    results = []
    total = len(df)

    # Main processing loop
    for idx, row in df.iterrows():
        # --- LEFT: Update status to "Preparing prompt"
        with left_col:
            status.update(
                label=f"Email {idx+1}/{total}: preparing prompt",
                state="running",
            )

        subject = row.get("Subject", "") or ""
        body = row.get("Message Body", "") or ""
        sentences = split_sentences(body)
        prompt = build_prompt(subject, body, sentences)

        # --- LEFT: Update status to "Invoking Azure OpenAI"
        with left_col:
            status.update(
                label=f"Email {idx+1}/{total}: invoking Azure OpenAI",
                state="running",
            )

        # Invoke the model (you can also use llm.invoke(prompt))
        response = llm.invoke([HumanMessage(content=prompt)])

        # Parse model response to JSON
        raw = response.content.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)  # strip code fences
        raw = raw.strip()
        json_start = raw.find("{")
        if json_start > 0:
            raw = raw[json_start:]

        try:
            analysis = json.loads(raw)
            with left_col:
                status.update(
                    label=f"Email {idx+1}/{total}: parsing JSON response",
                    state="running",
                )
        except json.JSONDecodeError:
            analysis = {
                "is_non_compliant": False,
                "category": "Unknown",
                "reason": "Model response could not be parsed",
                "evidence_line_ids": []
            }
            with left_col:
                status.update(
                    label=f"Email {idx+1}/{total}: JSON parse fallback",
                    state="running",
                )

        # Compute priority & evidence mapping
        priority = (
            calculate_priority(analysis.get("category", ""))
            if analysis.get("is_non_compliant")
            else 0
        )
        evidence_ids = set(analysis.get("evidence_line_ids", []))
        evidence_texts = [s["text"] for s in sentences if s["line_id"] in evidence_ids]

        # --- LEFT: Rich, collapsible explainers for users
        with left_col.expander(f"📜 What we did: {subject or '(no subject)'}", expanded=False):
            st.markdown("""
**Workflow (high level)**
1. Numbered the sentences in the email body
2. Queried Azure OpenAI with a JSON-only prompt
3. Parsed JSON and mapped evidence line IDs to the text
4. Computed priority using the risk matrix
""")

            # 1) Input Preprocessing: show numbered sentences as sent to the model
            with st.expander("🔢 Input preprocessing (numbered sentences)", expanded=False):
                if sentences:
                    for s in sentences:
                        st.write(f"{s['line_id']}. {s['text']}")
                else:
                    st.info("No sentences found in the email body.")

            # 2) Prompt Preview: show the prompt (trim if very long)
            with st.expander("🧾 Prompt preview (sanitized)", expanded=False):
                prompt_preview = prompt
                MAX_CHARS = 4000
                if len(prompt_preview) > MAX_CHARS:
                    st.warning(f"Prompt truncated for display (>{MAX_CHARS} chars)")
                    prompt_preview = prompt_preview[:MAX_CHARS] + "\n...\n[truncated]"
                st.code(prompt_preview, language="markdown")

            # 3) Model Response (Raw JSON) – cleaned and shown for education/debugging
            with st.expander("📦 Model response (raw JSON)", expanded=False):
                try:
                    st.code(json.dumps(analysis, indent=2), language="json")
                except Exception:
                    st.write(analysis)

            # 4) Risk Scoring Explanation – how priority was computed
            with st.expander("🧮 Risk scoring explanation", expanded=False):
                chosen_category = analysis.get("category", "Unknown")
                is_nc = analysis.get("is_non_compliant", False)
                base_weight = RISK_WEIGHTS.get(chosen_category, 1)

                st.markdown(f"""
- **Chosen category:** `{chosen_category}`
- **Non-compliant?:** `{is_nc}`
- **Base risk weight:** `{base_weight}` (from your RISK_WEIGHTS)

**Priority formula:**
- If non-compliant: **Priority = RISK_WEIGHTS[category]**
- Otherwise: **Priority = 0**

**Computed result:** `{priority}`
""")

            # 5) Outcome summary – concise human-readable recap
            with st.expander("✅ Outcome summary", expanded=True):
                st.markdown(f"""
- **Decision:** {"🚩 Non-compliant" if analysis.get("is_non_compliant", False) else "✅ Compliant"}
- **Category:** `{analysis.get("category", "Unknown")}`
- **Priority:** `{priority}`
- **Model’s rationale:**  
{analysis.get("reason", "No rationale provided")}
""")

                if evidence_texts:
                    st.markdown("**Evidence sentences:**")
                    for i, t in enumerate(evidence_texts, start=1):
                        st.write(f"- {i}. {t}")
                else:
                    st.info("No evidence line IDs were provided by the model.")

        # ✅ Append current result to list BEFORE building the DataFrame
        results.append({
            "From": row.get("Email Address From", "") or "",
            "To": row.get("Email Address To", "") or "",
            "Subject": subject,
            "Non-Compliant": analysis.get("is_non_compliant", False),
            "Category": analysis.get("category", "Unknown"),
            "Priority Score": priority,
            "Reason": analysis.get("reason", ""),
            "Evidence Lines": evidence_texts
        })

        # --- RIGHT: Live update table & chart
        result_df = pd.DataFrame(results)

        with right_col:
            # Only sort if the column exists and DataFrame not empty
            if not result_df.empty and "Priority Score" in result_df.columns:
                sorted_df = result_df.sort_values("Priority Score", ascending=False)
                table_placeholder.dataframe(sorted_df, use_container_width=True)
            else:
                table_placeholder.info("No results yet.")

            # Summary chart
            if not result_df.empty and "Category" in result_df.columns:
                chart_placeholder.bar_chart(result_df["Category"].value_counts())
            else:
                chart_placeholder.info("No results to summarize yet.")

        # Update progress bar
        with left_col:
            pct = int(((idx + 1) / total) * 100)
            progress_bar.progress(pct)

    # Finalize status
    with left_col:
        status.update(label="Analysis complete", state="complete")
