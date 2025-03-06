import streamlit as st

# Function to communicate with Gemini API
def chat_with_gemini(question, chat_history, model):
    """Handles chat conversation with Gemini API."""
    chat = model.start_chat(history=chat_history)
    response = chat.send_message(question)
    return response.text, chat.history

# Function to format chat history for Gemini API
def adjust_history_for_gemini(history):
    """Adjusts chat history for Gemini API."""
    return [{"role": message["role"], "parts": [message["content"]]} for message in history]

# Standalone chatbot function
def chatbot_interface(model):
    """Streamlit-based chatbot interface using Gemini API."""
    st.markdown("## 🤖 Doubt Clearance Chatbot")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages in a scrollable container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Fixed input bar at the bottom
    user_input = st.chat_input("Ask a question...")
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Save user's message to session state
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate response using Gemini API
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                # Format history and call API
                formatted_history = adjust_history_for_gemini(st.session_state.messages)
                response_text, chat_history = chat_with_gemini(user_input, formatted_history, model)

                # Display response dynamically
                full_response = response_text
                message_placeholder.markdown(full_response)

                # Save assistant's response to session state
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error in communication with Gemini API: {e}")
