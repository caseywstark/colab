from django import forms
from threadedcomments.models import DEFAULT_MAX_COMMENT_LENGTH
from threadedcomments.models import FreeThreadedComment, ThreadedComment
from django.utils.translation import ugettext_lazy as _

from tinymce.widgets import TinyMCE

class RichCommentForm(forms.ModelForm):
    """
    Form for ThreadedComments that employs TinyMCE for rich text editing.
    
    """
    
    comment = forms.CharField(label=_("comment"), widget=TinyMCE)
    
    class Meta:
        model = ThreadedComment
        fields = ('comment',)

class ThreadedCommentForm(forms.ModelForm):
    """
    Form which can be used to validate data for a new ThreadedComment.
    It consists of just two fields: ``comment``, and ``markup``.
    
    The ``comment`` field is the only one which is required.
    """

    comment = forms.CharField(
        label = _('comment'),
        max_length = DEFAULT_MAX_COMMENT_LENGTH,
        widget = forms.Textarea
    )

    class Meta:
        model = ThreadedComment
        fields = ('comment', 'markup')

class FreeThreadedCommentForm(forms.ModelForm):
    """
    Form which can be used to validate data for a new FreeThreadedComment.
    It consists of just a few fields: ``comment``, ``name``, ``website``,
    ``email``, and ``markup``.
    
    The fields ``comment``, and ``name`` are the only ones which are required.
    """

    comment = forms.CharField(
        label = _('comment'),
        max_length = DEFAULT_MAX_COMMENT_LENGTH,
        widget = forms.Textarea
    )

    class Meta:
        model = FreeThreadedComment
        fields = ('comment', 'name', 'website', 'email', 'markup')
