from django.conf.urls.defaults import *
from django.conf import settings

from papers import views
from papers.models import Paper, PaperRevision

from voting.views import vote_on_object

urlpatterns = patterns('',
    url(r'^create/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.create, name='paper_create'),
    
    # specific
    url(r'^paper/(?P<slug>[-\w]+)/$', views.paper, name='paper_detail'),
    url(r'^paper/(?P<slug>[-\w]+)/edit/$', views.edit, name='paper_edit'),
    url(r'^paper/(?P<slug>[-\w]+)/delete/$', views.delete, name='paper_delete'),
    url(r'^paper/(?P<slug>[-\w]+)/history/$', views.history, name='paper_history'),
    url(r'^paper/(?P<slug>[-\w]+)/revision/(?P<revision>\d+)/$', views.revision, name='paper_revision'),
    url(r'^paper/(?P<slug>[-\w]+)/revert/(?P<revision>\d+)/$', views.revert, name='paper_revert'),
    
    # paper voting
    url(r'^paper/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=Paper, template_object_name='paper',
            allow_xmlhttprequest=True, confirm_vote=False), name="paper_vote"),
    url(r'^revision/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=PaperRevision, template_object_name='revision',
            allow_xmlhttprequest=True, confirm_vote=False), name="paper_revision_vote"),
)
