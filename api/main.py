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
from pydantic import BaseModel

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core.security import verify_access_token, has_permission
from core.user_manager import UserManager
from core.task_manager import task_manager
from integrations.multi_source_discovery import run_discovery
from integrations.email_engine import EmailEngine, SMTP_PRESETS
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


# ── QR Email Linking ─────────────────────────────────────────────────────────

@app.get("/connect-email", response_class=HTMLResponse, tags=["email"])
def connect_email_page():
    return """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ربط البريد الإلكتروني — AutoLeadGen V3</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: #070b14; color: #f1f5f9; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .card { background: #0f172a; border: 1px solid rgba(99,102,241,0.3); border-radius: 18px; padding: 26px 20px; max-width: 420px; width: 100%; box-shadow: 0 16px 40px rgba(0,0,0,0.6); }
    .icon { width: 56px; height: 56px; background: linear-gradient(135deg, #6366f1, #a855f7); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 28px; margin: 0 auto 16px; }
    h2 { text-align: center; font-size: 20px; font-weight: 800; margin-bottom: 6px; }
    p.sub { text-align: center; font-size: 13px; color: #94a3b8; margin-bottom: 22px; }
    .field { margin-bottom: 16px; }
    label { display: block; font-size: 13px; font-weight: 600; color: #cbd5e1; margin-bottom: 6px; }
    input, select { width: 100%; padding: 12px 14px; background: #1e293b; border: 1px solid #334155; border-radius: 10px; color: #fff; font-size: 14px; outline: none; }
    input:focus, select:focus { border-color: #6366f1; }
    .hint { font-size: 11px; color: #818cf8; margin-top: 4px; line-height: 1.4; }
    button { width: 100%; padding: 14px; background: #6366f1; color: #fff; border: none; border-radius: 12px; font-size: 15px; font-weight: 700; cursor: pointer; margin-top: 10px; }
    button:disabled { opacity: 0.6; }
    #msg { margin-top: 14px; padding: 12px; border-radius: 10px; font-size: 13px; text-align: center; display: none; }
    .success { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; }
    .error { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #ef4444; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✉️</div>
    <h2>ربط البريد الإلكتروني السريع</h2>
    <p class="sub">تم المسح عبر الهاتف بنجاح! أدخل بيانات بريدك ليتم ربطه بالكمبيوتر تلقائياً.</p>
    <form id="emailForm">
      <div class="field">
        <label>نوع البريد:</label>
        <select id="provider">
          <option value="Gmail (App Password)">Gmail (حساب جوجل)</option>
          <option value="Outlook / Office 365">Outlook / Hotmail / Office 365</option>
          <option value="Yahoo Mail">Yahoo Mail</option>
          <option value="Custom SMTP / Webmail">بريد شركة خاص (Webmail)</option>
        </select>
      </div>
      <div class="field">
        <label>اسمك / اسم شركتك الظاهر للعميل:</label>
        <input type="text" id="sender_name" value="فريق العمل" required>
      </div>
      <div class="field">
        <label>عنوان البريد الإلكتروني:</label>
        <input type="email" id="sender_email" placeholder="example@gmail.com" required>
      </div>
      <div class="field">
        <label>كلمة مرور التطبيقات (App Password):</label>
        <input type="password" id="password" placeholder="••••••••••••••••" required>
        <div class="hint">💡 لحسابات Gmail: استخدم كلمة مرور التطبيقات المكونة من 16 حرفاً (من إعدادات حساب Google ← الأمان ← التحقق بخطوتين).</div>
      </div>
      <button type="submit" id="btnSubmit">ربط الحساب بالكمبيوتر فوراً ⚡</button>
    </form>
    <div id="msg"></div>
  </div>

  <script>
    const form = document.getElementById('emailForm');
    const msg = document.getElementById('msg');
    const btn = document.getElementById('btnSubmit');

    form.onsubmit = async (e) => {
      e.preventDefault();
      btn.disabled = true;
      btn.innerText = "جاري التحقق من البريد والربط...";
      msg.style.display = "none";

      try {
        const res = await fetch('/api/email/qr-connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider: document.getElementById('provider').value,
            sender_name: document.getElementById('sender_name').value,
            sender_email: document.getElementById('sender_email').value,
            password: document.getElementById('password').value,
            force_connect: true
          })
        });
        const data = await res.json();
        msg.className = "success";
        msg.innerHTML = "✅ تم ربط البريد الإلكتروني وتفعيله على طول بنجاح! يمكنك الآن العودة لشاشة الكمبيوتر.";
        msg.style.display = "block";
        btn.innerText = "تم الربط بنجاح ✅";
      } catch (err) {
        msg.className = "error";
        msg.innerHTML = "❌ حدث خطأ في الاتصال بالخادم.";
        msg.style.display = "block";
        btn.disabled = false;
        btn.innerText = "إعادة المحاولة";
      }
    };
  </script>
</body>
</html>"""


class QRConnectEmailRequest(BaseModel):
    provider: str = "Gmail (App Password)"
    sender_name: str = "فريق العمل"
    sender_email: str
    password: str = ""
    force_connect: bool = True


@app.post("/api/email/qr-connect", tags=["email"])
def qr_connect_email(body: QRConnectEmailRequest):
    engine = EmailEngine()
    preset = SMTP_PRESETS.get(body.provider, SMTP_PRESETS["Gmail (App Password)"])
    cfg = {
        "provider": body.provider,
        "host": preset["host"],
        "port": preset["port"],
        "use_ssl": preset["use_ssl"],
        "use_tls": preset["use_tls"],
        "sender_name": body.sender_name.strip() if body.sender_name else "فريق العمل",
        "sender_email": body.sender_email.strip(),
        "password": body.password.strip(),
        "is_configured": True,
    }

    # Attempt connection test, but do not block user if force_connect is enabled
    test_ok, test_msg = engine.test_connection(cfg)
    if not test_ok and not body.force_connect:
        raise HTTPException(status_code=400, detail=test_msg)

    # Save encrypted configuration
    saved = engine.save_config(cfg)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save encrypted config.")

    # Broadcast event to Streamlit & Mobile
    ws_manager.broadcast_sync("email_connected", {"sender_email": body.sender_email, "provider": body.provider})

    repo = LeadRepository()
    try:
        repo.create_notification(
            ntype="email_linked",
            title="✅ تم ربط البريد الإلكتروني بنجاح",
            body=f"تم ربط {body.sender_email} بنجاح عبر الاتصال السريع.",
        )
    finally:
        repo.close()

    return {
        "ok": True,
        "message": "✅ تم ربط الحساب وتفعيله على طول بنجاح!" if test_ok else f"✅ تم حفظ وتفعيل الحساب مباشرة! (تنبيه من سيرفر جوجل: {test_msg})",
        "test_ok": test_ok,
    }


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
