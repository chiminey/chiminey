# Copyright (C) 2014, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import json
from pprint import pformat
import logging
import logging.config


from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.conf import settings as django_settings

from chiminey.smartconnectorscheduler.errors import InvalidInputError

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, help_text="Information about the user")
    company = models.CharField(max_length=255, blank=True, help_text="Company of the user")
    nickname = models.CharField(max_length=255, blank=True, help_text="User's nickname")
    PROFILE_SCHEMA_NS = "%s/userprofile1" % django_settings.SCHEMA_PREFIX

    def __unicode__(self):
        return self.user.username


# declaration of a set of parameter (e.g., XML schema)
class Schema(models.Model):
    """ Representation of a set of parameters (equiv to XML Schema)

        :attribute namespace: namespace for this schema
        :attribute name: unique name
        :attribute description: displayable text describing the schema

    """
    namespace = models.URLField(max_length=400, help_text="A URI that uniquely ids the schema")
    description = models.CharField(max_length=80, default="", help_text="The description of this schema")
    name = models.SlugField(default="", help_text="A unique identifier for the schema")
    hidden = models.BooleanField(default=False)

    class Meta:
        unique_together = (('namespace', 'name'),)

    def __unicode__(self):
        return "%s" % self.name

    def get_parameters(self):
        return ParameterName.filter(schema=self)


class ParameterName(models.Model):
    """ A parameter associated with a schema

        :attribute schema: the  :class:`chiminey.smartconnectorscheduler.models.Schema` which this parameter belongs to
        :attribute name: the name of the parameter
        :attribute type: the type of the parameter from TYPES
        :attribute ranking: int which indicates relative ranking in listings
        :attribute initial: any initial value for this parameter
        :attribute choices: a serialised python list of string choices for the STRLIST type
        :attribute help_text: text that appears in admin tool
        :attribute max_length: maximum length for STRING types
    """
    schema = models.ForeignKey(Schema, help_text="Schema that contains this parameter")
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
    subtype = models.TextField(default="", blank=True,
                                 verbose_name="Subtype for the parameter")
    description = models.TextField(default="", blank=True,
        verbose_name="Human readable name for the parameter")
    hidefield = models.URLField(max_length=400, help_text="", blank=True, default="", null=True)
    # FIXME: as hidecondition becomes rhs of expression in html, could be
    # untrusted context.  Therefore, only superusers should be able to change
    # this field....
    hidecondition = models.TextField(default="", blank=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.schema.name)

    #TODO: make a method to display schema and parameters as XML schema definition
    def get_type_string(self, val):
        for (t, str) in self.TYPES:
            if t == val:
                return str
        return "UNKNOWN"

    #TODO: Check MyTardis code base for consistency
    def get_value(self, val):
        #logger.debug("type=%s" % self.type)
        #logger.debug("val=%s" % val)
        res = val
        if self.type == self.STRING:
            res = val
        elif self.type == self.NUMERIC:
            try:
                res = int(val)
            except ValueError:
                logger.debug("invalid numeric type")
                raise
        elif self.type == self.STRLIST:
            res = val
            # try:
            #     import ast
            #     res = ast.literal_eval(val)
            #     logger.debug('STRLIST %s length %d' % (res, len(res)))
            # except ValueError:
            #     logger.debug("invalid strlist type")
            #     raise
        else:
            logger.debug("Unsupported Type")
            raise ValueError
        return res


class UserProfileParameterSet(models.Model):
    """ Association of a user profile object with a specific schema.

        :attribute user_profile: the :class:`chiminey.smartconnectorscheduler.models.MediaObject`
        :attribute schema:  the :class:`chiminey.smartconnectorscheduler.models.Schema`
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

        :parameter name: the associated  :class:`chiminey.smartconnectorscheduler.models.ParameterName` that the value matches to
        :parameter paramset: associated  :class:`chiminey.smartconnectorscheduler.models.UserProfile` and class:`chiminey.smartconnectorscheduler.models.Schema` for this value
        :parameter value: the actual value
    """
    name = models.ForeignKey(ParameterName, verbose_name="Parameter Name")
    paramset = models.ForeignKey(UserProfileParameterSet, verbose_name="Parameter Set")
    value = models.TextField(blank=True, verbose_name="Parameter Value", help_text="The Value of this parameter")
    #ranking = models.IntegerField(default=0,help_text="Describes the relative ordering of parameters when displaying: the larger the number, the more prominent the results")

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.paramset, self.value)

    def getValue(self,):
        try:
            val = self.name.get_value(self.value)
        except ValueError:
            logger.error("up:got bad value %s" % self.value)
            raise
        return val

    class Meta:
        ordering = ("name",)


