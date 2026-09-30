from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.location import Building
from backend.app.schemas.location import (
    BuildingResponse,
    BuildingSummary,
    RoomResponse,
    LocationVerifyResponse,
)
from backend.app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Campus Location Directory"])

@router.get("/buildings", response_model=list[BuildingSummary])
def list_buildings(db: Session = Depends(get_db)) -> Any:
    """Retrieve all campus buildings with floor count and room counts."""
    buildings = LocationService.get_all_buildings(db)
    results = []
    for b in buildings:
        results.append(
            BuildingSummary(
                id=b.id,
                code=b.code,
                name=b.name,
                description=b.description,
                total_floors=b.total_floors,
                room_count=len(b.rooms)
            )
        )
    return results

@router.get("/buildings/{building_id}", response_model=BuildingResponse)
def get_building(building_id: int, db: Session = Depends(get_db)) -> Any:
    """Retrieve a specific building along with all its registered rooms."""
    building = LocationService.get_building_by_id(db, building_id)
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building with ID {building_id} not found"
        )
    return building

@router.get("/buildings/{building_id}/rooms", response_model=list[RoomResponse])
def list_rooms_for_building(
    building_id: int,
    floor: Optional[int] = Query(None, description="Optional floor filter"),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve all rooms within a building, with optional floor filtering."""
    building = LocationService.get_building_by_id(db, building_id)
    if not building:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building with ID {building_id} not found"
        )
    return LocationService.get_rooms_by_building(db, building_id, floor)

@router.get("/verify", response_model=LocationVerifyResponse)
def verify_location(
    building: str = Query(..., description="Building ID or Code, e.g. '1' or 'ENG-A'"),
    room_number: str = Query(..., description="Room Number, e.g. 'LAB-1'"),
    db: Session = Depends(get_db)
) -> Any:
    """Verify that a selected or entered building and room combination is valid."""
    result = LocationService.verify_location(db, building, room_number)
    return result

@router.get("/search")
def search_locations(
    q: str = Query(..., min_length=1, description="Search term for building or room"),
    db: Session = Depends(get_db)
) -> Any:
    """Autocomplete search across campus buildings and rooms for rapid selection."""
    return LocationService.search_locations(db, q)
