# 🧠 TN Startup Assistant

This is an interactive chatbot designed to assist Tamil Nadu entrepreneurs in turning their ideas into registered startups. It provides tailored guidance based on user inputs and the Tamil Nadu Startup & Innovation Policy.

---

## Features

* 🔐 Supports both **OpenAI** and **Gemini** API integration.
* 📎 PDF upload for startup pitch analysis.
* 🚦 Startup Readiness Score based on your idea.
* 🏷️ Recommends Tamil Nadu government startup schemes.
* 🏢 Lists nearest incubators based on user location.
* 📅 Shows active grant deadlines in TN.
* 💬 Built-in Q&A referencing the official Tamil Nadu Startup Policy.
* 🌐 Bilingual interface: English and தமிழ்
* 🧠 RAG (Retrieval-Augmented Generation) model backed by policy document.
* 🗃️ Session data storage in Supabase.

---

## File Structure

```
📁 tn-startup-assistant/
├── app.py                      # Main Streamlit app
├── requirements.txt           # Python dependencies
├── .streamlit/
│   └── secrets.toml           # API keys and Supabase credentials (not pushed to GitHub)
├── Tamil_Nadu_Startup_Policy.pdf # Policy doc used for RAG
└── README.md
```

---

## Notes

* Do **not** upload your `.streamlit/secrets.toml` file to public repositories.
* This project uses [Supabase](https://supabase.io) for session data logging.
* Refer to official sources like [MCA](https://www.mca.gov.in/) or [StartupTN](https://startuptn.in/) for up-to-date registration procedures and document lists.
* For deployment to Streamlit Community Cloud, ensure your repo is private if using `.streamlit/secrets.toml`.

---

## License

MIT License © 2025
