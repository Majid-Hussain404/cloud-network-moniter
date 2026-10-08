import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..database import CheckResult, Incident, ServerSnapshot, SessionLocal, Target
from ..config import settings
from ..monitoring.http_checker import check_http
from ..monitoring.ping_checker import check_ping
from ..monitoring.system_metrics import collect_system_metrics
from ..monitoring.tcp_checker import check_tcp

logger = logging.getLogger(__name__)
INTERVAL_SECONDS = settings.monitoring_interval_seconds
worker_state = {"status": "starting", "last_run_at": None, "last_error": None}


def run_target_check(target: Target, db: Session) -> None:
    if target.target_type == "http":
        result = check_http(target.address)
        status_code = result.status_code
        response_time_ms = result.response_time_ms
    elif target.target_type == "tcp" and target.port is not None:
        result = check_tcp(target.address, target.port)
        status_code = None
        response_time_ms = result.response_time_ms
    elif target.target_type == "host":
        result = check_ping(target.address)
        status_code = None
        response_time_ms = result.latency_ms
    else:
        return

    previous_result = (
        db.query(CheckResult)
        .filter(CheckResult.target_id == target.id)
        .order_by(CheckResult.checked_at.desc())
        .first()
    )
    db.add(CheckResult(
        target_id=target.id,
        success=result.success,
        status_code=status_code,
        response_time_ms=response_time_ms,
        error=result.error,
    ))

    open_incident = (
        db.query(Incident)
        .filter(Incident.target_id == target.id, Incident.status == "open")
        .first()
    )
    if not result.success and open_incident is None and (previous_result is None or previous_result.success):
        db.add(Incident(
            target_id=target.id,
            status="open",
            reason=result.error or "Target check failed.",
        ))
    elif result.success and open_incident is not None:
        open_incident.status = "resolved"
        open_incident.resolved_at = datetime.now(timezone.utc)


def run_monitoring_cycle() -> None:
    with SessionLocal() as db:
        targets = db.query(Target).filter(Target.enabled.is_(True)).all()
        for target in targets:
            run_target_check(target, db)

        metrics = collect_system_metrics()
        db.add(ServerSnapshot(**metrics.__dict__))
        db.commit()


async def monitoring_loop() -> None:
    worker_state["status"] = "running"
    while True:
        try:
            await asyncio.to_thread(run_monitoring_cycle)
            worker_state["last_run_at"] = datetime.now(timezone.utc).isoformat()
            worker_state["last_error"] = None
        except Exception as error:  # Keep one failed cycle from killing monitoring.
            worker_state["last_error"] = str(error)
            logger.exception("Monitoring cycle failed")
        await asyncio.sleep(INTERVAL_SECONDS)
