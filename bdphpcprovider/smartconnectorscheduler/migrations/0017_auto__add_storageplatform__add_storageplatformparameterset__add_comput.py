# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StoragePlatform'
        db.create_table('smartconnectorscheduler_storageplatform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.UserProfile'])),
            ('schema_namespace_prefix', self.gf('django.db.models.fields.CharField')(default='http://rmit.edu.au/schemas/platform/storage', max_length=512)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['StoragePlatform'])

        # Adding model 'StoragePlatformParameterSet'
        db.create_table('smartconnectorscheduler_storageplatformparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('computation_platform', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.StoragePlatform'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['StoragePlatformParameterSet'])

        # Adding model 'ComputationPlatformParameterSet'
        db.create_table('smartconnectorscheduler_computationplatformparameterset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('computation_platform', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.ComputationPlatform'])),
            ('schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['smartconnectorscheduler.Schema'])),
            ('ranking', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['ComputationPlatformParameterSet'])

        # Deleting field 'ComputationPlatform.username'
        db.delete_column('smartconnectorscheduler_computationplatform', 'username')

        # Deleting field 'ComputationPlatform.root_path'
        db.delete_column('smartconnectorscheduler_computationplatform', 'root_path')

        # Deleting field 'ComputationPlatform.type'
        db.delete_column('smartconnectorscheduler_computationplatform', 'type')

        # Deleting field 'ComputationPlatform.password'
        db.delete_column('smartconnectorscheduler_computationplatform', 'password')

        # Deleting field 'ComputationPlatform.ip_address'
        db.delete_column('smartconnectorscheduler_computationplatform', 'ip_address')

        # Deleting field 'ComputationPlatform.private_key_name'
        db.delete_column('smartconnectorscheduler_computationplatform', 'private_key_name')

        # Adding field 'ComputationPlatform.schema_namespace_prefix'
        db.add_column('smartconnectorscheduler_computationplatform', 'schema_namespace_prefix',
                      self.gf('django.db.models.fields.CharField')(default='http://rmit.edu.au/schemas/platform/computation', max_length=512),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'StoragePlatform'
        db.delete_table('smartconnectorscheduler_storageplatform')

        # Deleting model 'StoragePlatformParameterSet'
        db.delete_table('smartconnectorscheduler_storageplatformparameterset')

        # Deleting model 'ComputationPlatformParameterSet'
        db.delete_table('smartconnectorscheduler_computationplatformparameterset')

        # Adding field 'ComputationPlatform.username'
        db.add_column('smartconnectorscheduler_computationplatform', 'username',
                      self.gf('django.db.models.fields.CharField')(default='iman', max_length=50),
                      keep_default=False)

        # Adding field 'ComputationPlatform.root_path'
        db.add_column('smartconnectorscheduler_computationplatform', 'root_path',
                      self.gf('django.db.models.fields.CharField')(default='path', max_length=512),
                      keep_default=False)

        # Adding field 'ComputationPlatform.type'
        db.add_column('smartconnectorscheduler_computationplatform', 'type',
                      self.gf('django.db.models.fields.CharField')(default='nectar', max_length=256),
                      keep_default=False)

        # Adding field 'ComputationPlatform.password'
        db.add_column('smartconnectorscheduler_computationplatform', 'password',
                      self.gf('django.db.models.fields.CharField')(default='e', max_length=50),
                      keep_default=False)

        # Adding field 'ComputationPlatform.ip_address'
        db.add_column('smartconnectorscheduler_computationplatform', 'ip_address',
                      self.gf('django.db.models.fields.CharField')(default='123', max_length=50),
                      keep_default=False)

        # Adding field 'ComputationPlatform.private_key_name'
        db.add_column('smartconnectorscheduler_computationplatform', 'private_key_name',
                      self.gf('django.db.models.fields.CharField')(default='private', max_length=50),
                      keep_default=False)

        # Deleting field 'ComputationPlatform.schema_namespace_prefix'
        db.delete_column('smartconnectorscheduler_computationplatform', 'schema_namespace_prefix')


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
        'smartconnectorscheduler.computationplatform': {
            'Meta': {'object_name': 'ComputationPlatform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"}),
            'schema_namespace_prefix': ('django.db.models.fields.CharField', [], {'default': "'http://rmit.edu.au/schemas/platform/computation'", 'max_length': '512'})
        },
        'smartconnectorscheduler.computationplatformparameterset': {
            'Meta': {'ordering': "['-ranking']", 'object_name': 'ComputationPlatformParameterSet'},
            'computation_platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ComputationPlatform']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.context': {
            'Meta': {'object_name': 'Context'},
            'current_stage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"})
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'smartconnectorscheduler.directiveargset': {
            'Meta': {'object_name': 'DirectiveArgSet'},
            'directive': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Stage']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
        },
        'smartconnectorscheduler.parametername': {
            'Meta': {'ordering': "['-ranking']", 'unique_together': "(('schema', 'name'),)", 'object_name': 'ParameterName'},
            'choices': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'help_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'max_length': ('django.db.models.fields.IntegerField', [], {'default': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'smartconnectorscheduler.platform': {
            'Meta': {'object_name': 'Platform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'nectar'", 'max_length': '256'}),
            'root_path': ('django.db.models.fields.CharField', [], {'default': "'/home/centos'", 'max_length': '512'})
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
        'smartconnectorscheduler.storageplatform': {
            'Meta': {'object_name': 'StoragePlatform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfile']"}),
            'schema_namespace_prefix': ('django.db.models.fields.CharField', [], {'default': "'http://rmit.edu.au/schemas/platform/storage'", 'max_length': '512'})
        },
        'smartconnectorscheduler.storageplatformparameterset': {
            'Meta': {'ordering': "['-ranking']", 'object_name': 'StoragePlatformParameterSet'},
            'computation_platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.StoragePlatform']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranking': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.Schema']"})
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