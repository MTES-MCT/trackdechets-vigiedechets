from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from mptt.admin import DraggableMPTTAdmin

from .models import ContentBlock, FaqPage, SuggestedPage
from accounts.constants import UserCategoryChoice


class ContentBlockInline(admin.StackedInline):
    model = ContentBlock
    inline_classes = ("grp-collapse grp-open",)
    sortable_field_name = "order"
    extra = 0


class SuggestedPageInline(admin.StackedInline):
    model = SuggestedPage
    inline_classes = ("grp-collapse grp-open",)
    sortable_field_name = "order"
    extra = 0
    fk_name = "parent_page"
    autocomplete_fields = ("linked_page",)


@admin.register(FaqPage)
class PageAdmin(DraggableMPTTAdmin):
    list_display = [
        "tree_actions",
        "indented_title",
        "get_user_categories",
    ]
    position_field = "position"

    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ContentBlockInline, SuggestedPageInline]

    @admin.display(
        description=_("User Categories"),
    )
    def get_user_categories(self, obj):

        if not obj.user_categories:
            return "Tous"
        return ",".join([str(getattr(UserCategoryChoice, el).label) for el in obj.user_categories])
