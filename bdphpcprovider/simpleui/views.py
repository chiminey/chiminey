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

import logging
import os
import json
import requests
import ast
from pprint import pformat

from urllib2 import URLError, HTTPError


logger = logging.getLogger(__name__)

from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

from django.template import Context, RequestContext, loader
from django.shortcuts import redirect

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from django.contrib import messages

from bdphpcprovider.simpleui.hrmc.hrmcsubmit import HRMCSubmitForm
from bdphpcprovider.simpleui.makeform import MakeSubmitForm
from bdphpcprovider.simpleui.sweepform import SweepSubmitForm
from bdphpcprovider.simpleui.hrmc.copy import CopyForm
from bdphpcprovider.simpleui.ncicomputationplatform import NCIComputationPlatformForm
from bdphpcprovider.simpleui.nectarcomputationplatform import NeCTARComputationPlatformForm
from bdphpcprovider.simpleui.sshstorageplatform import SSHStoragePlatformForm
#TODO,FIXME: simpleui shouldn't refer to anything in smartconnectorscheduler
#and should be using its own models and use the REST API for all information.

from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages, platform
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError

from django.utils.datastructures import SortedDict
from django import forms

from bdphpcprovider.simpleui import validators
from django.core.validators import ValidationError

from django.http import Http404
from django.views.generic.edit import FormView

from django.views.generic import DetailView

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, render


def bdp_account_settings(request):
    return render(request, 'accountsettings/bdpaccount.html', {})


def computation_platform_settings(request):
    nciform = NCIComputationPlatformForm()
    nectarform = NeCTARComputationPlatformForm()
    if request.method == "POST":
        nciform = NCIComputationPlatformForm(request.POST)
        nectarform = NeCTARComputationPlatformForm(request.POST)
        if nciform.is_valid():
            schema = 'http://rmit.edu.au/schemas/platform/computation/nci'
            post_platform(schema, nciform.cleaned_data, request)
            return HttpResponseRedirect('/accounts/settings/platform/computation/')
        elif nectarform.is_valid():
            schema = 'http://rmit.edu.au/schemas/platform/computation/nectar'
            post_platform(schema, nectarform.cleaned_data, request, type='nectar')
            return HttpResponseRedirect('/accounts/settings/platform/computation/')

    #FIXME: consider using non-locahost URL for api_host
    api_host = "http://127.0.0.1"

    url = "%s/api/v1/platformparameter/?format=json&limit=0&schema=http://rmit.edu.au/schemas/platform/computation" % api_host
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    headers = {'content-type': 'application/json'}
    try:
        #response = urlopen(req)
        r = requests.get(url,
        headers=headers,
        cookies=cookies)
    except HTTPError as e:
        logger.debug('The server couldn\'t fulfill the request. %s' % e)
        logger.debug('Error code: ', e.code)
    except URLError as e:
        logger.debug('We failed to reach a server. %s' % e)
        logger.debug('Reason: ', e.reason)
    else:
        logger.debug('everything is fine')
        #logger.debug(r.text)
        #logger.debug(r.json())
        GET_data = r.json()
        computation_platforms, all_headers = filter_computation_platforms(GET_data)
        logger.debug(computation_platforms)
    # FIXME: schemas in all_headers must be sorted with "name" as first
    # parameter so that footable will respond correctly.
    return render(request, 'accountsettings/computationplatform.html',
                              {'nci_form': nciform, 'nectar_form': nectarform,
                               'computation_platforms': computation_platforms,
                               'all_headers': all_headers})


def storage_platform_settings(request):
    unix_form = SSHStoragePlatformForm()
    if request.method == "POST":
        unix_form = SSHStoragePlatformForm(request.POST)
        if unix_form.is_valid():
            schema = 'http://rmit.edu.au/schemas/platform/storage/unix'
            post_platform(schema, unix_form.cleaned_data, request)
            return HttpResponseRedirect('/accounts/settings/platform/storage')

    #FIXME: consider using non-locahost URL for api_host
    api_host = "http://127.0.0.1"

    url = "%s/api/v1/platformparameter/?format=json&limit=0&schema=http://rmit.edu.au/schemas/platform/storage" % api_host
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    headers = {'content-type': 'application/json'}
    try:
        #response = urlopen(req)
        r = requests.get(url,
        headers=headers,
        cookies=cookies)
    except HTTPError as e:
        logger.debug('The server couldn\'t fulfill the request. %s' % e)
        logger.debug('Error code: ', e.code)
    except URLError as e:
        logger.debug('We failed to reach a server. %s' % e)
        logger.debug('Reason: ', e.reason)
    else:
        logger.debug('everything is fine')
        #logger.debug(r.text)
        #logger.debug(r.json())
        GET_data = r.json()
        storage_platforms, all_headers = filter_computation_platforms(GET_data)
        logger.debug(storage_platforms)
    return render(request, 'accountsettings/storageplatform.html',
                              {'unix_form': unix_form,
                               'all_headers': all_headers})


def post_platform(schema, form_data, request, type=None):
    logger.debug('operation=%s' % form_data['operation'])
    api_host = "http://127.0.0.1"  # fixme: remove local host address
    url = "%s/api/v1/platformparamset/?format=json" % api_host
    # pass the sessionid cookie through to the internal API
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    headers = {'content-type': 'application/json'}
    parameters = {}
    filters = {}
    for k, v in form_data.items():
        parameters[k] = v
    for i in ast.literal_eval(form_data['filters']):
        logger.debug(i)
        filters[i[0]] = i[1]
    data = json.dumps({'operation': form_data['operation'],
                       'parameters': parameters,
                       'schema': schema,
                       'filters': filters})
    logger.debug('filters=%s' % form_data['filters'])
    logger.debug('filters=%s' % filters)
    r = requests.post(url,
        data=data,
        headers=headers,
        cookies=cookies)

    if r.status_code != 201:
        error_message = ''
        if r.status_code == 409:
            messages.error(request, "%s" % r.headers['message'])
        else:
            messages.error(request, "Task Failed with status code %s: %s" % (r.status_code, r.headers['message']))
        return False
    else:
        messages.success(request, "%s" % r.headers['message'])
    # TODO: need to check for status_code and handle failures.


