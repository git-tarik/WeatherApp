import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# Load variables from .env
load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found in the .env file."
    )


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=GEMINI_API_KEY,
)