def make_stage_transitions(stage):
    """ Starting at stage, traverse the whole composite stage and record
    and return the path (assuming no branches).  TODO: branches?
    """
    # FIXME: should be in models.Stage?
    if Stage.objects.filter(parent=stage).count():
        return _make_stage_trans_recur(stage, 0)
    else:
        return {'%s' % stage.id: 0}


def _make_stage_trans_recur(stage, parent_next_sibling_id):
    # TODO: test this carefully
    logger.debug("mps stage=%s" % stage)
    transition = {}
    childs = Stage.objects.filter(parent=stage).order_by('order')
    logger.debug("childs=%s", childs)
    # FIXME: rewrite this
    for i, child in enumerate(childs):
        key = child.id
        value = childs[i + 1].id if i < len(childs) - 1 else -1
        transition[key] = value
        logger.debug("%s -> %s" % (key, value))
        subtransition = _make_stage_trans_recur(child, value)
        logger.debug("subtransiton=%s", subtransition)
        transition.update(subtransition)

    if len(childs) > 0:
        k, v = stage.id, childs[0].id
        logger.debug("%s -> %s" % (key, value))
        transition[k] = v
        k, v = childs.reverse()[0].id, parent_next_sibling_id
        logger.debug("%s -> %s" % (key, value))
        transition[k] = v
    # else:
    #        transition[stage.id] = 0
    logger.debug("transition=%s" % transition)

    return transition

# TODO: if hierarchies become very complicated, may need to use mptt
#from mptt.models import MPTTModel, TreeForeignKey


#class Stage(MPTTModel):
class Stage(models.Model):
    """
    The units of execution.
    """
    name = models.CharField(max_length=256,)
    impl = models.CharField(max_length=256, blank=True)
    description = models.TextField(default="")
    order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', null=True, blank=True)
    #parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    package = models.CharField(max_length=256, default="")

    class MPTTMeta:
        order_insertion_by = ['order']

    def __unicode__(self):
        return u'#%s %s "%s" parent="%s"' % (self.id, self.name, self.description, self.parent)

    def get_next_stage(self, context):
        """
        Given a stage, determine the next stage to execute, by consulting transition map
        """

        if u'%s/system/misc' % django_settings.SCHEMA_PREFIX in context:
            misc = context[u'%s/system/misc' % django_settings.SCHEMA_PREFIX]
        else:
            misc = {}

        if u'transitions' in misc:
            transitions = json.loads(misc[u'transitions'])
        else:
            transitions = {}

        logger.debug("transitions=%s" % transitions)
        logger.debug("current_stage=%s" % self)
        logger.debug("self.id=%s" % self.id)
        next_stage_id = transitions["%s" % self.id]
        logger.debug("next_stage_id = %s" % next_stage_id)

        if next_stage_id:
            next_stage = Stage.objects.get(id=next_stage_id)
        else:
            return None
        return next_stage

    def get_settings(self):
        """
        Returns a readonly dict that holds all the information for the stage
        """
        schema_map = {}
        for sps in StageParameterSet.objects.filter(stage=self):
            schema = sps.schema.namespace
            logger.debug("schema=%s" % schema)
            sch_cont = {}
            for param in StageParameter.objects.filter(paramset=sps):
                sch_cont[param.name.name] = param.getValue()  # NB: Assume that key is unique to each schema
            sch = schema_map[schema] if schema in schema_map else []
            sch.append(sch_cont)
            schema_map[schema] = sch[0]  # NB: assume only one instance of each schema per context

        settings = schema_map
        logger.debug("settings=%s" % settings)

        return settings

    def update_settings(self, stage_settings):
        """
            update the stage_settings associated with the context with new values from a map
        """
        #logger.debug("stage_settings=%s" % stage_settings)
        for schdata in stage_settings:
            #logger.debug("schdata=%s" % schdata)
            try:
                sch = Schema.objects.get(namespace=schdata)
            except Schema.DoesNotExist:
                logger.error("schema %s does not exist" % schdata)
                raise
            except MultipleObjectsReturned:
                logger.error("multiple schemas found for %s" % schdata)
                raise

            #logger.debug("sch=%s" % sch)

            paramset, _ = StageParameterSet.objects.get_or_create(schema=sch, stage=self)

            #logger.debug("paramset=%s" % paramset)
            #TODO: what if entries in original context have been deleted?
            kvs = stage_settings[schdata]

            for k in kvs:
                v = kvs[k]
                try:
                    pn = ParameterName.objects.get(schema=sch,
                        name=k)
                except ParameterName.DoesNotExist:
                    msg = "Unknown parameter '%s' for context '%s'" % (k, stage_settings)
                    logger.exception(msg)
                    raise InvalidInputError(msg)
                try:
                    cp = StageParameter.objects.get(name__name=k, paramset=paramset)
                except StageParameter.DoesNotExist:
                    # TODO: need to check type
                    #logger.debug("new param =%s" % pn)
                    cp = StageParameter.objects.create(name=pn,
                        paramset=paramset, value=v)
                except MultipleObjectsReturned:
                    logger.exception("Found duplicate entry in StageParamterSet")
                    raise
                else:
                    #logger.debug("updating %s to %s" % (cp.name, v))
                    # TODO: need to check type
                    cp.value = v
                    cp.save()

    def get_stage_setting(self, schema, key):
        param_set = StageParameterSet.objects.filter(schema=schema, stage=self)
        for ps in param_set:
            pn = ParameterName.objects.get(schema=schema, name=key)
            p = StageParameter.objects.get(paramset=ps, name=pn)
            return p.value
        return ""



