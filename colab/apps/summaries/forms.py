from django import forms
from django.forms import widgets
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from summaries.models import Summary
from tinymce.widgets import TinyMCE

class SummaryForm(forms.ModelForm):
    
    content = forms.CharField(widget=TinyMCE)
    comment = forms.CharField(required=False, max_length=255)
    
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        required=False, widget=forms.HiddenInput)
    object_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Summary
        fields = ['summarized', 'content', 'tags', 'content_type', 'object_id']
    
    def __init__(self, *args, **kwargs):
        super(SummaryForm, self).__init__(*args, **kwargs)
        
        #self.fields['summarized'].widget = forms.CheckboxSelectMultiple()

    def save(self):
        # 1 - Get the old stuff before saving
        if self.instance.id is None:
            old_content = ''
            new = True
        else:
            old_content = self.instance.content
            new = False
        comment = self.cleaned_data["comment"]

        # 2 - Save the page
        summary = super(SummaryForm, self).save(commit=False)

        # 3 - Set creator and group
        editor = getattr(self, 'editor', None)
        content_object = getattr(self, 'content_object', None)
        if new:
            summary.content_object = content_object
            if editor is not None:
                summary.creator = editor
                summary.last_editor = editor
        
        summary.save()
        self.save_m2m()

        # 4 - Create new revision
        revision = summary.new_revision(old_content, comment, editor)

        return summary, revision
