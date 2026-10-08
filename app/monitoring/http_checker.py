from dataclasses import dataclass
from time import perf_counter

import httpx


@dataclass(frozen=True)
class HttpCheckResult:
    success: bool
    status_code: int | None
    response_time_ms: float | None
    error: str | None


def check_http(url: str, timeout_seconds: float = 5.0) -> HttpCheckResult:
    """Request a URL and measure the time until its response arrives."""
    started_at = perf_counter()
    try:
        response = httpx.get(url, timeout=timeout_seconds, follow_redirects=True)
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        return HttpCheckResult(
            success=response.is_success,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            error=None if response.is_success else f"HTTP {response.status_code}",
        )
    except httpx.HTTPError as error:
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        return HttpCheckResult(
            success=False,
            status_code=None,
            response_time_ms=elapsed_ms,
            error=str(error),
        )
