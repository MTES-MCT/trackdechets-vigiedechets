from django import template

register = template.Library()

@register.filter
def to_range(value):
    """Convertit un entier en range(1, n+1) pour les boucles de pagination."""
    return range(1, int(value) + 1)

@register.filter
def to_int(value):
    """Convertit une valeur en entier (pour comparer page_size avec les boutons)."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def split(value, arg):
    return value.split(arg)