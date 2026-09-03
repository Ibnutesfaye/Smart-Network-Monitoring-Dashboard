# Deployment Guide

## Docker Compose (recommended)

```bash
cp .env.example .env
# Edit SECRET_KEY, DB passwords, EMAIL_* for production
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

## Production overlay

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Build `frontend/dist` before starting the stack and configure TLS certificates in Nginx (`docker/nginx.conf`). The production Compose file runs Daphne/ASGI and exposes only Nginx; PostgreSQL, Redis, the backend, and workers use an internal network.

## Monitoring modes

| Mode | Use case |
|------|----------|
| `mock` | Demos, CI, restricted Wi-Fi, Windows without elevated privileges |
| `real` | Authorized lab networks with ping/access |

**Warning**: Real network scanning may violate policies if run without authorization. Use only on networks you own or have written permission to test.

### Linux real monitoring

- Set `MONITORING_MODE=real`
- Consider `cap_add: [NET_RAW]` on backend/celery services
- Or run collectors on host network

### Windows development

- Default to `MONITORING_MODE=mock`
- For real scans, use WSL2 with appropriate network access

## Environment checklist

- [ ] Strong `SECRET_KEY`
- [ ] `DEBUG=False`
- [ ] PostgreSQL backups configured
- [ ] Redis persistence (if required)
- [ ] SMTP for critical alert emails
- [ ] CORS origins restricted to frontend domain
- [ ] HTTPS enabled via Nginx

## GitHub Actions

CI runs on push to `main`/`develop`: backend pytest, frontend build, Docker image build on main.
