# admin.py
import streamlit as st
import sqlite3
import pandas as pd
import os

# ------------------- Admin Password ------------------- #
PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# ------------------- Authentication ------------------- #
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Admin Login")
    pwd = st.text_input("Enter admin password", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ Wrong password")
    st.stop()

# Logout
st.sidebar.title("Account")
if st.sidebar.button("🚪 Logout"):
    st.session_state.auth = False
    st.rerun()

# ------------------- SQLite Setup ------------------- #
DB_PATH = os.path.join(os.path.dirname(__file__), "feedback.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# ✅ Create table if missing
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

# ------------------- Read Data ------------------- #
c.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
rows = c.fetchall()
df = pd.DataFrame(rows, columns=["timestamp", "rating", "review", "ai_response", "ai_summary", "ai_actions"])

if df.empty:
    st.info("No feedback entries found yet.")
    st.stop()

df['timestamp'] = pd.to_datetime(df['timestamp'])

# ------------------- Filters ------------------- #
st.sidebar.title("Filters")
rating_filter = st.sidebar.multiselect("Select Ratings", options=[1,2,3,4,5], default=[1,2,3,4,5])
keyword = st.sidebar.text_input("Search Keyword", "")

filtered_df = df[
    (df['rating'].isin(rating_filter)) &
    (df['review'].str.contains(keyword, case=False, na=False))
]

# ------------------- Metrics ------------------- #
st.title("📊 Admin Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", len(filtered_df))
col2.metric("Average Rating", round(filtered_df["rating"].mean(), 2))
col3.metric("5-Star Reviews", len(filtered_df[filtered_df["rating"]==5]))

# ------------------- Ratings Distribution ------------------- #
st.subheader("Ratings Distribution")
if not filtered_df.empty:
    st.bar_chart(filtered_df['rating'].value_counts().sort_index())
else:
    st.info("No data to display.")

# ------------------- Review Details ------------------- #
st.subheader("Reviews")
if not filtered_df.empty:
    for _, row in filtered_df.sort_values("timestamp", ascending=False).iterrows():
        with st.expander(f"⭐ {row['rating']} | {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
            st.write(f"**Review:** {row['review']}")
            st.write(f"**AI Response:** {row['ai_response']}")
            st.write(f"**AI Summary:** {row['ai_summary']}")
            st.write(f"**AI Actions:** {row['ai_actions']}")
else:
    st.info("No reviews match current filters.")
