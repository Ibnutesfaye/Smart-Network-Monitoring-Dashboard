# Developer Guide

## Project structure

```
SNMADMDCP/
├── backend/          # Django apps under apps/
├── frontend/         # React Vite SPA
├── docker/           # Nginx config
├── docs/             # Documentation
└── .github/workflows # CI
```

## Adding a Django app

1. Create app under `backend/apps/`
2. Register in `config/settings/base.py` `INSTALLED_APPS`
3. Add URLs to `config/api_urls.py`
4. Run `python manage.py makemigrations`

## Monitoring providers

Implement `NetworkMonitor` protocol in `apps/monitoring/services/`:

- `discover_devices(subnet) -> list[DeviceDTO]`
- `ping_device(ip) -> PingResult`
- `collect_traffic() -> TrafficDTO`

Register via `get_monitor()` factory using `MONITORING_MODE`.

## WebSocket events

Broadcast from `apps/monitoring/broadcast.py`. Frontend handles:

- `dashboard.update`, `traffic.sample`, `alert.created`
- `device.updated`

## Celery tasks

Defined in `apps/monitoring/tasks.py`, scheduled in `config/celery.py`.

## Running tests

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test pytest
```

Uses in-memory SQLite and eager Celery.

## Code style

- Backend: `ruff check .`
- Frontend: `npm run lint`

## Extending anomaly detection

Replace rule-based `AnomalyDetector` in `apps/monitoring/anomaly.py` with ML model (e.g. sklearn isolation forest).

## API schema

Regenerate OpenAPI at `/api/schema/` via drf-spectacular. Document new endpoints in `docs/api-docs.md`.
