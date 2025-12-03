import datetime as dt
import logging
import re
import uuid
from pathlib import Path

from django.core.files.storage import storages
from django.db import models
from django.db.models import ExpressionWrapper, F
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.urls.base import reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_jsonform.models.fields import ArrayField
from django_prose_editor.fields import ProseEditorField
from icalendar import Calendar, Event
from mptt.models import MPTTModel, TreeForeignKey

from accounts.constants import UserCategoryChoice
from common.domain import get_domain

from .managers import FaqPageManager

logger = logging.getLogger(__name__)


class FaqPage(MPTTModel):
    ITEMS_SCHEMA = {
        "type": "array",
        "items": {
            "type": "string",
            "choices": [{"value": k, "title": v} for k, v in UserCategoryChoice.choices],
            "maxLength": 50,
        },
        "maxItems": 10,
    }
    title = models.CharField(max_length=200)

    position = models.PositiveIntegerField(default=0)

    user_categories = ArrayField(
        models.CharField(max_length=32, choices=UserCategoryChoice.choices),
        default=list,
        blank=True,
        schema=ITEMS_SCHEMA,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    objects = FaqPageManager()

    class Meta:
        ordering = ["position"]
        verbose_name = _("Page de faq")
        verbose_name_plural = _("Pages de faq")

    def __str__(self):
        return self.title


prose_config = {
    # Core text formatting
    "Bold": True,
    "Italic": True,
    "Strike": True,
    "Underline": True,
    "HardBreak": True,
    # Structure
    "Heading": {
        "levels": [1, 2, 3]  # Only allow h1, h2, h3
    },
    "BulletList": True,
    "OrderedList": True,
    "ListItem": True,  # Used by BulletList and OrderedList
    "Blockquote": True,
    # Advanced extensions
    "Link": {
        "enableTarget": True,  # Enable "open in new window"
        "protocols": ["http", "https", "mailto"],  # Limit protocols
    },
    # Editor capabilities
    "History": True,  # Enables undo/redo
    "HTML": True,  # Allows HTML view
    "Typographic": True,  # Enables typographic chars
}


def image_path(instance, filename):
    ext = Path(filename).suffix.lower()
    unique_id = uuid.uuid4()
    return f"faq/images/{unique_id}{ext}"


def clean_list_items(html):
    # Remove <p> tags from inside <li> tags that prose mirror adds
    html = re.sub(r"<li>\s*<p>(.*?)</p>\s*</li>", r"<li>\1</li>", html, flags=re.DOTALL)
    return html


class ContentBlock(models.Model):
    page = models.ForeignKey(FaqPage, on_delete=models.CASCADE, related_name="blocks")
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content = ProseEditorField(
        _("Content"),
        extensions=prose_config,
        sanitize=True,  # Enable sanitization
        blank=True,
        help_text=_("Le tag #ASSISTANCE sera remplacé par un lien vers l'assistance"),
    )
    # Django does not delete file when models are deleted or updated
    # See relevant signals receiver below
    image = models.ImageField(
        _("Image"), upload_to=image_path, max_length=512, storage=storages["private_s3"], blank=True
    )

    video_source = models.URLField(_("Video url"), max_length=512, blank=True)

    class Meta:
        verbose_name = _("Bloc de faq")
        verbose_name_plural = _("Blocs de faq")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.__class__.__name__} for {self.page.title}"

    def enriched_content(self):
        assistance_link = reverse_lazy("assistance_wrapper_home")
        content = clean_list_items(self.content)
        content = content.replace("#ASSISTANCE", f"<a href='{assistance_link}'>FAQ</a>")
        return content


class SuggestedPage(models.Model):
    parent_page = models.ForeignKey(FaqPage, on_delete=models.CASCADE, related_name="suggestions")
    linked_page = models.ForeignKey(FaqPage, on_delete=models.CASCADE, related_name="suggested")

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "order",
        ]
        verbose_name = _("Suggested Page")

    def __str__(self):
        return f"{self.__class__.__name__} {self.linked_page.title}"


def delete_file_if_exists(file_field):
    """
    Delete a file from storage (works for both local and S3)
    """
    if file_field:
        try:
            if file_field.storage.exists(file_field.name):
                file_field.storage.delete(file_field.name)

        except Exception as e:
            logger.error(f"Error deleting file {file_field.name}: {e}")


