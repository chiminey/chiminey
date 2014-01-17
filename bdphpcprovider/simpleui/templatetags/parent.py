from django import template
import logging
logger = logging.getLogger(__name__)


register = template.Library()

@register.assignment_tag
def myparent(theform, curr_id ):

    key = "parent"
    #key = 'param-%s-parent' %int(curr_id)
    for f in theform:
        if f.name == key:
            try:
                return int(f.value())
            except TypeError:
                return ""
    else:
        return ""
