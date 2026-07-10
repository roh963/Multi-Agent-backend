import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.routers import auth, pipeline, user
from app.config import settings

app = FastAPI(
    title="Multi-Agent Research API",
    description="FastAPI backend for AI-powered research pipeline",
    version="1.0.0"
)

# ✅ Comma-separated support + fallback
FRONTEND_URL = settings.FRONTEND_URL or ""
origins = [url.strip().rstrip("/") for url in FRONTEND_URL.split(",") if url.strip()]  
if not origins:
    origins = ["*"]

print(f"✅ Allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,)
app.include_router(pipeline.router)
app.include_router(user.router)

@app.on_event("startup")
def startup():
    create_tables()
    print("✅ Database tables created/verified")

@app.get("/")
def health():
    return {"status": "ok", "message": "Multi-Agent API is running!"}