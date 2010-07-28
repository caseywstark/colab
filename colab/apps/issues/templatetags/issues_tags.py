from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

register = template.Library()

from voting.models import Vote
from issues.models import Issue, IssueContributor

@register.inclusion_tag("issues/issue_item.html", takes_context=True)
def show_issue(context, issue):
    return {'issue': issue, 'request': context['request']}

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

@register.simple_tag
def filter_url(request, the_filter, the_value):
    getvars = request.GET.copy()
    getvars[the_filter] = the_value
    return "%s?%s" % (request.path, getvars.urlencode())

@register.simple_tag
def remove_filter_url(request, the_filter):
    getvars = request.GET.copy()
    del getvars[the_filter]
    return "%s?%s" % (request.path, getvars.urlencode())

@register.simple_tag
def filter_link(request, the_filter, the_value, the_text):
    return '<a href="%s">%s</a>' % (filter_url(request, the_filter, the_value), the_text)

# can't believe this isn't in django core...
@register.filter
# truncate after a certain number of characters
def truncatechar(text, length):
    if len(text) <= length:
        return text
    else:
        return text[:length] + '...'
