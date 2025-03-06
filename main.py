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

        # Fetch last chat history ID and increment it (as an integer)
        response = supabase.table("Chat-History").select("id").order("id", desc=True).limit(1).execute()
        last_id = response.data[0]["id"] if response.data else 0  # Default to 0 if no data
        new_id = last_id + 1  # Increment the integer ID

        # Insert the new chat history into Supabase
        supabase.table("Chat-History").insert({
            "id": new_id,  # Store as integer
            "name": chat_name,
            "created_at": datetime.utcnow().isoformat(),
            "displayname": user_display_name
        }).execute()

        # Create user folder in the Supabase bucket
        bucket_name = "user-documents"
        user_folder = f"{user_display_name}/"
        supabase.storage.from_(bucket_name).upload(user_folder, "")

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

        # Check if user has existing chat history
        user_display_name = st.session_state["username"]
        response = supabase.table("Chat-History").select("*").eq("displayname", user_display_name).execute()

        if not response.data:
            st.warning("You have no chat history.")
            if st.button("Create Chat History"):
                create_chat_history()

        # Handle chat creation prompt
        if st.session_state.get("creating_chat"):
            chat_name = st.text_input("Enter chat history name")
            if st.button("Save Chat"):
                if chat_name.strip():
                    save_chat_history(chat_name)
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
