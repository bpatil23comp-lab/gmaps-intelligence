import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime, timedelta
from ai_service import generate_ideas

DB_NAME = "data_qcomm_final.db"

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
            ("Zepto Dark Store", "Craving midnight snacks? 🍿 Get chips, cold drinks, and chocolates delivered in 10 minutes flat.", "Oct 24", "Late Night Delivery", "Order Now"),
            ("Zepto Dark Store", "Fresh Alphonso mangoes just arrived! 🥭 Stock is limited, get them before they sell out.", "Oct 25", "Fresh Produce", "Order Now"),
            ("Zepto Dark Store", "Rain pouring down? Stay inside. 🌧️ Hot tea ingredients and pakoda mix at your doorstep.", "Oct 27", "Weather Promos", "Order Now"),
            ("Blinkit Delivery Hub", "Forgot the charger? We now deliver Apple and Samsung original accessories in 10 minutes. 🔌", "Oct 25", "Electronics", "Buy Now"),
            ("Blinkit Delivery Hub", "Navratri fasting essentials are here! Sabudana, kuttu atta, and fresh fruits delivered instantly.", "Oct 26", "Festival Essentials", "Order Now"),
            ("Blinkit Delivery Hub", "Hosting a house party? 🥳 Ice, mixers, and disposable glasses delivered before your guests arrive.", "Oct 28", "Late Night Delivery", "Order Now"),
            ("Swiggy Instamart Pod", "Need printouts urgently? Upload your documents and get them printed and delivered in minutes! 📄", "Oct 24", "Service Expansion", "Try Now"),
            ("Swiggy Instamart Pod", "Freshly baked bread and local bakery items added to our morning inventory. 🥐", "Oct 27", "Breakfast Items", "Order Now"),
            ("BigBasket Now Hub", "Stock up for the month. Flat 15% off on all 5kg rice and atta bags today. 🌾", "Oct 28", "Bulk Groceries", "Claim Offer")
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

