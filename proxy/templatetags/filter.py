# coding: utf-8
from django import template


register = template.Library()


@register.filter(name='key_to_value')
def key_to_value(data, key_name):
    return data[key_name]
