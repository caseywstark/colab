from django.conf.urls.defaults import *

urlpatterns = patterns('object_feeds.views',
    url(r'^feed/(?P<feed_id>\d+)/$', 'feed', name='feeds_feed'),
    url(r'^feed/object/(?P<content_type>\d+)/(?P<object_id>\d+)/$', 'feed', name='feeds_feed'),
    
    url(r'^feed/(?P<feed_id>\d+)/subscription/$', 'subscription', name='feeds_subscription'),
    url(r'^feed/object/(?P<content_type>\d+)/(?P<object_id>\d+)/subscription/$', 'subscription', name='feeds_subscription'),
    
    url(r'^mine$', 'feeds', name='my_feeds'),
    url(r'^user/(?P<username>[\w\._-]+)$', 'feeds', kwargs={'mine': False}, name='user_feeds'),
)
