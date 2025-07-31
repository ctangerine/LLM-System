from typing import Optional, Generator
from sqlmodel import SQLModel, Field, create_engine, Session

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, echo=True)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password: str  

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized and table User is ready in app.db")
