from chiminey.initialisation import CoreInitial
from chiminey.settings import COMPUTE_RESOURCES, STORAGE_RESOURCES

class TutorialInitial(CoreInitial):

    #def get_updated_execute_params(self):
    #    return {'package': "chiminey.examples.randnumunix.randexecute.RandExecute"}


    def get_ui_schema_namespace(self):
        ui_construct = [COMPUTE_RESOURCES['unix'], STORAGE_RESOURCES['unix']]
        return ui_construct
