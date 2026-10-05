import json
import os
from typing import Any, Optional

DATASET_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/campus_locations_dataset.json")
)

class CampusLocationDataset:
    """Utility class to load, validate, and search the campus spatial dataset."""
    _data: Optional[dict[str, Any]] = None

    @classmethod
    def load(cls) -> dict[str, Any]:
        if cls._data is None:
            if not os.path.exists(DATASET_PATH):
                raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
            with open(DATASET_PATH, "r", encoding="utf-8") as f:
                cls._data = json.load(f)
        return cls._data

    @classmethod
    def validate_integrity(cls) -> dict[str, Any]:
        """Verify no duplicate building codes, valid floor lists, and non-empty rooms."""
        data = cls.load()
        buildings = data.get("buildings", [])
        
        seen_building_codes = set()
        total_rooms = 0
        issues = []

        for b in buildings:
            code = b.get("code")
            if not code or code in seen_building_codes:
                issues.append(f"Duplicate or invalid building code: {code}")
            seen_building_codes.add(code)

            floors = b.get("floors", [])
            if not floors:
                issues.append(f"Building {code} has no registered floors")

            seen_rooms_in_building = set()
            for f in floors:
                for r in f.get("rooms", []):
                    r_num = r.get("room_number")
                    if r_num in seen_rooms_in_building:
                        issues.append(f"Duplicate room {r_num} in building {code}")
                    seen_rooms_in_building.add(r_num)
                    total_rooms += 1

        return {
            "valid": len(issues) == 0,
            "building_count": len(buildings),
            "total_rooms": total_rooms,
            "issues": issues
        }

    @classmethod
    def get_building_by_code(cls, code: str) -> Optional[dict[str, Any]]:
        data = cls.load()
        for b in data.get("buildings", []):
            if b["code"].upper() == code.strip().upper():
                return b
        return None

    @classmethod
    def get_room_details(cls, building_code: str, room_number: str) -> Optional[dict[str, Any]]:
        building = cls.get_building_by_code(building_code)
        if not building:
            return None
        for f in building.get("floors", []):
            for r in f.get("rooms", []):
                if r["room_number"].upper() == room_number.strip().upper():
                    return {
                        "building_code": building["code"],
                        "building_name": building["name"],
                        "floor_number": f["floor_number"],
                        "floor_name": f["name"],
                        "room_number": r["room_number"],
                        "room_type": r["room_type"],
                        "capacity": r.get("capacity"),
                        "nearest_exit": r.get("nearest_exit"),
                        "fire_extinguisher_id": r.get("fire_extinguisher_id")
                    }
        return None

if __name__ == "__main__":
    report = CampusLocationDataset.validate_integrity()
    print("Dataset Validation Report:", report)
