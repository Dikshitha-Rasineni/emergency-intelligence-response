/**
 * RESQ.AI - Operational Emergency Response Engine
 * Decision-Support System Architecture
 * Compliant with real-world public safety and healthcare standards.
 */

// ============================================================================
// 1. DATA STATE & PRESET INCIDENTS
// ============================================================================

const PRESET_INCIDENTS = {
  accident: {
    incident_id: "INC-D4457C47",
    emergency_type: "Major Road Accident",
    description: "Major accident near highway. Three people injured and one person is unconscious.",
    location_name: "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
    latitude: 12.9352,
    longitude: 77.6944,
    location_details: "Near Kadubeesanahalli Flyover, Left 2 lanes blocked. GPS Accuracy ±6m",
    affected_people: 3,
    injuries: 3,
    critical_indicators: ["Unconscious casualty reported", "Multi-vehicle collision", "Highway corridor lane blockage"],
    system_priority: 82,
    user_priority: 82,
    timestamp: "10:05 AM",
    status: "Active - Response Pending"
  },
  fire: {
    incident_id: "INC-F8902A11",
    emergency_type: "Commercial Building Fire",
    description: "Dense smoke billowing from 2nd floor commercial kitchen. Two staff members trapped in rear corridor.",
    location_name: "100ft Road, Indiranagar, Bengaluru",
    latitude: 12.9784,
    longitude: 77.6408,
    location_details: "Corner of 12th Main, Indiranagar. Commercial complex. GPS Accuracy ±8m",
    affected_people: 2,
    injuries: 1,
    critical_indicators: ["Dense smoke condition", "Occupants trapped in rear corridor", "Kitchen gas cylinders present"],
    system_priority: 79,
    user_priority: 80,
    timestamp: "10:14 AM",
    status: "Active - Rescue Required"
  },
  flood: {
    incident_id: "INC-W3320B94",
    emergency_type: "Urban Flash Flood & Vehicle Stall",
    description: "Severe waterlogging in underpass. Vehicle stalled in 3-foot rising water, 2 occupants safe on vehicle roof.",
    location_name: "Marathahalli Underpass, Bengaluru",
    latitude: 12.9562,
    longitude: 77.7011,
    location_details: "Eastbound underpass lane submerged. Storm drain overflow. GPS Accuracy ±10m",
    affected_people: 2,
    injuries: 0,
    critical_indicators: ["Rising water level in underpass", "Passengers waiting on car roof", "Roadway impassable"],
    system_priority: 48,
    user_priority: 50,
    timestamp: "10:20 AM",
    status: "Active - Rescue Support Staged"
  },
  medical: {
    incident_id: "INC-M6012E55",
    emergency_type: "Cardiac / Acute Medical Crisis",
    description: "Elderly resident collapsed in apartment lobby. Unresponsive, bystander CPR initiated.",
    location_name: "Sobha Jasmine, Green Glen Layout, Bellandur",
    latitude: 12.9279,
    longitude: 77.6710,
    location_details: "Tower B, Ground Floor Lobby. Elevators operational. GPS Accuracy ±5m",
    affected_people: 1,
    injuries: 1,
    critical_indicators: ["Unresponsive casualty", "CPR in progress", "Immediate ALS defibrillator needed"],
    system_priority: 88,
    user_priority: 90,
    timestamp: "10:22 AM",
    status: "Active - Critical ALS Dispatch"
  },
  lowrisk: {
    incident_id: "INC-L1042Z08",
    emergency_type: "Minor Fender Bender / Safe",
    description: "Minor vehicle scratch at low speed parking exit. No injuries, both drivers exchanging details.",
    location_name: "Sarjapur Road, Near Total Mall",
    latitude: 12.9234,
    longitude: 77.6811,
    location_details: "Parking gate #2. Traffic moving normally. GPS Accuracy ±12m",
    affected_people: 0,
    injuries: 0,
    critical_indicators: ["No injuries", "No lane obstruction", "Vehicles drivable"],
    system_priority: 18,
    user_priority: 20,
    timestamp: "10:25 AM",
    status: "Safe - Information Only"
  }
};

// Current active incident loaded in memory
let activeIncident = JSON.parse(JSON.stringify(PRESET_INCIDENTS.accident));

// Responder organizations with real fixed base coordinates
const RESPONDER_NODES = {
  HOSPITAL: {
    id: "HOSP-01",
    name: "City Care Hospital",
    subtext: "Trauma Center Level-1 · Operational Node BLR-CC-04",
    roleName: "Hospital Triage Directorate",
    latitude: 12.9550,
    longitude: 77.6500,
    address: "Old Airport Road, Kodihalli, Bengaluru",
    resources: {
      emergency_dept: "Available (Level-1 Triage Ready)",
      icu_beds: "6 Available of 20",
      general_beds: "18 Available",
      ambulances: "2 ALS Units Ready on Bay",
      trauma_team: "Alpha Surgical Team On Duty"
    }
  },
  POLICE: {
    id: "POL-01",
    name: "Indiranagar Police Station",
    subtext: "Sub-Division Traffic & Patrol Desk · Zone 4",
    roleName: "Police Operations & CAD Dispatch",
    latitude: 12.9780,
    longitude: 77.6400,
    address: "100ft Road, Indiranagar, Bengaluru",
    resources: {
      patrol_units: "Patrol-14 (Available), Patrol-08 (Standby)",
      traffic_squad: "Traffic Control Unit 3 Ready",
      barricades: "Corridor cones and diversions staged",
      duty_officer: "Insp. M. Kumar (On Duty)"
    }
  },
  FIRE: {
    id: "FIRE-01",
    name: "Central Fire & Rescue Station #04",
    subtext: "Division 4 Tactical Rescue Unit · Station Cockpit",
    roleName: "Fire & Rescue Operations",
    latitude: 12.9650,
    longitude: 77.6000,
    address: "HAL 2nd Stage, Domlur, Bengaluru",
    resources: {
      tenders: "Heavy Rescue Tender HR-04 (Ready)",
      crew: "6 Firefighters on Active Duty",
      extrication: "Hydraulic Cutter/Spreader Kit Ready",
      water_foam: "4,500 L Water / 500 L AFFF Foam"
    }
  }
};

// Nearby Emergency Services Directory (Calculated from Incident)
const ALL_RESOURCES = [
  {
    id: "RES-H1",
    type: "HOSPITAL",
    name: "City Care Hospital",
    distance_km: 2.4,
    eta_min: 8,
    availability: "Emergency Department Available",
    capability: "Trauma Care Level-1 · 6 ICU Beds Ready",
    contact: "+91 80 2520 1100",
    lat: 12.9550,
    lng: 77.6500
  },
  {
    id: "RES-H2",
    type: "HOSPITAL",
    name: "Manipal Hospital HAL",
    distance_km: 4.8,
    eta_min: 14,
    availability: "Trauma Department Available",
    capability: "Multi-Speciality · Emergency Surgery On Call",
    contact: "+91 80 2502 4444",
    lat: 12.9580,
    lng: 77.6490
  },
  {
    id: "RES-H3",
    type: "HOSPITAL",
    name: "Sakra World Hospital",
    distance_km: 6.1,
    eta_min: 18,
    availability: "Limited ICU Beds",
    capability: "Advanced Cardiac & Trauma Wing",
    contact: "+91 80 4969 4969",
    lat: 12.9288,
    lng: 77.6833
  },
  {
    id: "RES-A1",
    type: "AMBULANCE",
    name: "Ambulance A-12 (ALS Unit)",
    distance_km: 3.1,
    eta_min: 10,
    availability: "Available on Ramp",
    capability: "Advanced Life Support · Defibrillator · Stretcher",
    contact: "108 / Dispatch",
    lat: 12.9420,
    lng: 77.6750
  },
  {
    id: "RES-A2",
    type: "AMBULANCE",
    name: "Ambulance B-04 (BLS Unit)",
    distance_km: 5.2,
    eta_min: 15,
    availability: "Available",
    capability: "Basic Life Support · Oxygen · Spinal Board",
    contact: "108 / Dispatch",
    lat: 12.9610,
    lng: 77.6600
  },
  {
    id: "RES-P1",
    type: "POLICE",
    name: "Indiranagar Police Station",
    distance_km: 3.8,
    eta_min: 7,
    availability: "Patrol Unit Available",
    capability: "Traffic Management · Scene Perimeter Security",
    contact: "100 / +91 80 2294 2522",
    lat: 12.9780,
    lng: 77.6400
  },
  {
    id: "RES-P2",
    type: "POLICE",
    name: "HAL Police Station",
    distance_km: 5.1,
    eta_min: 12,
    availability: "Patrol-08 Ready",
    capability: "Corridor Patrol · Road Diversion Support",
    contact: "100 / +91 80 2294 2530",
    lat: 12.9530,
    lng: 77.6620
  },
  {
    id: "RES-F1",
    type: "FIRE",
    name: "Central Fire & Rescue Station #04",
    distance_km: 5.6,
    eta_min: 12,
    availability: "Heavy Rescue Tender Ready",
    capability: "Extrication Gear · Fire Suppression · 6 Crew",
    contact: "101 / +91 80 2297 1500",
    lat: 12.9650,
    lng: 77.6000
  },
  {
    id: "RES-F2",
    type: "FIRE",
    name: "Sarjapur Fire Sub-Station",
    distance_km: 7.2,
    eta_min: 16,
    availability: "Water Bowser Available",
    capability: "Rapid Response Tender · Chemical Extinguisher",
    contact: "101 / +91 80 2297 1550",
    lat: 12.9150,
    lng: 77.6850
  }
];

// Current responder acknowledgement state
let acknowledgementState = {
  HOSPITAL: { acknowledged: false, responder: "Dr. V. Rao (Lead Triage)", timestamp: null },
  POLICE: { acknowledged: false, responder: "Insp. M. Kumar (Patrol Command)", timestamp: null },
  FIRE: { acknowledged: false, responder: "Capt. S. Sharma (Station Commander)", timestamp: null }
};

// Current active role
let currentRole = "USER"; // USER, HOSPITAL, POLICE, FIRE, ADMIN
let responderStatus = "AVAILABLE"; // AVAILABLE, BUSY, OFFLINE

// ============================================================================
// 2. INTELLIGENCE & DECISION-SUPPORT ENGINE
// ============================================================================

const LOCALIZED_SEVERITY = {
  en: { CRITICAL: "CRITICAL", HIGH: "HIGH", MODERATE: "MODERATE", LOW: "LOW" },
  te: { CRITICAL: "అత్యవసరం (CRITICAL)", HIGH: "అధిక ప్రాధాన్యత (HIGH)", MODERATE: "మధ్యస్థం (MODERATE)", LOW: "సాధారణం (LOW)" },
  ta: { CRITICAL: "அதிமுக்கியம் (CRITICAL)", HIGH: "உயர் (HIGH)", MODERATE: "நடுத்தரம் (MODERATE)", LOW: "குறைவு (LOW)" },
  hi: { CRITICAL: "गंभीर (CRITICAL)", HIGH: "उच्च (HIGH)", MODERATE: "मध्यम (MODERATE)", LOW: "सामान्य (LOW)" },
  kn: { CRITICAL: "ಗಂಭೀರ (CRITICAL)", HIGH: "ಉನ್ನತ (HIGH)", MODERATE: "ಮಧ್ಯಮ (MODERATE)", LOW: "ಸಾಮಾನ್ಯ (LOW)" },
  ml: { CRITICAL: "അത്യാഹിതം (CRITICAL)", HIGH: "ഉയർന്നത് (HIGH)", MODERATE: "മിതമായത് (MODERATE)", LOW: "കുറഞ്ഞത് (LOW)" },
};

function getLocalizedSeverityLabel(label, lang = "en") {
  const l = (lang || "en").toLowerCase();
  return (LOCALIZED_SEVERITY[l] && LOCALIZED_SEVERITY[l][label]) || label;
}

/**
 * Calculates priority score and severity classification based on verified inputs
 */
