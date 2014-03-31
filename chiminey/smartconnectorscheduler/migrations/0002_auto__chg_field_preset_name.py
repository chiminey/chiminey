# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Preset.name'
        db.alter_column('smartconnectorscheduler_preset', 'name', self.gf('django.db.models.fields.CharField')(max_length=121))

    def backwards(self, orm):

        # Changing field 'Preset.name'
        db.alter_column('smartconnectorscheduler_preset', 'name', self.gf('django.db.models.fields.CharField')(max_length=256))

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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'stage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']", 'null': 'True', 'blank': 'True'})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '121'}),
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
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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