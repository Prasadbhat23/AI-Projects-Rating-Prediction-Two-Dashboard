# user_dashboard.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# CSV storage
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "feedback.csv")
os.makedirs(DATA_DIR, exist_ok=True)

# Create CSV if missing
if not os.path.exists(CSV_PATH):
    df = pd.DataFrame(columns=[
        "timestamp","rating","review","ai_response","ai_summary","ai_actions"
    ])
    df.to_csv(CSV_PATH, index=False)

st.set_page_config(page_title="User Feedback Dashboard", layout="centered")

# LLM calls using new API
def call_llm_for_user_response(review, rating):
    if not OPENAI_API_KEY:
        return "Demo: (no API key) Thanks for your review!"
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user",
                   "content": f"You are a friendly support agent. Write a warm, short reply to this {rating}-star review: {review}"}],
        max_tokens=150,
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()

def call_llm_for_summary_and_actions(review):
    if not OPENAI_API_KEY:
        return "Demo summary (no API key)", "Demo actions (no API key)"

    summary_resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user",
                   "content": f"Summarize this review in 20 words: {review}"}],
        max_tokens=60
    )
    actions_resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user",
                   "content": f"Give 3 recommended actions based on this review: {review}"}],
        max_tokens=120
    )

    return summary_resp.choices[0].message.content.strip(), actions_resp.choices[0].message.content.strip()

def save_feedback(row):
    df = pd.read_csv(CSV_PATH)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)

# Streamlit UI
st.title("⭐ User Feedback Portal")

with st.form("feedback_form"):
    rating = st.slider("Star Rating", 1, 5, 5)
    review = st.text_area("Write your review:", height=120)
    submitted = st.form_submit_button("Submit")

if submitted:
    if not review.strip():
        st.error("Please enter a review.")
    else:
        st.info("Processing with AI...")
        try:
            ai_response = call_llm_for_user_response(review, rating)
            ai_summary, ai_actions = call_llm_for_summary_and_actions(review)
        except Exception as e:
            st.error(f"Error contacting OpenAI API: {e}")
            ai_response = "Demo: (error) Thanks for your review!"
            ai_summary, ai_actions = "Demo summary", "Demo actions"

        save_feedback({
            "timestamp": datetime.utcnow().isoformat(),
            "rating": rating,
            "review": review,
            "ai_response": ai_response,
            "ai_summary": ai_summary,
            "ai_actions": ai_actions
        })

        st.success("Thank you! Your feedback was submitted.")
        st.write("### 🤖 AI Response")
        st.write(ai_response)


