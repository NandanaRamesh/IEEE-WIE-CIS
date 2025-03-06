import streamlit as st
import os
from database import supabase_client as supabase
from PyPDF2 import PdfReader
from google.generativeai import configure, GenerativeModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini-1.5-Pro API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("gemini-1.5-pro")


def fetch_document_content(file_name):
    """Fetches and reads the selected document from session state or Supabase Storage."""
    if "selected_document_text" in st.session_state:
        return st.session_state["selected_document_text"]

    user_display_name = st.session_state["username"]
    selected_chat = st.session_state.get("selected_chat")

    if not selected_chat:
        st.sidebar.error("Please select a chat first.")
        return None

    bucket_name = "user-documents"
    file_path = f"{user_display_name}/{selected_chat}/{file_name}"

    try:
        response = supabase.storage.from_(bucket_name).download(file_path)
        if response:
            document_text = response.decode("utf-8")
            st.session_state["selected_document_text"] = document_text
            return document_text
        else:
            st.error("Failed to retrieve the document.")
            return None
    except Exception as e:
        st.error(f"Error retrieving document: {e}")
        return None


def analyze_notes(content, user_prompt):
    """Uses Gemini AI to analyze and enhance notes."""
    prompt = (
        f"Analyze and enhance the following notes for better learning. "
        f"User request: {user_prompt}\n\n{content}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text if response else "AI analysis failed."
    except Exception as e:
        st.error(f"Error in AI analysis: {e}")
        return None


def create_simple_pdf(text):
    """Generates a simple PDF with plain text."""
    pdf_path = "Enhanced_Notes.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    for line in text.split("\n"):
        elements.append(Paragraph(line, styles["BodyText"]))
        elements.append(Spacer(1, 12))

    doc.build(elements)
    return pdf_path


def notes_page():
    """Displays the AI-Enhanced Notes page in Streamlit."""
    st.title("📑 AI-Enhanced Notes")
    st.write("AI will enhance your selected document for better learning.")

    file_content = st.session_state.get("selected_document_text")

    if not file_content:
        st.warning("⚠️ No document content available. Please upload or select a document.")
        return

    text = ""
    try:
        if isinstance(file_content, bytes):
            from io import BytesIO
            pdf_reader = PdfReader(BytesIO(file_content))
            text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        else:
            text = file_content
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return

    st.text_area("📄 Document Content", text, height=300, disabled=True)
    user_prompt = st.text_area("✍️ Specify your learning focus",
                               placeholder="Summarize key concepts, explain acronyms, etc.")

    if st.button("🧠 Enhance Notes"):
        enhanced_notes = analyze_notes(text, user_prompt)
        st.session_state["enhanced_notes"] = enhanced_notes
        st.text_area("📘 Enhanced Notes", enhanced_notes, height=400, disabled=True)

        pdf_path = create_simple_pdf(enhanced_notes)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(label="📥 Download Enhanced Notes (PDF)", data=pdf_file, file_name="Enhanced_Notes.pdf",
                               mime="application/pdf")
