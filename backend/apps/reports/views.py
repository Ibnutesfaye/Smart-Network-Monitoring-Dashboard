import os

from django.conf import settings
from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdministrator, IsAdministratorOrReadOnly

from .models import Report
from .serializers import ReportGenerateSerializer, ReportSerializer
from .tasks import generate_report_task


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related("generated_by").all()
    serializer_class = ReportSerializer
    permission_classes = [IsAdministratorOrReadOnly]
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["report_type", "export_format"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["post"], permission_classes=[IsAdministrator])
    def generate(self, request):
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = Report.objects.create(
            report_type=serializer.validated_data["report_type"],
            export_format=serializer.validated_data.get("export_format", "pdf"),
            generated_by=request.user,
        )
        generate_report_task.delay(report.id)
        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        report = self.get_object()
        if not report.file_path:
            return Response({"detail": "Report not ready."}, status=status.HTTP_404_NOT_FOUND)
        full_path = os.path.join(settings.MEDIA_ROOT, report.file_path)
        if not os.path.exists(full_path):
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        content_types = {"pdf": "application/pdf", "csv": "text/csv", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        ext = report.export_format
        ct = content_types.get(ext, "application/octet-stream")
        filename = os.path.basename(full_path)
        return FileResponse(open(full_path, "rb"), content_type=ct, as_attachment=True, filename=filename)
