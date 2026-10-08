# Cloud Network Monitoring Platform — Phase 1 Project Plan

## 1. What we are building

A web application that periodically checks selected network targets and presents their health in a dashboard.

The first useful version will answer:

- Is a target reachable?
- How long did it take to respond?
- Is an HTTP/HTTPS endpoint working?
- Is a TCP service port open?
- What is the monitoring server's CPU, memory, uptime, and basic network activity?
- What happened over time?
- Did a target go offline and recover?

The application will have three logical parts:

1. **Dashboard** — the web page a user opens.
2. **Backend API** — the service that manages targets, returns results, and exposes history.
3. **Monitoring worker** — a scheduled process that performs checks and stores results.

The first deployment will run these parts on one AWS EC2 Linux virtual machine to keep the system understandable and inexpensive. They remain separate in the design so they can later be moved to separate services.

## 2. Why we are building it

Network monitoring is a practical way to learn networking, Python, APIs, databases, Linux, cloud deployment, security, testing, and GitHub workflow in one project.

The project is also intentionally honest about what it can measure:

- **Remote availability checks:** ping, HTTP/HTTPS, and TCP port checks.
- **Local server metrics:** CPU, memory, uptime, and network counters from the machine running the monitoring service.
- **Remote CPU/memory:** not included in the first version because a remote machine must explicitly provide those metrics through an agent or secure management interface.

## 3. Networking concepts in simple language

### IP address

An IP address is a numerical address used to identify a device or service location on a network. IPv4 addresses look like `203.0.113.10`; IPv6 addresses are longer. A domain name such as `example.com` is translated to an IP address by DNS.

### Port

A port is a numbered doorway on a device. Different programs listen on different ports. HTTP commonly uses port 80, HTTPS uses 443, and SSH commonly uses 22. An open port does not automatically mean the application is healthy; it only means something accepted a connection.

### TCP

TCP is a reliable connection protocol. Before data is exchanged, the client and server establish a connection. A TCP port check tests whether that connection can be established within a time limit.

### ICMP and ping

ICMP is a network control protocol. The `ping` command sends an ICMP echo request and measures whether an echo reply returns. Some firewalls block ICMP, so a failed ping does not always prove that a server is offline.

### Latency

Latency is the time required for a request to travel to a target and for a response to return. It is usually measured in milliseconds. A larger value means a slower response, but one measurement is not enough to identify a problem.

### HTTP and HTTPS

HTTP is the protocol used by websites and web APIs. HTTPS is HTTP protected by TLS encryption. An HTTP check can verify DNS, connection, TLS, status code, and response time—not merely whether a port is open.

### Cloud VM

A cloud virtual machine is a computer rented from a provider such as AWS. An EC2 instance is an AWS virtual machine. It has an operating system, private network identity, and—when configured—public internet access.

### API

An API is a defined way for programs to communicate. The dashboard will call backend endpoints such as “list targets” and “get recent results,” and the backend will return structured JSON data.

### Database

A database stores information so it remains available after a process restarts. We need it for targets, check results, incidents, and historical charts. SQLite is appropriate for local development and a small single-machine demonstration; PostgreSQL is the safer long-term cloud choice when the system grows.

## 4. Requirements

### Functional requirements

- Add, view, edit, enable, and disable monitoring targets.
- Support target types: host/ping, HTTP/HTTPS URL, and TCP host plus port.
- Run checks on a fixed schedule.
- Record timestamp, check type, success/failure, latency or response time, and an error message when relevant.
- Display current status and recent history in a browser dashboard.
- Show monitoring-server CPU, memory, uptime, and basic network counters.
- Detect transitions such as healthy-to-failing and failing-to-healthy.
- Store alert events and show them in the dashboard.
- Validate user input and never store secrets in source code.
- Provide health endpoints for deployment and troubleshooting.

### Non-functional requirements

- Beginner-readable Python and SQL.
- Clear separation between API, monitoring logic, database access, and frontend.
- Configurable timeouts and check intervals.
- Tests for normal, failed, and recovery cases.
- Logs that help diagnose failures without exposing sensitive data.
- Safe default network exposure and documented limitations.

## 5. Recommended technology stack

| Area | Choice | Reason |
|---|---|---|
| Backend | Python + FastAPI | Readable, modern, automatic API documentation, good validation support |
| Frontend | HTML, CSS, and browser JavaScript | Avoids a build system at the start while still allowing a professional UI |
| Database | SQLite locally; PostgreSQL-ready design | Zero setup for learning, with a migration path for cloud growth |
| ORM/data access | SQLAlchemy | Keeps database code organized and supports SQLite/PostgreSQL |
| Validation | Pydantic through FastAPI | Rejects malformed targets before checks run |
| HTTP checks | Python HTTP client library | Handles URLs, timeouts, status codes, and TLS errors |
| System metrics | `psutil` | Cross-platform CPU, memory, uptime, and network counters |
| Scheduling | A simple worker loop initially | Fewer moving parts; later it can move to a task queue if needed |
| Web serving | Uvicorn during development; Nginx + Uvicorn in deployment | Simple local run, more appropriate production proxy later |
| Version control | Git and GitHub | History, portfolio presentation, and safe collaboration |
| Cloud | One AWS EC2 Linux instance initially | Matches the learning goal and keeps the first deployment understandable |

