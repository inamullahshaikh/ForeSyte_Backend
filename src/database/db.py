# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Read DB config from environment
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "fe118emaan2004")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "foresyte_db")

# Create SQLAlchemy database URL
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create engine (connection pool)
engine = create_engine(
    DATABASE_URL,
    echo=False,           # Set True to log SQL queries
    pool_size=10,         # Connection pool size
    max_overflow=5,       # Extra connections beyond pool_size
    pool_pre_ping=True,   # Test connections before use
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


