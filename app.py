import os
import sys
import json

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hey there, you are running python test bot", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            if "messaging" in entry:  # messaging in work chat
                for messaging_event in entry["messaging"]:

                    if messaging_event.get("message"):  # someone sent us a message

                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        message_text = messaging_event["message"]["text"]  # the message's text

                        send_message(sender_id, "roger that!")

                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        pass
            elif "changes" in entry: # mention in group
                for changes_event in entry["changes"]:
                    log(changes_event)
                    # if changes_event["mention"]:
                    # log("mention={msg1}".format(msg1=changes_event["mention"]))
                    # if "mention" in changes_event["field"]:
                    if changes_event["field"].get("mention"):
                        log("inside mention logic...")
                        mention_bot = changes_event["value"]["message_tags"]["name"]
                        log("mention_bot={msg1}".format(msg1=mention_bot))
                        message_text = changes_event["value"]["message"]
                        log("message_text={msg1}".format(msg1=message_text))
                        post_id = changes_event["value"]["post_id"]
                        log("post_id={msg1}".format(msg1=post_id))

                        # log("mention_bot={msg1} message_text={msg2} post_id={msg3}".format(msg1=mention_bot, msg2=message_text, msg3=post_id))


                        # found_message = message_text.find(mention_bot)
                        # trim_message = message_text[found_message+1:len(message_text)]
                        # trim_message = trim_message.lstrip()

                        # log("trim_message={msg1} found_message={msg2}".format(msg1=trim_message, msg2=found_message))

                        # if trim_message == "run":
                        #     createPost("ok to " + trim_message, comment_id)
                        # else:
                        #     createPost("Not ok to " + trim_message, comment_id)

    return "ok", 200


def createPost(message_text, comment_id):
    log("creating message to {recipient}: {text}".format(recipient=comment_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com" + "/" + comment_id + "/comments", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()



if __name__ == '__main__':
    app.run(debug=True)
