from django import template

register = template.Library()


def split(value, arg):
    try:
        return value.split(',')[int(arg)]
    except Exception:
        return value

def custom_divide(value, arg):
    try:
        return ','.join(value.split(',')[int(arg):])
    except Exception:
        return value


register.filter('split', split)
register.filter('custom_divide', custom_divide)
