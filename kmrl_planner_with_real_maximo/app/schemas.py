from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TrainsetBase(BaseModel):
    code: str
    fitness_valid: bool
    mileage: float
    job_card_open: bool
    branding: Optional[str] = None
    needs_deep_clean: bool

    class Config:
        orm_mode = True

class Trainset(TrainsetBase):
    id: int

class PlanItem(BaseModel):
    trainset: str
    status: str
    reason: Optional[str]
    brand: Optional[str]
    mileage: float
    needs_deep_clean: bool

    class Config:
        orm_mode = True

class PlanBase(BaseModel):
    created_at: datetime
    service_count: int
    standby_count: int
    ibl_count: int

class Plan(PlanBase):
    id: int
    items: List[PlanItem] = []

class StatsResponse(BaseModel):
    service_count: int
    standby_count: int
    ibl_count: int
    mileage_distribution: dict

class PlanResponse(BaseModel):
    revenue: List[PlanItem]
    standby: List[PlanItem]
    ibl: List[PlanItem]
    alerts: List[str]
