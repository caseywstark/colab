from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import object_feeds

STATUS_CHOICES = (
    ('open', 'Open'),
    ('closed', 'Closed'),
)

class Status(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    default = models.BooleanField(blank=True, help_text='New feedback will have this status')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    
    def save(self):
        if self.default == True:
            try:
                default_project = Status.objects.get(default=True)
                default_project.default = False
                default_project.save()
            except:
                pass
        super(Status, self).save()
    
    def __unicode__(self):
        return self.title

class Type(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    
    def __unicode__(self):
        return self.title

class Feedback(models.Model):
    type = models.ForeignKey(Type)
    status = models.ForeignKey(Status)
    title = models.CharField(max_length=500)
    description = models.TextField()
    anonymous = models.BooleanField(blank=True, help_text=_('Do not show who submitted this'))
    private = models.BooleanField(blank=True, help_text=_('Hide from public pages. Only site administrators will be able to view and respond to this.'))
    user = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    page_specific = models.BooleanField(default=False, help_text=_('Specific to this page?'))
    page = models.CharField(max_length=255, blank=True)
    
    ### denormalization
    # votes
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)
    # contributors
    contributors_count = models.PositiveIntegerField(default=0, editable=False)
    # comments
    comments_count = models.PositiveIntegerField(default=0, editable=False)
    
    class Meta:
        ordering = ['-created']
    
    def save(self):
        try:
            self.status
        except:
            try:
                default = Status.objects.get(default=True)
            except:
                default = Status.objects.filter()[0]
            self.status = default
        super(Feedback, self).save()
    
    def get_absolute_url(self):
        return reverse("feedback_detail", kwargs={"object_id": self.id})
    
    def __unicode__(self):
        return self.title
    
object_feeds.register(Feedback)

