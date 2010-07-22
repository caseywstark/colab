from django import forms
from django.forms import widgets
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from summaries.models import Summary, SummaryRevision
from tinymce.widgets import TinyMCE

class SummaryForm(forms.ModelForm):
    
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        required=False, widget=forms.HiddenInput)
    object_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    
    # extra SummaryRevsion fields
    content = forms.CharField(widget=TinyMCE)
    comment = forms.CharField(label=_('Change comment (optional)'), required=False, max_length=255)

    class Meta:
        model = Summary
        fields = ['title', 'tags', 'content_type', 'object_id']
    
    def __init__(self, *args, **kwargs):
        super(SummaryForm, self).__init__(*args, **kwargs)

    def save(self, request, *args, **kwargs):
        
        kwargs["commit"] = False # this is hacky, but we don't want to commit the summary so we can modify creator and last_editor
        
        # if the summary is new, add the creator
        new_summary = False
        if not self.instance.id:
            new_summary = True
            
        summary = super(SummaryForm, self).save(*args, **kwargs)
        summary.last_editor = request.user
        if new_summary:
            summary.creator = request.user
            content_object = getattr(self, 'content_object', None)
            summary.content_object = content_object
        summary.save()
        self.save_m2m()
        
        if new_summary:
            revision_number = 1
        else:
            revision_number = summary.current.revision + 1
        
        revision = SummaryRevision.objects.create(
            summary = summary,
            revision = revision_number,
            editor = request.user,
            content = self.cleaned_data['content'],
            comment = self.cleaned_data['comment']
        )

        return summary, revision
        
class DeleteSummaryForm(forms.Form):
    delete = forms.ChoiceField(label=_('Delete'), choices=())

    def __init__(self, request, *args, **kwargs):
        '''
        Override the __init__ to display only delete choices the user has
        permission for.
        '''
        self.base_fields['delete'].choices = []
        if request.user.has_perm('summaries.delete_revision'):
            self.base_fields['delete'].choices.append(('revision', _('Delete this revision')),)

        if request.user.has_perm('wakawaka.delete_revision') and \
           request.user.has_perm('wakawaka.delete_summary'):
            self.base_fields['delete'].choices.append(('summary', _('Delete the summary (and all revisions)')),)

        super(DeleteSummaryForm, self).__init__(*args, **kwargs)

    def _delete_summary(self, summary):
        summary.delete()

    def _delete_revision(self, revision):
        revision.delete()

    def delete_summary(self, request, summary, revision):
        """
        Deletes the summary with all revisions or the revision, based on the
        users choice.

        Returns a HttpResponseRedirect.
        """
        
        content_object = summary.content_object
        if content_object:
            summary_deletion_redirect = content_object.get_absolute_url()
        else:
            summary_deletion_redirect = reverse('headquarters')
        
        # Delete the summary
        if self.cleaned_data.get('delete') == 'summary' and \
           request.user.has_perm('summaries.delete_revision') and \
           request.user.has_perm('summaries.delete_summary'):
            self._delete_summary(summary)
            request.user.message_set.create(message=ugettext('The Summary %s was deleted' % summary.title))
            return HttpResponseRedirect(summary_deletion_redirect)

        # Revision handling
        if self.cleaned_data.get('delete') == 'revision':

            revision_length = len(summary.revisions.all())

            # Delete the revision if there are more than 1 and the user has permission
            if revision_length > 1 and request.user.has_perm('summaries.delete_revision'):
                self._delete_revision(revision)
                request.user.message_set.create(message=ugettext('Revision #%d for %s was deleted' % (revision.revision_number, summary.title)))
                return HttpResponseRedirect(reverse('summary_history', kwargs={'slug': summary.slug}))

            # Do not allow deleting the revision, if it's the only one and the user
            # has no permisson to delete the summary.
            if revision_length <= 1 and \
               not request.user.has_perm('summaries.delete_summary'):
                request.user.message_set.create(message=ugettext('You can not delete this revison for %s because it\'s the only one and you have no permission to delete the whole summary.' % summary.title))
                return HttpResponseRedirect(reverse('summary_history', kwargs={'slug': summary.slug}))

            # Delete the summary and the revision if the user has both permissions
            if revision_length <= 1 and \
               request.user.has_perm('summaries.delete_revision') and \
               request.user.has_perm('summaries.delete_summary'):
                self._delete_summary(summary)
                request.user.message_set.create(message=ugettext('The summary for %s was deleted because you deleted the only revision' % summary.title))
                return HttpResponseRedirect(summary_deletion_redirect)

        return None
