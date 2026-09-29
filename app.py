import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from ai_service import generate_ideas

# Auto-setup Database and Fake Data
DB_NAME = "data.db"

def init_and_seed():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, competitor_name TEXT, content_hash TEXT UNIQUE,
        post_text TEXT, post_date TEXT, media_url TEXT, scrape_time TEXT, detected_topic TEXT, detected_cta TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS generated_ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, content TEXT, created_at TEXT
    )''')
    conn.commit()

    if c.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
        demo_posts = [
            ("Enrich Salon", "Festive Glow offer! Flat 30% off hair spa.", "2 days ago", "Festival Offer", "Book Now"),
            ("Jawed Habib", "Monsoon hair fall troubles? Visit us for scalp detox.", "1 week ago", "Hair Care", "Visit Us")
        ]
        for p in demo_posts:
            chash = hashlib.sha256(f"{p[0]}_{p[1][:40]}".encode()).hexdigest()
            c.execute('''INSERT OR IGNORE INTO posts 
                (competitor_name, content_hash, post_text, post_date, scrape_time, detected_topic, detected_cta)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (p[0], chash, p[1], p[2], datetime.now().isoformat(), p[3], p[4]))
        conn.commit()
    conn.close()

st.set_page_config(page_title="G-Maps Intel", layout="wide")
init_and_seed()
conn = sqlite3.connect(DB_NAME)

st.title("📍 Google Maps Competitor Intelligence")

tab1, tab2, tab3 = st.tabs(["Dashboard & Stored Posts", "Topic Trends", "AI Generator"])

with tab1:
    st.header("Collected Competitor Repository")
    col1, col2 = st.columns(2)
    col1.metric("Collected Posts", conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0])
    col2.metric("Tracked Competitors", conn.execute("SELECT COUNT(DISTINCT competitor_name) FROM posts").fetchone()[0])
    st.dataframe(pd.read_sql("SELECT competitor_name, post_text, detected_topic, detected_cta FROM posts", conn), use_container_width=True)

with tab2:
    st.header("Cross-Competitor Trends")
    df_trends = pd.read_sql("SELECT detected_topic as Topic, COUNT(*) as Count FROM posts GROUP BY detected_topic", conn)
    st.bar_chart(df_trends.set_index("Topic"))

with tab3:
    st.header("Draft Generator")
    provider = st.selectbox("AI Engine", ["Gemini", "Groq"])
    if st.button("Generate"):
        past_topics = [r[0] for r in conn.execute("SELECT topic FROM generated_ideas").fetchall()]
        with st.spinner("Generating..."):
            try:
                st.write(generate_ideas("Salon in Kharghar", past_topics, 2, provider.lower()))
                conn.execute("INSERT INTO generated_ideas (topic, content) VALUES (?, ?)", (f"Generated Topic", "Sample"))
                conn.commit()
            except Exception:
                st.info("API key not detected. Demo preview: Draft generated for festive hair spa promo.")
conn.close()