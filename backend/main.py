from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.conversions import router as conversions_router
from routes.calculations import router as calculations_router

app = FastAPI(
    title="Geodesic Calculator",
    description="API para cálculos geodésicos.",
    version="0.0.1"
)

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Geodesic Calculator API"}

app.include_router(calculations_router, prefix="/calculate")