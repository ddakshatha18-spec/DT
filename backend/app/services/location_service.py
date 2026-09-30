from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models.location import Building, Room

class LocationService:
    @staticmethod
    def get_all_buildings(db: Session) -> list[Building]:
        """Fetch all buildings sorted alphabetically."""
        return db.query(Building).order_by(Building.name.asc()).all()

    @staticmethod
    def get_building_by_id(db: Session, building_id: int) -> Optional[Building]:
        return db.query(Building).filter(Building.id == building_id).first()

    @staticmethod
    def get_building_by_code(db: Session, code: str) -> Optional[Building]:
        return db.query(Building).filter(Building.code.ilike(code.strip())).first()

    @staticmethod
    def get_rooms_by_building(db: Session, building_id: int, floor: Optional[int] = None) -> list[Room]:
        query = db.query(Room).filter(Room.building_id == building_id)
        if floor is not None:
            query = query.filter(Room.floor == floor)
        return query.order_by(Room.floor.asc(), Room.room_number.asc()).all()

    @classmethod
    def verify_location(cls, db: Session, building_query: str, room_number: str) -> dict:
        """
        Verify if a building and room pair exists.
        Supports building ID (e.g. '1') or building code (e.g. 'ENG-A').
        """
        building = None
        if building_query.isdigit():
            building = cls.get_building_by_id(db, int(building_query))
        if not building:
            building = cls.get_building_by_code(db, building_query)

        if not building:
            return {
                "valid": False,
                "message": f"Campus building '{building_query}' not recognized in directory"
            }

        room = db.query(Room).filter(
            Room.building_id == building.id,
            Room.room_number.ilike(room_number.strip())
        ).first()

        if not room:
            return {
                "valid": False,
                "building_id": building.id,
                "building_name": building.name,
                "building_code": building.code,
                "message": f"Room '{room_number}' not registered in {building.name}"
            }

        return {
            "valid": True,
            "building_id": building.id,
            "building_name": building.name,
            "building_code": building.code,
            "room_number": room.room_number,
            "floor": room.floor,
            "wing": room.wing,
            "room_type": room.room_type,
            "message": f"Location verified: {building.name}, Floor {room.floor}, Room {room.room_number}"
        }

    @staticmethod
    def search_locations(db: Session, query_str: str) -> list[dict]:
        """Search buildings and rooms matching query string."""
        pattern = f"%{query_str.strip()}%"
        rooms = (
            db.query(Room)
            .join(Building)
            .filter(
                or_(
                    Room.room_number.ilike(pattern),
                    Room.room_type.ilike(pattern),
                    Building.name.ilike(pattern),
                    Building.code.ilike(pattern)
                )
            )
            .limit(20)
            .all()
        )
        return [
            {
                "room_id": r.id,
                "room_number": r.room_number,
                "room_type": r.room_type,
                "floor": r.floor,
                "wing": r.wing,
                "building_id": r.building.id,
                "building_name": r.building.name,
                "building_code": r.building.code,
                "display_label": f"{r.building.name} - Floor {r.floor} ({r.room_number}: {r.room_type})"
            }
            for r in rooms
        ]
