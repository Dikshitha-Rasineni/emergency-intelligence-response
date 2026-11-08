"""
Demo knowledge base for RESQ.AI's RAG layer.

These documents are a compiled summary of widely taught first-aid and public-safety practice, written
for this student project. They are NOT an official SOP of any agency. Replace them with your state's
approved SOPs (Admin console -> Knowledge) before any real use. India helplines: 112 (all emergencies),
108 (ambulance), 101 (fire), 100 (police).
"""
from __future__ import annotations

PUBLISHER = "RESQ.AI demo knowledge base (general first-aid practice, not an official SOP)"

DOCS = [
    ("Road traffic collision: scene safety and casualty care", ["road_accident", "rescue", "medical"], """
Make the scene safe first. Park the emergency vehicle to shield the crash site, switch on warning lights and set up cones or warning triangles well before the scene. Keep bystanders and traffic away from the wreck.

Check the crashed vehicle for danger: leaking fuel, smoke, fire and an unstable vehicle. If it is safe, switch off the ignition and apply the hand brake. Keep clear of the path of any airbag that has not deployed.

Assume a head, neck or spine injury in any high-speed crash, rollover or impact against a fixed object such as a pole or tree. Do not move the casualty unless there is immediate danger such as fire. Support the head in line with the body. Do not remove a motorcyclist's helmet unless the airway cannot be managed otherwise and a trained person does it.

Check responsiveness and breathing. An unconscious driver slumped forward may have a blocked airway: open it with a jaw thrust, keeping the neck still. Control severe bleeding with firm direct pressure using a clean pad. Keep the casualty warm and talk to them even if they do not respond.

A person trapped in a vehicle needs fire and rescue extrication. Stabilise the vehicle before anyone enters it, disconnect the battery if trained to do so, and manage broken glass. The ambulance crew should prepare spinal immobilisation, oxygen and a trauma bay at the receiving hospital.

Members of the public: call 112 or 108, give the exact location and the number of people hurt, do not stand in moving traffic, do not move the injured person unless there is fire, do not give them food or water, and press firmly on any heavy bleeding with a clean cloth.
"""),
    ("Unconscious or not breathing: basic life support", ["medical", "road_accident"], """
Check if the person responds: speak loudly and tap their shoulders. If there is no response, shout for help and call 108 or 112. Put the phone on speaker so the call-taker can guide you.

Open the airway by tilting the head back and lifting the chin. If a neck injury is possible, lift the jaw without tilting the head. Look, listen and feel for normal breathing for no more than 10 seconds.

If the person is not breathing normally, start chest compressions: hands in the centre of the chest, push hard and fast, about 5 to 6 cm deep, at 100 to 120 compressions a minute. If trained, give 2 rescue breaths after every 30 compressions. Use an AED as soon as one arrives and follow its voice prompts.

If the person is breathing and there is no suspected spine injury, turn them onto their side in the recovery position so the airway stays open. Keep checking their breathing until help takes over.
"""),
    ("Fire in a building or vehicle", ["fire"], """
Get everyone out and stay out. Close doors behind you to slow the fire. If there is smoke, stay low where the air is cleaner. Do not use lifts. Call 101 or 112 from a safe place and tell them if anyone is still inside.

If clothes catch fire: stop, drop to the ground, cover the face and roll. Cool a burn under cool running water for 20 minutes. Do not put ice, butter or toothpaste on a burn and do not pull off clothing stuck to the skin.

For a vehicle fire, move far away from the vehicle and keep others back: tyres, fuel tanks and gas cylinders can burst. Do not open the bonnet.

Fire and rescue crews: size up the scene, set a safety perimeter, search for trapped people, locate and cool gas cylinders, and request ambulance support for smoke inhalation and burn casualties.
"""),
    ("LPG or gas leak", ["gas_leak", "fire"], """
If you smell gas, do not switch any electrical device on or off, do not light a flame and do not use a phone near the leak. Turn off the cylinder regulator if it is safe to reach. Open doors and windows and get everyone outside.

Call 101 or 112 from outside, away from the building. Do not go back in until the fire service says it is safe.

Responders: approach from upwind, eliminate ignition sources, ventilate the area, isolate the gas supply, and treat anyone with dizziness, headache or breathing difficulty as possible gas exposure.
"""),
    ("Flooding and water rescue", ["flood", "rescue"], """
Move to higher ground immediately. Do not walk through moving water: 15 cm of fast water can knock an adult over. Do not drive into flood water: 60 cm of water can float a car.

Switch off the mains electricity only if it is safe and dry to do so. Stay away from fallen power lines and electrical equipment in water. Keep children and the elderly together and ready to leave.

Responders: bring life jackets, throw lines and a boat for water rescue, check for people stranded on roofs and in vehicles, and coordinate evacuation and relief camps with disaster management.
"""),
    ("Building or structure collapse", ["structural_collapse", "rescue"], """
If you can leave safely, get out and move away from the structure; more parts may fall. Do not re-enter to look for belongings.

If you are trapped, cover your mouth with cloth against dust, do not light a match, and tap on a pipe or wall so rescuers can hear you. Shout only as a last resort to save energy.

Responders: secure the scene, isolate gas and electricity, call specialist search and rescue teams, do not climb on unstable debris, and set up a casualty collection point with ambulance support.
"""),
]


def seed_knowledge(db) -> int:
    """Insert the demo guidance once (idempotent by title). Returns how many documents were added."""
    from app.models.operations import KnowledgeDocument
    from app.services.rag_service import RagService
    added = 0
    for title, cats, body in DOCS:
        if db.query(KnowledgeDocument).filter(KnowledgeDocument.title == title).first():
            continue
        RagService.ingest(db, title=title, publisher=PUBLISHER, body=body.strip(), categories=cats, language="en",
                          version="demo-2026.11", approved=True, created_by="seed")
        added += 1
    db.flush()
    return added
