from typing import Optional
from pydantic import BaseModel, Field

class RoomResponse(BaseModel):
    id: int
    building_id: int
    room_number: str
    floor: int
    wing: Optional[str] = None
    room_type: str

    class Config:
        from_attributes = True

class BuildingResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    total_floors: int
    rooms: list[RoomResponse] = []

    class Config:
        from_attributes = True

class BuildingSummary(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    total_floors: int
    room_count: int = 0

    class Config:
        from_attributes = True

class LocationVerifyResponse(BaseModel):
    valid: bool
    building_id: Optional[int] = None
    building_name: Optional[str] = None
    building_code: Optional[str] = None
    room_number: Optional[str] = None
    floor: Optional[int] = None
    wing: Optional[str] = None
    room_type: Optional[str] = None
    message: str
