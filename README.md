# PulseWatch Network Monitor

PulseWatch is a beginner-friendly cloud network monitoring platform built with Python and FastAPI. It checks selected targets and presents their health through a web dashboard.

## Current features

- HTTP/HTTPS availability and response-time checks
- TCP port availability checks
- ICMP host reachability and latency checks where permitted
- Local monitoring-server CPU, memory, uptime, and network statistics
- SQLite persistence through SQLAlchemy
- Automatic background monitoring every 30 seconds
- Incident creation when a target fails and resolution when it recovers
- Dashboard showing targets, server metrics, and recent incidents

## Technology

- Python 3.13
- FastAPI and Uvicorn
- SQLite and SQLAlchemy
- HTTPX
- psutil
- HTML, CSS, and browser JavaScript

## Run locally

Create and activate a virtual environment, then install dependencies:

```powershell
& "C:/Program Files/Python313/python.exe" -m venv .venv
& ".venv/Scripts/python.exe" -m pip install -r requirements.txt
```

Start the development server:

```powershell
& ".venv/Scripts/python.exe" -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in a browser. API documentation is available at `http://127.0.0.1:8000/docs`.

## Configuration

Runtime settings are read from environment variables. See [.env.example](.env.example) for the available names. `MONITOR_INTERVAL_SECONDS` controls how often the background worker runs and defaults to 30 seconds. The application does not require secrets for the current local features.

For a cloud process, set environment variables in the service manager rather than committing a `.env` file.

## Important limitations

- CPU and memory metrics currently describe the machine running PulseWatch, not arbitrary remote servers.
- ICMP can be blocked by firewalls, so a failed ping is not conclusive proof of a complete outage.
- SQLite is intended for local development and a small single-machine deployment.
- Email notifications and authentication are planned future improvements.

## Project planning

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the architecture, roadmap, testing plan, and AWS deployment plan.

The AWS preparation guide is in [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md).

## Security

Do not commit passwords, API keys, private keys, `.env` files, or cloud credentials. The repository ignores the local virtual environment, generated database data, and environment files.
