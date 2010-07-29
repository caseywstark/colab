from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.contenttypes import generic

import mptt
import object_feeds

class Discipline(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    
    about = models.TextField(blank=True)
    
    # followers
    followers_count = models.PositiveIntegerField(default=0, editable=False)
    
    # fields for the tree to work and migrate properly
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    lft = models.PositiveIntegerField(null=True, blank=True)
    rght = models.PositiveIntegerField(null=True, blank=True)
    tree_id = models.PositiveIntegerField(null=True, blank=True)
    level = models.PositiveIntegerField(null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('discipline_detail', (), {'slug': self.slug})
    
    def researcher_is_member(self, researcher):
        if self == researcher.expertise:
            return True
        else:
            return False
    
    def save(self, *args, **kwargs):
        super(Discipline, self).save(*args, **kwargs)
        
        if not self.feed.all():
            pass

try:
    mptt.register(Discipline)
except mptt.AlreadyRegistered:
    pass

object_feeds.register(Discipline)


from django.db.models.signals import pre_save, post_save

def discipline_feed_title_update(sender, instance, created, **kwargs):
    instance.feed.title = instance.name
    instance.feed.save()

post_save.connect(discipline_feed_title_update, sender=Discipline)
