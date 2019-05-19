import os
import click
from twilio.rest import Client
from click.exceptions import ClickException


def get_attribute_config_items(config, attribute):
    return {k: v for (k, v) in config.items() if k.startswith(attribute)}


def setup_twilio_client():
    """
    Sets up the Twilio client that will be used based on the authentication of the user.
    :return: Returns a Twilio Client object.
    """
    # TODO: Handle when Twilio authentication fails.
    try:
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]

        client = Client(account_sid, auth_token)
    except KeyError as e:
        raise ClickException("Missing authentication environmental variable '{}'.".format(e))

    return client


def get_assistant_names(client):
    """

    :param client:
    :return:
    """
    return [assistant.unique_name for assistant in client.autopilot.assistants.list()]


def echo_format_msg(msg):
    """

    :param msg:
    :return:
    """
    color_map = {
        "INFO": "blue",
        "FAIL": "red",
        "COMPLETED": "green",
        "SUCCESS": "green"
    }

    intent = msg.split(":")[0]

    click.echo(click.style(msg, fg=color_map[intent]), nl=True)
