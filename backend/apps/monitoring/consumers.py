from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class AuthenticatedConsumer(AsyncJsonWebsocketConsumer):
    group_name = None

    @database_sync_to_async
    def authorized_groups(self):
        user = self.scope["user"]
        site_ids = list(user.sites.values_list("id", flat=True))
        if user.is_superuser or user.role == "administrator" or not site_ids:
            return [self.group_name]
        return [f"site_{site_id}_{self.group_name}" for site_id in site_ids]

    async def connect(self):
        if self.scope["user"].is_anonymous or not self.scope["user"].is_active:
            await self.close(code=4401)
            return
        self.group_names = await self.authorized_groups()
        for group in self.group_names:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept(subprotocol=self.scope.get("accepted_subprotocol"))

    async def disconnect(self, close_code):
        for group in getattr(self, "group_names", []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"event": "pong"})


class DashboardConsumer(AuthenticatedConsumer):
    group_name = "dashboard"

    async def dashboard_update(self, event):
        await self.send_json({"event": "dashboard.update", "data": event["data"]})

    async def traffic_update(self, event):
        await self.send_json({"event": "traffic.sample", "data": event["data"]})

    async def alert_created(self, event):
        await self.send_json({"event": "alert.created", "data": event["data"]})

    async def operational_event(self, event):
        await self.send_json(event["data"])


class DeviceConsumer(AuthenticatedConsumer):
    group_name = "devices"

    async def device_update(self, event):
        await self.send_json({"event": "device.updated", "data": event["data"]})


class AlertConsumer(AuthenticatedConsumer):
    group_name = "alerts"

    async def alert_created(self, event):
        await self.send_json({"event": "alert.created", "data": event["data"]})
