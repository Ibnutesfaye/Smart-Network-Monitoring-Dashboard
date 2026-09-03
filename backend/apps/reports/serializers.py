from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    generated_by_username = serializers.CharField(source="generated_by.username", read_only=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "report_type",
            "export_format",
            "generated_by",
            "generated_by_username",
            "file_path",
            "period_start",
            "period_end",
            "created_at",
        )
        read_only_fields = ("id", "file_path", "generated_by", "created_at")


class ReportGenerateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=Report.ReportType.choices)
    export_format = serializers.ChoiceField(choices=Report.ExportFormat.choices, default="pdf")
