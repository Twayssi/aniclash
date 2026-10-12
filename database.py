from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError('Не обнаружена ссылка на базу данных в .env')

engine = create_engine(url=DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()