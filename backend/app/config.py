from pathlib import Path
import os
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "voice_agent.db")))
