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
    
    # Set up signal receiver to manage the tree when instances of the
    # model are about to be saved.
    model_signals.pre_save.connect(pre_save, sender=model)
    model_signals.post_save.connect(post_save, sender=model)
    
    
    """
    # Add a custom tree manager
    TreeManager(parent_attr, left_attr, right_attr, tree_id_attr,
                level_attr).contribute_to_class(model, tree_manager_attr)
    setattr(model, '_tree_manager', getattr(model, tree_manager_attr))

    # Wrap the model's delete method to manage the tree structure before
    # deletion. This is icky, but the pre_delete signal doesn't currently
    # provide a way to identify which model delete was called on and we
    # only want to manage the tree based on the topmost node which is
    # being deleted.
    def wrap_delete(delete):
        def _wrapped_delete(self):
            opts = self._meta
            tree_width = (getattr(self, opts.right_attr) -
                          getattr(self, opts.left_attr) + 1)
            target_right = getattr(self, opts.right_attr)
            tree_id = getattr(self, opts.tree_id_attr)
            self._tree_manager._close_gap(tree_width, target_right, tree_id)
            delete(self)
        return wraps(delete)(_wrapped_delete)
    model.delete = wrap_delete(model.delete)
    """
