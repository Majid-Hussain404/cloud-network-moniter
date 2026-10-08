import os
from dataclasses import dataclass


def positive_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("PULSEWATCH_ENVIRONMENT", "development")
    monitoring_interval_seconds: float = positive_float("MONITOR_INTERVAL_SECONDS", 30.0)


settings = Settings()
