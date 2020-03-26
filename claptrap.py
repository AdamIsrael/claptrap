import os
import logging
import ssl as ssl_lib

import certifi
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import sqlite3


# Initialize a Flask app to host the events adapter
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(
    os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app
)

# Initialize a Web API client
slack_web_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])


class Claptrap:
    """Encapsulation of Claptrap's personality, err, functionality."""

    version = 0.1
    quotes = [
        "Magic waits for no one, apprentice!",
        "Success! My spell to make you want to hang out with me worked!",
        "Stay a while, and listen. Oh god, please -- PLEASE! -- stay a while.",
    ]

    def __init__(self, *args, **kwargs):
        pass

    def get_help(self):
        return """
        Claptrap version {0}

        Available commands:
        get greeting
        set greeting #channel Success! My spell to make you want to hang out with me worked!
        help

        """.format(self.version)

    def get_greeting(self, channel):

        sql = """
        SELECT greeting FROM greeting WHERE channel = '{}' LIMIT 1
        """.format(
            channel
        )

        rows = self._get(sql)
        for row in rows:
            return row[0]

        return None

    def set_greeting(self, channel, greeting):
        sql = """
        INSERT INTO greeting (channel, greeting) VALUES ('{0}', '{1}')
        ON CONFLICT(channel) DO UPDATE SET greeting='{1}';
        """.format(
            channel, greeting
        )

        self._execute(sql)
        return True

    def not_implemented(self):
        return "Command not implemented."

    def _get_connection(self):
        return sqlite3.connect("claptrap.db")

    def _get(self, sql):

        conn = self._get_connection()
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        return rows

    def _execute(self, sql):
        conn = self._get_connection()
        conn.execute(sql)
        conn.commit()
        conn.close()


claptrap = Claptrap()


def reply(ts, user_id, message):
    """Create and send a reply message to a bot command."""

    response = slack_web_client.im_open(user=user_id)
    channel = response["channel"]["id"]

    message = {
        "ts": ts,
        "channel": channel,
        "username": user_id,
        "text": message,
    }

    response = slack_web_client.chat_postMessage(**message)

    pass


@slack_events_adapter.on("member_joined_channel")
def greeting_message(payload):
    """Create and send an onboarding welcome message to new users. Save the
    time stamp of this message so we can update this message in the future.
    """

    event = payload.get("event", {})
    print(event)

    user_id = event["user"]
    channel_id = event["channel"]

    # Get the greeting for this channel
    greeting = claptrap.get_greeting(channel_id)

    if greeting:
        print("User {} joined channel {}".format(user_id, channel_id))

        response = slack_web_client.im_open(user=user_id)
        channel = response["channel"]["id"]

        # TODO: Make this work with Markdown embedded in the text
        message = {
            "ts": response["ts"],
            "channel": channel,
            "username": user_id,
            "text": greeting,
        }

    response = slack_web_client.chat_postMessage(**message)


# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'.
# Here we'll link the message callback to the 'message' event.
@slack_events_adapter.on("message")
def message(payload):
    """Display the onboarding welcome message after receiving a message
    that contains "start".
    """
    event = payload.get("event", {})
    print("message received: {}".format(event))

    # TODO: Skip messages that aren't directed **to** claptrap

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    ts = event.get("ts")

    # Parse the text into <verb> <message>
    # set greeting <greeting>
    # get greeting

    try:
        # TODO: Clean up the parsing of commands
        fields = text.split(" ")
        verb = fields[0]

        # parse channel to get the channel id
        if verb.lower() == "set":
            (_, noun, channel, payload) = text.split(" ", 3)
            print("Noun: {}".format(noun))

            # HACK: There's probably a better way to get this.
            channel_id = channel.split("|")[0][2:]

            print("Set {} for channel {} to {}".format(noun, channel, payload))
            if noun == "greeting":
                if claptrap.set_greeting(channel_id, payload):
                    print("Greeting set!")
                    # TODO: send a response to slack knows the message was received
                    reply(ts, user_id, "Greeting saved!")

        elif verb.lower() == "get":
            (_, noun, channel) = text.split(" ", 2)

            channel_id = channel.split("|")[0][2:]

            if noun == "greeting":
                reply(ts, user_id, claptrap.get_greeting(channel_id))
        elif verb.lower() == "help":
            reply(ts, user_id, claptrap.get_help())
            print("Help")
    except ValueError as ex:
        # Ignore errors if the tuple is smaller than four
        print(text)
        pass

    # if text and text.lower() == "start":
    #     return start_onboarding(user_id, channel_id)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run(port=3000)
