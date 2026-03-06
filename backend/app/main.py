from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.observability import setup_observability
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.billing import router as billing_router
from app.routers.internal_email_queue import router as internal_email_queue_router
from app.routers.organizations import router as organizations_router
from app.routers.planner import router as planner_router
from app.routers.reviews import router as reviews_router
from app.routers.sessions import router as sessions_router
from app.routers.subjects import router as subjects_router
from app.routers.tasks import router as tasks_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
setup_observability(app)

default_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://study-os-xi.vercel.app",
    "https://studyos-staging.vercel.app",
}
configured_origins = {origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()}
allowed_origins = sorted(default_origins | configured_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=settings.cors_allow_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if settings.security_headers_enabled:

    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


all_routers = [
    auth_router,
    organizations_router,
    subjects_router,
    tasks_router,
    planner_router,
    reviews_router,
    sessions_router,
    analytics_router,
    internal_email_queue_router,
    billing_router,
]

for router in all_routers:
    app.include_router(router)
    app.include_router(router, prefix="/v1")
