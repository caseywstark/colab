from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from ajax_select.fields import AutoCompleteSelectMultipleField
from tinymce.widgets import TinyMCE

from issues.models import Issue, IssueContributor
from disciplines.models import Discipline
from people.models import Researcher
from tinymce.widgets import TinyMCE

class IssueForm(forms.ModelForm):
    
    title = forms.CharField(label=_("Title"), max_length=255)
    slug = forms.SlugField(max_length=20,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
    )
    description = forms.CharField(widget=TinyMCE)
    disciplines = AutoCompleteSelectMultipleField('discipline', required=False)
    
    def clean_title(self):
        if not self.instance.id and Issue.objects.filter(title__iexact=self.cleaned_data["title"]).exists():
            raise forms.ValidationError(_("An issue already exists with that title."))
        return self.cleaned_data["title"]
    
    def clean_slug(self):
        if not self.instance.id and Issue.objects.filter(slug__iexact=self.cleaned_data["slug"]).exists():
            raise forms.ValidationError(_("An issue already exists with that slug."))
        return self.cleaned_data["slug"].lower()
    
    def __init__(self, *args, **kwargs):
        super(IssueForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['title', 'slug', 'disciplines', 'tags', 'description', 'private']
    
    class Meta:
        model = Issue
        fields = ['title', 'slug', 'tags', 'description', 'disciplines', 'private']

class InviteContributorForm(forms.Form):
    
    recipients = AutoCompleteSelectMultipleField('researcher', required=True)
    
    def __init__(self, *args, **kwargs):
        self.issue = kwargs.pop("issue")
        super(InviteContributorForm, self).__init__(*args, **kwargs)
    
    def save(self):
        recipient_ids = self.cleaned_data["recipients"]
        recipients = Researcher.objects.filter(id__in=recipient_ids)
        for researcher in recipients:
            IssueContributor.objects.get_or_create(issue=self.issue, user=researcher.user)
        
        return recipients

class ResolutionForm(forms.Form):
    
    resolution = forms.ModelChoiceField(queryset=None, empty_label=None)
    
    def __init__(self, *args, **kwargs):
        self.issue = kwargs.pop("issue")
        super(ResolutionForm, self).__init__(*args, **kwargs)
        
        self.fields['resolution'].queryset = self.issue.papers
    
    def save(self):
        resolution = self.issue.resolve(self.cleaned_data['resolution'])
        return resolution

