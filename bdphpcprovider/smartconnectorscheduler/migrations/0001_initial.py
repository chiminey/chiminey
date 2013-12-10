# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserProfile'
        db.create_table('smartconnectorscheduler_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('company', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('nickname', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['UserProfile'])

        # Adding model 'Schema'
        db.create_table('smartconnectorscheduler_schema', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namespace', self.gf('django.db.models.fields.URLField')(max_length=400)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('name', self.gf('django.db.models.fields.SlugField')(default='', max_length=50)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Schema'])

        # Adding unique constraint on 'Schema', fields ['namespace', 'name']
        db.create_unique('smartconnectorscheduler_schema', ['namespace', 'name'])

        # Adding model 'ParameterName'
        db.create_table('smartconnectorscheduler_parametername', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('initial', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('choices', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('help_text', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('max_length', self.gf('django.db.models.fields.IntegerField')(default=255)),
            ('subtype', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('hidefield', self.gf('django.db.models.fields.URLField')(default='', max_length=400, null=True, blank=True)),
            ('hidecondition', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['ParameterName'])

        # Adding unique constraint on 'ParameterName', fields ['schema', 'name']
        db.create_unique('smartconnectorscheduler_parametername', ['schema_id', 'name'])

        # Adding model 'UserProfileParameterSet'
        db.create_table('smartconnectorscheduler_userprofileparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfile'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['UserProfileParameterSet'])

        # Adding model 'UserProfileParameter'
        db.create_table('smartconnectorscheduler_userprofileparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ParameterName'])),
            ('paramset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfileParameterSet'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['UserProfileParameter'])

        # Adding model 'Stage'
        db.create_table('smartconnectorscheduler_stage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('impl', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='')),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Stage'], null=True, blank=True)),
            ('package', self.gf('django.db.models.fields.CharField')(default='', max_length=256)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Stage'])

        # Adding model 'Platform'
        db.create_table('smartconnectorscheduler_platform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='nectar', max_length=256)),
            ('root_path', self.gf('django.db.models.fields.CharField')(default='/home/centos', max_length=512)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Platform'])

        # Adding model 'PlatformInstance'
        db.create_table('smartconnectorscheduler_platforminstance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfile'])),
            ('schema_namespace_prefix', self.gf('django.db.models.fields.CharField')(default='http://rmit.edu.au/schemas/platform', max_length=512)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PlatformInstance'])

        # Adding model 'PlatformInstanceParameterSet'
        db.create_table('smartconnectorscheduler_platforminstanceparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('platform', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.PlatformInstance'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PlatformInstanceParameterSet'])

        # Adding model 'PlatformInstanceParameter'
        db.create_table('smartconnectorscheduler_platforminstanceparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ParameterName'])),
            ('paramset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.PlatformInstanceParameterSet'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PlatformInstanceParameter'])

        # Adding model 'PlatformParameterSet'
        db.create_table('smartconnectorscheduler_platformparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfile'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PlatformParameterSet'])

        # Adding unique constraint on 'PlatformParameterSet', fields ['owner', 'name']
        db.create_unique('smartconnectorscheduler_platformparameterset', ['owner_id', 'name'])

        # Adding model 'PlatformParameter'
        db.create_table('smartconnectorscheduler_platformparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ParameterName'])),
            ('paramset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.PlatformParameterSet'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PlatformParameter'])

        # Adding model 'Directive'
        db.create_table('smartconnectorscheduler_directive', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Directive'])

        # Adding model 'Command'
        db.create_table('smartconnectorscheduler_command', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('directive', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Directive'])),
            ('stage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Stage'], null=True, blank=True)),
            ('platform', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Platform'])),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Command'])

        # Adding model 'DirectiveArgSet'
        db.create_table('smartconnectorscheduler_directiveargset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('directive', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Directive'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
        ))
        db.send_create_signal('smartconnectorscheduler', ['DirectiveArgSet'])

        # Adding model 'SmartConnector'
        db.create_table('smartconnectorscheduler_smartconnector', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('composite_stage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Stage'])),
        ))
        db.send_create_signal('smartconnectorscheduler', ['SmartConnector'])

        # Adding model 'Context'
        db.create_table('smartconnectorscheduler_context', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfile'])),
            ('current_stage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Stage'])),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('status', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('directive', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Directive'], null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Context'], null=True, blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Context'])

        # Adding model 'ContextMessage'
        db.create_table('smartconnectorscheduler_contextmessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('context', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Context'])),
            ('message', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['ContextMessage'])

        # Adding model 'ContextParameterSet'
        db.create_table('smartconnectorscheduler_contextparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('context', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Context'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['ContextParameterSet'])

        # Adding model 'CommandArgument'
        db.create_table('smartconnectorscheduler_commandargument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('template_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['CommandArgument'])

        # Adding model 'ContextParameter'
        db.create_table('smartconnectorscheduler_contextparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ParameterName'])),
            ('paramset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ContextParameterSet'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['ContextParameter'])

        # Adding model 'StageParameterSet'
        db.create_table('smartconnectorscheduler_stageparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Stage'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['StageParameterSet'])

        # Adding model 'StageParameter'
        db.create_table('smartconnectorscheduler_stageparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ParameterName'])),
            ('paramset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.StageParameterSet'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['StageParameter'])

        # Adding model 'Preset'
        db.create_table('smartconnectorscheduler_preset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('user_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfile'])),
            ('directive', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Directive'])),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Preset'])

        # Adding unique constraint on 'Preset', fields ['name', 'user_profile']
        db.create_unique('smartconnectorscheduler_preset', ['name', 'user_profile_id'])

        # Adding model 'PresetParameterSet'
        db.create_table('smartconnectorscheduler_presetparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('preset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Preset'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PresetParameterSet'])

        # Adding model 'PresetParameter'
        db.create_table('smartconnectorscheduler_presetparameter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ParameterName'])),
            ('paramset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.StageParameterSet'])),
            ('value', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['PresetParameter'])


    def backwards(self, orm):
        # Removing unique constraint on 'Preset', fields ['name', 'user_profile']
        db.delete_unique('smartconnectorscheduler_preset', ['name', 'user_profile_id'])

        # Removing unique constraint on 'PlatformParameterSet', fields ['owner', 'name']
        db.delete_unique('smartconnectorscheduler_platformparameterset', ['owner_id', 'name'])

        # Removing unique constraint on 'ParameterName', fields ['schema', 'name']
        db.delete_unique('smartconnectorscheduler_parametername', ['schema_id', 'name'])

        # Removing unique constraint on 'Schema', fields ['namespace', 'name']
        db.delete_unique('smartconnectorscheduler_schema', ['namespace', 'name'])

        # Deleting model 'UserProfile'
        db.delete_table('smartconnectorscheduler_userprofile')

        # Deleting model 'Schema'
        db.delete_table('smartconnectorscheduler_schema')

        # Deleting model 'ParameterName'
        db.delete_table('smartconnectorscheduler_parametername')

        # Deleting model 'UserProfileParameterSet'
        db.delete_table('smartconnectorscheduler_userprofileparameterset')

        # Deleting model 'UserProfileParameter'
        db.delete_table('smartconnectorscheduler_userprofileparameter')

        # Deleting model 'Stage'
        db.delete_table('smartconnectorscheduler_stage')

        # Deleting model 'Platform'
        db.delete_table('smartconnectorscheduler_platform')

        # Deleting model 'PlatformInstance'
        db.delete_table('smartconnectorscheduler_platforminstance')

        # Deleting model 'PlatformInstanceParameterSet'
        db.delete_table('smartconnectorscheduler_platforminstanceparameterset')

        # Deleting model 'PlatformInstanceParameter'
        db.delete_table('smartconnectorscheduler_platforminstanceparameter')

        # Deleting model 'PlatformParameterSet'
        db.delete_table('smartconnectorscheduler_platformparameterset')

        # Deleting model 'PlatformParameter'
        db.delete_table('smartconnectorscheduler_platformparameter')

        # Deleting model 'Directive'
        db.delete_table('smartconnectorscheduler_directive')

        # Deleting model 'Command'
        db.delete_table('smartconnectorscheduler_command')

        # Deleting model 'DirectiveArgSet'
        db.delete_table('smartconnectorscheduler_directiveargset')

        # Deleting model 'SmartConnector'
        db.delete_table('smartconnectorscheduler_smartconnector')

        # Deleting model 'Context'
        db.delete_table('smartconnectorscheduler_context')

        # Deleting model 'ContextMessage'
        db.delete_table('smartconnectorscheduler_contextmessage')

        # Deleting model 'ContextParameterSet'
        db.delete_table('smartconnectorscheduler_contextparameterset')

        # Deleting model 'CommandArgument'
        db.delete_table('smartconnectorscheduler_commandargument')

        # Deleting model 'ContextParameter'
        db.delete_table('smartconnectorscheduler_contextparameter')

        # Deleting model 'StageParameterSet'
        db.delete_table('smartconnectorscheduler_stageparameterset')

        # Deleting model 'StageParameter'
        db.delete_table('smartconnectorscheduler_stageparameter')

        # Deleting model 'Preset'
        db.delete_table('smartconnectorscheduler_preset')

        # Deleting model 'PresetParameterSet'
        db.delete_table('smartconnectorscheduler_presetparameterset')

        # Deleting model 'PresetParameter'
        db.delete_table('smartconnectorscheduler_presetparameter')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'smartconnectorscheduler.command': {
            'Meta': {'object_name': 'Command'},
            'directive': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Directive']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Platform']"}),
            'stage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']", 'null': 'True', 'blank': 'True'})
        },
        'smartconnectorscheduler.commandargument': {
            'Meta': {'object_name': 'CommandArgument'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'template_url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'smartconnectorscheduler.context': {
            'Meta': {'object_name': 'Context'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_stage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'directive': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Directive']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Context']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'smartconnectorscheduler.contextmessage': {
            'Meta': {'object_name': 'ContextMessage'},
            'context': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Context']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.contextparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ContextParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ContextParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.contextparameterset': {
            'Meta': {'ordering': "['-ranking']", 'object_name': 'ContextParameterSet'},
            'context': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Context']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.directive': {
            'Meta': {'object_name': 'Directive'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'smartconnectorscheduler.directiveargset': {
            'Meta': {'object_name': 'DirectiveArgSet'},
            'directive': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Directive']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.parametername': {
            'Meta': {'ordering': "['-ranking']", 'unique_together': "(('schema', 'name'),)", 'object_name': 'ParameterName'},
            'choices': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'help_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hidecondition': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hidefield': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'max_length': ('django.db.models.fields.IntegerField', [], {'default': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"}),
            'subtype': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'smartconnectorscheduler.platform': {
            'Meta': {'object_name': 'Platform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'nectar'", 'max_length': '256'}),
            'root_path': ('django.db.models.fields.CharField', [], {'default': "'/home/centos'", 'max_length': '512'})
        },
        'smartconnectorscheduler.platforminstance': {
            'Meta': {'object_name': 'PlatformInstance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"}),
            'schema_namespace_prefix': ('django.db.models.fields.CharField', [], {'default': "'http://rmit.edu.au/schemas/platform'", 'max_length': '512'})
        },
        'smartconnectorscheduler.platforminstanceparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'PlatformInstanceParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.PlatformInstanceParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.platforminstanceparameterset': {
            'Meta': {'ordering': "['-ranking']", 'object_name': 'PlatformInstanceParameterSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.PlatformInstance']"}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.platformparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'PlatformParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.PlatformParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.platformparameterset': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('owner', 'name'),)", 'object_name': 'PlatformParameterSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.preset': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('name', 'user_profile'),)", 'object_name': 'Preset'},
            'directive': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Directive']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"})
        },
        'smartconnectorscheduler.presetparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'PresetParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.PresetParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.presetparameterset': {
            'Meta': {'ordering': "('ranking',)", 'object_name': 'PresetParameterSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'preset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Preset']"}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.schema': {
            'Meta': {'unique_together': "(('namespace', 'name'),)", 'object_name': 'Schema'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'default': "''", 'max_length': '50'}),
            'namespace': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'smartconnectorscheduler.smartconnector': {
            'Meta': {'object_name': 'SmartConnector'},
            'composite_stage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'smartconnectorscheduler.stage': {
            'Meta': {'object_name': 'Stage'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impl': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'package': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']", 'null': 'True', 'blank': 'True'})
        },
        'smartconnectorscheduler.stageparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'StageParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.StageParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.stageparameterset': {
            'Meta': {'ordering': "['-ranking']", 'object_name': 'StageParameterSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"}),
            'stage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']"})
        },
        'smartconnectorscheduler.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'company': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'smartconnectorscheduler.userprofileparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'UserProfileParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfileParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'smartconnectorscheduler.userprofileparameterset': {
            'Meta': {'ordering': "['-ranking']", 'object_name': 'UserProfileParameterSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"})
        }
    }

    complete_apps = ['smartconnectorscheduler']
