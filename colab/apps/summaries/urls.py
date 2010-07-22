from django.conf.urls.defaults import *
from django.conf import settings

from summaries import views
from summaries.models import Summary, SummaryRevision

from voting.views import vote_on_object

urlpatterns = patterns('',
    url(r'^create/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.create, name='summary_create'),
    
    # specific
    url(r'^(?P<slug>[-\w]+)/$', views.summary, name='summary_detail'),
    url(r'^(?P<slug>[-\w]+)/edit/$', views.edit, name='summary_edit'),
    url(r'^(?P<slug>[-\w]+)/delete/$', views.delete, name='summary_delete'),
    url(r'^(?P<slug>[-\w]+)/history/$', views.history, name='summary_history'),
    url(r'^(?P<slug>[-\w]+)/changes/$' , views.changes, name='summary_changes'),
    url(r'^(?P<slug>[-\w]+)/revision/(?P<revision_number>\d+)/$', views.summary, name='summary_revision'),
    url(r'^(?P<slug>[-\w]+)/revision/(?P<revision_number>\d+)/delete/$', views.delete, name='summary_delete'),
    url(r'^(?P<slug>[-\w]+)/revert/(?P<revision_number>\d+)/$', views.edit, name='summary_edit'),
    
    # summary voting
    url(r'^(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=Summary, template_object_name='summary',
            allow_xmlhttprequest=True, confirm_vote=False), name="summary_vote"),
    url(r'^(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=SummaryRevision, template_object_name='revision',
            allow_xmlhttprequest=True, confirm_vote=False), name="summary_revision_vote"),
)
