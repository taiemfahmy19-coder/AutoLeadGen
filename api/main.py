"""AutoLeadGen V3 — FastAPI REST + WebSocket Server.

Runs alongside Streamlit on port 8502.
Provides JWT-secured endpoints for the Android app and external clients.

Usage:
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8502 --reload
Or via Start_V3_API.bat
"""
import json
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core.security import verify_access_token, has_permission
from core.user_manager import UserManager
from core.task_manager import task_manager
from integrations.multi_source_discovery import run_discovery
from database.repository import LeadRepository
from api.schemas import (
    LoginResponse, LeadsPage, LeadDetail, TaskOut,
    DiscoveryRequest, PatchLeadRequest, DashboardMetrics,
    GeoJSONResponse,
)
from api.websocket_manager import ws_manager

app = FastAPI(
    title="AutoLeadGen V3 API",
    version="3.0.0",
    description="Global AI Business Discovery & Email Intelligence Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Auth Dependency ─────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload


def require_permission(perm: str):
    def _dep(user: dict = Depends(get_current_user)):
        if not has_permission(user.get("role", ""), perm):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission '{perm}' required")
        return user
    return _dep


# ── Auth Endpoints ──────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=LoginResponse, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    repo = LeadRepository()
    try:
        mgr = UserManager(repo=repo)
        auth = mgr.authenticate_user(form_data.username, form_data.password)
        if not auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        return {
            "access_token": auth["access_token"],
            "token_type": "bearer",
            "username": auth["username"],
            "role": auth["role"],
        }
    finally:
        repo.close()


# ── Leads Endpoints ─────────────────────────────────────────────────────────

@app.get("/api/leads", response_model=LeadsPage, tags=["leads"])
def list_leads(
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    industry: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    _user=Depends(require_permission("leads:read")),
):
    repo = LeadRepository()
    try:
        filters = {}
        if status: filters["status"] = status
        if country: filters["country"] = country
        if city: filters["city"] = city
        if industry: filters["industry"] = industry
        if min_score is not None: filters["min_score"] = min_score
        if search: filters["search"] = search
        rows, total = repo.get_leads_paginated(page=page, page_size=page_size, filters=filters)
        return {"leads": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        repo.close()


@app.get("/api/leads/geojson", tags=["leads"])
def leads_geojson(
    min_lat: float = -90, max_lat: float = 90,
    min_lon: float = -180, max_lon: float = 180,
    limit: int = 5000,
    industry: Optional[str] = None,
    min_score: Optional[int] = None,
    _user=Depends(require_permission("leads:read")),
):
    repo = LeadRepository()
    try:
        filters = {}
        if industry: filters["industry"] = industry
        if min_score is not None: filters["min_score"] = min_score
        rows = repo.get_leads_in_bbox(min_lat, max_lat, min_lon, max_lon, limit=limit, filters=filters)
        features = []
        for r in rows:
            lat = r.get("latitude")
            lon = r.get("longitude")
            if lat is None or lon is None:
                continue
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "id": r.get("id"),
                    "name": r.get("business_name"),
                    "phone": r.get("phone", ""),
                    "industry": r.get("industry", ""),
                    "city": r.get("city", ""),
                    "country": r.get("country", ""),
                    "score": r.get("score", 0),
                    "status": r.get("status", ""),
                    "email": r.get("email", ""),
                    "website": r.get("website", ""),
                },
            })
        return {"type": "FeatureCollection", "features": features, "count": len(features)}
    finally:
        repo.close()


@app.get("/api/leads/{lead_id}", response_model=LeadDetail, tags=["leads"])
def get_lead(lead_id: int, _user=Depends(require_permission("leads:read"))):
    repo = LeadRepository()
    try:
        row = repo.get_lead_by_id(lead_id)
        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")
        if isinstance(row, dict):
            return row
        col_names = [
            "id", "business_name", "phone", "address", "website", "industry", "city",
            "source", "score", "status", "language", "created_at", "updated_at",
            "whatsapp_status", "phone_validity", "email", "email_status",
            "instagram_handle", "facebook_url",
        ]
        return dict(zip(col_names, row))
    finally:
        repo.close()


@app.patch("/api/leads/{lead_id}", tags=["leads"])
def update_lead(lead_id: int, body: PatchLeadRequest, _user=Depends(require_permission("leads:write"))):
    repo = LeadRepository()
    try:
        fields = {k: v for k, v in body.model_dump(exclude_none=True).items()}
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        repo.update_lead_fields(lead_id, **fields)
        return {"ok": True}
    finally:
        repo.close()


@app.delete("/api/leads/{lead_id}", tags=["leads"])
def delete_lead(lead_id: int, _user=Depends(require_permission("leads:delete"))):
    repo = LeadRepository()
    try:
        repo.delete_lead(lead_id)
        return {"ok": True}
    finally:
        repo.close()


# ── Metrics ─────────────────────────────────────────────────────────────────

@app.get("/api/metrics/dashboard", response_model=DashboardMetrics, tags=["metrics"])
def dashboard_metrics(_user=Depends(require_permission("leads:read"))):
    repo = LeadRepository()
    try:
        return repo.get_dashboard_metrics()
    finally:
        repo.close()


# ── Discovery ────────────────────────────────────────────────────────────────

@app.post("/api/discovery/start", tags=["discovery"])
def start_discovery(body: DiscoveryRequest, _user=Depends(require_permission("discovery:run"))):
    task_id = task_manager.submit_task(
        func=run_discovery,
        params={
            "country": body.country,
            "city": body.city or "",
            "business_type": body.business_type or "all",
            "sources": body.sources or ["overpass", "wikidata"],
        },
        task_type="discovery",
    )
    return {"task_id": task_id, "status": "started"}


# ── Tasks ────────────────────────────────────────────────────────────────────

@app.get("/api/tasks", tags=["tasks"])
def list_tasks(limit: int = 50, _user=Depends(require_permission("tasks:manage"))):
    return task_manager.list_tasks(limit=limit)


@app.get("/api/tasks/{task_id}", tags=["tasks"])
def get_task(task_id: str, _user=Depends(require_permission("tasks:manage"))):
    t = task_manager.get_status(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t


@app.post("/api/tasks/{task_id}/cancel", tags=["tasks"])
def cancel_task(task_id: str, _user=Depends(require_permission("tasks:manage"))):
    ok = task_manager.cancel_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


# ── Email inbox ──────────────────────────────────────────────────────────────

@app.get("/api/email/inbox", tags=["email"])
def email_inbox(lead_id: Optional[int] = None, limit: int = 50, _user=Depends(require_permission("leads:read"))):
    repo = LeadRepository()
    try:
        return repo.get_email_messages(lead_id=lead_id, limit=limit)
    finally:
        repo.close()


# ── Notifications ────────────────────────────────────────────────────────────

@app.get("/api/notifications", tags=["notifications"])
def notifications(unread_only: bool = False, _user=Depends(require_permission("leads:read"))):
    repo = LeadRepository()
    try:
        return repo.get_notifications(unread_only=unread_only)
    finally:
        repo.close()


@app.post("/api/notifications/{nid}/read", tags=["notifications"])
def mark_read(nid: int, _user=Depends(require_permission("leads:read"))):
    repo = LeadRepository()
    try:
        repo.mark_notification_read(nid)
        return {"ok": True}
    finally:
        repo.close()


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket, token: str = ""):
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive; client may ping
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# Wire broadcaster into task_manager
task_manager.set_broadcaster(
    lambda evt, data: __import__("asyncio").ensure_future(ws_manager.broadcast(evt, data))
)
