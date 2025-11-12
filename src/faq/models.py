import uuid
from pathlib import Path

from django.contrib.postgres.indexes import GinIndex
from django.core.files.storage import storages
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prose_editor.fields import ProseEditorField
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django_jsonform.models.fields import ArrayField

from accounts.constants import UserCategoryChoice

from .managers import FaqPageManager


class FaqPage(MPTTModel):
    ITEMS_SCHEMA = {
        "type": "array",
        "items": {
            "type": "string",
            'choices': [{"value": k, "title": v} for k, v in UserCategoryChoice.choices],

            "maxLength": 50
        },
        "maxItems": 10
    }
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    position = models.PositiveIntegerField(default=0)

    user_categories = ArrayField(models.CharField(
        max_length=32,
        blank=True,
        choices=UserCategoryChoice.choices),
        default=list,
        blank=True,
        schema=ITEMS_SCHEMA
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


config = {
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


class ContentBlock(models.Model):
    page = models.ForeignKey(FaqPage, on_delete=models.CASCADE, related_name="blocks")
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content = ProseEditorField(
        _("Content"),
        extensions=config,
        sanitize=True,  # Enable sanitization based on extension configuration
        blank=True,
    )
    image = models.ImageField(
        _("Image"), upload_to=image_path, max_length=512, storage=storages["private_s3"], blank=True
    )

    video_source = models.URLField(_("Video url"), max_length=512, blank=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Content block")

    def __str__(self):
        return f"{self.__class__.__name__} for {self.page.title}"


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


@receiver(pre_delete, sender=ContentBlock)
def delete_has_folder(sender, instance, *args, **kwargs):
    """Delete S3 files on model deletion"""
    instance.image.delete()
