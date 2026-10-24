"""
Tool 3: Shared connection to the Gemini AI model.
Every AI tool in this project will use ask_llm() to talk to the model.
"""
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()  # reads GEMINI_API_KEY and GEMINI_MODEL from the .env file

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
client = genai.Client()  # picks up GEMINI_API_KEY automatically

RETRY_CODES = {429, 500, 503}  # rate limit, server error, overloaded


def with_retry(call, attempts=5, wait=2):
    """Run an API call, retrying temporary failures with growing waits (2s, 4s, 8s...)."""
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except (errors.ServerError, errors.ClientError) as e:
            if e.code not in RETRY_CODES or attempt == attempts:
                raise
            print(f"  Gemini busy (error {e.code}). Retry {attempt}/{attempts - 1} in {wait}s...")
            time.sleep(wait)
            wait *= 2


def ask_llm(prompt):
    """Send a prompt to Gemini and return its text answer."""
    response = with_retry(
        lambda: client.models.generate_content(model=MODEL, contents=prompt)
    )
    return response.text


if __name__ == "__main__":
    question = (
        "You are an assistant for a South Florida construction company. "
        "In 3 short bullet points, what is an RFI in construction?"
    )
    print(ask_llm(question))