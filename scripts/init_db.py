from app.db.session import SessionLocal
from app.db.init_db import init_db

def main() -> None:
    db = SessionLocal()
    init_db(db)

if __name__ == "__main__":
    main()
    print("Database initialized and test user created") 