from django.conf import settings

from .base import MonitoringResult
from .mock import MockCollector
from .ping import PingCollector
from .snmp import SNMPCollector


class RealCollector:
    def collect_device(self, device):
        ping = PingCollector().collect_device(device)
        if not device.snmp_enabled:
            return ping
        snmp = SNMPCollector().collect_device(device)
        return MonitoringResult(reachable=ping.reachable or snmp.reachable, latency_ms=ping.latency_ms, packet_loss_pct=ping.packet_loss_pct, uptime_seconds=snmp.uptime_seconds, cpu_pct=snmp.cpu_pct, memory_pct=snmp.memory_pct, interfaces=snmp.interfaces, metadata=snmp.metadata, errors=snmp.errors, source="ping+snmp")


def get_collector():
    return MockCollector() if settings.MONITORING_MODE == "mock" else RealCollector()


__all__ = ["MockCollector", "PingCollector", "get_collector"]
