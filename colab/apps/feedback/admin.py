from django.contrib import admin
from feedback.models import Feedback, Status, Type

class SlugFieldAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}

admin.site.register(Feedback)
admin.site.register([Status, Type], SlugFieldAdmin)
