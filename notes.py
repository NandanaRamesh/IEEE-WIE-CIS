import streamlit as st
import os
from database import supabase_client as supabase
from PyPDF2 import PdfReader
from google.generativeai import configure, GenerativeModel
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from dotenv import load_dotenv

load_dotenv()

# Configure Gemini-1.5-Pro API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("gemini-1.5-pro")


def fetch_document_content(file_name):
    """Fetches and reads the selected document from session state or Supabase Storage."""

    # Check if the document is already stored in session state
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
            document_text = response.decode("utf-8")  # Convert bytes to text
            st.session_state["selected_document_text"] = document_text  # Store in session state
            return document_text
        else:
            st.error("Failed to retrieve the document.")
            return None
    except Exception as e:
        st.error(f"Error retrieving document: {e}")
        return None


def analyze_notes(content, user_prompt):
    """Uses Gemini AI to analyze, structure, and enhance notes."""
    prompt = (
        f"Analyze and enhance the following notes to improve learning. "
        f"Add structured sections, images, flowcharts, and acronyms where necessary. "
        f"User request: {user_prompt}\n\n{content}"
    )

    try:
        response = model.generate_content(prompt)
        return response.text if response else "AI analysis failed."
    except Exception as e:
        st.error(f"Error in AI analysis: {e}")
        return None


def create_stylized_pdf(text):
    """Generates a properly formatted PDF with styles, headings, and bullet points."""
    pdf_path = "Enhanced_Notes.pdf"

    # Define the document template
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    elements = []

    # Register a custom font (Times New Roman)
    pdfmetrics.registerFont(TTFont("Times", "times.ttf"))

    # Split text into sections
    lines = text.split("\n")

    for line in lines:
        if line.strip() == "":
            elements.append(Spacer(1, 12))  # Add spacing for paragraph breaks
        elif line.startswith("### "):  # Big Heading
            elements.append(Paragraph(f"<font size=16><b>{line[4:]}</b></font>", styles["Title"]))
            elements.append(Spacer(1, 10))
        elif line.startswith("## "):  # Medium Heading
            elements.append(Paragraph(f"<font size=14><b>{line[3:]}</b></font>", styles["Heading2"]))
            elements.append(Spacer(1, 8))
        elif line.startswith("# "):  # Small Heading
            elements.append(Paragraph(f"<font size=12><b>{line[2:]}</b></font>", styles["Heading3"]))
            elements.append(Spacer(1, 6))
        elif line.startswith("- "):  # Bullet points
            elements.append(Paragraph(f"• {line[2:]}", styles["BodyText"]))
            elements.append(Spacer(1, 4))
        elif "**" in line:  # Bold text
            formatted_line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
            elements.append(Paragraph(formatted_line, styles["BodyText"]))
        elif "*" in line:  # Italics
            formatted_line = line.replace("*", "<i>", 1).replace("*", "</i>", 1)
            elements.append(Paragraph(formatted_line, styles["BodyText"]))
    else:  # Regular paragraph text
            elements.append(Paragraph(line, styles["BodyText"]))

    elements.append(PageBreak())  # Add a final page break if needed

    # Build the PDF
    doc.build(elements)
    return pdf_path

def notes_page():
    """Displays the AI-Enhanced Notes page in Streamlit."""
    st.title("📑 AI-Enhanced Notes")
    st.write("AI will enhance your selected document for better learning.")

    # Retrieve document content from session state
    file_content = st.session_state.get("selected_document_text")

    if not file_content:
        st.warning("⚠️ No document content available. Please upload or select a document.")
        return

    # Convert file content to text
    text = ""
    try:
        if isinstance(file_content, bytes):  # Handle PDFs stored as bytes
            from io import BytesIO
            pdf_reader = PdfReader(BytesIO(file_content))
            text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        else:
            text = file_content  # Assume it's already text
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return

    # Display the document content
    st.text_area("📄 Document Content", text, height=300, disabled=True)

    user_prompt = st.text_area("✍️ Specify your learning focus",
                               placeholder="Summarize key concepts, explain acronyms, etc.")

    if st.button("🧠 Enhance Notes"):
        enhanced_notes = analyze_notes(text, user_prompt)
        st.session_state["enhanced_notes"] = enhanced_notes

        st.text_area("📘 Enhanced Notes", enhanced_notes, height=400, disabled=True)

        # Generate a properly formatted PDF
        pdf_path = create_stylized_pdf(enhanced_notes)

        with open(pdf_path, "rb") as pdf_file:
            st.download_button(label="📥 Download Enhanced Notes (Styled PDF)",
                               data=pdf_file, file_name="Enhanced_Notes.pdf",
                               mime="application/pdf")
