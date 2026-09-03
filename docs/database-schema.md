# Database Schema

## accounts_user

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| username | VARCHAR(150) UNIQUE | |
| email | VARCHAR(254) | |
| password | VARCHAR(128) | Hashed |
| role | VARCHAR(32) | administrator / network_analyst |
| created_at | TIMESTAMPTZ | |

## devices_device

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| device_name | VARCHAR(255) | |
| hostname | VARCHAR(255) | |
| ip_address | INET UNIQUE | |
| mac_address | VARCHAR(17) | |
| vendor | VARCHAR(255) | |
| status | VARCHAR(16) | online/offline/unknown |
| last_seen | TIMESTAMPTZ | Indexed |
| last_latency_ms | FLOAT | |
| is_known | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

## traffic_trafficsample

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| device_id | FK nullable | NULL = global sample |
| upload_speed | FLOAT | Mbps |
| download_speed | FLOAT | Mbps |
| bandwidth_usage | FLOAT | Mbps |
| timestamp | TIMESTAMPTZ | Indexed |

## alerts_alert

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| device_id | FK nullable | |
| alert_level | VARCHAR(16) | low/medium/high/critical |
| alert_type | VARCHAR(32) | |
| message | TEXT | |
| acknowledged | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

## reports_report

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| report_type | VARCHAR(16) | daily/weekly/monthly |
| export_format | VARCHAR(8) | pdf/excel/csv |
| generated_by_id | FK | |
| file_path | VARCHAR(512) | |
| period_start | TIMESTAMPTZ | |
| period_end | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

## audit_activitylog

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| user_id | FK nullable | |
| action | VARCHAR(64) | |
| description | TEXT | |
| ip_address | INET | |
| created_at | TIMESTAMPTZ | |
# P1 monitoring entities

The monitoring hierarchy is `Organization -> Site -> NetworkSegment -> Device -> DeviceInterface`. A segment is the authorization boundary for real monitoring and discovery. `DeviceTelemetry` and `InterfaceTelemetry` hold indexed historical samples; current interface counters/state stay on `DeviceInterface`.

Alerts retain their legacy fields and add lifecycle state, deduplication key, trigger/acknowledgement/resolution timestamps, occurrence count, operator, and note. Alert rules may be scoped to a site or device.
