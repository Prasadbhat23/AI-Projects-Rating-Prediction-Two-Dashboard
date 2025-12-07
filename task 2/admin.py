import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# -------- CORRECT DEPLOYMENT-SAFE PATH -------- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "feedback.csv")

# ---------------------------------------------- #

PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Authentication
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Admin Login")

    pwd = st.text_input("Enter admin password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ Wrong password")

    st.stop()

# LOGOUT
st.sidebar.title("Account")
if st.sidebar.button("🚪 Logout"):
    st.session_state.auth = False
    st.rerun()

# -------- LOAD CSV SAFELY -------- #

if not os.path.exists(CSV_PATH):
    st.error("⚠️ No feedback data found. Please submit a review from user dashboard first.")
    st.stop()

try:
    df = pd.read_csv(CSV_PATH)
except Exception as e:
    st.error(f"Error reading feedback data: {e}")
    st.stop()

if df.empty:
    st.info("No feedback entries found yet.")
    st.stop()

df['timestamp'] = pd.to_datetime(df['timestamp'])

# -------- FILTERS -------- #

st.sidebar.title("Filters")
rating_filter = st.sidebar.multiselect(
    "Select Ratings", options=[1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5]
)
keyword = st.sidebar.text_input("Search Keyword", "")

filtered_df = df[
    (df['rating'].isin(rating_filter)) &
    (df['review'].str.contains(keyword, case=False, na=False))
]

# -------- METRICS -------- #

st.title("📊 Admin Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", len(filtered_df))
col2.metric("Average Rating", round(filtered_df["rating"].mean(), 2))
col3.metric("5-Star Reviews", len(filtered_df[filtered_df["rating"] == 5]))

# -------- CHART -------- #

st.subheader("Ratings Distribution")
if not filtered_df.empty:
    st.bar_chart(filtered_df['rating'].value_counts().sort_index())
else:
    st.info("No data to display.")

# -------- REVIEW DETAILS -------- #

st.subheader("Reviews")
if not filtered_df.empty:
    for _, row in filtered_df.sort_values("timestamp", ascending=False).iterrows():
        with st.expander(f"⭐ {row['rating']} | {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
            st.write(f"**Review:** {row['review']}")
            st.write(f"**AI Summary:** {row['ai_summary']}")
            st.write(f"**AI Actions:** {row['ai_actions']}")
else:
    st.info("No reviews match current filters.")