#fixme revise this method
def filter_computation_platforms(GET_json_data):
    platform_parameters_objects = GET_json_data['objects']
    computation_platforms = {}

    for i in platform_parameters_objects:
        schema = i['paramset']['platform']['schema_namespace_prefix']
        computation_platforms[schema] = {}


    for i in platform_parameters_objects:
        schema = i['paramset']['platform']['schema_namespace_prefix']
        paramset_id = i['paramset']['id']
        computation_platforms[schema][paramset_id] = {}


    for i in platform_parameters_objects:
        schema = i['paramset']['platform']['schema_namespace_prefix']
        paramset_id = i['paramset']['id']
        name = i['name']['name']

        if name == 'password':
            value = '****'
        else:
            value = i['value']
        computation_platforms[schema][paramset_id][str(name)] = str(value)

    headers={}
    all_headers={}
    import os
    logger.debug('computation=%s' % computation_platforms)
    for i, j in computation_platforms.items():
        headers[i] = []
        platform_type = os.path.basename(i)

        params = []
        for a, b in j.items():
            for c, d in b.items():
                params.append(c)
            break
        headers[i] = params
        all_headers[platform_type] = {tuple(params): j}
        logger.debug(platform_type)
    logger.debug('----')
    logger.debug(all_headers)


    return computation_platforms, all_headers

class UserProfileParameterListView(ListView):
    model = models.UserProfileParameter
    template_name = "list_userprofileparameter.html"

    def get_queryset(self):
            return models.UserProfileParameter.objects.filter(paramset__user_profile__user=self.request.user)

from django.views.generic import TemplateView

class AboutView(TemplateView):
    template_name = "home.html"

class CreateUserProfileParameterView(CreateView):
    model = models.UserProfileParameter
    template_name = "edit_userprofileparameter.html"

    def get_success_url(self):
        return reverse('userprofileparameter-list')

    def get_context_data(self, **kwargs):
        context = super(CreateUserProfileParameterView, self).get_context_data(**kwargs)
        context['action'] = reverse('userprofileparameter-new')
        return context


class UpdateUserProfileParameterView(UpdateView):
    model = models.UserProfileParameter
    template_name = "edit_userprofileparameter.html"

    def get_success_url(self):
        return reverse('userprofileparameter-list')

    def get_context_data(self, **kwargs):
        context = super(UpdateUserProfileParameterView, self).get_context_data(**kwargs)
        context['action'] = reverse('userprofileparameter-edit', kwargs={'pk': self.get_object().id})
        return context

    def get_object(self):
        object = super(UpdateUserProfileParameterView, self).get_object()
        if object.paramset.user_profile.user == self.request.user:
            return object
        else:
            raise Http404


class DeleteUserProfileParameterView(DeleteView):
    model = models.UserProfileParameter
    template_name = 'delete_userprofileparameter.html'

    def get_success_url(self):
        return reverse('userprofileparameter-list')

    def get_object(self):
        object = super(DeleteUserProfileParameterView, self).get_object()
        if object.paramset.user_profile.user == self.request.user:
            return object
        else:
            raise Http404


def logout_page(request):
    """
    Log users out and re-direct them to the main page.
    """
    logout(request, next_page="/")
    return HttpResponseRedirect('/')


class ContextList(ListView):
    model = models.Context
    template_name = "list_jobs.html"

    def get_queryset(self):
        return models.Context.objects.filter(owner__user=self.request.user).order_by('-id')

from django.shortcuts import get_object_or_404
from django.db.models import Model
class AccountSettingsView(FormView):
    template_name = "accountsettings/computationplatform.html"
    form_class = NCIComputationPlatformForm
    #success_url = '/accountsettings/computationplatform.html'

    def get_success_url(self):
        return reverse('hrmcjob-list')


class FinishedContextUpdateView(UpdateView):
    model = models.Context
    template_name = "edit_context.html"

    def get_success_url(self):
        return reverse('hrmcjob-list')

    # def get_context_data(self, **kwargs):
    #     context = super(UpdateUserProfileParameterView, self).get_context_data(**kwargs)
    #     context['action'] = reverse('userprofileparameter-edit', kwargs={'pk': self.get_object().id})
    #     return context

    def get_object(self):
        object = super(FinishedContextUpdateView, self).get_object()
        if object.owner.user == self.request.user:
            return object
        else:
            raise Http404


class ListDirList(TemplateView):

    template_name = "listdir.html"

    def get_context_data(self, **kwargs):
        context = super(ListDirList, self).get_context_data(**kwargs)

        url = smartconnector.get_url_with_pkey({}, ".", is_relative_path=True)
        file_paths = [x[1:] for x in hrmcstages.list_all_files(url)]
        context['paths'] = file_paths
        return context


