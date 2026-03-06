import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model=MODEL,
    contents="How is the weather in Bangalore Today?"
)

print(response.text)