import platform
import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PingCheckResult:
    success: bool
    latency_ms: float | None
    packet_loss_percent: float
    error: str | None


def check_ping(host: str, timeout_seconds: float = 3.0) -> PingCheckResult:
    """Send one ICMP echo request using the operating system ping command."""
    timeout_ms = max(1, round(timeout_seconds * 1000))
    if platform.system().lower() == "windows":
        command = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        command = ["ping", "-c", "1", "-W", str(max(1, round(timeout_seconds))), host]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 1,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return PingCheckResult(False, None, 100.0, str(error))

    output = f"{completed.stdout}\n{completed.stderr}"
    match = re.search(r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms", output, re.IGNORECASE)
    if completed.returncode == 0 and match:
        return PingCheckResult(True, float(match.group(1)), 0.0, None)

    return PingCheckResult(False, None, 100.0, "No ICMP response received.")
