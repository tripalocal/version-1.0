from django import template
import markdown

register = template.Library()

@register.filter
def markdown_filter(text):
    # safe_mode governs how the function handles raw HTML
    return markdown.markdown(text, safe_mode='False') 
