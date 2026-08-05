import factory

from .models import BsdPdf, PdfBundle


class BsdPdfFactory(factory.django.DjangoModelFactory):
    bsd_id = factory.Sequence(lambda n: f"BSD-{n}")

    class Meta:
        model = BsdPdf


class PdfBundleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PdfBundle
