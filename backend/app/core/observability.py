import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings


def setup_observability(app: FastAPI) -> None:
    settings = get_settings()
    log_format = "%(message)s" if settings.observability.json_logs_enabled else "%(levelname)s %(message)s"
    logging.basicConfig(level=settings.observability.log_level, format=log_format)
    logger = logging.getLogger("studyos")

    try:
        import sentry_sdk  # type: ignore

        if settings.observability.sentry_enabled:
            sentry_sdk.init(
                dsn=settings.observability.sentry_dsn,
                traces_sample_rate=settings.observability.sentry_traces_sample_rate,
            )
    except Exception:
        pass

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    }
                )
            )
            response.headers["X-Request-Id"] = request_id
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                json.dumps(
                    {
                        "event": "http_request_error",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                    }
                )
            )
            raise

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
        logger.exception(
            json.dumps(
                {
                    "event": "unhandled_exception",
                    "request_id": request_id,
                    "path": request.url.path,
                    "error": str(exc),
                }
            )
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id})