class ContextView(DetailView):
    model = models.Context
    template_name = 'view_context.html'

    def get_context_data_old(self, **kwargs):
        context = super(ContextView, self).get_context_data(**kwargs)
        cpset = models.ContextParameterSet.objects.filter(context=self.object)
        res = []
        context['stage'] = self.object.current_stage.name
        for cps in cpset:
            # TODO: HTML should be part of template
            res.append("<h2>%s</h2> " % cps.schema.namespace)
            for cp in models.ContextParameter.objects.filter(paramset=cps):
                res.append("%s=%s" % (cp.name.name, cp.value))
        context['settings'] = '<br>'.join(res)
        return context

    def get_context_data(self, **kwargs):
        context = super(ContextView, self).get_context_data(**kwargs)
        cpset = models.ContextParameterSet.objects.filter(context=self.object)
        res = {}
        context['stage'] = self.object.current_stage.name
        for cps in cpset:
            res2 = {}
            for cp in models.ContextParameter.objects.filter(paramset=cps):
                res2[cp.name.name] = [cp.value, cp.name.help_text, cp.name.subtype]
                #res2[cp.name.name] = [cp.value, "hello"]
            if cps.schema.name:
                res["%s (%s) " % (cps.schema.name, cps.schema.namespace)] = res2
            else:
                res[cps.schema.namespace] = res2
        context['settings'] = res
        return context

    def get_object(self):
            object = super(ContextView, self).get_object()
            if object.owner.user == self.request.user:
                return object
            else:
                raise Http404




class ContextList(ListView):
    model = models.Context
    template_name = "list_jobs.html"

    def get_queryset(self):
        return models.Context.objects.filter(owner__user=self.request.user).order_by('-id')


class HRMCSubmitFormView(FormView):
    template_name = 'hrmc.html'
    form_class = HRMCSubmitForm
    success_url = '/jobs'
    hrmc_schema = "http://rmit.edu.au/schemas/hrmc/"
    system_schema = "http://rmit.edu.au/schemas/system/misc/"

    initial = {'number_vm_instances': 1,
               'minimum_number_vm_instances': 1,
        'iseed': 42,
        'input_location': 'file://127.0.0.1/myfiles/input',
        'number_dimensions': 1,
        'threshold': "[2]",
        'error_threshold': "0.03",
        'max_iteration': 10,
        'pottype': 1,
        'experiment_id': 0,
        'output_location': 'file://local@127.0.0.1/hrmcrun'
        }

    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    def form_valid(self, form):
        # An example of using the REST API to control the system, rather than
        # talking directly to the models in smartconnectorscheduler.
        # TODO: do the same for other parts of UI, e.g., user settings form
        # should call user_setttings API endpoint.
        #FIXME: consider using non-locahost URL for api_host
        api_host = "http://127.0.0.1"
        url = "%s/api/v1/context/?format=json" % api_host

        logger.debug("self.request.user.username=%s" % self.request.user.username)
        logger.debug("self.request.user.username=%s" % self.request.user.password)

        # pass the sessionid cookie through to the internal API
        cookies = dict(self.request.COOKIES)
        logger.debug("cookies=%s" % cookies)
        headers = {'content-type': 'application/json'}
        data = json.dumps({'smart_connector': 'hrmc',
                    self.hrmc_schema + 'number_vm_instances': form.cleaned_data['number_vm_instances'],
                    self.hrmc_schema + 'minimum_number_vm_instances': form.cleaned_data['minimum_number_vm_instances'],
                    self.hrmc_schema + u'iseed': form.cleaned_data['iseed'],
                    self.hrmc_schema + 'input_location':  form.cleaned_data['input_location'],
                    self.hrmc_schema + 'number_dimensions': form.cleaned_data['number_dimensions'],
                    self.hrmc_schema + 'threshold': str(form.cleaned_data['threshold']),
                    self.hrmc_schema + 'error_threshold': str(form.cleaned_data['error_threshold']),
                    self.hrmc_schema + 'max_iteration': form.cleaned_data['max_iteration'],
                    self.hrmc_schema + 'pottype': form.cleaned_data['pottype'],
                    self.hrmc_schema + 'experiment_id': form.cleaned_data['experiment_id'],
                    self.system_schema + 'output_location': form.cleaned_data['output_location']})
        r = requests.post(url,
            data=data,
            headers=headers,
            cookies=cookies)

        # TODO: need to check for status_code and handle failures.

        logger.debug("r.json=%s" % r.json)
        logger.debug("r.text=%s" % r.text)
        logger.debug("r.headers=%s" % r.headers)
        header_location = r.headers['location']
        logger.debug("header_location=%s" % header_location)
        new_context_uri = header_location[len(api_host):]
        logger.debug("new_context_uri=%s" % new_context_uri)

        return super(HRMCSubmitFormView, self).form_valid(form)


class SweepSubmitFormView(FormView):
    template_name = 'sweep.html'
    form_class = SweepSubmitForm
    success_url = '/jobs'


    initial = {'number_vm_instances': 0,
               'minimum_number_vm_instances': 0,
        'iseed': 42,
        'maximum_retry': 1,
        'reschedule_failed_processes': 1,
        'input_location': 'file://127.0.0.1/myfiles/input',
        'number_dimensions': 1,
        'threshold': "[1]",
        'error_threshold': "0.03",
        'max_iteration': 2,
        'fanout_per_kept_result': 2,
        'pottype': 1,
        'sweep_map': '{}', #"var1": [3, 7], "var2": [1, 2]}',
        'run_map': '{}',
        'experiment_id': 0,
        'output_location': 'file://local@127.0.0.1/sweep'

        }

    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    def form_valid(self, form):

        schemas={
        'hrmc_schema':"http://rmit.edu.au/schemas/hrmc/",
        'system_schema':"http://rmit.edu.au/schemas/system/misc/",
        'run_schema':"http://rmit.edu.au/schemas/stages/run/",
        'sweep_schema':"http://rmit.edu.au/schemas/stages/sweep/",
        }
        submit_sweep_job(self.request, form, schemas)
        return super(SweepSubmitFormView, self).form_valid(form)


