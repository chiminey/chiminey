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
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from bdphpcprovider.smartconnectorscheduler import models, platform
from bdphpcprovider.smartconnectorscheduler.platform import retrieve_platform_paramsets, create_platform_paramset, delete_platform_paramsets

from django.db.models import ObjectDoesNotExist


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
        self.create_platform(
            bdp_username, platform_settings)
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

    def is_unique_platform(self, unique_key, parameterset):
        for parameter in parameterset:
            print parameter


    def create_platform(self, bdp_username,
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











































