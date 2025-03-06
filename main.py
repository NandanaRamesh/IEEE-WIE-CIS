import streamlit as st
from database import supabase_client as supabase
from login import login
from signup import sign_up
from datetime import datetime


def create_chat_history():
    """Creates a new chat history entry in Supabase and initializes user folders."""
    st.session_state["creating_chat"] = True


def save_chat_history(chat_name):
    """Saves the new chat history in Supabase and creates necessary folders."""
    try:
        user_display_name = st.session_state["username"]

        # Fetch last chat history ID and increment it
        response = supabase.table("Chat-History").select("id").order("id", desc=True).limit(1).execute()

        if response.data:
            last_id = response.data[0]["id"]  # Fetch the last ID
            last_number = int(last_id[2:])  # Extract numeric part after 'ID'
            new_id = f"ID{last_number + 1:04d}"  # Format as ID0001, ID0002, etc.
        else:
            new_id = "ID0001"  # First chat history entry

        # Insert the new chat history into Supabase
        supabase.table("Chat-History").insert({
            "id": new_id,  # Store as string (e.g., "ID0001")
            "name": chat_name,
            "created_at": datetime.utcnow().isoformat(),
            "displayname": user_display_name
        }).execute()

        # Create user folder in Supabase Storage by uploading a placeholder file
        bucket_name = "user-documents"
        user_folder = f"{user_display_name}/"
        placeholder_file_path = f"{user_folder}placeholder.txt"
        placeholder_content = b"Folder placeholder"

        supabase.storage.from_(bucket_name).upload(placeholder_file_path, placeholder_content)

        st.success(f"Chat history '{chat_name}' created successfully!")
        st.session_state["creating_chat"] = False
        st.rerun()
    except Exception as e:
        st.error(f"Error creating chat history: {e}")


def homepage():
    """Main homepage with chat history handling."""
    st.title("AI-Powered Tutoring System")
    st.write("Welcome to the AI Tutoring System! Learn complex topics easily and reinforce learning with AI-generated quizzes.")

    if "user_logged_in" in st.session_state and st.session_state["user_logged_in"]:
        st.success(f"Welcome, {st.session_state['username']}!")

        # Fetch existing chat histories for the logged-in user
        user_display_name = st.session_state["username"]
        response = supabase.table("Chat-History").select("id", "name").eq("displayname", user_display_name).execute()
        chat_histories = response.data if response.data else []

        # Prepare dropdown options (existing chats + new chat option)
        chat_options = ["➕ Create New Chat"] + [chat["name"] for chat in chat_histories]
        selected_chat = st.selectbox("Select a chat history:", chat_options, index=0)

        if selected_chat == "➕ Create New Chat":
            st.session_state["creating_chat"] = True  # Enable new chat creation
        else:
            st.session_state["creating_chat"] = False  # Reset if an existing chat is selected
            st.session_state["selected_chat"] = selected_chat
            st.success(f"Selected Chat: {selected_chat}")  # Show selected chat

        # Show new chat input box **only** if "Create New Chat" is selected
        if st.session_state.get("creating_chat", False):
            chat_name = st.text_input("Enter chat history name")
            if st.button("Save Chat"):
                if chat_name.strip():
                    save_chat_history(chat_name)
                    st.session_state["creating_chat"] = False  # Reset after saving
                    st.rerun()  # Refresh UI
                else:
                    st.error("Chat name cannot be empty.")


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

    if st.session_state["page"] == "home":
        homepage()
    elif st.session_state["page"] == "login":
        login()
    elif st.session_state["page"] == "signup":
        sign_up()


if __name__ == "__main__":
    main()
