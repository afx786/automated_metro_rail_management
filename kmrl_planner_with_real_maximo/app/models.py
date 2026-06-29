# models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Trainset(Base):
    __tablename__ = "trainsets"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    fitness_valid = Column(Boolean, default=True)
    job_card_open = Column(Boolean, default=False)
    branding = Column(String, nullable=True)
    mileage = Column(Float, default=0.0)
    needs_deep_clean = Column(Boolean, default=False)
    deep_clean_complexity = Column(String, default="medium")  # low, medium, high
    estimated_clean_time = Column(Integer, default=4)  # hours
    required_manpower = Column(Integer, default=2)  # people needed

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    params = Column(JSON, nullable=True)
    
    
    # Relationship to PlanItem
    items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")

class PlanItem(Base):
    __tablename__ = "plan_items"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    trainset_code = Column(String, index=True)
    status = Column(String)
    reason = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    mileage = Column(Float, default=0.0)
    needs_deep_clean = Column(Boolean, default=False)
    maintenance_priority = Column(Integer, nullable=True)
    priority_level = Column(String, nullable=True)
    urgency_score = Column(Integer, nullable=True)
    maintenance_score = Column(Float, nullable=True)
    fitness_status = Column(String, nullable=True)
    maintenance_priority = Column(Integer, nullable=True)
    priority_level = Column(String, nullable=True)
    urgency_score = Column(Integer, nullable=True)
    maintenance_score = Column(Float, nullable=True)
    fitness_status = Column(String, nullable=True)
    # New deep cleaning fields
    assigned_bay = Column(String, nullable=True)
    assigned_team = Column(String, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)
    plan = relationship("Plan", back_populates="items")
    
    # Relationship to Plan - MAKE SURE THIS IS CORRECT
    plan = relationship("Plan", back_populates="items")


class CleaningBay(Base):
    __tablename__ = "cleaning_bays"
    id = Column(Integer, primary_key=True, index=True)
    bay_number = Column(String, unique=True, index=True)
    capacity = Column(Integer, default=1)
    is_occupied = Column(Boolean, default=False)
    current_trainset = Column(String, nullable=True)
    available_manpower = Column(Integer, default=4)
    specialization = Column(String, default="interior")  # interior, exterior, general

class CleaningTeam(Base):
    __tablename__ = "cleaning_teams"
    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, unique=True, index=True)
    team_size = Column(Integer, default=4)
    current_assignment = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    specialization = Column(String, default="general")  # general, interior, exterior