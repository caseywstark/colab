from django.conf.urls.defaults import *

from issues.models import Issue
from voting.views import vote_on_object

urlpatterns = patterns("issues.views",
    url(r"^$", "issues", name="issue_list"),
    url(r"^create/$", "create", name="issue_create"),
    url(r"^my_issues/$", "issues", kwargs={'mine': True}, name="my_issues"),
    
    # issue-specific
    url(r"^issue/(?P<slug>[-\w]+)/$", "issue", name="issue_detail"),
    url(r"^issue/(?P<slug>[-\w]+)/delete/$", "delete", name="issue_delete"),
    url(r'^issue/(?P<slug>[-\w]+)/edit/$', "edit", name="issue_edit"),
    url(r'^issue/(?P<slug>[-\w]+)/resolve/$', "resolve", name="issue_resolve"),
    url(r'^issue/(?P<slug>[-\w]+)/invite/$', "invite", name="issue_invite"),
    
    # issue voting
    url(r'^issue/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=Issue, template_object_name='issue',
            allow_xmlhttprequest=True, confirm_vote=False), name="issue_vote"),
)
