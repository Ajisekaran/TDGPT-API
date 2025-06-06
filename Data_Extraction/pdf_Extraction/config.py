import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIRECTORY = r"C:\Users\atcha\TDGPT\Data_Collection"
SUBFOLDERS = ["PDF","Xlsx", "pptx", "Markdown"]

OUTPUT_DIRECTORY = os.path.join(os.getcwd(), "output")
IMAGE_OUTPUT_DIR = os.path.join(OUTPUT_DIRECTORY, "images")

os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError(" GROQ_API_KEY is not set in environment variables.")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

SAVE_IMAGES = True
CHUNK_SIZE = 500
