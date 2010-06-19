from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType

from object_feeds.models import FeedType, Action, Feed

def pre_save(sender, instance, **kwargs):
    """
    Makes sure that the feed object has a feed setup.
    
    """
    opts = instance._meta
    feed = getattr(instance, opts.feed_attr)
    
    if not feed: # no feed, yet
        ### terrible place to do this, but it must be done. Make sure that the
        ### FeedType and default action are defined.
        content_type = ContentType.objects.get_for_model(instance)
        model_name = unicode(opts.verbose_name)
        feed_type, created = FeedType.objects.get_or_create(content_type=content_type, name=model_name, slug=slugify(model_name))
        
        if created:
            create_action = Action.objects.create(feed_type=feed_type, action='create', description='created', slug='create')
            edit_action = Action.objects.create(feed_type=feed_type, action='edit', description='edited', slug='edit')
            comment_action = Action.objects.create(feed_type=feed_type, action='comment', description='commented on', slug='comment')
        
        the_feed = Feed.objects.create(feed_type=feed_type)
        setattr(instance, opts.feed_attr, the_feed)

def post_save(sender, instance, created, **kwargs):
    """
    Updates things only accessible after the instance is saved, like object_id.
    
    """
    if not instance.feed.feed_object:
        instance.feed.feed_object = instance
        instance.feed.save()
