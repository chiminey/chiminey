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

import os.path

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import ObjectDoesNotExist

from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler.platform import \
    retrieve_platform_paramsets, create_platform_paramset, delete_platform_paramsets
from bdphpcprovider.smartconnectorscheduler.storage import RemoteStorage, get_bdp_root_path
from bdphpcprovider.sshconnection import open_connection
from bdphpcprovider.compute import run_command_with_status


class Command(BaseCommand):
    args = 'i'
    help = 'Fires one run_contexts task (for debugging without celerybeat'
    namespace = 'http://rmit.edu.au/schemas/platform/computation/nci'

    def handle(self, *args, **kwargs):
        #from celery.task.control import discard_all
        #discard_all()

        #contexts = models.Context.objects.all()
        #for context in contexts:
        #    context.deleted = True
        #    context.save()

        #fixme: if http request is made, then
        #fixme bdp_username=request.user.username
        bdp_username = 'seid'
        interactive = False
        print kwargs
        if len(args) > 0:
            if args[0] == 'i':
                interactive = True
        if interactive:
            type = self.collect_data('type', validate=True)
            ip_address = self.collect_data('ip_address', validate=True)
            root_path = self.collect_data('root_path', validate=True)
            username = self.collect_data('username', validate=True)
            password = self.collect_data('password')
            private_key_name = self.collect_data('private_key_name')

        else:
            type = 'nectar'
            ip_address = '127.0.0.1'
            root_path = '/home/centos'
            username = 'centos'
            password = ''
            private_key_name = 'nectar_key'
        platform_settings = {
            'type': type,
            'ip_address': ip_address,
            'root_path': root_path,
            'username': username,
            'password': password,
            'private_key_name': private_key_name
        }
        self.update_platform()
        #self.create_platform_old(
        #    bdp_username, platform_settings)
        filter_list= {'username': 'nci2'}
        #self.retrieve_platform(bdp_username, filter_list)

    def collect_data(self, parameter, validate=False):
        validated = False
        while not validated:
            data = raw_input("Enter %s: " % parameter)
            if validate and data:
                validated = True
            elif not validate:
                validated = True
        return data

    def retrieve_all_platforms(self):
        username = 'seid'
        name = 'nectar_home_test'
        schema_namespace_prefix = 'http://rmit.edu.au/schemas/platform/computation/nectsfa'
        platforms = []
        try:
            user = User.objects.get(username=username)
            owner = models.UserProfile.objects.get(user=user)
            if not schema_namespace_prefix:
                paramsets = models.PlatformParameterSet.objects.filter(owner=owner)
            else:
                schema = models.Schema.objects.get(namespace__startswith=schema_namespace_prefix)
                paramsets = models.PlatformParameterSet.objects.filter(
                    owner=owner, schema=schema)
            for paramset in paramsets:
                parameters = {'name': paramset.name}
                parameter_objects = models.PlatformParameter.objects.filter(paramset=paramset)
                for parameter in parameter_objects:
                    parameters[parameter.name.name] = parameter.value
                platforms.append(parameters)
        except ObjectDoesNotExist, e:
            print e
        for i in platforms:
            print i['name']
        return platforms



    def retrieve_platform(self, bdp_username, filterlist):
        user = User.objects.get(username=bdp_username)
        print 'user %s ' % user
        profile = models.UserProfile.objects.get(user=user)
        print('profile=%s' % profile)
        platform = models.PlatformInstance.objects.filter(schema_namespace_prefix=self.namespace)
        print platform

        platform_schema = models.Schema.objects\
            .get(namespace=self.namespace)


        for platform in platform:
            param_set = models.PlatformInstanceParameterSet.objects.\
                filter(platform=platform)
            print param_set


            for k, v in filterlist.items():
                print k, v
                try:
                    param_name = models.ParameterName.objects.get(schema=platform_schema,
                        name=k)
                    p = models.PlatformInstanceParameter.objects.get(name=param_name,
                        paramset=param_set,
                        value=v)
                    print p
                except Exception as e:
                    if isinstance(e, ObjectDoesNotExist):
                        print 'New model'
                    else:
                        raise



            #for i in param_set:
            #    print i.schema.namespace



    def unix_key_generate(self):
        import socket, paramiko
        remote_path = '/home/ec2-user'
        parameters = {'username': 'ec2-user', 'password': '1234', 'ip_address': '118.138.241.55',
                      'home_path': '/home/ec2-user', 'private_key_path': '.ssh/seid/unix/bdp_iman'}
        passwd_auth = True

        from django.core.files.base import ContentFile


        key_generated = True
        message = 'Key generated successfully'
        password = ''
        if 'password' in parameters.keys():
            password = parameters['password']

        ssh_settings = {'username': parameters['username'],
                    'password': password}

        storage_settings = {'params': ssh_settings,
                            'host': parameters['ip_address'],
                            'root': "/"}
        bdp_root_path = get_bdp_root_path()
        key_name_org = os.path.splitext(os.path.basename(parameters['private_key_path']))[0]
        key_name = key_name_org
        private_key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
        key_dir = os.path.dirname(private_key_absolute_path)
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
        counter = 1
        while os.path.exists(os.path.join(key_dir, key_name)):
            key_name = '%s_%d' % (key_name_org, counter)
            counter += 1
        parameters['private_key_path'] = os.path.join(os.path.dirname(
                parameters['private_key_path']), key_name)
        private_key_absolute_path = os.path.join(bdp_root_path, parameters['private_key_path'])
        public_key_absolute_path = '%s.pub' % private_key_absolute_path
        remote_key_path = os.path.join(parameters['home_path'], '.ssh', ('%s.pub' % key_name))
        authorized_remote_path = os.path.join(parameters['home_path'], '.ssh', 'authorized_keys')
        try:
            private_key = paramiko.RSAKey.generate(1024)
            private_key.write_private_key_file(private_key_absolute_path)
            public_key = paramiko.RSAKey(filename=private_key_absolute_path)
            public_key_content = '%s %s' % (public_key.get_name(), public_key.get_base64())
            f = open(public_key_absolute_path, 'w')
            f.write("\n%s\n" % public_key_content)
            f.close()
            fs = RemoteStorage(settings=storage_settings)
            fs.save(remote_key_path, ContentFile(public_key_content))
            ssh_client = open_connection(parameters['ip_address'], ssh_settings)
            command = 'cat %s >> %s' % (remote_key_path, authorized_remote_path)
            command_out, errs = run_command_with_status(ssh_client, command)
            if errs:
                if 'Permission denied' in errs:
                    key_generated = False
                    message = 'Permission denied to copy public key to %s/.ssh/authorized_keys' % parameters['home_path']
                else:
                    raise IOError
        except AuthError:
            key_generated = False
            message = 'Unauthorized access to %s' % parameters['ip_address']
        except socket.gaierror, e:
            key_generated = False
            if 'Name or service not known' in e:
                message = 'Unknown IP address [%s]' % parameters['ip_address']
            else:
                message = '[%s]: %s, %s' % (parameters['ip_address'], e.__doc__, e.strerror)
        except IOError, e:
            key_generated = False
            if 'Permission denied' in e:
                message = "Permission denied to copy public key to %s/.ssh " % parameters['home_path']
            elif 'No such file' in e:
                message = 'Home path [%s] does not exist' % parameters['home_path']
            else:
                message = '[%s]: %s, %s' % (parameters['home_path'], e.__doc__, e.strerror)
        except Exception as e:
            key_generated = False
            message = e
        print message

        return key_generated, message




    def remote_path_exists(self):
        import socket, paramiko
        remote_path = '/home/ec2-user'
        parameters = {'username': 'ec2-user', 'password': '1234', 'ip_address': '118.138.241.55'}
        passwd_auth = True


        password = ''
        if 'password' in parameters.keys():
            password = parameters['password']
        paramiko_settings = {'username': parameters['username'],
                             'password': password}
        if (not passwd_auth) and 'private_key_path' in parameters:
            paramiko_settings['key_filename'] = os.path.join(
                get_bdp_root_path(), parameters['private_key_path'])
        ssh_settings = {'params': paramiko_settings,
                        'host': parameters['ip_address'],
                        'root': "/"}
        exists = True
        message = 'Remote path [%s] exists' % remote_path
        try:
            fs = RemoteStorage(settings=ssh_settings)
            fs.listdir(remote_path)
        except paramiko.AuthenticationException, e:
            message = 'Unauthorized access to %s' % parameters['ip_address']
            exists = False
        except socket.gaierror as e:
            exists = False
            if 'Name or service not known' in e:
                message = 'Unknown IP address [%s]' % parameters['ip_address']
            else:
                message = '[%s]: %s, %s' % (parameters['ip_address'], e.__doc__, e.strerror)
        except IOError, e:
            exists = False
            if 'Permission denied' in e:
                message = "Permission denied to access %s/.ssh " % remote_path
            elif 'No such file' in e:
                message = 'Remote path [%s] does not exist' % remote_path
            else:
                message = '[%s]: %s, %s' % (remote_path, e.__doc__, e.strerror)
        return exists, message



    def is_unique_platform(self, unique_key, parameterset):
        for parameter in parameterset:
            print parameter


    def retrieve_platform(self):
        username = 'seid'
        name = 'nectar_home_test'
        parameters = {}
        try:
            user = User.objects.get(username=username)
            owner = models.UserProfile.objects.get(user=user)
            paramset = models.PlatformParameterSet.objects.get(
                name=name, owner=owner)
            parameter_objects = models.PlatformParameter.objects.filter(paramset=paramset)
            for parameter in parameter_objects:
                parameters[parameter.name.name] = parameter.value


            #print platform
        except ObjectDoesNotExist, e:
            print e

        print parameters

    @transaction.commit_on_success
    def update_platform(self):
        from django.db.utils import IntegrityError
        self.retrieve_platform()
        username = 'seid'
        name = 'home'
        updated_parameters = {u'ec2_access_key': u'special-282XX82', u'name':'home'}
        try:

            user = User.objects.get(username=username)
            owner = models.UserProfile.objects.get(user=user)
            paramset = models.PlatformParameterSet.objects.get(
                name=name, owner=owner)
            print paramset
            #parameter_objects = models.PlatformParameter.objects.filter(paramset=paramset)


            for k, v in updated_parameters.items():
                try:

                    param_name = models.ParameterName.objects\
                        .get(schema=paramset.schema, name=k)
                    print param_name
                    platform_param = models.PlatformParameter.objects\
                        .get(name=param_name, paramset=paramset)
                    print platform_param
                    platform_param.value = v
                    print 'hi'
                    platform_param.save()
                except ObjectDoesNotExist as e:
                    print('Skipping unrecognized parameter name: %s' % k)
                    continue
            if 'name' in updated_parameters.keys():
                paramset.name = updated_parameters['name']
                paramset.save()
            #print platform
        except ObjectDoesNotExist, e:
            print e
        except IntegrityError, e:
            print '---'
            print e
            print '-------'
        print '--'
        #self.retrieve_platform()


    def delete_platform(self):
        self.retrieve_platform()
        username = 'seid'
        name = 'nectar_home_test'
        updated_parameters = {u'ec2_access_key': u'special'}
        try:

            user = User.objects.get(username=username)
            owner = models.UserProfile.objects.get(user=user)
            paramset = models.PlatformParameterSet.objects\
                .get(
                name=name, owner=owner)
            paramset.delete()
            #parameter_objects = models.PlatformParameter.objects.filter(paramset=paramset)

            #print platform
        except ObjectDoesNotExist, e:
            print e
        print '--'
        self.retrieve_platform()


    def create_platform(self):
        from django.db.utils import IntegrityError
        username = 'seid'
        namespace = 'http://rmit.edu.au/schemas/platform/computation/nectar'
        name = 'nectar_home_test'
        parameters = {
                'ec2_access_key': 'unique',
                'ec2_secret_key': 'secret_key_test',
                #'ec2_access_key': 'access_key_test114',
                'private_key': 'file://local@127.0.0.1/schema.pem',
                'private_key_iman': 'file://local@127.0.0.1/test.pem'
            }
        try:
            user = User.objects.get(username=username)

            owner = models.UserProfile.objects.get(user=user)

            schema = models.Schema.objects\
                .get(namespace=namespace)
        except ObjectDoesNotExist, e:
            print e
            return

        try:
            param_set = models.PlatformParameterSet.objects.create(name=name, owner=owner, schema=schema)
        except IntegrityError, e:
            print e
            print ('Plaatform name %s already exists' % name)
            return
        for k, v in parameters.items():
            try:
                param_name = models.ParameterName.objects\
                    .get(schema=schema, name=k)
            except ObjectDoesNotExist as e:
                print('Skipping unrecognized parameter name: %s' % k)
                continue
            models.PlatformParameter.objects\
                .create(name=param_name, paramset=param_set, value=v)





    def create_platform_old(self, bdp_username,
                                    platform_settings):

        self.PARAMS = {
                'ec2_access_key': 'unique',
                'ec2_secret_key': 'secret_key_test',
                #'ec2_access_key': 'access_key_test114',
                'private_key': 'file://local@127.0.0.1/schema.pem',
                'private_key_iman': 'file://local@127.0.0.1/test.pem'
            }

        self.PARAMS_D = {
                'username': 'nci',
                }

        self.name = 'HRMC_tenancy'
        self.private_key = 'bdp'
        self.private_key_path = '/home/bdp/.ssh/bdp.pem'
        self.vm_image_size = 'm1.small'
        self.ec2_access_key = 'EC2_ACCESS_KEY_1234'
        self.ec2_secret_key = 'EC2_SECRET_KEY_5678'
        self.nectar_parameters =  {
            'name': self.name,
            'private_key': self.private_key,
            'private_key_path': self.private_key_path,
            'vm_image_size': self.vm_image_size,
            'ec2_access_key': self.ec2_access_key,
            'ec2_secret_key': self.ec2_secret_key
        }

        self.PARAMS = self.nectar_parameters
        self.namespace = 'http://rmit.edu.au/schemas/platform/computation/nectar'

        create_platform_paramset(bdp_username, self.namespace, self.PARAMS)

        self.name = 'HRMC_tenancy'
        self.private_key = 'bdp'
        self.private_key_path = '/home/bdp/.ssh/bdp.pem'
        self.vm_image_size = 'm1.small'
        self.ec2_access_key = 'EC2_ACCESS_KEY_1234'
        self.ec2_secret_key = 'EC2_SECRET_KEY_5678'
        self.nectar_parameters =  {
            'name': self.name,
            'private_key': self.private_key,
            'private_key_path': self.private_key_path,
            'vm_image_size': self.vm_image_size,
            'ec2_access_key': self.ec2_access_key,
            'ec2_secret_key': self.ec2_secret_key
        }

        self.PARAMS = self.nectar_parameters
        self.namespace = 'http://rmit.edu.au/schemas/platform/computation/nectar'

        create_platform_paramset(bdp_username, self.namespace, self.PARAMS)

        self.nci_parameters = {
            'private_key_path': '/home/user2',
            'username': 'user2'
        }
        self.namespace = 'http://rmit.edu.au/schemas/platform/computation/nci'
        self.PARAMS = self.nci_parameters
        create_platform_paramset(bdp_username, self.namespace, self.PARAMS)


        #delete_platform_paramsets(bdp_username, self.namespace, self.PARAMS_D)
        '''
        print'-----'
        platform implementation in progress

        user = User.objects.get(username=bdp_username)
        print 'user %s ' % user
        profile = models.UserProfile.objects.get(user=user)
        print('profile=%s' % profile)


        '''


        print 'x'
        x= (retrieve_platform_paramsets(bdp_username, 'http://rmit.edu.au/schemas/platform/computation'))
        for i in x:
            print i

        return

        print 'x'
        x= (retrieve_platform_paramsets(bdp_username, 'http://rmit.edu.au/schemas/platform/computation'))
        for i in x:
            print i

        return
        try:
           platform, _ = models.PlatformInstance.objects\
               .get_or_create(owner=profile, schema_namespace_prefix=self.namespace)
        except models.MultipleObjectsReturned as e:
            #fixme move to reliability framework
            print 'Computation platform already registered'
            print e
        except Exception:
            raise


        #check for non existent schema
        platform_schema = models.Schema.objects\
            .get(namespace=self.namespace)

        #test = models.PlatformInstance.nectar_objects.all()
        #self.is_unique('', test)


        self.PARAMS = {

                'ec2_access_key': 'access_key_test12',
                'ec2_secret_key': 'secret_key_test',
                'ec2_access_key': 'access_key_test114',
                'private_key': 'file://local@127.0.0.1/test.pem',
                'private_key_iman': 'file://local@127.0.0.1/test.pem'
            }

        #self.PARAMS = {'username': 'nci', 'private_key_path': '/local/path'}
        filterlist = self.PARAMS

        unique = self.is_unique_platform_paramterset(
            filterlist, platform, platform_schema)
        if not unique:
            print 'not unique'
            return
        print 'unique'
        try:
            param_set = models.PlatformInstanceParameterSet.objects\
                .create(platform=platform,
                        schema=platform_schema)
            for k, v in self.PARAMS.items():
                #print k
                param_name = models.ParameterName.objects.get(schema=platform_schema,
                    name=k)
                models.PlatformInstanceParameter.objects.create(name=param_name,
                    paramset=param_set,
                    value=v)
        except ObjectDoesNotExist as e:
            print e
        except Exception as e:
            #fixme move to reliability framework
            if isinstance(e, models.MultipleObjectsReturned):
                print 'Computation platform parameterset already registered'
                print e
            else:
                raise






        '''
            owner=profile, type=platform_settings['type'],
            ip_address=platform_settings['ip_address'],
            root_path=platform_settings['root_path'],
            username=platform_settings['username'],
            password=platform_settings['password'],
            private_key_name=platform_settings['private_key_name'])
        '''











































