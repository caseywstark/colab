from django.contrib import admin
from object_feeds.models import FeedType, Feed, Subscription, Update, Action

admin.site.register(FeedType)
admin.site.register(Feed)
admin.site.register(Subscription)
admin.site.register(Update)admin.site.register(Action)
