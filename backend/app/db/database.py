"""
Database engine and session factory — SQLAlchemy 2.x.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_timeout=10,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Session:
    """
    Dependency generator for FastAPI (and standalone scripts).

    Usage in FastAPI:
        @app.get("/...")
        def endpoint(db: Session = Depends(get_db)):
            ...

    Usage in scripts:
        with get_db() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
