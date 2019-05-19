import re
import logging
from twilio.base.exceptions import TwilioRestException
from otto.utilities import get_attribute_config_items


def get_resource_params(resource_obj, params):
    return {k: v for (k, v) in resource_obj.items() if k in params}


def teardown_nested_resources(base_resource, nested_resources):
    for resource_type in nested_resources:
        for resource_obj in getattr(base_resource, resource_type).list():
            resource_obj.delete()


class Assistant:

    RESOURCE_PARAMS = ["unique_name", "friendly_name", "log_queries", "style_sheet", "defaults"]

    def __init__(self, twilio_client, unique_name, friendly_name=None, log_queries=True, style_sheet=None,
                 defaults=None):
        """
        An object representing an Autopilot assistant.  Modeled after the Assistant resource from Twilio.

        Twilio Assistant Documentation: https://www.twilio.com/docs/autopilot/api/assistant

        :param twilio_client: The Twilio Client object that will create the assistant.
        :param unique_name: str.  Name given to uniquely identify the assistant.
        :param friendly_name: str.  A user friendly name to assign to the assistant.
        :param log_queries: bool.  Indicates whether queries should be logged or not.
        :param style_sheet: str.  A JSON string identifying the Assistant's stylesheet.
        :param defaults: dict.  A JSON  object defining the default tasks for the Assistant.
        """
        self.twilio_client = twilio_client
        self.unique_name = unique_name
        self.friendly_name = friendly_name
        self.log_queries = log_queries
        self.style_sheet = style_sheet
        self.defaults = defaults

    def validate(self):
        response = {
            "FAIL": [],
            "WARN": []
        }
        # Check that `defaults` attribute is constructed correctly.
        if self.defaults is None:
            return response
        else:
            if "defaults" not in self.defaults:
                response["FAIL"].append("ERROR: The `defaults` parameter for Assistant {} is not formed properly.").\
                    format(self.unique_name)
            else:
                if not all(x in self.defaults["defaults"] for x in ["assistant_initiation", "fallback"]):
                    response["WARN"].append("INFO: For Assistant `defaults` to take effect you must minimally specify a"
                                            "default for `assistant_initiation` and `fallback`.  Check Assistant `{}` "
                                            "for missing parameters").format(self.unique_name)

        return response

    def exists(self):
        """
        Checks whether an assistant exists.
        :return: Boolean indicating if the object exists or not.
        """
        try:
            self.twilio_client.assistants(self.unique_name).fetch()
            return True
        except TwilioRestException:
            return False

    def fetch_or_create(self):
        """
        If an assistant exists then update the assistant with the current parameters and returns the Assistant.

        If the assistant does not exist then create it based on the current values.
        :return: A Twilio AssistantInstance object.
        """
        assistant_params = get_resource_params(self.__dict__, self.RESOURCE_PARAMS)

        try:
            assistant = self.twilio_client.assistants(self.unique_name).fetch()

            # Remove any existing tasks and fields from current assistant.
            for task in assistant.tasks.list():
                Task(task.unique_name).teardown(assistant)

            for field_type in assistant.field_types.list():
                FieldType(field_type.unique_name).teardown(assistant)

            return self.twilio_client.assistants(assistant.sid).update(**assistant_params)
        except TwilioRestException:
            return self.twilio_client.assistants.create(**assistant_params)


class Task:

    RESOURCE_PARAMS = ["unique_name", "friendly_name", "actions", "actions_url"]
    NESTED_RESOURCES = ["samples", "fields"]

    def __init__(self, unique_name, samples=None, friendly_name=None, actions=None, actions_url=None, task_fields=None):
        """
        An object representing a Task for an assistant.

        Twilio Task Documentation: https://www.twilio.com/docs/autopilot/api/task

        :param unique_name: str.  Unique name assigned to the task.
        :param samples: list or dict.  Samples to train the task against.  If list is provided will assume language is
            'en-US' by default.
        :param friendly_name: str.  Friendly name defining the task.
        :param actions: dict.  Expects "actions" as a key and then a list of actions defining the task.
        :param actions_url: URL where the task can fetch actions.
        :param task_fields: list.  A list of Field objects if there are field attributes defined for the task.
        """
        self.unique_name = unique_name
        self.samples = samples
        self.friendly_name = friendly_name
        self.actions = actions
        self.actions_url = actions_url
        self.task_fields = task_fields

    def create(self, assistant):
        """
        Creates a task resource for the given assistant.
        :param assistant: The assistant object to create the task within.
        """
        task_definition = get_resource_params(self.__dict__, self.RESOURCE_PARAMS)

        try:
            task = assistant.tasks(self.unique_name).fetch()
            task = task.update(**task_definition)
        except TwilioRestException:
            task = assistant.tasks.create(**task_definition)

        # Remove any existing samples and fields.
        teardown_nested_resources(task, self.NESTED_RESOURCES)

        # Add any task fields.
        defined_fields = []
        if self.task_fields is not None:
            for task_field in self.task_fields:
                tf = TaskField(**task_field).create(task)
                if tf.unique_name not in defined_fields:
                    defined_fields.append(tf.unique_name)

        custom_fields = []
        for sample in self.samples:
            if isinstance(sample, dict):
                s = Sample(**sample).create(task)
            else:
                s = Sample(tagged_text=sample).create(task)

            for custom_field in re.findall(r"\{(\w+)\}", s.tagged_text):
                if custom_field not in custom_fields:
                    custom_fields.append(custom_field)

        # Check if samples include field types that are not defined.
        missing_fields = set(custom_fields) - set(defined_fields)
        if missing_fields:
            str_missing = ", ".join(missing_fields)
            warn_msg = "The following fields are used in the samples, but have not definition: {}".format(str_missing)
            logging.warning(warn_msg)

        return task

    def teardown(self, assistant):
        """
        Deletes a Task along with any other nested resources (samples and fields) associated with it.
        :param assistant: The assistant object to delete the task from.
        """
        task = assistant.tasks(self.unique_name).fetch()

        # Remove any existing samples and fields.
        teardown_nested_resources(task, self.NESTED_RESOURCES)

        task.delete()


