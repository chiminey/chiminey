class Stage(Object):

    def __init__(self):
        pass

    def triggered(self, filesystem):
        """ return true if the directory pattern triggers this stage
        """
        return False

    def process(self, filesystem):
        """ perfrom the stage operation
        """
        pass

    def output(self, filesystem):
        """ produce the resulting datfiles and metadata
        """
        pass

class UI(object):
    pass

class Configure(Stage, UI):

    def triggered(self, filesystem):
        return True


    def process(self, filesystem):
        # get the input from the user to override config settings

    def output(self, filesystem):
        # store in filesystem

class FileSystem(Object):
    pass


class Create(Stage):

    def __init__(self):
        pass

    def triggered(self):
        """ return true if the directory pattern triggers this stage
        """
        self.metadata = self._load_metadata_file()
        return metadata

    def _transform_the_filesystem(filesystem, settings):
        key =  settings['ec2_access_key']

        print key


    def process(self, filesystem):
        # get the input from the user to override config settings
        # load up the metadata

        settings = {}
        settings['number_vm_instances'] = self.metadata.number
        settings['ec2_access_key'] = self.metadata.ec2_access_key
        settings['ec2_secret_key'] = self.metadata.ec2_secret_key
        # ...


        self.temp_sys = FileSystem(filesystem)

        self._transform_the_filesystem(self.temp_sys, settings)

        #import codecs
        #f = codecs.open('metadata.json', encoding='utf-8')
        #import json
        #metadata = json.loads(f.read())

    def output(self, filesystem):
        # store in filesystem
        self._store(self.temp_sys, filesystem)


class Setup(Stage):
    pass


class Run(Stage):
    pass


class Check(Stage):
    pass


class Teardown(Stage):
    pass


class SmartConnector():

    def register(self,stage):
        stages.append(stage)


def create_initial_filesystem(filesystem):
    # create standardised metdata files and data files in filesystem
    pass


def mainloop():

    smart_con = SmartConnector()
    filesys = Filesystem()

    create_initial_filesystem(filesys)

    for stage in (Configure, Create, Setup, Run, Check, TearDown):
        smart_con.register(stage)

    while (True):
        for stage in smart_con.stages:
            if stage.triggered(filesys)
                stage.process(filesys)
                stage.output(filesys)