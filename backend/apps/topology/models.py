from django.core.exceptions import ValidationError
from django.db import models


class TopologyLink(models.Model):
    class LinkType(models.TextChoices):
        PHYSICAL = "physical", "Physical"
        LOGICAL = "logical", "Logical"
        WAN = "wan", "WAN"
        UPLINK = "uplink", "Uplink"
        TRUNK = "trunk", "Trunk"
        WIRELESS = "wireless", "Wireless"
        VIRTUAL = "virtual", "Virtual"
        UNKNOWN = "unknown", "Unknown"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        SNMP = "snmp", "SNMP"
        LLDP = "lldp", "LLDP"
        CDP = "cdp", "CDP"
        IMPORT = "import", "Import"

    site = models.ForeignKey("devices.Site", on_delete=models.CASCADE, related_name="topology_links")
    source_device = models.ForeignKey("devices.Device", on_delete=models.CASCADE, related_name="outgoing_topology_links")
    source_interface = models.ForeignKey("devices.DeviceInterface", null=True, blank=True, on_delete=models.SET_NULL, related_name="outgoing_topology_links")
    target_device = models.ForeignKey("devices.Device", on_delete=models.CASCADE, related_name="incoming_topology_links")
    target_interface = models.ForeignKey("devices.DeviceInterface", null=True, blank=True, on_delete=models.SET_NULL, related_name="incoming_topology_links")
    link_type = models.CharField(max_length=16, choices=LinkType.choices, default=LinkType.UNKNOWN)
    discovery_source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)
    confidence = models.PositiveSmallIntegerField(default=100)
    status = models.CharField(max_length=16, default="unknown", db_index=True)
    bandwidth_bps = models.PositiveBigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["site", "status"]), models.Index(fields=["source_device", "target_device"])]
        constraints = [
            models.CheckConstraint(condition=~models.Q(source_device=models.F("target_device")), name="topology_no_self_link"),
            models.UniqueConstraint(fields=["source_device", "target_device", "source_interface", "target_interface"], name="unique_topology_link"),
        ]

    def clean(self):
        if self.source_device_id == self.target_device_id:
            raise ValidationError("A topology link cannot connect a device to itself.")
        if self.source_device_id and self.source_device.site_id != self.site_id:
            raise ValidationError("Source device must belong to the link site.")
        if self.target_device_id and self.target_device.site_id != self.site_id:
            raise ValidationError("Target device must belong to the link site.")
        if self.source_interface_id and self.source_interface.device_id != self.source_device_id:
            raise ValidationError("Source interface does not belong to source device.")
        if self.target_interface_id and self.target_interface.device_id != self.target_device_id:
            raise ValidationError("Target interface does not belong to target device.")