class Sample:

    def __init__(self, tagged_text, language="en-US", source_channel=None):
        """
        A Sample is associated with a Task and is used for training your assistant.  A sample represents a way that
        a user might express themselves to complete the task.

        Twilio Sample Documentation: https://www.twilio.com/docs/autopilot/api/task-sample

        :param tagged_text: str.  Text of the sample.  Might include field tags.
        :param language: str.  Language the tagged_text is in.
        :param source_channel: str.  Channel the sample is coming from (i.e. voice, sms, chat etc.)
        """
        self.tagged_text = tagged_text
        self.language = language
        self.source_channel = source_channel

    def create(self, task):
        """
        Creates a text sample to include in the training of the task.
        :param task: Task object to associate the sample with.
        """
        return task.samples.create(**self.__dict__)


class ModelBuild:

    def __init__(self, unique_name):
        """
        The object of a trained Twilio Autopilot model.

        Twilio Documentation: https://www.twilio.com/docs/autopilot/api/model-build

        :param unique_name: str.  Unique name to identify the model.
        """
        self.unique_name = unique_name

    def create(self, assistant):
        """
        Creates a new model for the given assistant.  Creating the model will train the model against the resources
        included with the assistant.
        :param assistant: Assistant object to train the model for.
        """
        try:
            model = assistant.model_builds(self.unique_name).fetch()
            model = model.update(**self.__dict__)
        except TwilioRestException:
            model = assistant.model_builds.create(**self.__dict__)

        return model


class TaskField:

    def __init__(self, field_type, unique_name):
        """
        Represents attributes expected to be used in the task samples that tell the model where to look for given
        attributes that might be provided by the user.

        Twilio Documentation: https://www.twilio.com/docs/autopilot/api/task-field

        :param field_type: str.  The type of field for the attribute.  Could be a built-in type or a custom field type.
        :param unique_name: str.  Unique name for the field.
        """
        self.field_type = field_type
        self.unique_name = unique_name

    def create(self, task):
        """
        Creates a Field Resource for the task that tells the model to look for a specific attribute when training.
        :param task: Task object to create the field for.
        """
        return task.fields.create(**self.__dict__)


class FieldType:

    RESOURCE_PARAMS = ["unique_name", "field_type"]
    NESTED_RESOURCES = ["field_values"]

    def __init__(self, unique_name, values=None, friendly_name=None):
        """
        Defines a custom Field Type that can be used to capture custom attributes.

        Twilio Documentation: https://www.twilio.com/docs/autopilot/api/field-type

        :param unique_name: str.  Unique name to assign to the
        :param values:
        :param friendly_name:
        """
        self.unique_name = unique_name
        self.field_values = values
        self.friendly_name = friendly_name

    def create(self, assistant):
        """
        Creates the custom field type for the assistant.
        :param assistant: Assistant object to create the custom field for.
        """
        field_type_definition = get_resource_params(self.__dict__, self.RESOURCE_PARAMS)

        try:
            field_type = assistant.field_types(self.unique_name).fetch()
            field_type = field_type.update(**field_type_definition)
        except TwilioRestException:
            field_type = assistant.field_types.create(**field_type_definition)

        # Remove any existing samples and fields.
        teardown_nested_resources(field_type, self.NESTED_RESOURCES)

        for fv in self.field_values or []:
            if isinstance(fv, dict):
                FieldValue(**fv).create(field_type)
            else:
                FieldValue(value=fv).create(field_type)

        return field_type

    def teardown(self, assistant):
        """
        Deletes the field type along with any other nested attributes for the field type.
        :param assistant: Assistant object to delete the field type from.
        """
        field_type = assistant.field_types(self.unique_name).fetch()

        # Remove any existing samples and fields.
        teardown_nested_resources(field_type, self.NESTED_RESOURCES)

        field_type.delete()


class FieldValue:

    def __init__(self, value, language="en-US", synonym_of=None):
        """
        Values to associate with a custom Field Type

        Twilio Documentation: https://www.twilio.com/docs/autopilot/api/field-value

        :param value: str.
        :param language: str.  Language the tagged_text is in.
        :param synonym_of:
        """
        self.language = language
        self.value = value
        self.synonym_of = synonym_of

    def create(self, base_resource):
        return base_resource.\
            field_values.\
            create(**self.__dict__)
