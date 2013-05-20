
import os
import logging
import logging.config

from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand

from bdphpcprovider.smartconnectorscheduler import models


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Load up the initial state of the database (replaces use of
    fixtures).  Assumes specific strcture.
    NB: passwords are wrong and will need to be changed in the admin
    tool.
    """

    args = ''
    help = 'Setup an initial task structure.'

    def setup(self):
        confirm = raw_input("This will ERASE and reset the database. "
            " Are you sure [Yes|No]")
        if confirm != "Yes":
            print "action aborted by user"
            return

        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(
                codename="change_%s" % model_name)
            #delete_model = Permission.objects.get(codename="delete_%s" % model_name)
            #self.group.permissions.add(add_model)
            self.group.permissions.add(change_model)
            #self.group.permissions.add(delete_model)

        schema_data = {
            u'http://rmit.edu.au/schemas//files':
                [u'general input files for directive',
                {
                u'file0': (models.ParameterName.STRING, '', 3),
                u'file1': (models.ParameterName.STRING, '', 2),
                u'file2': (models.ParameterName.STRING, '', 1),
                }
                ],
             # Note that file schema ns must match regex
             # protocol://host/schemas/{directective.name}/files
             # otherwise files will not be matched correctly.
             # TODO: make fall back to directive files in case specfici
             # version not defined here.
            u'http://rmit.edu.au/schemas/smartconnector1/files':
                 [u'the smartconnector1 input files',
                 {
                 u'file0': (models.ParameterName.STRING, '', 3),
                 u'file1': (models.ParameterName.STRING, '', 2),
                 u'file2': (models.ParameterName.STRING, '', 1),
                 }
                 ],
            u'http://rmit.edu.au/schemas/smartconnector_hrmc/files':
                 [u'the smartconnector hrmc input files',
                 {
                 }
                 ],
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                [u'the smartconnector1 create stage config',
                {
                u'iseed': (models.ParameterName.NUMERIC, '', 4),
                u'num_nodes': (models.ParameterName.NUMERIC, '', 3),
                u'null_number': (models.ParameterName.NUMERIC, '', 2),
                u'parallel_number': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            # we might want to reuse schemas in muliple contextsets
            # hence we could merge next too stages, for example.
            # However, current ContextParameterSets are unamed in the
            # URI so we can't identify which one to use.
            u'http://rmit.edu.au/schemas/stages/null/testing':
                [u'the null stage internal testing',
                {
                u'output': (models.ParameterName.NUMERIC, '', 2),
                u'index': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/parallel/testing':
                [u'the parallel stage internal testing',
                {

                u'output': (models.ParameterName.NUMERIC, '', 2),
                u'index': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://nci.org.au/schemas/smartconnector1/custom':
                [u'the smartconnector1 custom command',
                {
                u'command': (models.ParameterName.STRING, '', 2),
                }
                ],
            u'http://rmit.edu.au/schemas/system/misc':
                [u'system level misc values',
                {
                u'transitions': (models.ParameterName.STRING, '', 4),  # deprecated
                u'system': (models.ParameterName.STRING, '', 3),
                u'id': (models.ParameterName.NUMERIC, '', 2),
                u'output_location': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/system':
                [u'Information about the deployment platform',
                {
                u'platform': (models.ParameterName.STRING, '', 2),
                u'contextid': (models.ParameterName.NUMERIC, '', 1)                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta':
                ["datafile",
                {
                u"a": (models.ParameterName.NUMERIC, '', 2),
                u'b': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://tardis.edu.au/schemas/hrmc/dfmeta2':
                ["datafile2",
                {
                u'c': (models.ParameterName.STRING, '', 1),
                }
                ],
            models.UserProfile.PROFILE_SCHEMA_NS:
                [u'user profile',
                {
                    u'userinfo1': (models.ParameterName.STRING,
                        'test parameter1', 11),
                    u'userinfo2': (models.ParameterName.NUMERIC,
                        'test parameter2', 10),
                    u'nci_private_key': (models.ParameterName.STRING,
                        'location of NCI private key', 9),
                    u'nci_user': (models.ParameterName.STRING,
                        'username for NCI access', 8),
                    u'nci_password': (models.ParameterName.STRING,
                        'password for NCI access', 7),
                    u'nci_host': (models.ParameterName.STRING,
                        'hostname for NCI', 6),
                    u'flag': (models.ParameterName.NUMERIC,
                        'not used?', 5),
                    u'nectar_private_key_name': (models.ParameterName.STRING,
                        'name of the key for nectar', 4),
                    u'nectar_private_key': (models.ParameterName.STRING,
                        'location of NeCTAR private key', 3),
                    u'nectar_ec2_access_key': (models.ParameterName.STRING,
                        'NeCTAR EC2 Access Key', 2),
                    u'nectar_ec2_secret_key': (models.ParameterName.STRING,
                        'NeCTAR EC2 Secret Key', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/copy/files':
                 [u'the copy input files',
                 {
                 u'file0': (models.ParameterName.STRING, '', 2),
                 u'file1': (models.ParameterName.STRING, '', 1),
                 }
                 ],
            u'http://rmit.edu.au/schemas/program/files':
                 [u'the copy input files',
                 {
                 u'file0': (models.ParameterName.STRING, '', 3),
                 u'file1': (models.ParameterName.STRING, '', 2),
                 u'file2': (models.ParameterName.STRING, '', 1),
                 }
                 ],
            u'http://rmit.edu.au/schemas/stages/copy/testing':
                [u'the copy stage internal testing',
                {
                u'output': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/program/testing':
                [u'the program stage internal testing',
                {
                u'output': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/program/config':
                [u'the program command internal config',
                {
                u'program': (models.ParameterName.STRING, '', 3),
                u'remotehost': (models.ParameterName.STRING, '', 2),
                u'program_success': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/greeting/salutation':
                [u'salute',
                {
                u'salutation': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/hrmc':
                [u'the hrmc smart connector input values',
                {
                u'number_vm_instances': (models.ParameterName.NUMERIC, '', 8),
                u'iseed': (models.ParameterName.NUMERIC, '', 7),
                u'input_location': (models.ParameterName.STRING, '', 6),
                u'number_dimensions': (models.ParameterName.NUMERIC, '', 5),
                u'threshold': (models.ParameterName.STRING, '', 4),  # FIXME: should be list of ints
                u'error_threshold': (models.ParameterName.STRING, '', 3),  # FIXME: should use float here
                u'max_iteration': (models.ParameterName.NUMERIC, '', 2),
                u'pottype': (models.ParameterName.NUMERIC, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/configure':
                [u'the configure state of the hrmc smart connector',
                {
                u'configure_done': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/create':
                [u'the create state of the smartconnector1',
                {
                u'group_id': (models.ParameterName.STRING, '', 10),
                u'vm_size': (models.ParameterName.STRING, '', 9),
                u'vm_image': (models.ParameterName.STRING, '', 8),
                u'security_group': (models.ParameterName.STRLIST, '', 7),
                u'group_id_dir': (models.ParameterName.STRING, '', 6),
                u'cloud_sleep_interval': (models.ParameterName.NUMERIC, '', 5),
                u'custom_prompt': (models.ParameterName.STRING, '', 4),
                u'nectar_username': (models.ParameterName.STRING,
                    'name of username for accessing nectar', 3),
                u'nectar_password': (models.ParameterName.STRING,
                    'password of username for accessing nectar', 2),
                u'created_nodes': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/setup':
                [u'the create stage of the smartconnector1',
                {
                u'setup_finished': (models.ParameterName.NUMERIC, '', 3),
                u'payload_source': (models.ParameterName.STRING, '', 2),
                u'payload_destination': (models.ParameterName.STRING, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/deploy':
                [u'the deploy stage of the smartconnector1',
                {
                u'started': (models.ParameterName.NUMERIC, '', 2),
                u'deployed_nodes': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/run':
                [u'the create stage of the smartconnector1',
                {
                u'runs_left': (models.ParameterName.NUMERIC, '', 10),
                u'max_seed_int': (models.ParameterName.NUMERIC, '', 9),
                u'payload_cloud_dirname': (models.ParameterName.STRING, '', 8),
                u'compile_file': (models.ParameterName.STRING, '', 7),
                u'retry_attempts': (models.ParameterName.NUMERIC, '', 6),
                u'error_nodes': (models.ParameterName.NUMERIC, '', 5),
                u'initial_numbfile': (models.ParameterName.NUMERIC, '', 4),
                u'random_numbers': (models.ParameterName.STRING, '', 3),
                u'rand_index': (models.ParameterName.NUMERIC, '', 2),
                u'finished_nodes': (models.ParameterName.STRING, '', 1)
                }
                ],
            u'http://rmit.edu.au/schemas/stages/transform':
                [u'the transform stage of the smartconnector1',
                {
                u'transformed': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/converge':
                [u'the converge stage of the smartconnector1',
                {
                u'converged': (models.ParameterName.NUMERIC, '', 2),
                u'criterion': (models.ParameterName.STRING, '', 1),  # Use STRING as float not implemented
                }
                ],
            u'http://rmit.edu.au/schemas/stages/teardown':
                [u'the teardown stage of the smartconnector1',
                {
                u'run_finished': (models.ParameterName.NUMERIC, '', 1),
                }
                ],
            u'http://rmit.edu.au/schemas/stages/sweep':
                [u'the sweep stage',
                {
                u'input_location': (mode.ParameterName.STRING, '', 4),
                u'directive': (models.ParameterName.STRING, '', 3),
                u'template_name': (models.ParameterName.STRING, '',2),
                u'sweep_done': (models.ParameterName.NUMERIC, '',1)

                }
                ],

            u'http://rmit.edu.au/schemas/sweep/files':
                 [u'the smartconnector hrmc input files',
                 {
                 }
                 ],
        }

        from urlparse import urlparse
        from django.template.defaultfilters import slugify

        for ns in schema_data:
            l = schema_data[ns]
            logger.debug("l=%s" % l)
            desc = l[0]
            logger.debug("desc=%s" % desc)
            kv = l[1:][0]
            logger.debug("kv=%s", kv)

            url = urlparse(ns)

            context_schema, _ = models.Schema.objects.get_or_create(
                namespace=ns,
                defaults={'name': slugify(url.path.replace('/', ' ')),
                    'description': desc})

            for k, v in kv.items():
                val, help_text, ranking = (v[0], v[1], v[2])
                models.ParameterName.objects.get_or_create(
                    schema=context_schema,
                    name=k,
                    defaults={
                        'type': val, 'help_text': help_text,
                        'ranking': ranking})

        logger.debug("stages=%s" % models.Stage.objects.all())
        local_filesys_rootpath = '/var/cloudenabling/remotesys'
        local_platform, _ = models.Platform.objects.get_or_create(name='local',
            root_path=local_filesys_rootpath)
        nectar_platform, _ = models.Platform.objects.get_or_create(
            name='nectar', root_path='/home/centos')
        platform, _ = models.Platform.objects.get_or_create(
            name='nci', root_path=local_filesys_rootpath)

        logger.debug("local_filesys_rootpath=%s" % local_filesys_rootpath)
        local_fs = FileSystemStorage(location=local_filesys_rootpath)

        copy_dir, _ = models.Directive.objects.get_or_create(name="copydir")
        program_dir, _ = models.Directive.objects.get_or_create(name="program")
        self.copy_dir_stage = "bdphpcprovider.smartconnectorscheduler.stages.movement.CopyDirectoryStage"
        self.program_stage = "bdphpcprovider.smartconnectorscheduler.stages.program.LocalProgramStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        copy_stage, _ = models.Stage.objects.get_or_create(name="copydir",
             description="data movemement operation",
             package=self.copy_dir_stage,
             order=100)
        copy_stage.update_settings({})
        program_stage, _ = models.Stage.objects.get_or_create(name="program",
            description="program execution stage",
            package=self.program_stage,
            order=0)
        program_stage.update_settings({})
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=copy_dir, stage=copy_stage)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=program_dir, stage=program_stage)
        local_fs.save("local/greet.txt",
            ContentFile("{{salutation}} World"))
        local_fs.save("remote/greetaddon.txt",
            ContentFile("(remotely)"))

        copy_dir, _ = models.Directive.objects.get_or_create(name="copyfile")
        self.copy_file_stage = "bdphpcprovider.smartconnectorscheduler.stages.movement.CopyFileStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        copy_stage, _ = models.Stage.objects.get_or_create(name="copy",
             description="data movemement operation",
             package=self.copy_file_stage,
             order=100)
        copy_stage.update_settings({})
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=copy_dir, stage=copy_stage)

        smart_dir, _ = models.Directive.objects.get_or_create(name="smartconnector1")
        self.null_package = "bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage"
        self.parallel_package = "bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        composite_stage, _ = models.Stage.objects.get_or_create(name="basic_connector",
             description="encapsulates a workflow",
             package=self.parallel_package,
             order=100)
        setup_stage, _ = models.Stage.objects.get_or_create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package=self.null_package,
            order=0)
        # stage settings are usable from subsequent stages in a run so only
        # need to define once for first null or parallel stage
        setup_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'null_number': 4,
                }
            })
        stage2, _ = models.Stage.objects.get_or_create(name="run",
            parent=composite_stage,
            description="This is the running connector",
            package=self.parallel_package,
            order=1)
        stage2.update_settings(
            {
            u'http://rmit.edu.au/schemas/smartconnector1/create':
                {
                    u'parallel_number': 2
                }
            })
        models.Stage.objects.get_or_create(name="run1",
            parent=stage2,
            description="This is the running part 1",
            package=self.null_package,
            order=1)
        models.Stage.objects.get_or_create(name="run2",
            parent=stage2,
            description="This is the running part 2",
            package=self.null_package,
            order=2)
        models.Stage.objects.get_or_create(name="finished",
            parent=composite_stage,
            description="And here we finish everything off",
            package=self.null_package,
            order=3)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=smart_dir, stage=composite_stage)
        local_fs.save("input/input.txt",
            ContentFile("a={{a}} b={{b}} c={{c}}"))
        local_fs.save("input/file.txt",
            ContentFile("foobar"))

        hrmc_smart_dir, _ = models.Directive.objects.get_or_create(name="smartconnector_hrmc")
        self.configure_package = "bdphpcprovider.smartconnectorscheduler.stages.configure.Configure"
        self.create_package = "bdphpcprovider.smartconnectorscheduler.stages.create.Create"
        self.setup_package = "bdphpcprovider.smartconnectorscheduler.stages.setup.Setup"
        self.deploy_package = "bdphpcprovider.smartconnectorscheduler.stages.deploy.Deploy"
        self.run_package = "bdphpcprovider.smartconnectorscheduler.stages.run.Run"
        self.finished_package = "bdphpcprovider.smartconnectorscheduler.stages.finished.Finished"
        self.transform_package = "bdphpcprovider.smartconnectorscheduler.stages.hrmc2.transform.Transform"
        self.converge_package = "bdphpcprovider.smartconnectorscheduler.stages.hrmc2.converge.Converge"
        self.teardown_package = "bdphpcprovider.smartconnectorscheduler.stages.teardown.Teardown"

        hrmc_composite_stage, _ = models.Stage.objects.get_or_create(name="hrmc_connector",
            description="Encapsultes HRMC smart connector workflow",
            package=self.parallel_package,
            order=100)
        # FIXME: tasks.progress_context does not load up composite stage settings
        hrmc_composite_stage.update_settings({})

        configure_stage, _ = models.Stage.objects.get_or_create(name="configure",
            description="This is configure stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.configure_package,
            order=0)
        configure_stage.update_settings({})
        create_stage, _ = models.Stage.objects.get_or_create(name="create",
            description="This is create stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.create_package,
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
        # setup_stage, _ = models.Stage.objects.get_or_create(name="setup",
        #     description="This is setup stage of HRMC smart connector",
        #     parent=hrmc_composite_stage,
        #     package=self.setup_package,
        #     order=2)
        # setup_stage.update_settings(
        #     {
        #     u'http://rmit.edu.au/schemas/stages/setup':
        #         {
        #             u'payload_source': 'file://127.0.0.1/local/testpayload',
        #             u'payload_destination': 'celery_payload_2',
        #         },
        #     })

        deploy_stage, _ = models.Stage.objects.get_or_create(name="deploy",
            description="This is setup stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.deploy_package,
            order=2)
        deploy_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/setup':
                {
                    u'payload_source': 'file://127.0.0.1/local/testpayload',
                    u'payload_destination': 'celery_payload_2',
                },
            })
        run_stage, _ = models.Stage.objects.get_or_create(name="run",
            description="This is run stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.run_package,
            order=3)
        run_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': 'AEAO_v1_1',
                    u'compile_file': 'HRMC',
                    u'retry_attempts': 3,
                    u'max_seed_int': 1000,  # FIXME: should we use maxint here?
                    u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                },
            })
        finished_stage, _ = models.Stage.objects.get_or_create(name="finished",
            description="This is finished stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.finished_package,
            order=4)
        finished_stage.update_settings({})
        transform_stage, _ = models.Stage.objects.get_or_create(name="transform",
            description="This is transform stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.transform_package,
            order=5)
        transform_stage.update_settings({})
        converge_stage, _ = models.Stage.objects.get_or_create(name="converge",
            description="This is converge stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.converge_package,
            order=6)
        converge_stage.update_settings({})
        teardown_stage, _ = models.Stage.objects.get_or_create(name="teardown",
            description="This is teardown stage of HRMC smart connector",
            parent=hrmc_composite_stage,
            package=self.teardown_package,
            order=7)
        teardown_stage.update_settings({})
        comm, _ = models.Command.objects.get_or_create(platform=nectar_platform,
            directive=hrmc_smart_dir, stage=hrmc_composite_stage)
        print "done"

        sweep, _ = models.Directive.objects.get_or_create(name="sweep")

        sweep_stage, _ = models.Stage.objects.get_or_create(name="sweep",
            description="Sweep Test",
            package="bdphpcprovider.smartconnectorscheduler.stages.sweep.Sweep",
            order=100)
        sweep_stage.update_settings({
            u'http://rmit.edu.au/schemas/stages/sweep':
            {
                u'template_name': 'HRMC.inp'
            },
            # FIXME: move random_numbers into system schema
            u'http://rmit.edu.au/schemas/stages/run':
            {
                u'random_numbers': 'file://127.0.0.1/randomnums.txt'
            },

            })

        # FIXME: tasks.progress_context does not load up composite stage settings
        comm, _ = models.Command.objects.get_or_create(platform=local_platform,
            directive=sweep, stage=sweep_stage)
        print "done"


    def handle(self, *args, **options):
        self.setup()
        print "done"
