from fastapi import APIRouter, HTTPException
from services import coordinate_services

router = APIRouter()

@router.post("/validate")
def validate(data: CoordinateInput):
    return coordinate_services.validate_coordinates(data)