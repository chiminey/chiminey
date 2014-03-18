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
import abc
from chiminey.smartconnectorscheduler import models
from chiminey.initialisation.chimineyinitial import register_schemas

RMIT_SCHEMA = "http://rmit.edu.au/schemas"
SWEEP_SCHEMA = RMIT_SCHEMA + "/input/sweep"
logger = logging.getLogger(__name__)


class CoreInitial(object):
    def __init__(self):
        self.directive_name = 'core'

    def get_parent_name(self):
        return "%s_connector" % self.directive_name

    def define_parent_stage(self):
        parent = "chiminey.corestages.parent.Parent"
        parent_stage, _ = models.Stage.objects.get_or_create(
            name=self.get_parent_name(),
            description="This is the core parent stage",
            package=parent,
            order=0)
        return parent_stage

    def define_create_stage(self):
        create_package = "chiminey.corestages.create.Create"
        create_stage, _ = models.Stage.objects.get_or_create(name="create",
            description="This is the core create stage",
            parent=self.define_parent_stage(),
            package=create_package,
            order=1)
        create_stage.update_settings({u'http://rmit.edu.au/schemas/stages/create':
                {
                    u'vm_size': "m1.small",
                    u'vm_image': "ami-0000000d",
                    u'cloud_sleep_interval': 20,
                    u'security_group': '["ssh"]',
                    u'group_id_dir': 'group_id',
                    u'custom_prompt': '[smart-connector_prompt]$',
                    u'nectar_username': 'root',
                    u'nectar_password': ''
                }})
        return create_stage

    def define_configure_stage(self):
        configure_package = "chiminey.corestages.configure.Configure"
        configure_stage, _ = models.Stage.objects.get_or_create\
            (name="configure",
            description="This is the core configure stage",
            parent=self.define_parent_stage(),
            package=configure_package,
            order=0)
        configure_stage.update_settings({
            u'http://rmit.edu.au/schemas/system':
                {
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                },
        })
        return configure_stage

    def define_bootstrap_stage(self):
        bootstrap_package = "chiminey.corestages.bootstrap.Bootstrap"
        bootstrap_stage, _ = models.Stage.objects.get_or_create(
            name="bootstrap",
            description="This is the core bootstrap stage",
            parent=self.define_parent_stage(),
            package=bootstrap_package,
            order=20)
        bootstrap_stage.update_settings(
            {
                u'http://rmit.edu.au/schemas/stages/setup':
                    {
                        u'payload_source': '',
                        u'payload_destination': '',
                        u'payload_name': 'process_payload',
                        u'filename_for_PIDs': 'PIDs_collections',
                    },
            })
        return bootstrap_stage

    def define_schedule_stage(self):
        schedule_package = "chiminey.corestages.schedule.Schedule"
        schedule_stage, _ = models.Stage.objects.get_or_create(
            name="schedule",
            description="This is schedule stage of this smart connector",
            parent=self.define_parent_stage(),
            package=schedule_package,
            order=25)
        return schedule_stage

    def get_updated_execute_params(self):
        return {}

    def _get_default_execute_params(self):
        package = "chiminey.corestages.execute.Execute"
        name = 'execute'
        description = "This is the execute stage"
        settings = {u'http://rmit.edu.au/schemas/stages/run':
                    {
                        u'process_output_dirname': 'chiminey',
                    },
                   }
        params = {'package': package, 'name': name,
                  'description': description, 'settings': settings}
        return params

    def update_default_stage_params(self, default_params, updated={}):
        if updated:
            for k in default_params.keys():
                try:
                    default_params[k] = updated[k]
                    print("k=%s, v=%s" % (k, default_params[k]))
                except KeyError:
                    pass
        return default_params

    def define_execute_stage(self):
        default_params = self._get_default_execute_params()
        updated_params = self.get_updated_execute_params()
        self.update_default_stage_params(default_params, updated_params)
        #execute_package = "chiminey.corestages.execute.Execute"
        execute_package = default_params['package']
        execute_stage, _ = models.Stage.objects.get_or_create(name=default_params['name'], # "execute",
            description=default_params['description'], # "This is the core execute stage",
            parent=self.define_parent_stage(),
            package=execute_package,
            order=30)
        execute_stage.update_settings(default_params['settings'])

           # {
           # u'http://rmit.edu.au/schemas/stages/run':
           #     {
           #         u'process_output_dirname': 'chiminey',
           #     },
           # })
        return execute_stage

    def define_wait_stage(self):
        wait_package = "chiminey.corestages.wait.Wait"
        wait_stage, _ = models.Stage.objects.get_or_create(
            name="wait",
            description="This is the core wait stage",
            parent=self.define_parent_stage(),
            package=wait_package,
            order=40)
        wait_stage.update_settings({})
        return wait_stage

    def define_transform_stage(self):
        transform_package = "chiminey.corestages.transform.Transform"
        transform_stage, _ = models.Stage.objects.get_or_create(name="transform",
            description="This is the core transform stage",
            parent=self.define_parent_stage(),
            package=transform_package,
            order=50)
        transform_stage.update_settings({})
        return transform_stage

    def define_converge_stage(self):
        converge_package = "chiminey.corestages.converge.Converge"
        converge_stage, _ = models.Stage.objects.get_or_create(name="converge",
            description="This is the core converge stage",
            parent=self.define_parent_stage(),
            package=converge_package,
            order=60)
        converge_stage.update_settings({})
        return converge_stage

    def define_destroy_stage(self):
        destroy_package = "chiminey.corestages.destroy.Destroy"
        destroy_stage, _ = models.Stage.objects.get_or_create(
            name="destroy",
            description="This is core destroy stage",
            parent=self.define_parent_stage(),
            package=destroy_package,
            order=70)
        destroy_stage.update_settings({})
        return destroy_stage

    def define_sweep_stage(self, subdirective):
        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep_%s" % subdirective.name,
            description="This is the sweep stage of %s smart connector" % subdirective.name,
            package="chiminey.corestages.sweep.Sweep",
            order=100)
        sweep_stage.update_settings({
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'directive': subdirective.name
            }
            })
        return sweep_stage

    def define_directive(self, directive_name, description='', sweep=False):
        self.directive_name = directive_name
        if not description:
            description = '%s Smart Connector' % self.directive_name
        register_schemas(self.get_domain_specific_schemas())
        parent_stage = self.assemble_stages()
        directive, _ = models.Directive.objects.get_or_create(
            name=self.directive_name,
            defaults={'stage': parent_stage,
                      'description': description,
                      'hidden': sweep}
        )
        self._attach_directive_args(directive)
        if sweep:
            sweep_directive = self.define_sweep_directive(
                directive, description)
            self._attach_directive_args(sweep_directive)


    def define_sweep_directive(self, subdirective, description):
        sweep_stage = self.define_sweep_stage(subdirective)
        sweep_directive_name = "sweep_%s" % subdirective.name
        sweep_directive, _ = models.Directive.objects.get_or_create(
            name=sweep_directive_name,
            defaults={'stage': sweep_stage,
                      'description': 'Sweep for %s' % description,
                      'hidden': False}
                    )
        max_order = 0
        for das in models.DirectiveArgSet.objects.filter(directive=subdirective):
            new_das = models.DirectiveArgSet.objects.create(
                directive=sweep_directive, order=das.order, schema=das.schema)
            max_order = max(max_order, das.order)
        schema = models.Schema.objects.get(namespace=SWEEP_SCHEMA)
        new_das = models.DirectiveArgSet.objects.create(
            directive=sweep_directive, order=max_order + 1, schema=schema)
        return subdirective

    def _attach_directive_args(self, new_directive):
        ui_schema_namespace = self.get_ui_schema_namespace()
        for i, sch in enumerate(ui_schema_namespace):
            schema = models.Schema.objects.get(namespace=sch)
            das, _ = models.DirectiveArgSet.objects.get_or_create(
                directive=new_directive, order=i, schema=schema)

    @abc.abstractmethod
    def get_ui_schema_namespace(self):
        return ''

    def get_domain_specific_schemas(self):
        return ''

    def assemble_stages(self):
        parent_stage = self.define_parent_stage()
        self.define_configure_stage()
        self.define_create_stage()
        self.define_bootstrap_stage()
        self.define_schedule_stage()
        self.define_execute_stage()
        self.define_wait_stage()
        self.define_transform_stage()
        self.define_converge_stage()
        self.define_destroy_stage()
        return parent_stage