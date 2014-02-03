
# Copyright (C) 2014, RMIT University

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
from pprint import pformat

from django.views.generic import FormView
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from .forms import (
    NewDirectiveForm1,
    NewDirectiveForm2,
    SchemaFormSet,
    ParameterNameFormSet,
    StageParamsFormSet,
    InputSchemaForm,
    StageSetForm)

logger = logging.getLogger(__name__)


class AddDirective1View(FormView):
    template_name = 'wizard/create_directive1.html'
    form_class = NewDirectiveForm1

    def get_context_data(self, **kwargs):
        context = super(AddDirective1View, self).get_context_data(**kwargs)
        if self.request.POST:
            context['formset_schema'] = SchemaFormSet(self.request.POST,
                                                      prefix="schemas")
            # context['formset_stageparams'] = StageParamsFormSet(self.request.POST,
            #                                                 prefix="dirargs")
            context['formset_params'] = ParameterNameFormSet(self.request.POST,
                                                             prefix="param")
            # context['form_input_schemas'] = InputSchemaForm(self.request.POST)
            # context['form_stage_set'] = StageSetForm(self.request.POST)

        else:
            context['formset_schema'] = SchemaFormSet(prefix="schemas")
            # context['formset_stageparams'] = StageParamsFormSet(prefix="dirargs")
            context['formset_params'] = ParameterNameFormSet(prefix="param")
            # context['form_input_schemas'] = InputSchemaForm()
            # context['form_stage_set'] = StageSetForm()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset_schema = context['formset_schema']
        # formset_stageparams = context['formset_stageparams']
        formset_params = context['formset_params']
        # form_input_schemas = context['form_input_schemas']
        # form_stage_set = context['form_stage_set']
        logger.debug("form_valid?")
        if all([x.is_valid() for x in [
                form,
                formset_schema,
                # formset_stageparams,
                formset_params,
                # form_input_schemas,
                # form_stage_set
                ]]):

            debug_text = []
            res = {}
            if 'name' in form.cleaned_data:
                res['name'] = form.cleaned_data['name']
            if 'description' in form.cleaned_data:
                res['description'] = form.cleaned_data['description']
            debug_text.append(res)

            for i, f1 in enumerate(formset_schema):
                try:
                    r = f1.cleaned_data
                except AttributeError:
                    # TODO: why does this happen?
                    continue
                if 'DELETE' in r:
                    if r['DELETE']:
                        continue
                res = [r]
                for j, f2 in enumerate(formset_params):
                    try:
                        r = f2.cleaned_data
                    except AttributeError:
                        # TODO: why does this happen?
                        continue
                    if 'DELETE' in r:
                        if r['DELETE']:
                            continue
                    if ('param-%s-parent' % j) in self.request.POST:
                        parent = self.request.POST['param-%s-parent' % j]

                        if int(parent) == i:
                            f2clean = f2.cleaned_data
                            res.append(dict(f2clean))
                debug_text.append(res)

            # res = []
            # for i, f1 in enumerate(formset_stageparams):
            #     try:
            #         r = f1.cleaned_data
            #     except AttributeError:
            #         # TODO: why does this happen?
            #         continue
            #     if 'DELETE' in r:
            #         if r['DELETE']:
            #             continue
            #     if 'namespace' in r:
            #         res.append(r['namespace'])

            # debug_text.append(res)

            # r1 = str(form_input_schemas.cleaned_data)
            # debug_text.append(r1)
            # print debug_text

            #FIXME: consider using non-locahost URL for api_host
            if (False):
                api_host = "http://127.0.0.1"
                url = "%s/coreapi/directive" % api_host
                logger.debug("request.user.username=%s" % self.request.user.username)
                logger.debug("self.request.user.username=%s" % self.request.user.password)
                # pass the sessionid cookie through to the internal API
                cookies = dict(self.request.COOKIES)
                logger.debug("cookies=%s" % cookies)
                headers = {'content-type': 'application/json'}

                # data = {}
                # data_list = ''

                # for f in ['form', 'formset_schema', 'formset_stageparams',
                #     'formset_params', 'form_input_schemas', 'form_stage_set']:
                #     if getattr(self, f).cleaned_data:
                #         data_list.append((f, getattr(self, f)()))

                # data = json.dumps(dict(data_list))

                data = {}
                if form.cleaned_data:
                    data['form'] = form.cleaned_data
                if formset_schema.cleaned_data:
                    data['formset_schema'] = formset_schema.cleaned_data
                if formset_params.cleaned_data:
                    data['formset_params'] = formset_params.cleaned_data

                data = json.dumps(data)

                # data = json.dumps({
                #     'form': form,
                #     'formset_schema': dict(formset_schema.cleaned_data),
                #     'formset_stageparams': dict(formset_stageparams.cleaned_data),
                #     'formset_params': dict(formset_params.cleaned_data),
                #     'form_input_schemas': dict(form_input_schemas.cleaned_data),
                #     'form_stage_set': dict(form_stage_set.cleaned_data)})
                logger.debug("data=%s" % data)

                r = requests.post(url,
                    data=data,
                    headers=headers,
                    cookies=cookies)
                logger.debug("r.status_code=%s" % r.status_code)
                logger.debug("r.text=%s" % r.text)
                logger.debug("r.headers=%s" % r.headers)
                if r.status_code != 201:
                    logger.error(self.request, "Task Failed with status code %s: %s"
                        % (r.status_code, r.text))
                    return False
                logger.debug("r.json=%s" % r.json)
                logger.debug("r.status_code=%s" % r.status_code)
                logger.debug("r.text=%s" % r.text)
                logger.debug("r.headers=%s" % r.headers)
                # if 'location' in r.headers:
                #     header_location = r.headers['location']
                #     logger.debug("header_location=%s" % header_location)
                #     new_context_uri = header_location[len(api_host):]
                #     logger.debug("new_context_uri=%s" % new_context_uri)
                #     if str(new_context_uri)[-1] == '/':
                #         job_id = str(new_context_uri).split('/')[-2:-1][0]
                #     else:
                #         job_id = str(new_context_uri).split('/')[-1]
                #     logger.debug("job_id=%s" % job_id)
            logger.debug("passes")
            return HttpResponseRedirect(reverse('wizard2')) # Redirect after POST
            # return render_to_response(
            #     'wizard/create_directive2.html',
            #         {'debug_text': str(debug_text)},
            #             context_instance=self.RequestContext(self.request))
        else:
            logger.debug("errors")
            new_context = self.get_context_data(form=form)
            # debug_text = str(pformat(self.request.POST)) + "hgello"
            return HttpResponseRedirect(reverse('wizard'))
            # return self.render_to_response(new_context.update({'debug_text': "ERROR:" + debug_text}))

            # debug_text = str(pformat(form.errors))  \
            #     + str(pformat(formset_schema.errors)) \
            #     + str(pformat(formset_stageparams.errors)) \
            #     + str(pformat(formset_params.errors)) \
            #     + str(pformat(self.request.POST))
            # print debug_text
            # return render_to_response(
            #                    'wizard/create_directive1.html',
            #                    {'debug_text': "ERROR:" + debug_text},
            #                    context_instance=RequestContext(self.request))


