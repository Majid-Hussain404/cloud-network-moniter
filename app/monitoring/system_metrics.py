from dataclasses import dataclass
from time import time

import psutil


@dataclass(frozen=True)
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    uptime_seconds: int
    bytes_sent: int
    bytes_received: int


def collect_system_metrics() -> SystemMetrics:
    boot_time = psutil.boot_time()
    network = psutil.net_io_counters()
    return SystemMetrics(
        cpu_percent=psutil.cpu_percent(interval=0.2),
        memory_percent=psutil.virtual_memory().percent,
        uptime_seconds=round(time() - boot_time),
        bytes_sent=network.bytes_sent,
        bytes_received=network.bytes_recv,
    )