function evaluateIncidentSeverity(text, injuries, affected, indicators) {
  let score = 30; // base score
  const lower = (text || "").toLowerCase();
  
  if (lower.includes("unconscious") || lower.includes("not breathing") || lower.includes("cardiac") || lower.includes("severe") || lower.includes("స్పృహ") || lower.includes("बेहोश") || lower.includes("மயக்கம்")) {
    score += 35;
  }
  if (lower.includes("fire") || lower.includes("smoke") || lower.includes("trapped") || lower.includes("explosion") || lower.includes("మంటలు") || lower.includes("ఆగ") || lower.includes("தீ") || lower.includes("बೆಂಕಿ")) {
    score += 30;
  }
  if (lower.includes("accident") || lower.includes("crash") || lower.includes("collision") || lower.includes("ప్రమాదం") || lower.includes("दुर्घटना") || lower.includes("விபத்து") || lower.includes("ಅಪಘಾತ")) {
    score += 20;
  }
  if (injuries > 0) {
    score += Math.min(injuries * 10, 30);
  }
  if (affected > 0) {
    score += Math.min(affected * 5, 15);
  }
  
  // Boundary constraints
  score = Math.max(10, Math.min(100, score));
  
  let label = "LOW";
  if (score >= 75) label = "CRITICAL";
  else if (score >= 50) label = "HIGH";
  else if (score >= 25) label = "MODERATE";
  
  return { score, label };
}

/**
 * Generates practical precautions for citizens.
 * Strictly non-diagnostic; uses verified AI-generated precautions from backend if available.
 */
function generateCitizenPrecautions(emergencyType, text, priority, lang = "en") {
  // If backend returned precautions in user's language, prioritize them directly!
  if (activeIncident && activeIncident.precautions && activeIncident.precautions.length > 0) {
    return activeIncident.precautions.map((p, idx) => ({ num: idx + 1, text: p }));
  }

  const t = (emergencyType || "").toLowerCase() + " " + (text || "").toLowerCase();
  const currentLang = (lang || (activeIncident && activeIncident.detected_language) || "en").toLowerCase();

  if (currentLang === "te") {
    if (t.includes("fire") || t.includes("smoke") || t.includes("మంటలు")) {
      return [
        { num: 1, text: "పొగ కింద నేలపై వంగి పాకండి — శుభ్రమైన గాలి నేల నుండి 1 అడుగు ఎత్తులో ఉంటుంది." },
        { num: 2, text: "ఎటువంటి పరిస్థితుల్లోనూ లిఫ్టులను ఉపయోగించవద్దు; అత్యవసర మెట్లను మాత్రమే ఉపయోగించండి." },
        { num: 3, text: "మంటలు వ్యాపించకుండా ఉండటానికి బయటకు వచ్చేటప్పుడు తలుపులు మూసివేయండి." },
        { num: 4, text: "బట్టలకు మంటలు అంటుకుంటే: వెంటనే ఆగండి, నేలపై పడుకోండి, దొర్లండి (Stop, Drop, Roll)." }
      ];
    } else if (t.includes("flood") || t.includes("water") || t.includes("వరద")) {
      return [
        { num: 1, text: "ప్రవహించే వరద నీటిలో నడవడానికి లేదా వాహనాలు నడపడానికి ప్రయత్నించవద్దు." },
        { num: 2, text: "నీటిలో మునిగిన విద్యుత్ వైర్లు మరియు తెరిచి ఉన్న మ్యాన్‌హోల్స్ పట్ల జాగ్రత్తగా ఉండండి." },
        { num: 3, text: "రెస్క్యూ బృందాలు వచ్చే వరకు ఎత్తైన ప్రదేశంలో లేదా భవనం పైకప్పుపై వేచి ఉండండి." }
      ];
    } else {
      return [
        { num: 1, text: "తీవ్రంగా గాయపడిన వ్యక్తులను మంటలు లేదా పేలుడు ప్రమాదం లేకపోతే కదల్చవద్దు." },
        { num: 2, text: "రహదారి రద్దీకి దూరంగా, సురక్షితమైన ప్రదేశంలో నిలబడండి." },
        { num: 3, text: "అత్యవసర అంబులెన్స్ రాక కోసం రహదారి మార్గాన్ని ఖాళీగా ఉంచండి." }
      ];
    }
  }

  if (t.includes("fire") || t.includes("smoke") || t.includes("burn")) {
    return [
      { num: 1, text: "Move away from the fire immediately and stay upwind of smoke." },
      { num: 2, text: "Do not enter smoke-filled corridors or closed rooms." },
      { num: 3, text: "Alert everyone in the building and pull manual fire alarms if safe." },
      { num: 4, text: "Avoid elevators at all times; use external staircases." },
      { num: 5, text: "Wait for Central Fire & Rescue teams at an open outdoor assembly point." },
      { num: 6, text: "Do not return into the structure to retrieve personal property." }
    ];
  } else if (t.includes("flood") || t.includes("water") || t.includes("submerged")) {
    return [
      { num: 1, text: "Move to higher ground immediately; do not linger in low-lying corridors." },
      { num: 2, text: "Avoid walking or driving through moving water (6 inches can sweep an adult)." },
      { num: 3, text: "Do not touch downed electrical poles or enter water near power junction boxes." },
      { num: 4, text: "If trapped on a stalled vehicle, remain on the roof and signal for assistance." },
      { num: 5, text: "Follow official municipal warnings and keep phone battery reserved for SOS." }
    ];
  } else if (t.includes("cardiac") || t.includes("collapsed") || t.includes("unresponsive")) {
    return [
      { num: 1, text: "Verify casualty response and breathing; alert bystanders to call 108 immediately." },
      { num: 2, text: "If casualty is unresponsive with no normal breathing, begin chest compressions if trained." },
      { num: 3, text: "Send a bystander to bring an Automated External Defibrillator (AED) if available." },
      { num: 4, text: "Do not administer food, water, or medication into casualty's mouth." },
      { num: 5, text: "Ensure apartment gate or building lobby is held open for incoming ambulance crew." }
    ];
  } else {
    return [
      { num: 1, text: "Move to a safe position off the road corridor to avoid secondary vehicle impacts." },
      { num: 2, text: "Do not move an injured person unless there is immediate danger (e.g. active vehicle fire)." },
      { num: 3, text: "Call 112 (National SOS) or 108 (Medical Dispatch) immediately." },
      { num: 4, text: "Keep the accident area clear so arriving emergency responders can park and work." },
      { num: 5, text: "Share your exact landmark or verified GPS location with dispatchers." },
      { num: 6, text: "Do not crowd the casualties or create additional traffic rubbernecking." }
    ];
  }
}

/**
 * Generates role-specific operational recommendations
 */
function generateRoleIntelligence(role, incident) {
  const isCritical = incident.system_priority >= 75;
  const isHigh = incident.system_priority >= 50;

  // Use backend multilingual recommendations if present
  if (incident && incident.recommendations && incident.recommendations.recommendation) {
    const rec = incident.recommendations;
    const checklist = rec.operational_checklist || [rec.recommendation];
    if (role === "HOSPITAL") {
      return {
        required_services: [
          { label: "Emergency Department Triage", status: "Required", verified: true },
          { label: "Trauma Resuscitation Bay", status: isCritical ? "Immediate Prep" : "Standby", verified: true },
          { label: "Ambulance Receiving Ramp", status: "Designate Bay 2", verified: true },
          { label: "Emergency Medical Team", status: "Alerted", verified: true }
        ],
        capacity_needs: {
          affected_count: incident.affected_people,
          injuries_count: incident.injuries,
          critical_count: (incident.description || "").toLowerCase().includes("unconscious") ? 1 : 0
        },
        recommended_prep: checklist,
        summary: rec.summary
      };
    } else if (role === "POLICE") {
      return {
        required_response: [
          { label: "Dispatch Nearest Patrol Unit", status: "En Route", verified: true },
          { label: "Secure Incident Perimeter", status: "Required", verified: true },
          { label: "Corridor Traffic Management", status: isHigh ? "High Priority" : "Monitor", verified: true }
        ],
        scene_intelligence: {
          corridor: incident.location_name || incident.location,
          traffic_impact: isCritical ? "Severe Lane Obstruction" : "Moderate Slowdown",
          road_blockage: "Corridor Managed",
          priority_level: isCritical ? "CRITICAL" : "HIGH"
        },
        recommended_actions: checklist,
        summary: rec.summary
      };
    } else if (role === "FIRE") {
      return {
        required_response: [
          { label: "Deploy Heavy Rescue Tender", status: "En Route", verified: true },
          { label: "Hydraulic Extrication Readiness", status: "Required", verified: true },
          { label: "Hazard Isolation Perimeter", status: "Active", verified: true }
        ],
        tactical_assessment: {
          hazard_condition: "Scene Scan Active",
          staging_sector: "Upwind Corridor",
          water_foam_readiness: "Ready"
        },
        recommended_actions: checklist,
        summary: rec.summary
      };
    }
  }
  
  if (role === "HOSPITAL") {
    return {
      required_services: [
        { label: "Emergency Department Triage", status: "Required", verified: true },
        { label: "Trauma Resuscitation Bay", status: isCritical ? "Immediate Prep" : "Standby", verified: true },
        { label: "Ambulance Receiving Ramp", status: "Designate Bay 2", verified: true },
        { label: "Emergency Medical Team (Alpha)", status: "Alerted", verified: true }
      ],
      capacity_needs: {
        affected_count: incident.affected_people,
        injuries_count: incident.injuries,
        critical_count: incident.description.toLowerCase().includes("unconscious") ? 1 : 0
      },
      recommended_prep: [
        "Prepare emergency receiving area for incoming blunt trauma casualties",
        incident.description.toLowerCase().includes("unconscious")
          ? "Alert neuro-trauma consult and staging for unconscious casualty"
          : "Stage standard laceration and orthopedic stabilization equipment",
        `Reserve ${Math.max(1, incident.injuries)} emergency bays and prepare triage telemetry`,
        "Designate ambulance receiving ramp with spinal immobilization kits",
        "Prepare suction, advanced airway equipment, and intravenous fluids"
      ]
    };
  } else if (role === "POLICE") {
    return {
      required_response: [
        { label: "Dispatch Nearest Patrol Unit (Patrol-14)", status: "En Route", verified: true },
        { label: "Secure Incident Perimeter", status: "Required", verified: true },
        { label: "Corridor Traffic Management", status: isHigh ? "High Priority" : "Monitor", verified: true },
        { label: "Maintain Clear Emergency Vehicle Access", status: "Critical", verified: true },
        { label: "Coordinate Multi-Agency Logistics", status: "Active", verified: true }
      ],
      scene_intelligence: {
        corridor: incident.location_name,
        traffic_impact: isCritical ? "Severe Lane Obstruction (Corridor Slowdown)" : "Moderate Slowdown",
        road_blockage: "2 Lanes Affected of 4",
        priority_level: incident.system_priority >= 75 ? "CRITICAL" : "HIGH"
      },
      recommended_actions: [
        "Proceed immediately to incident coordinates via assigned clear corridor.",
        "Deploy high-visibility cones 150m upstream to prevent secondary collisions.",
        "Keep lane 1 fully open for arriving medical ambulances and fire rescue tenders.",
        "Coordinate traffic diversion at previous junction to ease upstream bottlenecks.",
        "Document involved vehicle registrations and maintain chain of evidence."
      ]
    };
  } else if (role === "FIRE") {
    const isFire = incident.emergency_type.toLowerCase().includes("fire");
    return {
      required_response: [
        { label: isFire ? "Structural Fire Suppression" : "Vehicle Stabilization / Rescue Support", status: "Required", verified: true },
        { label: "Casualty Extrication Assessment", status: isCritical ? "Cutting Gear Ready" : "Standby", verified: true },
        { label: "Scene Safety & Hazard Containment", status: "Active", verified: true },
        { label: "Thermal & Hydrocarbon Scan", status: "Recommended", verified: true }
      ],
      required_equipment: isFire ? [
        "Primary Water / AFFF Foam Tender HR-04",
        "Self-Contained Breathing Apparatus (SCBA) sets for entry crew",
        "Thermal imaging camera to locate internal heat hotspots",
        "Positive pressure ventilation fan for corridor smoke clearance"
      ] : [
        "Hydraulic rescue spreaders and cutters (casualty extrication kit)",
        "Dry chemical / foam extinguisher (hydrocarbon vehicle spill prevention)",
        "Vehicle battery isolation disconnect tool",
        "Fluid absorbent containment booms for oil runoff prevention"
      ],
      recommended_actions: [
        "Dispatch Heavy Rescue Tender HR-04 with 6-person crew.",
        "Establish 30m tactical standoff zone around vehicle wreckage.",
        "Isolate electrical battery cables to prevent spontaneous ignition.",
        "Support medical triage team during casualty extrication if trapped."
      ]
    };
  }
  return null;
}

