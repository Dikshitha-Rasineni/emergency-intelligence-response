---
name: Mission-Critical Tactical Incident System
colors:
  surface: '#031427'
  surface-dim: '#031427'
  surface-bright: '#2a3a4f'
  surface-container-lowest: '#000f21'
  surface-container-low: '#0b1c30'
  surface-container: '#102034'
  surface-container-high: '#1b2b3f'
  surface-container-highest: '#26364a'
  on-surface: '#d3e4fe'
  on-surface-variant: '#c6c6cd'
  inverse-surface: '#d3e4fe'
  inverse-on-surface: '#213145'
  outline: '#909097'
  outline-variant: '#45464d'
  surface-tint: '#bec6e0'
  primary: '#bec6e0'
  on-primary: '#283044'
  primary-container: '#0f172a'
  on-primary-container: '#798098'
  inverse-primary: '#565e74'
  secondary: '#b4c5ff'
  on-secondary: '#002a78'
  secondary-container: '#0053db'
  on-secondary-container: '#cdd7ff'
  tertiary: '#ffb4ab'
  on-tertiary: '#690005'
  tertiary-container: '#390002'
  on-tertiary-container: '#f23733'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#ffdad6'
  tertiary-fixed-dim: '#ffb4ab'
  on-tertiary-fixed: '#410002'
  on-tertiary-fixed-variant: '#93000b'
  background: '#031427'
  on-background: '#d3e4fe'
  surface-variant: '#26364a'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: 0em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-sm: 0.5rem
  gutter-lg: 1.5rem
  margin: 1.5rem
  margin-mobile: 0.75rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system establishes a high-reliability, zero-distraction operating environment for emergency dispatchers, clinical trauma coordinators, and field incident commanders. The visual tone balances extreme operational clarity with calm, clinical authority. In high-stress, time-sensitive contexts, cognitive friction must be minimized; every UI element exists purely to support situational awareness, triage speed, and decision accuracy.

Drawing from modern mission-critical operational standards (Mil-Spec UI, avionics, and high-tier medical telemetry consoles), the system prioritizes:
- **Absolute Legibility:** Uncluttered layouts, strict typographic scale, and instantaneous scanning capability.
- **Controlled Chromatic Hierarchy:** Strict functional color usage where high-saturation hues represent urgency, state change, and operational risk—never decorative flourishes.
- **Structural Integrity:** Crisp low-contrast borders and clear planar containment instead of atmospheric blurs, neon glow, or skeuomorphic distraction.
- **Accessibility:** Strict WCAG AAA compliance for critical indicators, text elements, and tactical map overlays across both low-light command hubs and daylight mobile field terminals.

## Colors

The system uses a dark foundation by default to reduce ocular fatigue during 12-hour emergency operations center (EOC) shifts and to maximize contrast against prioritized tactical statuses. Light mode variables invert cleanly for outdoor, direct-sunlight field tablets.

### Functional Palette Structure
- **Structural Deep Navy & Slate:**
  - Base Canvas (`#090d16` / `#0f172a`): Deep, non-reflective background planes.
  - Surface Containers (`#1e293b`): Elevated modular cards, command bars, and navigation rails.
  - Sub-surface / Inset (`#0b1120`): Map controls, active telemetry feeds, data tables.
- **Status & Triage Semantics:**
  - **Critical / Tier 1 Alert (`#dc2626` base, `#b91c1c` active, `#fca5a5` text badge):** Immediate life-safety threat, cardiac arrest, active structure collapse, dispatch priority.
  - **Urgent Warning / Tier 2 (`#d97706` base, `#b45309` active, `#fcd34d` text badge):** Deteriorating conditions, unit delay, escalating vitals, standby warnings.
  - **Operational / Clear (`#16a34a` base, `#15803d` active, `#86efac` text badge):** Unit on scene, normal triage vital, stable condition, task acknowledged.
  - **Tactical Information / Clinical (`#2563eb` base, `#1d4ed8` active, `#93c5fd` text badge):** System telemetry, protocol guidance, hospital routing, comms frequency.
- **Structural Lines & Dividing Neutral:**
  - Low-Contrast Borders (`#334155` dark mode, `#cbd5e1` light mode): Clean geometric division without visual clutter.

## Typography

The typography strategy fulfills three distinct functional roles:
1. **Headlines (`Space Grotesk`):** Engineered for crisp, high-visibility sector titling, triage station headers, and incident summaries. Its subtle technical geometry delivers commanding authority without sacrificing speed of recognition.
2. **Body & Telemetry Notes (`Inter`):** Selected for its industry-standard tall x-height, neutral letterforms, and exceptional legibility across dense incident logs, medical reports, and dispatch summaries.
3. **Labels, Coordinates & Timers (`JetBrains Mono`):** Fixed-width numerical alignment ensures that changing timestamps, GPS coordinates, unit identifiers, and vital telemetry columns do not cause layout shifts during live data streaming.

### Usage Standards
- All timestamps (ETA, elapsed time on scene) and unit badges must strictly use `JetBrains Mono` with uppercase tracking.
- Do not use italic styling in mission-critical alert surfaces.
- Text contrast must exceed a 7:1 ratio (WCAG AAA) for body and tactical data readouts.

## Layout & Spacing

The layout is built on an adaptive multi-pane grid engineered for multi-monitor command workstations, single-screen dispatch consoles, and ruggedized vehicle/field tablets.

