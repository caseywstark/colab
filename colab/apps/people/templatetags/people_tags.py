from django import template

register = template.Library()

@register.inclusion_tag("people/researcher_item.html")
def show_researcher(researcher):
    return {"researcher": researcher}

@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if "search" in getvars:
        del getvars["search"]
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path
