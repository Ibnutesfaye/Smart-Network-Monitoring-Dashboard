# Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose
Define requirements for the Smart Network Monitoring and Device Management Dashboard (SNMADMDCP).

### 1.2 Scope
Web platform for network administrators and analysts to monitor devices, traffic, alerts, and generate reports.

## 2. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | JWT authentication with refresh tokens | High |
| FR-02 | Role-based access (Administrator, Network Analyst) | High |
| FR-03 | Device discovery and CRUD | High |
| FR-04 | Online/offline monitoring with ping latency | High |
| FR-05 | Traffic sampling and visualization | High |
| FR-06 | Security alerts with severity levels | High |
| FR-07 | Report generation (PDF, Excel, CSV) | High |
| FR-08 | Real-time updates via WebSocket | High |
| FR-09 | Network topology visualization | Medium |
| FR-10 | Analytics dashboards | Medium |
| FR-11 | Audit activity logging | Medium |
| FR-12 | Email on critical alerts | Medium |

## 3. Non-Functional Requirements

- Response time: API < 500ms for list endpoints
- Availability: 99% uptime target in production
- Security: HTTPS, JWT, rate-limited login, input validation
- Scalability: Horizontal scaling via Celery workers

## 4. User Roles

- **Administrator**: Full access including user management and report generation
- **Network Analyst**: Read-only on users; view/monitor devices, traffic, alerts
