from django import forms
from django.utils.translation import ugettext_lazy as _

from feedback.models import Feedback
from tinymce.widgets import TinyMCE

class FeedbackForm(forms.ModelForm):
    
    description = forms.CharField(label=_("description"), widget=TinyMCE)
    
    class Meta:
        model = Feedback
        fields = ('user', 'type', 'title', 'description', 'anonymous', 'private', 'page', 'page_specific')
        
    def __init__(self, *args, **kwargs):
        super(FeedbackForm, self).__init__(*args, **kwargs)
        self.fields['user'].widget = forms.HiddenInput()

class WidgetForm(forms.ModelForm):
    
    class Meta:
        model = Feedback
        fields = ('user', 'type', 'title', 'description', 'anonymous', 'private', 'page', 'page_specific')
    
    def __init__(self, *args, **kwargs):
        super(WidgetForm, self).__init__(*args, **kwargs)
        self.fields['user'].widget = forms.HiddenInput()
        self.fields['page'].widget = forms.HiddenInput()


