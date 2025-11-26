from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, students, teachers, schools, platform_admin,
    content, surveys, games, payments, theming, feature_flags
)

app = FastAPI(title="EigoKit API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

