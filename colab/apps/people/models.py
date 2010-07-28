from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from timezones.fields import TimeZoneField
from tagging.fields import TagField

from disciplines.models import Discipline
import object_feeds

OCCUPATIONS = (
    ('EN', 'Enthusiast'),
    ('SU', 'Undergraduate Student'),
    ('SG', 'Graduate Student'),
    ('PD', 'Postdoctorate'),
    ('RS', 'Researcher'),
    ('PA', 'Assistant Professor'),
    ('PF', 'Full Professor'),
    ('OT', 'Other'),
)

class Institution(models.Model):

    name = models.CharField(max_length=255)
    about = models.TextField(blank=True)
    slug = models.SlugField()
    
    creator = models.ForeignKey(User)
    
    class Meta:
        verbose_name = _("institution")
        verbose_name_plural = _("institutions")
    
    def __unicode__(self):
        return self.name
    
    @models.permalink
    def get_absolute_url(self):
        return ('institution_detail', (), {'slug': self.slug})

class Researcher(models.Model):
    
    user = models.ForeignKey(User, unique=True, verbose_name=_("user"))
    name = models.CharField(_("name"), max_length=50)
    about = models.TextField(_("about"), blank=True)
    website = models.URLField(_("website"),
        blank = True,
        verify_exists = False
    )
    
    expertise = models.ForeignKey(Discipline, null=True, blank=True, related_name='researcher')
    tags = TagField()
    occupation = models.CharField(max_length=2, choices=OCCUPATIONS, blank=True)
    institution = models.ForeignKey(Institution, verbose_name=_("Current Institution"), null=True, blank=True, related_name='researchers')
    grad_institution = models.ForeignKey(Institution, verbose_name=_("Graduate Institution"), null=True, blank=True, related_name='graduates')
    
    ### denormalization
    # followers
    followers_count = models.PositiveIntegerField(default=0, editable=False)
    
    class Meta:
        verbose_name = _("researcher")
        verbose_name_plural = _("researchers")
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("researcher_detail", kwargs={
            "username": self.user.username
        })

object_feeds.register(Researcher)

def create_researcher(sender, instance=None, **kwargs):
    if instance is None:
        return
    researcher, created = Researcher.objects.get_or_create(user=instance)

post_save.connect(create_researcher, sender=User)

def researcher_feed_title_update(sender, instance, created, **kwargs):
    instance.feed.title = instance.name
    instance.feed.save()

post_save.connect(researcher_feed_title_update, sender=Researcher)

