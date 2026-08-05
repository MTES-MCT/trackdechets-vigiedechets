import pytest

from ..factories import BsdPdfFactory, PdfBundleFactory

pytestmark = pytest.mark.django_db


def test_bsd_pdf_factory():
    bsd = BsdPdfFactory()
    assert bsd.pk
    assert bsd.created_at


def test_pdf_bundle_factory():
    bundle = PdfBundleFactory()
    assert bundle.pk
    assert bundle.created_at
