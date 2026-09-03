import ipaddress

from django.conf import settings

from apps.devices.models import NetworkSegment


class UnauthorizedTarget(ValueError):
    pass


def parse_authorized_network(cidr: str):
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        raise UnauthorizedTarget("Invalid authorized network CIDR.") from exc
    if network.prefixlen == 0:
        raise UnauthorizedTarget("Default-route networks are forbidden.")
    if network.num_addresses > settings.DISCOVERY_MAX_HOSTS:
        raise UnauthorizedTarget("Authorized network exceeds the discovery host limit.")
    return network


def is_authorized_target(ip_address, site=None) -> bool:
    if settings.MONITORING_MODE == "mock":
        return True
    try:
        target = ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    segments = NetworkSegment.objects.filter(active=True, monitoring_enabled=True)
    if site is not None:
        segments = segments.filter(site=site)
    for cidr in segments.values_list("cidr", flat=True):
        try:
            if target in parse_authorized_network(cidr):
                return True
        except UnauthorizedTarget:
            continue
    return False


def require_authorized_device(device):
    if not device.monitoring_enabled or not is_authorized_target(device.ip_address, device.site):
        raise UnauthorizedTarget("Device is outside an enabled authorized network segment.")
