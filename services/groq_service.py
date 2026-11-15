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
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        if status == 429:
            raise RuntimeError(
                "Groq rate limit or token quota reached. FINN is running, but Groq cannot "
                "accept more requests on the current quota yet. Wait for the quota window "
                "to reset, then retry. Avoid repeatedly clicking AI actions while limited."
            ) from exc
        if status == 401:
            raise RuntimeError("Groq rejected the API key (401). Check GROQ_API_KEY in Streamlit secrets.") from exc
        raise RuntimeError(f"Groq request failed{f' (HTTP {status})' if status else ''}: {exc}") from exc
