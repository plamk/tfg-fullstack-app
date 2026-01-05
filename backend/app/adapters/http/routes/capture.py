from fastapi import APIRouter, Depends, HTTPException
from app.adapters.http.deps import get_runner

router = APIRouter()

@router.get("/api/status")
def status(runner=Depends(get_runner)):
    return runner.status()

@router.post("/api/capture")
def capture(runner=Depends(get_runner)):
    try:
        meta = runner.capture_now()
        return {"ok": True, "metadata": meta}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))