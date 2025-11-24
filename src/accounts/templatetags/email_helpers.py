from django import template
from django.templatetags.static import static
from django.urls import reverse_lazy

from common.domain import get_domain

register = template.Library()


@register.simple_tag(takes_context=True)
def second_factor_url(context):
    domain = get_domain()
    return f"https://{domain}{reverse_lazy('second_factor')}"


@register.simple_tag(takes_context=True)
def logo_url(context):
    domain = get_domain()
    return f"https://{domain}{static('img/trackdechets.png')}"
