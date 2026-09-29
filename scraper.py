from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import sqlite3
import hashlib
from datetime import datetime
import time

def scrape_gmaps_profiles():
    print("Initializing Selenium WebDriver...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    # Initialize driver
    driver = webdriver.Chrome(options=options)
    
    # Target Google Maps query
    test_urls = ["https://www.google.com/maps/search/quick+commerce+dark+stores+mumbai/"]
    
    conn = sqlite3.connect("data_qcomm_final.db")
    c = conn.cursor()
    
    try:
        for url in test_urls:
            driver.get(url)
            time.sleep(5)  # Allow dynamic content to load
            
            # Conceptual selectors for Google Maps update posts
            posts = driver.find_elements(By.CSS_SELECTOR, ".update-post-container")
            
            for post in posts:
                try:
                    store_name = driver.find_element(By.CSS_SELECTOR, "h1").text
                    content = post.find_element(By.CSS_SELECTOR, ".post-text").text
                    date_posted = post.find_element(By.CSS_SELECTOR, ".post-date").text
                    
                    # Prevent duplicates using SHA-256 hash
                    content_hash = hashlib.sha256(f"{store_name}_{content[:40]}".encode()).hexdigest()
                    
                    c.execute('''INSERT OR IGNORE INTO posts 
                        (competitor_name, content_hash, post_text, post_date, scrape_time, detected_topic, detected_cta)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                        (store_name, content_hash, content, date_posted, datetime.now().isoformat(), "Pending Analysis", "Pending CTA"))
                        
                except Exception as e:
                    continue
                    
        conn.commit()
        print("Scraping completed. Local database updated.")
        
    finally:
        conn.close()
        driver.quit()

if __name__ == "__main__":
    scrape_gmaps_profiles()