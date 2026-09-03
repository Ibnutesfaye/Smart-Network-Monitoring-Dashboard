# SNMP Monitoring Guide

## Support status

| Capability | Status |
| --- | --- |
| PySNMP transport | Implemented |
| SNMPv2c | Implemented; intended for authorized labs |
| SNMPv3 `noAuthNoPriv`, `authNoPriv`, `authPriv` | Implemented |
| Generic MIB-II / IF-MIB profile | Implemented and mock-tested |
| Real authorized hardware | Not tested |

SNMPv3 `authPriv` is the recommended production mode. The generic profile does not fabricate CPU or memory metrics; those remain null until a reviewed vendor profile supplies reliable OIDs.

## Secret boundary

Credentials are injected only through the process environment. They are not database fields, API serializer fields, WebSocket data, or log values.

```dotenv
SNMP_V3_USERNAME=monitoring-user
SNMP_V3_AUTH_KEY=use-an-external-secret
SNMP_V3_PRIV_KEY=use-an-external-secret
SNMP_V3_SECURITY_LEVEL=authPriv
SNMP_V3_AUTH_PROTOCOL=SHA256
SNMP_V3_PRIV_PROTOCOL=AES128
```

For an authorized v2c lab, set `SNMP_COMMUNITY` externally and select version `2c` on the device. Do not place real values in committed `.env` files.

## Standard polling

System polling includes `sysName`, `sysDescr`, `sysObjectID`, and `sysUpTime`. Interface polling includes names/descriptions/aliases, administrative and operational states, type, MTU, speed, errors, and discards. `ifHCInOctets`/`ifHCOutOctets` are preferred; `ifInOctets`/`ifOutOctets` are used only when HC values are unavailable. `ifHighSpeed` is preferred over `ifSpeed`.

Unsupported OIDs produce partial results. Internally persisted error summaries are limited to these non-secret classifications: `TIMEOUT`, `AUTH_FAILURE`, `UNSUPPORTED_OID`, `TRANSPORT_ERROR`, and `INVALID_CONFIGURATION`.

## Bounds

`SNMP_TIMEOUT_SECONDS` defaults to 2 seconds and `SNMP_RETRIES` defaults to 1, with retries capped at 3. A failed SNMP poll does not crash the worker; the combined real collector retains ping reachability and records the sanitized SNMP state.

## Vendor profiles

Profiles implement `BaseSNMPProfile` under `apps/monitoring/snmp_profiles/`. The `generic` profile is the default. Future Cisco, Juniper, MikroTik, or net-snmp profiles should add only verified vendor OIDs and must never contain credentials.
