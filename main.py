import streamlit as st
from database import supabase_client as supabase
from login import login
from signup import sign_up
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def upload_document():
    """Handles document upload to Supabase Storage."""
    st.sidebar.subheader("📂 Upload Document")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "txt", "docx"])

    if uploaded_file:
        user_display_name = st.session_state["username"]
        bucket_name = "user-documents"
        file_path = f"{user_display_name}/{uploaded_file.name}"

        try:
            supabase.storage.from_(bucket_name).upload(file_path, uploaded_file.getvalue())
            st.sidebar.success(f"Uploaded '{uploaded_file.name}' successfully!")
        except Exception as e:
            st.sidebar.error(f"Upload failed: {e}")


def fetch_user_documents():
    """Fetches all documents for the logged-in user from Supabase Storage."""
    user_display_name = st.session_state["username"]
    bucket_name = "user-documents"

    try:
        response = supabase.storage.from_(bucket_name).list(user_display_name)
        return [file["name"] for file in response]
    except Exception as e:
        st.sidebar.error(f"Failed to fetch documents: {e}")
        return []


def sidebar_options():
    """Renders sidebar options when user is logged in."""
    # Large College Scholar Emoji as Home Button
    st.sidebar.markdown(
        """
        <style>
            .emoji-button {
                font-size: 50px;
                text-align: left;
                display: block;
                cursor: pointer;
            }
        </style>
        <a href="#" class="emoji-button" onclick="window.location.reload();">🎓</a>
        """,
        unsafe_allow_html=True
    )

    if "user_logged_in" in st.session_state and st.session_state["user_logged_in"]:
        st.sidebar.subheader(f"👤 Welcome, {st.session_state['username']}!")

        # Document Upload
        upload_document()

        # View Available Documents
        st.sidebar.subheader("📑 Select Documents")
        documents = fetch_user_documents()
        if documents:
            selected_docs = st.sidebar.multiselect("Choose documents:", documents)

            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("📂 Load") and selected_docs:
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

        # Other Functionalities (Properly Styled Buttons)
        if st.sidebar.button("📖 Flash Cards"):
            st.sidebar.info("Flash Cards feature coming soon!")

        if st.sidebar.button("📝 Notes"):
            st.sidebar.info("Notes feature coming soon!")

        # Logout Button (Now Works Correctly)
        if st.sidebar.button("🚪 Log Out"):
            st.session_state.clear()
            st.session_state["page"] = "home"  # Ensure it redirects to home
            st.rerun()

        # Chat History
        st.sidebar.subheader("💬 Chat History")
        user_display_name = st.session_state["username"]
        response = supabase.table("Chat-History").select("id", "name").eq("displayname", user_display_name).execute()
        chat_histories = response.data if response.data else []

        chat_options = ["➕ Create New Chat"] + [chat["name"] for chat in chat_histories]
        selected_chat = st.sidebar.selectbox("Select a chat history:", chat_options, index=0)

        if selected_chat == "➕ Create New Chat":
            st.session_state["creating_chat"] = True
        else:
            st.session_state["creating_chat"] = False
            st.session_state["selected_chat"] = selected_chat
            st.sidebar.success(f"Selected Chat: {selected_chat}")

        if st.session_state.get("creating_chat", False):
            chat_name = st.sidebar.text_input("Enter chat history name")
            if st.sidebar.button("Save Chat"):
                if chat_name.strip():
                    save_chat_history(chat_name)
                    st.session_state["creating_chat"] = False
                    st.rerun()
                else:
                    st.sidebar.error("Chat name cannot be empty.")

    else:
        # Redirect to homepage when emoji is clicked (for logged-out users)
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
    """Saves the new chat history in Supabase and creates necessary folders."""
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

        # Create user folder in Supabase Storage
        bucket_name = "user-documents"
        user_folder = f"{user_display_name}/"
        placeholder_file_path = f"{user_folder}placeholder.txt"
        placeholder_content = b"Folder placeholder"

        supabase.storage.from_(bucket_name).upload(placeholder_file_path, placeholder_content)

        st.sidebar.success(f"Chat history '{chat_name}' created successfully!")
        st.session_state["creating_chat"] = False
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error creating chat history: {e}")


def homepage():
    """Main homepage with chat history handling."""
    st.title("AI-Powered Tutoring System")
    st.write("Welcome to the AI Tutoring System! Learn complex topics easily and reinforce learning with AI-generated quizzes.")

    if "user_logged_in" in st.session_state and st.session_state["user_logged_in"]:
        st.success(f"Welcome, {st.session_state['username']}!")


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
    elif st.session_state["page"] == "login":
        login()
    elif st.session_state["page"] == "signup":
        sign_up()


if __name__ == "__main__":
    main()
