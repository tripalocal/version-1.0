from django import template

register = template.Library()

@register.filter(name='numeric_forloop') 
def numeric_forloop(number):
    if type(number) == int and number > 0:
        return range(number+1)
    else:
        return range(11)