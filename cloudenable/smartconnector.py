import time

class Stage(object):

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
        pass
        
    def output(self, filesystem):
        # store in filesystem
        pass

class FileSystem(object):
    def create_initial_filesystem(self):
    # create standardised metdata files and data files in filesystem
        pass


class Create(Stage):

    def __init__(self):
        pass
    
    def _load_metadata_file(self):
        pass

    def triggered(self, filesystem):
        """ return true if the directory pattern triggers this stage
        """
        self.metadata = self._load_metadata_file()
        return self.metadata

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


class SmartConnector(object):
    stages = []
    def register(self,stage):
        self.stages.append(stage)


def mainloop():

    smart_con = SmartConnector()
    filesys = FileSystem()

    filesys.create_initial_filesystem()

    for stage in (Configure(), Create(), Setup(), Run(), Check(), Teardown()):
        smart_con.register(stage)
        print "Here", stage
    
    #print smart_con.stages

    #while loop is infinite
    while (True):
        for stage in smart_con.stages:
            print "Before error",stage
            if stage.triggered(filesys):
                stage.process(filesys)
                stage.output(filesys)
                
if __name__ == '__main__':
    begins = time.time()
    mainloop()
    ends = time.time()
    logger.info("Total execution time: %d seconds", ends-begins)                