@receiver(pre_delete, sender=ContentBlock)
def delete_content_block_media_on_delete(sender, instance, *args, **kwargs):
    """Delete S3 files on model deletion"""
    instance.image.delete()


@receiver(pre_save, sender=ContentBlock)
def delete_content_block_media_on_update(sender, instance, *args, **kwargs):
    """Delete S3 files on model instance"""

    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_file = getattr(old_instance, "image")
    new_file = getattr(instance, "image")
    if old_file and old_file != new_file:
        delete_file_if_exists(old_file)


ASSISTANCE_PAGE_TITLE_LENGTH = 200


class AssistancePage(MPTTModel):
    class ContactFormOptions(models.TextChoices):
        NO = "NO", "Aucun"
        CLOSED = "CLOSED", "Fermé"
        OPEN = "OPEN", "Ouvert"

    title = models.CharField(max_length=ASSISTANCE_PAGE_TITLE_LENGTH)
    link_anchor = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Link Anchor",
        help_text="Override Title to display as link",
    )
    content = ProseEditorField(
        _("Content"),
        extensions=prose_config,
        sanitize=True,  # Enable sanitization based on extension configuration
        blank=True,
    )

    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    display_contact_form = models.CharField(
        "Affichage du formulaire de contact",
        max_length=6,
        default=ContactFormOptions.NO,
        choices=ContactFormOptions.choices,
    )

    class Meta:
        verbose_name = _("Page d'Assistance")
        verbose_name_plural = _("Pages d'Assistance")

    def __str__(self):
        return self.title

    @property
    def anchor(self):
        return self.link_anchor or self.title

    @property
    def open_form(self):
        return self.display_contact_form == self.ContactFormOptions.OPEN

    @property
    def closed_form(self):
        return self.display_contact_form == self.ContactFormOptions.CLOSED

    @property
    def has_form(self):
        return self.display_contact_form != self.ContactFormOptions.NO


class Message(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)

    subject = models.TextField("Objet du message", blank=True)
    message = models.TextField("Message", blank=True)
    origin_page_title = models.CharField("Page d'appel du formulaire", max_length=250, blank=True)

    ip = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

        verbose_name = _("Message")
        verbose_name_plural = _("Messages")


class WebinarQuerySet(models.QuerySet):
    def visible(self):
        now = timezone.now()

        return self.annotate(
            display_date=ExpressionWrapper(
                F("scheduled_at__date") - F("display_days_before"),
                output_field=models.DateTimeField(),
            ),
        ).filter(display_date__date__lte=now.date())

    def future(self):
        now = timezone.now()
        return self.visible().filter(scheduled_at__date__gte=now.date())

    def past(self):
        now = timezone.now()
        return self.filter(scheduled_at__date__lt=now.date())


class Webinar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("Titre du webinaire", max_length=120)

    scheduled_at = models.DateTimeField("Date et heure du webinaire")
    duration = models.PositiveSmallIntegerField("Durée prévue en mn", default=120)

    display_days_before = models.PositiveSmallIntegerField("Afficher X jours avant", default=28)

    visio_link = models.URLField("Lien visio", blank=True)

    objects = WebinarQuerySet.as_manager()

    class Meta:
        verbose_name = "Webinaire"
        verbose_name_plural = "Webinaires"
        ordering = ("-scheduled_at",)

    def __str__(self):
        return self.title

    @property
    def ends_at(self):
        return self.scheduled_at + dt.timedelta(minutes=self.duration)

    @property
    def display_after(self):
        return self.scheduled_at.date() - dt.timedelta(days=self.display_days_before)

    def is_future(self):
        return self.scheduled_at.date() >= timezone.now().date()

    @property
    def slug(self):
        return slugify(f"{self.title} {self.scheduled_at:%d %m %Y}")

    @cached_property
    def site_uid(self):
        domain = get_domain().split()
        domain.reverse()
        return ".".join(domain)

    @property
    def uid(self):
        return f"{self.id}.event.events.{self.site_uid}"

    def as_ics(self):
        domain = get_domain()
        cal = Calendar()
        ical_event = Event()

        ical_event.add("summary", self.title)
        ical_event.add("dtstart", self.scheduled_at)
        ical_event.add("dtend", self.ends_at)
        ical_event.add("uid", self.uid)
        ical_event.add("dtstamp", self.ends_at)

        ical_event.add("url", f"https://{domain}/")
        cal.add_component(ical_event)

        return cal.to_ical()
