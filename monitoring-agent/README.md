# Monitoring Agent (Optional)

Standalone collector placeholder. The primary monitoring logic lives in `backend/apps/monitoring/`.

To run as a separate process, import `apps.monitoring.services.get_monitor()` and invoke discovery/ping/traffic on a schedule, POSTing results to the API.

Future: package as CLI with `SUBNET_CIDR` and API token env vars.
