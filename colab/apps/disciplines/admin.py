from django.contrib import admin
from models import Discipline, ResearchInterest

class DisciplineAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(ResearchInterest)

