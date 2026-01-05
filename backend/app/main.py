from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ENV, DATA_DIR
from app.infrastructure.simulator.runner_fake import FakeRunner
from app.infrastructure.raspi.runner_raspi import RaspiRunner

from app.adapters.http.routes.system import router as system_router
from app.adapters.http.routes.projects import router as projects_router
from app.adapters.http.routes.capture import router as capture_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if ENV == "raspi":
        app.state.runner = RaspiRunner(DATA_DIR)
    else:
        app.state.runner = FakeRunner(DATA_DIR)

    yield

    try:
        app.state.runner.shutdown()
    except Exception:
        pass


app = FastAPI(title="TFG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(projects_router)
app.include_router(capture_router)