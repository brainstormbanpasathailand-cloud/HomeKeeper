"""Aggregate all versioned API routers."""
from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    categories,
    health,
    jobs,
    notifications,
    oauth,
    properties,
    quotations,
    reviews,
    technicians,
    uploads,
    warranties,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(oauth.router)
api_router.include_router(categories.router)
api_router.include_router(properties.router)
api_router.include_router(jobs.router)
api_router.include_router(quotations.router)
api_router.include_router(technicians.router)
api_router.include_router(health.router)
api_router.include_router(warranties.router)
api_router.include_router(reviews.router)
api_router.include_router(notifications.router)
api_router.include_router(uploads.router)
api_router.include_router(admin.router)
