from django.conf.urls.defaults import *
from django.conf import settings

from wikis import views
from wikis.models import Wiki, ChangeSet

from voting.views import vote_on_object

urlpatterns = patterns('',
    url(r'^create/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.create, kwargs={'wiki_type': 'page'}, name='wiki_create'),
    url(r'^create/(?P<content_type>\d+)/(?P<object_id>\d+)/paper/$', views.create, kwargs={'wiki_type': 'paper'}, name='wiki_create_paper'),
    url(r'^create/(?P<content_type>\d+)/(?P<object_id>\d+)/summary/$', views.create, kwargs={'wiki_type': 'summary'}, name='wiki_create_summary'),
    
    # specific
    url(r'^wiki/(?P<wiki_id>\d+)/$', views.wiki, name='wiki_detail'),
    url(r'^wiki/(?P<wiki_id>\d+)/edit/$', views.edit, name='wiki_edit'),
    url(r'^wiki/(?P<wiki_id>\d+)/delete/$', views.delete, name='wiki_delete'),
    url(r'^wiki/(?P<wiki_id>\d+)/history/$', views.history, name='wiki_history'),
    url(r'^wiki/(?P<wiki_id>\d+)/history/changeset/(?P<revision>\d+)/$', views.changeset, name='wiki_changeset'),
    url(r'^wiki/(?P<wiki_id>\d+)/history/revert/(?P<revision>\d+)/$', views.revert, name='wiki_revert'),
    
    # wiki voting
    url(r'^wiki/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=Wiki, template_object_name='wiki',
            allow_xmlhttprequest=True, confirm_vote=False), name="wiki_vote"),
    url(r'^changeset/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=ChangeSet, template_object_name='changeset',
            allow_xmlhttprequest=True, confirm_vote=False), name="changeset_vote"),
)
