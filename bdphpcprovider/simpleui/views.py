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
import json
import requests
from urllib2 import URLError, HTTPError


logger = logging.getLogger(__name__)

from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from bdphpcprovider.simpleui.hrmc.hrmcsubmit import HRMCSubmitForm
from bdphpcprovider.simpleui.makeform import MakeSubmitForm
from bdphpcprovider.simpleui.sweepform import SweepSubmitForm
from bdphpcprovider.simpleui.hrmc.copy import CopyForm
from bdphpcprovider.simpleui.ncicomputationplatform import NCIComputationPlatformForm
from bdphpcprovider.simpleui.nectarcomputationplatform import NeCTARComputationPlatformForm

#TODO,FIXME: simpleui shouldn't refer to anything in smartconnectorscheduler
#and should be using its own models and use the REST API for all information.

from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError


from django.http import Http404
from django.views.generic.edit import FormView

from django.views.generic import DetailView

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, render

def computation_platform_settings(request):
    nciform = NCIComputationPlatformForm()
    nectarform = NeCTARComputationPlatformForm()
    if request.method == "POST":
        nciform = NCIComputationPlatformForm(request.POST)
        nectarform = NeCTARComputationPlatformForm(request.POST)
        if nciform.is_valid():
            logger.debug('nci')
            logger.debug('operation=%s' % nciform.cleaned_data['operation'])
            return HttpResponseRedirect('/accounts/settings/')
        elif nectarform.is_valid():
            logger.debug('nectar')
            logger.debug('operation=%s' % nectarform.cleaned_data['operation'])
            return HttpResponseRedirect('/accounts/profile/')
    elif request.method == "GET":
        #FIXME: consider using non-locahost URL for api_host
        api_host = "http://127.0.0.1"
        url = "%s/api/v1/platformparameter/?format=json&schema=http://rmit.edu.au/schemas/platform/computation" % api_host
        cookies = dict(request.COOKIES)
        logger.debug("cookies=%s" % cookies)
        headers = {'content-type': 'application/json'}
        try:
            #response = urlopen(req)
            r = requests.get(url,
            headers=headers,
            cookies=cookies)
        except HTTPError as e:
            logger.debug( 'The server couldn\'t fulfill the request. %s' % e)
            logger.debug( 'Error code: ', e.code)
        except URLError as e:
            logger.debug( 'We failed to reach a server. %s' % e)
            logger.debug( 'Reason: ', e.reason)
        else:
            logger.debug('everything is fine')
            #logger.debug(r.text)
            #logger.debug(r.json())
            GET_data = r.json()
            computation_platforms, all_headers = filter_computation_platforms(GET_data)
            logger.debug(computation_platforms)
    return render(request, 'accountsettings/computationplatform.html',
                              {'nci_form': nciform, 'nectar_form': nectarform,
                               'computation_platforms': computation_platforms,
                               'all_headers': all_headers})

#fixme revise this method
def filter_computation_platforms(GET_json_data):
    platform_parameters_objects = GET_json_data['objects']
    computation_platforms = {}
    test={}

    for i in platform_parameters_objects:
        schema = i['paramset']['platform']['schema_namespace_prefix']
        computation_platforms[schema] = {}

    for i in platform_parameters_objects:
        schema = i['paramset']['platform']['schema_namespace_prefix']
        paramset_id = i['paramset']['id']
        computation_platforms[schema][paramset_id] = {}

    logger.debug(computation_platforms)
    for i in platform_parameters_objects:
        schema = i['paramset']['platform']['schema_namespace_prefix']
        paramset_id = i['paramset']['id']
        name = i['name']['name']
        value = i['value']
        computation_platforms[schema][paramset_id][name] = value

    headers={}
    all_headers={}
    for i, j in computation_platforms.items():
        headers[i] = []

        params = []
        for a, b in j.items():
            for c, d in b.items():
                params.append(c)
            break
        headers[i] = params
        all_headers[tuple(params)] = j
    logger.debug('----')
    logger.debug(all_headers)


    return computation_platforms, all_headers

