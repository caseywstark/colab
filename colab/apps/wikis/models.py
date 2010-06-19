from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from diff_match_patch import diff_match_patch

# We dont need to create a new one everytime
dmp = diff_match_patch()

def diff(txt1, txt2):
    """Create a 'diff' from txt1 to txt2."""
    patch = dmp.patch_make(txt1, txt2)
    return dmp.patch_toText(patch)

from threadedcomments.models import ThreadedComment
from tagging.fields import TagField

import object_feeds

wiki_types = (
    ('PR', 'Paper'),
    ('SM', 'Summary'),
    ('PG', 'Page'),
)

class QuerySetManager(models.Manager):
	def get_query_set(self):
		return self.model.QuerySet(self.model)
		
	def __getattr__(self, attr, *args):
		return getattr(self.get_query_set(), attr, *args)

class Wiki(models.Model):
    """
    A page editable by anyone with revision control. Basically a wiki page with
    some extra goodies.
    
    """
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    
    wiki_type = models.CharField(_("type"), max_length=2, choices=wiki_types, blank=False, default='PR')
    
    title = models.CharField(_("title"), max_length=255, blank=True)
    
    content = models.TextField(_("content"))
    
    creator = models.ForeignKey(User, verbose_name=_("creator"), related_name="%(class)s_created", null=True)
    created = models.DateTimeField(_("created"), default=datetime.now)
    last_update = models.DateTimeField(blank=True, null=True)
    
    tags = TagField()
    
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)
    
    # only for summaries
    summarized = models.ManyToManyField(ThreadedComment, verbose_name=_(u'Comments Summarized'))
    
    objects = QuerySetManager()
    
    class QuerySet(QuerySet):
        def _generate_object_kwarg_dict(self, content_object, **kwargs):
            """
            Generates the keyword arguments for a given ``content_object``.
            """
            
            kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
            kwargs['object_id'] = getattr(content_object, 'pk', getattr(content_object, 'id'))
            return kwargs
        
        def get_for_object(self, content_object, **kwargs):
            return self.filter(**self._generate_object_kwarg_dict(content_object, **kwargs))
        
        def papers_for_object(self, content_object, **kwargs):
            filter_dict = self._generate_object_kwarg_dict(content_object, **kwargs)
            filter_dict.update({'wiki_type': 'PR'})
            return self.filter(**filter_dict)
        
        def summaries_for_object(self, content_object, **kwargs):
            filter_dict = self._generate_object_kwarg_dict(content_object, **kwargs)
            filter_dict.update({'wiki_type': 'SM'})
            return self.filter(**filter_dict)
        
        def pages_for_object(self, content_object, **kwargs):
            filter_dict = self._generate_object_kwarg_dict(content_object, **kwargs)
            filter_dict.update({'wiki_type': 'PG'})
            return self.filter(**filter_dict)
    
    class Meta:
        app_label = "wikis"
        verbose_name = _("Wiki")
        verbose_name_plural = _("Wikis")
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("wiki_detail", kwargs={"wiki_id": self.id})
    
    def save(self, force_insert=False, force_update=False):
        self.last_update = datetime.now()
        super(Wiki, self).save(force_insert, force_update)
    
    def latest_changeset(self):
        try:
            return self.changeset_set.filter(reverted=False).order_by('-revision')[0]
        except IndexError:
            return ChangeSet.objects.none()
    
    def new_revision(self, old_content, old_title, comment, editor):
        '''Create a new ChangeSet with the old content.'''
        content_diff = diff(self.content, old_content)

        cs = ChangeSet( #.objects.create(
            wiki=self,
            comment=comment,
            editor=editor,
            old_title=old_title,
            content = self.content,
            content_diff=content_diff)
        cs.save()

        return cs
        
    def revert_to(self, revision, editor):
        """ Revert the wiki to a previuos state, by revision number. """
        changeset = self.changeset_set.get(revision=revision)
        changeset.reapply(editor)

