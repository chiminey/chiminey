from django.contrib import admin
from bdphpcprovider.smartconnectorscheduler import models


class ParameterNameInline(admin.TabularInline):
    model = models.ParameterName
    extra = 0


class SchemaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'namespace']
    list_display = ['namespace', 'name', 'description']
    inlines = [ParameterNameInline]
    ordering = ('namespace','name')


class ContextParameterInline(admin.TabularInline):
    model = models.ContextParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class ContextParameterSetAdmin(admin.ModelAdmin):
    inlines = [ContextParameterInline]
    list_display = ('context', 'schema')



class UserProfileParameterInline(admin.TabularInline):
    model = models.UserProfileParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class UserProfileParameterSetAdmin(admin.ModelAdmin):
    inlines = [UserProfileParameterInline]
    list_display = ('user_profile', 'schema')





class StageParameterInline(admin.TabularInline):
    model = models.StageParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class StageParameterSetAdmin(admin.ModelAdmin):
    inlines = [StageParameterInline]



class ContextAdmin(admin.ModelAdmin):
    model = models.Context
    list_display = ('owner', 'current_stage')


# from datetime import date

# from django.utils.translation import ugettext_lazy as _
# from django.contrib.admin import SimpleListFilter


# class ParentListFilter(SimpleListFilter):
#      # Human-readable title which will be displayed in the
#      # right admin sidebar just above the filter options.
#     title = _('parent')

#      # Parameter for the filter that will be used in the URL query.
#     parameter_name = 'stage__parent'

#      # def lookups(self, request, model_admin):
#      #     """
#      #     Returns a list of tuples. The first element in each
#      #     tuple is the coded value for the option that will
#      #     appear in the URL query. The second element is the
#      #     human-readable name for the option that will appear
#      #     in the right sidebar.
#      #     """
#      #     return (
#      #         ('80s', _('in the eighties')),
#      #         ('90s', _('in the nineties')),
#      #     )

#     def queryset(self, request, queryset):
#         """
#          Returns the filtered queryset based on the value
#          provided in the query string and retrievable via
#         `self.value()`.
#         """
#         # Compare the requested value (either '80s' or '90s')
#         # to decide how to filter the queryset.

#         return queryset.filter(id=parent)



class StageInline(admin.TabularInline):
    model = models.StageParameterSet
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class StageAdmin(admin.ModelAdmin):
    model = models.Stage
    list_display = ('name', 'description', 'parent_name', 'package')
    list_display_links = ('name',)
    #list_filter = ('ParentListFilter',)
    list_filter = ('parent',)
    ordering= ('parent', 'order')
    inlines = (StageInline,)

    def parent_name(self, obj):
      return obj.parent.name



class UserProfileParameterSetInline(admin.TabularInline):
    model = models.UserProfileParameterSet
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }

class UserProfileAdmin(admin.ModelAdmin):
    model = models.UserProfile
    list_display = ('user', 'company', 'nickname')
    list_display_links = ('user',)
    list_filter = ('company',)
    ordering= ('company', 'user')
    inlines = (UserProfileParameterSetInline,)





admin.site.register(models.UserProfile, UserProfileAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ParameterName)
admin.site.register(models.UserProfileParameterSet, UserProfileParameterSetAdmin)
#admin.site.register(models.UserProfileParameter)
admin.site.register(models.Platform)
admin.site.register(models.Stage, StageAdmin)
admin.site.register(models.Context, ContextAdmin)
admin.site.register(models.ContextParameterSet, ContextParameterSetAdmin)
admin.site.register(models.ContextParameter)
admin.site.register(models.StageParameterSet, StageParameterSetAdmin)
admin.site.register(models.Command)
admin.site.register(models.Directive)

