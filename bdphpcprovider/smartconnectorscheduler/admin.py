# Copyright (C) 2013, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
from tastypie.admin import ApiKeyInline

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin

from bdphpcprovider.smartconnectorscheduler import models


class ParameterNameInline(admin.TabularInline):
    model = models.ParameterName
    extra = 0


class SchemaAdmin(admin.ModelAdmin):
    search_fields = ['name', 'namespace']
    list_display = ['namespace', 'name', 'description']
    inlines = [ParameterNameInline]
    ordering = ('namespace', 'name')


class DirectiveArgSetInline(admin.TabularInline):
    model = models.DirectiveArgSet
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class DirectiveAdmin(admin.ModelAdmin):
    inlines = [DirectiveArgSetInline]


class ContextParameterInline(admin.TabularInline):
    model = models.ContextParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class ContextParameterSetAdmin(admin.ModelAdmin):
    inlines = [ContextParameterInline]
    list_display = ('context_owner', 'context_name', 'schema', )

    def context_name(self, obj):
        return obj.schema.name

    def context_owner(self, obj):
        return obj.context.owner


class PlatformInstanceParameterInline(admin.TabularInline):
    model = models.PlatformInstanceParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class PlatformInstanceParameterSetAdmin(admin.ModelAdmin):
    inlines = [PlatformInstanceParameterInline]
    list_display = ('owner', 'schema_prefix', 'schema', )

    def name(self, obj):
        return obj.schema.name

    def schema_prefix(self, obj):
        return obj.platform.schema_namespace_prefix

    def owner(self, obj):
        return obj.platform.owner


class PlatformParameterInline(admin.TabularInline):
    model = models.PlatformParameter
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class PlatformParameterSetAdmin(admin.ModelAdmin):
    inlines = [PlatformParameterInline]
    list_display = ('name', 'owner', 'schema', )

    def name(self, obj):
        return obj.name

    def schema(self, obj):
        return obj.schema.namespace

    def owner(self, obj):
        return obj.owner


class DirectiveArgSetAdmin(admin.ModelAdmin):
    list_display = ('directive', 'schema')


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

    list_display = ('owner', 'curr_stage', 'deleted', 'directive')

    def curr_stage(self, obj):
        return "#%s %s" % (obj.current_stage.id, obj.current_stage.name)

    def directive(self, obj):
        return "#%s %s" % (obj.directive.id, obj.directive.name)


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

#         return queryset.filter(id=stage__parent).order_by('id')


class StageInline(admin.TabularInline):
    model = models.StageParameterSet
    extra = 0
    # formfield_overrides = {
    #   django.db.models.TextField: {'widget': TextInput},
    # }


class StageAdmin(admin.ModelAdmin):
    model = models.Stage
    list_display = ('id', 'name', 'description', 'parent_name', 'package')
    list_display_links = ('name',)
    # list_filter = ('ParentListFilter',)
    list_filter = ('parent',)
    ordering = ('id','parent', 'order')
    inlines = (StageInline,)

    def parent_name(self, obj):
        return "#%s %s" % (obj.parent.id, obj.parent.name)


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
    ordering = ('company', 'user')
    inlines = (UserProfileParameterSetInline,)


#TODO: add timestamp to messages to allow auditing
class ContextMessageAdmin(admin.ModelAdmin):
    model = models.ContextMessage
    list_display = ('context_out', 'message_out')
    # list_display_links = ('context',)
    # list_filter = ('',)
    ordering = ('message', 'context')
    # inlines = (UserProfileParameterSetInline,)


    def context_out(self, obj):
        return obj.context.id

    def message_out(self, obj):
        return obj.message


class PresetParameterInline(admin.TabularInline):
    model = models.PresetParameter
    extra = 0


class PresetParameterSetAdmin(admin.ModelAdmin):
    inlines = [PresetParameterInline]
    # list_display = ('preset', 'schema')


#admin.site.register(ApiKey)
#admin.site.register(ApiAccess)

class UserModelAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [ApiKeyInline]

admin.site.unregister(User)
admin.site.register(User, UserModelAdmin)
admin.site.register(models.UserProfile, UserProfileAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ParameterName)
admin.site.register(models.UserProfileParameterSet, UserProfileParameterSetAdmin)
admin.site.register(models.UserProfileParameter)
admin.site.register(models.Platform)
admin.site.register(models.Stage, StageAdmin)
admin.site.register(models.Context, ContextAdmin)
admin.site.register(models.ContextMessage, ContextMessageAdmin)
admin.site.register(models.ContextParameterSet, ContextParameterSetAdmin)
admin.site.register(models.ContextParameter)
admin.site.register(models.StageParameterSet, StageParameterSetAdmin)
admin.site.register(models.StageParameter)
admin.site.register(models.Directive, DirectiveAdmin)
admin.site.register(models.DirectiveArgSet, DirectiveArgSetAdmin)
admin.site.register(models.PlatformInstance)
admin.site.register(models.PlatformInstanceParameterSet, PlatformInstanceParameterSetAdmin)
admin.site.register(models.PlatformInstanceParameter)
admin.site.register(models.PlatformParameterSet, PlatformParameterSetAdmin)
admin.site.register(models.PlatformParameter)
admin.site.register(models.Preset)
admin.site.register(models.PresetParameterSet, PresetParameterSetAdmin)
admin.site.register(models.PresetParameter)
