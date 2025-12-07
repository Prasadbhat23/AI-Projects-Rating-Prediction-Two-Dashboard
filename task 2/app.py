# user_dashboard.py
import streamlit as st
import sqlite3
from datetime import datetime
import openai
import pandas as pd
import os

# ------------------- Load OpenAI API ------------------- #
if "openai" in st.secrets:
    openai.api_key = st.secrets["openai"]["api_key"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    import os
    openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------- SQLite Setup ------------------- #
DB_PATH = os.path.join(os.path.dirname(__file__), "feedback.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    timestamp TEXT,
    rating INTEGER,
    review TEXT,
    ai_response TEXT,
    ai_summary TEXT,
    ai_actions TEXT
)
''')
conn.commit()

# ------------------- Helper Functions ------------------- #
def save_feedback(rating, review, ai_response, ai_summary, ai_actions):
    c.execute('''
        INSERT INTO feedback (timestamp, rating, review, ai_response, ai_summary, ai_actions)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.utcnow().isoformat(), rating, review, ai_response, ai_summary, ai_actions))
    conn.commit()

def read_feedback():
    c.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=["timestamp", "rating", "review", "ai_response", "ai_summary", "ai_actions"])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# ------------------- AI Functions ------------------- #
def call_llm_for_user_response(review, rating):
    if not openai.api_key:
        return "Demo: (no API key) Thanks for your review!"
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"You are a friendly support agent. Write a warm short reply to this {rating}-star review: {review}"
        }],
        max_tokens=150,
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()

def call_llm_for_summary_and_actions(review):
    if not openai.api_key:
        return "Demo summary", "Demo actions"
    summary_resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Summarize this review in 20 words: {review}"}],
        max_tokens=60
    )
    actions_resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Give 3 recommended actions based on this review: {review}"}],
        max_tokens=120
    )
    return summary_resp.choices[0].message.content.strip(), actions_resp.choices[0].message.content.strip()

# ------------------- Streamlit UI ------------------- #
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

        save_feedback(rating, review, ai_response, ai_summary, ai_actions)
        st.success("✅ Your feedback was submitted successfully!")
        st.write("### 🤖 AI Response")
        st.write(ai_response)
