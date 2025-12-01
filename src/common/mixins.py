from braces.views._access import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.urls import reverse_lazy


class FullyLoggedMixin(AccessMixin):
    """
    This mixin extends AccessMixin to handle multi-factor authentication (MFA) and OIDC plus
    user category-based permissions or user email permissions. It ensures users are fully authenticated
    (two-factor verification or coming from OIDC) and belong to allowed user categories.

    Forbid access to :
     - non verified users (users logged with second factor)
     - users not coming from MonAIOT
     - user not having the relevant category

    User are redirected :
        - to verifiy page if they're logged in without second factor and not coming from MonAIOT
        - to login page if they're not logged.
    When fully logged, they're denied access if they do not have the right categories

    Attributes:
    allowed_user_categories (list): Categories of users allowed to access views
        using this mixin. Must be explicitly set in subclasses. Use ["*"]
        for unlimited access.
    allowed_user_emails (list): List of user email to be allowed

    Example:
    class SecureView(FullyLoggedMixin, View):
        allowed_user_categories = ['admin', 'manager']

        def get(self, request):
            return HttpResponse('Secure content')

    Note:
    - Place this mixin before other view classes in inheritance
    - Staff users automatically bypass category and email restrictions
    - Setting allowed_user_categories = ["*"] allows access to all authenticated users

    """

    allowed_user_categories = []
    allowed_user_emails = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_user_categories = self.get_allowed_user_categories()
        allowed_user_emails = self.get_allowed_user_emails()

        if allowed_user_categories and allowed_user_emails:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} do not allow `allowed_user_categories` and `allowed_user_emails` attribute to be set"
            )
        if not allowed_user_categories and not allowed_user_emails:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires the `allowed_user_categories` or `allowed_user_emails` attribute to be set"
            )

    def get_allowed_user_categories(self):
        """Allow overriding in child classes"""
        return self.allowed_user_categories

    def get_allowed_user_emails(self):
        """Allow overriding in child classes"""
        return self.allowed_user_emails

    def no_permissions_fail(self, request=None):
        """Handle failed permission checks by redirecting users appropriately."""
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy("second_factor"))
        return redirect_to_login(
            request.get_full_path(),
            self.get_login_url(),
            self.get_redirect_field_name(),
        )

    def test_is_fully_logged(self, user):
        """Verify if a user has completed all required authentication steps."""
        if not user.is_authenticated:
            return False
        is_verified_with_otp = user.is_verified()
        is_authenticated_from_oidc = user.is_authenticated_from_oidc()
        return is_verified_with_otp or is_authenticated_from_oidc

    def check_has_right_categories(self):
        """Verify if the user belongs to allowed categories."""

        if self.request.user.is_staff:
            return True
        allowed_user_categories = self.get_allowed_user_categories()
        if self.allowed_user_categories == ["*"]:
            return True

        user_category = self.request.user.user_category

        return user_category in allowed_user_categories

    def check_email_is_allowed(self):
        """Verify if the user belongs to allowed categories."""
        if self.request.user.is_staff:
            return True
        allowed_user_emails = self.get_allowed_user_emails()
        return self.request.user.email.lower() in allowed_user_emails

    def dispatch(self, request, *args, **kwargs):
        """Check if user is fully logged, then if has appropriate categories"""
        user_test_result = self.test_is_fully_logged(request.user)
        allowed_user_categories = self.get_allowed_user_categories()
        allowed_user_emails = self.get_allowed_user_emails()
        if not user_test_result:
            return self.handle_no_permission(request)

        if allowed_user_categories:
            in_category = self.check_has_right_categories()
            if not in_category:
                raise PermissionDenied()

        if allowed_user_emails:
            email_is_allowed = self.check_email_is_allowed()
            if not email_is_allowed:
                raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)


class HtmxOnlyMixin:
    """Restrict views responses to htmx requests"""

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)
