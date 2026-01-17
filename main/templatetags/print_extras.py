from django import template

register = template.Library()

@register.filter
def print_entry_for(image, competition):
    if not image or not competition:
        return None
    return image.print_entries.filter(competition=competition).first()