### Grid & Density Principles
- **Command Consoles (>= 1440px):** 12 or 16-column fixed-density layouts. Tri-pane architecture: left pane for incoming triaged incidents, center for interactive vector mapping/tactical routing, right for selected incident vitals, dispatch comms, and active personnel.
- **Field Tablets (768px - 1439px):** Split-view 2-column or tabbed multi-drawer interface with a dominant map or patient manifest. Gutter shifts to `gutter-sm` (8px) to maximize data density.
- **Mobile Handhelds (< 768px):** Single-column stacked triage flow, top-pinned emergency action bar, bottom-sheet situational drawer, with `margin-mobile` (12px).
- **Rhythm:** Spacing tokens operate on a rigid 4px/8px incremental rhythm. Spacing around interactive controls and critical triage actions is preserved even in high-density tables to prevent touch/click targeting errors under high-stress conditions.

## Elevation & Depth

Visual hierarchy is constructed through **tonal layering and low-contrast physical outlines**, strictly rejecting drop-shadow heavy designs, glassmorphism, or translucent backdrops that impair contrast.

### Tiers of Depth
- **Level 0 (Canvas Base):** `#090d16`. Ground floor for full-viewport spatial maps, CAD (Computer Aided Dispatch) layers, and dark terminal backdrops.
- **Level 1 (Structural Containers):** `#0f172a` bordered with 1px solid `#1e293b`. Hosts stationary side panels, main incident list streams, and persistent top command navigation.
- **Level 2 (Active Cards & Modules):** `#1e293b` bordered with 1px solid `#334155`. Dynamic cards representing active squads, clinical triage patients, or critical system alerts.
- **Level 3 (Tactical Overlays & Drawers):** `#1e293b` bordered with 1px solid `#475569`, supported by a direct, crisp ambient shadow (`0 8px 24px -4px rgba(0, 0, 0, 0.6)`). Reserved for priority dispatch prompts, triage classification popovers, and defibrillator/vital event modals.
- **Level 4 (Critical Threat Flashes / Interventions):** `#0f172a` canvas augmented with a high-contrast perimeter outline in `#dc2626` (Critical) or `#d97706` (Urgent), drawing immediate visual focus to unassigned emergency incidents.

## Shapes

The design system maintains a **Soft-Edge utilitarian profile (`roundedness: 1`)**. 
- Base components (buttons, input fields, badges, and segmented toggles) utilize a crisp `0.25rem` (4px) border radius.
- Cards, operational modules, and map viewport overlays utilize `0.5rem` (8px, `rounded-lg`).
- Modals, emergency slide-out drawers, and telemetry alert frames use `0.75rem` (12px, `rounded-xl`).
- Fully rounded pills are strictly limited to active presence indicators (e.g., green dot "ON SCENE") and priority count pills. Pill buttons are prohibited to avoid looking consumer-oriented.
- Every container features a visible, calibrated 1px border to preserve silhouette separation under degraded viewing environments (smoke, glare, or vehicle vibration).

## Components

### Buttons & Tactical Triggers
- **Primary Operational:** Solid `#2563eb` fill with `#ffffff` text in `Inter` semi-bold. Focus states feature a 2px offset border in `#93c5fd`.
- **Emergency Critical Action:** Solid `#dc2626` fill with bold `#ffffff` text. Used exclusively for destructive or irreversible actions: "DISPATCH UNIT", "MASS CASUALTY DECLARATION", "DEFIBRILLATOR OVERRIDE".
- **Secondary / Utility:** Surface `#1e293b` fill, 1px `#334155` border, `#f8fafc` text. Hover shifts border to `#64748b`.
- **Destructive Standby:** Inset `#0f172a`, border `#dc2626` with red text; does not utilize solid red until direct active intent.

### Status Indicators & Triage Badges
- Constructed with `JetBrains Mono` in `label-sm` or `label-md`.
- Encapsulated in a 1px border with a 10% alpha fill of the status color:
  - **Red Alert:** Background `rgba(220, 38, 38, 0.15)`, Border `#dc2626`, Text `#fca5a5`.
  - **Amber Alert:** Background `rgba(217, 119, 6, 0.15)`, Border `#d97706`, Text `#fcd34d`.
  - **Operational:** Background `rgba(22, 163, 74, 0.15)`, Border `#16a34a`, Text `#86efac`.
  - **Clinical / Info:** Background `rgba(37, 99, 235, 0.15)`, Border `#2563eb`, Text `#93c5fd`.
- When an active pulse is required for unacknowledged incidents, a 6px static beacon dot is prepended to the badge text.

### Data Tables & Incident Lists
- High-density list items with strict 40px row height in default view, and 32px compact view.
- Alternating subtle row separation using 1px border lines (`#1e293b`).
- Left-edge 3px semantic border strip indicating incident severity (Red, Amber, Green, or Blue) for rapid peripheral scanning.
- Numerical values, radio call signs, and timestamps rendered in `JetBrains Mono` with tabular figures enabled (`font-variant-numeric: tabular-nums`).

### Input Fields & Dispatch Controls
- Background `#0b1120`, border 1px solid `#334155`, text `#f8fafc`.
- Focus ring: 2px solid `#2563eb` with 0px offset.
- Floating or persistent uppercase labels in `JetBrains Mono` `label-sm` at `#94a3b8`.
- Integrated validation message renders directly below field without shifting vertical height.

### Incident Cards & Mission Dossiers
- Heavy structural clarity: `#1e293b` background, `#334155` border, 8px padding (`space-md`).
- Header split: Left side contains call sign / incident ID in monospace, right side displays elapsed timer and triage level badge.
- Inner grid for immediate glanceability: Target Location, Responding Units, and Critical Patient Vitals.

### Operational Map Integration
- Basemaps default to desaturated, high-contrast dark cartography.
- Geofences and emergency corridors use high-contrast solid vector strokes (2px minimum) matching the status color palette.
- Unit markers are clean geometric glyphs (square: engine/apparatus, diamond: EMS/paramedic, circle: patrol) with contrasting status badges.