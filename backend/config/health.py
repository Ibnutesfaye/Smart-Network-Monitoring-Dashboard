from django.conf import settings
from django.db import connections
from redis import Redis
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LivenessView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"status": "ok"})


class ReadinessView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)


    def get(self, request):
        checks = {"database": False, "redis": False}
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                checks["database"] = cursor.fetchone()[0] == 1
        except Exception:
            pass
        try:
            redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
            checks["redis"] = bool(redis_client.ping())
        except Exception:
            pass
        ready = all(checks.values())
        return Response(
            {"status": "ready" if ready else "unavailable", "checks": checks},
            status=200 if ready else 503,
        )
