import ipaddress

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Site(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="sites")
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=64)
    description = models.TextField(blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    address = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "code"], name="uniq_site_org_code")]
        indexes = [models.Index(fields=["organization", "active"])]

    def __str__(self):
        return f"{self.organization.code}/{self.code}"


def validate_safe_cidr(value):
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise ValidationError("Enter a valid IPv4 or IPv6 CIDR.") from exc
    if network.prefixlen == 0:
        raise ValidationError("A default-route CIDR is not an authorized monitoring boundary.")


class NetworkSegment(models.Model):
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="network_segments")
    name = models.CharField(max_length=255)
    cidr = models.CharField(max_length=64, validators=[validate_safe_cidr])
    vlan_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    monitoring_enabled = models.BooleanField(default=True)
    discovery_enabled = models.BooleanField(default=False)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "cidr"], name="uniq_segment_site_cidr"),
            models.CheckConstraint(condition=models.Q(vlan_id__isnull=True) | models.Q(vlan_id__lte=4094), name="valid_vlan_id"),
        ]
        indexes = [models.Index(fields=["site", "active", "monitoring_enabled"])]

    def clean(self):
        validate_safe_cidr(self.cidr)
        self.cidr = str(ipaddress.ip_network(self.cidr, strict=False))


class Device(models.Model):
    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        UNKNOWN = "unknown", "Unknown"
        DEGRADED = "degraded", "Degraded"
        MAINTENANCE = "maintenance", "Maintenance"

    class DeviceType(models.TextChoices):
        ROUTER = "router", "Router"
        SWITCH = "switch", "Switch"
        FIREWALL = "firewall", "Firewall"
        SERVER = "server", "Server"
        WIRELESS_AP = "wireless_ap", "Wireless AP"
        CONTROLLER = "controller", "Controller"
        PRINTER = "printer", "Printer"
        WORKSTATION = "workstation", "Workstation"
        IOT = "iot", "IoT"
        UPS = "ups", "UPS"
        STORAGE = "storage", "Storage"
        VM = "vm", "Virtual machine"
        HYPERVISOR = "hypervisor", "Hypervisor"
        UNKNOWN = "unknown", "Unknown"

    class Criticality(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="devices", null=True, blank=True)
    network_segment = models.ForeignKey(NetworkSegment, on_delete=models.PROTECT, related_name="devices", null=True, blank=True)

    device_name = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=17, blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    operating_system = models.CharField(max_length=255, blank=True)
    ipv6_address = models.GenericIPAddressField(protocol="IPv6", null=True, blank=True, unique=True)
    device_type = models.CharField(max_length=32, choices=DeviceType.choices, default=DeviceType.UNKNOWN, db_index=True)
    criticality = models.CharField(max_length=16, choices=Criticality.choices, default=Criticality.MEDIUM)
    lifecycle_status = models.CharField(max_length=32, default="active", db_index=True)
    monitoring_enabled = models.BooleanField(default=True, db_index=True)
    snmp_enabled = models.BooleanField(default=False, db_index=True)
    snmp_version = models.CharField(max_length=8, choices=[("2c", "SNMPv2c"), ("3", "SNMPv3")], default="3")
    snmp_port = models.PositiveIntegerField(default=161)
    snmp_profile = models.CharField(max_length=32, default="generic")
    snmp_status = models.CharField(max_length=32, default="disabled")
    snmp_last_error_code = models.CharField(max_length=32, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.UNKNOWN, db_index=True
    )
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)
    last_latency_ms = models.FloatField(null=True, blank=True)
    current_packet_loss = models.FloatField(null=True, blank=True)
    uptime_seconds = models.PositiveBigIntegerField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    consecutive_successes = models.PositiveIntegerField(default=0)
    first_discovered_at = models.DateTimeField(default=timezone.now)
    last_checked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    is_known = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen", "device_name"]
        indexes = [
            models.Index(fields=["status", "last_seen"]),
            models.Index(fields=["site", "status", "monitoring_enabled"]),
        ]

    def __str__(self):
        return f"{self.device_name} ({self.ip_address})"


class DeviceStatusHistory(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=16, choices=Device.Status.choices)
    latency_ms = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["device", "recorded_at"]),
        ]


class DeviceInterface(models.Model):
    class State(models.TextChoices):
        UP = "up", "Up"
        DOWN = "down", "Down"
        TESTING = "testing", "Testing"
        UNKNOWN = "unknown", "Unknown"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="interfaces")
    if_index = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)
    admin_status = models.CharField(max_length=16, choices=State.choices, default=State.UNKNOWN)
    oper_status = models.CharField(max_length=16, choices=State.choices, default=State.UNKNOWN, db_index=True)
    speed_bps = models.PositiveBigIntegerField(null=True, blank=True)
    mtu = models.PositiveIntegerField(null=True, blank=True)
    interface_type = models.CharField(max_length=64, blank=True)
    alias = models.CharField(max_length=255, blank=True)
    inbound_octets = models.PositiveBigIntegerField(null=True, blank=True)
    outbound_octets = models.PositiveBigIntegerField(null=True, blank=True)
    inbound_errors = models.PositiveBigIntegerField(null=True, blank=True)
    outbound_errors = models.PositiveBigIntegerField(null=True, blank=True)
    inbound_discards = models.PositiveBigIntegerField(null=True, blank=True)
    outbound_discards = models.PositiveBigIntegerField(null=True, blank=True)
    utilization_in_pct = models.FloatField(null=True, blank=True)
    utilization_out_pct = models.FloatField(null=True, blank=True)
    last_polled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["device", "if_index"], name="uniq_device_ifindex")]
        indexes = [models.Index(fields=["device", "oper_status"])]


class DeviceTelemetry(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="telemetry")
    timestamp = models.DateTimeField(default=timezone.now)
    latency_ms = models.FloatField(null=True, blank=True)
    packet_loss_pct = models.FloatField(null=True, blank=True)
    cpu_pct = models.FloatField(null=True, blank=True)
    memory_pct = models.FloatField(null=True, blank=True)
    uptime_seconds = models.PositiveBigIntegerField(null=True, blank=True)
    reachable = models.BooleanField()
    source = models.CharField(max_length=32, default="unknown")

    class Meta:
        ordering = ["timestamp"]
        indexes = [models.Index(fields=["device", "timestamp"])]


class InterfaceTelemetry(models.Model):
    interface = models.ForeignKey(DeviceInterface, on_delete=models.CASCADE, related_name="telemetry")
    timestamp = models.DateTimeField(default=timezone.now)
    inbound_bps = models.FloatField(null=True, blank=True)
    outbound_bps = models.FloatField(null=True, blank=True)
    utilization_in_pct = models.FloatField(null=True, blank=True)
    utilization_out_pct = models.FloatField(null=True, blank=True)
    inbound_errors_delta = models.PositiveBigIntegerField(null=True, blank=True)
    outbound_errors_delta = models.PositiveBigIntegerField(null=True, blank=True)
    inbound_discards_delta = models.PositiveBigIntegerField(null=True, blank=True)
    outbound_discards_delta = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [models.Index(fields=["interface", "timestamp"])]
