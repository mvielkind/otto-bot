One of the Twilio Autopilot tutorials demonstrates how you can build a bot to make reservations at a restaurant.  To
show how otto-bot works I'm going to walk through how to recreate the tutorial using otto-bot.  In this example we'll
walk through how to configure the JSON file.  There will be 4 sections to the file, an assistant, task__get-specials and
task__make-reservation for each of the two tasks for our assistant, and finally a section defining the model.  Let's
get started by building the `assistant` portion of the JSON.  To help you can run `otto-bot init` to get a blank
configuration file with some of the structure already in place where you can fill in the details where needed.

The `assistant` portion of our JSON should look like this:

```
"assistant": {
  "unique_name": "deep-table-tutorial",
  "friendly_name": "Deep Table Tutorial"
  }
```

For the `assistant` we are just assigning a name to our assistant.  Next, we're going to create our first task,
`get-specials` that will display the daily special when prompted.  To do this we need to add a new element to our JSON
with the configuration for this task.

```
"task__get-specials": {
"unique_name": "get-specials",
"friendly_name": "Get the Daily Specials",
"actions": {
  "actions": [
    {
      "say": "Todays special is duck confit with roasted brussel sprouts"
    },
    {
      "listen": true
    }
  ]
},
"samples": [
  "What's today's special?",
  "What's today's specials?",
  "what is the special today",
  "do you have a special today",
  "what do you have for special today",
  "I want today's special",
  "dinner special",
  "today's special",
  "get today's special",
  "Can you tell me what's today's special",
  "are there any specials",
  "specials"
]
}
```

In this task the daily special will be returned if someone sends a message related to the samples of the text
provided.

The second task is `make-reservation`.  In this task the bot will collect information from the user about their name,
desired date/time for the reservation, and party size.  To incorporate this task we'll add another component to our
JSON file:

```
"task__make-reservation": {
  "unique_name": "make-reservation",
  "friendly_name": "Make a Reservation",
  "actions": {
    "actions": [
      {
        "collect": {
          "name": "make_reservation",
          "questions": [
            {
              "question": {
                "say": "Great, I can help you with that. What's your first name?"
              },
              "name": "first_name",
              "type": "Twilio.FIRST_NAME"
            },
            {
              "question": {
                "say": "When day would you like your reservation for?"
              },
              "name": "date",
              "type": "Twilio.DATE"
            },
            {
              "question": {
                "say": "Great at what time?"
              },
              "name": "time",
              "type": "Twilio.TIME"
            },
            {
              "question": {
                "say": "For how many people"
              },
              "name": "party_size",
              "type": "Twilio.NUMBER"
            }
          ],
          "on_complete": {
            "redirect": {
              "uri": "REPLACE THIS!!!",
              "method": "POST"
            }
          }
        }
      }
    ]
  },
  "samples": [
    {
      "language": "en-US",
      "tagged_text": "book a table"
    },
    {
      "language": "en-US",
      "tagged_text": "make a reservation"
    },
    {
      "language": "en-US",
      "tagged_text": "I want to make a reservation"
    },
    {
      "language": "en-US",
      "tagged_text": "I need a table"
    },
    {
      "language": "en-US",
      "tagged_text": "I want to book a table"
    },
    {
      "language": "en-US",
      "tagged_text": "I'd like to make a reservation please"
    },
    {
      "language": "en-US",
      "tagged_text": "I would like to make a reservation"
    },
    {
      "language": "en-US",
      "tagged_text": "I'm looking for a table for dinner"
    },
    {
      "language": "en-US",
      "tagged_text": "make reservation"
    },
    {
      "language": "en-US",
      "tagged_text": "make reservation please"
    }
  ]
}
```

Unlike in the `get-specials` task where we simply provided a list
of sample text strings for the task, in `make-reservation` we supplied a list of objects where we can define the 
language of the sample.  By default all `samples` will be assumed to be English, but there is flexibility to explicitly
define the language for a text sample.  We are not quite done with this task.  Notice the last action of the task,
`on_complete`, where the `uri` attribute has some placeholder text.  We're going to have to create a Runtime function
and paste the link here since Runtime functions cannot be deploy via the API, so we'll revisit that piece.

Finally, the last segment we need in our JSON file is for `model` where we'll just provide a name for our model.

```
"model": {
  "unique_name": "v0.01"
}
```

Just like that we're almost done!  To check your JSON file should look like this [example](https://github.com/mvielkind/otto-bot/blob/master/examples/deep-table-tutorial.json).
  
There is one catch, one thing we cannot do with otto-bot is deploy Runtime functions,
which the Deep Table tutorial does use, so we'll have to go into the console to create our function and make one more
edit to our JSON before we can deploy.

-Sign into the Twilio console and go to **Runtime -> Functions** and create a blank function
-Name the function *deep-table* and make sure the file path is *deep-table*
-Paste the code below and save

```javascript
exports.handler = function(context, event, callback) {
    var moment = require('moment');
    let responseObject = {};
  
  let memory = JSON.parse(event.Memory)

  let first_name = memory.twilio.collected_data.make_reservation.answers.first_name.answer || '';
  let reservation_date = memory.twilio.collected_data.make_reservation.answers.date.answer || '';
  let reservation_time = moment(memory.twilio.collected_data.make_reservation.answers.time.answer, "hhmm").format("HH:mm a") || '';
  let party_size = memory.twilio.collected_data.make_reservation.answers.party_size.answer || '';

  console.log("First name: "+first_name );
  console.log("Reservation date: "+reservation_date);
  console.log("Reservation time: "+reservation_time);
  console.log("Party size: "+party_size);

  let message = "Ok "+first_name+". Your reservation for "+reservation_date+" at "+reservation_time+" for "+party_size+" people is now confirmed. thank you for booking with us";
  responseObject = {"actions":[
    { "say": { "speech": message } }
    ]};
    callback(null, responseObject);
};
```

Copy the function URL and paste the link in the `on-complete` action of the `make-reservations` task.  Now we're
ready to deploy!  Deploying is as easy as:

```bash
otto-bot deploy deep-table-tutorial.json
```

The last step is to go into the Twilio console and copy the Autopilot Assistant link to the webhook for your Twilio
number.  Go to your Autopilot assistants in the Twilio console, click on the "Deep Restaurant Tutorial", select the
"Programmable Messaging" channel, copy the URL, and paste it as the webhook for your Twilio number.