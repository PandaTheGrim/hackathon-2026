from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from app.routes.check import check_assignment
from app.services.db import client


@asynccontextmanager
async def lifespan(_: FastAPI):
    client.admin.command("ping")
    yield
    client.close()

app = FastAPI(
    title="Assignment Checker API",
    version="0.1.0",
    lifespan=lifespan
)

router = APIRouter(prefix="/api/v1", tags=["check"])
router.add_api_route("/check", check_assignment, methods=["POST"])

app.include_router(router)