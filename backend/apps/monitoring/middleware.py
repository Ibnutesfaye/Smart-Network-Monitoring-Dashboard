from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user(token):
    try:
        access = AccessToken(token)
        return User.objects.get(pk=access["user_id"])
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = None
        protocols = scope.get("subprotocols", [])
        if len(protocols) >= 2 and protocols[0] == "access_token":
            token = protocols[1]
            scope["accepted_subprotocol"] = "access_token"
        elif settings.WEBSOCKET_ALLOW_QUERY_AUTH:
            query_string = scope.get("query_string", b"").decode()
            token = parse_qs(query_string).get("token", [None])[0]
        if token:
            scope["user"] = await get_user(token)
        else:
            scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
