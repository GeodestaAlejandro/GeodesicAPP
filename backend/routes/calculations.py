from fastapi import APIRouter, HTTPException
from services.calculations import (
    calculate_xz_from_latitude,
    calculate_xz_from_w,
    calculate_xz_from_theta,
    calculate_xyz_from_latitude_longitude,
    calculate_latitude_from_w,
)

router = APIRouter()

@router.post("/calculate/xz-from-latitude")
def calculate_xz_from_latitude_endpoint(data: dict):
    try:
        latitude = data.get("latitude")
        result = calculate_xz_from_latitude(latitude)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/xz-from-w")
def calculate_xz_from_w_endpoint(data: dict):
    try:
        w = data.get("w")
        R_gzx = data.get("R_gzx")
        result = calculate_xz_from_w(w, R_gzx)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/xz-from-theta")
def calculate_xz_from_theta_endpoint(data: dict):
    try:
        theta = data.get("theta")
        result = calculate_xz_from_theta(theta)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/xyz-from-latitude-longitude")
def calculate_xyz_from_latitude_longitude_endpoint(data: dict):
    try:
        latitude = data.get("latitude")
        longitude_ = data.get("longitude")
        h = data.get("h", 0)
        result = calculate_xyz_from_latitude_longitude(latitude, longitude_, h)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/latitude-from-w")
def calculate_latitude_from_w_endpoint(data: dict):
    try:
        w = data.get("w")
        result = calculate_latitude_from_w(w)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))