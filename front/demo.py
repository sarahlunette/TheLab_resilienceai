import streamlit as st
import requests
import markdown
from fpdf import FPDF
import os

# from dotenv import load_dotev

st.set_page_config(page_title="ResilienceGPT Chatbot", layout="wide")
st.title("🧠 ResilienceGPT — RAG Chatbot (Claude + Qdrant)")

API_URL = (
    "https://resilience-debug-app-763875669747.europe-west1.run.app/chat/mistral-claude"
)
# API_URL = os.getenv("API_URL")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for role, message in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(message)

# Chat input
user_input = st.chat_input("Pose une question…")


def clean_llm_markdown(text: str) -> str:
    import re

    text = text.replace("\\n", "\n").replace("\\t", "    ").strip('"')
    text = re.sub(r"\n\s+(\- |\* |\d+\. |#)", r"\n\1", text)
    text = re.sub(r"\n\s*(#{1,6})\s*", r"\n\1 ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_pdf_from_markdown(markdown_text, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    lines = markdown_text.split("\n")
    for line in lines:
        pdf.multi_cell(0, 5, line)
    pdf.output(output_path)


if user_input:
    st.session_state.messages.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        response = requests.post(API_URL, json={"question": user_input})
        response.raise_for_status()
    except Exception as e:
        st.error(f"❌ Impossible d’appeler l’API : {e}")
        st.stop()

    data = response.json()
    clean_answer = clean_llm_markdown(data["answer"])
    st.session_state.messages.append(("assistant", clean_answer))
    with st.chat_message("assistant"):
        st.markdown(clean_answer)

# PDF export
if st.button("📥 Exporter la conversation en PDF"):
    full_markdown = ""
    for role, msg in st.session_state.messages:
        full_markdown += f"### {role.capitalize()}\n{msg}\n\n"
    out_path = "conversation.pdf"
    generate_pdf_from_markdown(full_markdown, out_path)
    with open(out_path, "rb") as pdf:
        st.download_button(
            "📄 Télécharger le PDF",
            pdf,
            file_name="conversation.pdf",
            mime="application/pdf",
        )
