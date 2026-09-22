import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "rapijob-dev-secret-key-change-in-production")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rapijob")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    DEFAULT_COMMISSION_PCT = float(os.getenv("DEFAULT_COMMISSION_PCT", 15.0))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
