from django.contrib import admin
from issues.models import Issue

class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'created')

admin.site.register(Issue, IssueAdmin)
