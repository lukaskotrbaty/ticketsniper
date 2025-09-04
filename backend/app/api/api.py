from fastapi import APIRouter, Response, status

from app.api.endpoints import auth, routes, data # Import routes and data modules

api_router = APIRouter()

@api_router.get("/health", tags=["health"])
def health_check():
    """
    Checks if the application is healthy.
    """
    return {"status": "ok"}

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include route monitoring routes
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])

# Include data fetching routes
api_router.include_router(data.router, prefix="/data", tags=["data"])
