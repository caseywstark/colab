from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from threadedcomments.models import ThreadedComment
from tagging.fields import TagField

import object_feeds

# The diff stuff
from diff_match_patch import diff_match_patch

# We dont need to create a new one everytime
dmp = diff_match_patch()

def diff(txt1, txt2):
    """Create a 'diff' from txt1 to txt2."""
    patch = dmp.patch_make(txt1, txt2)
    return dmp.patch_toText(patch)


class QuerySetManager(models.Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)
		
	def __getattr__(self, attr, *args):
		return getattr(self.get_query_set(), attr, *args)

class Summary(models.Model):
    """ A summary of a discussion. """
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    
    summarized = models.ManyToManyField(ThreadedComment, verbose_name=_(u'Comments Summarized'))
    
    content = models.TextField(_("content"))
    
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
        app_label = "summaries"
        verbose_name = _("Summary")
        verbose_name_plural = _("Summaries")
    
    def __unicode__(self):
        return u"Summary of %s" % self.content_object
    
    def get_absolute_url(self):
        return reverse("summary_detail", kwargs={"summary_id": self.id})
    
    def latest_revision(self):
        try:
            return self.revision_set.filter(reverted=False).order_by('-revision')[0]
        except IndexError:
            return SummaryRevision.objects.none()
    
    def new_revision(self, old_content, comment, editor):
        """ Create a new Revision with the old content. """
        content_diff = diff(self.content, old_content)

        rev = SummaryRevision( #.objects.create(
            summary=self,
            comment=comment,
            editor=editor,
            content = self.content,
            content_diff=content_diff)
        rev.save()
        
        return rev
        
    def revert_to(self, revision, editor):
        """ Revert the summary to a previuos state, by revision number. """
        revision = self.revision_set.get(revision=revision)
        revision.reapply(editor)

object_feeds.register(Summary)

class NonRevertedRevisionManager(QuerySetManager):
    def get_default_queryset(self):
        super(NonRevertedRevisionManager, self).get_query_set().filter(reverted=False)

class SummaryRevision(models.Model):
    """ A change in Summary. """
    
    summary = models.ForeignKey(Summary, verbose_name=_(u'Summary'), related_name='revision')
    editor = models.ForeignKey(User, verbose_name=_(u'Editor'), null=True)
    revision = models.IntegerField(_(u"Revision Number"))
    
    content_diff = models.TextField(_(u"Content Patch"), blank=True)
    content = models.TextField(_(u"Content"))

    comment = models.CharField(_(u"Editor comment"), max_length=255, blank=True)
    modified = models.DateTimeField(_(u"Modified at"), default=datetime.now)
    reverted = models.BooleanField(_(u"Reverted Revision"), default=False)
    
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)

    objects = QuerySetManager()
    non_reverted_objects = NonRevertedRevisionManager()

    class QuerySet(QuerySet):
        def all_later(self, revision):
            """ Return all changes later to the given revision.
            Util when we want to revert to the given revision.
            """
            return self.filter(revision__gt=int(revision))

    class Meta:
        verbose_name = _(u'Summary revision')
        verbose_name_plural = _(u'Summary revisions')
        get_latest_by  = 'modified'
        ordering = ('-revision',)
    
    def __unicode__(self):
        return u'Summary Revision %d' % self.revision
    
    def get_absolute_url(self):
        return reverse("summary_revision", kwargs={"summary_id": self.summary.id, "revision": self.revision})
    
    def reapply(self, editor):
        """ Return the Summary to this revision. """

        # XXX Would be better to exclude reverted revisions
        #     and revisions previous/next to reverted ones
        next_changes = self.summary.revision_set.filter(
            revision__gt=self.revision).order_by('-revision')

        summary = self.summary

        content = None
        for revision in next_changes:
            if content is None:
                content = summary.content
            patch = dmp.patch_fromText(revision.content_diff)
            content = dmp.patch_apply(patch, content)[0]

            revision.reverted = True
            revision.save()

        old_content = summary.content
        old_title = summary.title

        summary.content = content
        summary.title = revision.old_title
        summary.save()

        summary.new_revision(old_content=old_content, old_title=old_title,
            comment="Reverted to revision #%s" % self.revision, editor=editor)

        self.save()

    def save(self, force_insert=False, force_update=False):
        """ Saves the summary with a new revision. """
        if self.id is None:
            try:
                self.revision = SummaryRevision.objects.filter(
                    summary=self.summary).latest().revision + 1
            except self.DoesNotExist:
                self.revision = 1
        super(SummaryRevision, self).save()#force_insert, force_update)

    def display_diff(self):
        ''' Returns a HTML representation of the diff. '''

        # well, it *will* be the old content
        old_content = self.summary.content

        # newer non-reverted revisions of this summary, starting from this
        newer_revisions = SummaryRevision.non_reverted_objects.filter(
            summary=self.summary,
            revision__gte=self.revision)

        # apply all patches to get the content of this revision
        for i, revision in enumerate(newer_revisions):
            patches = dmp.patch_fromText(revision.content_diff)
            if len(newer_revisions) == i+1:
                # we need to compare with the next revision after the change
                next_rev_content = old_content
            old_content = dmp.patch_apply(patches, old_content)[0]

        diffs = dmp.diff_main(old_content, next_rev_content)
        return dmp.diff_prettyHtml(diffs)


