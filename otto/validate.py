import re
import click
from collections import Counter
from otto.utilities import echo_format_msg


class InputValidation:

    def __init__(self, config):
        self.config = config
        self.validation_pass = True

    def required_parameters(self):
        """
        Each input file must have:
            - An assistant resource.
            - At least 1 task resource.
            - A Model Build resource.
        """
        click.echo("CHECKING BASE FILE FORMAT....")
        required_tags = ["assistant", "model"]
        missing_tags = list(set(required_tags) - set(self.config.keys()))

        if missing_tags:
            missing_str = ", ".join(missing_tags)
            msg = "FAIL: Configuration file is missing the required element(s): {}".format(missing_str)
            echo_format_msg(msg)
            self.validation_pass = False

        if not any(k.startswith("task__") for k in self.config.keys()):
            msg = "FAIL: Your Assistant has no tasks defined.  Must have at least 1 task."
            echo_format_msg(msg)
            self.validation_pass = False

    def validate_task(self, lbl, task):
        """
        Each task must have:
            - At least 1 sample.
            - A Field if custom field identified in samples
            - If a custom field exists in a sample there must be a corresponding field resource in the task
            - If task has a `collect` action make sure `on_complete` is a `redirect` action.
            - A task cannot have multiple instances of the same action.
        """
        if "actions" not in task:
            msg = "INFO: Task `{}` has no actions associated with it.".format(lbl)
            echo_format_msg(msg)
        elif "actions" not in task["actions"]:
            msg = "FAIL: Actions object in task `{}` is misformed.".format(lbl)
            echo_format_msg(msg)
            self.validation_pass = False
        else:
            task_actions = task["actions"]["actions"]
            for ta in task_actions:
                try:
                    collect_action = ta["collect"]["on_complete"]
                    assert list(collect_action.keys()) == ["redirect"]
                except KeyError:
                    continue
                except AssertionError:
                    collect_action = ta["collect"]["on_complete"]
                    str_exists = ", ".join(collect_action.keys())
                    msg = "FAIL: In `{}` the `on_complete` action for `collect` must be a `redirect`.  You used a `{}` action".\
                        format(lbl, str_exists)
                    echo_format_msg(msg)
                    self.validation_pass = False

            # Check if actions are repeated in the task.
            action_counts = Counter([list(action.keys())[0] for action in task_actions])
            for action, counts in action_counts.items():
                if counts > 1:
                    msg = "FAIL: In task `{}` you have multiple `{}` actions. Can only have one.".format(lbl, action)
                    echo_format_msg(msg)
                    self.validation_pass = False

        # Check if task has samples associated with it.
        try:
            n_samples = len(task["samples"])

            if n_samples == 0:
                msg = "FAIL: There are no samples provided for '{}'".format(lbl)
                echo_format_msg(msg)
                self.validation_pass = False
            elif n_samples < 10:
                msg = "INFO: Task `{}` only has `{}` samples.  Recommended to have at least 10.".format(lbl, str(n_samples))
                echo_format_msg(msg)
        except KeyError:
            msg = "FAIL: There are no samples provided for '{}'".format(lbl)
            echo_format_msg(msg)
            self.validation_pass = False

        # Check that task fields are defined.
        for task_field in task.get("task_fields", []):
            if "unique_name" not in task_field:
                msg = "FAIL: A task field in '{}' is missing a unique_name.".format(lbl)
                echo_format_msg(msg)
                self.validation_pass = False

            if "field_type" not in task_field:
                msg = "FAIL: A task field in '{}' is missing a field_type.".format(lbl)
                echo_format_msg(msg)
                self.validation_pass = False

        # Make sure samples with custom fields have a defined field.
        missing_fields = []
        task_field_labels = [tf["unique_name"] for tf in task.get("task_fields", [])]
        for sample in task.get("samples", []):
            if isinstance(sample, dict):
                sample = sample["tagged_text"]

            for custom_field in re.findall(r"\{(\w+)\}", sample):
                if custom_field not in task_field_labels:
                    missing_fields.append(custom_field)

        if missing_fields:
            missing_fields_str = ", ".join(list(set(missing_fields)))
            msg = "FAIL: Task `{}` contains undefined custom fields.  Make sure your task includes these fields: `{}`".\
                format(lbl, missing_fields_str)
            echo_format_msg(msg)
            self.validation_pass = False

    def validate_assistant(self, lbl, assistant):
        """
        Check the assistant for properly formatted input.

        Specifically checks how the `defaults` parameters is formatted if it is used.
        """
        # Check that defaults are defined correctly in Assistant.
        if "defaults" in assistant:
            if "defaults" not in assistant["defaults"]:
                msg = "FAIL: The `defaults` parameter for Assistant `{}` is not formed properly.".format(lbl)
                echo_format_msg(msg)
                self.validation_pass = False
            else:
                if not all(x in assistant["defaults"]["defaults"] for x in ["assistant_initiation", "fallback"]):
                    msg = "INFO: For Assistant `defaults` to take effect you must minimally specify a " \
                          "default for `assistant_initiation` and `fallback`.  Check Assistant `{}` " \
                          "for missing parameters".format(lbl)
                    echo_format_msg(msg)

    def validate_field_type(self, lbl, assistant):
        """
        Check that custom field types have values associated with them.  Will not cause a critical error, but does
        alert when values are missing since they aren't really useful without defining values.
        """
        # Raise a warning if no values associated with a field type.
        if ("values" not in assistant) or (len(assistant["values"]) == 0):
            msg = "INFO: Custom Field Type `{}` has no values associated with it.".format(lbl)
            echo_format_msg(msg)

    def validate_input(self):
        """
        Performs the validation on the input configuration file.
        :return: Boolean indicating if a critical error is detected in the input file.
        """
        self.required_parameters()

        # Iterate across tags to check tag specific criteria.
        click.echo("\nCHECKING INDIVIDUAL RESOURCES...")
        for tag, attributes in self.config.items():
            click.echo("\nValidating `{}`...".format(tag))
            if "unique_name" not in attributes:
                msg = "FAIL: `{}` does not have a 'unique_name'".format(tag)
                echo_format_msg(msg)
                self.validation_pass = False

            if tag.startswith("task__"):
                self.validate_task(tag, attributes)
            elif tag == "assistant":
                self.validate_assistant(tag, attributes)
            elif tag.startswith("field_type__"):
                self.validate_field_type(tag, attributes)

        return self.validation_pass
