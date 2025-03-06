import streamlit as st
from database import supabase_client as supabase

def get_user_metadata():
    """Fetch user metadata synchronously."""
    try:
        session = supabase.auth.get_user()  # No need for await
        if session and session.user:
            return session.user.user_metadata
        return None
    except Exception:
        return None

def login():
    st.title("Login")

    user_email = st.text_input("Enter your email")
    password = st.text_input("Enter your password", type="password")

    if st.button("Login", key="login_button"):
        if user_email and password:
            try:
                response = supabase.auth.sign_in_with_password(
                    {"email": user_email, "password": password}
                )

                if response.user:
                    st.write("Login Response User Object:", response.user)

                    # Get metadata from login response
                    user_metadata = response.user.user_metadata
                    username = user_metadata.get("display_name", "User")

                    # Fetch latest session metadata synchronously
                    session_metadata = get_user_metadata()
                    session_username = session_metadata.get("display_name", "User") if session_metadata else "User"

                    # Store in session state
                    st.session_state["user_logged_in"] = True
                    st.session_state["user_email"] = response.user.email
                    st.session_state["username"] = username  # From login response
                    st.session_state["session_username"] = session_username  # From session retrieval

                    st.success(f"Welcome back, {username}!")
                    st.session_state["page"] = "home"
                    st.rerun()
                    if "user_logged_in" in st.session_state and st.session_state["user_logged_in"]:
                        if "session_username" not in st.session_state:
                            session_metadata = get_user_metadata()
                            st.session_state["session_username"] = session_metadata.get("display_name",
                                                                                        "User") if session_metadata else "User"

                else:
                    st.error("Invalid credentials. Please try again.")
            except Exception as e:
                st.error(f"Login failed: {e}")
        else:
            st.error("Please fill in both fields.")

    if st.button("Don't have an account? Sign Up", key="signup_redirect"):
        st.session_state["page"] = "signup"
        st.rerun()  # Ensure rerun happens after setting the session state
