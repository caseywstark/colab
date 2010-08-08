from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("issues_invite", _("Invitation Received"), _("you have received an invitation"))
        notification.create_notice_type("object_feeds_update", _("Acitivity Feed Update"), _("someone updated an object you are following"))

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
