from django.contrib import admin

from summaries.models import Summary, SummaryRevision

admin.site.register(Summary)
admin.site.register(SummaryRevision)
