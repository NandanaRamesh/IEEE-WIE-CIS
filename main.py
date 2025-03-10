import streamlit as st
from database import supabase_client as supabase
from login import login
from signup import sign_up
from datetime import datetime
from notes import notes_page
from dotenv import load_dotenv
import google.generativeai as genai
import fitz
import io
import os
from chatbot import chatbot_interface
from flashcards import show_flashcards
from quiz import show_quiz

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def upload_document():
    """Handles document upload to the selected chat folder in Supabase Storage."""
    st.sidebar.subheader("📂 Upload Document")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf"])

    if uploaded_file:
        user_display_name = st.session_state["username"]
        selected_chat = st.session_state.get("selected_chat")

        if not selected_chat:
            st.sidebar.error("Please select or create a chat first.")
            return

        bucket_name = "user-documents"
        file_path = f"{user_display_name}/{selected_chat}/{uploaded_file.name}"

        try:
            # Read file content correctly
            file_bytes = uploaded_file.read()

            # Upload file as bytes
            supabase.storage.from_(bucket_name).upload(file_path, file_bytes)

            st.sidebar.success(f"Uploaded '{uploaded_file.name}' to '{selected_chat}' successfully!")
        except Exception as e:
            st.sidebar.error(f"Upload failed: {e}")


def fetch_user_documents():
    """Fetches all documents for the selected chat history from Supabase Storage."""
    user_display_name = st.session_state["username"]
    bucket_name = "user-documents"

    # Ensure a chat is selected
    selected_chat = st.session_state["selected_chat"]
    if not selected_chat:
        st.sidebar.warning("No chat history selected.")
        return []

    chat_folder = f"{user_display_name}/{selected_chat}/"

    try:
        response = supabase.storage.from_(bucket_name).list(chat_folder)


        if response:
            return [file["name"] for file in response]
        else:
            st.sidebar.warning("No documents found in this chat history.")
            return []
    except Exception as e:
        st.sidebar.error(f"Failed to fetch documents: {e}")
        return []

