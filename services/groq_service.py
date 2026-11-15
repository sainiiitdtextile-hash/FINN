import os
import streamlit as st
from groq import Groq

def get_model():
    try:
        return st.secrets.get("GROQ_MODEL", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
    except Exception:
        return os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

def get_api_key():
    try:
        return st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    except Exception:
        return os.getenv("GROQ_API_KEY", "")

def ask_groq(system_prompt, user_prompt, temperature=0.2, max_tokens=1200):
    key = get_api_key()
    if not key:
        raise RuntimeError("Groq API key not configured. Add GROQ_API_KEY to .env or Streamlit secrets.")
    client = Groq(api_key=key)
    model = get_model()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
