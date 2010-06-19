from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

class IssueAware(models.Model):
    """
    A mixin abstract base model to use on models you want to make issue-aware,
    as in they can be linked to issues.
    
    """
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    issue = generic.GenericForeignKey("content_type", "object_id")
    
    class Meta:
        abstract = True
