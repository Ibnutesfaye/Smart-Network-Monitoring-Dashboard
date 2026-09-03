# Monitoring Guide

## Processing architecture

Every monitoring cycle follows one path:

```text
Collector -> MonitoringResult -> transactional processing -> current state
          -> telemetry -> availability -> alerts -> on-commit WebSocket signal
```

Collectors return normalized, typed results and do not write models. The processing service locks the device row, rejects stale samples, records telemetry, updates interfaces, applies availability thresholds, evaluates rules, and broadcasts only after commit.

## Authorization boundary

In `mock` mode no network traffic is generated. In `real` mode a target must belong to an active, monitoring-enabled `NetworkSegment`. Discovery considers only segments that also have `discovery_enabled=True`. Default-route CIDRs are forbidden and `DISCOVERY_MAX_HOSTS` bounds every discovery network.

Clients cannot submit an arbitrary discovery CIDR; the discovery endpoint only schedules configured segments.

## Availability

- `MONITOR_FAILURE_THRESHOLD` defaults to 3. Earlier failures produce `degraded`, not `offline`.
- `MONITOR_RECOVERY_THRESHOLD` defaults to 2. A down device must succeed repeatedly before returning online.
- Older results cannot overwrite newer device state.
- Being offline is a valid result and is not retried as a task failure.

## Ping

`PingCollector` validates the IP and centralized authorization policy, invokes `ping` with an argument array, uses bounded attempts/timeouts, and calculates loss and mean latency. It never uses `shell=True`.

## SNMP foundation

`SNMPCollector` uses PySNMP through a generic MIB-II/IF-MIB profile. No default community or credentials are supplied, stored in device models, serialized, or logged. Production should prefer SNMPv3 authentication/privacy; SNMPv2c is restricted to authorized labs. Unsupported OIDs return partial normalized results. See [snmp-guide.md](snmp-guide.md). Real SNMP hardware was not available for validation.

Interface rules evaluate unexpected down state (`admin=up`, `oper=down`), telemetry-derived maximum inbound/outbound utilization, and recent error/discard deltas. They use the same pending/firing/acknowledged/resolved lifecycle and include interface identity in deduplication keys.

## Interface rates

Rates use `(new_octets - old_octets) * 8 / elapsed_seconds`. First samples, zero/negative elapsed time, resets/wraps, and values exceeding 120% of known link speed produce `NULL`. Utilization remains `NULL` when speed is unknown and is otherwise bounded to 0–100%.

## Retention

Device and interface telemetry default to 30 days (`TELEMETRY_RETENTION_DAYS`). The daily cleanup task deletes records in batches controlled by `TELEMETRY_CLEANUP_BATCH_SIZE`. Alert, audit, and legacy status history retention is independent.

## Alert lifecycle

Rules support a threshold, comparison operator, consecutive samples, recovery samples, cooldown metadata, and optional site/device scope. Active conditions share a stable deduplication key and increment occurrence counts instead of creating alert storms.

```text
PENDING -> FIRING -> ACKNOWLEDGED -> RESOLVED
```

Acknowledgement records the operator, time, and note; it does not resolve the condition. Recovery resolves firing or acknowledged alerts.
