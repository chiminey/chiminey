
# Contains the specific connectors and stages for HRMC


import logging
import logging.config
import json
logger = logging.getLogger(__name__)


from smartconnector import Stage
from smartconnector import UI
from smartconnector import ParallelStage
from smartconnector import SequentialStage

from filesystem import FileSystem
from filesystem import DataObject

from simplepackage import _get_rego_nodes
from simplepackage import setup_multi_task

# class DataObject():
#     # Assume that whole file is contained in one big string
#     # as it makes json parsing easier

#     def __init__(self):
#         self.line = ""

#     def create(self,line):
#         self.line = line

#     def retrieve(self):
#         return self.line


# class FileSystem(object):

#     def __init__(self):
#         self.fs = {}

#     def create(self, name, felem):
#         self.fs[name] = felem

#     def retrieve(self, name):
#         return self.fs[name]

#     def update(self, name, felem):
#         self.fs[name] = felem

#     def delete(self):
#         self.fs.delete(felem)
#         pass

#     def __str__(self):
#         return "%s" % self.fs


def get_elem(context,key):
    try:
        fsys = context[key]
    except KeyError,e:
        logger.error("canot load filesys %s from %s" % (e,context))
        return {}
    return fsys


def get_filesys(context):
    return get_elem(context,'filesys')


def get_file(fsys,file):
    try:
        config = fsys.retrieve(file)
    except KeyError,e:
        logger.error("canot load %s %s" % (file,e))
        return {}
    return config


def get_settings(context):
    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys, "default/config.sys")
    logger.debug("config= %s" % config)
    settings_text = config.retrieve()
    logger.debug("settings_text= %s" % settings_text)
    res = json.loads(settings_text)
    logger.debug("res=%s" % dict(res))
    return dict(res)


def get_run_info(context):
    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)
    config = get_file(fsys,"default/runinfo.sys")
    logger.debug("config= %s" % config)

    settings_text = config.retrieve()

    logger.debug("runinfo_text= %s" % settings_text)
    res = json.loads(settings_text)
    logger.debug("res=%s" % dict(res))
    return dict(res)


class Configure(Stage, UI):
    """
        - Load config.sys file into the filesystem
        - Nothing beyond specifying the path to config.sys
        - Later could be dialogue box,...

    """
    def triggered(self, context):
        #check for filesystem in context
        return True


            #logger.debug("%s" % field_val)

    def process(self, context):
        # - Load config.sys file into the filesystem
        # - Nothing beyond specifying the path to config.sys
        # - Later could be dialogue box,...
        # 1. creates instance of file system
        # 2. pass the file system as entry in the Context
        # create status  file in file system
        #print " Security Group", filesystem.settings.SECURITY_GROUP

        pass

    # indicate the process() is completed
    def output(self, context):
        # store in filesystem
        pass





class Create(Stage):


    def triggered(self, context):
        """ return true if the directory pattern triggers this stage
        """
        #check the context for existence of a file system or other
        # key words, then if true, trigger
        #self.metadata = self._load_metadata_file()

        if True:
            self.settings = utility.load_generic_settings()
            return True

    def _transform_the_filesystem(filesystem, settings):
        key =  settings['ec2_access_key']

        print key


    def process(self, context):

        # get the input from the user to override config settings
        # load up the metadata

        #settings = {}
        #settings['number_vm_instances'] = self.metadata.number

        #settings['ec2_access_key'] = self.metadata.ec2_access_key
        #settings['ec2_secret_key'] = self.metadata.ec2_secret_key
        # ...


        #self.temp_sys = FileSystem(filesystem)

        #self._transform_the_filesystem(self.temp_sys, settings)

        #import codecs
        #f = codecs.open('metadata.json', encoding='utf-8')
        #import json
        #metadata = json.loads(f.read())
        print "Security Group ", self.settings.SECURITY_GROUP
        pass

    def output(self, context):
        # store in filesystem
        #self._store(self.temp_sys, filesystem)
        pass


class Setup(Stage):

    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        # triggered if the set of the VMS has been established.

        self.settings = get_settings(context)
        logger.debug("settings = %s" % self.settings)
        run_info = get_run_info(context)
        logger.debug("runinfo=%s" % run_info)
        self.settings.update(run_info)

        logger.debug("settings = %s" % self.settings)

        self.group_id = self.settings["group_id"]

        logger.debug("group_id = %s" % self.group_id)
        packaged_nodes = _get_rego_nodes(self.group_id, self.settings)
        logger.debug("packaged_nodes = %s" % packaged_nodes)
        return len(packaged_nodes)

    def process(self, context):
        setup_multi_task(self.group_id, self.settings)
        pass

    def output(self, context):
        # TODO: how to signal next stage
        pass


class Run(Stage):
    """
    Start N nodes and return status
    """

    def triggered(self, context):
        # triggered when we now that we have N nodes setup and ready to run.
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']
        self.fsys== get_filesys(context)
        packaged_nodes = _get_rego_nodes(group_id, settings)

        # TODO: look for compiled packages on nodes.


    def process(self, context):

        seed = self.settings['seed']

        # assume that correct local file system has been created.

        prepare_multi_input(self.group_id, options.input_dir,
                            settings, seed)

        try:
            pids = run_multi_task(group_id, options.input_dir, settings)
        except PackageFailedError, e:
            logger.error(e)
            logger.error("unable to start packages")
            #TODO: cleanup node of copied input files etc.
            sys.exit(1)


    def output(self, context):
        pass

class Finished(Stage):
    """
    Return whether the run has finished or not
    """
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']


        pass

    def process(self, context):
        pass

    def output(self, context):
        pass


class Converge(Stage):
    """
    Return whether the run has finished or not
    """
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']
        pass

    def process(self, context):
        pass

    def output(self, context):
        pass





class Transform(Stage):
    """
    Return whether the run has finished or not
    """
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']
        pass

    def process(self, context):
        pass

    def output(self, context):
        pass




class Teardown(Stage):
    def triggered(self, context):
        self.settings = get_settings(context)
        self.group_id = self.settings['group_id']

    def process(self, context):
        pass

    def output(self, context):
        pass


