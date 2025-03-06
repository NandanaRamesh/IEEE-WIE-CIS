import streamlit as st
import google.generativeai as genai
import os

def initialize_session_state():
    """Initializes session state variables for the quiz."""
    if 'quiz' not in st.session_state:
        st.session_state.quiz = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'player_score' not in st.session_state:
        st.session_state.player_score = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'quiz_finished' not in st.session_state:
        st.session_state.quiz_finished = False

def generate_quiz(model, text, num_questions):
    """Generates a multiple-choice quiz from the provided text."""
    response = model.generate_content(
        f"Create a {num_questions}-question multiple-choice quiz based on the following text:\n"
        f"For each question, provide four options (A, B, C, D) and specify the correct answer.\n"
        f"Format:\n"
        f"Q: [question]\n"
        f"A) [option1]\n"
        f"B) [option2]\n"
        f"C) [option3]\n"
        f"D) [option4]\n"
        f"Correct: [correct option letter]\n\n"
        f"Text:\n{text}"
    )

    return extract_quiz_data(response.text)

def extract_quiz_data(quiz_text):
    """Parses and extracts structured quiz data from the Gemini response."""
    quiz_data = []
    questions = quiz_text.strip().split("\nQ: ")

    for q in questions:
        lines = q.strip().split("\n")
        if len(lines) >= 6:
            question = lines[0].replace("Q:", "").strip()
            options = [line.split(") ")[1].strip() for line in lines[1:5]]
            correct_answer = lines[5].split(": ")[1].strip()
            quiz_data.append({"question": question, "options": options, "correct_answer": correct_answer})
    
    return quiz_data

def display_question(question_idx):
    """Displays a single question and options."""
    question = st.session_state.quiz[question_idx]
    st.subheader(f"Q{question_idx + 1}: {question['question']}")
    selected_option = st.radio("Select your answer:", question['options'], key=f"question_{question_idx}")
    return selected_option

def show_quiz(model,text):
    """Main quiz app logic."""
    st.title("AI-Generated Multiple-Choice Quiz")

    initialize_session_state()

    num_questions = st.number_input("How many questions do you want?", min_value=1, max_value=10, value=5)

    if st.button("Generate Quiz"):
        if text and num_questions > 0:
            with st.spinner("Generating quiz..."):
                st.session_state.quiz = generate_quiz(model, text, num_questions)
                st.session_state.current_question = 0
                st.session_state.player_score = 0
                st.session_state.user_answers = [None] * num_questions
                st.session_state.quiz_finished = False
                st.rerun()
        else:
            st.error("Please enter valid text and select the number of questions.")

    if "quiz" in st.session_state and st.session_state.quiz:
        selected_option = display_question(st.session_state.current_question)
        
        if st.button("Save and Next"):
            correct_answer = st.session_state.quiz[st.session_state.current_question]['correct_answer']
            if selected_option == correct_answer:
                st.session_state.player_score += 1
            
            st.session_state.user_answers[st.session_state.current_question] = selected_option
            
            if st.session_state.current_question < len(st.session_state.quiz) - 1:
                st.session_state.current_question += 1
                st.rerun()
            else:
                st.session_state.quiz_finished = True

    if st.session_state.quiz_finished:
        st.subheader("Quiz Completed!")
        st.write(f"Your Score: **{st.session_state.player_score} / {len(st.session_state.quiz)}**")

        for i, question in enumerate(st.session_state.quiz):
            user_answer = st.session_state.user_answers[i]
            correct_answer = question['correct_answer']
            status = "✅ Correct" if user_answer == correct_answer else f"❌ Incorrect (Correct: {correct_answer})"
            st.write(f"Q{i+1}: {question['question']}")
            st.write(f"Your answer: {user_answer} - {status}")
            st.write("")

if __name__ == "__main__":
    show_quiz()
