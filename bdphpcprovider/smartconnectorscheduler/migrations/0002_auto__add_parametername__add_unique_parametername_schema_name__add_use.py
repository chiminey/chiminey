# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
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
        ))
        db.send_create_signal('smartconnectorscheduler', ['ParameterName'])

        # Adding unique constraint on 'ParameterName', fields ['schema', 'name']
        db.create_unique('smartconnectorscheduler_parametername', ['schema_id', 'name'])

        # Adding model 'UserProfile'
        db.create_table('smartconnectorscheduler_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('company', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('nickname', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['UserProfile'])

        # Adding model 'Schema'
        db.create_table('smartconnectorscheduler_schema', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namespace', self.gf('django.db.models.fields.URLField')(max_length=400)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            ('name', self.gf('django.db.models.fields.SlugField')(default='', max_length=50)),
        ))
        db.send_create_signal('smartconnectorscheduler', ['Schema'])

        # Adding unique constraint on 'Schema', fields ['namespace', 'name']
        db.create_unique('smartconnectorscheduler_schema', ['namespace', 'name'])

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
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('smartconnectorscheduler', ['UserProfileParameter'])


    def backwards(self, orm):
        # Removing unique constraint on 'Schema', fields ['namespace', 'name']
        db.delete_unique('smartconnectorscheduler_schema', ['namespace', 'name'])

        # Removing unique constraint on 'ParameterName', fields ['schema', 'name']
        db.delete_unique('smartconnectorscheduler_parametername', ['schema_id', 'name'])

        # Deleting model 'ParameterName'
        db.delete_table('smartconnectorscheduler_parametername')

        # Deleting model 'UserProfile'
        db.delete_table('smartconnectorscheduler_userprofile')

        # Deleting model 'Schema'
        db.delete_table('smartconnectorscheduler_schema')

        # Deleting model 'UserProfileParameterSet'
        db.delete_table('smartconnectorscheduler_userprofileparameterset')

        # Deleting model 'UserProfileParameter'
        db.delete_table('smartconnectorscheduler_userprofileparameter')


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
        'smartconnectorscheduler.schema': {
            'Meta': {'unique_together': "(('namespace', 'name'),)", 'object_name': 'Schema'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'default': "''", 'max_length': '50'}),
            'namespace': ('django.db.models.fields.URLField', [], {'max_length': '400'})
        },
        'smartconnectorscheduler.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'company': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'smartconnectorscheduler.userprofileparameter': {
            'Meta': {'ordering': "('name',)", 'object_name': 'UserProfileParameter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.ParameterName']"}),
            'paramset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smartconnectorscheduler.UserProfileParameterSet']"}),
            'value': ('django.db.models.fields.TextField', [], {})
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