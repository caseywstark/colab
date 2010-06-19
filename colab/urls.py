from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from account.openid_consumer import PinaxConsumer

handler500 = "pinax.views.server_error"


if settings.ACCOUNT_OPEN_SIGNUP:
    signup_view = "account.views.signup"
else:
    signup_view = "signup_codes.views.signup"

# custom site-wide views
from headquarters import views as hq_views

urlpatterns = patterns("",
    url(r'^$', hq_views.homepage, name="home"),
    url(r'^tutorial/$', hq_views.tutorial, name="tutorial"),
        
    url(r"^admin/invite_user/$", "signup_codes.views.admin_invite_user", name="admin_invite_user"),
    url(r"^account/signup/$", signup_view, name="acct_signup"),
    
    (r"^about/", include("about.urls")),
    (r"^account/", include("account.urls")),
    (r"^openid/(.*)", PinaxConsumer()),
    (r"^bbauth/", include("bbauth.urls")),
    (r"^authsub/", include("authsub.urls")),
    (r"^profiles/", include("profiles.urls")),
    (r"^tags/", include("tag_app.urls")),
    (r"^notices/", include("notification.urls")),
    (r"^messages/", include("messages.urls")),
    (r"^announcements/", include("announcements.urls")),
    (r"^comments/", include("threadedcomments.urls")),
    (r"^robots.txt$", include("robots.urls")),
    (r"^i18n/", include("django.conf.urls.i18n")),
    (r"^admin/", include(admin.site.urls)),
    (r"^avatar/", include("avatar.urls")),
    (r"^flag/", include("flag.urls")),
    
    ### extra ###
    (r"^comments/", include("django.contrib.comments.urls")),
    (r"^feedback/", include("feedback.urls")),
    (r'^ajax-autocomplete/', include('ajax_select.urls')),
    (r'^tinymce/', include('tinymce.urls')),
    
    ### custom ###
    (r"^disciplines/", include("disciplines.urls")),
    (r"^researchers/", include("people.urls")),
    (r"^issues/", include("issues.urls")),
    (r"^wikis/", include("wikis.urls")),
    (r"^headquarters/", include("headquarters.urls")),
    (r"^feeds/", include("object_feeds.urls")),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        (r"", include("staticfiles.urls")),
    )
