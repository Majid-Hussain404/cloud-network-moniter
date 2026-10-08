from pathlib import Path

import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import CheckResult, Incident, ServerSnapshot, SessionLocal, Target, create_tables
from .monitoring.http_checker import check_http
from .monitoring.ping_checker import check_ping
from .monitoring.tcp_checker import check_tcp
from .monitoring.system_metrics import collect_system_metrics
from .services.monitoring_worker import monitoring_loop, worker_state


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    worker_task = asyncio.create_task(monitoring_loop())
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        worker_state["status"] = "stopped"


app = FastAPI(
    title="Cloud Network Monitoring Platform",
    description="A beginner-friendly network monitoring API.",
    version="0.1.0",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    """Serve the initial dashboard page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a small response proving that the API process is running."""
    return {"status": "ok"}


@app.get("/api/overview")
def overview() -> dict[str, object]:
    """Return temporary dashboard data until the database is added."""
    with SessionLocal() as session:
        targets = session.query(Target).filter(Target.enabled.is_(True)).all()
        latest_results = {
            target.id: session.query(CheckResult)
            .filter(CheckResult.target_id == target.id)
            .order_by(CheckResult.checked_at.desc())
            .first()
            for target in targets
        }
        active_alerts = session.query(Incident).filter(Incident.status == "open").count()

    healthy_targets = sum(
        1 for result in latest_results.values() if result and result.success
    )

    return {
        "monitoring_status": "Monitoring ready",
        "targets_monitored": len(targets),
        "healthy_targets": healthy_targets,
        "active_alerts": active_alerts,
        "message": "HTTP, TCP, and host checks are available from the target actions API.",
    }


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_type: str = Field(pattern="^(host|http|tcp)$")
    address: str = Field(min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)


def get_db():
    with SessionLocal() as session:
        yield session


@app.get("/api/targets")
def list_targets(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    targets = db.query(Target).order_by(Target.id).all()
    response = []
    for target in targets:
        latest_result = (
            db.query(CheckResult)
            .filter(CheckResult.target_id == target.id)
            .order_by(CheckResult.checked_at.desc())
            .first()
        )
        response.append({
            "id": target.id,
            "name": target.name,
            "target_type": target.target_type,
            "address": target.address,
            "port": target.port,
            "enabled": target.enabled,
            "latest_result": None
            if latest_result is None
            else {
                "success": latest_result.success,
                "status_code": latest_result.status_code,
                "response_time_ms": latest_result.response_time_ms,
                "error": latest_result.error,
            },
        })
    return response


@app.post("/api/targets", status_code=201)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    if payload.target_type == "tcp" and payload.port is None:
        raise HTTPException(status_code=422, detail="TCP targets require a port.")

    target = Target(**payload.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)
    return {
        "id": target.id,
        "name": target.name,
        "target_type": target.target_type,
        "address": target.address,
        "port": target.port,
        "enabled": target.enabled,
    }


@app.post("/api/targets/{target_id}/check")
def run_target_check(target_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Target not found.")
    if target.target_type == "http":
        result = check_http(target.address)
        status_code = result.status_code
        packet_loss_percent = None
        response_time_ms = result.response_time_ms
    elif target.target_type == "tcp" and target.port is not None:
        result = check_tcp(target.address, target.port)
        status_code = None
        packet_loss_percent = None
        response_time_ms = result.response_time_ms
    elif target.target_type == "host":
        result = check_ping(target.address)
        status_code = None
        packet_loss_percent = result.packet_loss_percent
        response_time_ms = result.latency_ms
    else:
        raise HTTPException(status_code=400, detail="This target type is not ready for checks yet.")

    saved_result = CheckResult(
        target_id=target.id,
        success=result.success,
        status_code=status_code,
        response_time_ms=response_time_ms,
        error=result.error,
    )
    db.add(saved_result)
    db.commit()
    db.refresh(saved_result)
    return {
        "target_id": target.id,
        "success": result.success,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "latency_ms": getattr(result, "latency_ms", None),
        "packet_loss_percent": packet_loss_percent,
        "error": result.error,
    }


@app.get("/api/system-metrics")
def system_metrics(db: Session = Depends(get_db)) -> dict[str, int | float]:
    metrics = collect_system_metrics()
    snapshot = ServerSnapshot(**metrics.__dict__)
    db.add(snapshot)
    db.commit()
    return metrics.__dict__


@app.get("/api/worker-status")
def get_worker_status() -> dict[str, object]:
    return worker_state


@app.get("/api/incidents")
def list_incidents(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    incidents = db.query(Incident).order_by(Incident.opened_at.desc()).limit(20).all()
    return [
        {
            "id": incident.id,
            "target_id": incident.target_id,
            "opened_at": incident.opened_at.isoformat(),
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "status": incident.status,
            "reason": incident.reason,
        }
        for incident in incidents
    ]
