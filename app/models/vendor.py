from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    street = Column(String)
    city = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    zip = Column(String)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    is_company = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    state = relationship("State", back_populates="vendors")
    country = relationship("Country", back_populates="vendors")
    products = relationship("Product", back_populates="vendor")
    categories = relationship("Category", back_populates="vendor") 