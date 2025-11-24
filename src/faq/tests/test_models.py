from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from accounts.constants import UserCategoryChoice

from ..factories import (
    AssistancePageFactory,
    ContentBlockFactory,
    FaqPageFactory,
    MessageFactory,
    SuggestedPageFactory,
    WebinarFactory,
)
from ..models import AssistancePage, Webinar

pytestmark = pytest.mark.django_db


def test_faq_page_creation():
    faq = FaqPageFactory()

    assert faq.id is not None
    assert faq.title is not None
    assert faq.slug is not None
    assert faq.created_at is not None
    assert faq.updated_at is not None

    assert faq.user_categories == []


def test_faq_page_user_categories_with_values():
    categories = [choice[0] for choice in UserCategoryChoice.choices][:3]
    faq = FaqPageFactory(user_categories=categories)

    assert len(faq.user_categories) == 3
    for cat in faq.user_categories:
        valid_choices = [c[0] for c in UserCategoryChoice.choices]
        assert cat in valid_choices


def test_faq_page_parent_child_relationship():
    root = FaqPageFactory(title="Root")
    child1 = FaqPageFactory(parent=root, title="Child 1")
    child2 = FaqPageFactory(parent=root, title="Child 2")
    grandchild = FaqPageFactory(parent=child1, title="Grandchild")

    assert root.parent is None
    assert child1.parent == root
    assert child2.parent == root
    assert grandchild.parent == child1


def test_content_block_creation():
    block = ContentBlockFactory()

    assert block.id
    assert block.page
    assert block.content
    assert isinstance(block.order, int)


def test_content_block_str_representation():
    page = FaqPageFactory(title="Test Page")
    block = ContentBlockFactory(page=page)
    assert str(block) == "ContentBlock for Test Page"


def test_content_block_with_media():
    """Test ContentBlock with image and video"""
    block = ContentBlockFactory()

    assert block.image
    assert block.video_source is not None
    assert block.video_source.startswith("http")


def test_content_block_image_is_deleted_from_storage():
    """Test ContentBlock image is deleted from storage when block is deleted"""
    block = ContentBlockFactory()

    assert block.image
    image_name = block.image.name

    # Verify file exists in storage
    assert block.image.storage.exists(image_name)

    # Delete the block
    block.delete()

    # Verify file is removed from storage
    assert not block.image.storage.exists(image_name)


def test_content_block_old_image_is_deleted_from_storage_on_update():
    """Test old image is deleted from storage when ContentBlock image is updated"""
    block = ContentBlockFactory()

    assert block.image
    old_image_name = block.image.name

    # Verify old file exists in storage
    assert block.image.storage.exists(old_image_name)

    # Update with a new image
    new_image = SimpleUploadedFile(
        name="new_image.jpg",
        content=b"fake image content",
        content_type="image/jpeg",
    )
    block.image = new_image
    block.save()

    # Verify old file is removed from storage
    assert not block.image.storage.exists(old_image_name)

    # Verify new file exists
    assert block.image.storage.exists(block.image.name)


def test_content_block_without_media():
    """Test ContentBlock without media using trait"""
    block = ContentBlockFactory(no_media=True)

    assert block.image is None or not block.image
    assert block.video_source == ""


def test_content_block_with_video_only():
    """Test ContentBlock with video only"""
    block = ContentBlockFactory(with_video_only=True)

    assert block.image is None or not block.image
    assert block.video_source is not None
    assert block.video_source != ""


def test_content_block_with_image_only():
    """Test ContentBlock with image only"""
    block = ContentBlockFactory(with_image_only=True)

    assert block.image is not None
    assert block.video_source == ""


def test_content_block_ordering():
    """Test ContentBlock ordering by order field"""
    page = FaqPageFactory()
    ContentBlockFactory(page=page, order=10)
    ContentBlockFactory(page=page, order=5)
    ContentBlockFactory(page=page, order=15)

    blocks = page.blocks.all()
    orders = [b.order for b in blocks]
    assert orders == sorted(orders)


def test_content_block_enriched_content():
    """Test enriched_content method replaces #ASSISTANCE tag"""
    block = ContentBlockFactory(content="Click #ASSISTANCE for help")

    enriched = block.enriched_content()

    assistance_link = reverse("assistance_wrapper_home")
    assert f"<a href='{assistance_link}'>FAQ</a>" in enriched


def test_content_block_delete_signal():
    """Test that image is deleted when ContentBlock is deleted"""
    block = ContentBlockFactory()
    image_name = block.image.name if block.image else None

    # Mock the delete method to verify it's called
    with patch.object(block.image, "delete") as mock_delete:
        block.delete()
        if image_name:
            mock_delete.assert_called_once()


def test_content_block_relationship_with_page():
    """Test relationship between ContentBlock and FaqPage"""
    page = FaqPageFactory()
    blocks = ContentBlockFactory.create_batch(3, page=page)

    assert page.blocks.count() == 3
    for block in blocks:
        assert block.page == page


def test_suggested_page_creation():
    """Test basic SuggestedPage creation"""
    suggestion = SuggestedPageFactory()

    assert suggestion.id is not None
    assert suggestion.parent_page is not None
    assert suggestion.linked_page is not None
    assert isinstance(suggestion.order, int)


