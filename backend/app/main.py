from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os

from app.database import engine, Base

from app.auth import models as auth_models
from app.document import D_models as document_models
from app.ai_routing import models as ai_routing_models

from app.auth.routes import auth_router
from app.ai_routes import ai_router
from app.document.document_routes import router as document_router
from app.qr_tracking.routes import router as qr_router
from app.ai_routing.routes import router as ai_routing_router
from app.analytics.routes import router as analytics_router
from app.doccode.routes import router as doccode_router
from fastapi.staticfiles import StaticFiles

from app.ai_routing.scheduler import start_scheduler

app = FastAPI(title="DocRoute-RT Backend", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    if os.getenv("RUN_SCHEDULER", "true") == "true":
        start_scheduler()


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret"),
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(document_router)
app.include_router(qr_router)
app.include_router(ai_routing_router)
app.include_router(analytics_router)
app.include_router(doccode_router)


@app.get("/")
def root():
    return {
        "status": "Backend running",
        "service": "DocRoute-RT",
    }
