"""
Seed script for RESQ.AI Emergency Intelligence & Response System
Populates verified emergency resources, responder nodes, users, and baseline incidents.
"""

from app.db.session import SessionLocal
from app.models.user import User
from app.models.incident import EmergencyReport
from app.models.ai_extraction import AIExtraction
from app.models.severity_assessment import SeverityAssessment
from app.models.resource import EmergencyResource, ResourceAvailability
from app.models.recommendation import ResponseRecommendation


def seed_database():
    db = SessionLocal()
    try:
        # 1. Seed Users
        users_data = [
            {"name": "Citizen User", "email": "citizen@resq.ai", "role": "USER"},
            {"name": "Dr. V. Rao (Lead Triage)", "email": "triage@citycare.resq.ai", "role": "HOSPITAL"},
            {"name": "Insp. M. Kumar (Patrol Command)", "email": "cad@indiranagar.police.resq.ai", "role": "POLICE"},
            {"name": "Capt. S. Sharma (Station Commander)", "email": "commander@fire04.resq.ai", "role": "FIRE"},
            {"name": "CAD Admin Supervisor", "email": "admin@resq.ai", "role": "ADMIN"},
        ]

        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                db.add(User(**u))

        # 2. Seed Emergency Resources
        resources_data = [
            {
                "id": "RES-H1",
                "name": "City Care Hospital",
                "resource_type": "HOSPITAL",
                "latitude": 12.9550,
                "longitude": 77.6500,
                "address": "Old Airport Road, Kodihalli, Bengaluru",
                "phone": "+91 80 2520 1100",
                "capabilities": ["Trauma Care Level-1", "ICU Beds Ready", "Resuscitation Bay", "Ambulance Receiving Ramp"],
                "availability": {
                    "available_units": 6,
                    "wait_time": 0,
                    "status": "AVAILABLE",
                    "operational_details": {
                        "emergency_dept": "Available (Level-1 Triage Ready)",
                        "icu_beds": "6 Available of 20",
                        "general_beds": "18 Available",
                        "ambulances": "2 ALS Units Ready on Bay",
                        "trauma_team": "Alpha Surgical Team On Duty"
                    }
                }
            },
            {
                "id": "RES-H2",
                "name": "Manipal Hospital HAL",
                "resource_type": "HOSPITAL",
                "latitude": 12.9580,
                "longitude": 77.6490,
                "address": "98, HAL Old Airport Rd, Bengaluru",
                "phone": "+91 80 2502 4444",
                "capabilities": ["Multi-Speciality", "Emergency Surgery On Call", "CT Scan Ready", "Burn Unit"],
                "availability": {
                    "available_units": 4,
                    "wait_time": 5,
                    "status": "AVAILABLE",
                    "operational_details": {
                        "emergency_dept": "Trauma Department Available",
                        "icu_beds": "4 Available of 16",
                        "general_beds": "12 Available"
                    }
                }
            },
            {
                "id": "RES-H3",
                "name": "Sakra World Hospital",
                "resource_type": "HOSPITAL",
                "latitude": 12.9288,
                "longitude": 77.6833,
                "address": "Outer Ring Road, Devarabeesanahalli, Bellandur, Bengaluru",
                "phone": "+91 80 4969 4969",
                "capabilities": ["Advanced Cardiac Wing", "Neurotrauma Bay", "Emergency Cath Lab"],
                "availability": {
                    "available_units": 2,
                    "wait_time": 10,
                    "status": "AVAILABLE",
                    "operational_details": {
                        "emergency_dept": "Limited ICU Beds",
                        "icu_beds": "2 Available of 12",
                        "general_beds": "8 Available"
                    }
                }
            },
            {
                "id": "RES-A1",
                "name": "Ambulance A-12 (ALS Unit)",
                "resource_type": "AMBULANCE",
                "latitude": 12.9420,
                "longitude": 77.6750,
                "address": "Marathahalli Fast-Response Corridor Staging Bay",
                "phone": "108",
                "capabilities": ["Advanced Life Support", "Defibrillator", "Oxygen", "Spine Board", "Paramedic Onboard"],
                "availability": {
                    "available_units": 1,
                    "wait_time": 2,
                    "status": "AVAILABLE",
                    "operational_details": {"type": "ALS", "crew": 2, "readiness": "Immediate Staging"}
                }
            },
            {
                "id": "RES-A2",
                "name": "Ambulance B-04 (BLS Unit)",
                "resource_type": "AMBULANCE",
                "latitude": 12.9610,
                "longitude": 77.6600,
                "address": "Domlur Flyover Response Bay",
                "phone": "108",
                "capabilities": ["Basic Life Support", "Oxygen", "Spinal Board", "Stretcher"],
                "availability": {
                    "available_units": 1,
                    "wait_time": 4,
                    "status": "AVAILABLE",
                    "operational_details": {"type": "BLS", "crew": 2, "readiness": "Available"}
                }
            },
            {
                "id": "RES-P1",
                "name": "Indiranagar Police Station",
                "resource_type": "POLICE",
                "latitude": 12.9780,
                "longitude": 77.6400,
                "address": "100ft Road, Indiranagar, Bengaluru",
                "phone": "100 / +91 80 2294 2522",
                "capabilities": ["Traffic Management", "Scene Perimeter Security", "Corridor Clear Squad", "Drone Recon"],
                "availability": {
                    "available_units": 2,
                    "wait_time": 2,
                    "status": "AVAILABLE",
                    "operational_details": {
                        "patrol_units": "Patrol-14 (Available), Patrol-08 (Standby)",
                        "traffic_squad": "Traffic Control Unit 3 Ready",
                        "barricades": "Corridor cones and diversions staged",
                        "duty_officer": "Insp. M. Kumar (On Duty)"
                    }
                }
            },
            {
                "id": "RES-P2",
                "name": "HAL Police Station",
                "resource_type": "POLICE",
                "latitude": 12.9530,
                "longitude": 77.6620,
                "address": "Airport Road, HAL Post, Bengaluru",
                "phone": "100 / +91 80 2294 2530",
                "capabilities": ["Corridor Patrol", "Road Diversion Support", "Rapid Intervention"],
                "availability": {
                    "available_units": 1,
                    "wait_time": 5,
                    "status": "AVAILABLE",
                    "operational_details": {"patrol_units": "Patrol-08 Ready", "duty_officer": "Sub-Insp. S. Patil"}
                }
            },
            {
                "id": "RES-F1",
                "name": "Central Fire & Rescue Station #04",
                "resource_type": "FIRE",
                "latitude": 12.9650,
                "longitude": 77.6000,
                "address": "HAL 2nd Stage, Domlur, Bengaluru",
                "phone": "101 / +91 80 2297 1500",
                "capabilities": ["Heavy Rescue Tender HR-04", "Hydraulic Cutter/Spreader", "Thermal Imaging", "AFFF Foam"],
                "availability": {
                    "available_units": 1,
                    "wait_time": 3,
                    "status": "AVAILABLE",
                    "operational_details": {
                        "tenders": "Heavy Rescue Tender HR-04 (Ready)",
                        "crew": "6 Firefighters on Active Duty",
                        "extrication": "Hydraulic Cutter/Spreader Kit Ready",
                        "water_foam": "4,500 L Water / 500 L AFFF Foam"
                    }
                }
            },
            {
                "id": "RES-F2",
                "name": "Sarjapur Fire Sub-Station",
                "resource_type": "FIRE",
                "latitude": 12.9150,
                "longitude": 77.6850,
                "address": "Sarjapur Road, Kaikondrahalli, Bengaluru",
                "phone": "101 / +91 80 2297 1550",
                "capabilities": ["Water Bowser", "Rapid Response Tender", "Chemical Extinguisher"],
                "availability": {
                    "available_units": 1,
                    "wait_time": 6,
                    "status": "AVAILABLE",
                    "operational_details": {"tenders": "Water Bowser Ready", "crew": "4 Firefighters"}
                }
            }
        ]

        for res_item in resources_data:
            existing_res = db.query(EmergencyResource).filter(EmergencyResource.id == res_item["id"]).first()
            avail_data = res_item.pop("availability")
            if not existing_res:
                new_res = EmergencyResource(**res_item)
                db.add(new_res)
                db.flush()
                new_avail = ResourceAvailability(resource_id=new_res.id, **avail_data)
                db.add(new_avail)
            else:
                # Update existing
                for k, v in res_item.items():
                    setattr(existing_res, k, v)
                if existing_res.availability:
                    for ak, av in avail_data.items():
                        setattr(existing_res.availability, ak, av)
                else:
                    new_avail = ResourceAvailability(resource_id=existing_res.id, **avail_data)
                    db.add(new_avail)

        # 3. Seed Preset Incidents
        preset_incidents = [
            {
                "id": "INC-D4457C47",
                "description": "Major accident near highway. Three people injured and one person is unconscious.",
                "location": "Outer Ring Road, KM 14.2 Southbound, Bengaluru",
                "latitude": 12.9352,
                "longitude": 77.6944,
                "affected_people": 3,
                "injuries": 3,
                "status": "REPORTED",
                "source": "USER",
                "extraction": {
                    "emergency_type": "Major Road Accident",
                    "affected_people": 3,
                    "injuries": 3,
                    "critical_indicators": ["Unconscious casualty reported", "Multi-vehicle collision", "Highway corridor lane blockage"],
                    "location_information": "Outer Ring Road, KM 14.2 Southbound near Kadubeesanahalli Flyover",
                },
                "assessment": {
                    "severity": "CRITICAL",
                    "priority_score": 82.0,
                    "factors": ["Unconscious casualty (+35)", "Multi-vehicle highway accident (+20)", "3 Reported injuries (+27)"],
                },
                "recommendation": {
                    "role": "ALL",
                    "summary": "High-priority multi-vehicle collision with critical unconscious casualty on arterial corridor.",
                    "recommendation": "Immediate Level-1 trauma surgical staging, rapid corridor traffic clearance, and heavy rescue extrication standby.",
                    "precautions": [
                        "Do not move unconscious casualties unless immediate fire or explosion hazard exists.",
                        "Stay behind the safety barrier away from moving highway traffic.",
                        "Turn on vehicle hazard warning blinkers if safely accessible.",
                        "Keep the right emergency lane unobstructed for incoming ALS ambulances.",
                        "Do not offer water or fluids to unconscious or semi-conscious persons."
                    ],
                    "operational_checklist": [
                        "Hospital: Reserve Trauma Resuscitation Bay 1 & Alert surgical on-call team.",
                        "Police: Dispatch Patrol-14 to divert traffic at Kadubeesanahalli exit ramp.",
                        "Fire: Stage Hydraulic Cutter Tender HR-04 for potential vehicle pinch extrication."
                    ],
                    "missing_information": ["Vehicle fuel leak status unconfirmed", "Casualty age demographics unconfirmed"]
                }
            },
            {
                "id": "INC-F8902A11",
                "description": "Dense smoke billowing from 2nd floor commercial kitchen. Two staff members trapped in rear corridor.",
                "location": "100ft Road, Indiranagar, Bengaluru",
                "latitude": 12.9784,
                "longitude": 77.6408,
                "affected_people": 2,
                "injuries": 1,
                "status": "REPORTED",
                "source": "USER",
                "extraction": {
                    "emergency_type": "Commercial Building Fire",
                    "affected_people": 2,
                    "injuries": 1,
                    "critical_indicators": ["Dense smoke condition", "Occupants trapped in rear corridor", "Kitchen gas cylinders present"],
                    "location_information": "100ft Road, Indiranagar, Commercial Complex 2nd Floor",
                },
                "assessment": {
                    "severity": "CRITICAL",
                    "priority_score": 79.0,
                    "factors": ["Trapped occupants (+30)", "Active commercial fire (+30)", "Burn/smoke injury reported (+19)"],
                },
                "recommendation": {
                    "role": "ALL",
                    "summary": "Commercial kitchen fire with trapped personnel and gas cylinder explosion risk.",
                    "recommendation": "Deploy structural fire suppression with SCBA breathing apparatus, isolate commercial gas lines, establish triage staging on 100ft road.",
                    "precautions": [
                        "Crawl low under smoke — clean breathable air remains within 1 foot of the floor.",
                        "Do NOT use elevators under any circumstances.",
                        "Close internal doors behind you to compartmentalize fire spread.",
                        "Move across the street to an upwind location away from glass facades."
                    ],
                    "operational_checklist": [
                        "Fire: Deploy HR-04 tender with 4,500L water + AFFF foam on 2nd floor front approach.",
                        "Police: Seal 100ft road between 12th Main and 80ft road intersection.",
                        "Hospital: Standby for smoke inhalation & burn trauma triage."
                    ],
                    "missing_information": ["Main gas manifold shutoff location", "Building occupancy count on upper floors"]
                }
            },
            {
                "id": "INC-W3320B94",
                "description": "Severe waterlogging in underpass. Vehicle stalled in 3-foot rising water, 2 occupants safe on vehicle roof.",
                "location": "Marathahalli Underpass, Bengaluru",
                "latitude": 12.9562,
                "longitude": 77.7011,
                "affected_people": 2,
                "injuries": 0,
                "status": "REPORTED",
                "source": "USER",
                "extraction": {
                    "emergency_type": "Urban Flash Flood & Vehicle Stall",
                    "affected_people": 2,
                    "injuries": 0,
                    "critical_indicators": ["Rising water level in underpass", "Passengers waiting on car roof", "Roadway impassable"],
                    "location_information": "Eastbound underpass lane submerged",
                },
                "assessment": {
                    "severity": "MODERATE",
                    "priority_score": 48.0,
                    "factors": ["Submerged vehicle (+25)", "Rising water level (+15)", "2 stranded occupants (+8)"],
                },
                "recommendation": {
                    "role": "ALL",
                    "summary": "Flash flood underpass submersion with stranded passengers on vehicle roof.",
                    "recommendation": "Deploy inflatable rescue dinghy/wading team, close underpass approaches, stage tow recovery.",
                    "precautions": [
                        "Do NOT attempt to walk through submerged flowing flood water.",
                        "Beware of hidden open manholes and submerged electric wiring.",
                        "Stay on top of stable roof elevation until rescue team secures safety lines."
                    ],
                    "operational_checklist": [
                        "Police: Place high-water barricades at both entrances of Marathahalli underpass.",
                        "Fire: Deploy rescue boat/wading crew with life jackets."
                    ],
                    "missing_information": ["Current rate of water level rise in inches/hr"]
                }
            },
            {
                "id": "INC-M6012E55",
                "description": "Elderly resident collapsed in apartment lobby. Unresponsive, bystander CPR initiated.",
                "location": "Sobha Jasmine, Green Glen Layout, Bellandur",
                "latitude": 12.9279,
                "longitude": 77.6710,
                "affected_people": 1,
                "injuries": 1,
                "status": "REPORTED",
                "source": "USER",
                "extraction": {
                    "emergency_type": "Cardiac / Acute Medical Crisis",
                    "affected_people": 1,
                    "injuries": 1,
                    "critical_indicators": ["Unresponsive casualty", "CPR in progress", "Immediate ALS defibrillator needed"],
                    "location_information": "Tower B, Ground Floor Lobby",
                },
                "assessment": {
                    "severity": "CRITICAL",
                    "priority_score": 88.0,
                    "factors": ["Unresponsive/Cardiac arrest (+35)", "CPR in progress (+35)", "Single high-acuity casualty (+18)"],
                },
                "recommendation": {
                    "role": "ALL",
                    "summary": "Out-of-hospital cardiac arrest with ongoing bystander CPR.",
                    "recommendation": "Dispatch ALS unit A-12 with automated defibrillator immediately; prep resuscitation bay at Sakra Hospital.",
                    "precautions": [
                        "Continue chest compressions without interruption (100–120 beats per minute).",
                        "Push hard and fast in the center of the chest.",
                        "Send someone to fetch the nearest automated external defibrillator (AED) in the clubhouse.",
                        "Keep front gate clear for the incoming ambulance."
                    ],
                    "operational_checklist": [
                        "Ambulance: Dispatch A-12 ALS unit with defibrillator priority corridor.",
                        "Hospital: Prepare cardiac cath lab and resuscitation team."
                    ],
                    "missing_information": ["Time since initial collapse", "AED availability on site"]
                }
            },
            {
                "id": "INC-L1042Z08",
                "description": "Minor vehicle scratch at low speed parking exit. No injuries, both drivers exchanging details.",
                "location": "Sarjapur Road, Near Total Mall",
                "latitude": 12.9234,
                "longitude": 77.6811,
                "affected_people": 0,
                "injuries": 0,
                "status": "RESOLVED",
                "source": "USER",
                "extraction": {
                    "emergency_type": "Minor Fender Bender / Safe",
                    "affected_people": 0,
                    "injuries": 0,
                    "critical_indicators": ["No injuries", "No lane obstruction", "Vehicles drivable"],
                    "location_information": "Parking gate #2 exit",
                },
                "assessment": {
                    "severity": "LOW",
                    "priority_score": 18.0,
                    "factors": ["Zero injuries", "Minor property damage only", "Safe location"],
                },
                "recommendation": {
                    "role": "ALL",
                    "summary": "Non-emergency minor traffic incident without injuries or obstruction.",
                    "recommendation": "Exchange vehicle insurance details; file online e-FIR if needed; no active emergency dispatch required.",
                    "precautions": [
                        "Move vehicles out of the active lane to avoid blocking other drivers.",
                        "Photograph damage before moving vehicles.",
                        "Exchange insurance and contact numbers calmly."
                    ],
                    "operational_checklist": [
                        "No emergency dispatch required.",
                        "Log into non-emergency CAD record."
                    ],
                    "missing_information": []
                }
            }
        ]

        for inc_item in preset_incidents:
            existing_inc = db.query(EmergencyReport).filter(EmergencyReport.id == inc_item["id"]).first()
            ext_data = inc_item.pop("extraction")
            ass_data = inc_item.pop("assessment")
            rec_data = inc_item.pop("recommendation")

            if not existing_inc:
                new_inc = EmergencyReport(**inc_item)
                db.add(new_inc)
                db.flush()

                new_ext = AIExtraction(incident_id=new_inc.id, **ext_data)
                new_ass = SeverityAssessment(incident_id=new_inc.id, **ass_data)
                new_rec = ResponseRecommendation(incident_id=new_inc.id, **rec_data)
                db.add_all([new_ext, new_ass, new_rec])
            else:
                for k, v in inc_item.items():
                    setattr(existing_inc, k, v)

        db.commit()
        print("[SUCCESS] Successfully seeded verified resources, responder nodes, users, and baseline incidents into PostgreSQL!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
