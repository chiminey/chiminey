from chiminey.initialisation import CoreInitial
from chiminey.settings import INPUT_FIELDS

class TutorialInitial(CoreInitial):

    #def get_updated_execute_params(self):
    #    return {'package': "chiminey.examples.randnumunix.randexecute.RandExecute"}


    def get_ui_schema_namespace(self):
        ui_construct = [INPUT_FIELDS['unix'], INPUT_FIELDS['output_location']]
        return ui_construct
