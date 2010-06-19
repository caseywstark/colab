from django.conf.urls.defaults import *

from feedback.models import Feedback
from voting.views import vote_on_object

urlpatterns = patterns("feedback.views",
    url(r"^$", "list", name="feedback_list"),
    url(r"^(?P<list>all|open|closed|mine)/$", "list", name="feedback_list"),
    url(r"^(?P<list>all|open|closed|mine)/(?P<type>[-\w]+)/$", "list", name="feedback_list_type"),
    url(r"^(?P<list>all|open|closed|mine)/(?P<type>[-\w]+)/(?P<status>[-\w]+)/$", "list", name="feedback_list_type_status"),
    
    url(r"^submit/$", "submit", name="feedback_submit"),
    url(r"^detail/(?P<object_id>\d+)/$", "detail", name="feedback_detail"),
    url(r"^detail/(?P<object_id>\d+)/edit/$", "edit", name="feedback_edit"),
    url(r"^detail/(?P<object_id>\d+)/delete/$", "delete", name="feedback_delete"),
    
    url(r"^mine/$", "list", kwargs={"mine": True}, name="my_feedback"),
)

urlpatterns += patterns("",
    url(r"^detail/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/$",
        vote_on_object, dict(model=Feedback, template_object_name='feedback',
        allow_xmlhttprequest=True, confirm_vote=False), name="feedback_vote"),
)
