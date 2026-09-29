import os
import google.generativeai as genai
from groq import Groq

def generate_ideas(context, past_topics, count, provider="gemini"):
    prompt = f"Generate {count} Google Maps posts for a {context}. DO NOT use these past topics: {past_topics}. Return in JSON format containing 'topic', 'post_copy', and 'cta'."
    
    if provider == "gemini":
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)
        return res.text
    else:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return res.choices[0].message.content