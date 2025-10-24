import os
import streamlit as st
import openai
import google.generativeai as genai
from typing import Dict
from PyPDF2 import PdfReader
from datetime import datetime, timezone
from supabase import create_client
# Import the specific error for better error handling
from postgrest.exceptions import APIError 

# --- API Config ---
st.set_page_config(page_title="TN Startup Assistant", layout="wide")

st.sidebar.title("🔐 API Configuration")
api_provider = st.sidebar.selectbox("Choose LLM Provider", ["Gemini (Google)", "OpenAI (ChatGPT)"])
api_key = st.sidebar.text_input("Enter your API Key", type="password")

if not api_key:
    st.sidebar.warning("Please enter your API key to start using the assistant.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <a href="https://www.linkedin.com/in/ganesh-kumar-e1609" target="_blank">
        <button style="width:100%;padding:0.5rem 1rem;background-color:#0A66C2;color:white;border:none;border-radius:5px;cursor:pointer;">
            🔗 Visit My LinkedIn
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# --- Model Setup ---
# Use st.cache_resource for the model setup since it's an expensive, persistent object
@st.cache_resource
def setup_model(provider, key):
    if provider == "Gemini (Google)":
        genai.configure(api_key=key)
        return genai.GenerativeModel("gemini-2.5-flash")
    else:
        openai.api_key = key
        # Return a simple object/dict or a class instance if needed, but the wrapper handles the call
        return "OpenAI Ready"

model_config = setup_model(api_provider, api_key)

def run_model(prompt):
    if api_provider == "Gemini (Google)":
        # model_config is the GenerativeModel instance
        return model_config.generate_content(prompt).text.strip()
    else:
        # openai.api_key is set globally
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

# --- Load Policy PDF for RAG ---
# Use st.cache_data since the policy text is static data
@st.cache_data(show_spinner="Loading policy document...")
def load_policy_pdf():
    try:
        reader = PdfReader("Tamil_Nadu_Startup_Policy.pdf")
        return "\n".join([
            p.extract_text() for p in reader.pages if p.extract_text()
        ])
    except Exception as e:
        st.error(f"Could not load PDF policy file: {e}")
        return ""

st.session_state.policy_text = load_policy_pdf()

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_session(data: Dict):
    try:
        # The execute() method should raise an APIError on failure
        supabase.table("startup_sessions").insert(data).execute()
    except APIError as e:
        # Catching the specific error raised by the postgrest client
        st.error(f"Failed to log session to Supabase. RLS/Database Error: {e.message}")
        # Optionally, print the full traceback for debugging (not shown to user)
        # st.exception(e) 

# --- Session State ---
if "stage" not in st.session_state:
    st.session_state.stage = "start"
    st.session_state.answers = {}
    st.session_state.language = "English"
    st.session_state.session_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

# --- Language Toggle (Kept the same) ---
lang = st.selectbox("Choose Language / மொழியைத் தேர்ந்தெடுக்கவும்", ["English", "தமிழ்"])
st.session_state.language = lang

T = {
    "English": {
        "welcome": "Welcome! Let's turn your idea into a registered startup in Tamil Nadu.",
        "idea_q": "1️⃣ What's your startup idea (1–2 lines)?",
        "founder_q": "2️⃣ How many founders are involved?",
        "funding_q": "3️⃣ Do you plan to raise funding?",
        "yes": "Yes", "no": "No",
        "continue": "Continue to Policy Q&A",
        "upload_prompt": "📎 Upload your idea deck or pitch (PDF only):",
        "processing_file": "Analyzing your uploaded PDF...",
        "summary_title": "📝 Summary of Uploaded Idea Deck",
        "score_title": "🚦 Startup Readiness Score",
        "scheme_match": "🏷️ Suggested Startup Schemes for You",
        "incubator_match": "🏢 Nearest Incubators Based on Your Location",
        "deadlines": "📅 Active Grant Deadlines in Tamil Nadu",
        "feedback": "📝 Was this answer helpful?",
        "saved": "📦 Your session was saved successfully.",
        "ask_q": "💬 Ask any question about Tamil Nadu startup policy, registration, or benefits"
    },
    "தமிழ்": {
        "welcome": "வணக்கம்! உங்கள் யோசனையை தமிழ்நாட்டில் பதிவு செய்யப்பட்ட ஸ்டார்ட்அப்பாக மாற்றுவோம்.",
        "idea_q": "1️⃣ உங்கள் ஸ்டார்ட்அப் யோசனை என்ன? (1–2 வரிகளில்)",
        "founder_q": "2️⃣ எத்தனை நிறுவியர்கள் உள்ளனர்?",
        "funding_q": "3️⃣ முதலீட்டைத் தேடுகிறீர்களா?",
        "yes": "ஆம்", "no": "இல்லை",
        "continue": "கொள்கை கேள்விகளுக்கு தொடருங்கள்",
        "upload_prompt": "📎 உங்கள் ஐடியா டெக் அல்லது பிச்சை PDF வடிவில் பதிவேற்றவும்:",
        "processing_file": "பதிவேற்றிய கோப்பை பகுப்பாய்வு செய்கிறோம்...",
        "summary_title": "📝 பதிவேற்றிய டெக்கின் சுருக்கம்",
        "score_title": "🚦 ஸ்டார்ட்அப் தயார் மதிப்பெண்",
        "scheme_match": "🏷️ உங்களுக்கு பொருந்தும் ஸ்டார்ட்அப் திட்டங்கள்",
        "incubator_match": "🏢 உங்கள் மாவட்டத்திற்கு அருகிலுள்ள இன்கியூபேட்டர்கள்",
        "deadlines": "📅 தமிழ்நாட்டில் இயங்கும் நிதி வாய்ப்புகள்",
        "feedback": "📝 இந்த பதில் பயனுள்ளதா?",
        "saved": "📦 உங்கள் அமர்வு வெற்றிகரமாக சேமிக்கப்பட்டது.",
        "ask_q": "💬 தமிழ்நாடு ஸ்டார்ட்அப் கொள்கை, பதிவு அல்லது நன்மைகள் பற்றி கேளுங்கள்"
    }
}
ltext = T[st.session_state.language]

# --- LLM Wrappers (Cached) ---

# Central context manager
LLM_CONTEXT = "You are an expert on the Tamil Nadu Startup Policy. Your response must be concise and actionable."

@st.cache_data(ttl=3600, show_spinner=False)
def summarize_pdf(_text):
    prompt = f"{LLM_CONTEXT} Summarize the following startup pitch in a few bullet points: {_text[:8000]}"
    return run_model(prompt)

@st.cache_data(ttl=3600, show_spinner=False)
def readiness_score(_text):
    prompt = f"{LLM_CONTEXT} Score the startup idea from 0–100 for readiness based on the text. Provide a brief explanation of the score. Text: {_text[:8000]}"
    return run_model(prompt)

@st.cache_data(ttl=3600, show_spinner=False)
def match_schemes(_text):
    prompt = f"{LLM_CONTEXT} Suggest 3 relevant Tamil Nadu startup schemes based on this idea: {_text[:5000]}. Be specific with names."
    return run_model(prompt)

@st.cache_data(ttl=3600, show_spinner=False)
def find_incubators(district):
    prompt = f"{LLM_CONTEXT} List 3 active startup incubators or co-working spaces in or near the district: {district}"
    return run_model(prompt)

@st.cache_data(ttl=3600, show_spinner=False)
def grant_deadlines():
    prompt = f"{LLM_CONTEXT} List 3 current or recurring startup grant and funding deadlines specific to Tamil Nadu, including their source or link. If none are current, state this clearly."
    return run_model(prompt)

def policy_qa(question):
    # This is not cached as it's an interactive QA session
    context = st.session_state.policy_text[:16000] if st.session_state.policy_text else ""
    prompt = f"{LLM_CONTEXT}\nUse the Tamil Nadu Startup Policy below to answer the question:\n\n{context}\n\nQuestion: {question}\nAnswer:"
    return run_model(prompt)

# --- UI Flow ---
st.title("🧠 Tamil Nadu Startup Assistant")

# Helper function for stage transition
def set_stage(stage_name):
    st.session_state.stage = stage_name

if st.session_state.stage == "start":
    set_stage("ask_idea")
    st.success(ltext["welcome"])

if st.session_state.stage == "ask_idea":
    idea = st.text_input(ltext["idea_q"], value=st.session_state.answers.get("idea", ""))
    if idea:
        st.session_state.answers["idea"] = idea
        st.button("Next ➡️", on_click=set_stage, args=["ask_founders"])

elif st.session_state.stage == "ask_founders":
    # Use existing value if available
    founders_str = st.session_state.answers.get("founder_count", "")
    founders = st.text_input(ltext["founder_q"], value=str(founders_str))
    
    if founders.isdigit():
        st.session_state.answers["founder_count"] = int(founders)
        st.button("Next ➡️", on_click=set_stage, args=["ask_funding"])
    elif founders:
        st.error("Please enter a number for the founder count.")

elif st.session_state.stage == "ask_funding":
    # Use index 0 for Yes, 1 for No to select the default
    default_index = 0 if st.session_state.answers.get("funding_needed") else 1
    funding = st.radio(ltext["funding_q"], [ltext["yes"], ltext["no"]], index=default_index)
    
    st.session_state.answers["funding_needed"] = funding == ltext["yes"]
    st.button("Next ➡️", on_click=set_stage, args=["ask_location"])

elif st.session_state.stage == "ask_location":
    district = st.text_input("📍 Your District", value=st.session_state.answers.get("district", ""))
    if district:
        st.session_state.answers["district"] = district
        st.button("Next ➡️", on_click=set_stage, args=["upload_pdf"])

elif st.session_state.stage == "upload_pdf":
    st.markdown(f"### {ltext['upload_prompt']}")
    uploaded = st.file_uploader("Upload PDF", type="pdf")
    
    # Use the combination of idea and file content for analysis
    user_text = st.session_state.answers["idea"]
    
    if uploaded or st.button("Skip PDF and Analyze with Idea Only"):
        file_text = ""
        if uploaded:
            # Re-read the PDF if uploaded
            with st.spinner("Reading PDF..."):
                reader = PdfReader(uploaded)
                file_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

        user_text += "\n" + file_text
        st.session_state.answers["full_text"] = user_text
        
        # --- Run LLM Analysis (Cached) ---
        with st.spinner(ltext['processing_file']):
            ans = st.session_state.answers
            # The cache key is based on the input text, so we pass user_text
            ans["summary"] = summarize_pdf(user_text)
            ans["score"] = readiness_score(user_text)
            ans["schemes"] = match_schemes(user_text)
            # Incubators and Deadlines are only cached based on district/no args
            ans["incubators"] = find_incubators(ans["district"])
            ans["deadlines"] = grant_deadlines()

        set_stage("results")
        st.rerun() # Rerun to display results

elif st.session_state.stage == "results":
    ans = st.session_state.answers
    
    st.subheader(ltext["summary_title"])
    st.write(ans["summary"])
    
    st.subheader(ltext["score_title"])
    st.success(ans["score"])
    
    st.subheader(ltext["scheme_match"])
    st.info(ans["schemes"])
    
    st.subheader(ltext["incubator_match"])
    st.info(ans["incubators"])
    
    st.subheader(ltext["deadlines"])
    st.warning(ans["deadlines"])

    # --- Log Session Data (Updated Error Handling is inside log_session) ---
    log_session({
        "session_id": st.session_state.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "language": st.session_state.language,
        "idea": ans["idea"],
        # Ensure numerical data types are handled (though Supabase often casts strings)
        "founder_count": ans["founder_count"],
        "funding_needed": ans["funding_needed"], # Boolean is fine for Supabase, but logged as Python bool
        "district": ans["district"],
        "score": ans["score"][:500], # Truncate long LLM outputs if the DB column is small
        "company_type": "Auto", # Static value
        "schemes": ans["schemes"][:500],
        "incubators": ans["incubators"][:500],
        "pdf_uploaded": 1 if len(ans.get("full_text", "")) > len(ans["idea"]) else 0
    })
    st.success(ltext["saved"])
    set_stage("qa")
    st.rerun() # Rerun to switch to QA stage

elif st.session_state.stage == "qa":
    st.markdown(f"### {ltext['ask_q']}")
    
    # Display previous results for context
    with st.expander("Review Analysis"):
        ans = st.session_state.answers
        st.markdown(f"**{ltext['score_title']}**: {ans['score']}")
        st.markdown(f"**{ltext['scheme_match']}**: {ans['schemes']}")
        
    q = st.text_input("Q:")
    if q:
        with st.spinner("Thinking..."):
            response = policy_qa(q)
            st.markdown("---")
            st.success(response)
            st.markdown("---")
            st.radio(ltext["feedback"], ["👍", "👎"], key="feedback_radio") # Use a key
