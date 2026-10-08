import subprocess

import httpx

from app.monitoring.http_checker import check_http
from app.monitoring.ping_checker import check_ping
from app.monitoring.tcp_checker import check_tcp


def test_http_checker_reports_success(monkeypatch):
    class FakeResponse:
        is_success = True
        status_code = 200

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: FakeResponse())

    result = check_http("https://example.test")

    assert result.success is True
    assert result.status_code == 200
    assert result.error is None
    assert result.response_time_ms is not None


def test_tcp_checker_reports_connection_failure(monkeypatch):
    def refuse_connection(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr("socket.create_connection", refuse_connection)

    result = check_tcp("127.0.0.1", 59999)

    assert result.success is False
    assert result.error == "connection refused"


def test_ping_checker_parses_success(monkeypatch):
    completed = subprocess.CompletedProcess(
        args=["ping"],
        returncode=0,
        stdout="Reply from 127.0.0.1: time<1ms",
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)
    monkeypatch.setattr("platform.system", lambda: "Windows")

    result = check_ping("127.0.0.1")

    assert result.success is True
    assert result.latency_ms == 1.0
    assert result.packet_loss_percent == 0.0
