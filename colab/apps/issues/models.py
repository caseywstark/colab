from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from tagging.fields import TagField

from disciplines.models import Discipline
from people.models import Institution
from papers.models import Paper
import object_feeds

class Issue(models.Model):
    
    title = models.CharField(_("title"), max_length=255, unique=True)
    slug = models.SlugField(_("slug"), unique=True)
    creator = models.ForeignKey(User, verbose_name=_("creator"), related_name="%(class)s_created")
    created = models.DateTimeField(_("created"), default=datetime.now)
    description = models.TextField(_("description"))
    
    private = models.BooleanField(_("private"), default=False)
    
    disciplines = models.ManyToManyField(Discipline, blank=True)
    tags = TagField()
    
    # resolution
    resolved = models.BooleanField(default=False)
    resolution = models.ForeignKey(Paper, null=True, blank=True, related_name='resolved_issue')
    
    contributor_users = models.ManyToManyField(User,
        through = "IssueContributor",
        verbose_name = _("contributor")
    )
    
    # store contributing institutions! why not?
    institutions = models.ManyToManyField(Institution, blank=True)
    
    ### denormalization
    # votes
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)
    # contributors
    contributors_count = models.PositiveIntegerField(default=1, editable=False)
    # comments
    comments_count = models.PositiveIntegerField(default=0, editable=False)
    # followers
    followers_count = models.PositiveIntegerField(default=1, editable=False)
    
    @property
    def papers(self):
        return Paper.objects.filter(content_type=ContentType.objects.get_for_model(self),object_id=self.id)
    
    class Meta:
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("issue_detail", kwargs={"slug": self.slug})
    
    def user_is_contributor(self, user):
        return self.contributors.filter(user=user).exists()
    
    def user_can_read(self, user):
        if self.private and not self.user_is_contributor(user):
            return False
        return True
    
    def resolve(self, resolution_id):
        try:
            resolution = Paper.objects.get(id=resolution_id)
        except:
            return False
        
        self.resolution = resolution
        self.resolved = True
        self.save()
        return resolution

object_feeds.register(Issue)

class IssueContributor(models.Model):
    
    issue = models.ForeignKey(Issue, related_name = "contributors", verbose_name = _("issue"))
    user = models.ForeignKey(User, related_name = "issues", verbose_name = _("user"))
    
    contributions = models.PositiveIntegerField(_("contributions"), default=1)
    
    away = models.BooleanField(_("away"), default=False)
    away_message = models.CharField(_("away_message"), max_length=500)
    away_since = models.DateTimeField(_("away since"), default=datetime.now)
    
    class Meta:
        unique_together = [("user", "issue")]

