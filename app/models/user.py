from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone = Column(String)
    street = Column(String)
    city = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    zip = Column(String)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    is_company = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    state = relationship("State", back_populates="users")
    country = relationship("Country", back_populates="users")
    orders = relationship("Order", back_populates="user")
    basket = relationship("Basket", back_populates="user", uselist=False) 