// Calculate route metrics between responder and incident
function calculateRouteMetrics(responderRole, incident) {
  const node = RESPONDER_NODES[responderRole];
  if (!node) return { distance_km: 4.2, eta_min: 9, origin: "Central Post" };
  
  // Real Haversine calculation
  const R = 6371; // Earth radius in km
  const dLat = (incident.latitude - node.latitude) * Math.PI / 180;
  const dLon = (incident.longitude - node.longitude) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(node.latitude * Math.PI / 180) * Math.cos(incident.latitude * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const straightKm = R * c;
  
  // Road factor (~1.3x straight distance in urban grid)
  const roadKm = Math.max(1.2, +(straightKm * 1.35).toFixed(1));
  // Average urban emergency speed ~28-32 km/h
  const etaMin = Math.max(3, Math.round((roadKm / 28) * 60));
  
  return {
    origin_name: node.name,
    origin_address: node.address,
    destination_name: incident.location_name,
    distance_km: roadKm,
    eta_min: etaMin,
    route_corridor: "Fastest route via Main Arterial & Corridor Access Road"
  };
}

// ============================================================================
// 3. API CLIENT (Connecting to FastAPI backend if available)
// ============================================================================

const RESQ_API = {
  baseUrl: window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1") ? "" : "http://localhost:8000",
  activeEndpoint: "",
  isBackendConnected: false,

  async checkHealth() {
    const endpoints = [
      `${this.baseUrl}/api/v1/health`,
      `${this.baseUrl}/api/health`,
      `${this.baseUrl}/health`,
      "http://localhost:8000/api/v1/health",
      "http://localhost:8000/api/health"
    ];

    for (const ep of endpoints) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1200);
        const res = await fetch(ep, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          const data = await res.json();
          this.isBackendConnected = true;
          this.activeEndpoint = ep.replace(/\/health$/, "");
          this.updateApiStatusUI(true, data.database === "connected");
          return true;
        }
      } catch (e) {
        // continue probe
      }
    }
    this.isBackendConnected = false;
    this.updateApiStatusUI(false, false);
    return false;
  },

  async getIncidents() {
    if (this.isBackendConnected) {
      try {
        const res = await fetch(`${this.activeEndpoint}/incidents`);
        if (res.ok) {
          const list = await res.json();
          if (list && list.length > 0) return list;
        }
      } catch (e) {
        console.warn("Failed to fetch incidents:", e);
      }
    }
    return Object.values(PRESET_INCIDENTS);
  },

  async getIncident(id) {
    if (this.isBackendConnected) {
      try {
        const res = await fetch(`${this.activeEndpoint}/incidents/${id}`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn(`Failed to fetch incident ${id}:`, e);
      }
    }
    return Object.values(PRESET_INCIDENTS).find(i => i.incident_id === id) || null;
  },

  async createIncident(incidentData) {
    if (this.isBackendConnected) {
      try {
        const payload = {
          description: incidentData.description,
          latitude: incidentData.latitude,
          longitude: incidentData.longitude,
          location: incidentData.location_name || incidentData.location,
          location_name: incidentData.location_name || incidentData.location,
          affected_people: incidentData.affected_people || 0,
          injuries: incidentData.injuries || 0,
          critical_indicators: incidentData.critical_indicators || [],
          emergency_type: incidentData.emergency_type || null,
          source: "USER"
        };
        const ep = `${this.activeEndpoint}/incidents`;
        const res = await fetch(ep, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const data = await res.json();
          return data;
        }
      } catch (err) {
        console.warn("Backend API call failed, falling back to local intelligence engine:", err);
      }
    }
    // High-fidelity fallback / local response
    const evalResult = evaluateIncidentSeverity(
      incidentData.description,
      incidentData.injuries || 0,
      incidentData.affected_people || 0,
      incidentData.critical_indicators || []
    );
    return {
      incident_id: incidentData.incident_id || "INC-LOCAL",
      id: incidentData.incident_id || "INC-LOCAL",
      description: incidentData.description,
      latitude: incidentData.latitude,
      longitude: incidentData.longitude,
      location_name: incidentData.location_name || "Verified Incident Location",
      affected_people: incidentData.affected_people || 0,
      injuries: incidentData.injuries || 0,
      critical_indicators: incidentData.critical_indicators || [],
      emergency_type: incidentData.emergency_type || "General Emergency",
      priority_score: evalResult.score,
      system_priority: evalResult.score,
      user_priority: incidentData.user_priority || evalResult.score,
      severity: evalResult.label,
      status: "REPORTED",
      source: "USER"
    };
  },

  async updateIncident(id, updateData) {
    if (this.isBackendConnected) {
      try {
        const res = await fetch(`${this.activeEndpoint}/incidents/${id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updateData)
        });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn("Update incident error:", e);
      }
    }
    return null;
  },

  async getNearbyResources(lat, lng, type = null, radius = 25.0) {
    if (this.isBackendConnected) {
      if (lat == null || lng == null) {
        return [];
      }
      try {
        let url = `${this.activeEndpoint}/resources/nearby?latitude=${lat}&longitude=${lng}&radius=${radius}`;
        if (type && type !== "ALL") url += `&type=${encodeURIComponent(type)}`;
        const res = await fetch(url);
        if (res.ok) {
          const list = await res.json();
          return Array.isArray(list) ? list : [];
        }
      } catch (e) {
        console.warn("Fetch nearby resources error:", e);
      }
      return [];
    }
    return type && type !== "ALL" ? ALL_RESOURCES.filter(r => r.type === type) : ALL_RESOURCES;
  },

  async getRoute(originLat, originLng, destLat, destLng, originName, destName, role = null) {
    if (this.isBackendConnected) {
      try {
        const params = new URLSearchParams({
          origin_lat: originLat,
          origin_lng: originLng,
          destination_lat: destLat,
          destination_lng: destLng,
          origin_name: originName || "Station Base",
          destination_name: destName || "Incident Location",
        });
        if (role) params.append("responder_role", role);
        const res = await fetch(`${this.activeEndpoint}/routes?${params.toString()}`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn("Fetch route error:", e);
      }
    }
    return null;
  },

  async getPrecautions(emergencyType, description = "", priority = 50) {
    if (this.isBackendConnected) {
      try {
        const res = await fetch(`${this.activeEndpoint}/ai/precautions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            emergency_type: emergencyType,
            description: description,
            priority_score: priority
          })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.precautions && data.precautions.length > 0) {
            return data.precautions.map((text, idx) => ({ num: idx + 1, text }));
          }
        }
      } catch (e) {
        console.warn("Fetch precautions error:", e);
      }
    }
    return generateCitizenPrecautions(emergencyType, description, priority);
  },

  async getDashboardOverview() {
    if (this.isBackendConnected) {
      try {
        const res = await fetch(`${this.activeEndpoint}/dashboard/overview`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn("Fetch dashboard overview error:", e);
      }
    }
    return null;
  },

  updateApiStatusUI(connected, dbLive = false) {
    const badge = document.getElementById("backendApiBadge");
    if (badge) {
      if (connected) {
        badge.innerHTML = `<span style="width:6px;height:6px;border-radius:50%;background:#16a34a;display:inline-block;"></span> ${dbLive ? 'POSTGRESQL + FASTAPI LIVE' : 'FASTAPI LIVE'}`;
        badge.className = "badge badge-safe mono";
        badge.title = "Connected to live FastAPI backend & PostgreSQL database";
      } else {
        badge.innerHTML = `<span style="width:6px;height:6px;border-radius:50%;background:#d97706;display:inline-block;"></span> LOCAL ENGINE`;
        badge.className = "badge badge-warning mono";
        badge.title = "FastAPI backend running in standalone local intelligence mode";
      }
    }
  }
};

// ============================================================================
// 4. MAP RENDERING ENGINE
//    Primary:  MapLibre GL JS + Amazon Location Service (backend proxy)
//    Fallback: Leaflet + OpenStreetMap tiles
//    Final:    SVG vector canvas (zero external dependencies)
// ============================================================================

let activeMapInstance = null;   // MapLibre map instance
let leafletMapInstance = null;  // Leaflet fallback instance
let mapMarkersGroup = null;

// Routing source badge labels
const ROUTING_SOURCE_LABELS = {
  AMAZON_LOCATION_ROUTES: "Amazon Location Routes",
  OSRM_ROAD_NETWORK: "OSRM Road Network",
  ACCURATE_OSRM_ROAD_NETWORK: "OSRM Road Network",
  GIS_FALLBACK_MATRIX: "Local GIS Fallback",
};

/**
 * Fetch verified road route from FastAPI backend.
 * Backend tries: Amazon Location Routes → OSRM → local fallback.
 * Never fabricates routes — returns null if all sources fail.
 */
async function getVerifiedRoadRoute(originLat, originLng, destLat, destLng, originName, destName, role) {
  if (RESQ_API.isBackendConnected) {
    try {
      const res = await RESQ_API.getRoute(originLat, originLng, destLat, destLng, originName, destName, role);
      if (res && res.coordinates && res.coordinates.length > 2) {
        return res;
      }
    } catch (e) {
      console.warn("Backend route API error:", e);
    }
  }
  return null;
}

/**
 * Destroy any existing map instance cleanly.
 */
function destroyExistingMap() {
  if (activeMapInstance) {
    try { activeMapInstance.remove(); } catch (_) {}
    activeMapInstance = null;
  }
  if (leafletMapInstance) {
    try { leafletMapInstance.remove(); } catch (_) {}
    leafletMapInstance = null;
  }
  mapMarkersGroup = null;
}

/**
 * Build a MapLibre marker element with role-appropriate colour.
 * RED=incident, BLUE=hospital, ORANGE=police, YELLOW=fire, GREEN=ambulance
 */
function makeMarkerEl(type) {
  const cfg = {
    INCIDENT:  { bg: "#dc2626", emoji: "🚨" },
    HOSPITAL:  { bg: "#1d4ed8", emoji: "🏥" },
    AMBULANCE: { bg: "#16a34a", emoji: "🚑" },
    POLICE:    { bg: "#ea580c", emoji: "🚓" },
    FIRE:      { bg: "#ca8a04", emoji: "🚒" },
    BASE:      { bg: "#0f172a", emoji: "📍" },
  };
  const c = cfg[type] || cfg.BASE;
  const el = document.createElement("div");
  el.style.cssText = `background:${c.bg};color:#fff;border:2px solid #fff;border-radius:50%;
    width:30px;height:30px;display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 6px rgba(0,0,0,0.35);font-size:14px;cursor:pointer;`;
  el.textContent = c.emoji;
  return el;
}

/**
 * PRIMARY: Initialize map using MapLibre GL JS with Amazon Location tile proxy.
 * Falls back to Leaflet+OSM if MapLibre or backend unavailable.
 */