class UserProfileParameterListView(ListView):
    model = models.UserProfileParameter
    template_name = "list_userprofileparameter.html"

    def get_queryset(self):
            return models.UserProfileParameter.objects.filter(paramset__user_profile__user=self.request.user)


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
                res2[cp.name.name] = [cp.value, cp.name.help_text]
                #res2[cp.name.name] = [cp.value, "hello"]
            res[cps.schema.namespace] = res2
        context['settings'] = res
        return context

    def get_object(self):
            object = super(ContextView, self).get_object()
            if object.owner.user == self.request.user:
                return object
            else:
                raise Http404


class HRMCSubmitFormView(FormView):
    template_name = 'hrmc.html'
    form_class = HRMCSubmitForm
    success_url = '/jobs'
    hrmc_schema = "http://rmit.edu.au/schemas/hrmc/"
    system_schema = "http://rmit.edu.au/schemas/system/misc/"

    initial = {'number_vm_instances': 8,
               'minimum_number_vm_instances': 1,
        'iseed': 42,
        'input_location': 'file://127.0.0.1/myfiles/input',
        'number_dimensions': 2,
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

    hrmc_schema = "http://rmit.edu.au/schemas/hrmc/"
    system_schema = "http://rmit.edu.au/schemas/system/misc/"
    run_schema = "http://rmit.edu.au/schemas/stages/run/"
    sweep_schema = "http://rmit.edu.au/schemas/stages/sweep/"

    initial = {'number_vm_instances': 2,
               'minimum_number_vm_instances': 1,
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
        #FIXME: consider using non-locahost URL for api_host
        api_host = "http://127.0.0.1"
        url = "%s/api/v1/context/?format=json" % api_host

        logger.debug("self.request.user.username=%s" % self.request.user.username)
        logger.debug("self.request.user.username=%s" % self.request.user.password)

        # pass the sessionid cookie through to the internal API
        cookies = dict(self.request.COOKIES)
        logger.debug("cookies=%s" % cookies)
        headers = {'content-type': 'application/json'}
        data = json.dumps({'smart_connector': 'sweep',
                    self.hrmc_schema + 'number_vm_instances': form.cleaned_data['number_vm_instances'],
                    self.hrmc_schema + 'minimum_number_vm_instances': form.cleaned_data['minimum_number_vm_instances'],
                    self.hrmc_schema + u'iseed': form.cleaned_data['iseed'],
                    self.hrmc_schema + 'maximum_retry': form.cleaned_data['maximum_retry'],
                    self.hrmc_schema + 'reschedule_failed_processes': form.cleaned_data['reschedule_failed_processes'],
                    self.sweep_schema + 'input_location':  form.cleaned_data['input_location'],
                    self.hrmc_schema + 'number_dimensions': form.cleaned_data['number_dimensions'],
                    self.hrmc_schema + 'fanout_per_kept_result': form.cleaned_data['fanout_per_kept_result'],
                    self.hrmc_schema + 'threshold': str(form.cleaned_data['threshold']),
                    self.hrmc_schema + 'error_threshold': str(form.cleaned_data['error_threshold']),
                    self.hrmc_schema + 'max_iteration': form.cleaned_data['max_iteration'],
                    self.hrmc_schema + 'pottype': form.cleaned_data['pottype'],
                    #'experiment_id': form.cleaned_data['experiment_id'],
                    self.sweep_schema + 'sweep_map': form.cleaned_data['sweep_map'],
                    self.sweep_schema + 'directive': 'hrmc',
                    #'run_map': form.cleaned_data['run_map'],
                    self.run_schema + 'run_map': "{}",
                    self.system_schema + 'output_location': form.cleaned_data['output_location']})

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

        return super(SweepSubmitFormView, self).form_valid(form)


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