def submit_sweep_job(request, form, schemas):

    #FIXME: consider using non-locahost URL for api_host
    api_host = "http://127.0.0.1"
    url = "%s/api/v1/context/?format=json" % api_host

    logger.debug("request.user.username=%s" % request.user.username)
    logger.debug("request.user.username=%s" % request.user.password)

    # pass the sessionid cookie through to the internal API
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    headers = {'content-type': 'application/json'}

    data = json.dumps({'smart_connector': 'sweep',
                schemas['hrmc_schema'] + 'number_vm_instances': form.cleaned_data['number_vm_instances'],
                schemas['hrmc_schema'] + 'minimum_number_vm_instances': form.cleaned_data['minimum_number_vm_instances'],
                schemas['hrmc_schema'] + u'iseed': form.cleaned_data['iseed'],
                schemas['sweep_schema'] + 'input_location':  form.cleaned_data['input_location'],
                schemas['hrmc_schema'] + 'number_dimensions': form.cleaned_data['number_dimensions'],
                schemas['hrmc_schema'] + 'fanout_per_kept_result': form.cleaned_data['fanout_per_kept_result'],
                schemas['hrmc_schema'] + 'threshold': str(form.cleaned_data['threshold']),
                schemas['hrmc_schema'] + 'error_threshold': str(form.cleaned_data['error_threshold']),
                schemas['hrmc_schema'] + 'max_iteration': form.cleaned_data['max_iteration'],
                schemas['hrmc_schema'] + 'pottype': form.cleaned_data['pottype'],
                #'experiment_id': form.cleaned_data['experiment_id'],
                schemas['sweep_schema'] + 'sweep_map': form.cleaned_data['sweep_map'],
                schemas['sweep_schema'] + 'directive': 'hrmc',
                #'run_map': form.cleaned_data['run_map'],
                schemas['run_schema'] + 'run_map': "{}",
                schemas['system_schema'] + 'output_location': form.cleaned_data['output_location']})

    logger.debug("data=%s" % data)
    r = requests.post(url,
        data=data,
        headers=headers,
        cookies=cookies)

     # TODO: need to check for status_code and handle failures.

    logger.debug("r.json=%s" % r.json)
    logger.debug("r.text=%s" % r.text)
    logger.debug("r.headers=%s" % r.headers)
    header_location = r.headers['location']
    logger.debug("header_location=%s" % header_location)
    new_context_uri = header_location[len(api_host):]
    logger.debug("new_context_uri=%s" % new_context_uri)


class MakeSubmitFormView(FormView):
    template_name = 'make.html'
    form_class = MakeSubmitForm
    success_url = '/jobs'
    system_schema = "http://rmit.edu.au/schemas/system/misc/"

    initial = {
        'input_location': 'file://local@127.0.0.1/myfiles/vasppayload',
        'output_location': 'file://local@127.0.0.1/myfiles/vaspoutput',
        'experiment_id': 0,
        'sweep_map': '{"num_kp": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], "encut": [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700]}'
    }

    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    def form_valid(self, form):
        #FIXME: consider using non-locahost URL for api_host
        api_host = "http://127.0.0.1"
        url = "%s/api/v1/context/?format=json" % api_host

        logger.debug("self.request.user.username=%s" % self.request.user.username)
        logger.debug("self.request.user.username=%s" % self.request.user.password)

        # pass the sessionid cookie through to the internal API
        cookies = dict(self.request.COOKIES)
        logger.debug("cookies=%s" % cookies)
        headers = {'content-type': 'application/json'}

        remotemake_schema = "http://rmit.edu.au/schemas/remotemake/"
        make_schema = "http://rmit.edu.au/schemas/stages/make/"
        data = json.dumps({'smart_connector': 'remotemake',
                    remotemake_schema+'input_location':  form.cleaned_data['input_location'],
                    remotemake_schema+'experiment_id': form.cleaned_data['experiment_id'],
                    make_schema+'sweep_map': form.cleaned_data['sweep_map'],
                    self.system_schema+'output_location': form.cleaned_data['output_location']})

        r = requests.post(url,
            data=data,
            headers=headers,
            cookies=cookies)

         # TODO: need to check for status_code and handle failures.

        logger.debug("r.json=%s" % r.json)
        logger.debug("r.text=%s" % r.text)
        logger.debug("r.headers=%s" % r.headers)
        logger.debug("data=%s" % data)
        header_location = r.headers['location']
        logger.debug("header_location=%s" % header_location)
        new_context_uri = header_location[len(api_host):]
        logger.debug("new_context_uri=%s" % new_context_uri)

        return super(MakeSubmitFormView, self).form_valid(form)



    # def form_valid(self, form):
    #     # This method is called when valid form data has been POSTed.
    #     # It should return an HttpResponse.
    #     platform = 'local'
    #     directive_name = "remotemake"
    #     logger.debug("%s" % directive_name)
    #     directive_args = []

    #     directive_args.append(
    #         ['',
    #             ['http://rmit.edu.au/schemas/remotemake',
    #                 ('input_location',  form.cleaned_data['input_location'])]])

    #     logger.debug("form=%s" % pformat(form.cleaned_data))

    #     logger.debug("directive_args=%s" % directive_args)

    #     # make the system settings, available to initial stage and merged with run_settings
    #     system_dict = {
    #         u'system': u'settings',
    #         u'output_location': form.cleaned_data['output_location']}
    #     system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

    #     logger.debug("directive_name=%s" % directive_name)
    #     logger.debug("directive_args=%s" % directive_args)

    #     # FIXME: we should be sending this request to scheduler API using
    #     # POST, to keep separation of concerns.  See sweep for example.

    #     try:
    #         (run_settings, command_args, run_context) \
    #             = hrmcstages.make_runcontext_for_directive(
    #             platform,
    #             directive_name,
    #             directive_args, system_settings, self.request.user.username)

    #     except InvalidInputError, e:
    #         return HttpResponse(str(e))

    #     return super(MakeSubmitFormView, self).form_valid(form)


