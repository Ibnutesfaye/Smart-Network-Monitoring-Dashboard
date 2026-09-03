
import pytest
from django.test import override_settings

from apps.devices.models import Device
from apps.devices.serializers import DeviceSerializer
from apps.monitoring.collectors.snmp import SNMPCollector
from apps.monitoring.snmp_profiles.generic import GenericProfile
from apps.monitoring.snmp_transport import PySNMPTransport, SNMPCredentials, SNMPErrorCode


class FakeTransport:
    def __init__(self, system=None, tables=None, errors=None):
        self.system = system or {}
        self.tables = tables or {}
        self.errors = errors or []

    def get(self, target, oids):
        return self.system, list(self.errors)

    def walk(self, target, roots):
        return self.tables, []


def test_generic_profile_system_interfaces_and_hc_counter_preference():
    transport = FakeTransport(
        system={"sys_name": "core-1", "sys_descr": "Example", "sys_object_id": "1.3.6.1.4.1", "sys_uptime": "12300"},
        tables={
            "if_name": {1: "xe0"}, "if_descr": {1: "uplink"}, "if_alias": {1: "WAN"},
            "if_admin_status": {1: "1"}, "if_oper_status": {1: "1"},
            "if_high_speed": {1: "1000"}, "if_hc_in_octets": {1: "5000000000"},
            "if_hc_out_octets": {1: "6000000000"}, "if_in_octets": {1: "10"}, "if_out_octets": {1: "20"},
        },
    )
    result = GenericProfile().collect(transport, "10.0.0.1")
    assert result.reachable and result.uptime_seconds == 123
    assert result.metadata["sys_name"] == "core-1"
    assert result.interfaces[0].speed_bps == 1_000_000_000
    assert result.interfaces[0].inbound_octets == 5_000_000_000
    assert result.interfaces[0].outbound_octets == 6_000_000_000
    assert result.cpu_pct is None and result.memory_pct is None


def test_generic_profile_32_bit_fallback_and_partial_errors():
    transport = FakeTransport(
        system={"sys_name": "partial"},
        tables={"if_descr": {2: "eth0"}, "if_in_octets": {2: "123"}, "if_out_octets": {2: "456"}},
        errors=[str(SNMPErrorCode.UNSUPPORTED_OID)],
    )
    result = GenericProfile().collect(transport, "10.0.0.2")
    assert result.reachable
    assert result.interfaces[0].inbound_octets == 123
    assert result.interfaces[0].outbound_octets == 456
    assert str(SNMPErrorCode.UNSUPPORTED_OID) in result.errors


@pytest.mark.parametrize("text,expected", [
    ("No SNMP response before timeout", SNMPErrorCode.TIMEOUT),
    ("authentication failure for secret-user", SNMPErrorCode.AUTH_FAILURE),
    ("No Such Object", SNMPErrorCode.UNSUPPORTED_OID),
    ("socket broke", SNMPErrorCode.TRANSPORT_ERROR),
])
def test_snmp_error_classification_is_sanitized(text, expected):
    assert PySNMPTransport._classify(RuntimeError(text)) == expected
    assert "secret-user" not in str(PySNMPTransport._classify(RuntimeError(text)))


def test_credentials_repr_redacts_v2c_and_v3_secrets():
    for credentials in (
        SNMPCredentials(version="2c", community="private-community"),
        SNMPCredentials(version="3", username="operator", auth_key="auth-secret", priv_key="priv-secret"),
    ):
        rendered = repr(credentials)
        assert "private-community" not in rendered
        assert "auth-secret" not in rendered and "priv-secret" not in rendered
        assert "<redacted>" in rendered


@pytest.mark.django_db
@override_settings(MONITORING_MODE="mock")
def test_device_serializer_never_contains_snmp_credentials():
    device = Device.objects.create(device_name="snmp", ip_address="10.0.0.1", snmp_enabled=True)
    serialized = str(DeviceSerializer(device).data).lower()
    for secret_name in ("community", "auth_key", "priv_key", "password", "username"):
        assert secret_name not in serialized


def test_snmp_v2c_and_v3_configuration_paths():
    with override_settings(SNMP_COMMUNITY="lab-secret"):
        assert SNMPCollector.credentials("2c").community == "lab-secret"
    with override_settings(SNMP_V3_USERNAME="operator", SNMP_V3_AUTH_KEY="a", SNMP_V3_PRIV_KEY="p", SNMP_V3_SECURITY_LEVEL="authPriv"):
        credentials = SNMPCollector.credentials("3")
        assert credentials.username == "operator" and credentials.security_level == "authPriv"


def test_invalid_snmp_configuration_is_classified_without_secret_text():
    class MinimalHLAPI:
        pass

    with pytest.raises(ValueError) as error:
        PySNMPTransport(SNMPCredentials(version="2c", community=""))._auth(MinimalHLAPI)
    assert str(SNMPErrorCode.INVALID_CONFIGURATION) in str(error.value)
