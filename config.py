import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")
PROJECT_PATH = Path(os.getenv("PROJECT_PATH", "test_project")).resolve()

if not NVIDIA_API_KEY:
    raise ValueError("NVIDIA_API_KEY is missing. Add it to your .env file.")
