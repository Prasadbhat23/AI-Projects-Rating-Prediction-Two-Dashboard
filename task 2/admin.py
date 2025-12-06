# admin.py
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "feedback.csv")
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

# LOGOUT BUTTON
st.sidebar.title("Account")
if st.sidebar.button("🚪 Logout"):
    st.session_state.auth = False
    st.rerun()
# Load data
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.warning("No feedback data found.")
    st.stop()

df['timestamp'] = pd.to_datetime(df['timestamp'])

# --- Filters ---
st.sidebar.title("Filters")
rating_filter = st.sidebar.multiselect("Select Ratings", options=[1,2,3,4,5], default=[1,2,3,4,5])
start_date = st.sidebar.date_input("Start Date", df['timestamp'].min())
end_date = st.sidebar.date_input("End Date", df['timestamp'].max())
keyword = st.sidebar.text_input("Search Keyword", "")

filtered_df = df[
    (df['rating'].isin(rating_filter)) &
    (df['timestamp'].dt.date >= start_date) &
    (df['timestamp'].dt.date <= end_date) &
    (df['review'].str.contains(keyword, case=False, na=False))
]

# --- Metrics ---
st.title("📊 Admin Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", len(filtered_df))
col2.metric("Average Rating", round(filtered_df["rating"].mean(), 2) if not filtered_df.empty else 0)
col3.metric("5-Star Reviews", len(filtered_df[filtered_df["rating"] == 5]))

# --- Ratings Distribution ---
st.subheader("Ratings Distribution")
st.bar_chart(filtered_df['rating'].value_counts().sort_index(), width=700)

# --- Review Table with Expanders ---
st.subheader("Reviews")
if not filtered_df.empty:
    for i, row in filtered_df.sort_values("timestamp", ascending=False).iterrows():
        with st.expander(f"⭐ {row['rating']} | {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
            st.write(f"**Review:** {row['review']}")
            st.write(f"**AI Summary:** {row['ai_summary']}")
            st.write(f"**AI Actions:** {row['ai_actions']}")
else:
    st.info("No reviews match the current filters.")
