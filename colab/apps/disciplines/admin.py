from django.contrib import admin
from models import Discipline

class DisciplineAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Discipline, DisciplineAdmin)

