import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from app.routes.check import check_assignment
from app.services.db import client
from app.services.llm import ollama_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    print("Checking dependencies:")
    while True:
        try:
            models = ollama_client.list().models
            if any("qwen2.5-coder" in m.model for m in models):
                print("Ollama OK")
                break
        except Exception:
            pass
        time.sleep(3)

    client.admin.command("ping")
    print("MongoDB OK")
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
