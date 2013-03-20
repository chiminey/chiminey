from django.contrib import admin
from bdphpcprovider.smartconnectorscheduler import models


class ParameterNameInline(admin.TabularInline):
    model = models.ParameterName
    extra = 0


class SchemaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'namespace']
    inlines = [ParameterNameInline]


class ContextParameterInline(admin.TabularInline):
    model = models.ContextParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class ContextParameterSetAdmin(admin.ModelAdmin):
    inlines = [ContextParameterInline]


class UserProfileParameterInline(admin.TabularInline):
    model = models.UserProfileParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class UserProfileParameterSetAdmin(admin.ModelAdmin):
    inlines = [UserProfileParameterInline]


admin.site.register(models.UserProfile)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ParameterName)
admin.site.register(models.UserProfileParameterSet, UserProfileParameterSetAdmin)
admin.site.register(models.UserProfileParameter)
admin.site.register(models.Platform)
admin.site.register(models.Stage)
admin.site.register(models.Context)
admin.site.register(models.ContextParameterSet, ContextParameterSetAdmin)
admin.site.register(models.ContextParameter)


