from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.models.base import Base  # noqa: F401

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    db = Session()
    try:
        yield db
    except Exception:
        db.rollback()    
        raise
    finally:
        db.close()