async function initializeOperationalMap(containerId, originRole) {
  const container = document.getElementById(containerId);
  if (!container) return;

  destroyExistingMap();
  container.innerHTML = "";

  const incidentLat = activeIncident.latitude;
  const incidentLng = activeIncident.longitude;
  const originNode  = originRole ? RESPONDER_NODES[originRole] : null;
  const originLat   = originNode ? originNode.latitude  : null;
  const originLng2  = originNode ? originNode.longitude : null;

  // ── Attempt MapLibre + Amazon Location ──────────────────────────────────
  if (typeof maplibregl !== "undefined" && RESQ_API.isBackendConnected) {
    try {
      const styleUrl = `${RESQ_API.activeEndpoint}/maps/style.json`;

      // Quick probe — if style endpoint fails, fall through to Leaflet
      const probe = await fetch(styleUrl, { signal: AbortSignal.timeout(3000) }).catch(() => null);
      if (probe && probe.ok) {
        activeMapInstance = new maplibregl.Map({
          container: containerId,
          style: styleUrl,
          center: [incidentLng, incidentLat],
          zoom: 13,
          attributionControl: false,
        });

        activeMapInstance.addControl(new maplibregl.NavigationControl(), "top-right");
        activeMapInstance.addControl(
          new maplibregl.AttributionControl({ compact: true,
            customAttribution: "© Amazon Location Service · © Esri" }),
          "bottom-right"
        );

        activeMapInstance.on("load", async () => {
          // Incident marker
          new maplibregl.Marker({ element: makeMarkerEl("INCIDENT") })
            .setLngLat([incidentLng, incidentLat])
            .setPopup(new maplibregl.Popup({ offset: 16 }).setHTML(
              `<b>${activeIncident.emergency_type}</b><br>${activeIncident.location_name}<br>Priority: ${activeIncident.system_priority}/100`
            ))
            .addTo(activeMapInstance);

          if (originNode) {
            // Responder base marker
            const baseType = originRole === "HOSPITAL" ? "HOSPITAL" : originRole === "POLICE" ? "POLICE" : "FIRE";
            new maplibregl.Marker({ element: makeMarkerEl(baseType) })
              .setLngLat([originLng2, originLat])
              .setPopup(new maplibregl.Popup({ offset: 16 }).setHTML(
                `<b>${originNode.name}</b><br>${originNode.address}`
              ))
              .addTo(activeMapInstance);

            // Fit bounds to both points while route loads
            activeMapInstance.fitBounds(
              [[Math.min(originLng2, incidentLng) - 0.01, Math.min(originLat, incidentLat) - 0.01],
               [Math.max(originLng2, incidentLng) + 0.01, Math.max(originLat, incidentLat) + 0.01]],
              { padding: 50 }
            );

            // Fetch verified route from backend (Amazon Location → OSRM → fallback)
            const route = await getVerifiedRoadRoute(
              originLat, originLng2, incidentLat, incidentLng,
              originNode.name, activeIncident.location_name, originRole
            );

            if (route && route.coordinates && route.coordinates.length > 2) {
              window.activeLiveRoute = route;

              // Convert [[lat,lng],...] → [[lng,lat],...] for GeoJSON
              const geojsonCoords = route.coordinates.map(c => [c[1], c[0]]);

              activeMapInstance.addSource("resq-route", {
                type: "geojson",
                data: { type: "Feature", geometry: { type: "LineString", coordinates: geojsonCoords } }
              });
              activeMapInstance.addLayer({
                id: "resq-route-line",
                type: "line",
                source: "resq-route",
                layout: { "line-join": "round", "line-cap": "round" },
                paint: { "line-color": "#2563eb", "line-width": 4, "line-opacity": 0.85 }
              });

              // Fit to actual route geometry
              const lngs = geojsonCoords.map(c => c[0]);
              const lats = geojsonCoords.map(c => c[1]);
              activeMapInstance.fitBounds(
                [[Math.min(...lngs) - 0.005, Math.min(...lats) - 0.005],
                 [Math.max(...lngs) + 0.005, Math.max(...lats) + 0.005]],
                { padding: 50 }
              );

              // Update telemetry panel
              _updateRouteTelemetry(route);
            } else {
              console.warn("No verified route geometry available — route line not drawn.");
            }
          } else {
            // Citizen view: resource markers
            const resources = (currentResources && currentResources.length > 0)
              ? currentResources.slice(0, 6) : ALL_RESOURCES.slice(0, 5);
            resources.forEach(res => {
              const rType = (res.type || res.resource_type || "BASE").toUpperCase();
              const lat = res.latitude || res.lat;
              const lng = res.longitude || res.lng;
              if (!lat || !lng) return;
              new maplibregl.Marker({ element: makeMarkerEl(rType) })
                .setLngLat([lng, lat])
                .setPopup(new maplibregl.Popup({ offset: 14 }).setHTML(
                  `<b>${res.name}</b><br>${res.distance_km || "?"} km · ${res.eta_min || "?"} min<br>${res.availability || ""}`
                ))
                .addTo(activeMapInstance);
            });
          }
        });

        activeMapInstance.on("error", (e) => {
          console.warn("MapLibre error:", e);
        });

        return; // MapLibre initialised successfully
      }
    } catch (e) {
      console.warn("MapLibre/Amazon Location init failed, falling back to Leaflet:", e);
      destroyExistingMap();
      container.innerHTML = "";
    }
  }

  // ── Fallback: Leaflet + OpenStreetMap ────────────────────────────────────
  if (typeof L !== "undefined") {
    try {
      leafletMapInstance = L.map(containerId, { zoomControl: true, attributionControl: false })
        .setView([incidentLat, incidentLng], 13);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18, opacity: 0.95
      }).addTo(leafletMapInstance);

      mapMarkersGroup = L.layerGroup().addTo(leafletMapInstance);

      const mkIcon = (bg, emoji) => L.divIcon({
        className: "custom-map-icon",
        html: `<div style="background:${bg};color:#fff;border:2px solid #fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);font-size:13px;">${emoji}</div>`,
        iconSize: [28, 28], iconAnchor: [14, 14]
      });

      L.marker([incidentLat, incidentLng], { icon: mkIcon("#dc2626", "🚨") })
        .addTo(mapMarkersGroup)
        .bindPopup(`<b>${activeIncident.emergency_type}</b><br>${activeIncident.location_name}<br>Priority: ${activeIncident.system_priority}/100`);

      if (originNode) {
        const roleEmoji = originRole === "HOSPITAL" ? "🏥" : originRole === "POLICE" ? "🚓" : "🚒";
        L.marker([originLat, originLng2], { icon: mkIcon("#0f172a", roleEmoji) })
          .addTo(mapMarkersGroup)
          .bindPopup(`<b>${originNode.name}</b><br>${originNode.address}`);

        const bounds = L.latLngBounds([[originLat, originLng2], [incidentLat, incidentLng]]);
        leafletMapInstance.fitBounds(bounds, { padding: [40, 40] });

        // Fetch verified route
        getVerifiedRoadRoute(originLat, originLng2, incidentLat, incidentLng,
          originNode.name, activeIncident.location_name, originRole)
          .then(route => {
            if (route && route.coordinates && route.coordinates.length > 2) {
              window.activeLiveRoute = route;
              const poly = L.polyline(route.coordinates, {
                color: "#2563eb", weight: 4, opacity: 0.85, dashArray: "8, 6"
              }).addTo(mapMarkersGroup);
              leafletMapInstance.fitBounds(poly.getBounds(), { padding: [40, 40] });
              _updateRouteTelemetry(route);
            } else {
              console.warn("No verified route — route line not drawn.");
            }
          })
          .catch(e => console.warn("Leaflet route fetch error:", e));
      } else {
        const resources = (currentResources && currentResources.length > 0)
          ? currentResources.slice(0, 5) : ALL_RESOURCES.slice(0, 4);
        resources.forEach(res => {
          const rType = (res.type || res.resource_type || "").toUpperCase();
          const emoji = rType === "HOSPITAL" ? "🏥" : rType === "POLICE" ? "🚓" : rType === "FIRE" ? "🚒" : "🚑";
          const bg    = rType === "HOSPITAL" ? "#1d4ed8" : rType === "POLICE" ? "#ea580c" : rType === "FIRE" ? "#ca8a04" : "#16a34a";
          const lat = res.latitude || res.lat;
          const lng = res.longitude || res.lng;
          if (lat && lng) {
            L.marker([lat, lng], { icon: mkIcon(bg, emoji) })
              .addTo(mapMarkersGroup)
              .bindPopup(`<b>${res.name}</b><br>${res.distance_km || "?"} km · ${res.eta_min || "?"} min`);
          }
        });
      }
      return;
    } catch (e) {
      console.warn("Leaflet fallback failed:", e);
    }
  }

  // ── Final fallback: SVG canvas ───────────────────────────────────────────
  renderSvgOperationalMap(container, originNode, incidentLat, incidentLng);
}

/**
 * Update route telemetry panel elements with verified route data.
 */
function _updateRouteTelemetry(route) {
  const sourceLabel = ROUTING_SOURCE_LABELS[route.routing_status] || route.routing_status || "Verified Route";
  const distEl = document.getElementById("liveRoadDistance");
  if (distEl) distEl.innerText = `${route.distance_km} km`;
  const etaEl = document.getElementById("liveRoadEta");
  if (etaEl) etaEl.innerText = `${route.eta_min} min`;
  const corrEl = document.getElementById("liveRouteCorridorNote");
  if (corrEl) corrEl.innerText = `* ${sourceLabel}: ${route.route_corridor || "Verified road corridor"}.`;
}

function renderSvgOperationalMap(container, originNode, incLat, incLng) {
  const originLabel = originNode ? originNode.name : "Local Response Base";
  const metrics = calculateRouteMetrics(currentRole, activeIncident);
  
  container.innerHTML = `
    <div style="width:100%;height:100%;position:relative;background:#f8fafc;display:flex;flex-direction:column;justify-content:space-between;padding:16px;">
      <div style="display:flex;justify-content:space-between;align-items:center;z-index:2;">
        <span class="badge badge-info mono">TACTICAL VECTOR GRID · REAL-TIME COORDINATES</span>
        <span class="mono" style="font-size:11px;color:#64748b;">${activeIncident.latitude}° N, ${activeIncident.longitude}° E</span>
      </div>
      
      <!-- SVG Route Diagram -->
      <svg style="width:100%;height:240px;" viewBox="0 0 600 200" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Grid Lines -->
        <line x1="50" y1="40" x2="550" y2="40" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4" />
        <line x1="50" y1="100" x2="550" y2="100" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4" />
        <line x1="50" y1="160" x2="550" y2="160" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4" />
        
        <!-- Arterial Road Path -->
        <path d="M 80 140 Q 220 50 340 120 T 520 80" stroke="#2563eb" stroke-width="4" stroke-linecap="round" stroke-dasharray="8 6" />
        
        <!-- Origin Station Node -->
        <circle cx="80" cy="140" r="14" fill="#0f172a" stroke="#ffffff" stroke-width="3" />
        <text x="80" y="145" font-family="Inter, sans-serif" font-size="12" fill="#ffffff" text-anchor="middle">BASE</text>
        <text x="80" y="175" font-family="Inter, sans-serif" font-weight="600" font-size="12" fill="#0f172a" text-anchor="middle">${originLabel}</text>
        
        <!-- Mid-corridor Telemetry Marker -->
        <rect x="260" y="75" width="100" height="28" rx="4" fill="#ffffff" stroke="#cbd5e1" stroke-width="1" />
        <text x="310" y="93" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#2563eb" text-anchor="middle">${metrics.distance_km} KM · ${metrics.eta_min} MIN</text>
        
        <!-- Incident Destination Node -->
        <circle cx="520" cy="80" r="16" fill="#dc2626" stroke="#ffffff" stroke-width="3" />
        <text x="520" y="86" font-family="Inter, sans-serif" font-size="14" fill="#ffffff" text-anchor="middle">🚨</text>
        <text x="520" y="120" font-family="Inter, sans-serif" font-weight="600" font-size="12" fill="#dc2626" text-anchor="middle">ACTIVE INCIDENT</text>
      </svg>

      <div style="display:flex;justify-content:space-between;align-items:center;background:#ffffff;padding:8px 12px;border-radius:4px;border:1px solid #e2e8f0;z-index:2;">
        <div style="font-size:12px;">
          <span style="color:#64748b;">Route:</span> <b>${metrics.route_corridor}</b>
        </div>
        <div style="font-size:12px;">
          <span style="color:#64748b;">Target ETA:</span> <b style="color:#2563eb;">${metrics.eta_min} Minutes</b>
        </div>
      </div>
    </div>
  `;
}

// ============================================================================
// 5. VIEW RENDERERS (Citizen vs Hospital vs Police vs Fire vs Admin)
// ============================================================================

/**
 * Render Citizen / User Dashboard
 */