class AddDirective2View(FormView):

    template_name = 'wizard/create_directive2.html'
    form_class = NewDirectiveForm2

    def get_context_data(self, **kwargs):
        context = super(AddDirective2View, self).get_context_data(**kwargs)
        if self.request.POST:
            # context['formset_schema'] = SchemaFormSet(self.request.POST,
            #                                           prefix="schemas")
            context['formset_stageparams'] = StageParamsFormSet(self.request.POST,
                                                            prefix="dirargs")
            # context['formset_params'] = ParameterNameFormSet(self.request.POST,
            #                                                  prefix="param")
            context['form_input_schemas'] = InputSchemaForm(self.request.POST)
            context['form_stage_set'] = StageSetForm(self.request.POST)

        else:
            # context['formset_schema'] = SchemaFormSet(prefix="schemas")
            context['formset_stageparams'] = StageParamsFormSet(prefix="dirargs")
            # context['formset_params'] = ParameterNameFormSet(prefix="param")
            context['form_input_schemas'] = InputSchemaForm()
            context['form_stage_set'] = StageSetForm()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        # formset_schema = context['formset_schema']
        formset_stageparams = context['formset_stageparams']
        # formset_params = context['formset_params']
        form_input_schemas = context['form_input_schemas']
        form_stage_set = context['form_stage_set']

        if all([x.is_valid() for x in [
                form,
                # formset_schema,
                formset_stageparams,
                # formset_params,
                form_input_schemas,
                form_stage_set]]):

            debug_text = []
            res = {}
            if 'name' in form.cleaned_data:
                res['name'] = form.cleaned_data['name']
            if 'description' in form.cleaned_data:
                res['description'] = form.cleaned_data['description']
            debug_text.append(res)

            # for i, f1 in enumerate(formset_schema):
            #     try:
            #         r = f1.cleaned_data
            #     except AttributeError:
            #         # TODO: why does this happen?
            #         continue
            #     if 'DELETE' in r:
            #         if r['DELETE']:
            #             continue
            #     res = [r]
            #     for j, f2 in enumerate(formset_params):
            #         try:
            #             r = f2.cleaned_data
            #         except AttributeError:
            #             # TODO: why does this happen?
            #             continue
            #         if 'DELETE' in r:
            #             if r['DELETE']:
            #                 continue
            #         if ('param-%s-parent' % j) in self.request.POST:
            #             parent = self.request.POST['param-%s-parent' % j]

            #             if int(parent) == i:
            #                 f2clean = f2.cleaned_data
            #                 res.append(dict(f2clean))
            #     debug_text.append(res)

            res = []
            for i, f1 in enumerate(formset_stageparams):
                try:
                    r = f1.cleaned_data
                except AttributeError:
                    # TODO: why does this happen?
                    continue
                if 'DELETE' in r:
                    if r['DELETE']:
                        continue
                if 'namespace' in r:
                    res.append(r['namespace'])

            debug_text.append(res)

            r1 = str(form_input_schemas.cleaned_data)
            debug_text.append(r1)
            print debug_text

            #FIXME: consider using non-locahost URL for api_host
            api_host = "http://127.0.0.1"
            url = "%s/coreapi/directive" % api_host
            logger.debug("request.user.username=%s" % self.request.user.username)
            logger.debug("self.request.user.username=%s" % self.request.user.password)
            # pass the sessionid cookie through to the internal API
            cookies = dict(self.request.COOKIES)
            logger.debug("cookies=%s" % cookies)
            headers = {'content-type': 'application/json'}

            # data = {}
            # data_list = ''

            # for f in ['form', 'formset_schema', 'formset_stageparams',
            #     'formset_params', 'form_input_schemas', 'form_stage_set']:
            #     if getattr(self, f).cleaned_data:
            #         data_list.append((f, getattr(self, f)()))

            # data = json.dumps(dict(data_list))

            data = {}
            if form.cleaned_data:
                data['form'] = form.cleaned_data
            # if formset_schema.cleaned_data:
            #     data['formset_schema'] = formset_schema.cleaned_data
            if formset_stageparams.cleaned_data:
                data['formset_stageparams'] = formset_stageparams.cleaned_data
            # if formset_params.cleaned_data:
            #     data['formset_params'] = formset_params.cleaned_data
            if form_input_schemas.cleaned_data:
                data['form_input_schemas'] = form_input_schemas.cleaned_data
            if form_stage_set.cleaned_data:
                data['form_stage_set'] = form_stage_set.cleaned_data

            data = json.dumps(data)

            # data = json.dumps({
            #     'form': form,
            #     'formset_schema': dict(formset_schema.cleaned_data),
            #     'formset_stageparams': dict(formset_stageparams.cleaned_data),
            #     'formset_params': dict(formset_params.cleaned_data),
            #     'form_input_schemas': dict(form_input_schemas.cleaned_data),
            #     'form_stage_set': dict(form_stage_set.cleaned_data)})
            logger.debug("data=%s" % data)

            r = requests.post(url,
                data=data,
                headers=headers,
                cookies=cookies)
            logger.debug("r.status_code=%s" % r.status_code)
            logger.debug("r.text=%s" % r.text)
            logger.debug("r.headers=%s" % r.headers)
            if r.status_code != 201:
                logger.error(self.request, "Task Failed with status code %s: %s"
                    % (r.status_code, r.text))
                return False
            logger.debug("r.json=%s" % r.json)
            logger.debug("r.status_code=%s" % r.status_code)
            logger.debug("r.text=%s" % r.text)
            logger.debug("r.headers=%s" % r.headers)
            # if 'location' in r.headers:
            #     header_location = r.headers['location']
            #     logger.debug("header_location=%s" % header_location)
            #     new_context_uri = header_location[len(api_host):]
            #     logger.debug("new_context_uri=%s" % new_context_uri)
            #     if str(new_context_uri)[-1] == '/':
            #         job_id = str(new_context_uri).split('/')[-2:-1][0]
            #     else:
            #         job_id = str(new_context_uri).split('/')[-1]
            #     logger.debug("job_id=%s" % job_id)

            return render_to_response(
                'wizard/create_directive2.html',
                    {'debug_text': str(debug_text)},
                        context_instance=self.RequestContext(self.request))
        else:
            new_context = self.get_context_data(form=form)
            debug_text = str(pformat(self.request.POST)) + "hgello"
            return self.render_to_response(new_context.update({'debug_text': "ERROR:" + debug_text}))

            debug_text = str(pformat(form.errors))  \
                + str(pformat(formset_stageparams.errors)) \
                + str(pformat(formset_params.errors)) \
                + str(pformat(self.request.POST))
            print debug_text
            return render_to_response(
                               'wizard/create_directive2.html',
                               {'debug_text': "ERROR:" + debug_text},
                               context_instance=RequestContext(self.request))
