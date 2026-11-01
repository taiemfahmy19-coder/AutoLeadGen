# AutoLeadGen v2 — CRM & Lead Lifecycle Management

## 1. Overview
AutoLeadGen v2 includes a built-in CRM database designed specifically for WhatsApp outreach. It tracks leads from initial discovery through final conversion or rejection.

---

## 2. Lead Lifecycle State Machine

```
[ NEW ] 
   |
   v
[ READY ]  ----------------------> [ DO NOT CONTACT / REJECTED ]
   |                                            ^
   v                                            |
[ CONTACTED ]                                   |
   |                                            |
   +------------------> [ REPLIED ]             |
   |                         |                  |
   |                         v                  |
   |                  [ INTERESTED ]            |
   |                         |                  |
   |                         v                  |
   +------------------> [ FOLLOW_UP ] ----------+
                             |
                             v
                       [ CONVERTED ]
```

### State Descriptions:
1. **`new`**: Newly extracted lead, pending data normalization, phone verification, and deduplication.
2. **`ready`**: Phone validated, WhatsApp verified, lead scored, and queued for communication.
3. **`contacted`**: Initial outreach message successfully sent.
4. **`replied`**: Prospect responded to the outreach.
5. **`interested`**: Prospect expressed interest in products or services.
6. **`follow_up`**: Prospect requested follow-up at a later date (`next_follow_up_at`).
7. **`converted`**: Deal closed or target goal achieved.
8. **`rejected`**: Prospect opted out or is unqualified (automatically added to Do-Not-Contact).

---

## 3. Database Schema Extensions

The leads repository records full CRM interactions with the following schema:

| Column | Type | Description |
|:---|:---|:---|
| `status` | TEXT | Lifecycle stage (`new`, `ready`, `contacted`, `replied`, `interested`, `follow_up`, `converted`, `rejected`) |
| `priority` | TEXT | Priority level based on scoring (`HIGH`, `MEDIUM`, `LOW`) |
| `first_contact_at` | TIMESTAMP | ISO timestamp of first outreach |
| `last_contact_at` | TIMESTAMP | ISO timestamp of most recent communication |
| `next_follow_up_at` | TIMESTAMP | Scheduled date for subsequent follow-up |
| `notes` | TEXT | Freeform operator notes and call/chat logs |
| `do_not_contact` | INTEGER | Safety flag (1 = permanently blocked from outreach) |

---

## 4. CRM Features in Dashboard & UI

### 4.1 Funnel Analytics
The Dashboard displays real-time KPI metrics and a 7-stage visual pipeline funnel tracking conversion rates at every step.

### 4.2 Lead Profile & Communication Hub
In the **CRM View**, operators can:
- Filter leads by Lifecycle Stage, Priority Tier, Country, or Search Query.
- View comprehensive digital presence scores and verification status.
- Trigger one-click direct WhatsApp conversations (`wa.me` links or automated worker).
- Update status, schedule follow-up reminders with calendar pickers, and append timestamped notes.
- Execute bulk status updates and exports (CSV / Excel).