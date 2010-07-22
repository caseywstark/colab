from django.contrib import admin

from papers.models import Paper, PaperRevision

admin.site.register(Paper)
admin.site.register(PaperRevision)
