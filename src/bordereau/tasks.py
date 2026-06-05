import io
import logging
import zipfile

import httpx
from celery import current_task
from django.core.files.base import ContentFile

from config.celery_app import app
from roadcontrol.exceptions import FormDownloadException

from bordereau.models import BsdPdf, PdfBundle
from roadcontrol.td_requests import query_td_pdf
from .rendering_helpers import render_pdf_bordereau_fn

logger = logging.getLogger(__name__)


@app.task()
def prepare_bordereau_bundle(bundle_pk):
    """
    Pollable task to prepare html view.

    :param bundle_pk: PdfBundle pk
    """
    process = Process(bundle_pk)
    return process.process()


class Process:
    def __init__(self, bundle_pk):
        self.bundle_pk = bundle_pk

    def get_pdf_download_link(self, bsd_type, bsd_id):
        link = query_td_pdf(bsd_type=bsd_type, bsd_id=bsd_id)

        return link

    def get_pdf_download_content(self, link):
        try:
            r = self.client.get(link)
        except httpx.RequestError:
            raise FormDownloadException()
        return r.content

    def do_process(self):
        bundle = PdfBundle.objects.get(pk=self.bundle_pk)
        PdfBundle.objects.mark_as_processing(self.bundle_pk)
        self.client = httpx.Client(timeout=60)  # 1 minute
        bsds_total_count = len(bundle.params)
        bsds_count = 0
        for row in bundle.params:
            bsd_type = row["bsd_type"]
            bsd_id = row["bsd_id"]
            readable_id = row["readable_id"]
            waste_code = row["waste_code"]
            waste_code = row["waste_code"]
            weight = row["weight"]
            adr_code = row["adr_code"]
            packagings = row["packagings"]
            download_link = self.get_pdf_download_link(bsd_type=bsd_type, bsd_id=bsd_id)
            pdfdata = self.get_pdf_download_content(download_link)
            file = ContentFile(pdfdata, name="bsd.pdf")
            BsdPdf.objects.create(
                bsd_id=readable_id,
                waste_code=waste_code,
                weight=weight,
                adr_code=adr_code,
                packagings=packagings,
                pdf_file=file,
                created_by=bundle.created_by,
                bundle=bundle,
            )
            bsds_count += 1
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "progress": round(100 * (bsds_count / bsds_total_count)),
                    "bsds_count": bsds_count,
                    "bsds_total_count": bsds_total_count,
                },
            )

            # build zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            bytes_pdf = render_pdf_bordereau_fn(bundle)

            zip_file.writestr("Sommaire.pdf", bytes_pdf)

            for pdf in bundle.pdfs.all():
                with pdf.pdf_file.open() as f:
                    zip_file.writestr(pdf.bsd_file_name, f.read())

        bundle.zip_file.save(f"{bundle.id}.zip", ContentFile(zip_buffer.getvalue()))
        zip_buffer.close()
        PdfBundle.objects.mark_as_ready(self.bundle_pk)

    def process(self):
        errors = []
        try:
            self.do_process()
        except Exception as e:  # noqa
            current_task.update_state(state="ERROR", meta={"progress": 100})
            PdfBundle.objects.mark_as_failed(self.bundle_pk)
            logger.error(e)
            return {"errors": "Error"}
        current_task.update_state(state="DONE", meta={"progress": 100})

        return {"errors": errors}
