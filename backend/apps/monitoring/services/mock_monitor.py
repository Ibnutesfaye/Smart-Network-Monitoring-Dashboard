import random


from .base import DeviceDTO, PingResult, TrafficDTO

MOCK_DEVICES = [
    ("Router-GW", "192.168.1.1", "00:1A:2B:3C:4D:01", "Cisco"),
    ("Workstation-01", "192.168.1.10", "00:1A:2B:3C:4D:02", "Dell"),
    ("Server-DB", "192.168.1.20", "00:1A:2B:3C:4D:03", "HP"),
    ("Printer-Office", "192.168.1.30", "00:1A:2B:3C:4D:04", "Canon"),
    ("NAS-Storage", "192.168.1.40", "00:1A:2B:3C:4D:05", "Synology"),
    ("Camera-Security", "192.168.1.50", "00:1A:2B:3C:4D:06", "Hikvision"),
    ("IoT-Sensor", "192.168.1.60", "00:1A:2B:3C:4D:07", "Espressif"),
    ("Laptop-Dev", "192.168.1.70", "00:1A:2B:3C:4D:08", "Lenovo"),
]


class MockMonitor:
    def discover_devices(self, subnet: str) -> list[DeviceDTO]:
        devices = []
        for name, ip, mac, vendor in MOCK_DEVICES:
            devices.append(
                DeviceDTO(
                    device_name=name,
                    hostname=name.lower().replace(" ", "-"),
                    ip_address=ip,
                    mac_address=mac,
                    vendor=vendor,
                    status=random.choice(["online", "online", "offline"]),
                )
            )
        if random.random() < 0.2:
            ip = f"192.168.1.{random.randint(100, 200)}"
            devices.append(
                DeviceDTO(
                    device_name=f"Unknown-{ip.split('.')[-1]}",
                    hostname="",
                    ip_address=ip,
                    mac_address="02:" + ":".join([f"{random.randint(0,255):02x}" for _ in range(5)]),
                    vendor="Unknown",
                    status="unknown",
                )
            )
        return devices

    def ping_device(self, ip: str) -> PingResult:
        online = random.random() > 0.15
        latency = round(random.uniform(1, 50), 2) if online else None
        return PingResult(ip=ip, online=online, latency_ms=latency)

    def collect_traffic(self) -> TrafficDTO:
        up = round(random.uniform(5, 120), 2)
        down = round(random.uniform(10, 250), 2)
        return TrafficDTO(
            upload_speed=up,
            download_speed=down,
            bandwidth_usage=round(up + down, 2),
        )
