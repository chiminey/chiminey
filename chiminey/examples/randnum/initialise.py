from chiminey.initialisation import CoreInitial
from django.conf import settings

class RandNumInitial(CoreInitial):
    def get_ui_schema_namespace(self):
        schemas = [
                settings.INPUT_FIELDS['unix'],
                settings.INPUT_FIELDS['output_location'],
                ]
        return schemas


# ---EOF ---

