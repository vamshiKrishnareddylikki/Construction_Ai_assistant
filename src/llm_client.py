"""
Shared connection to the AI model.
Every AI tool in this project uses ask_llm() or ask_llm_json().
The provider (Groq or Gemini) is chosen in the .env file, so we can switch
without changing any other code.
"""
import os
import json
import time
from dotenv import load_dotenv

load_dotenv(override=True)  # .env values win over anything already set in the terminal

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
RETRY_CODES = {429, 500, 502, 503, 504}  # rate limit, server errors, overloaded, timeout

if PROVIDER == "groq":
    from groq import Groq
    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    groq_client = Groq(timeout=120)  # picks up GROQ_API_KEY automatically
else:
    from google import genai
    from google.genai import types
    MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    gemini_client = genai.Client(http_options=types.HttpOptions(timeout=120_000))


def error_code(e):
    """Read the HTTP status code from either provider's error."""
    return getattr(e, "code", None) or getattr(e, "status_code", None)


def with_retry(call, attempts=5, wait=2):
    """Run an API call, retrying temporary failures with growing waits (2s, 4s, 8s...)."""
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as e:
            code = error_code(e)
            if code not in RETRY_CODES or attempt == attempts:
                raise
            print(f"  AI service busy (error {code}). Retry {attempt}/{attempts - 1} in {wait}s...")
            time.sleep(wait)
            wait *= 2


def _ask(prompt, json_mode):
    if PROVIDER == "groq":
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        response = with_retry(lambda: groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # low = more consistent, factual answers
            **kwargs,
        ))
        return response.choices[0].message.content

    config = types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None
    response = with_retry(lambda: gemini_client.models.generate_content(
        model=MODEL, contents=prompt, config=config))
    return response.text


def ask_llm(prompt):
    """Send a prompt and return the text answer."""
    return _ask(prompt, json_mode=False)


def ask_llm_json(prompt):
    """Send a prompt and get back structured data (a Python dict)."""
    return json.loads(_ask(prompt, json_mode=True))


if __name__ == "__main__":
    start = time.time()
    print(f"Provider: {PROVIDER} | Model: {MODEL}\n")
    print(ask_llm("In 3 short bullet points, what is an RFI in construction?"))
    print(f"\n(answered in {time.time() - start:.1f} seconds)")