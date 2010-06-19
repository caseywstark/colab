from django import forms
from django.utils.translation import ugettext_lazy as _

from people.models import Researcher
from tinymce.widgets import TinyMCE

class ResearcherForm(forms.ModelForm):
    
    about = forms.CharField(label=_("about"), widget=TinyMCE)
    
    class Meta:
        model = Researcher
        fields = [
            "name",
            "about",
            "website",
            "expertise",
            "default_filter",
            "research_interests",
            "occupation",
        ]
