from django import template
import markdown

register = template.Library()

def clean_text(text, target, start_index):
    index = text.find(target, start_index)
    #find consecutive target (#, *)
    i = index+1
    t = target
    while i < len(text) and text[i] == target:
        t += target
        i += 1

    if target == "#" and len(t) < 4:
        #ignore #,##,###
        start_index = index+len(t)
        return (text, start_index)

    target = t

    #remove " " in front of target
    while index-2> 0 and text[index-1] == " ":
        text = text[:index-1] + text[index:]
        index -= 1

    #add "\n" in front of target
    if index-1 >= 0 and text[index-1] != "\n":
        text = text[:index] + "\n" + text[index:]
        index += 1

    #add " " after target
    if index+1 <= len(text) and text[index+len(target)] != " ":
        text = text[:index+len(target)] + " " + text[index+len(target):]

    start_index = index+len(target)
    return (text, start_index)

@register.filter
def markdown_filter(text):
    text = text.replace("＊","*")
    target = ["#", "*"]
    for t in target:
        start_index = 0
        while start_index < len(text) and text.find(t, start_index) >= 0:
            (text, start_index) = clean_text(text, t, start_index)

    # safe_mode governs how the function handles raw HTML
    return markdown.markdown(text, safe_mode='remove') 
