import logging
import ipaddress
import platform
import socket
import subprocess

import psutil
from django.conf import settings

from .base import DeviceDTO, PingResult, TrafficDTO

logger = logging.getLogger(__name__)

VENDOR_OUI = {
    "00:1A:2B": "Generic",
    "00:50:56": "VMware",
    "28:C6:8E": "Amazon",
}


def _lookup_vendor(mac: str) -> str:
    prefix = mac.upper().replace("-", ":")[:8]
    for oui, vendor in VENDOR_OUI.items():
        if prefix.startswith(oui):
            return vendor
    return "Unknown"


class RealMonitor:
    def discover_devices(self, subnet: str) -> list[DeviceDTO]:
        devices = []
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            if network.prefixlen == 0 or network.num_addresses > settings.DISCOVERY_MAX_HOSTS:
                return devices
            for address in list(network.hosts())[: settings.DISCOVERY_BATCH_SIZE]:
                ip = str(address)
                result = self.ping_device(ip)
                if result.online:
                    hostname = ""
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except (socket.herror, socket.gaierror):
                        hostname = ip
                    devices.append(
                        DeviceDTO(
                            device_name=hostname or f"Device-{ip}",
                            hostname=hostname,
                            ip_address=ip,
                            mac_address="",
                            vendor="Unknown",
                            status="online",
                        )
                    )
        except Exception as e:
            logger.warning("Discovery failed: %s", e)
        return devices

    def ping_device(self, ip: str) -> PingResult:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        try:
            output = subprocess.run(
                ["ping", param, "1", "-w", "1000", ip],
                capture_output=True,
                text=True,
                timeout=3,
            )
            online = output.returncode == 0
            latency = None
            if online and "time=" in output.stdout.lower():
                for part in output.stdout.replace(",", ".").split():
                    if "time" in part.lower() and "=" in part:
                        try:
                            latency = float(part.split("=")[-1].replace("ms", ""))
                        except ValueError:
                            pass
            return PingResult(ip=ip, online=online, latency_ms=latency)
        except Exception:
            return PingResult(ip=ip, online=False)

    def collect_traffic(self) -> TrafficDTO:
        counters = psutil.net_io_counters()
        up = round(counters.bytes_sent / (1024 * 1024), 2)
        down = round(counters.bytes_recv / (1024 * 1024), 2)
        return TrafficDTO(upload_speed=up, download_speed=down, bandwidth_usage=up + down)
