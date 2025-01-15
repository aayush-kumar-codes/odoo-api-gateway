from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.core.security import get_password_hash
from app.models.user import User

def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    
    # Create a test user
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit() 