from fastapi import APIRouter, Depends, HTTPException
from app.adapters.http.deps import get_runner
from app.application.validators.project_name import validate_project_name

router = APIRouter()

@router.get("/api/projects")
def list_projects(runner=Depends(get_runner)):
    return {"projects": runner.list_projects()}

@router.post("/api/projects/{name}/start")
def start_project(name: str, runner=Depends(get_runner)):
    name = validate_project_name(name)
    try:
        runner.start_project(name)
        return {"ok": True, "active_project": name}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project config.json not found")

@router.post("/api/projects/stop")
def stop_project(runner=Depends(get_runner)):
    runner.stop_project()
    return {"ok": True}