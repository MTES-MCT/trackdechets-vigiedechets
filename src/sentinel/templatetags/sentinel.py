from django import template

from sheets.utils import slugify_waste_code

register = template.Library()


def get_css_class(value):
    if value is None:
        return ""
    abs_value = abs(value)

    if abs_value > 75:
        return "td-text-alert"
    if abs_value > 40:
        return "td-text-warning"
    return "td-text-valid"


@register.inclusion_tag("sentinel/tags/sentinel_score.html")
def sentinel_score(row, key):
    if key != "score_percent":
        key = slugify_waste_code(key)
    score_percent = row.get(key)
    if not score_percent:
        return {}

    score_percent = round(score_percent, 1)
    return {"score_percent": score_percent, "css_class": get_css_class(score_percent)}
