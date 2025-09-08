from django import template

from sheets.utils import slugify_waste_code

register = template.Library()


@register.filter
def number(nb):
    """Format a given number with thousands separators (spaces)"""
    if (nb is None) or (nb == ""):
        return ""
    return str(nb).replace(" ", "&nbsp;")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(slugify_waste_code(key))
