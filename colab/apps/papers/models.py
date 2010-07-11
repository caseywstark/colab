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


class QuerySetManager(models.Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)
		
	def __getattr__(self, attr, *args):
		return getattr(self.get_query_set(), attr, *args)

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
    last_edited = models.DateTimeField(blank=True, null=True)
    
    tags = TagField()
    
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)
    
    class QuerySet(QuerySet):
        def _generate_object_kwarg_dict(self, content_object, **kwargs):
            """ Generates the keyword arguments for a given ``content_object``. """
            
            kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
            kwargs['object_id'] = getattr(content_object, 'pk', getattr(content_object, 'id'))
            return kwargs
        
        def get_for_object(self, content_object, **kwargs):
            return self.filter(**self._generate_object_kwarg_dict(content_object, **kwargs))
    
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

    objects = QuerySetManager()
    
    class QuerySet(QuerySet):
        def _generate_object_kwarg_dict(self, content_object, **kwargs):
            """ Generates the keyword arguments for a given ``content_object``. """
            
            kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
            kwargs['object_id'] = getattr(content_object, 'pk', getattr(content_object, 'id'))
            return kwargs
        
        def get_for_object(self, content_object, **kwargs):
            return self.filter(**self._generate_object_kwarg_dict(content_object, **kwargs))

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
        return reverse("paper_revision", kwargs={"paper_id": self.paper.id, "revision": self.revision})
