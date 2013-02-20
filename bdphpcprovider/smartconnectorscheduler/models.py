from django.db import models
from django.contrib.auth.models import User

import logging
import logging.config

logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    nickname = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.user.username


# declaration of a set of parameter (e.g., XML schema)
class Schema(models.Model):
    """ Representation of a set of parameters (equiv to XML Schema)

        :attribute namespace: namespace for this schema
        :attribute name: unique name
        :attribute description: displayable text describing the schema

    """
    namespace = models.URLField(verify_exists=False, max_length=400)
    description = models.CharField(max_length=80, default="")
    name = models.SlugField(default="", help_text="A unique identifier for the schema")

    class Meta:
        unique_together = (('namespace', 'name'),)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.namespace)


class ParameterName(models.Model):
    """ A parameter associated with a schema

        :attribute schema: the  :class:`bdphpcprovider.smartconnectorscheduler.models.Schema` which this parameter belongs to
        :attribute name: the name of the parameter
        :attribute type: the type of the parameter from TYPES
        :attribute ranking: int which indicates relative ranking in listings
        :attribute initial: any initial value for this parameter
        :attribute choices: a serialised python list of string choices for the STRLIST type
        :attribute help_text: text that appears in admin tool
        :attribute max_length: maximum length for STRING types
    """
    schema = models.ForeignKey(Schema)
    name = models.CharField(max_length=50)
    # TODO: need to do this so that each paramter can appear only once
    # in each schema

    class Meta:
        unique_together = (('schema', 'name'),)
        ordering = ["-ranking"]

    UNKNOWN = 0
    STRING = 1
    NUMERIC = 2  # only integers
    LINK = 3
    STRLIST = 4
    DATE = 5
    YEAR = 6
    TYPES = (
             (UNKNOWN, 'UNKNOWN'),
             (STRING, 'STRING'),
             (NUMERIC, 'NUMERIC'),
             (LINK, 'LINK'),
             (STRLIST, 'STRLIST'),
             (DATE, 'DATE'),
             (YEAR, 'YEAR')

            )
    # The form used to store dates in the DATE type field
    DATE_FORMAT = "%b %d, %Y"

    type = models.IntegerField(choices=TYPES, default=STRING)

    ranking = models.IntegerField(default=0,
                                  help_text="Describes the relative ordering "
                                  "of parameters when displaying: the larger "
                                  "the number, the more prominent the results")
    initial = models.TextField(default="", blank=True,
                               verbose_name="Initial Value",
                             help_text="The initial value for this parameter")
    choices = models.TextField(default="", blank=True,
                               verbose_name="Choices for the field")
    help_text = models.TextField(default="", blank=True,
                                 verbose_name="Text to help user fill out "
                                              "the field")
    max_length = models.IntegerField(default=255,
                                     verbose_name="Maximum number of "
                                     "characters in a parameter")

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.schema.name)

    #TODO: make a method to display schema and parameters as XML schema definition
    def get_type_string(self, val):
        for (t, str) in self.TYPES:
            if t == val:
                return str
        return "UNKNOWN"

    def get_value(self, val):
        logger.debug("type=%s" % self.type)
        logger.debug("val=%s" % val)
        res = val
        if self.type == self.NUMERIC:
            try:
                res = int(val)
            except ValueError:
                logger.debug("invalid type")
                raise
        return res


class UserProfileParameterSet(models.Model):
    """ Association of a user profile object with a specific schema.

        :attribute user_profile: the :class:`bdphpcprovider.smartconnectorscheduler.models.MediaObject`
        :attribute schema:  the :class:`bdphpcprovider.smartconnectorscheduler.models.Schema`
        :attribute ranking: int which indicates relative ranking of parameter set in listings
     """
    user_profile = models.ForeignKey(UserProfile, verbose_name="User Profile")
    schema = models.ForeignKey(Schema, verbose_name="Schema")
    #info = models.CharField(max_length=400, null=True)
    ranking = models.IntegerField(default=0)

#    def __unicode__(self):
#        return u'%s (%s)' % (self.user_profile.name, self.schema.name)

    class Meta:
        ordering = ["-ranking"]


