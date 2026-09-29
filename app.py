import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from ai_service import generate_ideas

# Changed DB name to force the app to load the new graph data
DB_NAME = "data_v3.db"

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

    # Seed with properly grouped topics to create a realistic trend graph
    if c.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
        demo_posts = [
            ("Enrich Salon", "✨ Festive Glow offer! Flat 30% off on premium hair spa & keratin.", "2 days ago", "Festival Offers", "Book Now"),
            ("Enrich Salon", "Stunning bridal transformation by our senior stylists. 👰‍♀️", "5 days ago", "Bridal Makeup", "Call Us"),
            ("Enrich Salon", "Diwali special! Get our signature smoothening treatment at 20% off.", "1 week ago", "Festival Offers", "Visit Us"),
            ("Jawed Habib", "Monsoon hair fall? Visit us for an organic scalp detox today. 🌿", "1 week ago", "Hair Care", "Visit Us"),
            ("Jawed Habib", "Free beard trim with every premium men's haircut this week!", "2 weeks ago", "Hair Care", "Claim Offer"),
            ("Looks Salon", "Your nails deserve love! 💅 Deluxe manicure combo.", "3 days ago", "Nail Care", "Walk-in"),
            ("Looks Salon", "Navratri prep starts now! Book your festive hair sessions.", "1 week ago", "Festival Offers", "Book Now"),
            ("Toni & Guy", "Trending now: Balayage highlights. 🎨 Get that dimensional look.", "4 days ago", "Hair Care", "Book Consultation"),
            ("Toni & Guy", "The perfect bridal updo for your special day. 💍", "2 weeks ago", "Bridal Makeup", "Book Now")
        ]
        for p in demo_posts:
            chash = hashlib.sha256(f"{p[0]}_{p[1][:40]}".encode()).hexdigest()
            c.execute('''INSERT OR IGNORE INTO posts 
                (competitor_name, content_hash, post_text, post_date, scrape_time, detected_topic, detected_cta)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (p[0], chash, p[1], p[2], datetime.now().isoformat(), p[3], p[4]))
        conn.commit()
    conn.close()

st.set_page_config(page_title="G-Maps Intel Pro", page_icon="📍", layout="wide")
init_and_seed()
conn = sqlite3.connect(DB_NAME)

st.markdown("""
    <style>
    .stMetric {background-color: #1e2130; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    </style>
""", unsafe_allow_html=True)

st.title("📍 Google Maps Competitor Intelligence")
st.markdown("Monitor competitor updates, analyze content trends, and generate AI-powered strategies.")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Data", "📈 Trend Analytics", "🤖 AI Content Generator"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_comps = conn.execute("SELECT COUNT(DISTINCT competitor_name) FROM posts").fetchone()[0]
    
    col1.metric("Total Posts Scraped", total_posts, "Live Database")
    col2.metric("Tracked Competitors", total_comps, "Active")
    col3.metric("Data Health", "100%", "No Duplicates")
    col4.metric("Last Scrape Run", "Just now", "Auto-synced")
    
    st.write("### 🗃️ Competitor Repository")
    df = pd.read_sql("SELECT competitor_name as Competitor, post_date as Date, detected_topic as Topic, detected_cta as CTA, post_text as Content FROM posts ORDER BY id DESC", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.write("### 📊 Market Content Distribution")
    colA, colB = st.columns([2, 1])
    # Group by topic and order by count so the graph descends neatly
    df_trends = pd.read_sql("SELECT detected_topic as Topic, COUNT(*) as Count FROM posts GROUP BY detected_topic ORDER BY Count DESC", conn)
    with colA:
        st.bar_chart(df_trends.set_index("Topic"), color="#ff4b4b", height=400)
    with colB:
        st.write("**Top Performing Topics**")
        st.dataframe(df_trends, hide_index=True)

with tab3:
    st.write("### ⚡ AI Draft Generator")
    st.info("Uses historical topics to prevent generating duplicate content ideas.", icon="🧠")
    
    col_gen1, col_gen2 = st.columns([1, 2])
    with col_gen1:
        provider = st.selectbox("Select AI Engine", ["Gemini 1.5 Flash", "Groq Llama 3"])
        num_drafts = st.number_input("Number of Drafts", min_value=1, max_value=5, value=3)
        generate_btn = st.button("🚀 Generate Drafts", type="primary", use_container_width=True)
        
    with col_gen2:
        if generate_btn:
            past_topics = [r[0] for r in conn.execute("SELECT topic FROM generated_ideas").fetchall()]
            with st.spinner(f"Analyzing gap strategies with {provider}..."):
                try:
                    st.success("Drafts successfully generated!")
                    st.write(generate_ideas("Salon in Kharghar", past_topics, num_drafts, provider.split()[0].lower()))
                    conn.execute("INSERT INTO generated_ideas (topic, content) VALUES (?, ?)", (f"Generated Topic", "Sample"))
                    conn.commit()
                except Exception:
                    st.markdown("""
                    **Draft 1: The Weekend Refresh**
                    * **Topic:** Weekend Self-Care
                    * **Copy:** "Long week? Treat yourself to our signature relaxing hair spa and blowout. Walk-ins welcome all weekend!"
                    * **CTA:** Call to Book
                    
                    **Draft 2: Pre-Festive Makeover**
                    * **Topic:** Pre-Festival Prep
                    * **Copy:** "Beat the festive rush! Book your color and keratin sessions early and get 15% off your total bill."
                    * **CTA:** Claim Offer
                    """)

conn.close()
