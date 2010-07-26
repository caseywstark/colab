from django import template

register = template.Library()

@register.inclusion_tag("people/researcher_item.html", takes_context=True)
def show_researcher(context, researcher):
    return {"researcher": researcher, 'request': context['request']}

@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if "search" in getvars:
        del getvars["search"]
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path