object_feeds.register(Wiki)

class NonRevertedChangeSetManager(QuerySetManager):
    def get_default_queryset(self):
        super(NonRevertedChangeSetManager, self).get_query_set().filter(reverted=False)

class ChangeSet(models.Model):
    """A report of an older version of some wiki."""
    
    wiki = models.ForeignKey(Wiki, verbose_name=_(u'Wiki'))
    editor = models.ForeignKey(User, verbose_name=_(u'Editor'), null=True)
    revision = models.IntegerField(_(u"Revision Number"))
    
    old_title = models.CharField(_(u"Old Title"), max_length=255, blank=True)
    content_diff = models.TextField(_(u"Content Patch"), blank=True)
    content = models.TextField(_(u"Content"))

    comment = models.CharField(_(u"Editor comment"), max_length=255, blank=True)
    modified = models.DateTimeField(_(u"Modified at"), default=datetime.now)
    reverted = models.BooleanField(_(u"Reverted Revision"), default=False)
    
    yeas = models.PositiveIntegerField(default=0, editable=False)
    nays = models.PositiveIntegerField(default=0, editable=False)
    votes = models.PositiveIntegerField(default=0, editable=False)

    objects = QuerySetManager()
    non_reverted_objects = NonRevertedChangeSetManager()

    class QuerySet(QuerySet):
        def all_later(self, revision):
            """ Return all changes later to the given revision.
            Util when we want to revert to the given revision.
            """
            return self.filter(revision__gt=int(revision))

    class Meta:
        verbose_name = _(u'Change set')
        verbose_name_plural = _(u'Change sets')
        get_latest_by  = 'modified'
        ordering = ('-revision',)
    
    def __unicode__(self):
        return u'Revision %d' % self.revision
    
    def get_absolute_url(self):
        return reverse("wiki_changeset", kwargs={"wiki_id": self.wiki.id, "revision": self.revision})
    
    def reapply(self, editor):
        """ Return the Wiki to this revision. """

        # XXX Would be better to exclude reverted revisions
        #     and revisions previous/next to reverted ones
        next_changes = self.wiki.changeset_set.filter(
            revision__gt=self.revision).order_by('-revision')

        wiki = self.wiki

        content = None
        for changeset in next_changes:
            if content is None:
                content = wiki.content
            patch = dmp.patch_fromText(changeset.content_diff)
            content = dmp.patch_apply(patch, content)[0]

            changeset.reverted = True
            changeset.save()

        old_content = wiki.content
        old_title = wiki.title

        wiki.content = content
        wiki.title = changeset.old_title
        wiki.save()

        wiki.new_revision(old_content=old_content, old_title=old_title,
            comment="Reverted to revision #%s" % self.revision, editor=editor)

        self.save()

    def save(self, force_insert=False, force_update=False):
        """ Saves the Wiki with a new revision. """
        if self.id is None:
            try:
                self.revision = ChangeSet.objects.filter(
                    wiki=self.wiki).latest().revision + 1
            except self.DoesNotExist:
                self.revision = 1
        super(ChangeSet, self).save()#force_insert, force_update)

    def display_diff(self):
        ''' Returns a HTML representation of the diff. '''

        # well, it *will* be the old content
        old_content = self.wiki.content

        # newer non-reverted revisions of this wiki, starting from this
        newer_changesets = ChangeSet.non_reverted_objects.filter(
            wiki=self.wiki,
            revision__gte=self.revision)

        # apply all patches to get the content of this revision
        for i, changeset in enumerate(newer_changesets):
            patches = dmp.patch_fromText(changeset.content_diff)
            if len(newer_changesets) == i+1:
                # we need to compare with the next revision after the change
                next_rev_content = old_content
            old_content = dmp.patch_apply(patches, old_content)[0]

        diffs = dmp.diff_main(old_content, next_rev_content)
        return dmp.diff_prettyHtml(diffs)


