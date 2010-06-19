from django.conf.urls.defaults import *
from django.conf import settings

from summaries import views
from summaries.models import Wiki, ChangeSet

from voting.views import vote_on_object

urlpatterns = patterns('',
    url(r'^create/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.create, name='summary_create'),
    
    # specific
    url(r'^summary/(?P<summary_id>\d+)/$', views.detail, name='summary_detail'),
    url(r'^summary/(?P<summary_id>\d+)/edit/$', views.edit, name='summary_edit'),
    url(r'^summary/(?P<summary_id>\d+)/delete/$', views.delete, name='summary_delete'),
    url(r'^summary/(?P<summary_id>\d+)/history/$', views.history, name='summary_history'),
    url(r'^summary/(?P<summary_id>\d+)/history/revision/(?P<revision>\d+)/$', views.revision, name='summary_revision'),
    url(r'^summary/(?P<summary_id>\d+)/history/revert/(?P<revision>\d+)/$', views.revert, name='summary_revert'),
    
    # summary voting
    url(r'^summary/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=Wiki, template_object_name='summary',
            allow_xmlhttprequest=True, confirm_vote=False), name="summary_vote"),
    url(r'^revision/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=ChangeSet, template_object_name='revision',
            allow_xmlhttprequest=True, confirm_vote=False), name="summary_revision_vote"),
)
