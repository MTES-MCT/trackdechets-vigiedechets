import uuid

from braces.views import LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView as BaseLoginView
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import resolve_url
from django.urls import reverse_lazy
from django.views.generic import FormView
from django_otp import login as otp_login
from django_otp.plugins.otp_email.models import EmailDevice

from accounts.forms import ResendTokenEmailForm, SecondFactorTokenForm
from common.redis import gen_otp_email_key, redis_client


def create_email_device(user):
    device = EmailDevice.objects.create(email=user.email, user=user, name="email_device")
    return device


def fancy_print(message):
    width = len(message) + 4
    print("╔" + "═" * (width - 2) + "╗")
    print(f"║\033[41m {message} \033[0m║")
    print("╚" + "═" * (width - 2) + "╝")


class SendSecondFactorMailMixin:
    def process(self):
        user = self.request.user
        devices = EmailDevice.objects.devices_for_user(user)

        if not devices:
            device = create_email_device(user)
        else:
            device = devices[0]
        device.generate_challenge()

        if settings.DEBUG:
            # Print security code to console for quick reference, eliminating need to search through email output
            fancy_print(f"SECURITY CODE : {device.token}")


class LoginView(SendSecondFactorMailMixin, BaseLoginView):
    def get_default_redirect_url(self):
        try:
            if self.request.user.is_authenticated_from_oidc():
                return resolve_url("private_home")
        except AttributeError:
            pass
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def form_valid(self, form):
        res = super().form_valid(form)

        self.process()
        return res


class VerifyView(LoginRequiredMixin, FormView):
    form_class = SecondFactorTokenForm
    template_name = "accounts/second_factor.html"
    success_url = reverse_lazy("private_home")

    def get(self, request, *args, **kwargs):
        if request.user.is_verified() or request.user.is_authenticated_from_oidc():
            return HttpResponseRedirect(self.success_url)

        res = super().get(request, *args, **kwargs)
        return res

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw.update({"user": self.request.user})

        return kw

    def form_valid(self, form):
        otp_login(self.request, self.request.user.otp_device)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, token_validity=int(settings.OTP_EMAIL_TOKEN_VALIDITY / 60))


class ResendTokenEmail(SendSecondFactorMailMixin, LoginRequiredMixin, FormView):
    """
    Request a new email contianing token.
    Throttled every OTP_EMAIL_THROTTLE_DELAY seconds.
    """

    form_class = ResendTokenEmailForm
    template_name = "accounts/second_factor.html"  # not used but required
    success_url = reverse_lazy("second_factor")

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, form.errors.get("__all__"))
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        self.process()
        redis_key = gen_otp_email_key(self.request.user)
        redis_client.set(redis_key, "_", ex=settings.OTP_EMAIL_THROTTLE_DELAY)
        return super().form_valid(form)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw.update({"user": self.request.user})
        return kw


def proconnect_logout(request):
    q = QueryDict(mutable=True)

    id_token = request.session.get("oidc_id_token")

    q["id_token_hint"] = id_token
    q["state"] = str(uuid.uuid4())
    q["post_logout_redirect_uri"] = "https://dev.inspection.trackdechets.beta.gouv.fr/oidc/logout/"
    query_string = q.urlencode()
    return f"{settings.OIDC_RP_LOGOUT_ENDPOINT}?{query_string}"
