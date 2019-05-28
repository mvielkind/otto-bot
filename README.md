# otto-bot

otto-bot is a helper utility for deploying chatbots using Twilio's Autopilot.  With otto-bot you can configure your
chatbots locally and on deployment all of the API calls to setup the bot are handled for you.  While I know Twilio has 
its own CLI utility, the primary motivation for this library was to help me learn more about Autopilot and how to deploy
packages to PyPi.  otto-bot is the outcome of that learning experience that I hope others may find beneficial as 
well!


## Getting Started

To use otto-bot you must have a Twilio account with your Twilio account credentials setup as environmental 
variables.  You can find information about signing up for Twilio [here](https://www.twilio.com/docs/sms/tutorials/how-to-send-sms-messages-python)
and setting up your environmental variables [here](https://www.twilio.com/blog/2017/01/how-to-set-environment-variables.html).

Once you have your Twilio account setup, otto-bot can be installed via `pip`:

```bash
pip install otto-bot
```

otto-bot is only configured to work with Python 3.6 and above.  If you have both a Python 2 and Python 3 version 
installed you might need to run the command above using `pip3` instead of `pip`.

Now you're ready to go!

## Configuring your Chatbot
The core of otto-bot is the JSON file defining your chatbot.  The content of your input file will instruct otto-bot
how to deploy your bot to Twilio.  To get started you started there is an `init` command that will generate an empty
JSON file with placeholders for some of the more common elements your chatbot might use.

```bash
otto-bot init
```

By default the `init` command will include a placeholder for model, field type, task, and model build elements.  These
basic settings are enough to get you started with building your chatbot.  How you structure your JSON is influenced by
the Twilio API model itself, so I've included links for where you can get more information about each setting as well as
more advanced settings you can add to the JSON file.

### Basic Settings- assistant
Each bot is defined by a single assistant object.  The assistant object is required for each bot as it is the core
object all the other components will be linked to to create the bot.  The assistant object contains metadata about your
bot and some of the default behaviors.

```
{
  "assistant": {
    "unique_name": "", # Required.  A name to uniquely identify your bot.
    "friendly_name": "", # Optional.  A more descriptive name defining the bot.
    "defaults": { # Optional.  Assigns default actions.
      "defaults": {
        "assistant_initiation": "", # Only used in voice messages to provide a greeting for inbound messages.
        "fallback": "", # How to respond if input can't be routed to a task.
        "collect": {
            "validate_on_failure": "" # What to do if there is an error collecting user input.
        }
      }
    }
  }
}
```

Extra information about settings for the Assistant settings can be found in the [Twilio Assistant Resource](https://www.twilio.com/docs/autopilot/api/assistant)

### Basic Settings- field_type
As a part of your chatbot you can define custom fields that are extracted from the user's input.  A chatbot does not
require you to include a field_type, but a chatbot can include multiple different custom field_types.
In the configuration file each field_type is defined with a prefix "field_type__" and must be uniquely named.  An
example definition is below:

```
{
  "field_type__your_custom_field": {
    "unique_name": "", # Required.  Unique name identifying your custom field type.
    "friendly_name": "", # Optional.  A more descriptive name defining the field type.  
    "values": [] # Required.  A list of values defining the field.
  }
}
```

You can find further details about this settings here: [Twilio FieldType Resource](https://www.twilio.com/docs/autopilot/api/field-type)

### Basic Settings- tasks
Tasks are the core of what dictates how your chatbot will interact with messages.  Your chatbot must contain at least
one task.  In the JSON file each a task is defined with the "task__" prefix and contains the following information:

```
{
  "task__your_task": {
    "unique_name": "", # Required.  Unique name identifying the task.
    "friendly_name": "", # Optional.  Most descriptive name defining the task.
    "actions": { # Required.  A list of actions your task should take.
      "actions": []
    },
    "task_fields": [ # Optional.  If your task uses custom fields you must define them here.
      {
        "unique_name": "", # Required.  Unique name identifying the field for the task.
        "field_type": "" # Required.  Field type to assign to the field.  Could be custom, or a Twilio default field.
      }
    ],
    "samples": [] # Required.  List of key phrases that will trigger this task.
  }
}
```

More details about these settings and additional settings are here: [Twilio Task Resource](https://www.twilio.com/docs/autopilot/api/task).

### Basic Settings- model
The last component of the JSON file is the "model".  The most build component tells Twilio to build the actual model 
using everything defined in the rest of the JSON file.

```
{
  "model": {
    "unique_name": "" # Required.  Unique name to identify the model.
  }
}
```

See here for extra details: [Twilio ModelBuild Resource](https://www.twilio.com/docs/autopilot/api/model-build).


## Deploying your Chatbot
Once you've defined your chatbot in the JSON file you can deploy the chatbot to Twilio with the following:

```bash
otto-bot deploy chatbot-config.json [--overwrite]
```

The `deploy` command reads the configuration JSON and will make all the API calls that are required.  By default
otto-bot will deploy the bot exactly as defined in your JSON.  If you have a chatbot that already exists all associated
resources with the chatbot will be deleted and replaced with the resources currently defined in the JSON file.  You can
use the `--overwrite` option to automatically overwrite an existing bot.  Otherwise you will be prompted during
deployment to agree to overwrite the existing bot.

Before deploying the bot a number of validation checks are run on the input file to ensure there are no errors.  These
checks ensure that your bot will successfully deploy without an error before anything starts to get deleted.  In 
addition to doing the error checking alerts will be raised about best practices that aren't necessarily errors, but
that could help improve your bot.  These checks will capture many common errors, but are not entirely robust.  As new
errors are discovered I'll keep these validation checks up-to-date.

### Deployment Limitations
otto-bot handles a lot, but not all aspects of your bot's deployment.  Twilio currently does not have an API for 
deploying custom Runtime functions.  If you want to include a custom Runtime function with your bot you will need
to define that function through the Twilio console.

A second limitation is that once your bot is deployed you will have to go into the Twilio console and attach your
bot to the channel you would like to deploy to.


## Deleting a Chatbot
So, you've deployed a chatbot and don't want to use it anymore, the `teardown` command will delete your bot and all
the resources associated with it.

```bash
otto-bot teardown unique_name
```

You can call the `teardown` command along with the unique_name of the bot you want to delete and your bot will be
deleted.


## Getting Started- Examples

In the [examples](https://github.com/mvielkind/otto-bot/tree/master/examples) directory there is a worked 
example using the Twilio [Deep Table Autopilot Tutorial](https://www.twilio.com/docs/autopilot/tutorials/deep-table-restaurant-assistant)
, demonstrating how otto-bot can be utilized.


## What's Next
I've learned a lot about Twilio Autopilot through this process.  From this process there are a number of initial 
enhancements I want to add.  If there is any other functionality you'd like to see let me know and I'll make sure it
gets added!