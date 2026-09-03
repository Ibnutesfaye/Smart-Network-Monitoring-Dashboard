# API Documentation

## P2 operations

- `GET /api/v1/noc/summary/` — bounded operational counts and worst-first site health.
- `GET /api/v1/noc/availability/?range=24h&site={id}` — bounded stored availability history.
- `GET /api/v1/noc/traffic/?site={id}` — known aggregate traffic and top-utilized interfaces.
- `GET /api/v1/noc/problems/` — bounded alert-heavy, longest-down, and highest-latency resources.
- `/api/v1/incidents/` — paginated CRUD with `assign_to_me`, `transition`, `attach_alert`, `detach_alert`, `comments`, and `timeline` actions.
- `/api/v1/maintenance/` — paginated scheduling and cancellation with required targets.
- `GET /api/v1/topology/?site={id}` — bounded nodes and real links without historical telemetry.
- `/api/v1/topology/links/` — administrator writes and scoped authenticated reads.

Operational events use `{version, type, timestamp, data}` for `incident.*`, `maintenance.*`, and `topology.changed`; payloads exclude credentials.

Users with explicit site assignments join only matching `site_{id}_dashboard`, device, and alert groups. Administrators and legacy unassigned users retain global groups.

Base URL: `/api/v1/`

Interactive Swagger UI: `http://localhost:8000/api/schema/swagger/`

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | Obtain JWT access + refresh |
| POST | `/auth/logout/` | Blacklist refresh token |
| POST | `/auth/refresh/` | Refresh access token |
| POST | `/auth/register/` | Admin-only user registration |
| POST | `/auth/password-reset/` | Request reset email |
| GET/PATCH | `/auth/profile/` | Current user profile |

## Resources

| Resource | Endpoints |
|----------|-----------|
| Users | `GET/POST /users/`, `GET/PUT/PATCH/DELETE /users/{id}/` |
| Devices | CRUD + `GET /devices/{id}/history/`, `POST /devices/discover/` |
| Traffic | `GET /traffic/`, `GET /traffic/summary/` |
| Alerts | CRUD + `PATCH /alerts/{id}/acknowledge/`; filter by `device`, `interface`, `state`, severity/type |
| Reports | `GET /reports/`, `POST /reports/generate/`, `GET /reports/{id}/download/` |
| Analytics | `/analytics/device-growth/`, `traffic-trends/`, `alert-trends/`, `security-stats/` |
| Dashboard | `GET /dashboard/metrics/` |
| Topology | `GET /topology/` |
| Activity Logs | `GET /activity-logs/` (admin) |
| Organizations | CRUD `/organizations/` |
| Sites | CRUD `/sites/`, filter by `organization`, `active` |
| Network segments | CRUD `/network-segments/` |
| Interfaces | `GET /interfaces/`, filter by `device`, `oper_status` |
| Device telemetry | `GET /telemetry/devices/{id}/?range=24h` |
| Interface telemetry | `GET /telemetry/interfaces/{id}/?range=24h` |

Telemetry ranges are mandatory server-side bounded values: `1h`, `6h`, `24h`, `7d`, or `30d`. Responses are capped/downsampled to 1,000 points.

## WebSocket

Connect with `?token=<access_token>`:

- `ws/dashboard/` — metrics, traffic, alerts
- `ws/devices/` — device status updates
- `ws/alerts/` — new alerts

## Pagination

List endpoints return `{ count, next, previous, results }` with `?page=` and `?page_size=`.

## Filtering

Use query params: `?search=`, `?status=`, `?alert_level=`, `?ordering=-created_at`
