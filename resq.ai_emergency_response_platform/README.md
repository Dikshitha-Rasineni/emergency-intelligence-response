# RESQ.AI — Emergency Response & Decision-Support Platform

## Overview

**RESQ.AI** converts unstructured emergency descriptions into actionable, role-specific emergency intelligence for citizens, hospitals, police stations, and fire & rescue divisions.

> **Core Safety Principle:** RESQ.AI is a **DECISION-SUPPORT SYSTEM**. The AI does not autonomously dispatch emergency services. All recommendations are explicitly presented as decision-support guidance, leaving operational decisions to authorized human responders.

---

## Design System & UX Standards

- **Visual Tone:** Professional, calm, trustworthy, and clinical public safety software.
- **Zero Cyberpunk / Zero Neon:** Uses a clean, neutral white/slate palette (`#f8fafc`, `#ffffff`) with subtle 1px borders (`#e2e8f0`).
- **Semantic Restraint:** High-contrast emergency red is reserved strictly for active crises; amber indicates high priority; safe green indicates available resources; info blue indicates routes and verified tags.
- **Strict Separation of Concerns:**
  - `[VERIFIED INFORMATION]` — Facts from sensors, GPS, user inputs, and official rosters.
  - `[AI ASSESSMENT]` — Model-derived priority scores (0–100) and incident categorization.
  - `[AI RESPONSE RECOMMENDATION]` — Non-diagnostic clinical prep and tactical staging checklists.

---

## Role-Specific Workflows

### 1. Citizen Portal
- **"What happened?"**: Clean incident description text box with quick location detection and coordinates toggle.
- **Emergency Priority**: Intuitive 0–100 priority scale clearly distinguishing **System Priority** from **User Reported Priority**.
- **Operational Status**: Simple, unambiguous `EMERGENCY` or `SAFE / LOW RISK` status banner.
- **What should you do now?**: Tailored, practical scene safety precautions (e.g. fire evacuation, flood elevation, collision standoff). No medical diagnoses.
- **Nearby Emergency Services**: Filterable compact directory (Hospitals, Ambulances, Police, Fire) with live distance, ETA, and capabilities.

### 2. Hospital Triage Directorate (City Care Hospital)
- **Active Incident Telemetry**: Incident ID, casualty counts, reported injuries, and critical flags (e.g. unconscious casualties).
- **Tactical GIS Route**: Calculated route from hospital base to incident with turn-by-turn navigation steps.
- **Required Medical Services**: Level-1 Triage, trauma resuscitation bay, ambulance receiving ramp, and trauma team staging.
- **Estimated Casualty Influx & Staging**: Non-diagnostic preparation protocols (e.g., preparing airway kits, reserving ICU beds).
- **Human Acknowledgment**: Official "Accept & Acknowledge Recommendation" logged with authorized responder ID and timestamp.

### 3. Police Operations & CAD Dispatch (Indiranagar Police Station)
- **Required Police Actions**: Rapid patrol dispatch, scene perimeter security, traffic corridor management, and lane clearance.
- **Corridor & Traffic Impact**: Road blockage indicators, diversion routes, and bottleneck alerts.
- **Recommended Operational Steps**: High-visibility cone staging upstream, ambulance transit preservation, and multi-agency coordination.

### 4. Fire & Rescue Operations (Central Fire Station #04)
- **Required Tactical Deployments**: Extrication assessment, structural suppression, battery isolation, and hazard scans.
- **Required Equipment**: Based strictly on verified data (e.g., hydraulic rescue cutters, SCBA breathing gear, foam tenders, thermal imagers). No hallucinated hazmat alerts.
- **Tactical Guidelines**: Standoff perimeter protocols and casualty extrication coordination.

### 5. Multi-Agency CAD Supervision (Admin)
- Unified overview across all active sectors, resource readiness, database connection telemetry, and audit trail ledger.

---

## Technical Stack & Running Locally

1. **Frontend**: Clean Vanilla JavaScript (`app.js`) + Modular Design System (`styles.css`) + Leaflet GIS mapping.
2. **Backend**: FastAPI REST API (`server.py` or sibling backend on port 8000).
3. **Running the Platform**:
   ```bash
   # Option A: Start the full platform server (serves frontend + FastAPI on port 8000)
   python server.py

   # Option B: Run static frontend on port 5173 (connects to FastAPI at port 8000)
   python -m http.server 5173
   ```
4. **Accessing Portals**:
   - Citizen Portal: `http://localhost:5173/#user`
   - Hospital Triage: `http://localhost:5173/#hospital`
   - Police Operations: `http://localhost:5173/#police`
   - Fire & Rescue: `http://localhost:5173/#fire`
   - Admin CAD: `http://localhost:5173/#admin`
