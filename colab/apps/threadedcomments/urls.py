from django.conf.urls.defaults import patterns, url
from threadedcomments.models import FreeThreadedComment, ThreadedComment
from threadedcomments import views

from voting.views import vote_on_object

free = {'model' : FreeThreadedComment}

urlpatterns = patterns('',
    ### Comments ###
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.comment, name="tc_comment"),
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/$', views.comment, name="tc_comment_parent"),
    url(r'^comment/(?P<object_id>\d+)/delete/$', views.comment_delete, name="tc_comment_delete"),
    url(r'^comment/(?P<edit_id>\d+)/edit/$', views.comment, name="tc_comment_edit"),
    
    ### Comments (AJAX) ###
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<ajax>json|xml)/$', views.comment, name="tc_comment_ajax"),
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/(?P<ajax>json|xml)/$', views.comment, name="tc_comment_parent_ajax"),
    url(r'^comment/(?P<edit_id>\d+)/edit/(?P<ajax>json|xml)/$', views.comment, name="tc_comment_edit_ajax"),

    ### Free Comments ###
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.free_comment, name="tc_free_comment"),
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/$', views.free_comment, name="tc_free_comment_parent"),
    url(r'^freecomment/(?P<object_id>\d+)/delete/$', views.comment_delete, free, name="tc_free_comment_delete"),
    url(r'^freecomment/(?P<edit_id>\d+)/edit/$', views.free_comment, name="tc_free_comment_edit"),

    ### Free Comments (AJAX) ###
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<ajax>json|xml)/$', views.free_comment, name="tc_free_comment_ajax"),
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/(?P<ajax>json|xml)/$', views.free_comment, name="tc_free_comment_parent_ajax"),
    url(r'^freecomment/(?P<edit_id>\d+)/edit/(?P<ajax>json|xml)/$', views.free_comment, name="tc_free_comment_edit_ajax"),
    
    ### Custom shit ###
    # comment voting
    url(r'^voting/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$',
            vote_on_object, dict(model=ThreadedComment, template_object_name='comment',
            allow_xmlhttprequest=True, confirm_vote=False), name="comment_vote"),
)