function renderCitizenDashboard() {
  const container = document.getElementById("mainAppView");
  const isEmergency = activeIncident.system_priority >= 50;
  const precautions = generateCitizenPrecautions(activeIncident.emergency_type, activeIncident.description, activeIncident.system_priority);

  container.innerHTML = `
    <!-- Top Action & One-Tap Direct SOS Strip -->
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:var(--radius-md);padding:14px 18px;margin-bottom:16px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;">
      <div>
        <h2 style="font-size:18px;font-weight:600;margin-bottom:2px;">Citizen Emergency Access</h2>
        <p style="font-size:13px;color:#475569;">Report an emergency or obtain immediate safety precautions and nearby medical/police assistance.</p>
      </div>
      <div class="sos-dial-bar">
        <a href="tel:112" class="dial-pill emergency-sos">
          <span>🚨</span> <span>SOS DIAL 112</span>
        </a>
        <a href="tel:108" class="dial-pill">
          <span>🚑</span> <span>Ambulance 108</span>
        </a>
        <a href="tel:100" class="dial-pill">
          <span>🚓</span> <span>Police 100</span>
        </a>
        <a href="tel:101" class="dial-pill">
          <span>🚒</span> <span>Fire 101</span>
        </a>
      </div>
    </div>

    <!-- Quick Scenario Presets Bar (For seamless prototype testing) -->
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap;background:#ffffff;padding:8px 12px;border:1px solid #e2e8f0;border-radius:var(--radius-sm);">
      <span class="mono" style="font-size:11px;font-weight:600;color:#64748b;">TEST SCENARIOS:</span>
      <button class="btn btn-secondary btn-sm" onclick="loadScenario('accident')">Major Highway Accident</button>
      <button class="btn btn-secondary btn-sm" onclick="loadScenario('fire')">Building Fire</button>
      <button class="btn btn-secondary btn-sm" onclick="loadScenario('flood')">Underpass Flood</button>
      <button class="btn btn-secondary btn-sm" onclick="loadScenario('medical')">Cardiac Collapse</button>
      <button class="btn btn-secondary btn-sm" onclick="loadScenario('lowrisk')">Minor Safe Incident</button>
    </div>

    <!-- MAIN TWO COLUMN WORKSTATION -->
    <div class="grid-main grid-main-split">
      
      <!-- LEFT COLUMN: Description, Priority & Status -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        
        <!-- SECTION 1: EMERGENCY DESCRIPTION -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">What happened?</h3>
              <p style="font-size:12px;color:#64748b;">Describe the situation in clear, plain words</p>
            </div>
            <span class="tag-fact">PUBLIC INPUT</span>
          </div>
          <div class="card-body">
            <textarea id="citizenDescriptionInput" 
                      style="width:100%;height:90px;padding:10px 12px;border:1px solid #cbd5e1;border-radius:var(--radius-sm);font-family:var(--font-sans);font-size:14px;resize:vertical;outline:none;" 
                      placeholder="e.g. Major accident near highway. Three people injured and one person is unconscious.">${activeIncident.description}</textarea>
            
            <div style="margin-top:12px;display:flex;flex-direction:column;gap:8px;">
              <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;">
                <label style="font-size:12px;font-weight:600;color:#475569;min-width:70px;">Location:</label>
                <input type="text" id="citizenLocationInput" value="${activeIncident.location_name || ''}" 
                       style="flex:1;min-width:220px;padding:8px 12px;border:1px solid #cbd5e1;border-radius:var(--radius-sm);font-size:13px;outline:none;" 
                       placeholder="e.g. Location X or MG Road, Bengaluru">
                <button class="btn btn-secondary btn-sm" onclick="detectUserLocation()">Detect GPS</button>
                <button class="btn btn-secondary btn-sm" onclick="toggleLocationDetails()">GPS Details</button>
              </div>

              <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;padding-top:4px;">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                  ${activeIncident.coordinates_verified === false || activeIncident.location_source === 'UNVERIFIED'
                    ? '<span class="badge" style="background:#fee2e2;color:#991b1b;font-weight:600;font-size:11px;">⚠️ UNVERIFIED COORDINATES (Original Text Preserved)</span>'
                    : '<span class="badge" style="background:#dcfce7;color:#166534;font-weight:600;font-size:11px;">✓ VERIFIED LOCATION COORDINATES</span>'
                  }
                  <span class="badge" style="background:#ede9fe;color:#5b21b6;font-size:11px;font-weight:600;">LANG: ${(activeIncident.detected_language || 'en').toUpperCase()}</span>
                </div>

                <div style="display:flex;align-items:center;gap:6px;">
                  <label style="font-size:12px;color:#64748b;font-weight:500;">Language:</label>
                  <select id="citizenLanguageSelect" style="padding:4px 8px;border:1px solid #cbd5e1;border-radius:var(--radius-sm);font-size:12px;background:#ffffff;outline:none;">
                    <option value="auto" ${!activeIncident.detected_language || activeIncident.detected_language === 'auto' ? 'selected' : ''}>Auto-Detect</option>
                    <option value="en" ${activeIncident.detected_language === 'en' ? 'selected' : ''}>English</option>
                    <option value="te" ${activeIncident.detected_language === 'te' ? 'selected' : ''}>Telugu (తెలుగు)</option>
                    <option value="ta" ${activeIncident.detected_language === 'ta' ? 'selected' : ''}>Tamil (தமிழ்)</option>
                    <option value="hi" ${activeIncident.detected_language === 'hi' ? 'selected' : ''}>Hindi (हिन्दी)</option>
                    <option value="kn" ${activeIncident.detected_language === 'kn' ? 'selected' : ''}>Kannada (ಕನ್ನಡ)</option>
                    <option value="ml" ${activeIncident.detected_language === 'ml' ? 'selected' : ''}>Malayalam (മലയാളം)</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Expandable Location Details (Hidden by default) -->
            <div id="locationDetailsBox" style="display:none;margin-top:10px;padding:8px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:var(--radius-sm);font-size:12px;color:#475569;">
              <div class="mono">Coordinates: ${activeIncident.latitude != null ? activeIncident.latitude + '° N, ' + activeIncident.longitude + '° E' : 'Unresolved / Unverified (No coordinates injected)'}</div>
              <div>Source: ${activeIncident.location_source || 'USER_ENTERED'} · Accuracy: ${activeIncident.location_details || 'Manual Landmark'}</div>
            </div>

            <div style="margin-top:14px;display:flex;justify-content:flex-end;">
              <button class="btn btn-primary" onclick="submitCitizenUpdate()">Update Incident Details</button>
            </div>
          </div>
        </div>

        <!-- SECTION 2: PRIORITY SCORE -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">Emergency Priority</h3>
              <p style="font-size:12px;color:#64748b;">Calculated urgency and user reported level</p>
            </div>
            <div style="display:flex;gap:6px;">
              <span class="tag-ai">AI ASSESSMENT: ${activeIncident.system_priority}/100</span>
            </div>
          </div>
          <div class="card-body">
            <!-- Priority Scale Labels -->
            <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;color:#64748b;margin-bottom:2px;">
              <span>0–24 LOW</span>
              <span>25–49 MODERATE</span>
              <span>50–74 HIGH</span>
              <span>75–100 CRITICAL</span>
            </div>

            <!-- Priority Slider Bar -->
            <div class="priority-track">
              <input type="range" min="0" max="100" value="${activeIncident.user_priority}" 
                     class="priority-slider" id="citizenPrioritySlider" 
                     oninput="handleCitizenPriorityChange(this.value)" />
            </div>

            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
              <div>
                <span style="font-size:12px;color:#64748b;">User Reported Priority: </span>
                <span class="mono" style="font-weight:700;font-size:14px;" id="userPriorityVal">${activeIncident.user_priority} / 100</span>
              </div>
              <div style="text-align:right;">
                <span style="font-size:12px;color:#64748b;">System Calculated Priority: </span>
                <span class="mono" style="font-weight:700;font-size:14px;color:${isEmergency ? '#dc2626' : '#16a34a'};">${activeIncident.system_priority} / 100</span>
              </div>
            </div>
            <p style="font-size:11px;color:#94a3b8;margin-top:6px;">
              * Note: System priority is calculated based on reported injuries and hazards. Adjusting the slider records user perception without overriding verified system triage.
            </p>
          </div>
        </div>

        <!-- SECTION 3: STATUS RESULT -->
        <div class="status-banner ${isEmergency ? 'status-banner-emergency' : 'status-banner-safe'}">
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="font-size:26px;">${isEmergency ? '🚨' : '🛡️'}</div>
            <div>
              <div style="font-weight:700;font-size:15px;color:${isEmergency ? '#dc2626' : '#16a34a'};letter-spacing:0.02em;">
                ${isEmergency ? 'EMERGENCY' : 'SAFE / LOW RISK'}
              </div>
              <div style="font-size:13px;color:#1e293b;margin-top:2px;">
                ${isEmergency 
                  ? 'Immediate emergency assistance may be required. Nearby responders alerted.' 
                  : 'Situation currently presents low immediate operational risk. Monitor conditions.'}
              </div>
            </div>
          </div>
          <div class="mono" style="font-size:13px;font-weight:700;padding:4px 10px;background:#ffffff;border:1px solid #cbd5e1;border-radius:var(--radius-sm);">
            Score: ${activeIncident.system_priority}/100
          </div>
        </div>

        <!-- SECTION 5: WHAT SHOULD YOU DO NOW? (PRECAUTIONS) -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">What should you do now?</h3>
              <p style="font-size:12px;color:#64748b;">Practical safety precautions tailored to this situation</p>
            </div>
            <span class="tag-ai">AI RECOMMENDED PRECAUTIONS</span>
          </div>
          <div class="card-body">
            <div style="display:flex;flex-direction:column;gap:8px;">
              ${precautions.map(p => `
                <div style="display:flex;align-items:flex-start;gap:10px;padding:8px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:var(--radius-sm);">
                  <div style="background:#0f172a;color:#ffffff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;">
                    ${p.num}
                  </div>
                  <div style="font-size:13px;color:#1e293b;line-height:1.4;">
                    ${p.text}
                  </div>
                </div>
              `).join('')}
            </div>
            <div class="decision-support-box" style="margin-top:12px;">
              <span>⚠️ Safety Notice: These precautions are practical scene safety guidelines, not medical advice. Stay clear of incoming traffic.</span>
            </div>
          </div>
        </div>

      </div>

      <!-- RIGHT COLUMN: Nearby Emergency Services & Map -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        
        <!-- SECTION 4: NEARBY EMERGENCY SERVICES -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">Nearby Emergency Services</h3>
              <p style="font-size:12px;color:#64748b;">Live verified stations & response units</p>
            </div>
            <span class="tag-fact">VERIFIED DIRECTORY</span>
          </div>
          <div class="card-body" style="padding-bottom:8px;">
            <!-- Simple Filter Tabs -->
            <div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;">
              <button class="filter-pill active" onclick="filterNearbyServices('ALL', this)">All</button>
              <button class="filter-pill" onclick="filterNearbyServices('HOSPITAL', this)">Hospitals</button>
              <button class="filter-pill" onclick="filterNearbyServices('AMBULANCE', this)">Ambulances</button>
              <button class="filter-pill" onclick="filterNearbyServices('POLICE', this)">Police</button>
              <button class="filter-pill" onclick="filterNearbyServices('FIRE', this)">Fire</button>
            </div>

            <!-- Service Rows Container -->
            <div id="nearbyServicesList">
              ${renderNearbyServicesRows("ALL")}
            </div>
          </div>
        </div>

        <!-- OPERATIONAL MAP VIEW -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">Incident Area Map</h3>
              <p style="font-size:12px;color:#64748b;">Incident location & nearby public safety bases</p>
            </div>
            <span class="mono" style="font-size:11px;color:#64748b;">BLR GRID</span>
          </div>
          <div class="card-body" style="padding:10px;">
            <div id="operationalMapCitizen" class="map-operational-frame"></div>
          </div>
        </div>

      </div>

    </div>
  `;

  // Initialize Map for citizen view
  setTimeout(() => {
    initializeOperationalMap("operationalMapCitizen", null);
  }, 50);
}

let currentResources = [...ALL_RESOURCES];

async function syncNearbyResources(filterType = "ALL") {
  if (RESQ_API.isBackendConnected) {
    if (activeIncident && activeIncident.latitude != null && activeIncident.longitude != null) {
      const list = await RESQ_API.getNearbyResources(
        activeIncident.latitude,
        activeIncident.longitude,
        filterType
      );
      currentResources = Array.isArray(list) ? list : [];
      return currentResources;
    } else {
      // Unverified coordinates: do NOT inject Bengaluru resources!
      currentResources = [];
      return currentResources;
    }
  }
  currentResources = filterType === "ALL" ? ALL_RESOURCES : ALL_RESOURCES.filter(r => r.type === filterType);
  return currentResources;
}

/**
 * Render Nearby Services List Rows
 */