# Function to render sidebar options
def sidebar_options():
    """Renders sidebar options when the user is logged in."""
    
    # Home Button - Reload Streamlit
    if st.sidebar.button("🎓 Home"):
        st.session_state["page"] = "home"
        st.rerun()

    if "user_logged_in" in st.session_state and st.session_state["user_logged_in"]:
        st.sidebar.subheader(f"👤 Welcome, {st.session_state['username']}!")

        # Document Upload
        upload_document()

        # Chat History
        st.sidebar.subheader("💬 Chat History")
        user_display_name = st.session_state["username"]

        response = supabase.table("Chat-History").select("id", "name").eq("displayname", user_display_name).execute()
        chat_histories = response.data if response.data else []

        chat_options = ["➕ Create New Chat"] + [chat["name"] for chat in chat_histories]
        selected_chat = st.sidebar.selectbox("Select a chat history:", chat_options, index=0)
        st.session_state["selected_chat"] = selected_chat

        if selected_chat == "➕ Create New Chat":
            st.session_state["creating_chat"] = True
        else:
            if st.session_state.get("selected_chat") != selected_chat:
                st.session_state["selected_chat"] = selected_chat
                st.rerun()
                st.session_state["creating_chat"] = False
            else:
                st.sidebar.success(f"Selected Chat: {selected_chat}")
                st.session_state["selected_chat"] = selected_chat
                st.session_state["creating_chat"] = False

        if st.session_state.get("creating_chat", True):
            chat_name = st.sidebar.text_input("Enter chat history name")
            if st.sidebar.button("Save Chat"):
                if chat_name.strip():
                    save_chat_history(chat_name)
                    st.session_state["creating_chat"] = False
                    st.rerun()
                else:
                    st.sidebar.error("Chat name cannot be empty.")

        # Sidebar Section: View Available Documents
        st.sidebar.subheader("📑 Select Documents")

        # Add a "Fetch" button to trigger fetching documents
        if st.sidebar.button("🔄 Fetch Documents"):
            st.session_state["documents"] = fetch_user_documents()  # Store fetched documents in session state

        # Retrieve stored documents or set an empty list if not fetched yet
        documents = st.session_state.get("documents", [])

        # Allow user to select documents if available
        selected_docs = st.sidebar.multiselect("Choose documents:", documents) if documents else []
        st.session_state["selected_docs"] = selected_docs  # Store it in session state

        col1, col2 = st.sidebar.columns(2)
        with col1:

            if st.button("📂 Load") and selected_docs:
                document_contents = []
                bucket_name = "user-documents"

                for doc in selected_docs:
                    file_path = f"{user_display_name}/{selected_chat}/{doc}"
                    print(file_path)

                    try:
                        response = supabase.storage.from_(bucket_name).download(file_path)

                        if doc.lower().endswith(".pdf"):  # Handle PDFs
                            pdf_bytes = io.BytesIO(response)  # Convert bytes to file-like object

                            with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_reader:  # Properly open PDF
                                pdf_text = "\n\n".join([page.get_text() for page in pdf_reader])

                            document_contents.append(pdf_text)

                        else:  # Handle text-based files normally
                            document_contents.append(response.decode("utf-8"))

                    except Exception as e:
                        st.sidebar.error(f"Error loading {doc}: {e}")

                if document_contents:
                    st.session_state["selected_document_text"] = "\n\n".join(document_contents)
                    st.sidebar.success(f"Loaded: {', '.join(selected_docs)}")


        with col2:
            if st.button("❌ Delete") and selected_docs:
                delete_documents(selected_docs)

        # Full-width Buttons using CSS
        st.sidebar.markdown(
            """
            <style>
            div.stButton > button {
                width: 100%;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Other Functionalities
        if st.sidebar.button("📖 Flash Cards"):
            st.session_state["page"]="flashcard"
        if st.sidebar.button("📝 Notes"):
            st.session_state["page"] = "notes"
        if st.sidebar.button("📖 Quiz"):
            st.session_state["page"]="quiz"

        # Logout Button
        if st.sidebar.button("🚪 Log Out"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.rerun()

    else:
        if "page" in st.session_state and st.session_state["page"] != "home":
            st.session_state["page"] = "home"
            st.rerun()


def delete_documents(file_names):
    """Deletes multiple documents from Supabase Storage."""
    try:
        user_display_name = st.session_state["username"]
        bucket_name = "user-documents"
        file_paths = [f"{user_display_name}/{file}" for file in file_names]

        supabase.storage.from_(bucket_name).remove(file_paths)
        st.sidebar.success(f"Deleted: {', '.join(file_names)} successfully!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Failed to delete documents: {e}")


def save_chat_history(chat_name):
    """Saves the new chat history in Supabase and creates a dedicated folder."""
    try:
        user_display_name = st.session_state["username"]

        # Fetch last chat history ID and increment it
        response = supabase.table("Chat-History").select("id").order("id", desc=True).limit(1).execute()

        if response.data:
            last_id = response.data[0]["id"]
            last_number = int(last_id[2:])
            new_id = f"ID{last_number + 1:04d}"
        else:
            new_id = "ID0001"

        supabase.table("Chat-History").insert({
            "id": new_id,
            "name": chat_name,
            "created_at": datetime.utcnow().isoformat(),
            "displayname": user_display_name
        }).execute()

        # Create chat folder inside the user's directory
        bucket_name = "user-documents"
        chat_folder = f"{user_display_name}/{chat_name}/"
        placeholder_file_path = f"{chat_folder}placeholder.txt"
        placeholder_content = b"Folder placeholder"

        supabase.storage.from_(bucket_name).upload(placeholder_file_path, placeholder_content)

        st.sidebar.success(f"Chat history '{chat_name}' created successfully!")
        st.session_state["creating_chat"] = False
        st.session_state["selected_chat"] = chat_name  # Set the new chat as selected
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error creating chat history: {e}")


def homepage():
    """Main homepage with chat history handling."""
    st.title("AI-Powered Tutoring System")
    st.write("Welcome to the AI Tutoring System! Learn complex topics easily and reinforce learning with AI-generated quizzes.")

    if "user_logged_in" in st.session_state and st.session_state["user_logged_in"]:
        st.success(f"Welcome, {st.session_state['username']}!")
        model = genai.GenerativeModel("gemini-1.5-flash")
        document_text = st.session_state.get("selected_document_text", "")
        chatbot_interface(model, document_text)


def main():
    st.set_page_config(page_title="AI Tutoring System", page_icon="🎓")

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    with st.sidebar:
        if "user_logged_in" not in st.session_state or not st.session_state["user_logged_in"]:
            if st.button("Sign Up"):
                st.session_state["page"] = "signup"
                st.rerun()
            if st.button("Login"):
                st.session_state["page"] = "login"
                st.rerun()
        else:
            sidebar_options()
    

    if st.session_state["page"] == "home":
        homepage()
    elif st.session_state["page"] == "flashcard":
        document_text = st.session_state.get("selected_document_text", "")
        show_flashcards(model,document_text)
    elif st.session_state["page"] == "quiz":
        document_text = st.session_state.get("selected_document_text", "")
        show_quiz(model,document_text)
    elif st.session_state["page"] == "login":
        login()
    elif st.session_state["page"] == "signup":
        sign_up()
    elif st.session_state["page"] == "notes":
        notes_page()


if __name__ == "__main__":
    main()