We will not introduce React, Docker, Kubernetes, Redis, or a message queue in the first milestone. They are useful in larger systems but would hide the networking fundamentals we want to learn.

## 6. Architecture

```text
Browser
   |
   | HTTP/HTTPS
   v
Nginx (cloud deployment only)
   |
   v
FastAPI backend  <------>  SQLite/PostgreSQL database
   |
   +------> Monitoring worker
                 |
                 +--> ICMP/ping checks (where permitted)
                 +--> HTTP/HTTPS checks
                 +--> TCP connection checks
                 +--> Local EC2 metrics via psutil
                 |
                 +--> Target servers and services
```

### Data flow

1. A user adds a target through the dashboard.
2. The API validates and stores the target.
3. The worker reads enabled targets at each interval.
4. The worker performs a check with a timeout.
5. The result is stored with its timestamp.
6. The dashboard requests current status, history, and alerts from the API.
7. A change from success to failure creates an incident/alert record; recovery closes it.

### Important boundary

Remote checks tell us whether a service responds from the monitoring VM's network location. They do not provide the remote server's CPU or memory. To support those later, we can install a small authenticated agent on each target or integrate a cloud metrics service.

## 7. Initial data model

- **targets:** name, type, host/URL, port, enabled flag, interval, timeout, creation time.
- **check_results:** target, check time, success flag, latency, HTTP status, error text, and optional metadata.
- **server_snapshots:** check time, CPU percentage, memory percentage, uptime seconds, bytes sent, and bytes received.
- **incidents:** target, opened time, resolved time, reason, and status.

## 8. Folder structure

```text
cloud-network-monitor/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # HTTP routes and request/response models
│   ├── db/                  # Database setup and models
│   ├── monitoring/          # Ping, HTTP, TCP, and system metric checks
│   ├── services/            # Scheduling, status transitions, and alerts
│   └── static/               # Dashboard HTML, CSS, and JavaScript
├── tests/                    # Automated tests
├── docs/                     # Architecture, testing, deployment notes
├── screenshots/              # Portfolio screenshots
├── .env.example              # Names of configuration values, no secrets
├── .gitignore
├── requirements.txt
└── README.md
```

This is the intended structure; it will be created incrementally during Phase 2.

## 9. Development roadmap

### Milestone 1 — Local foundation

Create the Python environment, install dependencies, start FastAPI, and serve a simple health endpoint and dashboard shell.

### Milestone 2 — First monitoring checks

Implement host reachability, latency, HTTP/HTTPS, and TCP port checks independently. Each check will have a small test and a manual command to run it.

### Milestone 3 — Persistence and scheduling

Add the database, target management API, periodic worker, result history, and incident transitions.

### Milestone 4 — Dashboard

Build status cards, target table, history charts, server metrics, and alert history.

### Milestone 5 — Reliability and security

Add validation, timeouts, logging, configuration through environment variables, authentication decision, and failure/recovery tests.

### Milestone 6 — AWS deployment

Deploy to an EC2 Linux VM, configure a narrow security group, run the application as a service, and add HTTPS when the deployment is stable.

### Milestone 7 — Portfolio packaging

Write the README, add architecture and screenshots, document tests and limitations, and write truthful resume bullets based on the completed features.

## 10. Cloud deployment plan

The first cloud version will use one small Linux EC2 instance. The instance will run the API, worker, database, and web server. The security group will initially allow SSH only from the developer's IP and web traffic only on the required ports. We will not open the database port publicly.

Before any AWS action, we will identify whether it can incur charges, check the current free-tier rules, and ask for confirmation if a paid resource or uncertain billing risk is involved.

Later improvements may include PostgreSQL, a separate worker, an agent on monitored servers, HTTPS with a domain name, backups, and a managed metrics/alerting service.

## 11. Testing plan

- Unit-test each check with reachable and unreachable examples.
- Test a closed TCP port and an open TCP port.
- Test HTTP success, HTTP error status, timeout, invalid URL, and TLS failure.
- Test that blocked ICMP is reported as “ping failed,” not automatically as “server definitely offline.”
- Test database insertion and retrieval.
- Test status transitions and recovery alerts.
- Test dashboard data after a worker run.
- Test restart behavior and configuration loading.
- Test input validation, secret handling, and production debug settings.
- Test deployment health endpoint and service restart.

## 12. Known first-version limitations

- ICMP may be blocked by firewalls or unavailable without elevated permissions.
- One monitoring location cannot represent the whole internet.
- SQLite is not ideal for many concurrent writers or multiple application instances.
- CPU and memory are local metrics unless a target agent is added.
- Basic alerts may be dashboard-only before email is introduced.
- A public cloud deployment must be secured before it is used for real production monitoring.

## 13. Definition of done for the first portfolio release

- A user can add at least one target and see live status.
- The worker records repeated results.
- The dashboard shows current status and history.
- At least one failure and recovery event is visible.
- Local system metrics are displayed.
- Automated tests cover the major checks.
- The application runs locally from documented commands.
- The application is deployed to AWS only after security review.
- GitHub contains no credentials or private keys.
- README, architecture diagram, screenshots, limitations, and truthful resume text are complete.