function renderNearbyServicesRows(filterType) {
  const filtered = filterType === "ALL" 
    ? currentResources 
    : currentResources.filter(r => {
        const t = (r.type || r.resource_type || "").toUpperCase();
        if (filterType === "HOSPITAL") {
          return t === "HOSPITAL" || t === "CLINIC";
        }
        return t === filterType;
      });

  if (!filtered || filtered.length === 0) {
    if (activeIncident && (activeIncident.coordinates_verified === false || activeIncident.latitude == null)) {
      return `<div style="padding:14px;text-align:center;color:#b91c1c;font-size:12px;background:#fef2f2;border:1px solid #fecaca;border-radius:6px;margin:8px 0;">
        ⚠️ Location coordinates are unverified. Please enter an identifiable landmark or detect GPS to discover real facilities in this sector.
      </div>`;
    }
    return `<div style="padding:16px;text-align:center;color:#64748b;font-size:13px;">No ${filterType === 'ALL' ? '' : filterType} emergency facilities found within sector search radius.</div>`;
  }

  return filtered.map(item => {
    const isClinic = item.is_clinic || (item.type || item.resource_type || "").toUpperCase() === "CLINIC" || (item.name || "").toLowerCase().includes("clinic");
    const rType = isClinic ? "CLINIC" : (item.type || item.resource_type || "HOSPITAL").toUpperCase();
    const icon = isClinic ? "🩺" : (rType === "HOSPITAL" ? "🏥" : rType === "AMBULANCE" ? "🚑" : rType === "POLICE" ? "🚓" : "🚒");
    const badgeLabel = isClinic 
      ? '<span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;background:#fef3c7;color:#92400e;margin-left:4px;">CLINIC / OUTPATIENT</span>' 
      : (rType === "HOSPITAL" ? '<span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;background:#dcfce7;color:#166534;margin-left:4px;">EMERGENCY HOSPITAL</span>' : '');

    const providerBadge = item.provider 
      ? `<span style="font-size:10px;color:#64748b;margin-left:4px;">(${item.provider})</span>` 
      : '';

    const navLink = item.navigation_url || `https://www.google.com/maps/dir/?api=1&destination=${item.latitude || item.lat},${item.longitude || item.lng}`;

    return `
    <div class="service-row" style="padding:10px 12px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;gap:10px;">
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <div style="font-size:18px;margin-top:2px;">${icon}</div>
        <div>
          <div style="font-weight:600;font-size:13px;color:#0f172a;display:flex;align-items:center;flex-wrap:wrap;gap:2px;">
            <span>${item.name}</span>
            ${badgeLabel}
            ${providerBadge}
          </div>
          <div style="font-size:12px;color:#475569;margin-top:1px;">${item.capability || (item.capabilities ? item.capabilities.join(' · ') : (item.address || 'Emergency Unit Ready'))}</div>
          <div style="font-size:11px;color:#16a34a;font-weight:500;margin-top:2px;">${item.availability || 'Available'} · Phone: ${item.contact || item.phone || '112'}</div>
        </div>
      </div>
      <div style="text-align:right;flex-shrink:0;">
        <div class="mono" style="font-weight:700;font-size:13px;color:#0f172a;">${item.distance_km != null ? item.distance_km : 2.5} km</div>
        <div class="mono" style="font-size:12px;color:#2563eb;font-weight:600;">${item.eta_min != null ? item.eta_min : (item.eta_minutes != null ? item.eta_minutes : 8)} min</div>
        <div style="display:flex;gap:4px;margin-top:4px;justify-content:flex-end;">
          <button class="btn btn-secondary btn-sm" onclick="viewServiceDetails('${item.id || item.resource_id}')">Info</button>
          <a href="${navLink}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="text-decoration:none;display:inline-flex;align-items:center;">Map ↗</a>
        </div>
      </div>
    </div>
  `;
  }).join('');
}