#FIXME: We assume 1 private key per platform. Relax this assumption
#fixme depreciate this model
class Platform(models.Model):
    """
    The envioronment where directives will be executed.
    """
    name = models.CharField(max_length=256, default='nectar')
    root_path = models.CharField(max_length=512, default='/home/centos')

    def __unicode__(self):
        return u"Platform:%s" % (self.name)


class PlatformParameterSet(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False, help_text='The name of the platform')
    owner = models.ForeignKey(UserProfile)
    schema = models.ForeignKey(Schema, verbose_name="Schema")
    ranking = models.IntegerField(default=0)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ("name",)
        unique_together = (('owner', 'name'),)


class PlatformParameter(models.Model):
    """ The value for some metadata for a User Profile
        :parameter name: the associated  :class:`chiminey.smartconnectorscheduler.models.ParameterName` that the value matches to
        :parameter paramset: associated  :class:`chiminey.smartconnectorscheduler.models.PlatformParameterSet` and class:`chiminey.smartconnectorscheduler.models.Schema` for this value
        :parameter value: the actual value
    """
    name = models.ForeignKey(ParameterName, verbose_name="Parameter Name")
    paramset = models.ForeignKey(PlatformParameterSet, verbose_name="Parameter Set")
    value = models.TextField(blank=True, verbose_name="Parameter Value", help_text="The Value of this parameter")

    class Meta:
        ordering = ("name",)

    def getValue(self,):
        try:
            val = self.name.get_value(self.value)
        except ValueError:
            logger.error("pi:got bad value %s" % self.value)
            raise
        return val

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.paramset, self.value)


class Directive(models.Model):
    """
    Holds an platform independent operation provided by an API
    """
    name = models.CharField(max_length=256)
    description = models.TextField(default="", blank=True,
                               verbose_name="Description",
                             help_text="Human Readable name for this directive")
    hidden = models.BooleanField(default=False)
    stage = models.ForeignKey(Stage, null=True, blank=True)

    def __unicode__(self):
        return u"Directive:%s" % (self.name)


class DirectiveArgSet(models.Model):
    """
    Describes the argument of a directive.
    The idea is to specify a type for each of the arguments of the directive
    as high level schemas
    which can then be checked against usage.
    """
    directive = models.ForeignKey(Directive)
    order = models.IntegerField()
    schema = models.ForeignKey(Schema)

    def __unicode__(self):
        return u"%s %s" % (self.directive, self.schema)


class SmartConnector(models.Model):
    """
    Pointer to a composite stage that specfies a smart connector
    """
    composite_stage = models.ForeignKey(Stage)


