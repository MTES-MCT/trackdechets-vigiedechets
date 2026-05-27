from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    logout_then_login,
)
from django.urls import path

from .forms import EmailAuthenticationForm, RestrictedPasswordResetForm
from .views import LoginView, PasswordResetBruteForceProtectedView, ResendTokenEmail, VerifyView

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=EmailAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "second_factor/",
        VerifyView.as_view(),
        name="second_factor",
    ),
    path(
        "resend-token/",
        ResendTokenEmail.as_view(),
        name="resend_token",
    ),
    path("logout/", logout_then_login, name="logout"),
    path(
        "password-reset/",
        PasswordResetBruteForceProtectedView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="emails/password_reset/body.txt",
            html_email_template_name="emails/password_reset/body.html",
            form_class=RestrictedPasswordResetForm,
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
