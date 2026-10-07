import os
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 5}
    )
else:
    # Local PostgreSQL
    DB_USER = "postgres"
    DB_PASSWORD = os.getenv(
        "AIDE_DB_PASSWORD",
        "YOUR_POSTGRES_PASSWORD"
    )
    DB_HOST = "127.0.0.1"
    DB_PORT = 5432
    DB_NAME = "aide_db"

    LOCAL_DATABASE_URL = URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

    engine = create_engine(
        LOCAL_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 5}
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()