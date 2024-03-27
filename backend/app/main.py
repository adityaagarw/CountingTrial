# backend/app/main.py

from fastapi import FastAPI
from .authentication import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# Allow all origins (not recommended for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)