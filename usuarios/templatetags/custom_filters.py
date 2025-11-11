from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acceder a un valor de un diccionario en el template."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def get_index(value, index):
    """Permite acceder a una posición dentro de una lista en el template."""
    try:
        return value[index]
    except (IndexError, TypeError):
        return None
