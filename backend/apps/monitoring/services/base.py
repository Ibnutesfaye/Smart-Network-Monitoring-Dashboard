from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceDTO:
    device_name: str
    hostname: str
    ip_address: str
    mac_address: str
    vendor: str
    status: str = "unknown"


@dataclass
class PingResult:
    ip: str
    online: bool
    latency_ms: Optional[float] = None


@dataclass
class TrafficDTO:
    upload_speed: float
    download_speed: float
    bandwidth_usage: float
