import os
import click
from twilio.rest import Client
from twilio.base.exceptions import TwilioException


def get_attribute_config_items(config, attribute):
    return {k: v for (k, v) in config.items() if k.startswith(attribute)}


def setup_twilio_client():
    """
    Sets up the Twilio client that will be used based on the authentication of the user.
    :return: Returns a Twilio Client object.
    """
    response = {
        "STATUS": "PASS"
    }
    try:
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]

        client = Client(account_sid, auth_token)

        # Capture if authentication failed.
        client.autopilot.assistants.list()

        response["Payload"] = client
    except KeyError as e:
        response["STATUS"] = "FAIL"
        response["Message"] = "FAIL: Check that your Twilio environmental variables have been configred correctly."
    except TwilioException:
        response["STATUS"] = "FAIL"
        response["Message"] = "FAIL: Double check your Twilio credentials are correct."

    return response


def get_assistant_names(client):
    """
    Gets the names of all the assistants associated with the Twilio client.
    :param client: Twilio client object.
    """
    return [assistant.unique_name for assistant in client.autopilot.assistants.list()]


def echo_format_msg(msg):
    """
    Colors a message according to the status that is implied.
    :param msg: Text of message to color.
    """
    color_map = {
        "INFO": "blue",
        "FAIL": "red",
        "COMPLETED": "green",
        "SUCCESS": "green"
    }

    intent = msg.split(":")[0]

    click.echo(click.style(msg, fg=color_map[intent]), nl=True)
