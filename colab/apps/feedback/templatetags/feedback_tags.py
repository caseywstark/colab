from django.template import Library, Node

from feedback.models import Feedback

register = Library()

@register.inclusion_tag("feedback/feedback_item.html", takes_context=True)
def show_feedback(context, feedback):
    return {'feedback': feedback, 'request': context['request']}

@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if 'search' in getvars:
        del getvars['search']
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path

@register.simple_tag
def persist_getvars(request):
    getvars = request.GET.copy()
    if len(getvars.keys()) > 0:
        return "?%s" % getvars.urlencode()
    return ''
