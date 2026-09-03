import ipaddress
import platform
import re
import subprocess

from django.conf import settings

from apps.monitoring.authorization import require_authorized_device

from .base import BaseCollector, MonitoringResult


class PingCollector(BaseCollector):
    latency_pattern = re.compile(r"time[=<]\s*(\d+(?:[.,]\d+)?)\s*ms", re.IGNORECASE)

    def collect_device(self, device):
        require_authorized_device(device)
        target = str(ipaddress.ip_address(device.ip_address))
        attempts = settings.MONITOR_PING_ATTEMPTS
        if platform.system().lower() == "windows":
            args = ["ping", "-n", str(attempts), "-w", str(settings.MONITOR_PING_TIMEOUT_MS), target]
        else:
            timeout_seconds = max(1, settings.MONITOR_PING_TIMEOUT_MS // 1000)
            args = ["ping", "-c", str(attempts), "-W", str(timeout_seconds), target]
        try:
            completed = subprocess.run(args, capture_output=True, text=True, timeout=(attempts * settings.MONITOR_PING_TIMEOUT_MS / 1000) + 2, check=False)
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as exc:
            return MonitoringResult(reachable=False, packet_loss_pct=100.0, source="ping", errors=(type(exc).__name__,))
        matches = [float(value.replace(",", ".")) for value in self.latency_pattern.findall(completed.stdout)]
        received = len(matches)
        loss = round((attempts - received) / attempts * 100, 2)
        return MonitoringResult(reachable=completed.returncode == 0 and received > 0, latency_ms=round(sum(matches) / received, 2) if received else None, packet_loss_pct=loss, source="ping")
