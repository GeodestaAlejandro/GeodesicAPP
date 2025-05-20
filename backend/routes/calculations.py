from fastapi import APIRouter
from services.calculations import (
    calculate_xz_from_phi,
    calculate_xz_from_w,
    calculate_xz_from_theta,
    calculate_xyz_from_phi_lambda,
    calculate_phi_from_w,
)

router = APIRouter()

@router.post("/calculate/xz-from-phi")
def calculate_xz_from_phi_endpoint(data: dict):
    try:
        phi = data.get("phi")
        result = calculate_xz_from_phi(phi)
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

@router.post("/calculate/xyz-from-phi-lambda")
def calculate_xyz_from_phi_lambda_endpoint(data: dict):
    try:
        phi = data.get("phi")
        lambda_ = data.get("lambda")
        h = data.get("h", 0)
        result = calculate_xyz_from_phi_lambda(phi, lambda_, h)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculate/phi-from-w")
def calculate_phi_from_w_endpoint(data: dict):
    try:
        w = data.get("w")
        result = calculate_phi_from_w(w)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))