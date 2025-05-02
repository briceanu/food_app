from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine



DB_URL= 'sqlite:///../database.db'

engine = create_engine(DB_URL,echo=True)
Session = sessionmaker(bind=engine,autocommit=False,autoflush=False)

def get_db():
    db_connection = Session()
    try:
        yield db_connection
    finally:
        db_connection.close()

