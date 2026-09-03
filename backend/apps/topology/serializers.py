from rest_framework import serializers

from .models import TopologyLink


class TopologyLinkSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source_device.device_name", read_only=True)
    target_name = serializers.CharField(source="target_device.device_name", read_only=True)

    class Meta:
        model = TopologyLink
        fields = "__all__"

    def validate(self, attrs):
        source = attrs.get("source_device", getattr(self.instance, "source_device", None))
        target = attrs.get("target_device", getattr(self.instance, "target_device", None))
        site = attrs.get("site", getattr(self.instance, "site", None))
        if source == target:
            raise serializers.ValidationError("A topology link cannot connect a device to itself.")
        if source and target and (source.site_id != site.id or target.site_id != site.id):
            raise serializers.ValidationError("Both devices must belong to the link site.")
        if source and target and TopologyLink.objects.filter(source_device=target, target_device=source).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("The equivalent reverse link already exists.")
        return attrs
