from django.db import models

from mptt.managers import TreeManager, TreeQuerySet
from django.db.models import Q

from accounts.models import User


class FaqPageQuerySet(TreeQuerySet):
    """Custom QuerySet for FaqPage with user_categories filtering methods."""

    def for_user(self, user: User):
        """
        Filter pages that are available for a specific user type.
        Returns pages that either have no user_categories (available to all)
        or contain the specified user_type.
        """


        if user.is_staff:
            return self.all()
        user_category = user.user_category
        return self.filter(
            Q(user_categories__contains=[user_category]) | Q(user_categories=[])
        )


class FaqPageManager(TreeManager):
    """Custom manager for FaqPage combining MPTT TreeManager with custom QuerySet."""

    def get_queryset(self):
        """Return custom QuerySet instance."""
        return FaqPageQuerySet(self.model, using=self._db)    .order_by(self.tree_id_attr, self.left_attr)


    def for_user(self, user: User):
        """
          Filter pages that are available for a specific user category.
          Returns pages that either have no user_categories (available to all)
          or contain the specified user_type.
          """
        return   self.get_queryset().for_user(user)

        if user.is_staff:
            return self.all()
        user_category = user.user_category
        return self.filter(
            Q(user_categories__contains=[user_category]) | Q(user_categories=[])
        )

    # def get_tree_for_user(self, user, parent=None):
    #     """
    #     Get the FAQ tree structure filtered by user permissions.
    #
    #     Args:
    #         user: The user to filter pages for
    #         parent: Optional parent node to start from
    #     """
    #     queryset = self.visible_to_user(user)
    #     if parent:
    #         queryset = queryset.filter(parent=parent)
    #     else:
    #         queryset = queryset.filter(parent__isnull=True)
    #
    #     return queryset.order_by('tree_id', 'lft')
