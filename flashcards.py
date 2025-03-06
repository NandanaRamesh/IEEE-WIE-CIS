import streamlit as st


def generate_flashcards(model,text):
    """Generates flashcards using the Gemini API."""
    response = model.generate_content(f"Create flashcards for the following text. Provide only question and answer format with question on top and its corresponding aswer below, again next question and answer always keep question at the first:\n{text}")
    return response.text

flip_card_html = """
<style>
.flip-card-container {{
  display: flex;
  flex-wrap: wrap;
  justify-content: space-evenly;
  gap: 20px;
  margin-top: 20px;
}}

.flip-card {{
  background-color: transparent;
  margin: 5px;
  width: 300px;
  height: 200px;
  perspective: 1000px;
  border-radius: 10px;
  padding: 10px;
}}

.flip-card-inner {{
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 0.6s;
}}

.flip-card:hover .flip-card-inner {{
  transform: rotateY(180deg);
}}

.flip-card-front, .flip-card-back {{
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border-radius: 8px;
}}

.flip-card-front {{
  background-color: #f0f0f5;
  color: black;
}}

.flip-card-back {{
  background-color: #000000;
  color: white;
  transform: rotateY(180deg);
}}
</style>

<div class="flip-card-container">
  <div class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        {front_text}
      </div>
      <div class="flip-card-back">
        {back_text}
      </div>
    </div>
  </div>
</div>
"""

def show_flashcards(model,text):
    flashcards = generate_flashcards(model,text)

    flashcard_lines = flashcards.split('\n')
    for i in range(0, len(flashcard_lines), 2):
        card_front = flashcard_lines[i].strip() if i < len(flashcard_lines) else ""
        card_back = flashcard_lines[i + 1].strip() if i + 1 < len(flashcard_lines) else ""
        if card_front and card_back:
            front_text = card_front.split("**")[-1].strip()
            back_text = card_back.split("**")[-1].strip()
            card_html = flip_card_html.format(front_text=front_text, back_text=back_text)
            st.markdown(card_html, unsafe_allow_html=True)

if __name__ == "__main__":
    show_flashcards()
