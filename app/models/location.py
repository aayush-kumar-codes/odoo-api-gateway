from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, index=True)
    
    states = relationship("State", back_populates="country")
    users = relationship("User", back_populates="country")
    vendors = relationship("Vendor", back_populates="country")

class State(Base):
    __tablename__ = "states"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"))
    
    country = relationship("Country", back_populates="states")
    users = relationship("User", back_populates="state")
    vendors = relationship("Vendor", back_populates="state") 