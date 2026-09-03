from django.conf import settings

from .mock_monitor import MockMonitor
from .real_monitor import RealMonitor


def get_monitor():
    if settings.MONITORING_MODE == "real":
        return RealMonitor()
    return MockMonitor()
