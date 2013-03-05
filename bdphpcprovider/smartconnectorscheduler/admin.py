from django.contrib import admin
from bdphpcprovider.smartconnectorscheduler import models


class ParameterNameInline(admin.TabularInline):
    model = models.ParameterName
    extra = 0

class SchemaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'namespace']
    inlines = [ParameterNameInline]

admin.site.register(models.UserProfile)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ParameterName)
admin.site.register(models.UserProfileParameterSet)
admin.site.register(models.UserProfileParameter)
admin.site.register(models.Stage)

