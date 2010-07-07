from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

register = template.Library()

### Constructs the paper_create url for any object ###
@register.simple_tag
def add_paper_url(content_object):
    kwargs = {
        'content_type' : ContentType.objects.get_for_model(content_object).id,
        'object_id' : getattr(content_object, 'pk', getattr(content_object, 'id')),
    }
    return reverse('paper_create', kwargs=kwargs)
    
    
