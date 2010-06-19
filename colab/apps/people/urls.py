from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r"^username_autocomplete/$", "autocomplete_app.views.username_autocomplete_friends", name="profile_username_autocomplete"),
    url(r"^$", "people.views.researchers", name="researcher_list"),
    url(r"^profile/(?P<username>[\w\._-]+)/$", "people.views.researcher", name="researcher_detail"),
    url(r"^edit/$", "people.views.researcher_edit", name="researcher_edit"),
    
    url(r"^my_profile/$", "people.views.researcher", kwargs={'myself': True}, name="my_profile"),
)
