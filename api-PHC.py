# api-PHC.py — FastAPI local server for PHC + OpenWave
# Part of the PHC repository by Eliya, 2026
# Run: python api-PHC.py
# Docs: http://localhost:8000/docs

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import uvicorn
import numpy as np

from phc import PHC
from openwave import OpenWave

app = FastAPI(
    title="api-PHC",
    description="Local API for the Physical Hybrid Computing engine + OpenWave protocol",
    version="0.2.0"
)

# --- Global instances ---
_phc_instance: Optional[PHC] = None
_openwave_instance: Optional[OpenWave] = None

def get_phc(size: int = 50) -> PHC:
    global _phc_instance
    if _phc_instance is None or _phc_instance.size != size:
        _phc_instance = PHC(size=size)
    return _phc_instance

def get_openwave(size: int = 50) -> OpenWave:
    global _openwave_instance
    if _openwave_instance is None:
        _openwave_instance = OpenWave(grid_size=size)
    return _openwave_instance


# ════════════════════════════════════════
# Request / Response models
# ════════════════════════════════════════

class InitRequest(BaseModel):
    size: int = 50

class TickRequest(BaseModel):
    cycles: int = 1
    size: int = 50

class ComputeRequest(BaseModel):
    a: float
    operator: str   # '+', '-', '*', '/'
    b: float
    size: int = 50

class ParallelComputeRequest(BaseModel):
    tasks: List[Tuple[float, float, str]]
    size: int = 50

class StateResponse(BaseModel):
    size: int
    states: List[List[float]]
    mean: float
    max: float
    min: float

class ComputeResponse(BaseModel):
    result: float
    cycles_run: int

class ParallelComputeResponse(BaseModel):
    results: List[float]
    task_count: int

# OpenWave models
class CreateGridRequest(BaseModel):
    name: str
    size: int = 50

class SendSignalRequest(BaseModel):
    from_grid: str
    to_grid: str
    value: float
    cycles: int = 10

class BroadcastRequest(BaseModel):
    from_grid: str
    value: float
    cycles: int = 10

class TickAllRequest(BaseModel):
    cycles: int = 1


# ════════════════════════════════════════
# PHC Endpoints
# ════════════════════════════════════════

@app.get("/")
def root():
    return {
        "name": "api-PHC",
        "version": "0.2.0",
        "status": "running",
        "author": "Eliya, 2026",
        "modules": ["PHC Engine", "OpenWave Protocol"]
    }

@app.post("/phc/init", response_model=StateResponse)
def init_phc(req: InitRequest):
    """Initialize a new PHC grid."""
    global _phc_instance
    _phc_instance = PHC(size=req.size)
    return StateResponse(
        size=req.size,
        states=_phc_instance.states.tolist(),
        mean=float(np.mean(_phc_instance.states)),
        max=float(np.max(_phc_instance.states)),
        min=float(np.min(_phc_instance.states))
    )

@app.post("/phc/tick", response_model=StateResponse)
def tick(req: TickRequest):
    """Run N wave propagation cycles."""
    phc = get_phc(req.size)
    for _ in range(req.cycles):
        phc.tick()
    return StateResponse(
        size=req.size,
        states=phc.states.tolist(),
        mean=float(np.mean(phc.states)),
        max=float(np.max(phc.states)),
        min=float(np.min(phc.states))
    )

@app.post("/phc/compute", response_model=ComputeResponse)
def compute(req: ComputeRequest):
    """Perform a single computation using PHC."""
    if req.operator not in ('+', '-', '*', '/'):
        raise HTTPException(status_code=400, detail="operator must be +, -, *, /")
    if req.operator == '/' and req.b == 0:
        raise HTTPException(status_code=400, detail="division by zero")
    phc = get_phc(req.size)
    result = phc.compute(req.a, req.operator, req.b)
    return ComputeResponse(result=float(result), cycles_run=1)

@app.post("/phc/compute/parallel", response_model=ParallelComputeResponse)
def compute_parallel(req: ParallelComputeRequest):
    """Run multiple computations in parallel using PHC."""
    if not req.tasks:
        raise HTTPException(status_code=400, detail="tasks list is empty")
    phc = get_phc(req.size)
    results = phc.compute_parallel(req.tasks)
    return ParallelComputeResponse(
        results=[float(r) for r in results],
        task_count=len(req.tasks)
    )

@app.get("/phc/state", response_model=StateResponse)
def get_state(size: int = 50):
    """Get current PHC grid state."""
    phc = get_phc(size)
    return StateResponse(
        size=size,
        states=phc.states.tolist(),
        mean=float(np.mean(phc.states)),
        max=float(np.max(phc.states)),
        min=float(np.min(phc.states))
    )

@app.post("/phc/reset")
def reset(req: InitRequest):
    """Reset PHC grid."""
    global _phc_instance
    _phc_instance = PHC(size=req.size)
    return {"status": "reset", "size": req.size}


# ════════════════════════════════════════
# OpenWave Endpoints
# ════════════════════════════════════════

@app.post("/openwave/grid/create")
def create_grid(req: CreateGridRequest):
    """Create a named PHC grid inside OpenWave."""
    ow = get_openwave(req.size)
    ow.create_grid(req.name)
    return {"status": "created", "grid": req.name}

@app.get("/openwave/grids")
def list_grids():
    """List all OpenWave grids."""
    ow = get_openwave()
    return {"grids": ow.list_grids()}

@app.post("/openwave/send")
def send_signal(req: SendSignalRequest):
    """Send a wave signal from one grid to another."""
    ow = get_openwave()
    edge_signal = ow.send(req.from_grid, req.to_grid, req.value, req.cycles)
    return {
        "from": req.from_grid,
        "to": req.to_grid,
        "value": req.value,
        "edge_signal": edge_signal
    }

@app.post("/openwave/broadcast")
def broadcast(req: BroadcastRequest):
    """Broadcast a signal from one grid to all others."""
    ow = get_openwave()
    results = ow.broadcast(req.value, req.from_grid, req.cycles)
    return {"from": req.from_grid, "sent_to": results}

@app.get("/openwave/snapshot")
def snapshot():
    """Get wave energy snapshot of all grids."""
    ow = get_openwave()
    return ow.snapshot()

@app.get("/openwave/energy/{grid_name}")
def grid_energy(grid_name: str):
    """Get energy stats for a specific grid."""
    ow = get_openwave()
    return ow.energy(grid_name)

@app.get("/openwave/channel/{grid_name}")
def channel_history(grid_name: str):
    """Get signal history for a grid."""
    ow = get_openwave()
    return {"grid": grid_name, "history": ow.channel_history(grid_name)}

@app.post("/openwave/tick")
def tick_all(req: TickAllRequest):
    """Advance all OpenWave grids by N cycles."""
    ow = get_openwave()
    ow.tick_all(req.cycles)
    return {"status": "ticked", "cycles": req.cycles, "grids": ow.list_grids()}

@app.post("/openwave/reset")
def reset_openwave(req: InitRequest):
    """Reset all OpenWave grids."""
    global _openwave_instance
    _openwave_instance = OpenWave(grid_size=req.size)
    return {"status": "reset"}


# ════════════════════════════════════════
# Run
# ════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 50)
    print("  api-PHC — Physical Hybrid Computing API")
    print("  http://localhost:8000")
    print("  http://localhost:8000/docs  ← full docs")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)
