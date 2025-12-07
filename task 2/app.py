import streamlit as st
import pandas as pd
import os
from datetime import datetime
import openai
from dotenv import load_dotenv
import csv

load_dotenv()

# API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Admin password
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# CSV path
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "feedback.csv")
os.makedirs(DATA_DIR, exist_ok=True)

# Create CSV if missing
if not os.path.exists(CSV_PATH):
    df = pd.DataFrame(columns=[
        "timestamp", "rating", "review",
        "ai_response", "ai_summary", "ai_actions"
    ])
    df.to_csv(CSV_PATH, index=False, quoting=csv.QUOTE_ALL)

def read_data():
    try:
        return pd.read_csv(CSV_PATH, engine="python")
    except:
        return pd.DataFrame(columns=[
            "timestamp", "rating", "review",
            "ai_response", "ai_summary", "ai_actions"
        ])

def save_feedback(row):
    df = read_data()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(CSV_PATH, index=False, quoting=csv.QUOTE_ALL)


# ---------------------------------------------------------
# Streamlit Config
# ---------------------------------------------------------
st.set_page_config(page_title="Two Dashboard AI System")

# Initialize login session state
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False


# =========================================================
#                      SIDEBAR
# =========================================================
page = st.sidebar.selectbox("Select Page", ["User Dashboard", "Admin Login"])


# =========================================================
#                  USER DASHBOARD
# =========================================================
if page == "User Dashboard":
    st.title("⭐ User Feedback Portal")

    with st.form("feedback_form"):
        rating = st.slider("Star Rating", 1, 5, 5)
        review = st.text_area("Write your review:")
        submitted = st.form_submit_button("Submit Review")

    if submitted:
        if not review.strip():
            st.error("Please write something")
            st.stop()

        try:
            resp = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user",
                           "content": f"Write a warm reply to a {rating}-star review: {review}"}],
                max_tokens=150
            )
            ai_response = resp.choices[0].message.content

            summary = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Summarize in 20 words: {review}"}],
                max_tokens=60
            ).choices[0].message.content

            actions = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user",
                           "content": f"Give 3 actions for this review: {review}"}],
                max_tokens=100
            ).choices[0].message.content

        except Exception as e:
            st.error(f"AI Error: {e}")
            ai_response = "Demo response"
            summary = "Demo summary"
            actions = "Demo actions"

        save_feedback({
            "timestamp": datetime.utcnow().isoformat(),
            "rating": rating,
            "review": review,
            "ai_response": ai_response,
            "ai_summary": summary,
            "ai_actions": actions
        })

        st.success("Submitted successfully!")
        st.subheader("🤖 AI Response")
        st.write(ai_response)



# =========================================================
#                  ADMIN LOGIN PAGE
# =========================================================
elif page == "Admin Login":

    # Already logged in?
    if st.session_state.admin_logged_in:
        st.success("You are already logged in!")
        if st.button("Go to Admin Dashboard"):
            st.session_state.show_dashboard = True
            st.rerun()

    st.title("🔐 Admin Login")

    password = st.text_input("Enter Admin Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("Login successful!")
            st.session_state.show_dashboard = True
            st.rerun()
        else:
            st.error("Incorrect password")



# =========================================================
#                  ADMIN DASHBOARD PAGE
# =========================================================
if st.session_state.admin_logged_in and st.session_state.get("show_dashboard", False):

    st.title("📊 Admin Dashboard")

    # Logout button
    if st.button("Logout"):
        st.session_state.admin_logged_in = False
        st.session_state.show_dashboard = False
        st.rerun()

    df = read_data()

    if df.empty:
        st.warning("No feedback found yet.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        st.subheader("📌 Metrics Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Reviews", len(df))
        col2.metric("Average Rating", round(df["rating"].mean(), 2))
        col3.metric("5-Star Ratings", len(df[df["rating"] == 5]))

        st.subheader("Ratings Distribution")
        st.bar_chart(df["rating"].value_counts().sort_index())

        st.subheader("📝 All Reviews")
        for i, row in df.iterrows():
            with st.expander(f"⭐ {row['rating']} | {row['timestamp']}"):
                st.write(f"**Review:** {row['review']}")
                st.write(f"**AI Summary:** {row['ai_summary']}")
                st.write(f"**AI Actions:** {row['ai_actions']}")
