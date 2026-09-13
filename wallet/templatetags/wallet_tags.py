from django import template

from core.utils import toman_format
from core.utils import gregorian_to_jalali

register = template.Library()


@register.filter
def toman(value):
    return toman_format(value)


@register.filter
def jalali_date(value):
    return gregorian_to_jalali(value)