class Context(models.Model):
    """
    Holds a pointer to the currently to be executed stage and all the
    arguments and variable storage for
    that execution
    """
    owner = models.ForeignKey(UserProfile)
    current_stage = models.ForeignKey(Stage)
    deleted = models.BooleanField(default=False)
    status = models.TextField(default="", blank=True,
                               verbose_name="Status of the Context",
                             help_text="")
    directive = models.ForeignKey(Directive, null=True)
    created = models.DateTimeField(auto_now_add=True)
    stopped = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    CONTEXT_SCHEMA_NS = "%s/context1" % django_settings.SCHEMA_PREFIX

    def get_absolute_url(self):
        return reverse('contextview', kwargs={'pk': self.id})

    def get_context(self):
        """
        Returns a readonly dict that holds all the information for the context
        """
        schema_map = {}
        for cps in ContextParameterSet.objects.filter(context=self):
            schema = cps.schema.namespace
            logger.debug("schema=%s" % schema)
            sch_cont = {}
            for param in ContextParameter.objects.filter(paramset=cps):
                logger.debug("param=%s" % param)
                sch_cont[param.name.name] = param.getValue()  # NB: Assume that key is unique to each schema
            sch = schema_map[schema] if schema in schema_map else []
            sch.append(sch_cont)
            schema_map[schema] = sch[0]  # NB: assume only one instance of each schema per context

        context = schema_map
        logger.debug("context=%s" % context)

        return context

    def update_run_settings(self, run_settings):
        """
            update the run_settings associated with the context with new values from a map
        """
        logger.debug("run_settings=%s" % run_settings)
        for schdata in run_settings:
            logger.debug("schdata=%s" % schdata)
            try:
                sch = Schema.objects.get(namespace=schdata)
            except Schema.DoesNotExist as e:
                logger.error("schema %s does not exist" % schdata)
                raise e
            except MultipleObjectsReturned:
                logger.error("multiple schemas found for %s" % schdata)
                raise

            logger.debug("sch=%s" % sch)

            paramset, _ = ContextParameterSet.objects.get_or_create(schema=sch, context=self)

            logger.debug("paramset=%s" % paramset)
            kvs = run_settings[schdata]

            cp_to_delete = []
            for pn in ContextParameter.objects.filter(paramset=paramset):
                if not pn.name.name in kvs:
                    cp_to_delete.append(pn.id)

            logger.debug("cp_to_delete=%s" % pformat(cp_to_delete))
            for pnid in cp_to_delete:
                pn = ContextParameter.objects.get(id=pnid)
                pn.delete()

            for k in kvs:
                v = kvs[k]
                logger.debug("k=%s v=%s" % (k, v))

                try:
                    pn = ParameterName.objects.get(schema=sch,
                        name=k)
                except ParameterName.DoesNotExist:
                    msg = "Unknown parameter '%s' for context '%s'" % (k, run_settings)
                    logger.error(msg)
                    raise InvalidInputError(msg)
                try:
                    cp = ContextParameter.objects.get(name__name=k, paramset=paramset)
                except ContextParameter.DoesNotExist:
                    # TODO: need to check type
                    logger.debug("new param =%s" % pn)
                    try:
                        cp = ContextParameter.objects.create(name=pn,
                            paramset=paramset, value=v)
                    except Exception, e:
                        logger.error(e)
                        pass
                except MultipleObjectsReturned, e:
                    logger.error(e)
                    logger.error("Found duplicate entry in ContextParamterSet")
                    raise
                else:
                    logger.debug("updating %s to %s" % (cp.name, v))
                    # TODO: need to check type
                    cp.value = v
                    cp.save()

    def __unicode__(self):
        if self.current_stage:
            res = self.current_stage.name
        else:
            res = "None"
        res2 = ContextParameterSet.objects.filter(context=self)

        return u"Context:{'owner':%s, 'stage':%s, 'parameters':%s}" % (self.owner,
             res, [unicode(x) for x in res2]
            )


class ContextMessage(models.Model):

    context = models.ForeignKey(Context)
    message = models.TextField(blank=True, verbose_name="Message", help_text="Status message for the context")

    def __unicode__(self):
        return "%s (contextid=%s)" % (self.message, self.context.id)

