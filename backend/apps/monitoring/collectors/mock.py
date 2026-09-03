import hashlib
from datetime import datetime, timezone

from .base import BaseCollector, InterfaceResult, MonitoringResult


class MockCollector(BaseCollector):
    """Stable per-device demo metrics; no network I/O."""

    def collect_device(self, device):
        seed = int(hashlib.sha256(str(device.ip_address).encode()).hexdigest()[:8], 16)
        reachable = seed % 11 != 0
        latency = round(2 + (seed % 480) / 10, 1) if reachable else None
        return MonitoringResult(
            reachable=reachable,
            latency_ms=latency,
            packet_loss_pct=0.0 if reachable else 100.0,
            cpu_pct=float(10 + seed % 65) if reachable else None,
            memory_pct=float(20 + seed % 60) if reachable else None,
            uptime_seconds=seed % 2_000_000 if reachable else None,
            interfaces=(InterfaceResult(if_index=1, name="eth0", admin_status="up", oper_status="up" if reachable else "down", speed_bps=1_000_000_000, inbound_octets=seed * 100, outbound_octets=seed * 80),),
            source="mock",
            metadata={"generated": True},
            collected_at=datetime.fromtimestamp(seed % 2_000_000_000, tz=timezone.utc),
        )
