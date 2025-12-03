import uuid

import factory
from django.utils import timezone
from factory import fuzzy
from factory.django import DjangoModelFactory

from accounts.factories import UserFactory

from .models import AssistancePage, ContentBlock, FaqPage, Message, SuggestedPage, Webinar


class FaqPageFactory(DjangoModelFactory):
    class Meta:
        model = FaqPage

    title = factory.Faker("sentence", nb_words=5)

    position = factory.Sequence(lambda n: n)

    parent = None  # Default to root level, can be overridden

    @factory.post_generation
    def children(obj, create, extracted, **kwargs):
        """Allow creation of child pages"""
        if not create:
            return

        if extracted:
            for child in extracted:
                child.parent = obj
                child.save()


class ContentBlockFactory(DjangoModelFactory):
    class Meta:
        model = ContentBlock

    page = factory.SubFactory(FaqPageFactory)
    order = factory.Sequence(lambda n: n)
    content = factory.Faker(
        "paragraph",
        nb_sentences=10,
        variable_nb_sentences=True,
        ext_word_list=["#ASSISTANCE", "FAQ", "help", "support"],
    )
    image = factory.django.ImageField(filename="test_image.jpg", width=800, height=600, color="blue", format="JPEG")
    video_source = factory.Faker("url", schemes=["https"])

    class Params:
        no_media = factory.Trait(image=None, video_source="")
        with_video_only = factory.Trait(image=None, video_source=factory.Faker("url", schemes=["https", "http"]))
        with_image_only = factory.Trait(video_source="")


class SuggestedPageFactory(DjangoModelFactory):
    class Meta:
        model = SuggestedPage

    parent_page = factory.SubFactory(FaqPageFactory)
    linked_page = factory.SubFactory(FaqPageFactory)
    order = factory.Sequence(lambda n: n)


class AssistancePageFactory(DjangoModelFactory):
    class Meta:
        model = AssistancePage

    title = factory.Faker("sentence", nb_words=6)
    link_anchor = factory.Faker("sentence", nb_words=3)
    content = factory.Faker("text", max_nb_chars=500, ext_word_list=["assistance", "help", "support", "contact"])
    parent = None  # Default to root level
    display_contact_form = AssistancePage.ContactFormOptions.NO

    class Params:
        with_open_form = factory.Trait(display_contact_form=AssistancePage.ContactFormOptions.OPEN)
        with_closed_form = factory.Trait(display_contact_form=AssistancePage.ContactFormOptions.CLOSED)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    user = factory.SubFactory(UserFactory)
    created = factory.LazyFunction(timezone.now)
    subject = factory.Faker("sentence", nb_words=8)
    message = factory.Faker("text", max_nb_chars=1000)
    origin_page_title = factory.Faker("sentence", nb_words=5)
    ip = factory.Faker("ipv4")


class WebinarFactory(DjangoModelFactory):
    class Meta:
        model = Webinar

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.Faker("sentence", nb_words=8)
    scheduled_at = factory.Faker(
        "date_time_between", start_date="+1d", end_date="+30d", tzinfo=timezone.get_current_timezone()
    )
    duration = fuzzy.FuzzyInteger(30, 180)  # 30 to 180 minutes
    display_days_before = 31  # 30d + 1
    visio_link = factory.Faker("url", schemes=["https"])

    class Params:
        future = factory.Trait(
            scheduled_at=factory.Faker(
                "date_time_between", start_date="+1d", end_date="+30d", tzinfo=timezone.get_current_timezone()
            )
        )
        past = factory.Trait(
            scheduled_at=factory.Faker(
                "date_time_between", start_date="-30d", end_date="-1d", tzinfo=timezone.get_current_timezone()
            )
        )
        today = factory.Trait(
            scheduled_at=factory.LazyFunction(
                lambda: timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
            )
        )


# Batch creation factories for testing
class FaqPageWithContentFactory(FaqPageFactory):
    """Factory that creates a FaqPage with associated content blocks"""

    @factory.post_generation
    def content_blocks(obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for block in extracted:
                block.page = obj
                block.save()
        else:
            # Create 3 content blocks by default
            ContentBlockFactory.create_batch(3, page=obj)


class FaqPageTreeFactory(FaqPageFactory):
    """Factory for creating a tree structure of FAQ pages"""

    @classmethod
    def create_tree(cls, depth=3, children_per_node=2):
        """
        Create a tree structure of FAQ pages.

        Args:
            depth: Maximum depth of the tree
            children_per_node: Number of children per node
        """

        def create_node(parent=None, current_depth=0):
            node = cls.create(parent=parent)

            if current_depth < depth - 1:
                for _ in range(children_per_node):
                    create_node(parent=node, current_depth=current_depth + 1)

            return node

        return create_node()


class AssistancePageTreeFactory(AssistancePageFactory):
    """Factory for creating a tree structure of Assistance pages"""

    @classmethod
    def create_tree(cls, depth=2, children_per_node=3):
        """
        Create a tree structure of Assistance pages.

        Args:
            depth: Maximum depth of the tree
            children_per_node: Number of children per node
        """

        def create_node(parent=None, current_depth=0):
            # Vary the contact form options
            form_options = [
                AssistancePage.ContactFormOptions.NO,
                AssistancePage.ContactFormOptions.OPEN,
                AssistancePage.ContactFormOptions.CLOSED,
            ]

            node = cls.create(parent=parent, display_contact_form=form_options[current_depth % 3])

            if current_depth < depth - 1:
                for _ in range(children_per_node):
                    create_node(parent=node, current_depth=current_depth + 1)

            return node

        return create_node()
