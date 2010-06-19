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
def register_action(self, user, action, content_object):
    # must be valid feed object, check for FeedType
    content_type = ContentType.objects.get_for_model(self)
    feed_type = FeedType.objects.get(content_type=content_type)
    
    # get the Action specified with the action string
    the_action = Action.objects.get(feed_type=feed_type, action=action)
    the_update = Update.objects.create(feed=self.feed, user=user, action=the_action, content_object=content_object)

### End Code ###

class FeedType(models.Model):
    """ Defines the feed type for every object registered to have a feed. """
    
    content_type = models.ForeignKey(ContentType)
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.name

class Feed(models.Model):
    
    feed_type = models.ForeignKey(FeedType)
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    feed_object = generic.GenericForeignKey("content_type", "object_id")
    
    subscriber_users = models.ManyToManyField(User, through="Subscription", verbose_name=_('subscribers'))
    
    children = models.ManyToManyField('self', blank=True)
    
    def __unicode__(self):
        return 'Feed for %s %s' % (self.feed_type, self.feed_object)
    
    @models.permalink
    def get_absolute_url(self):
        return ('feed_detail', (), {'feed_id': self.id})
    
    def is_user_following(self, user):
        try:
            subscription = Subscription.objects.get(feed=self, user=user)
        except Subscription.DoesNotExist:
            return False
        
        return subscription
    
    def save(self, *args, **kwargs):
        already_created = False
        if not self.id:
            already_created = True
            
        super(Feed, self).save(*args, **kwargs)
        
        if not already_created: # just created so we need to connect parent feeds
            if self.feed_type == 'PRJ':
                for discipline in self.feed_object.disciplines.all():
                    discipline.feed.all()[0].children.add(self)
            elif self.feed_type == 'ISU' or self.feed_type == 'WKI':
                self.feed_object.project.feed.all()[0].children.add(self)

class Subscription(models.Model):
    
    user = models.ForeignKey(User, related_name="feeds", verbose_name=_('user'))
    feed = models.ForeignKey(Feed, related_name="subscribers", verbose_name=_('feed'))
    
    actions = models.ManyToManyField('Action')
    
    top_level = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s\'s subscription to %s' % (self.user.get_profile(), self.feed)
    
    @models.permalink
    def get_absolute_url(self):
        return ('subscription_options', (), {'feed_id': self.feed.id})

class Action(models.Model):
    
    feed_type = models.ForeignKey(FeedType)
    action = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.action

class Update(models.Model):
    
    feed = models.ForeignKey(Feed, related_name='updates')
    user = models.ForeignKey(User)
    action = models.ForeignKey(Action, related_name='updates')
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    
    created = models.DateTimeField(_('created'), default=datetime.now)
    
    def __unicode__(self):
        return '%s %s %s' % (self.user, self.action.description, self.content_object)
    
    @models.permalink
    def get_absolute_url(self):
        return ('update_detail', (), {'update_id': self.id})
    
from threadedcomments.models import ThreadedComment


def comment_action_update(sender, instance, created, **kwargs):
    object_feed = getattr(instance.content_object, 'feed', None)
    if object_feed and created:
        instance.content_object.register_action(instance.user, 'comment', content_object=instance)

post_save.connect(comment_action_update, sender=ThreadedComment)
