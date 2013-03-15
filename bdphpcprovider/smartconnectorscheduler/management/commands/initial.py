
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
        confirm = raw_input("This will ERASE and reset the database.  Are you sure [Yes|No]")
        if confirm != "Yes":
            print "action aborted by user"
            return

        self.remote_fs_path = os.path.join(
            'smartconnectorscheduler', 'testing', 'remotesys/').decode("utf8")
        logger.debug("self.remote_fs_path=%s" % self.remote_fs_path)
        self.remote_fs = FileSystemStorage(location=self.remote_fs_path)

        self.group, _ = Group.objects.get_or_create(name="standarduser")
        self.group.save()

        for model_name in ('userprofileparameter', 'userprofileparameterset'):
            #add_model = Permission.objects.get(codename="add_%s" % model_name)
            change_model = Permission.objects.get(codename="change_%s" % model_name)
            #delete_model = Permission.objects.get(codename="delete_%s" % model_name)
            #self.group.permissions.add(add_model)
            self.group.permissions.add(change_model)
            #self.group.permissions.add(delete_model)

        self.group.save()

        # # Create a user and profile
        # self.user, _ = User.objects.get_or_create(username="username1",
        #     defaults={"password": "password"})
        # self.user.groups.add(self.group)
        # self.user.save()

        # logger.debug("user=%s" % self.user)
        # profile, _ = models.UserProfile.objects.get_or_create(
        #               user=self.user)

        # Create the schemas for template parameters or config info
        # specfied in directive arguments
        for ns, name, desc in [(models.UserProfile.PROFILE_SCHEMA_NS,
            "userprofile1", "Information about user"),
            ('http://rmit.edu.au/schemas/greeting/salutation', "salutation",
                "The form of salutation"),
            ("http://rmit.edu.au/schemas/program", "program",
                "A remote executing program"),
             ('http://tardis.edu.au/schemas/hrmc/dfmeta/', "datafile1",
                "datafile 1 schema"),
            ('http://tardis.edu.au/schemas/hrmc/dfmeta2/', "datafile2",
                "datafile 2 schema"),
            ('http://tardis.edu.au/schemas/hrmc/create', "create",
                "create stage"),
            ("http://nci.org.au/schemas/hrmc/custom_command/", "custom",
                "custom command")
            ]:
            sch, _ = models.Schema.objects.get_or_create(namespace=ns, name=name, description=desc)
            logger.debug("sch=%s" % sch)

        user_schema = models.Schema.objects.get(namespace=models.UserProfile.PROFILE_SCHEMA_NS)
        # Create the schema for stages (currently only one) and all allowed
        # values and their types for all stages.
        context_schema, _ = models.Schema.objects.get_or_create(
            namespace=models.Context.CONTEXT_SCHEMA_NS,
            name="Context Schema", description="Schema for run settings")
        # We assume that a run_context has only one schema at the moment, as
        # we have to load up this schema with all run settings values used in
        # any of the stages (and any parameters required for the stage
        # invocation)
        # TODO: allow multiple ContextParameterSet each with different schema
        # so each value will come from a namespace.  e.g., general/fsys
        # nectar/num_of_nodes, setup/nodes_setup etc.
        for name, param_type in {
            u'file0': models.ParameterName.STRING,
            u'file1': models.ParameterName.STRING,
            u'file2': models.ParameterName.STRING,
            u'program': models.ParameterName.STRING,
            u'remotehost': models.ParameterName.STRING,
            u'salutation': models.ParameterName.NUMERIC,
            u'transitions': models.ParameterName.STRING,  # TODO: use STRLIST
            u'program_output': models.ParameterName.NUMERIC,
            u'movement_output': models.ParameterName.NUMERIC,
            u'platform': models.ParameterName.NUMERIC,
            u'system': models.ParameterName.STRING,
            u'num_nodes': models.ParameterName.NUMERIC,
            u'program_success': models.ParameterName.STRING,
            u'iseed': models.ParameterName.NUMERIC,
            u'command': models.ParameterName.STRING,
            u'null_output': models.ParameterName.NUMERIC,
            u'parallel_output': models.ParameterName.NUMERIC,
            u'null_number': models.ParameterName.NUMERIC,
            u'parallel_number': models.ParameterName.NUMERIC,
            u'null_index': models.ParameterName.NUMERIC,
            u'parallel_index': models.ParameterName.NUMERIC,
            }.items():
            models.ParameterName.objects.get_or_create(schema=context_schema,
                name=name,
                type=param_type)

        self.PARAMTYPE = {'userinfo1': models.ParameterName.STRING,
            'userinfo2': models.ParameterName.NUMERIC,
            'fsys': models.ParameterName.STRING,
            'nci_user': models.ParameterName.STRING,
            'nci_password': models.ParameterName.STRING,
            'nci_host': models.ParameterName.STRING,
            'PASSWORD': models.ParameterName.STRING,
            'USER_NAME': models.ParameterName.STRING,
            'PRIVATE_KEY': models.ParameterName.STRING}
        for k, v in self.PARAMTYPE.items():
            param_name, _ = models.ParameterName.objects.get_or_create(schema=user_schema,
                name=k,
                type=self.PARAMTYPE[k])

        # Make a platform for the commands
        platform, _ = models.Platform.objects.get_or_create(name="nci")

        copy_dir, _ = models.Directive.objects.get_or_create(name="copy")
        program_dir, _ = models.Directive.objects.get_or_create(name="program")
        smart_dir, _ = models.Directive.objects.get_or_create(name="smartconnector1")

        self.movement_stage = "bdphpcprovider.smartconnectorscheduler.stages.movement.MovementStage"
        self.program_stage = "bdphpcprovider.smartconnectorscheduler.stages.program.ProgramStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        copy_stage, _ = models.Stage.objects.get_or_create(name="copy",
             description="data movemement operation",
             package=self.movement_stage,
             order=100)
        program_stage, _ = models.Stage.objects.get_or_create(name="program",
            description="program execution stage",
            package=self.program_stage,
            order=0)

        self.null_package = "bdphpcprovider.smartconnectorscheduler.stages.nullstage.NullStage"
        self.parallel_package = "bdphpcprovider.smartconnectorscheduler.stages.composite.ParallelStage"
        # Define all the stages that will make up the command.  This structure
        # has two layers of composition
        composite_stage, _ = models.Stage.objects.get_or_create(name="basic_connector",
             description="encapsulates a workflow",
             package=self.parallel_package,
             order=100)
        models.Stage.objects.get_or_create(name="setup",
            parent=composite_stage,
            description="This is a setup stage of something",
            package=self.null_package,
            order=0)
        stage2, _ = models.Stage.objects.get_or_create(name="run",
            parent=composite_stage,
            description="This is the running connector",
            package=self.parallel_package,
            order=1)
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

        logger.debug("stages=%s" % models.Stage.objects.all())
        # Make a new command that reliases composite_stage
        # TODO: add the command program to the model
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=copy_dir, stage=copy_stage)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=program_dir, stage=program_stage)
        comm, _ = models.Command.objects.get_or_create(platform=platform, directive=smart_dir, stage=composite_stage)

        # We could make one command with a composite containing three stages or
        # three commands each containing a single stage.

        # done setup

        logger.debug("remote_fs_path=%s" % self.remote_fs_path)

        self.remote_fs.save("local/greet.txt",
            ContentFile("{{salutation}} World"))

        self.remote_fs.save("remote/greetaddon.txt",
            ContentFile("(remotely)"))

        # setup the required initial files
        self.remote_fs.save("input/input.txt",
         ContentFile("a={{a}} b={{b}} c={{c}}"))

        self.remote_fs.save("input/file.txt",
         ContentFile("foobar"))
        print "done"

    def handle(self, *args, **options):
        self.setup()
        print "done"