class CopyFormView(FormView):
    template_name = 'copy.html'
    form_class = CopyForm
    success_url = '/jobs'

    initial = {'source_bdp_url': 'file://local@127.0.0.1/myfiles/sourcedir',
        'destination_bdp_url': 'file://local@127.0.0.1/myfiles/destdir',
        }

    # This method is called when valid form data has been POSTed.
    # It should return an HttpResponse.
    def form_valid(self, form):
        #FIXME: consider using non-locahost URL for api_host
        api_host = "http://127.0.0.1"
        url = "%s/api/v1/context/?format=json" % api_host

        logger.debug("self.request.user.username=%s" % self.request.user.username)
        logger.debug("self.request.user.username=%s" % self.request.user.password)

        # pass the sessionid cookie through to the internal API
        cookies = dict(self.request.COOKIES)
        logger.debug("cookies=%s" % cookies)
        headers = {'content-type': 'application/json'}

        data = json.dumps({'smart_connector': 'copydir',
                           'source_bdp_url': form.cleaned_data['source_bdp_url'],
                           'destination_bdp_url': form.cleaned_data['destination_bdp_url']
                           })

        r = requests.post(url,
            data=data,
            headers=headers,
            cookies=cookies)

         # TODO: need to check for status_code and handle failures.

        logger.debug("r.json=%s" % r.json)
        logger.debug("r.text=%s" % r.text)
        logger.debug("r.headers=%s" % r.headers)
        header_location = r.headers['location']
        logger.debug("header_location=%s" % header_location)
        new_context_uri = header_location[len(api_host):]
        logger.debug("new_context_uri=%s" % new_context_uri)

        return super(CopyFormView, self).form_valid(form)

subtype_validation = {
    'natural': ('natural number', validators.validate_natural_number, None, None),
    'string': ('string', validators.validate_string, None, None),
    'whole': ('whole number', validators.validate_whole_number, None, None),
    'even': ('even number', validators.validate_even_number, None, None),
    'bdpurl': ('BDP url', validators.validate_BDP_url, forms.TextInput, 255),
    'float': ('floading point number', validators.validate_float_number, None, None),
    'jsondict': ('JSON Dictionary', validators.validate_jsondict, forms.Textarea(attrs={'cols': 30, 'rows': 5}), None),
    'float': ('floading point number', validators.validate_float_number, None, None),
    'bool': ('On/Off', validators.validate_bool, None,  None),
    'platform': ('platform', validators.validate_nectar_platform, None,  None),
}

clean_rules = {
    'addition': validators.check_addition
}


def make_dynamic_field(parameter, **kwargs):

    if 'subtype' in parameter and parameter['subtype']:
        help_text = "%s (%s)" % (parameter['help_text'],
            subtype_validation[parameter['subtype']][0])
    else:
        help_text = parameter['help_text']
    # TODO: finish all types
    # TODO: requires knowledge of how ParameterNames represent types.
    field_params = {
        'required': False,
        'label': parameter['description'],
        'help_text': help_text
    }

    if parameter['subtype'] in  ['bdpurl', 'jsondict']:
        field_params['widget'] = subtype_validation[parameter['subtype']][2]
        field_params['max_length'] = subtype_validation[parameter['subtype']][3]

    if parameter['type'] == 2:
        if  parameter['initial']:
            field_params['initial'] = int(parameter['initial'])
        else:
            field_params['initial'] = 0

        if parameter['subtype'] == 'bool':
            field_params['initial'] = bool(parameter['initial'])
            field = forms.BooleanField(**field_params)
        else:
            field = forms.IntegerField(**field_params)
    if parameter['type'] == 4:
        logger.debug("found strlist")
        if parameter['subtype'] == "platform":

            field_params['initial'] = ""
            field_params['choices'] = ""
            # FIXME,TODO: compuation_ns value should be part of directive and
            # passed in, as some directives will only work with particular computation/*
            # categories.  Assume only nectar comp platforms ever allowed here.
            computation_ns = 'http://rmit.edu.au/schemas/platform/computation/nectar'
            if 'username' in kwargs:
                field_params['initial'] = platform.get_platform_name(kwargs['username'],
                 computation_ns)
                logger.debug("initial=%s" % field_params['initial'])
                # TODO: retrieve_platform_paramset should be an API call
                platform_name_choices = [(x['name'], x['name'])
                    for x in platform.retrieve_platform_paramsets(kwargs['username'],
                        computation_ns)]
                logger.debug("platform_name_choices=%s" % platform_name_choices)
                field_params['choices'] = platform_name_choices
        else:
            if parameter['initial']:
                field_params['initial'] = str(parameter['initial'])
            else:
                field_params['initial'] = ""
            if parameter['choices']:
                # TODO: We load the dynamic choices rather than use the choices field
                # in the model
                field_params['choices'] = ast.literal_eval(str(parameter['choices']))
            else:
                field_params['choices'] = []

        field = forms.ChoiceField(**field_params)
    else:
        field_params['initial'] = str(parameter['initial'])
        field = forms.CharField(**field_params)

    if 'subtype' in parameter and parameter['subtype']:
        field.validators.append(subtype_validation[parameter['subtype']][1])
    return field


def check_clean_rules(self, cleaned_data):
    for clean_rule_name, clean_rule in clean_rules.items():
        try:
            clean_rule(cleaned_data)
        except ValidationError, e:
            msg = "%s: %s" % (clean_rule_name, unicode(e))
            raise ValidationError(msg)
    return cleaned_data


