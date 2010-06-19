from django.contrib import admin

from wikis.models import Wiki, ChangeSet

class InlineChangeSet(admin.TabularInline):
    model = ChangeSet
    extra = 0
    raw_id_fields = ('editor',)

class WikiAdmin(admin.ModelAdmin):
    list_display = ('title', 'created')
    list_filter = ('title',)
    ordering = ('last_update',)
    fieldsets = (
        (None, {'fields': ('title', 'content')}),
        ('Creator', {'fields': ('creator',),
                     'classes': ('collapse', 'wide')}),
    )
    raw_id_fields = ('creator',)
    inlines = [InlineChangeSet]

admin.site.register(Wiki, WikiAdmin)


class ChangeSetAdmin(admin.ModelAdmin):
    list_display = ('wiki', 'revision', 'old_title', 'editor', 'reverted',
                    'modified', 'comment')
    list_filter = ('old_title', 'content_diff')
    ordering = ('modified',)
    fieldsets = (
        ('Wiki', {'fields': ('wiki',)}),
        ('Differences', {'fields': ('old_title', 'content_diff')}),
        ('Other', {'fields': ('comment', 'modified', 'revision', 'reverted'),
                   'classes': ('collapse', 'wide')}),
        ('Editor', {'fields': ('editor',),
                    'classes': ('collapse', 'wide')}),
    )
    raw_id_fields = ('editor',)

admin.site.register(ChangeSet, ChangeSetAdmin)

