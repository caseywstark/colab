from django import forms
from django.utils.translation import ugettext_lazy as _

from threadedcomments.models import ThreadedComment

from headquarters.widgets import WmdEditorWidget

class WmdCommentForm(forms.ModelForm):
    
    comment = forms.CharField(label=_("Comment"))
    
    def __init__(self, *args, **kwargs):
        self.extra_id = kwargs.pop('extra_id', None)
        super(WmdCommentForm, self).__init__(*args, **kwargs)
        
        self.fields['comment'].widget = WmdEditorWidget(extra_id=self.extra_id)
    
    class Meta:
        model = ThreadedComment
        fields = ('comment',)
