from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import DATA_DIR
from app.infrastructure.simulator.runner_fake import FakeRunner


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runner = FakeRunner(DATA_DIR)
    yield
    app.state.runner.shutdown()

app = FastAPI(title="TFG API (SIM)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_runner():
    return app.state.runner

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/status")
def status(runner=Depends(get_runner)):
    return runner.status()

@app.get("/projects")
def projects(runner=Depends(get_runner)):
    return {"projects": runner.list_projects()}

@app.post("/projects/{name}/start")
def start_project(name: str, runner=Depends(get_runner)):
    try:
        runner.start_project(name)
        return {"ok": True, "active_project": name}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project config.json not found")

@app.post("/projects/stop")
def stop_project(runner=Depends(get_runner)):
    runner.stop_project()
    return {"ok": True}

@app.post("/capture")
def capture(runner=Depends(get_runner)):
    try:
        return {"ok": True, "metadata": runner.capture_now()}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))