import socket
from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True)
class TcpCheckResult:
    success: bool
    response_time_ms: float | None
    error: str | None


def check_tcp(host: str, port: int, timeout_seconds: float = 5.0) -> TcpCheckResult:
    """Try to establish a TCP connection and measure connection time."""
    started_at = perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
            return TcpCheckResult(True, elapsed_ms, None)
    except OSError as error:
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        return TcpCheckResult(False, elapsed_ms, str(error))
