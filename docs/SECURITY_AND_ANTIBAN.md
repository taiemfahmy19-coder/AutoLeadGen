# AutoLeadGen v2 — Security & Anti-Ban Architecture

## 1. Compliance & Safety Policy
AutoLeadGen v2 is designed to protect user accounts, preserve platform integrity, and comply with automated messaging best practices. 

> **Important Safety Notice**
> The system's architecture prioritizes account longevity. It operates strictly within human behavioral parameters and does not attempt to bypass platform restrictions or send unsolicited spam.

---

## 2. Multi-Layer Anti-Ban Protections

### 2.1 Playwright Stealth Browser Profile
- **Persistent User Data Directory**: Keeps cookies, tokens, and browser session state intact across restarts, preventing repeated suspicious login flows.
- **Stealth Flag Injection**: Automatically neutralizes `navigator.webdriver`, fake canvas fingerprints, and WebGL telemetry indicators.

### 2.2 Human Bézier Curve Trajectory Simulation
Instead of moving mouse cursors in robotic straight lines:
- Generates cubic Bézier curves with control points simulating natural human hand drift.
- Adds random micro-jitters, velocity variations, and acceleration curves.
- Includes overshoot corrections when approaching clickable elements.

### 2.3 Realistic Typing & Keystroke Simulation
- Simulates human typing speeds: 40ms to 150ms per character with random variance.
- Periodically pauses for longer intervals (200ms - 500ms) to simulate thought pauses between sentences.

### 2.4 Humanized Operation Delays
- Inter-message cool-down: configurable randomized delays (default 45 - 90 seconds).
- Batch cooldown: mandatory resting periods after sending small batches (e.g. 10 messages).

---

## 3. Emergency Stop & Runtime Safety Controls

### 3.1 Runtime States
- `IDLE`: System is waiting for instructions.
- `RUNNING`: Actively extracting or processing leads.
- `PAUSED`: Safely halted midway through a job; locks active browser steps without terminating the session.
- `STOPPED`: Cleanly completed or cancelled.
- `EMERGENCY_STOP`: Immediate safety abort.

### 3.2 Emergency Stop Behavior
When **EMERGENCY STOP** is triggered via UI or API:
1. An abort flag is broadcast to all active worker threads.
2. Active browser actions are immediately interrupted.
3. Message queues are halted and flushed to prevent pending sends.
4. The system is locked until explicitly acknowledged and cleared by the user.

---

## 4. Do-Not-Contact & Verification Guardrails
1. **Strict Verification Guard**: Only numbers verified as active WhatsApp accounts are permitted into the automated messaging queue.
2. **Do-Not-Contact (DNC) Registry**: Leads marked with `do_not_contact = 1` or status `rejected` are permanently blocked from receiving outreach.
3. **Single Contact Window**: Built-in safeguards prevent contacting the same recipient multiple times within a configurable cooldown period (default 30 days).