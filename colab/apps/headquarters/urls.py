from django.conf.urls.defaults import *

urlpatterns = patterns("headquarters.views",
    
    url(r"^$", "headquarters", name="headquarters"),
    url(r"^updates/$", "headquarters", name="headquarters_updates"),
    url(r"^posts/$", "posts", name="headquarters_posts"),
    url(r"^votes/$", "votes", name="headquarters_votes"),
    
    url(r"^user/(?P<username>[\w\._-]+)/$", "headquarters", kwargs={'mine': False}, name="headquarters"),
    url(r"^user/(?P<username>[\w\._-]+)/updates/$", "headquarters", kwargs={'mine': False}, name="headquarters_updates"),
    url(r"^user/(?P<username>[\w\._-]+)/posts/$", "posts", kwargs={'mine': False}, name="headquarters_posts"),
    
    # comments
    url(r'^comment/(?P<comment_id>\d+)/edit$', "comment_edit", name="comment_edit"),
    url(r'^comment/(?P<comment_id>\d+)/reply$', "comment_reply", name="comment_reply"),
)
