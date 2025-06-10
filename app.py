import os
import json
import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Task definitions with dynamic instructions
TOPICS = {
    "Treatment": "Summarise first-line therapy including dose, route, frequency, and duration.",
    "Confirmatory test": "State single best confirmatory test with one-line rationale for selection.",
    "Differential & next steps": "List top 5 differential diagnoses then specify best next management step."
}

# System prompt template
SYSTEM_PROMPT = """ROLE: Clinical decision-support assistant for licensed clinicians.

OUTPUT STYLE
• ≤5 bullet points, each ≤25 words.
• Use standard medical abbreviations.
• For meds: dose / route / frequency / duration.
• Cite ≥2022 guideline source (e.g., "IDSA 2024").
• Include 1 red-flag / contraindication bullet.
• End with: "Clinical judgment required – not a substitute for professional assessment."

ACCURACY RULE
If evidence weak or guideline absent, begin with "Guideline match: NONE".

TASK: {task_instruction}"""

# Page config
st.set_page_config(
    page_title="Quick MD Helper",
    page_icon="⚡",
    layout="centered"
)

# Load templates
try:
    with open("common_cases.json") as f:
        TEMPLATES = json.load(f)
except FileNotFoundError:
    TEMPLATES = {
        "Chest Pain": "45yo M presents with acute substernal chest pain, radiating to left arm, associated with diaphoresis and nausea. BP 140/90, HR 95.",
        "UTI": "28yo F with dysuria, urinary frequency, and suprapubic pain x2 days. No fever or flank pain. Urine dipstick positive for nitrites and leukocytes.",
        "COPD Exacerbation": "68yo M with known COPD, increased dyspnea and productive cough with yellow sputum x3 days. Using rescue inhaler q2h. O2 sat 88% on RA."
    }

# Title and disclaimer
st.title("⚡ Quick MD Helper")
st.warning("⚠️ **For licensed clinicians only. Not for diagnosis. No PHI allowed. Clinical judgment required.**")

# Instructions expander
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### What This Tool Does
    This clinical decision-support tool provides evidence-based summaries for common medical scenarios. It uses OpenAI's o3 model to generate concise, guideline-aligned recommendations.
    
    ### How to Use
    1. **Select a task** - Choose between Treatment, Confirmatory Test, or Differential Diagnosis
    2. **Enter patient presentation** - Use the template buttons for common cases or type your own
    3. **Click Run** - The AI will generate ≤5 bullet points with guideline citations
    4. **Copy results** - Click the copy icon in the output box
    
    ### What You Get
    - **Concise summaries**: Maximum 5 bullet points, each ≤25 words
    - **Evidence-based**: Cites guidelines from 2022 or later when available
    - **Safety alerts**: Always includes contraindications/red flags
    - **Clear dosing**: For medications, includes dose/route/frequency/duration
    
    ### Important Notes
    - **No PHI**: Never enter patient identifiers or protected health information
    - **Clinical judgment required**: This is a support tool, not a replacement for clinical assessment
    - **Guideline transparency**: Shows "NONE" when evidence is weak or guidelines absent
    """)

# Task selection
task = st.radio("Select task", list(TOPICS.keys()), horizontal=True)

# Template buttons
st.markdown("### Quick Templates")
cols = st.columns(len(TEMPLATES))
for col, (label, text) in zip(cols, TEMPLATES.items()):
    if col.button(label, use_container_width=True):
        st.session_state.case = text

# Case input
case = st.text_area(
    "Patient presentation",
    value=st.session_state.get("case", ""),
    height=150,
    placeholder="Enter de-identified patient presentation..."
)

# Action buttons
col1, col2 = st.columns(2)
with col1:
    run_button = st.button("🚀 Run", type="primary", use_container_width=True)
with col2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.case = ""
        st.rerun()

# Process and display results
if run_button and case.strip():
    with st.spinner("Analyzing..."):
        try:
            # Build system prompt with selected task
            system_prompt = SYSTEM_PROMPT.format(task_instruction=TOPICS[task])
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="o3",  # Using o3 model for best clinical accuracy
                temperature=0.3,
                max_tokens=400,  # Sufficient for 5 bullets + disclaimer
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": case.strip()}
                ]
            )
            
            answer = response.choices[0].message.content
            
            # Display answer in code block for easy copying
            st.markdown("### Clinical Summary")
            st.code(answer, language="")
            
            # Extract guideline year (naive approach)
            guideline_tag = "NONE"
            for year in ["2025", "2024", "2023", "2022"]:
                if year in answer:
                    guideline_tag = year
                    break
            
            # Display guideline match
            st.markdown(f"**Guideline match:** {guideline_tag}")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Make sure your OpenAI API key is set in the environment variables.")

# Footer
st.markdown("---")
st.caption("Clinical judgment required – not a substitute for professional assessment.")