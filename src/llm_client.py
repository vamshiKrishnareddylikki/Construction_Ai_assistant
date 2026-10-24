"""
Tool 3: Shared connection to the Gemini AI model.
Every AI tool in this project will use ask_llm() to talk to the model.
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads GEMINI_API_KEY and GEMINI_MODEL from the .env file

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
client = genai.Client()  # picks up GEMINI_API_KEY automatically


def ask_llm(prompt):
    """Send a prompt to Gemini and return its text answer."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


if __name__ == "__main__":
    question = (
        "You are an assistant for a South Florida construction company. "
        "In 3 short bullet points, what is an RFI in construction?"
    )
    print(ask_llm(question))