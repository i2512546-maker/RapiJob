import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "rapijob-dev-secret-key-change-in-production")

    # --- MySQL (Alwaysdata) -------------------------------------------------
    # El host de Alwaysdata tiene la forma: mysql-USUARIO.alwaysdata.net
    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "")

    # Fallback local sin MySQL: usa SQLite (rapijob.db) con el MISMO esquema.
    # En Alwaysdata, al definir DB_HOST, se usa MySQL automáticamente.
    SQLITE_PATH = os.getenv("SQLITE_PATH", "rapijob.db")

    # Si no hay DB_HOST configurado, se usa SQLite para desarrollo local.
    @staticmethod
    def is_mysql_configured() -> bool:
        return bool(Config.DB_HOST and Config.DB_USER and Config.DB_NAME)

    # --- Aplicación ---------------------------------------------------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
