from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

register = template.Library()

from voting.models import Vote
from issues.models import Issue, IssueContributor
from wikis.models import Wiki

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

### Meta summary for a issue: votes; contrib, issues, wiki counts ###
@register.inclusion_tag("issues/meta_summary.html")
def issue_meta_summary(issue):
    contributor_count = issue.contributors.count()
    
    wikis = Wiki.objects.get_for_object(issue)
    wiki_count = wikis.count()
    
    return {'issue': issue, 'contributor_count': contributor_count, 'wiki_count': wiki_count}

### Meta for a issue: voting, permalink, flag, bounty, and top contribs ###
@register.inclusion_tag("issues/meta.html", takes_context=True)
def issue_meta(context, issue):
    
    # get vote details
    issue_type = ContentType.objects.get_for_model(Issue)
    try:
        previous_vote = Vote.objects.get(content_type=issue_type, object_id=issue.id, user=context['request'].user)
    except:
        previous_vote = None
    
    # get status
    status = 'unresolved'
    if issue.resolved:
        status = 'resolved'
    
    # get issue contributors
    contributors = IssueContributor.objects.filter(issue=issue).order_by('-contributions')
    
    return {'issue': issue, 'request': context['request'], 'top_contributors': contributors,
        'previous_vote': previous_vote, 'status': status,}

### Resolution preview: snippet of resolution article ###
@register.inclusion_tag("community_pages/teaser.html")
def resolution_preview(issue):
    return {}
