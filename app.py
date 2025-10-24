import streamlit as st
import openai
import google.generativeai as genai
from typing import Dict
from PyPDF2 import PdfReader
from datetime import datetime, timezone
from supabase import create_client
from postgrest.exceptions import APIError  # for catching Supabase errors

# --- Page Setup ---
st.set_page_config(page_title="TN Startup Assistant", layout="wide")

# --- Sidebar ---
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
if api_provider == "Gemini (Google)":
    genai.configure(api_key=api_key)
    gmodel = genai.GenerativeModel("gemini-2.5-flash")
    def run_model(prompt):
        return gmodel.generate_content(prompt).text.strip()
else:
    openai.api_key = api_key
    def run_model(prompt):
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

# --- Load Policy PDF (cached for speed) ---
@st.cache_data(show_spinner=False)
def load_policy_text():
    try:
        reader = PdfReader("Tamil_Nadu_Startup_Policy.pdf")
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    except Exception as e:
        st.warning("Policy PDF not found or unreadable.")
        return ""
st.session_state.policy_text = st.session_state.get("policy_text", load_policy_text())

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"].strip()
SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_session(data: Dict):
    """Insert session data into Supabase with safe error handling."""
    try:
        res = supabase.table("startup_sessions").insert(data).execute()
        if res.status_code != 201:
            st.error(f"Failed to log session (Status {res.status_code})")
    except APIError as e:
        st.error(f"Database Error: {e.message}")
    except Exception as e:
        st.error(f"Unexpected Error: {e}")

# --- Session State ---
if "stage" not in st.session_state:
    st.session_state.stage = "start"
    st.session_state.answers = {}
    st.session_state.language = "English"
    st.session_state.session_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

# --- Language Toggle ---
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
        "ask_q": "💬 Ask any question about Tamil Nad_
