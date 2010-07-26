from django import template

from django.core.urlresolvers import reverse

register = template.Library()

### Constructs the feed_subscription link for any object ###
@register.inclusion_tag("feeds/follow.html", takes_context=True)
def follow_link(context, content_object, extra_text=None):
    user = context['request'].user
    feed = content_object.feed
    subscription_url = reverse('feeds_subscription', kwargs={'feed_id': feed.id})
    
    if user.is_authenticated():
        subscription = feed.is_user_following(user)
    else:
        subscription = None
        
    return {'subscription_url': subscription_url, 'subscription': subscription, 'extra_text': extra_text}

@register.inclusion_tag("feeds/update_teaser.html", takes_context=True)
def update_teaser(context, update):
    
    return {'update': update, 'user': update.user, 'action': update.action, 'object': update.feed.feed_object}