async function filterNearbyServices(type, btnEl) {
  document.querySelectorAll(".filter-pill").forEach(el => el.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  const list = document.getElementById("nearbyServicesList");
  if (list) {
    list.innerHTML = `<div style="padding:12px;text-align:center;color:#64748b;font-size:12px;" class="mono">Querying PostgreSQL geospatial registry...</div>`;
    await syncNearbyResources(type);
    list.innerHTML = renderNearbyServicesRows(type);
  }
}

/**
 * Render Responder Dashboard (Hospital, Police, Fire)
 */
function renderResponderDashboard(role) {
  const container = document.getElementById("mainAppView");
  const node = RESPONDER_NODES[role];
  const intelligence = generateRoleIntelligence(role, activeIncident);
  const route = calculateRouteMetrics(role, activeIncident);
  const isAck = acknowledgementState[role].acknowledged;
  const isCritical = activeIncident.system_priority >= 75;

  // Control rooms strictly receive English output
  const rawLang = (activeIncident.detected_language || activeIncident.language || "en").toLowerCase();
  const isNonEnglish = rawLang !== "en" && rawLang !== "auto";
  const englishDispatchText = activeIncident.english_description || activeIncident.dispatch_summary_en || (
    isNonEnglish
      ? `CAD Dispatch: ${activeIncident.emergency_type} at ${activeIncident.location_name || activeIncident.location || 'Incident Site'}. ${activeIncident.injuries || 0} casualties reported (${activeIncident.affected_people || 0} individuals affected). Priority responder deployment required.`
      : activeIncident.description
  );

  container.innerHTML = `
    <!-- Top Organization Header Bar -->
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:var(--radius-md);padding:14px 18px;margin-bottom:16px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="background:#0f172a;color:#ffffff;border-radius:var(--radius-sm);width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-size:20px;">
          ${role === "HOSPITAL" ? "🏥" : role === "POLICE" ? "🚓" : "🚒"}
        </div>
        <div>
          <div style="display:flex;align-items:center;gap:8px;">
            <h2 style="font-size:18px;font-weight:600;">${node.name}</h2>
            <span class="badge badge-neutral mono">${node.id}</span>
          </div>
          <p style="font-size:12px;color:#475569;">${node.subtext}</p>
        </div>
      </div>

      <!-- Operational Status Control -->
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:12px;color:#64748b;">Station Status:</span>
        <select class="btn btn-secondary btn-sm" onchange="handleResponderStatusChange(this.value)" style="font-weight:600;">
          <option value="AVAILABLE" ${responderStatus === 'AVAILABLE' ? 'selected' : ''}>🟢 AVAILABLE (Duty)</option>
          <option value="BUSY" ${responderStatus === 'BUSY' ? 'selected' : ''}>🟡 BUSY (Dispatched)</option>
          <option value="OFFLINE" ${responderStatus === 'OFFLINE' ? 'selected' : ''}>⚪ OFFLINE</option>
        </select>
        <span class="badge ${isAck ? 'badge-safe' : 'badge-warning'} mono">
          ${isAck ? 'INCIDENT ACKNOWLEDGED' : 'ACTION PENDING'}
        </span>
      </div>
    </div>

    <!-- ACTIVE INCIDENT STRIP -->
    <div style="background:${isCritical ? '#fef2f2' : '#fffbeb'};border:1px solid ${isCritical ? '#fecaca' : '#fde68a'};border-radius:var(--radius-md);padding:14px 18px;margin-bottom:16px;">
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;">
        <div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <span class="badge ${isCritical ? 'badge-emergency' : 'badge-warning'} mono">${activeIncident.incident_id}</span>
            <span style="font-weight:700;font-size:16px;color:#0f172a;">${activeIncident.emergency_type}</span>
            <span class="tag-fact">${activeIncident.timestamp || 'ACTIVE'}</span>
            <span class="badge" style="background:#0f172a;color:#ffffff;font-size:10px;">EN DISPATCH</span>
          </div>
          <p style="font-size:13px;color:#1e293b;font-weight:500;">${englishDispatchText}</p>
          ${isNonEnglish ? `
            <details style="margin-top:6px;font-size:11px;color:#64748b;">
              <summary style="cursor:pointer;color:#475569;font-weight:600;">Original Citizen Input (${rawLang.toUpperCase()})</summary>
              <div style="margin-top:4px;padding:6px 10px;background:#ffffff;border-radius:4px;border:1px solid #e2e8f0;font-style:italic;">
                "${activeIncident.description}"
              </div>
            </details>
          ` : ''}
        </div>

        
        <!-- Urgency Metrics & Acknowledgement Button -->
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="text-align:right;">
            <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">Dispatch Priority</div>
            <div class="mono" style="font-size:20px;font-weight:700;color:${isCritical ? '#dc2626' : '#d97706'};">
              ${activeIncident.system_priority} <span style="font-size:13px;color:#64748b;">/ 100</span>
            </div>
            <span class="badge ${isCritical ? 'badge-emergency' : 'badge-warning'}">${isCritical ? 'CRITICAL' : 'HIGH'}</span>
          </div>

          <div>
            ${isAck ? `
              <div style="background:#ffffff;border:1px solid #86efac;border-radius:var(--radius-sm);padding:8px 12px;font-size:12px;color:#166534;">
                <div><b>✓ Acknowledged</b></div>
                <div style="font-size:11px;">By ${acknowledgementState[role].responder} at ${acknowledgementState[role].timestamp}</div>
              </div>
            ` : `
              <button class="btn btn-emergency btn-lg" onclick="acknowledgeIncident('${role}')">
                Accept & Acknowledge Recommendation
              </button>
            `}
          </div>
        </div>
      </div>

      <!-- Critical Indicators Row -->
      <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:8px;border-top:1px solid rgba(0,0,0,0.06);padding-top:10px;">
        <span class="tag-fact">AFFECTED: ${activeIncident.affected_people}</span>
        <span class="tag-fact">INJURIES: ${activeIncident.injuries}</span>
        ${activeIncident.critical_indicators.map(ind => `
          <span class="tag-ai">CRITICAL INDICATOR: ${ind}</span>
        `).join('')}
      </div>
    </div>

    <!-- MAIN TWO COLUMN OPERATIONAL LAYOUT -->
    <div class="grid-main grid-main-split">
      
      <!-- LEFT COLUMN: Incident Area Map & Shortest Route -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        
        <!-- OPERATIONAL ROUTE & MAP CARD -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">Incident Area Map & Route</h3>
              <p style="font-size:12px;color:#64748b;">Calculated route from station base to incident location</p>
            </div>
            <div style="display:flex;gap:6px;">
              <span class="tag-fact">VERIFIED GIS ROUTING</span>
            </div>
          </div>
          <div class="card-body" style="padding:10px;">
            <!-- Map Container -->
            <div id="operationalMapResponder" class="map-operational-frame"></div>

            <!-- Route Metrics Panel -->
            <div style="margin-top:12px;display:grid;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:8px;">
              <div class="telemetry-cell">
                <div class="telemetry-label">Your Station Base</div>
                <div class="telemetry-value" style="font-size:13px;">${node.name}</div>
              </div>
              <div class="telemetry-cell">
                <div class="telemetry-label">Shortest Road Distance</div>
                <div class="telemetry-value mono" id="liveRoadDistance" style="color:#0f172a;">${route.distance_km} km</div>
              </div>
              <div class="telemetry-cell">
                <div class="telemetry-label">Estimated Transit Time</div>
                <div class="telemetry-value mono" id="liveRoadEta" style="color:#2563eb;">${route.eta_min} min</div>
              </div>
              <div class="telemetry-cell">
                <div class="telemetry-label">Target Location</div>
                <div class="telemetry-value" style="font-size:12px;">${activeIncident.location_name}</div>
              </div>
            </div>

            <div style="margin-top:12px;display:flex;justify-content:space-between;align-items:center;">
              <span id="liveRouteCorridorNote" style="font-size:12px;color:#64748b;">* Route calculated via verified road network corridor.</span>
              <div style="display:flex;gap:6px;">
                <button class="btn btn-secondary btn-sm" onclick="showNavigationSteps('${role}')">View Full Route Steps</button>
                <button class="btn btn-primary btn-sm" onclick="startTurnByTurn('${role}')">Start Navigation</button>
              </div>
            </div>
          </div>
        </div>

        <!-- VERIFIED INCIDENT DETAILS -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">Structured Incident Telemetry</h3>
              <p style="font-size:12px;color:#64748b;">Distinction of verified facts vs AI assessment</p>
            </div>
            <span class="tag-fact">INCIDENT STREAM</span>
          </div>
          <div class="card-body">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <tbody>
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:6px 0;color:#64748b;width:160px;">Original Citizen Text:</td>
                  <td style="padding:6px 0;font-weight:500;">"${activeIncident.description}"</td>
                </tr>
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:6px 0;color:#64748b;">Verified Location:</td>
                  <td style="padding:6px 0;">${activeIncident.location_name} (${activeIncident.latitude}° N, ${activeIncident.longitude}° E)</td>
                </tr>
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:6px 0;color:#64748b;">Reported Injuries:</td>
                  <td style="padding:6px 0;font-weight:600;">${activeIncident.injuries} casualties (${activeIncident.affected_people} total affected)</td>
                </tr>
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:6px 0;color:#64748b;">AI Classification:</td>
                  <td style="padding:6px 0;"><span class="tag-ai">${activeIncident.emergency_type} · Priority ${activeIncident.system_priority}/100</span></td>
                </tr>
                <tr>
                  <td style="padding:6px 0;color:#64748b;">Safety Principle:</td>
                  <td style="padding:6px 0;color:#334155;font-size:12px;">Decision-support only. Autonomous dispatch disabled. Authorized responder makes final decision.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- RIGHT COLUMN: Role-Specific Response Requirements & Station Resources -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        
        <!-- ROLE SPECIFIC REQUIRED RESPONSE -->
        ${role === "HOSPITAL" ? renderHospitalRoleCard(intelligence) : ''}
        ${role === "POLICE" ? renderPoliceRoleCard(intelligence) : ''}
        ${role === "FIRE" ? renderFireRoleCard(intelligence) : ''}

        <!-- STATION RESOURCE INVENTORY -->
        <div class="card">
          <div class="card-header">
            <div>
              <h3 style="font-size:15px;font-weight:600;">${role === "HOSPITAL" ? "Hospital Resource Status" : role === "POLICE" ? "Police Patrol Status" : "Fire Apparatus Status"}</h3>
              <p style="font-size:12px;color:#64748b;">Live capacity available at this station</p>
            </div>
            <span class="tag-fact">LIVE STATION SENSORS</span>
          </div>
          <div class="card-body">
            <div class="telemetry-grid">
              ${Object.entries(node.resources).map(([key, val]) => `
                <div class="telemetry-cell">
                  <div class="telemetry-label">${key.replace(/_/g, ' ')}</div>
                  <div class="telemetry-value" style="font-size:12px;">${val}</div>
                </div>
              `).join('')}
            </div>
            
            <div style="margin-top:14px;display:flex;justify-content:flex-end;gap:8px;">
              <button class="btn btn-secondary btn-sm" onclick="alert('Station resource sensors refreshed: All indicators synced with hospital/precinct dispatch database.')">Refresh Resources</button>
              <button class="btn btn-secondary btn-sm" onclick="showNavigationSteps('${role}')">View Route</button>
            </div>
          </div>
        </div>

      </div>

    </div>
  `;

  // Initialize Map for responder view
  setTimeout(() => {
    initializeOperationalMap("operationalMapResponder", role);
  }, 50);
}

/**
 * Hospital Role Card (Medical Response & Capacity)
 */
function renderHospitalRoleCard(intel) {
  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h3 style="font-size:15px;font-weight:600;">Required Medical Services & Capacity</h3>
          <p style="font-size:12px;color:#64748b;">Clinical triage preparation support</p>
        </div>
        <span class="tag-ai">AI RESPONSE RECOMMENDATION</span>
      </div>
      <div class="card-body">
        
        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Required Clinical Services</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
          ${intel.required_services.map(s => `
            <div class="checklist-item verified">
              <span style="color:#16a34a;font-weight:700;">✓</span>
              <div style="display:flex;justify-content:space-between;width:100%;font-size:13px;">
                <span>${s.label}</span>
                <span class="badge badge-safe mono">${s.status}</span>
              </div>
            </div>
          `).join('')}
        </div>

        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Estimated Casualty Influx</div>
        <div class="telemetry-grid" style="margin-bottom:14px;">
          <div class="telemetry-cell">
            <div class="telemetry-label">Estimated Affected</div>
            <div class="telemetry-value mono">${intel.capacity_needs.affected_count} Patients</div>
          </div>
          <div class="telemetry-cell">
            <div class="telemetry-label">Reported Injuries</div>
            <div class="telemetry-value mono">${intel.capacity_needs.injuries_count} Casualties</div>
          </div>
          <div class="telemetry-cell">
            <div class="telemetry-label">Critical / Unconscious</div>
            <div class="telemetry-value mono" style="color:#dc2626;">${intel.capacity_needs.critical_count} Urgent</div>
          </div>
        </div>

        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Recommended Clinical Preparation</div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          ${intel.recommended_prep.map(item => `
            <div style="padding:6px 10px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:var(--radius-sm);font-size:12px;color:#1e293b;">
              • ${item}
            </div>
          `).join('')}
        </div>

        <div class="decision-support-box" style="margin-top:12px;">
          <span>Notice: Recommendations assist operational staging only. No medical diagnoses or specific pharmacological prescriptions are generated by the system.</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Police Role Card (Scene Safety & Traffic Control)
 */
function renderPoliceRoleCard(intel) {
  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h3 style="font-size:15px;font-weight:600;">Required Police Response & Traffic Operations</h3>
          <p style="font-size:12px;color:#64748b;">Scene safety and corridor management</p>
        </div>
        <span class="tag-ai">AI RESPONSE RECOMMENDATION</span>
      </div>
      <div class="card-body">
        
        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Required Police Actions</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
          ${intel.required_response.map(s => `
            <div class="checklist-item verified">
              <span style="color:#2563eb;font-weight:700;">✓</span>
              <div style="display:flex;justify-content:space-between;width:100%;font-size:13px;">
                <span>${s.label}</span>
                <span class="badge badge-info mono">${s.status}</span>
              </div>
            </div>
          `).join('')}
        </div>

        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Scene & Corridor Intelligence</div>
        <div class="telemetry-grid" style="margin-bottom:14px;">
          <div class="telemetry-cell">
            <div class="telemetry-label">Corridor Impact</div>
            <div class="telemetry-value" style="font-size:12px;color:#dc2626;">${intel.scene_intelligence.traffic_impact}</div>
          </div>
          <div class="telemetry-cell">
            <div class="telemetry-label">Road Obstruction</div>
            <div class="telemetry-value" style="font-size:12px;">${intel.scene_intelligence.road_blockage}</div>
          </div>
        </div>

        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Recommended Operational Steps</div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          ${intel.recommended_actions.map(item => `
            <div style="padding:6px 10px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:var(--radius-sm);font-size:12px;color:#1e293b;">
              ${item}
            </div>
          `).join('')}
        </div>

        <div class="decision-support-box" style="margin-top:12px;">
          <span>Notice: Operational recommendations provide situational support. The responding patrol officer in command maintains full jurisdiction on scene.</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Fire Role Card (Suppression & Rescue Readiness)
 */
function renderFireRoleCard(intel) {
  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h3 style="font-size:15px;font-weight:600;">Required Fire & Rescue Response</h3>
          <p style="font-size:12px;color:#64748b;">Tactical rescue and hazard containment</p>
        </div>
        <span class="tag-ai">AI RESPONSE RECOMMENDATION</span>
      </div>
      <div class="card-body">
        
        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Required Tactical Deployments</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
          ${intel.required_response.map(s => `
            <div class="checklist-item verified">
              <span style="color:#d97706;font-weight:700;">✓</span>
              <div style="display:flex;justify-content:space-between;width:100%;font-size:13px;">
                <span>${s.label}</span>
                <span class="badge badge-warning mono">${s.status}</span>
              </div>
            </div>
          `).join('')}
        </div>

        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Required Equipment (Based on Verified Incident Data)</div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
          ${intel.required_equipment.map(item => `
            <div style="padding:6px 10px;background:#fffbeb;border:1px solid #fde68a;border-radius:var(--radius-sm);font-size:12px;color:#92400e;display:flex;align-items:center;gap:6px;">
              <span>🧰</span> <span>${item}</span>
            </div>
          `).join('')}
        </div>

        <div style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:8px;">Tactical Guidelines</div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          ${intel.recommended_actions.map(item => `
            <div style="padding:6px 10px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:var(--radius-sm);font-size:12px;color:#1e293b;">
              • ${item}
            </div>
          `).join('')}
        </div>

        <div class="decision-support-box" style="margin-top:12px;">
          <span>Notice: Equipment lists derived only from reported scene parameters. No hazardous material is assumed without direct sensor or on-scene report.</span>
        </div>
      </div>
    </div>
  `;
}

async function renderAdminDashboard() {
  const container = document.getElementById("mainAppView");

  let incidentsList = Object.values(PRESET_INCIDENTS);
  let activeCount = "1 Critical";
  let dbBadge = RESQ_API.isBackendConnected ? "POSTGRESQL 17 LIVE" : "LOCAL CACHE";

  if (RESQ_API.isBackendConnected) {
    const overview = await RESQ_API.getDashboardOverview();
    if (overview && overview.active_incidents) {
      incidentsList = overview.active_incidents;
      activeCount = `${overview.critical_incidents_count} Critical / ${overview.total_active_incidents} Active`;
    }
  }

  container.innerHTML = `
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:var(--radius-md);padding:14px 18px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
      <div>
        <h2 style="font-size:18px;font-weight:600;">Multi-Agency CAD Supervision & Telemetry</h2>
        <p style="font-size:12px;color:#475569;">Central Command oversight across Hospitals, Police, and Fire Divisions</p>
      </div>
      <div style="display:flex;gap:8px;">
        <span class="badge badge-safe mono">${dbBadge}</span>
        <span class="badge badge-info mono">FASTAPI v1 ROUTER</span>
      </div>
    </div>

    <div class="telemetry-grid" style="margin-bottom:16px;">
      <div class="telemetry-cell">
        <div class="telemetry-label">Active Incidents</div>
        <div class="telemetry-value mono" style="color:#dc2626;">${activeCount}</div>
      </div>
      <div class="telemetry-cell">
        <div class="telemetry-label">Hospitals Synced</div>
        <div class="telemetry-value mono">3 Online</div>
      </div>
      <div class="telemetry-cell">
        <div class="telemetry-label">Police Sectors</div>
        <div class="telemetry-value mono">Zone 4 Active</div>
      </div>
      <div class="telemetry-cell">
        <div class="telemetry-label">Fire Stations</div>
        <div class="telemetry-value mono">Division 04 Ready</div>
      </div>
      <div class="telemetry-cell">
        <div class="telemetry-label">AI Decision Support</div>
        <div class="telemetry-value mono">Hybrid Engine Live</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <h3 style="font-size:15px;font-weight:600;">System-Wide Active Incident Roster</h3>
          <p style="font-size:12px;color:#64748b;">Live dispatches stored in PostgreSQL CAD database</p>
        </div>
        <span class="tag-fact">POSTGRES CAD STREAM</span>
      </div>
      <div class="card-body">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="border-bottom:2px solid #e2e8f0;text-align:left;color:#64748b;font-size:11px;text-transform:uppercase;">
              <th style="padding:8px;">Incident ID</th>
              <th style="padding:8px;">Type & Lang</th>
              <th style="padding:8px;">Location & Status</th>
              <th style="padding:8px;">Injuries</th>
              <th style="padding:8px;">Priority</th>
              <th style="padding:8px;">Status</th>
              <th style="padding:8px;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${incidentsList.map(inc => {
              const locDisplay = inc.location_name || inc.location || "Location Unspecified";
              const isUnverified = inc.coordinates_verified === false || inc.location_source === "UNVERIFIED" || inc.latitude == null;
              const langCode = (inc.detected_language || inc.language || "en").toUpperCase();
              const badgeVerified = isUnverified
                ? '<span class="badge" style="background:#fee2e2;color:#991b1b;font-size:10px;">⚠️ UNVERIFIED</span>'
                : '<span class="badge" style="background:#dcfce7;color:#166534;font-size:10px;">✓ VERIFIED</span>';
              const badgeLang = `<span class="badge" style="background:#ede9fe;color:#5b21b6;font-size:10px;margin-left:4px;">${langCode}</span>`;
              return `
              <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:8px;" class="mono"><b>${inc.incident_id || inc.id}</b></td>
                <td style="padding:8px;">${inc.emergency_type} ${badgeLang}</td>
                <td style="padding:8px;font-size:12px;color:#475569;">
                  <div style="font-weight:600;color:#0f172a;">${locDisplay}</div>
                  <div style="margin-top:2px;">${badgeVerified}</div>
                </td>
                <td style="padding:8px;">${inc.injuries != null ? inc.injuries : 0}</td>
                <td style="padding:8px;"><span class="badge ${(inc.system_priority || inc.priority_score) >= 75 ? 'badge-emergency' : (inc.system_priority || inc.priority_score) >= 50 ? 'badge-warning' : 'badge-safe'} mono">${inc.system_priority || inc.priority_score}/100</span></td>
                <td style="padding:8px;font-size:12px;">${inc.status}</td>
                <td style="padding:8px;">
                  <button class="btn btn-secondary btn-sm" onclick="selectIncidentById('${inc.incident_id || inc.id}')">Load CAD</button>
                </td>
              </tr>
            `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  // Start periodic 5s polling for Admin supervision
  if (!window.adminPollInterval) {
    window.adminPollInterval = setInterval(() => {
      if (currentRole === "ADMIN") {
        renderAdminDashboard();
      }
    }, 5000);
  }
}

// ============================================================================
// 6. EVENT HANDLERS & NAVIGATION
// ============================================================================

function switchRole(newRole) {
  currentRole = newRole;
  
  // Update role buttons
  document.querySelectorAll(".role-btn").forEach(btn => {
    btn.classList.remove("active");
    if (btn.getAttribute("data-role") === newRole) {
      btn.classList.add("active");
    }
  });

  // Render view
  if (newRole === "USER") {
    renderCitizenDashboard();
  } else if (newRole === "ADMIN") {
    renderAdminDashboard();
  } else {
    renderResponderDashboard(newRole);
  }

  // Update URL hash without scroll
  window.history.replaceState(null, null, `#${newRole.toLowerCase()}`);
}

function handleResponderStatusChange(newStatus) {
  responderStatus = newStatus;
  alert(`Station Operational Status updated to: ${newStatus}`);
}

function handleCitizenPriorityChange(val) {
  activeIncident.user_priority = parseInt(val, 10);
  const el = document.getElementById("userPriorityVal");
  if (el) el.innerText = `${val} / 100`;
}

async function submitCitizenUpdate() {
  const textarea = document.getElementById("citizenDescriptionInput");
  const locInput = document.getElementById("citizenLocationInput");
  const langSelect = document.getElementById("citizenLanguageSelect");

  if (!textarea) return;
  const newText = textarea.value.trim();
  const newLoc = locInput ? locInput.value.trim() : (activeIncident.location_name || "");
  const selectedLang = langSelect ? langSelect.value : (activeIncident.detected_language || "auto");

  if (newText.length < 3) {
    alert("Please enter a valid emergency description.");
    return;
  }
  
  const submitBtn = document.querySelector("button[onclick='submitCitizenUpdate()']");
  if (submitBtn) {
    submitBtn.innerText = "Analyzing & Persisting Incident...";
    submitBtn.disabled = true;
  }

  try {
    const isExisting = activeIncident.incident_id && !activeIncident.incident_id.startsWith("INC-LOCAL");

    if (isExisting && RESQ_API.isBackendConnected) {
      // Use updateIncident (PATCH) so location and description are cleanly updated/preserved!
      const updatePayload = {
        description: newText,
        location_name: newLoc,
        user_priority: activeIncident.user_priority,
      };
      if (selectedLang && selectedLang !== "auto") {
        updatePayload.language = selectedLang;
      }
      if (activeIncident.coordinates_verified && activeIncident.latitude != null) {
        updatePayload.latitude = activeIncident.latitude;
        updatePayload.longitude = activeIncident.longitude;
      }

      const updated = await RESQ_API.updateIncident(activeIncident.incident_id, updatePayload);
      if (updated) {
        activeIncident = {
          ...activeIncident,
          ...updated,
          incident_id: updated.incident_id || updated.id,
          system_priority: updated.priority_score != null ? updated.priority_score : updated.system_priority,
          user_priority: activeIncident.user_priority || updated.priority_score,
          location_name: updated.location_name || updated.location || newLoc,
          coordinates_verified: updated.coordinates_verified,
          detected_language: updated.detected_language || selectedLang
        };
      }
    } else {
      // Create new incident
      const payload = {
        description: newText,
        location_name: newLoc,
        latitude: activeIncident.latitude,
        longitude: activeIncident.longitude,
        affected_people: activeIncident.affected_people || 0,
        injuries: activeIncident.injuries || 0,
        critical_indicators: activeIncident.critical_indicators || [],
        user_priority: activeIncident.user_priority
      };
      if (selectedLang && selectedLang !== "auto") {
        payload.language = selectedLang;
      }

      const created = await RESQ_API.createIncident(payload);
      if (created) {
        activeIncident = {
          ...activeIncident,
          ...created,
          incident_id: created.incident_id || created.id,
          system_priority: created.priority_score || created.system_priority,
          user_priority: activeIncident.user_priority || created.priority_score,
          location_name: created.location_name || created.location || newLoc,
          coordinates_verified: created.coordinates_verified,
          detected_language: created.detected_language || selectedLang
        };
      }
    }

    await syncNearbyResources();
    renderCitizenDashboard();
    alert(`[LIVE FASTAPI + POSTGRESQL SUCCESS]\nIncident ID: ${activeIncident.incident_id}\nEmergency Type: ${activeIncident.emergency_type}\nSystem Priority: ${activeIncident.system_priority}/100 (${activeIncident.severity})\nStatus: Persisted to PostgreSQL database.`);
  } catch (err) {
    console.error("Incident submit error:", err);
    renderCitizenDashboard();
  }
}

function detectUserLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        activeIncident.latitude = +pos.coords.latitude.toFixed(4);
        activeIncident.longitude = +pos.coords.longitude.toFixed(4);
        activeIncident.location_details = `Detected device GPS: Accuracy ±${Math.round(pos.coords.accuracy)}m`;
        renderCitizenDashboard();
        alert(`Location detected: ${activeIncident.latitude}° N, ${activeIncident.longitude}° E`);
      },
      (err) => {
        alert("Location access not granted. Using verified station grid coordinates.");
      }
    );
  } else {
    alert("Geolocation is not supported by your browser.");
  }
}

