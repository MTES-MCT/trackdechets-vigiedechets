from django import template
import math


register = template.Library()

# SI units in descending order
si_units = [
    {'value': 1e12, 'symbol': 'T'},
    {'value': 1e9, 'symbol': 'G'},
    {'value': 1e6, 'symbol': 'M'},
    {'value': 1e3, 'symbol': 'k'},
    {'value': 1, 'symbol': ''},
]
def add_thousands_separator(value_str):
    """Add thousands separators to a numeric string"""
    # Split on decimal point if present
    parts = value_str.split('.')
    # Add commas to integer part
    parts[0] = f"{int(parts[0]):,}" if parts[0] else "0"
    return '.'.join(parts)


def to_precision(x, precision):
    """Python equivalent of JavaScript's toPrecision()"""
    if x == 0:
        return 0
    return round(x, -int(math.floor(math.log10(abs(x)))) + (precision - 1))


@register.filter
def format_int(value):
    """
    Format an integer with SI units (T, G, M, k) and thousands separators.

    Usage in template: {{ number|formatint }}
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return str(value)

    abs_num = abs(num)
    sign = "-" if num < 0 else ""



    for unit in si_units:
        if abs_num >= unit['value']:
            scaled_value = abs_num / unit['value']
            rounded = to_precision(scaled_value, 2)

            # Convert to string and add thousands separators
            if rounded == int(rounded):
                formatted = add_thousands_separator(str(int(rounded)))
            else:
                formatted = add_thousands_separator(str(rounded))

            symbol_part = f" {unit['symbol']}" if unit['symbol'] else ""
            return f"{sign}{formatted}{symbol_part}"

    return f"{sign}0"


@register.filter
def format_float(value, decimal_places=2):
    """
    Format a float with SI units and specified decimal places.

    Usage in template: {{ number|formatfloat }} or {{ number|formatfloat:3 }}
    """
    try:
        num = float(value)
        decimal_places = int(decimal_places) if decimal_places else 2
    except (ValueError, TypeError):
        return str(value)

    abs_num = abs(num)
    sign = "-" if num < 0 else ""



    for unit in si_units:
        if abs_num >= unit['value']:
            scaled_value = abs_num / unit['value']

            # Round to specified decimal places
            rounded = round(scaled_value, decimal_places)

            # Format with thousands separators
            if rounded == int(rounded):
                formatted = add_thousands_separator(str(int(rounded)))
            else:
                # Format with specified decimal places, removing trailing zeros
                formatted = f"{rounded:.{decimal_places}f}".rstrip('0').rstrip('.')
                formatted = add_thousands_separator(formatted)

            symbol_part = f" {unit['symbol']}" if unit['symbol'] else ""
            return f"{sign}{formatted} {symbol_part}"

    # For very small numbers, format with decimal places
    if abs_num == 0:
        return "0"
    else:
        rounded = round(num, decimal_places)
        if rounded == int(rounded):
            return str(int(rounded))
        else:
            formatted = f"{rounded:.{decimal_places}f}".rstrip('0').rstrip('.')
            return add_thousands_separator(formatted)


@register.filter
def format_percentage(value, decimal_places=2):
    """
    Format a decimal value as a percentage with specified decimal places.

    Usage in template: {{ 0.1234|formatpercentage }} → "12.3%"
                      {{ 0.1234|formatpercentage:2 }} → "12.34%"
    """
    try:
        num = float(value)
        decimal_places = int(decimal_places) if decimal_places else 1
    except (ValueError, TypeError):
        return str(value)

    # Convert to percentage
    percentage = num * 100
    abs_percentage = abs(percentage)
    sign = "-" if percentage < 0 else ""



    rounded = round(abs_percentage, decimal_places)
    if rounded == int(rounded):
        formatted = str(int(rounded))
    else:
        formatted = f"{rounded:.{decimal_places}f}".rstrip('0').rstrip('.')
    formatted = add_thousands_separator(formatted)



    return f"{sign}{formatted} %"

    return "0%"

