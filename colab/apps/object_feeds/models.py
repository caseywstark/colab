from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template.defaultfilters import date

BASIC_ACTIONS = (
    ('create', 'created'),
    ('edit', 'edited'),
    ('comment', 'commented on'),
)

### Code for the Feed Object ###
def register_action(self, user, action, content_object, object_title='', object_link='', update_content=''):
    content_type = ContentType.objects.get_for_model(self)
    
    # get the Action specified with the action string
    the_action = Action.objects.get(content_type=content_type, slug=action)
    the_update = Update.objects.create(feed=self.feed, user=user, 
        action=the_action, content_object=content_object,
        action_description=the_action.description, object_title=object_title,
        update_content=update_content)

def is_user_following(self, the_user):
    try:
        Subscription.objects.get(feed=self.feed, user=the_user)
        return True
    except:
        return False
        
### End Code ###

class Feed(models.Model):
    
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(null=True, blank=True) # needs to allow null because we create the feed right before the feed_object instance
    feed_object = generic.GenericForeignKey("content_type", "object_id")
    
    title = models.CharField(max_length=255) # keep it synced with the feed_object title somehow...
    
    subscriber_users = models.ManyToManyField(User, through="Subscription", verbose_name=_('subscribers'))
    
    children = models.ManyToManyField('self', blank=True)
    
    def __unicode__(self):
        return 'Feed for %s %s' % (self.content_type, self.feed_object)
    
    @models.permalink
    def get_absolute_url(self):
        return ('feed_detail', (), {'feed_id': self.id})
    
    def is_user_following(self, user):
        try:
            subscription = Subscription.objects.get(feed=self, user=user)
        except:
            return False
        return subscription
    
    def subscribe(self, the_user, the_actions='all'):
        subscription, created = Subscription.objects.get_or_create(feed=self, user=the_user)
        if created:
            if the_actions == 'all':
                actions = Action.objects.filter(content_type=self.content_type)
                subscription.actions = actions
            else:
                subscription.actions = the_actions
            subscription.save()
        return subscription
    
    def unsubscribe(self, the_user):
        try:
            subscription = Subscription.objects.get(feed=self, user=the_user)
        except Subscription.DoesNotExist:
            return false
        subscription.delete()
        return subscription
    
    @property
    def updates(self):
        """
        A wrapper for update_set used in order to distinguish between object
        feeds and researcher feeds (they act differently).
        
        """
        from people.models import Researcher
        researcher_type = ContentType.objects.get_for_model(Researcher)
        if self.content_type == researcher_type:
            return Update.objects.filter(user__id=self.object_id)
        else:
            return self.update_set
    
    def save(self, *args, **kwargs):
        already_created = False
        if self.id:
            already_created = True
            
        super(Feed, self).save(*args, **kwargs)
        
        if not already_created: # just created so we need to connect parent feeds
            pass # do this later

class Subscription(models.Model):
    
    user = models.ForeignKey(User, related_name="feeds", verbose_name=_('user'))
    feed = models.ForeignKey(Feed, related_name="subscribers", verbose_name=_('feed'))
    
    actions = models.ManyToManyField('Action')
    
    top_level = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s\'s subscription to %s' % (self.user, self.feed)
    
    @models.permalink
    def get_absolute_url(self):
        return ('subscription_options', (), {'feed_id': self.feed.id})

class Action(models.Model):
    
    content_type = models.ForeignKey(ContentType)
    description = models.CharField(max_length=255)
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.slug

class Update(models.Model):
    
    feed = models.ForeignKey(Feed, related_name='update_set')
    user = models.ForeignKey(User)
    action = models.ForeignKey(Action, related_name='updates')
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    
    created = models.DateTimeField(_('created'), default=datetime.now)
    
    # denormalizing
    action_description = models.CharField(max_length=255)
    object_title = models.CharField(max_length=255)
    object_link = models.CharField(max_length=255)
    update_content = models.TextField()
    
    def __unicode__(self):
        return '%s %s %s' % (self.user, self.action_description, self.object_title)
    
    @models.permalink
    def get_absolute_url(self):
        return ('update_detail', (), {'update_id': self.id})


from threadedcomments.models import ThreadedComment

def comment_action_update(sender, instance, created, **kwargs):
    object_feed = getattr(instance.content_object, 'feed', None)
    if object_feed and created:
        action_slug = "discussion-%s" % instance.content_object._meta.verbose_name.lower()
        instance.content_object.register_action(instance.user, action_slug, content_object=instance)

post_save.connect(comment_action_update, sender=ThreadedComment)

def followers_count_update(sender, instance, created, **kwargs):
    obj = instance.feed.feed_object
    if hasattr(obj, 'followers_count'):
        if created:
            obj.followers_count = obj.followers_count + 1
        obj.save()

post_save.connect(followers_count_update, sender=Subscription)

