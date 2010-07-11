from django import forms
from django.forms import widgets
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from papers.models import Paper, PaperRevision
from tinymce.widgets import TinyMCE

class PaperForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=30,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
    )
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        required=False, widget=forms.HiddenInput)
    object_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    
    # extra PaperRevsion fields
    content = forms.CharField(widget=TinyMCE)
    comment = forms.CharField(label=_('Change comment (optional)'), required=False, max_length=255)

    class Meta:
        model = Paper
        fields = ['title', 'slug', 'tags', 'content_type', 'object_id']
    
    def __init__(self, *args, **kwargs):
        super(PaperForm, self).__init__(*args, **kwargs)

    def save(self, request, *args, **kwargs):
        
        kwargs["commit"] = False # this is hacky, but we don't want to commit the paper so we can modify creator and last_editor
        
        # if the paper is new, add the creator
        new_paper = False
        if not self.instance.id:
            new_paper = True
            
        paper = super(PaperForm, self).save(*args, **kwargs)
        paper.last_editor = request.user
        if new_paper:
            paper.creator = request.user
            content_object = getattr(self, 'content_object', None)
            paper.content_object = content_object
        paper.save()
        self.save_m2m()
        
        if new_paper:
            revision_number = 1
        else:
            revision_number = paper.current.revision + 1
        
        revision = PaperRevision.objects.create(
            paper = paper,
            revision = revision_number,
            editor = request.user,
            content = self.cleaned_data['content'],
            comment = self.cleaned_data['comment']
        )

        return paper, revision

class DeletePaperForm(forms.Form):
    delete = forms.ChoiceField(label=_('Delete'), choices=())

    def __init__(self, request, *args, **kwargs):
        '''
        Override the __init__ to display only delete choices the user has
        permission for.
        '''
        self.base_fields['delete'].choices = []
        if request.user.has_perm('papers.delete_revision'):
            self.base_fields['delete'].choices.append(('revision', _('Delete this revision')),)

        if request.user.has_perm('wakawaka.delete_revision') and \
           request.user.has_perm('wakawaka.delete_paper'):
            self.base_fields['delete'].choices.append(('paper', _('Delete the paper (and all revisions)')),)

        super(DeletePaperForm, self).__init__(*args, **kwargs)

    def _delete_paper(self, paper):
        paper.delete()

    def _delete_revision(self, revision):
        revision.delete()

    def delete_paper(self, request, paper, revision):
        """
        Deletes the paper with all revisions or the revision, based on the
        users choice.

        Returns a HttpResponseRedirect.
        """
        
        content_object = paper.content_object
        if content_object:
            paper_deletion_redirect = content_object.get_absolute_url()
        else:
            paper_deletion_redirect = reverse('headquarters')
        
        # Delete the paper
        if self.cleaned_data.get('delete') == 'paper' and \
           request.user.has_perm('papers.delete_revision') and \
           request.user.has_perm('papers.delete_paper'):
            self._delete_paper(paper)
            request.user.message_set.create(message=ugettext('The Paper %s was deleted' % paper.title))
            return HttpResponseRedirect(paper_deletion_redirect)

        # Revision handling
        if self.cleaned_data.get('delete') == 'revision':

            revision_length = len(paper.revisions.all())

            # Delete the revision if there are more than 1 and the user has permission
            if revision_length > 1 and request.user.has_perm('papers.delete_revision'):
                self._delete_revision(revision)
                request.user.message_set.create(message=ugettext('Revision #%d for %s was deleted' % (revision.revision_number, paper.title)))
                return HttpResponseRedirect(reverse('paper_history', kwargs={'slug': paper.slug}))

            # Do not allow deleting the revision, if it's the only one and the user
            # has no permisson to delete the paper.
            if revision_length <= 1 and \
               not request.user.has_perm('papers.delete_paper'):
                request.user.message_set.create(message=ugettext('You can not delete this revison for %s because it\'s the only one and you have no permission to delete the whole paper.' % paper.title))
                return HttpResponseRedirect(reverse('paper_history', kwargs={'slug': paper.slug}))

            # Delete the paper and the revision if the user has both permissions
            if revision_length <= 1 and \
               request.user.has_perm('papers.delete_revision') and \
               request.user.has_perm('papers.delete_paper'):
                self._delete_paper(paper)
                request.user.message_set.create(message=ugettext('The paper for %s was deleted because you deleted the only revision' % paper.title))
                return HttpResponseRedirect(paper_deletion_redirect)

        return None
