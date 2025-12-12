from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router as evac_router

app = FastAPI(
    title="Evacuation Routing API",
    description="Prototyp modułu wyznaczania trasy ewakuacji z uwzględnieniem flood zones",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evac_router, prefix="/api")
