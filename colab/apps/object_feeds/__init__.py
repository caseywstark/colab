class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model for object_feeds more than once.
    """
    pass

registry = []

def register(model, feed_attr='feed'):
    """
    Gives the model class a feed for each object.
    
    """
    try:
        from functools import wraps
    except ImportError:
        from django.utils.functional import wraps # Python 2.3, 2.4 fallback

    from django.db.models import signals as model_signals
    from django.db.models import FieldDoesNotExist, ForeignKey
    from django.utils.translation import ugettext as _
    from django.template.defaultfilters import slugify
    from django.contrib.contenttypes.models import ContentType

    from object_feeds import models
    from object_feeds.signals import pre_save, post_save

    if model in registry:
        raise AlreadyRegistered(
            _('The model %s has already been registered.') % model.__name__)
    registry.append(model)

    # Add the feed to the model's Options
    opts = model._meta
    opts.feed_attr = feed_attr

    # Add the feed field since it probably doesn't exist
    for attr in [feed_attr]:
        try:
            opts.get_field(attr)
        except FieldDoesNotExist:
            ForeignKey(models.Feed, unique=True, null=True).contribute_to_class(model, attr)

    # Add feed object methods for model instances
    setattr(model, 'register_action', models.register_action)
    setattr(model, 'is_user_following', models.is_user_following)
    
    # Set up signal receiver to manage the tree when instances of the
    # model are about to be saved.
    model_signals.pre_save.connect(pre_save, sender=model)
    model_signals.post_save.connect(post_save, sender=model)