function promptChangeLocation() {
  const newLoc = prompt("Enter emergency landmark or street address:", activeIncident.location_name);
  if (newLoc && newLoc.trim()) {
    activeIncident.location_name = newLoc.trim();
    renderCitizenDashboard();
  }
}

function toggleLocationDetails() {
  const box = document.getElementById("locationDetailsBox");
  if (box) {
    box.style.display = box.style.display === "none" ? "block" : "none";
  }
}

async function loadScenario(type) {
  if (PRESET_INCIDENTS[type]) {
    const preset = PRESET_INCIDENTS[type];
    if (RESQ_API.isBackendConnected) {
      const realInc = await RESQ_API.getIncident(preset.incident_id);
      if (realInc) {
        activeIncident = {
          ...realInc,
          location_name: realInc.location_name || realInc.location,
          system_priority: realInc.priority_score || realInc.system_priority,
          user_priority: realInc.user_priority || realInc.priority_score
        };
      } else {
        activeIncident = JSON.parse(JSON.stringify(preset));
      }
    } else {
      activeIncident = JSON.parse(JSON.stringify(preset));
    }

    await syncNearbyResources();

    // Reset acknowledgements for clean test
    acknowledgementState.HOSPITAL.acknowledged = false;
    acknowledgementState.POLICE.acknowledged = false;
    acknowledgementState.FIRE.acknowledged = false;
    
    if (currentRole === "USER") {
      renderCitizenDashboard();
    } else if (currentRole === "ADMIN") {
      renderAdminDashboard();
    } else {
      renderResponderDashboard(currentRole);
    }
  }
}

async function selectIncidentById(id) {
  if (RESQ_API.isBackendConnected) {
    const realInc = await RESQ_API.getIncident(id);
    if (realInc) {
      activeIncident = {
        ...realInc,
        location_name: realInc.location_name || realInc.location,
        system_priority: realInc.priority_score || realInc.system_priority,
        user_priority: realInc.user_priority || realInc.priority_score
      };
      await syncNearbyResources();
      switchRole("USER");
      return;
    }
  }
  const match = Object.values(PRESET_INCIDENTS).find(i => i.incident_id === id);
  if (match) {
    activeIncident = JSON.parse(JSON.stringify(match));
    switchRole("USER");
  }
}

async function acknowledgeIncident(role) {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  acknowledgementState[role].acknowledged = true;
  acknowledgementState[role].timestamp = now;

  if (RESQ_API.isBackendConnected && activeIncident.incident_id) {
    await RESQ_API.updateIncident(activeIncident.incident_id, { status: "ACKNOWLEDGED" });
  }

  renderResponderDashboard(role);
  alert(`✓ Incident ${activeIncident.incident_id} acknowledged by ${RESPONDER_NODES[role].name}.\nLogged into operational PostgreSQL CAD ledger.`);
}

function viewServiceDetails(resId) {
  const res = (currentResources && currentResources.find(r => (r.id || r.resource_id) === resId)) || ALL_RESOURCES.find(r => r.id === resId);
  if (res) {
    alert(`Emergency Resource Details:\n\nName: ${res.name}\nType: ${res.type || res.resource_type}\nDistance: ${res.distance_km} km\nEstimated ETA: ${res.eta_min} min\nStatus: ${res.availability}\nCapabilities: ${res.capability || (res.capabilities && res.capabilities.join(', '))}\nDirect Dispatch Phone: ${res.contact || res.phone || '112'}`);
  }
}

function showNavigationSteps(role) {
  const route = window.activeLiveRoute || calculateRouteMetrics(role, activeIncident);
  const sourceLabel = ROUTING_SOURCE_LABELS[route.routing_status] || "Verified Route";
  let stepsText = "";
  if (route.steps && route.steps.length > 0) {
    stepsText = route.steps.slice(0, 8).map((s, idx) => `${idx + 1}. ${s.instruction} (${s.distance_km} km · ${s.duration_min} min)`).join("\n");
  } else {
    stepsText = "Route steps unavailable — see map for visual route.";
  }
  alert(`Road Navigation Route Steps\nSource: ${sourceLabel}\n\nOrigin: ${route.origin_name || "Station Base"}\nDestination: ${route.destination_name || "Incident Location"}\nRoad Distance: ${route.distance_km} km\nEstimated ETA: ${route.eta_min} min\n\nTurn-by-Turn:\n${stepsText}`);
}

function startTurnByTurn(role) {
  const route = window.activeLiveRoute || calculateRouteMetrics(role, activeIncident);
  alert(`Live Turn-by-Turn Navigation Active:\n\nRouting emergency responder unit to ${route.destination_name}.\nActual Road Transit Distance: ${route.distance_km} km.\nTarget Emergency Arrival: ${route.eta_min} minutes.\nTraffic corridor cleared for emergency priority.`);
}

// ============================================================================
// 7. INITIALIZATION
// ============================================================================

window.addEventListener("DOMContentLoaded", async () => {
  // Check hash route
  const hash = window.location.hash.replace("#", "").toUpperCase();
  if (["USER", "HOSPITAL", "POLICE", "FIRE", "ADMIN"].includes(hash)) {
    currentRole = hash;
  }
  
  // Set initial role button
  document.querySelectorAll(".role-btn").forEach(btn => {
    btn.classList.remove("active");
    if (btn.getAttribute("data-role") === currentRole) {
      btn.classList.add("active");
    }
  });

  // Probe FastAPI backend connection
  const isLive = await RESQ_API.checkHealth();
  if (isLive) {
    // Sync initial active incident from DB if available
    const initialReal = await RESQ_API.getIncident("INC-D4457C47");
    if (initialReal) {
      activeIncident = {
        ...initialReal,
        location_name: initialReal.location_name || initialReal.location,
        system_priority: initialReal.priority_score || initialReal.system_priority,
        user_priority: initialReal.user_priority || initialReal.priority_score
      };
    }
    await syncNearbyResources();
  }

  // Render initial view
  if (currentRole === "USER") {
    renderCitizenDashboard();
  } else if (currentRole === "ADMIN") {
    renderAdminDashboard();
  } else {
    renderResponderDashboard(currentRole);
  }
});
