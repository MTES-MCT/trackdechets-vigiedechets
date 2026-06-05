from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from roadcontrol.models import PdfBundle


def render_pdf(content):
    html = HTML(string=content, base_url=settings.BASE_URL)

    font_config = FontConfiguration()
    with open(settings.STATICFILES_DIR / "css" / "pdf.css") as f:
        css_content = f.read()

    css = CSS(
        string=css_content,
        font_config=font_config,
        base_url=f"{settings.BASE_URL}/static/css/",
    )

    bytes_pdf = html.write_pdf(stylesheets=[css], font_config=font_config)
    return bytes_pdf


def render_pdf_bordereau_fn(bundle: PdfBundle):
    ctx = {"bundle": bundle}
    content = render_to_string("bordereau/pdf/bordereau_bundle_digest.html", ctx)

    return render_pdf(content)
