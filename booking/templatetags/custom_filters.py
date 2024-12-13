from django import template

register = template.Library()

@register.filter
def has_key(dictionary, key):
    return key in dictionary

@register.filter
def get_item(dictionary, key):
    """Get the value of a dictionary for the given key."""
    return dictionary.get(key, [])