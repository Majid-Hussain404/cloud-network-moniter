# AWS EC2 Deployment Guide

This guide is for the first cloud deployment. It uses one Linux EC2 instance running the API, worker, SQLite database, and dashboard.

## Cost and safety checkpoint

Creating an EC2 instance, allocating storage, assigning a public IPv4 address, or sending traffic may incur charges depending on the AWS account, region, free-tier eligibility, and selected options. Check the current AWS pricing and billing dashboard before creating resources.

Do not create resources until the cost is understood. Do not commit AWS credentials, private keys, or `.env` files to GitHub.

## Planned network layout

```text
Browser
   |
   | TCP 80/443 (web traffic)
   v
EC2 security group
   |
   +--> Nginx
          |
          +--> Uvicorn/FastAPI on 127.0.0.1:8000
```

The database remains private on the instance. It is not exposed through a security-group rule.

## Security-group rules

Start with the narrowest rules possible:

- SSH TCP 22: source = your current public IP only.
- HTTP TCP 80: source = `0.0.0.0/0` only when the dashboard is intentionally public.
- HTTPS TCP 443: source = `0.0.0.0/0` after TLS is configured.
- No public rule for SQLite, PostgreSQL, or Uvicorn port 8000.

Remove temporary rules after troubleshooting. A security group is a stateful virtual firewall around the instance.

## Instance setup outline

1. Create or select an EC2 Linux instance only after the cost checkpoint.
2. Download the SSH key once and store it outside the repository.
3. Connect with SSH using the instance public IP.
4. Install Git and Python on the VM.
5. Clone this repository.
6. Create a VM-local virtual environment and install `requirements.txt`.
7. Set environment variables through the service manager.
8. Run the application through the systemd template in `deploy/pulsewatch.service`.
9. Put Nginx in front of Uvicorn.
10. Verify `/health`, dashboard access, worker status, and logs.

## Verification checklist

- `curl http://127.0.0.1:8000/health` returns `{"status":"ok"}` on the VM.
- `curl http://127.0.0.1:8000/api/worker-status` reports `running`.
- The security group does not expose port 8000.
- The dashboard is reachable only through the intended web port.
- The VM can reach the targets that it is supposed to monitor.
- No credentials appear in Git history or application logs.
- The AWS billing dashboard has no unexpected resources.
