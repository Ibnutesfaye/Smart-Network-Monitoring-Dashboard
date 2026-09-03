# System Architecture

## P2 operations layer

`apps.operations` owns incidents, incident events, plain-text comments, and maintenance windows. It consumes P1 alerts/devices/interfaces instead of duplicating telemetry. `apps.topology.TopologyLink` stores bounded operational relationships. Transactional services generate incident numbers from database primary keys, validate transitions centrally, and publish events after commit.

Administrators retain global access; analysts receive explicitly assigned sites across P2 aggregation, incidents, maintenance, topology, devices, interfaces, alerts, site resources, and Channels groups. Operational broadcasts are copied to the appropriate per-site group after commit. Legacy analysts without assignments retain global access for backward compatibility.

## Overview

SNMADMDCP is a three-tier application:

1. **Presentation**: React SPA (Vite, Tailwind, Recharts)
2. **Application**: Django REST Framework + Django Channels
3. **Data**: PostgreSQL, Redis, file storage for reports

## Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Frontend | React 19, TanStack Query | UI, charts, WebSocket client |
| API Server | Daphne/ASGI | REST + WebSocket |
| Workers | Celery + Beat | Discovery, ping, traffic, alerts |
| Cache/Broker | Redis | Channels layer, Celery broker |
| Database | PostgreSQL | Persistent storage |

## Data flow

1. Celery Beat triggers monitoring tasks
2. Monitoring service (mock or real) collects network data
3. Results persisted to PostgreSQL
4. Channels broadcasts events to WebSocket groups
5. Frontend invalidates React Query caches on events

## P1 monitoring domain

`Organization -> Site -> NetworkSegment -> Device -> DeviceInterface` models ownership and authorization. `DeviceTelemetry` and `InterfaceTelemetry` store bounded historical observations. Collectors normalize results without persistence; the monitoring processing service owns transactional persistence, availability transitions, rule evaluation, and on-commit WebSocket signaling. See [monitoring-guide.md](monitoring-guide.md).

Real collection composes authorized ICMP reachability with an optional PySNMP generic profile. SNMP secrets remain outside the database/API boundary. Interface alerts are evaluated from committed current state and per-cycle telemetry deltas inside the device transaction.

## Deployment

Production uses Docker Compose with Nginx reverse proxy, Gunicorn/Daphne backend, and static frontend build.
