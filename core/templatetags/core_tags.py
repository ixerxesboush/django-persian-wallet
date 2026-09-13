from django import template

from core.utils import toman_format

register = template.Library()


@register.filter
def toman(value):
    return toman_format(value)
