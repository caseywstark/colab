from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from tagging.fields import TagField

import object_feeds

class Paper(models.Model):
    """ A formal write-up of results. """
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    
    title = models.CharField(_("title"), max_length=255, unique=True)
    slug = models.SlugField()
    
    creator = models.ForeignKey(User, verbose_name=_("creator"), related_name="%(class)s_created")
    created = models.DateTimeField(_("created"), default=datetime.now)
    last_editor = models.ForeignKey(User, verbose_name=_("last_editor"), related_name="%(class)s_edited")
    last_edited = models.DateTimeField(default=datetime.now)
    
    tags = TagField()
    
    contributor_users = models.ManyToManyField(User,
        through = "PaperContributor",
        verbose_name = _("contributor")
    )
    
    ### denormalization
    # votes
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)
    # contributors
    contributors_count = models.PositiveIntegerField(default=0, editable=False)
    # comments
    comments_count = models.PositiveIntegerField(default=0, editable=False)
    # followers
    followers_count = models.PositiveIntegerField(default=1, editable=False)
    
    class Meta:
        app_label = "papers"
        verbose_name = _("Paper")
        verbose_name_plural = _("Papers")
        ordering = ['slug']
        get_latest_by = 'last_edited'
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("paper_detail", kwargs={"slug": self.slug})
    
    def user_is_contributor(self, user):
        return self.contributors.filter(user=user).exists()
    
    @property
    def current(self):
        return self.revisions.latest()
    
    @property
    def revision(self, rev_number):
        return self.revisions.get(revision=rev_number)

object_feeds.register(Paper)


class PaperRevision(models.Model):
    """ A change in Paper. """
    
    paper = models.ForeignKey(Paper, verbose_name=_(u'Paper'), related_name="revisions")
    editor = models.ForeignKey(User, verbose_name=_(u'Editor'), null=True)
    revision = models.IntegerField(_(u"Revision Number"))
    comment = models.CharField(_(u"Editor comment"), max_length=255, blank=True)
    
    content = models.TextField(_(u"Content"))

    created = models.DateTimeField(_(u"Modified at"), default=datetime.now)
    
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = _(u'Paper revision')
        verbose_name_plural = _(u'Paper revisions')
        get_latest_by  = 'created'
        ordering = ['-revision']
    
    def __unicode__(self):
        return ugettext('Revision %(created)s for %(page_title)s') % {
            'created': self.created.strftime('%Y%m%d-%H%M'),
            'page_title': self.paper.title,
        }
    
    def get_absolute_url(self):
        return reverse("paper_revision", kwargs={"paper_id": self.paper.id, "revision_number": self.revision})
        

class PaperContributor(models.Model):
    
    paper = models.ForeignKey(Paper, related_name = "contributors", verbose_name = _("paper"))
    user = models.ForeignKey(User, related_name = "papers", verbose_name = _("user"))
    
    contributions = models.PositiveIntegerField(_("contributions"), default=1)
    
    away = models.BooleanField(_("away"), default=False)
    away_message = models.CharField(_("away_message"), max_length=500)
    away_since = models.DateTimeField(_("away since"), default=datetime.now)
    
    class Meta:
        unique_together = [("user", "paper")]


from django.db.models.signals import pre_save, post_save

def paper_feed_title_update(sender, instance, created, **kwargs):
    instance.feed.title = instance.title
    instance.feed.save()

post_save.connect(paper_feed_title_update, sender=Paper)
