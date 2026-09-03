import random
import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.alerts.models import Alert, AlertRule
from apps.audit.models import ActivityLog
from apps.devices.models import Device, DeviceStatusHistory
from apps.traffic.models import TrafficSample

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data for SNMADMDCP"

    def add_arguments(self, parser):
        parser.add_argument("--noinput", action="store_true")
        parser.add_argument("--allow-production", action="store_true")

    def handle(self, *args, **options):
        production = os.getenv("DJANGO_SETTINGS_MODULE", "").endswith(".prod")
        allowed = os.getenv("ALLOW_DEMO_SEED", "False").lower() == "true"
        if production and not (allowed and options["allow_production"]):
            self.stderr.write("Demo seeding is disabled in production.")
            return
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@snmadmdcp.local",
                "role": "administrator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if _:
            admin.set_password("admin123")
            admin.save()

        analyst, _ = User.objects.get_or_create(
            username="analyst",
            defaults={"email": "analyst@snmadmdcp.local", "role": "network_analyst"},
        )
        if _:
            analyst.set_password("analyst123")
            analyst.save()

        devices_data = [
            ("Router-GW", "192.168.1.1", "00:1A:2B:3C:4D:01", "Cisco", "online"),
            ("Workstation-01", "192.168.1.10", "00:1A:2B:3C:4D:02", "Dell", "online"),
            ("Server-DB", "192.168.1.20", "00:1A:2B:3C:4D:03", "HP", "online"),
            ("Printer-Office", "192.168.1.30", "00:1A:2B:3C:4D:04", "Canon", "offline"),
            ("NAS-Storage", "192.168.1.40", "00:1A:2B:3C:4D:05", "Synology", "online"),
        ]
        for name, ip, mac, vendor, status in devices_data:
            device, _ = Device.objects.get_or_create(
                ip_address=ip,
                defaults={
                    "device_name": name,
                    "hostname": name.lower(),
                    "mac_address": mac,
                    "vendor": vendor,
                    "status": status,
                    "last_seen": timezone.now(),
                    "is_known": True,
                },
            )

        now = timezone.now()
        for day in range(7):
            for hour in range(0, 24, 2):
                ts = now - timedelta(days=day, hours=hour)
                TrafficSample.objects.get_or_create(
                    device=None,
                    timestamp=ts,
                    defaults={
                        "upload_speed": round(random.uniform(10, 80), 2),
                        "download_speed": round(random.uniform(20, 150), 2),
                        "bandwidth_usage": round(random.uniform(30, 200), 2),
                    },
                )

        for device in Device.objects.all()[:3]:
            for i in range(5):
                DeviceStatusHistory.objects.get_or_create(
                    device=device,
                    recorded_at=now - timedelta(hours=i),
                    defaults={
                        "status": random.choice(["online", "offline"]),
                        "latency_ms": round(random.uniform(1, 30), 2),
                    },
                )

        Alert.objects.get_or_create(
            alert_type=Alert.AlertType.DEVICE_OFFLINE,
            message="Printer-Office went offline",
            defaults={
                "device": Device.objects.filter(ip_address="192.168.1.30").first(),
                "alert_level": Alert.Level.HIGH,
            },
        )
        Alert.objects.get_or_create(
            alert_type=Alert.AlertType.HIGH_BANDWIDTH,
            message="Bandwidth spike detected",
            defaults={"alert_level": Alert.Level.MEDIUM},
        )

        AlertRule.objects.get_or_create(
            name="High Bandwidth",
            defaults={
                "alert_type": Alert.AlertType.HIGH_BANDWIDTH,
                "alert_level": Alert.Level.HIGH,
                "bandwidth_threshold_mbps": 150,
                "is_active": True,
            },
        )

        ActivityLog.objects.get_or_create(
            user=admin,
            action="login",
            description="Admin logged in",
            defaults={"ip_address": "127.0.0.1"},
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded. admin/admin123 analyst/analyst123"))
