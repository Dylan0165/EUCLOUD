"""
FastAPI main application for EUCLOUD
Migrated from Flask to FastAPI for better performance and modern features
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from config import Config
from models import db, Base, engine
from auth import get_current_user

# Import routers
from routes.auth import router as auth_router
from routes.files import router as files_router
from routes.folders import router as folders_router
from routes.shares import router as shares_router
from routes.storage import router as storage_router
from routes.trash import router as trash_router
from routes.extras import router as extras_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Create database tables
    Config.init_app(None)  # Initialize config (create directories)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    yield
    # Shutdown: Cleanup if needed
    print("👋 Shutting down EUCLOUD API")


# Create FastAPI app
app = FastAPI(
    title="EUCLOUD API",
    description="Personal cloud storage API built with FastAPI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoints
@app.get("/")
async def index():
    """API root endpoint"""
    return {
        "message": "EUCLOUD API is running", 
        "version": "2.0.0",
        "framework": "FastAPI"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers with /api prefix
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(files_router, prefix="/api/files", tags=["Files"])
app.include_router(folders_router, prefix="/api/folders", tags=["Folders"])
app.include_router(shares_router, prefix="/api/shares", tags=["Shares"])
app.include_router(storage_router, prefix="/api/storage", tags=["Storage"])
app.include_router(trash_router, prefix="/api/trash", tags=["Trash"])
app.include_router(extras_router, prefix="/api/extras", tags=["Extras"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