class ContextParameterSet(models.Model):
    """
    All the information required to run the stage in the context
    """
    context = models.ForeignKey(Context)
    schema = models.ForeignKey(Schema, verbose_name="Schema")
    ranking = models.IntegerField(default=0)

    class Meta:
        ordering = ["-ranking"]
        app_label = "smartconnectorscheduler"

    def __unicode__(self):
        res = "%s contextid=%s" % (self.schema, self.context.id)
        # res = "schema=%s\n" % self.schema
        # res += ('\n'.join([str(cp) for cp in ContextParameter.objects.filter(paramset=self)]))
        return res


class CommandArgument(models.Model):
    """
    A the level of command a representation of a local or remote file or dataset
    NB: unused
    """
    template_url = models.URLField()


class ContextParameter(models.Model):
    name = models.ForeignKey(ParameterName, verbose_name="Parameter Name")
    paramset = models.ForeignKey(ContextParameterSet, verbose_name="Parameter Set")
    value = models.TextField(blank=True, verbose_name="Parameter Value", help_text="The Value of this parameter")
    #ranking = models.IntegerField(default=0,help_text="Describes the relative ordering of parameters when displaying: the larger the number, the more prominent the results")

    def __unicode__(self):
        return u'%s = %s' % (self.name, self.value)

    def getValue(self,):
        try:
            val = self.name.get_value(self.value)
        except ValueError:
            logger.error("cp:got bad value %s" % self.value)
            raise
        return val

    class Meta:
        ordering = ("name",)


class StageParameterSet(models.Model):
    """
    All the information required to run the stage in the context
    """
    stage = models.ForeignKey(Stage)
    schema = models.ForeignKey(Schema, verbose_name="Schema")
    ranking = models.IntegerField(default=0)

    class Meta:
        ordering = ["-ranking"]
        # app_label = "smartconnectorscheduler"

    def __unicode__(self):
        res = "%s (ns=%s, stage=%s)" % (self.schema, self.schema.namespace, self.stage.name)
        # res = "schema=%s\n" % self.schema
        # res += ('\n'.join([str(cp) for cp in StageParameter.objects.filter(paramset=self)]))
        return res


class StageParameter(models.Model):
    name = models.ForeignKey(ParameterName, verbose_name="Parameter Name")
    paramset = models.ForeignKey(StageParameterSet, verbose_name="Parameter Set")
    value = models.TextField(blank=True, verbose_name="Parameter Value", help_text="The Value of this parameter")
    #ranking = models.IntegerField(default=0,help_text="Describes the relative ordering of parameters when displaying: the larger the number, the more prominent the results")

    def __unicode__(self):
        return u'%s =  %s' % (self.name, self.value)

    def getValue(self,):
        try:
            val = self.name.get_value(self.value)
        except ValueError:
            logger.error("sp:got bad value %s" % self.value)
            raise
        return val

    class Meta:
        ordering = ("name",)


class Preset(models.Model):
    name = models.CharField(max_length=121)
    user_profile = models.ForeignKey(UserProfile, verbose_name="User Profile")
    directive = models.ForeignKey(Directive)

    def __unicode__(self):
        return "name=%s\nuser_profile=%s\ndirective=%s\n" % (self.name, self.user_profile, self.directive)

    class Meta:
        ordering = ("name",)
        unique_together = (('name', 'user_profile'),)


class PresetParameterSet(models.Model):
    preset = models.ForeignKey(Preset, verbose_name="Preset")
    #schema = models.ForeignKey(Schema, verbose_name="Schema")
    ranking = models.IntegerField(default=0)

    def __unicode__(self):
        return "preset=%s" % (self.preset)

    class Meta:
        ordering = ("ranking",)


class PresetParameter(models.Model):
    name = models.ForeignKey(ParameterName, verbose_name="Preset Parameter Name")
    paramset = models.ForeignKey(PresetParameterSet, verbose_name="Preset Parameter Set")
    value = models.TextField(blank=True, verbose_name="Preset Parameter Value", help_text="The Value of this parameter")

    def __unicode__(self):
        # FIXME: be cautious here, self.value is UNTRUSTED and should not
        # be displayed to user without appropriate processing.
        return "%s (%s)=%s" % (self.name, self.paramset, self.value)

    class Meta:
        ordering = ("name",)

#def create_api_key_wrapper(sender, **kwargs):
#    from tastypie.models import create_api_key
#    create_api_key(sender, **kwargs)

#models.signals.post_save.connect(create_api_key_wrapper, sender=User)
