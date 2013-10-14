from django import template

register = template.Library()


def split(value, arg):
    try:
        return value.split(',')[int(arg)]
    except Exception:
        return value


register.filter('split', split)
