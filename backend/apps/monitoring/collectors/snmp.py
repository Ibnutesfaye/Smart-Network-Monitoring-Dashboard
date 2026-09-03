from django.conf import settings

from apps.monitoring.authorization import require_authorized_device
from apps.monitoring.snmp_profiles import get_profile
from apps.monitoring.snmp_transport import PySNMPTransport, SNMPCredentials, SNMPErrorCode

from .base import BaseCollector, MonitoringResult


class SNMPCollector(BaseCollector):
    def __init__(self, transport=None):
        self.transport = transport

    @staticmethod
    def credentials(version):
        return SNMPCredentials(version=version, community=settings.SNMP_COMMUNITY, username=settings.SNMP_V3_USERNAME, auth_key=settings.SNMP_V3_AUTH_KEY, priv_key=settings.SNMP_V3_PRIV_KEY, security_level=settings.SNMP_V3_SECURITY_LEVEL, auth_protocol=settings.SNMP_V3_AUTH_PROTOCOL, priv_protocol=settings.SNMP_V3_PRIV_PROTOCOL)

    def collect_device(self, device):
        require_authorized_device(device)
        if not device.snmp_enabled:
            return MonitoringResult(reachable=False, source="snmp", errors=(str(SNMPErrorCode.INVALID_CONFIGURATION),))
        transport = self.transport or PySNMPTransport(self.credentials(device.snmp_version), timeout=settings.SNMP_TIMEOUT_SECONDS, retries=settings.SNMP_RETRIES, port=device.snmp_port)
        return get_profile(device.snmp_profile).collect(transport, str(device.ip_address))
