from collections import defaultdict

import boto3
from django import forms
from django.conf import settings
from django.http import Http404
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from accounts.constants import PERMS_DATA_EXPORT
from common.mixins import FullyLoggedMixin

from .constants import PARQUET_BUCKET_NAME, PRESIGNED_URL_EXPIRATION
from .models import BsdTypeChoice, DataExport, DataExportDownload


class DummyForm(forms.Form):
    pass


class ExportList(FullyLoggedMixin, TemplateView):
    template_name = "data_exports/data_exports.html"
    allowed_user_categories = PERMS_DATA_EXPORT

    def get_exports(self):
        oldest_year = 2022
        today = timezone.now().date()
        current_year = today.year
        years = list(range(current_year, oldest_year - 1, -1)) + [None]
        exports = defaultdict(list)
        for year in years:
            for bsd_type in BsdTypeChoice:
                exp = DataExport.objects.filter(year=year, bsd_type=bsd_type).first()
                if exp:
                    exports[year].append(exp)

        return dict(exports)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, exports=self.get_exports())


class ExportDownload(FullyLoggedMixin, FormView):
    template_name = "dummy.html"
    form_class = DummyForm
    success_url = ""
    allowed_user_categories = PERMS_DATA_EXPORT

    def get(self, request, *args, **kwargs):
        raise Http404()

    def form_valid(self, form):
        self.success_url = self.generate_presigned_url()
        return super().form_valid(form)

    def generate_presigned_url(self):
        """Generate a presigned S3 url"""
        pk = self.kwargs.get("pk")
        session = boto3.Session(region_name="fr-par")
        export = DataExport.objects.get(pk=pk)

        client = session.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        response = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": PARQUET_BUCKET_NAME, "Key": export.s3_path},
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
        )
        DataExportDownload.objects.create(user=str(self.request.user), year=export.year, bsd_type=export.bsd_type)
        return response
