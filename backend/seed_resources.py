from dotenv import load_dotenv

load_dotenv()

from app.db.database import SessionLocal
from app.db.models import EmergencyResource, ResourceAvailability


resources = [
    {
        "name": "Demo City Hospital",
        "resource_type": "hospital",
        "latitude": 12.9750,
        "longitude": 77.5990,
        "address": "Demo address - Central Bengaluru",
        "contact_number": "0000000000",
        "available_units": 20,
        "status": "available",
        "wait_time_minutes": 10,
    },
    {
        "name": "Demo Emergency Ambulance Unit 01",
        "resource_type": "ambulance",
        "latitude": 12.9680,
        "longitude": 77.5900,
        "address": "Demo ambulance base",
        "contact_number": "0000000000",
        "available_units": 2,
        "status": "available",
        "wait_time_minutes": 5,
    },
    {
        "name": "Demo Fire Station",
        "resource_type": "fire_station",
        "latitude": 12.9800,
        "longitude": 77.5850,
        "address": "Demo fire station",
        "contact_number": "0000000000",
        "available_units": 3,
        "status": "available",
        "wait_time_minutes": 8,
    },
    {
        "name": "Demo Police Station",
        "resource_type": "police_station",
        "latitude": 12.9650,
        "longitude": 77.6050,
        "address": "Demo police station",
        "contact_number": "0000000000",
        "available_units": 4,
        "status": "available",
        "wait_time_minutes": 6,
    },
    {
        "name": "Demo Emergency Shelter",
        "resource_type": "shelter",
        "latitude": 12.9600,
        "longitude": 77.5800,
        "address": "Demo emergency shelter",
        "contact_number": "0000000000",
        "available_units": 50,
        "status": "available",
        "wait_time_minutes": 0,
    },
]


def seed_resources():
    db = SessionLocal()

    try:
        existing = db.query(EmergencyResource).count()

        if existing > 0:
            print(f"Resources already exist: {existing}")
            return

        for data in resources:
            resource = EmergencyResource(
                name=data["name"],
                resource_type=data["resource_type"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                address=data["address"],
                contact_number=data["contact_number"],
            )

            db.add(resource)
            db.flush()

            availability = ResourceAvailability(
                resource_id=resource.id,
                available_units=data["available_units"],
                status=data["status"],
                wait_time_minutes=data["wait_time_minutes"],
            )

            db.add(availability)

        db.commit()

        print(f"Seeded {len(resources)} emergency resources successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_resources()