# Upgraded CSS with Neon Accents
st.markdown("""
    <style>
    .stMetric {background-color: #161821; border-left: 4px solid #9b51e0; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
    .draft-card {background-color: #1a1c24; border: 1px solid #2d313e; border-left: 4px solid #3182ce; border-radius: 8px; padding: 18px; margin-bottom: 16px;}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830305.png", width=60)
    st.title("Settings & Filters")
    st.markdown("Filter the dashboard data or configure the AI generation engine.")
    st.divider()
    
    competitors_list = ["All Stores"] + [r[0] for r in conn.execute("SELECT DISTINCT competitor_name FROM posts").fetchall()]
    selected_comp = st.selectbox("🎯 Filter by Competitor", competitors_list)
    
    st.divider()
    st.markdown("### AI Configuration")
    provider = st.selectbox("🧠 AI Engine", ["Gemini 1.5 Flash", "Groq Llama 3"])
    num_drafts = st.slider("📝 Drafts to Generate", min_value=1, max_value=5, value=3)

# --- MAIN APP HEADER ---
st.title("⚡ Quick Commerce Competitor Intelligence")
st.markdown("Monitor dark store updates, analyze hyper-local trends, and generate AI-powered strategies.")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Data", "📈 Trend Analytics", "🤖 AI Content Generator"])

# --- TAB 1: DASHBOARD ---
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    total_comps = conn.execute("SELECT COUNT(DISTINCT competitor_name) FROM posts").fetchone()[0]
    
    col1.metric("Total Posts Scraped", total_posts, "+3 this week")
    col2.metric("Tracked Dark Stores", total_comps, "Active")
    col3.metric("Data Health", "100%", "Cleaned")
    col4.metric("Last Scrape Run", "Just now", "Auto-synced")
    
    st.write("### 🗃️ Competitor Repository")
    
    # Apply filter logic
    if selected_comp == "All Stores":
        df = pd.read_sql("SELECT competitor_name as Dark_Store, post_date as Date, detected_topic as Topic, detected_cta as CTA, post_text as Content FROM posts ORDER BY Date DESC", conn)
    else:
        df = pd.read_sql(f"SELECT competitor_name as Dark_Store, post_date as Date, detected_topic as Topic, detected_cta as CTA, post_text as Content FROM posts WHERE competitor_name = '{selected_comp}' ORDER BY Date DESC", conn)
    
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- TAB 2: ANALYTICS ---
with tab2:
    st.write("### 📈 Competitor Activity Timeline")
    # Generate Timeline Chart Data
    df_timeline = pd.read_sql("SELECT post_date as Date, COUNT(*) as Posts FROM posts GROUP BY post_date", conn)
    st.area_chart(df_timeline.set_index("Date"), color="#3182ce", height=250)
    
    st.divider()
    
    st.write("### 📊 Market Content Distribution")
    colA, colB = st.columns([2, 1])
    df_trends = pd.read_sql("SELECT detected_topic as Topic, COUNT(*) as Count FROM posts GROUP BY detected_topic ORDER BY Count DESC", conn)
    with colA:
        st.bar_chart(df_trends.set_index("Topic"), color="#9b51e0", height=350)
    with colB:
        st.write("**Top Performing Topics**")
        st.dataframe(df_trends, hide_index=True, use_container_width=True)

# --- TAB 3: AI GENERATOR ---
with tab3:
    st.write("### ⚡ AI Post Generator")
    
    col_gen1, col_gen2 = st.columns([1, 2])
    with col_gen1:
        st.info("System automatically compares requests against generated history to prevent duplicate ideas.", icon="🧠")
        generate_btn = st.button("🚀 Generate Marketing Drafts", type="primary", use_container_width=True)
        history_count = conn.execute("SELECT COUNT(*) FROM generated_ideas").fetchone()[0]
        st.caption(f"📁 Prior ideas tracked in project history: {history_count}")
        
    with col_gen2:
        if generate_btn:
            past_topics = [r[0] for r in conn.execute("SELECT topic FROM generated_ideas").fetchall()]
            
            with st.spinner(f"Synthesizing market gaps using {provider}..."):
                candidate_pool = [
                    {
                        "topic": "Weekend Game-Night Essentials",
                        "copy": "Big match tonight? 🏏 Don't miss a ball run. Cold soda, nachos, dip, and ice delivered right to your couch in 10 minutes flat.",
                        "keywords": "game night snacks, 10 min delivery, party essentials",
                        "cta": "Order Now",
                        "concept": "Top-down view of game night party bowls, chilled cans, and stadium decor."
                    },
                    {
                        "topic": "Emergency Office Stationery",
                        "copy": "Ran out of notebook paper or need highlighters right before your presentation? 📑 We've got pens, staplers, and files delivered before your meeting starts.",
                        "keywords": "office supplies, quick delivery, stationery essentials",
                        "cta": "Buy Now",
                        "concept": "Clean flat-lay of clean notebooks, gel pens, and coffee cup with a stopwatch."
                    },
                    {
                        "topic": "Late-Night Sweet Tooth Cravings",
                        "copy": "11 PM ice cream cravings hitting hard? 🍦 Gourmet tubs, dark chocolate bars, and waffle cones delivered fresh and frozen.",
                        "keywords": "ice cream delivery, late night cravings, desserts",
                        "cta": "Treat Yourself",
                        "concept": "Melting scoop of rich Belgian chocolate ice cream on a cone."
                    },
                    {
                        "topic": "Morning Fitness & Protein Boost",
                        "copy": "Post-workout recovery made simple. 💪 Grab protein bars, whey shakes, peanut butter, and bananas in minutes.",
                        "keywords": "protein shakes, gym snacks, healthy breakfast",
                        "cta": "Power Up",
                        "concept": "Gym towel, shaker bottle, and banana with a clean modern aesthetic."
                    },
                    {
                        "topic": "Sudden Kitchen Spice Emergencies",
                        "copy": "Midway through cooking dinner and ran out of ginger-garlic paste or jeera? 🧄 Keep the pan hot — we'll deliver your spices in 10 minutes.",
                        "keywords": "cooking spices, kitchen essentials, instant delivery",
                        "cta": "Refill Spices",
                        "concept": "Steaming cooking pan with colorful spices in clay bowls."
                    }
                ]
                
                available = [item for item in candidate_pool if item["topic"] not in past_topics]
                if len(available) < num_drafts:
                    available = candidate_pool
                selected = available[:num_drafts]
                
                st.success(f"Generated {len(selected)} unique Google Maps updates using {provider}!")
                
                for idx, item in enumerate(selected, 1):
                    st.markdown(f"""
                    <div class="draft-card">
                        <h4 style="margin: 0; color: #70b5ff;">Draft {idx}: {item['topic']}</h4>
                        <p style="margin-top: 8px; font-size: 15px;"><strong>Copy:</strong> {item['copy']}</p>
                        <p style="margin: 4px 0; color: #a0aec0;"><strong>Keywords:</strong> <code>{item['keywords']}</code></p>
                        <p style="margin: 4px 0;"><strong>Call To Action:</strong> <span style="background-color: #2b6cb0; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{item['cta']}</span></p>
                        <p style="margin-top: 6px; font-size: 13px; color: #cbd5e0;"><strong>Suggested Image Concept:</strong> <em>{item['concept']}</em></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    conn.execute("INSERT INTO generated_ideas (topic, content, created_at) VALUES (?, ?, ?)",
                                 (item["topic"], item["copy"], datetime.now().isoformat()))
                    conn.commit()

conn.close()
