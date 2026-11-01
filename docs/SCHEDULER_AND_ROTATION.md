# AutoLeadGen v2 — Smart Scheduler & Rotation Guide

## 1. Overview
The Smart Scheduler manages automated, scheduled prospecting tasks across global markets and industries. It enforces system consistency, prevents market fatigue, and maintains high lead quality.

---

## 2. Core Operational Principle: Quality > Quantity

> **Lead Quality > Quantity**
> 
> The daily target (default: 50 leads) represents a **maximum ceiling**, NOT a mandatory quota.
> If the extraction pipeline identifies only 37 high-quality, verified leads matching the day's criteria, the system **stops cleanly** at 37. It will NEVER pad results with invalid numbers, landlines, or low-scoring entities.

---

## 3. Seven-Day Default Rotation Schedule

The schedule automatically cycles based on the day of the week (Monday = Day 1 through Sunday = Day 7):

| Day | Region | Sample Countries | Target Niche | Daily Target |
|:---|:---|:---|:---|:---:|
| **Day 1 (Mon)** | Arab World | Saudi Arabia (SA), Egypt (EG), UAE (AE) | Restaurants & Cafes | 50 |
| **Day 2 (Tue)** | Americas | United States (US), Canada (CA), Brazil (BR) | Real Estate & Property | 50 |
| **Day 3 (Wed)** | Europe | Germany (DE), UK (GB), France (FR) | Tech & Software Services | 50 |
| **Day 4 (Thu)** | Arab World | Kuwait (KW), Qatar (QA), Oman (OM) | Healthcare & Clinics | 50 |
| **Day 5 (Fri)** | Americas | Mexico (MX), Argentina (AR), Colombia (CO) | Retail & E-commerce | 50 |
| **Day 6 (Sat)** | Europe | Italy (IT), Spain (ES), Netherlands (NL) | Tourism & Hospitality | 50 |
| **Day 7 (Sun)** | Global / Arab | Saudi Arabia (SA), UAE (AE), Egypt (EG) | Construction & Contracting | 50 |

---

## 4. Preset Validation & Integrity
All schedule items are strictly bound to system presets:
- **Countries**: Validated against `config.constants.WORLD_COUNTRIES_DATA`.
- **Industries**: Validated against `config.constants.INDUSTRY_PRESETS`.
- Arbitrary strings or unsupported country codes are rejected, ensuring scraper queries and language detection rules function without exceptions.

---

## 5. Dashboard Schedule Customization
Users can adjust the schedule directly from the **Settings** view in the UI:
1. Navigate to **Settings** > **Scheduler & Rotation Settings**.
2. Select the target day (1 through 7).
3. Update the Target Region, Country Codes, Industry, and Target Lead Count.
4. Click **Save Schedule Changes**. Updates take effect immediately and are saved to `data/app_config.json`.