from django import forms
from django.forms import widgets
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from wikis.models import Wiki
from headquarters.widgets import WmdEditorWidget

class WikiForm(forms.ModelForm):
    
    title = forms.CharField(required=True, max_length=255)
    content = forms.CharField(widget=WmdEditorWidget())
    comment = forms.CharField(required=False, max_length=255)
    
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        required=False,
        widget=forms.HiddenInput)
    object_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Wiki
        fields = ['wiki_type', 'title', 'content', 'tags', 'content_type', 'object_id']
    
    def __init__(self, *args, **kwargs):
        self.wiki_type = kwargs.pop('wiki_type', None)
        super(WikiForm, self).__init__(*args, **kwargs)
        
        self.fields["wiki_type"].widget = forms.HiddenInput()

    def save(self):
        # 1 - Get the old stuff before saving
        if self.instance.id is None:
            old_title = old_content = ''
            new = True
        else:
            old_title = self.instance.title
            old_content = self.instance.content
            new = False
        comment = self.cleaned_data["comment"]

        # 2 - Save the page
        wiki = super(WikiForm, self).save()

        # 3 - Set creator and group
        editor = getattr(self, 'editor', None)
        content_object = getattr(self, 'content_object', None)
        if new:
            if editor is not None:
                wiki.creator = editor
                wiki.content_object = content_object
            wiki.save()

        # 4 - Create new revision
        changeset = wiki.new_revision(old_content, old_title, comment, editor)

        return wiki, changeset
class PaperForm(WikiForm):
    def __init__(self, *args, **kwargs):
        super(PaperForm, self).__init__(*args, **kwargs)
        self.initial = {"wiki_type": "PR"}

class PageForm(WikiForm):
    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        self.initial = {"wiki_type": "PG"}

class SummaryForm(WikiForm):
    def __init__(self, *args, **kwargs):
        super(SummaryForm, self).__init__(*args, **kwargs)
        self.initial = {"wiki_type": "SM"}
        self.fields["title"].widget = forms.HiddenInput()
