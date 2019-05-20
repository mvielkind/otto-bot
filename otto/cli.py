import click
import json
from otto.validate import InputValidation
from .utilities import setup_twilio_client, get_attribute_config_items, echo_format_msg, get_assistant_names
from .resources import Assistant, FieldType, Task, ModelBuild


@click.group()
def handler():
    pass


@handler.command()
def init():
    """
    Creates an empty deployment file to serve as a template for defining your chatbot.
    :return:
    """
    copilot_settings = {
        "assistant": {
            "unique_name": "",
            "friendly_name": "",
            "defaults": {
                "defaults": {
                    "assistant_initiation": "",
                    "fallback": "",
                    "collect": {
                        "validate_on_failure": ""
                    }
                }
            }
        },
        "field_type__custom1": {
            "unique_name": "",
            "friendly_name": "",
            "values": []
        },
        "task__custom1": {
            "unique_name": "",
            "friendly_name": "",
            "actions": {
                "actions": [

                ]
            },
            "task_fields": [
                {
                    "unique_name": "",
                    "field_type": ""
                }
            ],
            "samples": []
        },
        "model": {
            "unique_name": ""
        }
    }

    with open("model-deploy-no-tasks.json", "w") as f:
        json.dump(copilot_settings, f, indent='\t')


@handler.command()
@click.argument("config_loc")
@click.option('--overwrite', default=False, is_flag=True)
def deploy(config_loc, overwrite):
    """
    Deploys a Twilio Autopilot model based on the configuration file provided.

    :param config_loc: Location of the configuration file to deploy.
    :param overwrite: Boolean flag indicating if a model should be overwritten if it exists.
    :return:
    """
    # Setup the Twilio client with the provided authorization.
    response = setup_twilio_client()
    if not response["STATUS"]:
        echo_format_msg(response["Message"])
        exit()

    client = response["Payload"]

    # Load and validate the configuration file.
    config = json.load(open(config_loc, "r"))
    input_validation = InputValidation(config)

    if not input_validation.validate_input():
        click.echo(click.style("DEPLOY FAILED.  See above for areas to improve.", fg='red'), nl=True)
        exit()
    else:
        click.echo("\n")
        click.echo(click.style("VALIDATION PASSED!", fg="green"), nl=True)

    # Get the assistant if it exists or create a new one.
    assistant = Assistant(client.autopilot, **config["assistant"])

    if (assistant.exists() is True) & (overwrite is False):
        response = input("Assistant already exists."
                         "Overwriting the assistant will create a new assistant based on your configuration, which"
                         "could cause some existing resources to be deleted.\n\n"
                         "Do you want to overwrite the existing assistant (y/n)? ")

        if response.lower() != "y":
            msg = "DEPLOY FAILED: Assistant already exists.  You can overwrite the current assistant or create a new" \
                  "one with a different name."
            click.echo(click.style(msg, fg="red"))
            exit()

    assistant = assistant.fetch_or_create()

    # Setup any custom fields that are used by the assistant.
    for field_type_key, field_type_definition in get_attribute_config_items(config, "field_types__").items():
        field_type = FieldType(**field_type_definition).create(assistant)
        msg = "COMPLETED: Custom field type {} has been created.".format(field_type.unique_name)
        echo_format_msg(msg)

    # Add Tasks to the chatbot.
    config_tasks = {k: v for (k, v) in config.items() if k.startswith("task__")}
    for task_key, task_definition in config_tasks.items():
        task = Task(**task_definition).create(assistant)
        msg = "COMPLETED: Task {} has been created.".format(task.unique_name)
        echo_format_msg(msg)

    # Now train the model.
    model = ModelBuild(**config.get("model")).create(assistant)
    msg = "COMPLETED: Model {} has been created.".format(model.unique_name)
    echo_format_msg(msg)

    msg = "SUCCESS!  Your Twilio Autopilot Assistant '{}' has been deployed!".format(assistant.unique_name)
    click.echo(click.style(msg, fg="green"))


@handler.command()
@click.argument("autopilot_sid")
def teardown(autopilot_sid):
    """
    Tears down an Autopilot bot working through the resource hierarchy.  All resources associated with the bot
    will be deleted.

    :param autopilot_sid: The unique identifier of the bot.
    :return:
    """
    client = setup_twilio_client()

    # Get the assistant.  Raise error if doesn't exist.
    try:
        assert autopilot_sid in get_assistant_names(client)
    except AssertionError:
        msg = "FAIL: There is no assistant with the identifier {} to teardown.  Check if the Assistant exists and " \
              "try again.".format(autopilot_sid)
        echo_format_msg(msg)
        exit()

    assistant = client.autopilot.assistants(autopilot_sid).fetch()

    # Begin by removing tasks.
    for t in assistant.tasks.list():

        # Remove all samples.
        for s in t.samples.list():
            s.delete()

        # Remove all fields.
        for f in t.fields.list():
            f.delete()
        t.delete()

    # Remove any custom field types.
    for field_type in assistant.field_types.list():

        for field_value in field_type.field_values.list():
            field_value.delete()

        field_type.delete()

    # Remove models.
    for model in assistant.model_builds.list():
        model.delete()

    assistant.delete()

    msg = "SUCCESS! The '{}' assistant and all of its related resources have been deleted.".format(autopilot_sid)
    click.echo(click.style(msg, fg="green"))


if __name__ == "__main__":
    handler()
