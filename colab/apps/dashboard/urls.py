from django.conf.urls.defaults import *

urlpatterns = patterns("dashboard.views",
    
    url(r"^$", "dashboard", name="dashboard"),
    url(r"^updates/$", "dashboard", name="dashboard_updates"),
    url(r"^posts/$", "posts", name="dashboard_posts"),
    url(r"^votes/$", "votes", name="dashboard_votes"),
    
    url(r"^user/(?P<username>[\w\._-]+)/$", "dashboard", kwargs={'mine': False}, name="dashboard"),
    url(r"^user/(?P<username>[\w\._-]+)/updates/$", "dashboard", kwargs={'mine': False}, name="dashboard_updates"),
    url(r"^user/(?P<username>[\w\._-]+)/posts/$", "posts", kwargs={'mine': False}, name="dashboard_posts"),
    
    # comments
    url(r'^comment/(?P<comment_id>\d+)/edit$', "comment_edit", name="comment_edit"),
    url(r'^comment/(?P<comment_id>\d+)/reply$', "comment_reply", name="comment_reply"),
)