def make_directive_form(**kwargs):
    fields = SortedDict()
    form_data = []
    if 'directive_params' in kwargs:
        for i, schema_data in enumerate(kwargs['directive_params']):
            logger.debug("schemadata=%s" % pformat(schema_data))
            for j, parameter in enumerate(schema_data['parameters']):
                logger.debug("parameter=%s" % parameter)
                # TODO: handle all possible types
                field_key = "%s/%s" % (schema_data['namespace'], parameter['name'])
                form_data.append((field_key, schema_data['description'] if not j else "", parameter['subtype'], parameter['hidefield'], parameter['hidecondition']))
                #fixme replce if else by fields[field_key] = make_dynamic_field(parameter) after unique key platform model is developed
                if 'username' in kwargs:
                    fields[field_key] = make_dynamic_field(parameter, username=kwargs['username'])
                else:
                    fields[field_key] = make_dynamic_field(parameter)
                logger.debug("field=%s" % fields[field_key].validators)
    logger.debug("fields = %s" % fields)
    #http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/
    ParamSetForm = type('ParamSetForm', (forms.BaseForm,),
                         {'base_fields': fields})
    #TODO: handle the initial values
    if 'request' in kwargs:
        pset_form = ParamSetForm(kwargs['request'], initial={})
    else:
        pset_form = ParamSetForm(initial={})

    def myclean(self):
        cleaned_data = super(ParamSetForm, self).clean()
        logger.debug("cleaning")
        return self.clean_rules(cleaned_data)
    import types
    pset_form.clean = types.MethodType(myclean, pset_form)
    pset_form.clean_rules = types.MethodType(check_clean_rules, pset_form)
    pset_form_data = zip(form_data, pset_form)
    logger.debug("pset_form_data = %s" % pformat(pset_form_data))
    return (pset_form, pset_form_data)


def get_test_schemas(direcive_id):

    return [
        {
        'description': 'desc of input1',
        'hidden': False,
        'id': 1,
        'name': 'input1',
        'namespace': 'http://rmit.edu.au/schemas/input1',
        'parameters': [
            {'pk': 1, 'name': 'arg1', 'help_text':'help for arg1', 'type': 1, 'initial': 1, 'subtype': 'natural'},
            {'pk': 2, 'name': 'arg2', 'help_text':'help for arg2', 'type': 2, 'initial': 'a', 'subtype': 'string'},
            {'pk': 3, 'name': 'arg3', 'help_text':'help for arg3','type': 2, 'initial': 'b', 'subtype': 'string'},
            {'pk': 4, 'name': 'arg4', 'help_text':'help for arg4','type': 1, 'initial': 3, 'subtype': 'whole'},
        ]},
        {
        'description': 'desc of input2',
        'hidden': False,
        'id': 2,
        'name': 'input2',
        'namespace': 'http://rmit.edu.au/schemas/input2',
        'parameters': [
            {'pk': 1, 'name': 'arg1', 'help_text':'help for arg1', 'type': 1, 'initial': 1, 'subtype': 'even'},
          {'pk': 2, 'name': 'arg2', 'help_text':'help for arg2', 'type': 1, 'initial': 2},
          {'pk': 3, 'name': 'arg3', 'help_text':'arg1+arg2', 'type': 1, 'initial': 2},

        ]}

        ]


def get_schema_info(request, schema_id):
    headers = {'content-type': 'application/json'}
    host_ip = "127.0.0.1"
    api_host = "http://%s" % host_ip
    url = "%s/api/v1/schema/%s/?format=json" % (api_host, schema_id)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug('r.json=%s' % r.json)
    logger.debug('r.text=%s' % r.text)
    logger.debug('r.headers=%s' % r.headers)
    return r.json()


def get_directive(request, directive_id):
    host_ip = "127.0.0.1"
    headers = {'content-type': 'application/json'}
    api_host = "http://%s" % host_ip
    url = "%s/api/v1/directive/%s?format=json" % (api_host, directive_id)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug('r.json=%s' % r.json)
    logger.debug('r.text=%s' % r.text)
    logger.debug('r.headers=%s' % r.headers)
    return r.json()


def get_directives(request):
    host_ip = "127.0.0.1"
    headers = {'content-type': 'application/json'}
    api_host = "http://%s" % host_ip
    url = "%s/api/v1/directive/?limit=0&format=json" % (api_host)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug("r.status_code=%s" % r.status_code)
    # logger.debug('r.json=%s' % r.json)
    # logger.debug('r.text=%s' % r.text)
    # logger.debug('r.headers=%s' % r.headers)
    return [ x for x in r.json()['objects'] ]


def get_directive_schemas(request, directive_id):
    host_ip = "127.0.0.1"
    headers = {'content-type': 'application/json'}
    api_host = "http://%s" % host_ip
    url = "%s/api/v1/directiveargset/?limit=0&directive=%s&format=json" % (api_host,
        directive_id)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug('r.json=%s' % r.json)
    logger.debug('r.text=%s' % r.text)
    logger.debug('r.headers=%s' % r.headers)
    schemas = [x['schema'] for x in sorted(r.json()['objects'],
                            key=lambda argset: int(argset['order']))]
    logger.debug("directiveargs= %s" % schemas)
    return schemas


def get_parameters(request, schema_id):
    host_ip = "127.0.0.1"
    headers = {'content-type': 'application/json'}
    api_host = "http://%s" % host_ip
    url = "%s/api/v1/parametername/?limit=0&schema=%s&format=json" % (api_host,
        schema_id)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug('r.json=%s' % r.json)
    logger.debug('r.text=%s' % pformat(r.text))
    logger.debug('r.headers=%s' % r.headers)
    schemas = [x for x in sorted(r.json()['objects'],
                                key=lambda ranking: ranking['ranking'])]
    return schemas


