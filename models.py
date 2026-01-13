from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    goals = relationship("Goal", back_populates="owner")
    subjects = relationship("Subject", back_populates="owner")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(String, primary_key=True)
    title = Column(String)
    type = Column(String) # MONTHLY, EXAM
    details = Column(JSON)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="goals")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(String, primary_key=True)
    goal_id = Column(String, ForeignKey("goals.id"))
    name = Column(String)
    color = Column(String)
    tracking_mode = Column(String, default="SCHEDULE")
    schedule = Column(JSON) # {days: [], time: '', duration: 0}
    
    total_study_hours = Column(Float, default=0.0)
    total_target_hours = Column(Float, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    name = Column(String)
    target_date = Column(String)
    target_time = Column(String, nullable=True)
    estimated_duration = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    
    subject = relationship("Subject", back_populates="chapters")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    subject_id = Column(String)
    subject_name = Column(String)
    type = Column(String)
    scheduled_hours = Column(Float)
    scheduled_time = Column(String)
    scheduled_date = Column(String)
    status = Column(String) # PENDING, COMPLETED, MISSED
    read = Column(Boolean, default=False)
    timestamp = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))
