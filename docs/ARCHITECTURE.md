# AutoLeadGen v2 — System Architecture

## 1. Executive Summary
AutoLeadGen v2 is an enterprise-grade automated lead generation, enrichment, deduplication, scoring, and WhatsApp CRM platform. The system operates on a local workstation (PC) environment with rigorous anti-ban safety, centralized JSON configuration, multi-level deduplication, and full lifecycle tracking.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------+
|                             Streamlit UI                              |
|  [Dashboard View]    [Search View]    [CRM View]    [Settings View]   |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|                             Core Engine                               |
|  - ConfigManager (Atomic disk persistence, thread-safe JSON)         |
|  - SystemController (IDLE, RUNNING, PAUSED, STOPPED, EMERGENCY_STOP)  |
|  - SmartScheduler (7-Day automated region/niche cycling, target 50)   |
+-----------------------------------------------------------------------+
        |                                                 |
        v                                                 v
+-----------------------------+         +-------------------------------+
|     Extraction Pipeline     |         |         CRM & Storage         |
| - Google Search / Maps      |         | - SQLite Repository           |
| - Web Scraper & Parser      |         | - Leads Table (v2 Schema)     |
| - Phone / Data Normalizer   |         | - Interaction Logs            |
| - 5-Level Deduplicator      |         | - Audit & Analytics           |
| - Multi-Factor Scorer       |         +-------------------------------+
+-----------------------------+                         |
        |                                               |
        v                                               v
+-----------------------------------------------------------------------+
|                    WhatsApp & Anti-Ban Protection                     |
| - Playwright Stealth Browser Session (Persistent Profile)             |
| - Human Bézier Curve Mouse Trajectory Simulation                      |
| - Dynamic Keystroke Typing Intervals (40-150ms)                       |
| - Spintax Personalization & Direct Web Link Fallback                  |
| - Strict Verification & Do-Not-Contact Shield                         |
+-----------------------------------------------------------------------+
```

---

## 3. Core Modules & Responsibilities

### 3.1 Configuration Manager (`core/config_manager.py`)
- **Single Source of Truth**: Centralizes settings previously scattered across source files into `data/app_config.json`.
- **Thread Safety**: Employs `threading.RLock` and atomic write maneuvers (writing to temporary `.tmp` before renaming) to eliminate corrupt writes.
- **Dynamic Access**: Provides dot-notation (`get("scheduler.daily_lead_target")`) and deep dictionary merges (`update_nested()`).

### 3.2 System Controller (`core/system_controller.py`)
- **State Machine**: Governs states: `IDLE`, `RUNNING`, `PAUSED`, `STOPPED`, and `EMERGENCY_STOP`.
- **Runtime Pause/Resume**: Implements non-busy thread synchronization via `threading.Event`.
- **Emergency Abort**: Instantly signals running worker threads to halt scraping and messaging tasks, and locks out new job dispatch.

### 3.3 Smart Scheduler (`core/scheduler.py`)
- **Intelligent Rotation**: Rotates target countries and industries according to a 7-day schedule.
- **Strict Preset Binding**: Restricted exclusively to validated system presets (`WORLD_COUNTRIES_DATA`, `INDUSTRY_PRESETS`).
- **Lead Quality Priority**: Strictly enforces **Quality > Quantity**. The system never fills the daily target (e.g. 50 leads) with low-quality or duplicate listings.

### 3.4 5-Level Deduplication Engine (`core/deduplication.py` / `pipeline/deduplicator.py`)
Protects database integrity and respects physical business branches across five distinct validation tiers:
1. **Normalized Phone**: Checks E.164 and clean international digits.
2. **Business Name + Location**: Requires BOTH Name similarity >= 60% AND City/Address similarity >= 60% (prevents false duplicate flags on retail chain branches like "صيدلية النور - الدقي" vs "صيدلية النور - المعادي").
3. **Canonical Website Domain**: Normalizes protocol, www prefix, and trailing slashes.
4. **Place / Listing URL**: Exact URL match across Google Maps, Yelp, Facebook, etc.
5. **Cross-Source Identifier**: Prevents duplicate leads ingested from different extraction channels.

### 3.5 Multi-Factor Lead Scoring (`pipeline/scorer.py`)
Evaluates leads across 100 possible points:
- **Phone & WhatsApp Presence** (30 pts): Verified mobile phone number.
- **Website & Online Identity** (25 pts): Functional website domain, verified directories.
- **Business Profile Completeness** (20 pts): Valid name, physical address, email, social links.
- **Industry & Market Alignment** (15 pts): Direct match with targeted niche keywords.
- **Engagement History** (10 pts): Freshness and responsiveness history.
- **Priority Categorization**:
  - `HIGH`: Score >= 75
  - `MEDIUM`: Score 50 - 74
  - `LOW`: Score < 50

### 3.6 WhatsApp Automation & Anti-Ban Architecture (`pipeline/whatsapp_engine.py`)
- **Playwright Stealth**: Injected scripts mask navigator automation flags.
- **Bézier Mouse Dynamics**: Generates non-linear cubic curves with natural overshoot and micro-jitters.
- **Typing Simulation**: Random delays between keystrokes simulating natural human rhythm.
- **Pre-Flight Verification**: Validates WhatsApp account status before queueing messages; unverified numbers are strictly blocked from automated messaging.