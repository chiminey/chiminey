import time
import os
import utility

#Every stage may be thrown away after completion 
# This stage has no impact on other stages
class Stage(object):
    def __init__(self):
        pass

    def triggered(self, context):
        """ return true if the directory pattern triggers this stage
        """
        return True

    def process(self, context):
        """ perfrom the stage operation
        """
        pass

    def output(self, context):
        """ produce the resulting datfiles and metadata
        """
        pass

class UI(object):
    pass

class FileSystem(object):
    #create, retrieve, update, delete
    # collection of files
    def create_initial_filesystem(self):
    # create standardised metdata files and data files in filesystem
        pass
    
    
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

    def __init__(self):
        pass
    
    def _load_metadata_file(self):
        pass

    def triggered(self, context):
        """ return true if the directory pattern triggers this stage
        """
        #check the context for existence of a file system or other
        # key words, then if true, trigger
        self.metadata = self._load_metadata_file()
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
        pass
    
  

    def output(self, context):
        # store in filesystem
        #self._store(self.temp_sys, filesystem)
        pass

class Setup(Stage):
    pass


class Run(Stage):
    #json output 
    pass


class Check(Stage):
    #json output 
    pass
 

class Teardown(Stage):
    pass


class SmartConnector(object):
    
    def __init__(self):
        self.stages = []
        
    def register(self,stage):
        self.stages.append(stage)


def mainloop():

# load system wide settings, e.g Security_Group
#communicating between stages: crud context or filesystem
#build context with file system as its only entry 
    context = {}
    context['version'] = "1.0.0"
    
    smart_con = SmartConnector()
    filesys = FileSystem()

    #filesys.create_initial_filesystem()
    #filesys.load_generic_settings()

    for stage in (Configure(), Create(), Setup(), Run(), Check(), Teardown()):
        smart_con.register(stage)
    
    #print smart_con.stages

    #while loop is infinite:
    # check the semantics for 'dropping data' into
    # designated location. 
    #What happens if data is dropped while
    #another is in progress?
    
    
    while(True):
        
    #while (True):
        done = 0
        for stage in smart_con.stages:
            print "Working in stage",stage
            if stage.triggered(context):
                stage.process(context)
                stage.output(context)
                done += 1
                #smart_con.unregister(stage)
                #print "Deleting stage",stage
                print done
    
        if done == len(smart_con.stages):
            break
                
if __name__ == '__main__':
    begins = time.time()
    mainloop()
    ends = time.time()
    print "Total execution time: %d seconds" % (ends-begins)               