class UserProfileParameter(models.Model):
    """ The value for some metadata for a User Profile

        :parameter name: the associated  :class:`bdphpcprovider.smartconnectorscheduler.models.ParameterName` that the value matches to
        :parameter paramset: associated  :class:`bdphpcprovider.smartconnectorscheduler.models.UserProfile` and class:`bdphpcprovider.smartconnectorscheduler.models.Schema` for this value
        :parameter value: the actual value
    """
    name = models.ForeignKey(ParameterName, verbose_name="Parameter Name")
    paramset = models.ForeignKey(UserProfileParameterSet, verbose_name="Parameter Set")
    value = models.TextField(verbose_name="Parameter Value", help_text="The Value of this parameter")
    #ranking = models.IntegerField(default=0,help_text="Describes the relative ordering of parameters when displaying: the larger the number, the more prominent the results")

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.paramset, self.value)

    def getValue(self,):
        try:
            val = self.name.get_value(self.value)
        except ValueError:
            logger.error("got bad value")
            raise
        return val

    class Meta:
        ordering = ("name",)


from mptt.models import MPTTModel, TreeForeignKey


class Stage(MPTTModel):
    """
    The units of execution.
    """
    name = models.CharField(max_length=256,)
    impl = models.CharField(max_length=256, null=True)
    description = models.TextField(default="")
    order = models.IntegerField(default=0)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    package = models.CharField(max_length=256, default="")

    class MPTTMeta:
        order_insertion_by = ['order']


# class DirectiveArgument(models.Model):
#     """
#     A parameter in a directive (unparsed)
#     """
#     directive = models.ForeignKey(Directive)
#     arg = models.charField()


class Platform(models.Model):
    name = models.CharField(max_length=256)


class Directive(models.Model):
    """
    Holds an platform independent operation provided by an API
    """
    name = models.CharField(max_length=256)


class Command(models.Model):
    """
    Holds a platform specific operation that uses an external API
    Initialised from the specified stage
    """
    directive = models.ForeignKey(Directive)
    initial_stage = models.ForeignKey(Stage)
    platform = models.ForeignKey(Platform)


class DirectiveArgSet(models.Model):
    """
    Describes the argument of a directive.
    The idea is to specify a type for each of the arguments of the directive as high level schemas
    which can then be checked against usage.
    """
    directive = models.ForeignKey(Stage)
    order = models.IntegerField()
    schema = models.ForeignKey(Schema)


class SmartConnector(models.Model):
    """
    Pointer to a composite stage that specfies a smart connector
    """
    composite_stage = models.ForeignKey(Stage)


class Context(models.Model):
    """ Holds a pointer to the currently to be executed stage and all the arguments and variable storage for
    that execution
    """
    owner = models.ForeignKey(UserProfile)
    current_stage = models.ForeignKey(Stage)


class ContextParameterSet(models.Model):
    """
    All the information required to run the stage in the context
    """
    context = models.ForeignKey(Context)
    schema = models.ForeignKey(Schema, verbose_name="Schema")
    ranking = models.IntegerField(default=0)

    class Meta:
        ordering = ["-ranking"]


# class CommandArgMetaParameter(models.Model):
#     name = models.CharField()
#     paramset = models.ForeignKey(CommandParameterSet)
#     value = models.TextField()


class CommandArgument(models.Model):
    """
    A the level of command a representation of a local or remote file or dataset
    """
    template_url = models.URLField()


class ContextParameter(models.Model):
    name = models.ForeignKey(ParameterName, verbose_name="Parameter Name")
    paramset = models.ForeignKey(ContextParameterSet, verbose_name="Parameter Set")
    value = models.TextField(verbose_name="Parameter Value", help_text="The Value of this parameter")
    #ranking = models.IntegerField(default=0,help_text="Describes the relative ordering of parameters when displaying: the larger the number, the more prominent the results")

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.paramset, self.value)

    def getValue(self,):
        try:
            val = self.name.get_value(self.value)
        except ValueError:
            logger.error("got bad value")
            raise
        return val

    class Meta:
        ordering = ("name",)


