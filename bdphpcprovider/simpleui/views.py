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
from pprint import pformat
import json
import requests
import logging.config
logger = logging.getLogger(__name__)

from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from django.contrib.auth import logout
from django.http import HttpResponseRedirect


from bdphpcprovider.simpleui.hrmc.hrmcsubmit import HRMCSubmitForm
from bdphpcprovider.simpleui.sweepform import SweepSubmitForm
from bdphpcprovider.simpleui.hrmc.copy import CopyForm

#TODO,FIXME: simpleui shouldn't refer to anything in smartconnectorscheduler
#and should be using its own models and use the REST API for all information.

from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler.errors import InvalidInputError


from django.http import Http404
from django.views.generic.edit import FormView

from django.views.generic import DetailView


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


from django.views.generic.base import TemplateView


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

    initial = {'number_vm_instances': 8,
        'iseed': 42,
        'input_location': 'file://127.0.0.1/myfiles/input',
        'number_of_dimensions': 2,
        'threshold': "[2]",
        'error_threshold': "0.03",
        'max_iteration': 10,
        'pottype': 1,
        'experiment_id': 0

        }

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        platform = 'nectar'
        directive_name = "smartconnector_hrmc"
        logger.debug("%s" % directive_name)
        directive_args = []

        directive_args.append(
            ['',
                ['http://rmit.edu.au/schemas/hrmc',
                    ('number_vm_instances',
                        form.cleaned_data['number_vm_instances']),
                    (u'iseed', form.cleaned_data['iseed']),
                    ('input_location',  form.cleaned_data['input_location']),
                    ('number_dimensions', form.cleaned_data['number_of_dimensions']),
                    ('threshold', str(form.cleaned_data['threshold'])),
                    ('error_threshold', str(form.cleaned_data['error_threshold'])),
                    ('max_iteration', form.cleaned_data['max_iteration']),
                    ('pottype', form.cleaned_data['pottype']),
                    ('experiment_id', form.cleaned_data['experiment_id'])
                ]
            ])

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {
        u'system': u'settings',
        u'output_location': os.path.join('hrmcrun')}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        # An example of using the REST API to control the system, rather than
        # talking directly to the models in smartconnectorscheduler.
        # TODO: do the same for other parts of UI, e.g., user settings form
        # should call user_setttings API endpoint.

        api_host = "http://127.0.0.1"
        url = "%s/api/v1/context/?format=json" % api_host

        logger.debug("self.request.user.username=%s" % self.request.user.username)
        logger.debug("self.request.user.username=%s" % self.request.user.password)

        # pass the sessionid cookie through to the internal API
        cookies = dict(self.request.COOKIES)
        logger.debug("cookies=%s" % cookies)
        headers = {'content-type': 'application/json'}
        data = json.dumps({'number_vm_instances': form.cleaned_data['number_vm_instances'],
                    u'iseed': form.cleaned_data['iseed'],
                    'input_location':  form.cleaned_data['input_location'],
                    'number_dimensions': form.cleaned_data['number_of_dimensions'],
                    'threshold': str(form.cleaned_data['threshold']),
                    'error_threshold': str(form.cleaned_data['error_threshold']),
                    'max_iteration': form.cleaned_data['max_iteration'],
                    'pottype': form.cleaned_data['pottype'],
                    'experiment_id': form.cleaned_data['experiment_id'],
                    'output_location': os.path.join('hrmcrun')})

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

    initial = {'number_vm_instances': 1,
        'iseed': 42,
        'input_location': 'file://127.0.0.1/myfiles/input',
        'number_of_dimensions': 1,
        'threshold': "[1]",
        'error_threshold': "0.03",
        'max_iteration': 2,
        'pottype': 1,
        'sweep_map': '{"var1": [3, 7], "var2": [1, 2]}',
        'run_map': '{}',
        'experiment_id': 0

        }

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        platform = 'local'
        directive_name = "sweep"
        logger.debug("%s" % directive_name)
        directive_args = []

        directive_args.append(
            ['',
                ['http://rmit.edu.au/schemas/hrmc',
                    ('number_vm_instances',
                        form.cleaned_data['number_vm_instances']),
                    (u'iseed', form.cleaned_data['iseed']),
                    ('input_location',  ''),
                    ('number_dimensions', form.cleaned_data['number_of_dimensions']),
                    ('threshold', str(form.cleaned_data['threshold'])),
                    ('error_threshold', str(form.cleaned_data['error_threshold'])),
                    ('max_iteration', form.cleaned_data['max_iteration']),
                    ('experiment_id', form.cleaned_data['experiment_id']),
                    ('pottype', form.cleaned_data['pottype'])],
                ['http://rmit.edu.au/schemas/stages/sweep',
                    ('input_location',  form.cleaned_data['input_location']),
                    ('sweep_map', form.cleaned_data['sweep_map']),
                ],
                ['http://rmit.edu.au/schemas/stages/run',
                    ('run_map', form.cleaned_data['run_map'])
                ]
            ])

        logger.debug("form=%s" % pformat(form.cleaned_data))

        logger.debug("directive_args=%s" % directive_args)

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {
            u'system': u'settings',
            u'output_location': 'sweephrmc'}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        # FIXME: we should be sending this request to scheduler API using
        # POST, to keep separation of concerns.  See sweep for example.

        try:
            (run_settings, command_args, run_context) \
                = hrmcstages.make_runcontext_for_directive(
                platform,
                directive_name,
                directive_args, system_settings, self.request.user.username)

        except InvalidInputError, e:
            return HttpResponse(str(e))

        return super(SweepSubmitFormView, self).form_valid(form)


class CopyFormView(FormView):
    template_name = 'copy.html'
    form_class = CopyForm
    success_url = '/jobs'

    initial = {'source_bdp_url': 'file://local@127.0.0.1/myfiles/sourcedir',
        'destination_bdp_url': 'file://local@127.0.0.1/myfiles/destdir',
        }

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        platform = 'nci'  # FIXME: should be local
        directive_name = "copydir"
        logger.debug("%s" % directive_name)
        directive_args = []
        directive_args.append([form.cleaned_data['source_bdp_url'], []])
        directive_args.append([form.cleaned_data['destination_bdp_url'], []])

        # make the system settings, available to initial stage and merged with run_settings
        system_dict = {u'system': u'settings'}
        system_settings = {u'http://rmit.edu.au/schemas/system/misc': system_dict}

        logger.debug("directive_name=%s" % directive_name)
        logger.debug("directive_args=%s" % directive_args)

        try:
            (run_settings, command_args, run_context) \
                = hrmcstages.make_runcontext_for_directive(
                platform,
                directive_name,
                directive_args, system_settings, self.request.user.username)

        except InvalidInputError, e:
            return HttpResponse(str(e))

        return super(CopyFormView, self).form_valid(form)
