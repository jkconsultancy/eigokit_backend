from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import (
    auth, students, teachers, schools, platform_admin,
    content, surveys, games, payments, theming, feature_flags
)
from app.config import settings
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.environment == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Reduce verbose logging from third-party libraries
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(title="EigoKit API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Error: {request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.3f}s",
            exc_info=True
        )
        raise

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path} - "
        f"Error: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "error_id": f"{datetime.now().timestamp()}"
        }
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["teachers"])
app.include_router(schools.router, prefix="/api/schools", tags=["schools"])
app.include_router(platform_admin.router, prefix="/api/platform", tags=["platform"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(surveys.router, prefix="/api/surveys", tags=["surveys"])
app.include_router(games.router, prefix="/api/games", tags=["games"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(theming.router, prefix="/api/theming", tags=["theming"])
app.include_router(feature_flags.router, prefix="/api/features", tags=["features"])


@app.get("/")
async def root():
    return {"message": "EigoKit API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

