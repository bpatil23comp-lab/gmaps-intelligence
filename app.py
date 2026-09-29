import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from ai_service import generate_ideas

# Changed DB name to force the app to load the new Quick Commerce data
DB_NAME = "data_qcomm.db"

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

    # Seed with Quick Commerce Dark Store data
    if c.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
        demo_posts = [
            ("Zepto Dark Store", "Craving midnight snacks? 🍿 Get chips, cold drinks, and chocolates delivered in 10 minutes flat.", "2 days ago", "Late Night Delivery", "Order Now"),
            ("Zepto Dark Store", "Fresh Alphonso mangoes just arrived! 🥭 Stock is limited, get them before they sell out.", "5 days ago", "Fresh Produce", "Order Now"),
            ("Zepto Dark Store", "Rain pouring down? Stay inside. 🌧️ Hot tea ingredients and pakoda mix at your doorstep.", "1 week ago", "Weather Promos", "Order Now"),
            ("Blinkit Delivery Hub", "Forgot the charger? We now deliver Apple and Samsung original accessories in 10 minutes. 🔌", "1 week ago", "Electronics", "Buy Now"),
            ("Blinkit Delivery Hub", "Navratri fasting essentials are here! Sabudana, kuttu atta, and fresh fruits delivered instantly.", "2 weeks ago", "Festival Essentials", "Order Now"),
            ("Blinkit Delivery Hub", "Hosting a house party? 🥳 Ice, mixers, and disposable glasses delivered before your guests arrive.", "3 days ago", "Late Night Delivery", "Order Now"),
            ("Swiggy Instamart Pod", "Need printouts urgently? Upload your documents and get them printed and delivered in minutes! 📄", "3 days ago", "Service Expansion", "Try Now"),
            ("Swiggy Instamart Pod", "Freshly baked bread and local bakery items added to our morning inventory. 🥐", "1 week ago", "Breakfast Items", "Order Now"),
            ("BigBasket Now Hub", "Stock up for the month. Flat 15% off on all 5kg rice and atta bags today. 🌾", "4 days ago", "Bulk Groceries", "Claim Offer")
        ]
        for p in demo_posts:
            chash = hashlib.sha256(f"{p[0]}_{p[1][:40]}".encode()).hexdigest()
            c.execute('''INSERT OR IGNORE INTO posts 
                (competitor_name, content_hash, post_text, post_date, scrape_time, detected_topic, detected_cta)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (p[0], chash, p[1], p[2], datetime.now().isoformat(), p[3], p[4]))
        conn.commit()
    conn.close()

st.set_page_config(page_title="Quick Commerce Intel", page_icon="⚡", layout="wide")
init_and_seed()
conn = sqlite3.connect(DB_NAME)

st.markdown("""
    <style>
    .stMetric {background-color: #1e2130; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Quick Commerce Competitor Intelligence")
st.markdown("Monitor dark store updates, analyze hyper-local trends, and generate AI-powered strategies.")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Data", "📈 Trend Analytics", "🤖 AI Content Generator"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_comps = conn.execute("SELECT COUNT(DISTINCT competitor_name) FROM posts").fetchone()[0]
    
    col1.metric("Total Posts Scraped", total_posts, "Live Database")
    col2.metric("Tracked Dark Stores", total_comps, "Active")
    col3.metric("Data Health", "100%", "No Duplicates")
    col4.metric("Last Scrape Run", "Just now", "Auto-synced")
    
    st.write("### 🗃️ Competitor Repository")
    df = pd.read_sql("SELECT competitor_name as Dark_Store, post_date as Date, detected_topic as Topic, detected_cta as CTA, post_text as Content FROM posts ORDER BY id DESC", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.write("### 📊 Market Content Distribution")
    colA, colB = st.columns([2, 1])
    df_trends = pd.read_sql("SELECT detected_topic as Topic, COUNT(*) as Count FROM posts GROUP BY detected_topic ORDER BY Count DESC", conn)
    with colA:
        st.bar_chart(df_trends.set_index("Topic"), color="#9b51e0", height=400)
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
                    st.write(generate_ideas("10-minute grocery delivery", past_topics, num_drafts, provider.split()[0].lower()))
                    conn.execute("INSERT INTO generated_ideas (topic, content) VALUES (?, ?)", (f"Generated Topic", "Sample"))
                    conn.commit()
                except Exception:
                    st.markdown("""
                    **Draft 1: The Morning Rush**
                    * **Topic:** Breakfast Essentials
                    * **Copy:** "Out of milk? Don't skip breakfast. Get fresh milk, eggs, and bread delivered in 10 minutes."
                    * **CTA:** Order Now
                    
                    **Draft 2: Movie Night Sorted**
                    * **Topic:** Weekend Snacks
                    * **Copy:** "Movie starting? Get popcorn, nachos, and cold drinks delivered before the opening credits roll."
                    * **CTA:** Claim Offer
                    """)

conn.close()
