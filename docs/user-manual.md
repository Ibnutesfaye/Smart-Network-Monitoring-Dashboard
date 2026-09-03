# User Manual

## NOC operations workflow

Use the command center to locate the lowest-health site, then inspect Alerts, Devices, Interfaces, or Topology. Create an incident, attach related alerts, assign it, and add investigation notes. Supported lifecycle states are Open, Acknowledged, Investigating, Mitigated, Resolved, and Closed; resolved/closed incidents can reopen to Investigating.

Use Maintenance for planned work. Supply timezone-aware start/end times and site/device/interface targets. Celery activates and completes windows idempotently. Monitoring and telemetry continue; conditions remain recorded with maintenance suppression context. Cancelled windows never activate. The read-focused dark wallboard is available at `/wallboard`.

| Capability | Administrator | Network analyst |
| --- | --- | --- |
| View operational state | All sites | Assigned sites |
| Acknowledge alerts | Yes | Yes |
| Manage incidents | Yes | Assigned sites |
| Schedule maintenance | Yes | Assigned sites |
| Edit topology/device metadata | Yes | No |

## Logging in

1. Open the dashboard URL (default: http://localhost:5173)
2. Enter username and password
3. Demo accounts: `admin` / `admin123` or `analyst` / `analyst123`

## Dashboard

View total/online/offline devices, active alerts, network health score, traffic summary, and recent activity. Updates automatically via WebSocket.

## Devices

- Browse all discovered devices
- Search by name, IP, MAC, or vendor
- Filter by status
- Click a row for device detail and latency history
- **Administrators** can trigger **Run Discovery**

## Traffic

Monitor upload/download speeds and historical charts. Data refreshes from periodic sampling.

## Alerts

Security alerts show severity (Low → Critical). Click **Acknowledge** to mark handled.

## Reports

**Administrators** generate Daily/Weekly/Monthly reports in PDF, Excel, or CSV. Download when `file_path` is populated (async generation).

## Topology

Interactive graph: gateway at center, devices connected. Click a device node to open its detail page. Drag and zoom to explore.

## Settings

Toggle dark/light theme. Email notifications for critical alerts are server-configured.

## Profile

View account info and change password.

## Role differences

| Feature | Administrator | Network Analyst |
|---------|---------------|-----------------|
| User management | Yes | No |
| Device discovery trigger | Yes | No |
| Report generation | Yes | View only |
| View devices/traffic/alerts | Yes | Yes |
