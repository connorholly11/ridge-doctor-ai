import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key - try st.secrets first (for Streamlit Cloud), then environment variable
try:
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    logger.info("Loaded API key from st.secrets")
except:
    api_key = os.getenv("OPENAI_API_KEY")
    logger.info("Loaded API key from environment")

logger.info(f"API Key loaded: {'Yes' if api_key else 'No'}")
logger.info(f"API Key length: {len(api_key) if api_key else 0}")

# Check if API key is available
if not api_key:
    st.error("⚠️ OpenAI API key not found!")
    st.info("""
    **To fix this:**
    
    **For Streamlit Cloud:**
    1. Go to your app settings (⋮ menu → Settings)
    2. Navigate to "Secrets" section
    3. Add: `OPENAI_API_KEY = "your-api-key-here"`
    4. Click Save
    
    **For local development:**
    1. Create a `.env` file in the project root
    2. Add: `OPENAI_API_KEY=your-api-key-here`
    3. Restart the app
    """)
    st.stop()

# Initialize client with error handling
try:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    st.error(f"Failed to initialize OpenAI client: {str(e)}")
    st.stop()

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

# Custom CSS for better formatting
st.markdown("""
<style>
    /* Improve text wrapping in code blocks */
    .stCode {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-x: auto !important;
    }
    
    /* Better formatting for info boxes */
    .stAlert {
        padding: 1rem !important;
        border-radius: 0.5rem !important;
    }
    
    /* Ensure bullets are properly spaced */
    .stAlert p {
        margin-bottom: 0.5rem !important;
        line-height: 1.6 !important;
    }
    
    /* Make the main container more readable */
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

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
    This clinical decision-support tool provides evidence-based summaries for common medical scenarios. It uses OpenAI's o3 model to generate concise, guideline-aligned recommendations for:
    - **Treatment**: First-line therapy with dosing details
    - **Confirmatory Test**: Best diagnostic test with rationale
    - **Differential & Next Steps**: Top 5 differentials + management
    
    ### How to Use
    
    #### Option 1: Single Task Analysis
    1. **Select a task** using the radio buttons (Treatment, Confirmatory Test, or Differential)
    2. **Enter patient presentation** - Use template buttons for common cases or type your own
    3. **Click "Run Selected"** - Analyzes only the selected task
    4. **Review results** - Formatted bullets with guideline citations
    
    #### Option 2: Complete Analysis (All Tasks)
    1. **Enter patient presentation** - Use templates or custom text
    2. **Click "Run All Tasks"** - Analyzes all 3 tasks simultaneously
    3. **Navigate tabs** - Each task's results appear in its own tab
    4. **Copy all results** - Use the expander at bottom for combined output
    
    ### What You Get
    - **Concise summaries**: Maximum 5 bullet points, each ≤25 words
    - **Evidence-based**: Cites guidelines from 2022 or later when available
    - **Safety alerts**: Always includes contraindications/red flags
    - **Clear dosing**: For medications, includes dose/route/frequency/duration
    - **Guideline badges**: ✅ = guideline found, ⚠️ = no specific guideline
    
    ### Template Library
    Click any template button to auto-fill common presentations:
    - Chest Pain, UTI, COPD Exacerbation
    - Pneumonia, Cellulitis, Asthma
    
    ### Important Notes
    - **No PHI**: Never enter patient identifiers or protected health information
    - **Clinical judgment required**: This is a support tool, not a replacement for clinical assessment
    - **Guideline transparency**: Shows "NONE" when evidence is weak or guidelines absent
    - **Token budget**: Each query uses up to 3,500 tokens (with 5,000 retry if needed)
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
col1, col2, col3 = st.columns(3)
with col1:
    run_button = st.button("🚀 Run Selected", type="primary", use_container_width=True)
with col2:
    run_all_button = st.button("🎯 Run All Tasks", type="secondary", use_container_width=True)
with col3:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.case = ""
        st.rerun()

# Token budget constants
MAX_TOKENS = 3500          # conservative first try
MAX_TOKENS_RETRY = 5000    # ultra-conservative fallback

def call_o3(messages, max_tok):
    """Call o3 with specified token limit"""
    return client.chat.completions.create(
        model="o3",
        max_completion_tokens=max_tok,
        reasoning_effort="medium",  # medium effort for balanced accuracy/cost
        messages=messages
    )

def display_result(task_name, answer, col=None):
    """Display formatted result for a task"""
    # Use the column if provided, otherwise use main streamlit container
    container = col if col else st
    
    # Task header
    container.markdown(f"#### {task_name}")
    
    # Extract guideline year
    guideline_tag = "NONE"
    if answer and answer != "[Still empty after retry]":
        for year in ["2025", "2024", "2023", "2022"]:
            if year in answer:
                guideline_tag = year
                break
    
    # Guideline status badge
    if guideline_tag != "NONE":
        container.success(f"✅ **Guideline:** {guideline_tag}")
    else:
        container.warning("⚠️ **Guideline:** NONE")
    
    # Format and display answer
    if answer and answer != "[Still empty after retry]":
        lines = answer.strip().split('\n')
        formatted_answer = ""
        
        for line in lines:
            line = line.strip()
            if line:
                if not line.startswith('•'):
                    line = f"• {line}"
                formatted_answer += f"{line}\n\n"
        
        container.info(formatted_answer.strip())
    else:
        container.error("❌ No response received")

def process_task(task_name, task_instruction, case_text):
    """Process a single task and return the answer"""
    logger.info(f"Processing task: {task_name}")
    
    # Build system prompt
    system_prompt = SYSTEM_PROMPT.format(task_instruction=task_instruction)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": case_text}
    ]
    
    # Call API with retry logic
    start_time = datetime.now()
    response = call_o3(messages, MAX_TOKENS)
    answer = response.choices[0].message.content or ""
    
    # Retry if empty
    if answer.strip() == "":
        logger.warning(f"Empty response for {task_name} → retrying")
        response = call_o3(messages, MAX_TOKENS_RETRY)
        answer = response.choices[0].message.content or "[Still empty after retry]"
    
    end_time = datetime.now()
    logger.info(f"{task_name} completed in {(end_time - start_time).total_seconds():.2f}s")
    
    return answer

# Process single task
if run_button and case.strip():
    logger.info("=" * 50)
    logger.info(f"SINGLE TASK REQUEST - Task: {task}")
    logger.info(f"Case input: {case[:100]}...")
    
    with st.spinner(f"Analyzing {task}..."):
        try:
            answer = process_task(task, TOPICS[task], case.strip())
            
            # Save to history
            history_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': f'Single Task: {task}',
                'case': case.strip(),
                'results': {task: answer}
            }
            st.session_state.history.append(history_entry)
            
            # Display results
            st.markdown("### 📋 Clinical Summary")
            display_result(task, answer)
            
            # Copy button
            with st.expander("📄 Copy Full Response"):
                st.code(answer, language="")
            
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {str(e)}")
            logger.error(f"Full error details:", exc_info=True)
            st.error(f"Error: {str(e)}")
            st.info("Make sure your OpenAI API key is set in the environment variables.")

# Process all tasks
if run_all_button and case.strip():
    logger.info("=" * 50)
    logger.info(f"ALL TASKS REQUEST")
    logger.info(f"Case input: {case[:100]}...")
    
    st.markdown("### 🏥 Complete Clinical Analysis")
    
    # Store all responses
    all_responses = {}
    
    # Create tabs instead of columns for better mobile responsiveness
    tabs = st.tabs(list(TOPICS.keys()))
    
    # Process each task
    for idx, (task_name, task_instruction) in enumerate(TOPICS.items()):
        with st.spinner(f"Analyzing {task_name}..."):
            try:
                answer = process_task(task_name, task_instruction, case.strip())
                all_responses[task_name] = answer
                
                # Display in respective tab
                with tabs[idx]:
                    display_result(task_name, answer)
                    
            except Exception as e:
                logger.error(f"ERROR in {task_name}: {type(e).__name__}: {str(e)}")
                all_responses[task_name] = f"Error: {str(e)}"
                with tabs[idx]:
                    st.error(f"❌ Error: {str(e)}")
    
    # Save to history
    if all_responses:
        history_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'All Tasks',
            'case': case.strip(),
            'results': all_responses
        }
        st.session_state.history.append(history_entry)
    
    # Combined copy section
    st.markdown("---")
    with st.expander("📄 Copy All Responses", expanded=False):
        combined_text = f"Patient: {case.strip()}\n\n"
        combined_text += "="*50 + "\n\n"
        
        for task_name, response in all_responses.items():
            combined_text += f"### {task_name.upper()}\n"
            combined_text += response + "\n\n"
            combined_text += "="*50 + "\n\n"
        
        st.code(combined_text, language="")
        st.caption("💡 Click the copy icon to copy all responses at once")

# History section
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📜 Previous Runs")
    
    # Add clear history button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.caption(f"Showing {len(st.session_state.history)} previous runs")
    with col2:
        if st.button("🗑️ Clear", key="clear_history"):
            st.session_state.history = []
            st.rerun()
    
    # Display history in reverse chronological order
    for idx, entry in enumerate(reversed(st.session_state.history)):
        with st.container():
            # Header with run info
            st.markdown(f"#### Run #{len(st.session_state.history) - idx} - {entry['timestamp']}")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Type:** {entry['type']}")
            with col2:
                st.markdown(f"**Tasks:** {len(entry['results'])}")
            
            # Show full patient presentation
            st.info(f"**Patient:** {entry['case']}")
            
            # Show results for each task
            st.markdown("**Results:**")
            for task_name, response in entry['results'].items():
                with st.container():
                    st.markdown(f"**{task_name}:**")
                    # Display formatted response
                    if response and "Error:" not in response:
                        lines = response.strip().split('\n')
                        formatted = ""
                        for line in lines:
                            line = line.strip()
                            if line:
                                formatted += f"{line}\n"
                        st.code(formatted, language="")
                    else:
                        st.error(response)
            
            st.markdown("---")

# Footer with confirmation of o3 model
st.markdown("---")
st.caption("Clinical judgment required – not a substitute for professional assessment.")
st.caption("🤖 Using OpenAI o3 model with medium reasoning effort")