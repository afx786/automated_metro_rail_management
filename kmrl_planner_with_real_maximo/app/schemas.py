from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class TrainsetBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    fitness_valid: bool
    mileage: float
    job_card_open: bool
    branding: Optional[str] = None
    needs_deep_clean: bool

class Trainset(TrainsetBase):
    id: int

class PlanItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    trainset: str
    status: str
    reason: Optional[str] = None
    brand: Optional[str] = None
    mileage: float = 0.0
    needs_deep_clean: bool = False
    # Maintenance fields (present on maintenance items)
    maintenance_priority: Optional[int] = None
    priority_level: Optional[str] = None
    urgency_score: Optional[int] = None
    maintenance_score: Optional[float] = None
    fitness_status: Optional[str] = None
    # Deep cleaning fields (present on assigned maintenance items)
    assigned_bay: Optional[str] = None
    assigned_team: Optional[str] = None
    estimated_time: Optional[int] = None
    manpower: Optional[int] = None
    complexity: Optional[str] = None
    estimated_completion: Optional[str] = None

class PlanBase(BaseModel):
    created_at: datetime
    service_count: int
    standby_count: int
    maintenance_count: int

class Plan(PlanBase):
    id: int
    items: List[PlanItem] = []

class StatsResponse(BaseModel):
    service_count: int
    standby_count: int
    maintenance_count: int
    mileage_distribution: dict

class PlanResponse(BaseModel):
    generated_at: str
    service: List[PlanItem]
    standby: List[PlanItem]
    maintenance: List[PlanItem]
    alerts: List[str]