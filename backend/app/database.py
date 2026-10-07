import os

from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base


# =========================================================
# AIDE DATABASE CONFIGURATION
# =========================================================

# IMPORTANT:
# Keep your existing PostgreSQL password here.
# Do NOT change it unless your PostgreSQL password has changed.

DB_USER = "postgres"

DB_PASSWORD = os.getenv(
    "AIDE_DB_PASSWORD",
    "kkk2410+"
)

DB_HOST = "127.0.0.1"
DB_PORT = 5432
DB_NAME = "aide_db"


# =========================================================
# DATABASE URL
# =========================================================
#
# URL.create() is used instead of manually constructing
# the connection string.
#
# This safely handles special characters in the password,
# including characters such as +, @, :, /, etc.
# =========================================================

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)


# =========================================================
# SQLALCHEMY ENGINE
# =========================================================

engine = create_engine(
    DATABASE_URL,

    echo=False,

    # Check that pooled connections are still alive.
    pool_pre_ping=True,

    # Recycle long-lived connections periodically.
    pool_recycle=1800,

    # Prevent an unavailable PostgreSQL server from
    # hanging the FastAPI request for a long time.
    connect_args={
        "connect_timeout": 5
    }
)


# =========================================================
# DATABASE SESSION
# =========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


# =========================================================
# BASE MODEL
# =========================================================

Base = declarative_base()


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()