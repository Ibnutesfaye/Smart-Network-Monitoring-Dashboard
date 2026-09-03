from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.utils import timezone


@dataclass(frozen=True)
class InterfaceResult:
    if_index: int
    name: str
    admin_status: str = "unknown"
    oper_status: str = "unknown"
    speed_bps: int | None = None
    inbound_octets: int | None = None
    outbound_octets: int | None = None
    inbound_errors: int | None = None
    outbound_errors: int | None = None
    inbound_discards: int | None = None
    outbound_discards: int | None = None
    description: str = ""
    alias: str = ""
    mac_address: str = ""
    mtu: int | None = None
    interface_type: str = ""


@dataclass(frozen=True)
class MonitoringResult:
    reachable: bool
    latency_ms: float | None = None
    packet_loss_pct: float | None = None
    uptime_seconds: int | None = None
    cpu_pct: float | None = None
    memory_pct: float | None = None
    interfaces: tuple[InterfaceResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()
    source: str = "unknown"
    collected_at: datetime = field(default_factory=timezone.now)


class BaseCollector:
    def collect_device(self, device) -> MonitoringResult:
        raise NotImplementedError
