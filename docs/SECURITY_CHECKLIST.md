# Security Checklist

## Completed

- Virtual environment and generated database are excluded from Git.
- `.env` files are excluded; `.env.example` contains no secrets.
- API input fields have length, type, and TCP-port validation.
- Network checks use timeouts instead of waiting indefinitely.
- The deployment service runs with `NoNewPrivileges=true`.
- Production mode disables the interactive FastAPI documentation pages.
- The deployment plan does not expose SQLite or Uvicorn directly.

## Required before public production use

- Add authentication before exposing target-management and monitoring APIs publicly.
- Add authorization so only approved users can edit targets.
- Add SSRF protections and an explicit target allowlist if the dashboard is internet-facing.
- Configure HTTPS through Nginx and a valid certificate.
- Store production configuration through the service manager or a secrets system.
- Restrict SSH to the administrator's current IP address.
- Configure backups and log rotation.
- Review AWS billing alerts and remove unused resources.
