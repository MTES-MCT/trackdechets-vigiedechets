from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from mptt.admin import DraggableMPTTAdmin

from accounts.constants import UserCategoryChoice

from .models import AssistancePage, ContentBlock, FaqPage, Message, SuggestedPage, Webinar


class ContentBlockInline(admin.StackedInline):
    model = ContentBlock
    inline_classes = ("grp-collapse grp-open",)
    sortable_field_name = "order"
    extra = 0

    class Media:
        css = {"all": ("admin/css/custom_prose_editor.css",)}


class SuggestedPageInline(admin.StackedInline):
    model = SuggestedPage
    inline_classes = ("grp-collapse grp-open",)
    sortable_field_name = "order"
    extra = 0
    fk_name = "parent_page"
    autocomplete_fields = ("linked_page",)


@admin.register(FaqPage)
class FaqPageAdmin(DraggableMPTTAdmin):
    list_display = [
        "tree_actions",
        "indented_title",
        "get_user_categories",
    ]
    position_field = "position"

    search_fields = [
        "title",
    ]

    inlines = [ContentBlockInline, SuggestedPageInline]

    @admin.display(
        description=_("User Categories"),
    )
    def get_user_categories(self, obj):
        if not obj.user_categories:
            return "Tous"
        # prevent empty strings in array breaking the page
        user_categories = ",".join(
            [str(getattr(UserCategoryChoice, el).label) for el in obj.user_categories if el in UserCategoryChoice]
        )
        if not user_categories:
            return "Tous"
        return user_categories


@admin.register(AssistancePage)
class AssistancePageAdmin(DraggableMPTTAdmin):
    list_display = ["tree_actions", "indented_title", "display_contact_form", "display_contact_form"]

    list_display_links = ("indented_title",)

    class Media:
        css = {"all": ("admin/css/custom_prose_editor.css",)}


@admin.register(Message)
class AssistanceMessageAdmin(admin.ModelAdmin):
    list_display = ["pk", "subject", "created", "user", "origin_page_title"]
    list_select_related = ["user"]


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = ["title", "scheduled_at", "get_display_after", "visio_link"]

    @admin.display(description="Afficher après le")
    def get_display_after(self, obj):
        return obj.display_after
