from apps.monitoring.collectors.base import InterfaceResult, MonitoringResult

from .base import BaseSNMPProfile

SYSTEM_OIDS = {
    "sys_descr": "1.3.6.1.2.1.1.1.0",
    "sys_object_id": "1.3.6.1.2.1.1.2.0",
    "sys_uptime": "1.3.6.1.2.1.1.3.0",
    "sys_name": "1.3.6.1.2.1.1.5.0",
}
TABLE_OIDS = {
    "if_descr": "1.3.6.1.2.1.2.2.1.2",
    "if_type": "1.3.6.1.2.1.2.2.1.3",
    "if_mtu": "1.3.6.1.2.1.2.2.1.4",
    "if_speed": "1.3.6.1.2.1.2.2.1.5",
    "if_phys_address": "1.3.6.1.2.1.2.2.1.6",
    "if_admin_status": "1.3.6.1.2.1.2.2.1.7",
    "if_oper_status": "1.3.6.1.2.1.2.2.1.8",
    "if_in_octets": "1.3.6.1.2.1.2.2.1.10",
    "if_in_discards": "1.3.6.1.2.1.2.2.1.13",
    "if_in_errors": "1.3.6.1.2.1.2.2.1.14",
    "if_out_octets": "1.3.6.1.2.1.2.2.1.16",
    "if_out_discards": "1.3.6.1.2.1.2.2.1.19",
    "if_out_errors": "1.3.6.1.2.1.2.2.1.20",
    "if_name": "1.3.6.1.2.1.31.1.1.1.1",
    "if_hc_in_octets": "1.3.6.1.2.1.31.1.1.1.6",
    "if_hc_out_octets": "1.3.6.1.2.1.31.1.1.1.10",
    "if_high_speed": "1.3.6.1.2.1.31.1.1.1.15",
    "if_alias": "1.3.6.1.2.1.31.1.1.1.18",
}


def _integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _state(value):
    return {1: "up", 2: "down", 3: "testing"}.get(_integer(value), "unknown")


class GenericProfile(BaseSNMPProfile):
    def collect(self, transport, target):
        system, errors = transport.get(target, SYSTEM_OIDS)
        tables, table_errors = transport.walk(target, TABLE_OIDS)
        errors.extend(table_errors)
        indexes = sorted({index for values in tables.values() for index in values})
        interfaces = []
        for index in indexes:
            def value(key, idx=index):
                return tables.get(key, {}).get(idx)

            high_speed = _integer(value("if_high_speed"))
            speed = high_speed * 1_000_000 if high_speed else _integer(value("if_speed"))
            interfaces.append(InterfaceResult(
                if_index=index,
                name=str(value("if_name") or value("if_descr") or f"if{index}"),
                description=str(value("if_descr") or ""), alias=str(value("if_alias") or ""),
                admin_status=_state(value("if_admin_status")), oper_status=_state(value("if_oper_status")),
                speed_bps=speed, mtu=_integer(value("if_mtu")), interface_type=str(value("if_type") or ""),
                mac_address=str(value("if_phys_address") or ""),
                inbound_octets=_integer(value("if_hc_in_octets")) if value("if_hc_in_octets") is not None else _integer(value("if_in_octets")),
                outbound_octets=_integer(value("if_hc_out_octets")) if value("if_hc_out_octets") is not None else _integer(value("if_out_octets")),
                inbound_errors=_integer(value("if_in_errors")), outbound_errors=_integer(value("if_out_errors")),
                inbound_discards=_integer(value("if_in_discards")), outbound_discards=_integer(value("if_out_discards")),
            ))
        uptime_ticks = _integer(system.get("sys_uptime"))
        return MonitoringResult(reachable=bool(system or interfaces), uptime_seconds=uptime_ticks // 100 if uptime_ticks is not None else None, interfaces=tuple(interfaces), metadata={"sys_name": str(system.get("sys_name", "")), "sys_descr": str(system.get("sys_descr", "")), "sys_object_id": str(system.get("sys_object_id", ""))}, errors=tuple(errors), source="snmp")