def test_suggested_page_ordering():
    """Test SuggestedPage ordering by order field"""
    parent = FaqPageFactory()
    SuggestedPageFactory(parent_page=parent, order=10)
    SuggestedPageFactory(parent_page=parent, order=5)
    SuggestedPageFactory(parent_page=parent, order=15)

    suggestions = parent.suggestions.all()
    orders = [s.order for s in suggestions]
    assert orders == sorted(orders)


def test_assistance_page_creation():
    """Test basic AssistancePage creation"""
    page = AssistancePageFactory()

    assert page.id is not None
    assert page.title is not None
    assert page.content is not None
    assert page.display_contact_form in [c[0] for c in AssistancePage.ContactFormOptions.choices]


def test_assistance_page_contact_form_options():
    """Test different contact form options"""
    no_form = AssistancePageFactory()
    open_form = AssistancePageFactory(with_open_form=True)
    closed_form = AssistancePageFactory(with_closed_form=True)

    assert no_form.display_contact_form == AssistancePage.ContactFormOptions.NO
    assert open_form.display_contact_form == AssistancePage.ContactFormOptions.OPEN
    assert closed_form.display_contact_form == AssistancePage.ContactFormOptions.CLOSED


def test_assistance_page_anchor_property():
    # With custom anchor
    with_anchor = AssistancePageFactory(title="Very Long Title Here", link_anchor="Short")
    assert with_anchor.anchor == "Short"

    # Without custom anchor (uses title)
    without_anchor = AssistancePageFactory(title="Page Title", link_anchor="")
    assert without_anchor.anchor == "Page Title"


# ============================================================================
# Message Model Tests
# ============================================================================


def test_message_creation():
    """Test basic Message creation"""
    message = MessageFactory()

    assert message.id
    assert message.user
    assert message.subject
    assert message.message
    assert message.created
    assert message.ip


def test_webinar_creation():
    """Test basic Webinar creation"""
    webinar = WebinarFactory()

    assert webinar.id

    assert webinar.title
    assert webinar.scheduled_at
    assert isinstance(webinar.duration, int)
    assert webinar.duration > 0


def test_webinar_future():
    """Test future webinar creation and is_future method"""
    webinar = WebinarFactory(future=True)

    assert webinar.scheduled_at.date() > timezone.now().date()
    assert webinar.is_future()


def test_webinar_past():
    """Test past webinar creation and is_future method"""
    webinar = WebinarFactory(past=True)

    assert webinar.scheduled_at.date() < timezone.now().date()
    assert not webinar.is_future()


def test_webinar_today():
    """Test webinar scheduled for today"""
    webinar = WebinarFactory(today=True)

    assert webinar.scheduled_at.date() == timezone.now().date()
    assert webinar.is_future()


def test_webinar_ends_at_property():
    """Test ends_at property calculation"""
    webinar = WebinarFactory(duration=90)

    expected_end = webinar.scheduled_at + timedelta(minutes=90)
    assert webinar.ends_at == expected_end


def test_webinar_display_after_property():
    """Test display_after property calculation"""
    webinar = WebinarFactory(display_days_before=14)

    expected_display = webinar.scheduled_at.date() - timedelta(days=14)
    assert webinar.display_after == expected_display


def test_webinar_uid_property():
    """Test UID property generation"""
    webinar = WebinarFactory()

    uid = webinar.uid
    assert str(webinar.id) in uid
    assert ".event.events." in uid


def test_webinar_as_ics():
    """Test ICS calendar generation"""
    webinar = WebinarFactory(title="Test Event", duration=60)

    ics_content = webinar.as_ics()

    assert ics_content is not None
    assert b"BEGIN:VCALENDAR" in ics_content
    assert b"END:VCALENDAR" in ics_content
    assert b"Test Event" in ics_content
    assert b"BEGIN:VEVENT" in ics_content
    assert b"END:VEVENT" in ics_content


def test_webinar_queryset_visible():
    """Test visible() queryset method"""
    # Create webinars with different display settings
    future_visible = WebinarFactory(
        scheduled_at=timezone.now() + timedelta(days=35),
        display_days_before=40,  # Should be visible
    )

    visible = Webinar.objects.visible()

    assert visible.filter(id=future_visible.id).exists()


def test_webinar_queryset_future():
    """Test future() queryset method"""
    past = WebinarFactory(past=True)
    today = WebinarFactory(today=True)
    future = WebinarFactory(future=True)

    future_webinars = Webinar.objects.future()

    assert not future_webinars.filter(id=past.id).exists()
    assert future_webinars.filter(id=today.id).exists()
    assert future_webinars.filter(id=future.id).exists()


def test_webinar_queryset_past():
    """Test past() queryset method"""
    past = WebinarFactory(past=True)
    today = WebinarFactory(today=True)
    future = WebinarFactory(future=True)

    past_webinars = Webinar.objects.past()

    assert past_webinars.filter(id=past.id).exists()
    assert not past_webinars.filter(id=today.id).exists()
    assert not past_webinars.filter(id=future.id).exists()
