"""AutoLeadGen V3 — FastAPI Pydantic Schemas."""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


class LeadDetail(BaseModel):
    id: Optional[int] = None
    business_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    source: Optional[str] = None
    score: Optional[int] = None
    status: Optional[str] = None
    language: Optional[str] = None
    email: Optional[str] = None
    email_status: Optional[str] = None
    whatsapp_status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    data_confidence: Optional[str] = None

    model_config = {"extra": "allow"}


class LeadsPage(BaseModel):
    leads: List[Any]
    total: int
    page: int
    page_size: int


class PatchLeadRequest(BaseModel):
    business_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    email: Optional[str] = None
    email_status: Optional[str] = None
    notes: Optional[str] = None
    country: Optional[str] = None
    ai_summary: Optional[str] = None
    data_confidence: Optional[str] = None


class DiscoveryRequest(BaseModel):
    country: str
    city: Optional[str] = ""
    business_type: Optional[str] = "all"
    sources: Optional[List[str]] = ["overpass", "wikidata"]


class DashboardMetrics(BaseModel):
    total: int
    new: Optional[int] = 0
    qualified: Optional[int] = 0
    ready: Optional[int] = 0
    contacted: Optional[int] = 0
    replied: Optional[int] = 0
    interested: Optional[int] = 0
    not_interested: Optional[int] = 0
    wa_verified: Optional[int] = 0
    duplicates_merged: Optional[int] = 0
    avg_score: Optional[float] = 0.0

    model_config = {"extra": "allow"}


class GeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict]
    count: int


class TaskOut(BaseModel):
    id: str
    task_type: str
    status: str
    progress: float
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_log: Optional[str] = None
    cancel_requested: Optional[int] = 0
