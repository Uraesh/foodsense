"""Main application entry point for the FoodSense backend, setting up the FastAPI app, middleware, and routes."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import get_settings
from app.routers.search import router as search_router
from app.routers.summarize import router as summarize_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Context manager for handling application lifecycle events."""
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(search_router)
app.include_router(summarize_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint to verify that the backend is running and responsive."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint providing a simple message to confirm that the backend is operational."""
    return {"message": "FoodSense backend is running."}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Endpoint to handle favicon requests, returning a 204 No Content response since there is no favicon provided."""
    return Response(status_code=204)