def get_directive_params(request, directive):
    directive_params = []
    for directive_schema in get_directive_schemas(request, directive['id']):
        logger.debug("directive_schema=%s" % directive_schema)
        schema_id = int([i for i in str(directive_schema).split('/') if i][-1])
        logger.debug("schema_id=%s" % schema_id)
        schema_info = get_schema_info(request, schema_id)
        logger.debug("schema_info=%s" % schema_info)
        parameters = get_parameters(request, schema_id)
        logger.debug("parameters=%s" % pformat(parameters))
        directive_params.append((schema_info, parameters))

    return directive_params

def get_from_api(request, resource_uri):
    headers = {'content-type': 'application/json'}
    host_ip = "127.0.0.1"
    api_host = "http://%s" % host_ip
    url = "%s%s/?format=json" % (api_host, resource_uri)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug('r.json=%s' % r.json)
    logger.debug('r.text=%s' % r.text)
    logger.debug('r.headers=%s' % r.headers)
    return r.json()



def add_form_fields(request, paramnameset):
    form_field_info = []
    for schema, paramnames in paramnameset:
        s = {}
        s['description'] = schema['description']
        s['name'] = schema['name']
        s['namespace'] = schema['namespace']
        p = []
        for pname  in paramnames:
            x = {}
            x['pk'] = pname['id']
            x['name'] = pname['name']
            x['description'] = pname['description']
            x['help_text'] = pname['help_text']
            x['type'] = pname['type']
            # TODO: initial values come from server initially,
            # but later may use values stored in the client to override these
            # to create different user preferences for different uses of the
            # schema
            x['initial'] = pname['initial']
            x['subtype'] = pname['subtype']
            x['choices'] = pname['choices']
            x['hidefield'] = pname['hidefield']
            x['hidecondition'] = pname['hidecondition']
            p.append(x)
        s['parameters'] = p
        form_field_info.append(s)
    return form_field_info



def submit_job(request, form, directive):

    #FIXME: consider using non-locahost URL for api_host
    api_host = "http://127.0.0.1"
    url = "%s/api/v1/context/?format=json" % api_host

    logger.debug("request.user.username=%s" % request.user.username)
    logger.debug("request.user.username=%s" % request.user.password)

    # pass the sessionid cookie through to the internal API
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    headers = {'content-type': 'application/json'}
    logger.debug("form.cleaned_data=%s" % pformat(form.cleaned_data))

    data = json.dumps(dict(form.cleaned_data.items() + [('smart_connector',directive)]))


    # data = json.dumps({'smart_connector': 'sweep',
    #             schemas['hrmc_schema'] + 'number_vm_instances': form.cleaned_data['number_vm_instances'],
    #             schemas['hrmc_schema'] + 'minimum_number_vm_instances': form.cleaned_data['minimum_number_vm_instances'],
    #             schemas['hrmc_schema'] + u'iseed': form.cleaned_data['iseed'],
    #             schemas['sweep_schema'] + 'input_location':  form.cleaned_data['input_location'],
    #             schemas['hrmc_schema'] + 'number_dimensions': form.cleaned_data['number_dimensions'],
    #             schemas['hrmc_schema'] + 'fanout_per_kept_result': form.cleaned_data['fanout_per_kept_result'],
    #             schemas['hrmc_schema'] + 'threshold': str(form.cleaned_data['threshold']),
    #             schemas['hrmc_schema'] + 'error_threshold': str(form.cleaned_data['error_threshold']),
    #             schemas['hrmc_schema'] + 'max_iteration': form.cleaned_data['max_iteration'],
    #             schemas['hrmc_schema'] + 'pottype': form.cleaned_data['pottype'],
    #             #'experiment_id': form.cleaned_data['experiment_id'],
    #             schemas['sweep_schema'] + 'sweep_map': form.cleaned_data['sweep_map'],
    #             schemas['sweep_schema'] + 'directive': 'hrmc',
    #             #'run_map': form.cleaned_data['run_map'],
    #             schemas['run_schema'] + 'run_map': "{}",
    #             schemas['system_schema'] + 'output_location': form.cleaned_data['output_location']})

    logger.debug("data=%s" % data)
    r = requests.post(url,
        data=data,
        headers=headers,
        cookies=cookies)

    logger.debug("r.status_code=%s" % r.status_code)
    logger.debug("r.text=%s" % r.text)
    logger.debug("r.headers=%s" % r.headers)

    if r.status_code != 201:
        error_message = ''
        messages.error(request, "Task Failed with status code %s: %s" % (r.status_code, r.text))
        return False
    else:
        messages.success(request, 'Job Created')

        logger.debug("r.json=%s" % r.json)

    logger.debug("r.status_code=%s" % r.status_code)
    logger.debug("r.text=%s" % r.text)
    logger.debug("r.headers=%s" % r.headers)
    if 'location' in r.headers:
        header_location = r.headers['location']
        logger.debug("header_location=%s" % header_location)
        new_context_uri = header_location[len(api_host):]
        logger.debug("new_context_uri=%s" % new_context_uri)
    return True




# class ContextList(ListView):
#     model = models.Context
#     template_name = "list_jobs.html"

