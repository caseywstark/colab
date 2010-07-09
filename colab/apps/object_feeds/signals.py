from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType

from object_feeds.models import Action, Feed

def pre_save(sender, instance, **kwargs):
    """
    Makes sure that the feed object has a feed setup.
    
    """
    opts = instance._meta
    feed = getattr(instance, opts.feed_attr)
    
    if not feed: # no feed, yet
        ### terrible place to do this, but it must be done. Make sure that the default actions are defined.
        content_type = ContentType.objects.get_for_model(instance)
        model_name = unicode(opts.verbose_name)
        
        create_action = Action.objects.get_or_create(content_type=content_type, name='create', description='created', slug='create')
        edit_action = Action.objects.get_or_create(content_type=content_type, name='edit', description='edited', slug='edit')
        comment_action = Action.objects.get_or_create(content_type=content_type, name='comment', description='commented on', slug='comment')
        
        the_feed = Feed.objects.create(content_type=content_type)
        setattr(instance, opts.feed_attr, the_feed)

def post_save(sender, instance, created, **kwargs):
    """
    Updates things only accessible after the instance is saved, like object_id.
    
    """
    if not instance.feed.feed_object:
        instance.feed.feed_object = instance
        instance.feed.save()
