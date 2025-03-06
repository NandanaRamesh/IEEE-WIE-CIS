import streamlit as st
from database import supabase_client as supabase
import time


def sign_up():
    st.markdown("### Sign Up")

    user_name = st.text_input("Enter your username")
    user_email = st.text_input("Enter your email")
    password = st.text_input("Enter your password", type="password")
    confirm_password = st.text_input("Confirm your password", type="password")

    if st.button("Sign Up", key="signup"):
        if not all([user_name, user_email, password, confirm_password]):
            st.error("Please fill in all fields.")
            return

        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        try:
            # ✅ **Check if the user already exists in Supabase Auth**
            existing_user = supabase.auth.sign_in_with_password({"email": user_email, "password": password})
            if existing_user.user:
                st.error("User already registered. Please log in.")
                return
        except Exception:
            pass  # If user doesn't exist, continue to sign up

        try:
            # ✅ **Create user with metadata (username) in Supabase Auth**
            response = supabase.auth.sign_up({
                "email": user_email,
                "password": password,
                "options": {"data": {"display_name": user_name}}  # Store username in user metadata
            })

            if response.user:
                st.success(f"Account created successfully, {user_name}! Please verify your email.")

                # ✅ **Redirect to login page**
                st.session_state["selected_page"] = "Signup/Login"
                time.sleep(5)
                st.rerun()
            else:
                st.error("Error: Unable to fetch user details from Supabase.")

        except Exception as e:
            st.error(f"Error: {e}")

    # ✅ **Login redirect button**
    if st.button("Already have an account? Login", key="login"):
        st.session_state["selected_page"] = "Signup/Login"
        st.rerun()
