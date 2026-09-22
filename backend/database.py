from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from config import get_settings

settings = get_settings()

# Render may expose PostgreSQL URLs using the legacy postgres:// scheme.
# SQLAlchemy expects the explicit PostgreSQL scheme when selecting a driver.
database_url = settings.DATABASE_URL.strip()
if database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg2://" + database_url[len("postgres://"):]
elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg2://" + database_url[len("postgresql://"):]

# Crear motor de base de datos
if database_url.startswith("sqlite"):
    engine = create_engine(
        database_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        database_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_recycle=3600
    )

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db():
    """Dependencia para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
