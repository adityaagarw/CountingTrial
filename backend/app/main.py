# backend/app/main.py

from fastapi import FastAPI
from .authentication import router as auth_router
from .camera import router as camera_router
from .sql_websocket import router as data_router
from .feed import router as feed_router
from .analytics import router as detection_data_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()
# Allow all origins (not recommended for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]
)
app.include_router(auth_router, prefix="/auth", tags=["User Auth"])
app.include_router(camera_router, prefix="/camera", tags=["Camera"])
app.include_router(data_router, prefix="/data", tags=["Data"])
app.include_router(detection_data_router, prefix="/stats", tags=["Statistics"])
app.include_router(feed_router, prefix="/feed", tags=["Feed"])