
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

from django.views.generic import FormView
from django.shortcuts import redirect

from django.shortcuts import render_to_response
from django.template import RequestContext
from pprint import pformat

from .forms import NewDirectiveForm1, SchemaFormSet, ParameterNameFormSet, DirectiveArgFormSet


class AddDirective1View(FormView):
    template_name = 'wizard/create_directive1.html'
    form_class = NewDirectiveForm1

    def get_context_data(self, **kwargs):
        context = super(AddDirective1View, self).get_context_data(**kwargs)
        if self.request.POST:
            context['formset_schema'] = SchemaFormSet(self.request.POST,
                                                      prefix="schemas")
            context['formset_dirarg'] = DirectiveArgFormSet(self.request.POST,
                                                            prefix="dirargs")
            context['formset_params'] = ParameterNameFormSet(self.request.POST,
                                                             prefix="param")
        else:
            context['formset_schema'] = SchemaFormSet(prefix="schemas")
            context['formset_dirarg'] = DirectiveArgFormSet(prefix="dirargs")
            context['formset_params'] = ParameterNameFormSet(prefix="param")

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset_schema = context['formset_schema']
        formset_dirarg = context['formset_dirarg']
        formset_params = context['formset_params']

        if (form.is_valid()
            and formset_schema.is_valid()
            and formset_dirarg.is_valid()
            and formset_params.is_valid()):

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

            res = []
            for i, f1 in enumerate(formset_dirarg):
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
            print debug_text

            return render_to_response(
                'wizard/create_directive1.html',
                    {'debug_text': str(debug_text)},
                        context_instance=RequestContext(self.request))
        else:
            new_context = self.get_context_data(form=form)
            debug_text = str(pformat(self.request.POST)) + "hgello"
            return self.render_to_response(new_context.update({'debug_text': "ERROR:" + debug_text}))

            debug_text = str(pformat(form.errors))  \
                + str(pformat(formset_schema.errors)) \
                + str(pformat(formset_dirarg.errors)) \
                + str(pformat(formset_params.errors)) \
                + str(pformat(self.request.POST))
            print debug_text
            return render_to_response(
                               'wizard/create_directive1.html',
                               {'debug_text': "ERROR:" + debug_text},
                               context_instance=RequestContext(self.request))

