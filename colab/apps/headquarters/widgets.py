from django import forms
from django.template import loader, Context
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.forms.util import flatatt

from django.conf import settings

class WmdEditorWidget(forms.Textarea):
    def __init__(self, attrs=None, extra_id=None):
        self.extra_id = extra_id
        self.attrs = {'cols': '40', 'rows': '10'}
        if attrs:
            self.attrs.update(attrs)
    
    def render(self, name, value, attrs=None):
        # Prepare values
        if not value:
            value = ''
        attrs = self.build_attrs(attrs, name=name)
        
        # unique id
        widget_id = attrs['id']
        if self.extra_id:
            widget_id += str(self.extra_id)
            attrs['id'] = widget_id
            
        # Render widget to HTML
        t = loader.get_template('wmd/widget.html')
        c = Context({
            'attributes': flatatt(attrs),
            'value': conditional_escape(force_unicode(value)),
            'id': widget_id,
            'STATIC_URL': settings.STATIC_URL
        })

        return t.render(c)
 
    class Media:
        js = (
            settings.STATIC_URL + 'new-wmd/wmd.js',
        )
