from django import template

register = template.Library()

@register.filter
def has_key(dictionary, key):
    return key in dictionary

@register.filter
def get_item(dictionary, key):
    """Get the value of a dictionary for the given key."""
    return dictionary.get(key, [])

@register.filter
def chunked(iterable, chunk_size):
    """Split an iterable into chunks of specified size."""
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i + chunk_size]
        