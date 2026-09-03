from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrator"
        NETWORK_ANALYST = "network_analyst", "Network Analyst"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.NETWORK_ANALYST,
    )
    sites = models.ManyToManyField("devices.Site", blank=True, related_name="authorized_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR

    @property
    def is_network_analyst(self):
        return self.role == self.Role.NETWORK_ANALYST
