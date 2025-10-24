import os
import streamlit as st
import openai
import google.generativeai as genai
from typing import Dict
from PyPDF2 import PdfReader
from datetime import datetime, timezone
from supabase import create_client

# --- API Config ---
st.set_page_config(page_title="TN Startup Assistant", layout="wide")

st.sidebar.title("🔐 API Configuration")
api_provider = st.sidebar.selectbox("Choose LLM Provider", ["Gemini (Google)", "OpenAI (ChatGPT)"])
api_key = st.sidebar.text_input("Enter your API Key", type="password")

if not api_key:
    st.sidebar.warning("Please enter your API key to start using the assistant.")
    st.stop()

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

# --- Load Policy PDF for RAG ---
if "policy_text" not in st.session_state:
    try:
        reader = PdfReader("Tamil_Nadu_Startup_Policy.pdf")
        st.session_state.policy_text = "\n".join([
            p.extract_text() for p in reader.pages if p.extract_text()
        ])
    except:
        st.session_state.policy_text = ""

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_session(data: Dict):
    response = supabase.table("startup_sessions").insert(data).execute()
    if response.status_code != 201:
        st.error("Failed to log session to Supabase.")

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

# --- LLM Wrappers ---
def summarize_pdf(text): return run_model(f"Summarize startup pitch: {text[:8000]}")
def readiness_score(text): return run_model(f"Score 0–100 and explain: {text[:8000]}")
def match_schemes(text): return run_model(f"Suggest 3 Tamil Nadu startup schemes: {text[:5000]}")
def find_incubators(district): return run_model(f"Incubators in or near {district}")
def grant_deadlines(): return run_model("List startup grant deadlines in Tamil Nadu with links")
def policy_qa(question):
    context = st.session_state.policy_text[:16000] if st.session_state.policy_text else ""
    prompt = f"Use the Tamil Nadu Startup Policy below to answer the question:\n\n{context}\n\nQuestion: {question}\nAnswer:"
    return run_model(prompt)

# --- UI Flow ---
st.title("🧠 Tamil Nadu Startup Assistant")

if st.session_state.stage == "start":
    st.session_state.stage = "ask_idea"
    st.success(ltext["welcome"])

if st.session_state.stage == "ask_idea":
    idea = st.text_input(ltext["idea_q"])
    if idea:
        st.session_state.answers["idea"] = idea
        st.session_state.stage = "ask_founders"
        st.rerun()

elif st.session_state.stage == "ask_founders":
    founders = st.text_input(ltext["founder_q"])
    if founders.isdigit():
        st.session_state.answers["founder_count"] = int(founders)
        st.session_state.stage = "ask_funding"
        st.rerun()

elif st.session_state.stage == "ask_funding":
    funding = st.radio(ltext["funding_q"], [ltext["yes"], ltext["no"]])
    st.session_state.answers["funding_needed"] = funding == ltext["yes"]
    st.session_state.stage = "ask_location"
    st.rerun()

elif st.session_state.stage == "ask_location":
    district = st.text_input("📍 Your District")
    if district:
        st.session_state.answers["district"] = district
        st.session_state.stage = "upload_pdf"
        st.rerun()

elif st.session_state.stage == "upload_pdf":
    st.markdown(f"### {ltext['upload_prompt']}")
    uploaded = st.file_uploader("Upload PDF", type="pdf")
    user_text = st.session_state.answers["idea"]
    if uploaded:
        reader = PdfReader(uploaded)
        file_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        user_text += "\n" + file_text
        st.session_state.answers["full_text"] = user_text
        with st.spinner(ltext['processing_file']):
            ans = st.session_state.answers
            ans["summary"] = summarize_pdf(user_text)
            ans["score"] = readiness_score(user_text)
            ans["schemes"] = match_schemes(user_text)
            ans["incubators"] = find_incubators(ans["district"])
            ans["deadlines"] = grant_deadlines()
        st.session_state.stage = "results"
        st.rerun()

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

    log_session({
        "session_id": st.session_state.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "language": st.session_state.language,
        "idea": ans["idea"],
        "founder_count": ans["founder_count"],
        "funding_needed": str(ans["funding_needed"]),
        "district": ans["district"],
        "score": ans["score"],
        "company_type": "Auto",
        "schemes": ans["schemes"],
        "incubators": ans["incubators"],
        "pdf_uploaded": 1
    })
    st.success(ltext["saved"])
    st.session_state.stage = "qa"
    st.button(ltext["continue"], on_click=lambda: st.rerun())

elif st.session_state.stage == "qa":
    st.markdown(f"### {ltext['ask_q']}")
    q = st.text_input("Q:")
    if q:
        with st.spinner("Thinking..."):
            response = policy_qa(q)
            st.success(response)
            st.radio(ltext["feedback"], ["👍", "👎"])
