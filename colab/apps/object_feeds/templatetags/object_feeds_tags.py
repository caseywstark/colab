from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

register = template.Library()

### Show an update instance ###
@register.inclusion_tag("feeds/update.html", takes_context=True)
def show_update(context, update):
    feed_object = update.feed.feed_object
    update_object = update.content_object
    icon = object_content = None
    
    feed_object_link = '<a class="update-object" href="%s">%s</a>' % (feed_object.get_absolute_url(), feed_object)
    update_object_link = None
    
    if update.action_description.startswith('create'):
        icon = 'create'
        update_line = update.action_description % feed_object_link
    elif update.action_description.startswith('edit'):
        icon = 'edit'
        update_line = update.action_description % feed_object_link
    elif update.action_description.startswith('added to the discussion'):
        icon = 'comment'
        update_line = update.action_description % feed_object_link
    elif update.action_description.startswith('added the paper'):
        icon = 'paper'
        update_object_link = '<a class="update-object" href="%s">%s</a>' % (update_object.get_absolute_url(), update_object)
        update_line = update.action_description % (update_object_link, feed_object_link)
    elif update.action_description.startswith('started following'):
        icon = 'follow'
        update_line = update.action_description % feed_object_link
    elif update.action_description.startswith('resolved'):
        icon = 'resolve'
        update_line = update.action_description % feed_object_link
    else:
        icon = 'settings'
        update_line = update.action_description % feed_object_link
    
    return {'update': update, 'update_user': update.user, 'icon': icon,
        'feed_object': feed_object, 'update_object': update_object, 'update_line': update_line,
        'update_content': update.update_content, 'STATIC_URL': settings.STATIC_URL}

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
