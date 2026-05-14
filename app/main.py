from datetime import datetime, timezone
from typing import List, Optional
from app.core import limiter
from app.utils.response import custom_response
from fastapi import FastAPI, status
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from app.core.config import settings
from app.api.v1.routes import (
    admin_panel_company,
    admin_panel_job,
    admin_panel_worker,
    auth,
    company,
    company_ws,
    industry_skill,
    job,
    worker,
    worker_ws,
)

# from app.utils.middlewares import LoggingMiddleware, AuthMiddleware

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    # description=settings.DESCRIPTION,
    # contact={"name": "Pavi", "email": "pavi@company.com"},
    # license_info={"name": "MIT"},
    # openapi_tags=[
    #     {"name": "Auth", "description": "User authentication using JWT tokens"},
    #     {"name": "Worker", "description": "Worker management endpoints"},
    #     {"name": "Job", "description": "Job posting and management endpoints"},
    # ],
)

# ---------- Middleware ----------
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://workforce360-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------- Middleware ----------
# app.add_middleware(LoggingMiddleware)
# app.add_middleware(AuthMiddleware)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(worker.router, prefix="/api/v1/worker", tags=["Worker"])
app.include_router(job.router, prefix="/api/v1/job", tags=["Job"])
app.include_router(company.router, prefix="/api/v1/company", tags=["Company"])
app.include_router(
    industry_skill.router, prefix="/api/v1/industry_skill", tags=["Industry & Skill"]
)
app.include_router(
    worker_ws.router, prefix="/api/v1/worker_ws", tags=["Worker WebSocket"]
)
app.include_router(
    company_ws.router, prefix="/api/v1/company_ws", tags=["Company WebSocket"]
)

app.include_router(
    admin_panel_company.router,
    prefix="/api/v1/admin_panel_company",
    tags=["Admin Panel - Company"],
)
app.include_router(
    admin_panel_worker.router,
    prefix="/api/v1/admin_panel_worker",
    tags=["Admin Panel - Worker"],
)
app.include_router(
    admin_panel_job.router,
    prefix="/api/v1/admin_panel_job",
    tags=["Admin Panel - Job"],
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom OpenAPI Branding
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=f"{settings.PROJECT_NAME} (Customized Docs)",
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return custom_response(
        success=True,
        message="API is up and running.",
        data={"version": settings.VERSION},
        code=status.HTTP_200_OK,
    )


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
