import asyncio
from dataclasses import dataclass
from enum import StrEnum


class SNMPErrorCode(StrEnum):
    TIMEOUT = "TIMEOUT"
    AUTH_FAILURE = "AUTH_FAILURE"
    UNSUPPORTED_OID = "UNSUPPORTED_OID"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"


@dataclass(frozen=True, repr=False)
class SNMPCredentials:
    version: str
    community: str = ""
    username: str = ""
    auth_key: str = ""
    priv_key: str = ""
    security_level: str = "authPriv"
    auth_protocol: str = "SHA256"
    priv_protocol: str = "AES128"

    def __repr__(self):
        return f"SNMPCredentials(version={self.version!r}, security_level={self.security_level!r}, secrets=<redacted>)"


class PySNMPTransport:
    def __init__(self, credentials, timeout=2, retries=1, port=161):
        self.credentials, self.timeout, self.retries, self.port = credentials, timeout, retries, port

    def _auth(self, hlapi):
        c = self.credentials
        if c.version == "2c":
            if not c.community:
                raise ValueError(SNMPErrorCode.INVALID_CONFIGURATION)
            return hlapi.CommunityData(c.community, mpModel=1)
        if not c.username or c.security_level not in {"noAuthNoPriv", "authNoPriv", "authPriv"}:
            raise ValueError(SNMPErrorCode.INVALID_CONFIGURATION)
        if c.security_level == "noAuthNoPriv":
            return hlapi.UsmUserData(c.username, authProtocol=hlapi.usmNoAuthProtocol, privProtocol=hlapi.usmNoPrivProtocol)
        auth = {"SHA": hlapi.usmHMACSHAAuthProtocol, "SHA256": hlapi.usmHMAC192SHA256AuthProtocol}.get(c.auth_protocol)
        if auth is None or not c.auth_key:
            raise ValueError(SNMPErrorCode.INVALID_CONFIGURATION)
        if c.security_level == "authNoPriv":
            return hlapi.UsmUserData(c.username, c.auth_key, authProtocol=auth, privProtocol=hlapi.usmNoPrivProtocol)
        priv = {"AES128": hlapi.usmAesCfb128Protocol}.get(c.priv_protocol)
        if priv is None or not c.priv_key:
            raise ValueError(SNMPErrorCode.INVALID_CONFIGURATION)
        return hlapi.UsmUserData(c.username, c.auth_key, c.priv_key, authProtocol=auth, privProtocol=priv)

    @staticmethod
    def _classify(error):
        if isinstance(error, ValueError) and error.args and error.args[0] == SNMPErrorCode.INVALID_CONFIGURATION:
            return SNMPErrorCode.INVALID_CONFIGURATION
        text = str(error).lower()
        if "timeout" in text or "no snmp response" in text:
            return SNMPErrorCode.TIMEOUT
        if "authentication" in text or "unknown user" in text or "authorization" in text:
            return SNMPErrorCode.AUTH_FAILURE
        if "no such" in text:
            return SNMPErrorCode.UNSUPPORTED_OID
        return SNMPErrorCode.TRANSPORT_ERROR

    def get(self, target, oids):
        return asyncio.run(self._get(target, oids))

    async def _get(self, target, oids):
        from pysnmp.hlapi.v3arch import asyncio as hlapi
        try:
            transport = await hlapi.UdpTransportTarget.create((target, self.port), timeout=self.timeout, retries=self.retries)
            error, status, _, binds = await hlapi.get_cmd(hlapi.SnmpEngine(), self._auth(hlapi), transport, hlapi.ContextData(), *[hlapi.ObjectType(hlapi.ObjectIdentity(oid)) for oid in oids.values()])
            if error or status:
                return {}, [str(self._classify(error or status))]
            return {name: bind[1].prettyPrint() for name, bind in zip(oids, binds)}, []
        except Exception as exc:
            return {}, [str(self._classify(exc))]

    def walk(self, target, roots):
        return asyncio.run(self._walk(target, roots))

    async def _walk(self, target, roots):
        from pysnmp.hlapi.v3arch import asyncio as hlapi
        output, errors = {}, []
        for name, root in roots.items():
            output[name] = {}
            try:
                transport = await hlapi.UdpTransportTarget.create((target, self.port), timeout=self.timeout, retries=self.retries)
                async for error, status, _, binds in hlapi.walk_cmd(hlapi.SnmpEngine(), self._auth(hlapi), transport, hlapi.ContextData(), hlapi.ObjectType(hlapi.ObjectIdentity(root)), lexicographicMode=False):
                    if error or status:
                        errors.append(str(self._classify(error or status)))
                        break
                    for oid, value in binds:
                        index = int(oid.prettyPrint().rsplit(".", 1)[-1])
                        output[name][index] = value.prettyPrint()
            except Exception as exc:
                errors.append(str(self._classify(exc)))
        return output, sorted(set(errors))