#     def get_queryset(self):
#         return models.Context.objects.filter(owner__user=self.request.user).order_by('-id')

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_contexts(request):

    offset = 0
    page_size = 20

    if request.method == 'POST':
        contexts = []
        logger.debug("POST=%s" % request.POST)
        for key in request.POST:
            logger.debug("key=%s" % key)
            logger.debug("value=%s" % request.POST[key])
            if key.startswith("delete_"):
                try:
                    val = int(key.split('_')[-1])
                except ValueError, e:
                    logger.error(e)
                else:
                    contexts.append(val)
        logger.debug("contexts=%s" % contexts)
        # TODO: schedule celery tasks to delete each context, as background
        # process because stages may already have write lock on context.
        from bdphpcprovider.smartconnectorscheduler import tasks
        for context_id in contexts:
            logger.debug("scheduling deletion of %s" % context_id)
            tasks.delete.delay(context_id)
        messages.info(request, "Deletion of contexts %s has been scheduled" % ','.join([str(x) for x in contexts]))

    if 'offset' in request.GET:
        try:
            offset = int(request.GET.get('offset'))
        except ValueError:
            pass
    if offset < 0:
        offset = 0

    limit = page_size
    #if 'limit' in request.GET:
    #    try:
    #         limit = int(request.GET.get('limit'))
    #     except ValueError:
    #         pass
    logger.debug("offset=%s" % offset)
    logger.debug("limit=%s" % limit)

    host_ip = "127.0.0.1"
    headers = {'content-type': 'application/json'}
    api_host = "http://%s" % host_ip
    url = "%s/api/v1/contextmessage/?limit=%s&offset=%s&format=json" % (api_host, limit, offset)
    cookies = dict(request.COOKIES)
    logger.debug("cookies=%s" % cookies)
    r = requests.get(url, headers=headers, cookies=cookies)
    # FIXME: need to check for status_code and handle failures such
    # as 500 - lack of disk space at mytardis
    logger.debug('URL=%s' % url)
    logger.debug("r.status_code=%s" % r.status_code)
    # logger.debug('r.json=%s' % r.json)
    # logger.debug('r.text=%s' % r.text)
    # logger.debug('r.headers=%s' % r.headers)

    import dateutil.parser
    object_list = []
    logger.debug("r.json()=%s" % pformat(r.json()))
    for x in r.json()['objects']:
        logger.debug("x=%s" % pformat(x))
        contextid = contextdeleted = contextcreated = ""
        directive_name = directive_desc = ""
        if 'context' in x and x['context']:
            if 'id' in x['context']:
                contextid = x['context']['id']
            if 'deleted' in x['context']:
                contextdeleted = x['context']['deleted']
            if 'created' in x['context']:
                    contextcreated = x['context']['created']
            if 'directive' in x['context'] and x['context']['directive']:
                if 'name' in x['context']['directive']:
                    directive_name = x['context']['directive']['name']
                if 'description' in x['context']['directive']:
                    directive_desc = x['context']['directive']['description']

        obj = []
        obj.append(contextid)
        obj.append(contextdeleted)
        obj.append(dateutil.parser.parse(contextcreated))
        obj.append(x['message'])
        obj.append(directive_name)
        obj.append(directive_desc)
        obj.append(reverse('contextview', kwargs={'pk': contextid}))
        object_list.append(obj)

    meta = r.json()['meta']

    # if offset > (meta['total_count'] - limit):
    #     offset = 0

    pages = []
    number_pages = meta['total_count'] / page_size
    for off in range(0, number_pages + 1):
        pages.append(page_size * off)

    logger.debug("pages=%s" % pages)

    return render_to_response(
                       'list_jobs.html',
                       {'object_list': object_list,
                       'limit': limit,
                       'page_offsets': pages,
                       'total_count': int(meta['total_count']),
                       'offset': int(offset)},
                       context_instance=RequestContext(request))


def submit_directive(request, directive_id):
    try:
        directive_id = int(directive_id)
    except ValueError:
        return redirect("makedirective")
    logger.debug("directive_id=%s" % directive_id)
    directives = get_directives(request)
    logger.debug('directives=%s' % directives)
    if directive_id == 0:
        for x in directives:
            if not x['hidden']:
                directive = x
                directive_id = x[u'id']
                break
        else:
            return redirect("home")
    else:
        for x in directives:
            logger.debug(x['id'])
        try:
            directive = [x for x in directives if x[u'id'] == directive_id][0]
        except IndexError:
            return redirect("home")
            # TODO: handle
            raise

    directive_params = get_directive_params(request, directive)
    logger.debug("directive_params=%s" % pformat(directive_params))
    directive_params = add_form_fields(request, directive_params)
    logger.debug("directive_params=%s" % pformat(directive_params))
    if request.method == 'POST':
        form, form_data = make_directive_form(
            request=request.POST,
            directive_params=directive_params,
            username=request.user.username)
        logger.debug("form=%s" % pformat(form))
        logger.debug("form_data=%s" % pformat(form_data))
        if form.is_valid():
            logger.debug("form result =%s" % form.cleaned_data)
            # schemas={
            # 'hrmc_schema': "http://rmit.edu.au/schemas/input/hrmc/",
            # 'system_schema': "http://rmit.edu.au/schemas/input/system",
            # 'run_schema': "http://rmit.edu.au/schemas/stages/run/",
            # 'sweep_schema': "http://rmit.edu.au/schemas/input/sweep/",
            # }
            valid = submit_job(request, form, directive['name'])
            if valid:
                return redirect("hrmcjob-list")
            else:
                logger.debug("invalid")
                redirect("makedirective", directive_id=directive_id)
        else:
            messages.error(request, "Job Failed because of validation errors. See below")
    else:
        form, form_data = make_directive_form(directive_params=directive_params, username=request.user.username)

    # TODO: generalise
    if directive['name'] == "sweep":
        for d in directives:
            if d['name'] == "hrmc":
                directive['name'] = d['name']
                directive['description'] = d['description']
                break

    return render_to_response(
                       'parameters.html',
                       {
                           'directives': [x for x in directives if not x['hidden']],
                           'directive': directive,
                           'form': form,
                           'formdata': form_data,
                           'longfield': [x for (x,y) in subtype_validation.items() if y[2] is not None]
                        },
                       context_instance=RequestContext(request))


