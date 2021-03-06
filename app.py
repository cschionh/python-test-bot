import os
import sys
import json

import requests
from flask import Flask, request

GRAPH_URL="https://graph.facebook.com"
NOTIFY_GP_ID = "1854531518146187" #test group ID
COMMENT_EDGE = "/comments"
FEED_EDGE = "/feed"
RUN_COMMAND = "*run"

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

@app.route('/security', methods=['GET'])
def security():

    return "Hey there, you are running python test bot with admin_create_account subscription", 200



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
                    if "mention" in changes_event["field"]:
                    # if changes_event["field"].get("mention"):
                        log("inside mention logic...")

                        # determine whether the app is mentioned in a post/comment/reply
                        if changes_event["value"]["item"] == "comment":
                            mention_id = changes_event["value"]["comment_id"]
                        else:
                            mention_id = changes_event["value"]["post_id"]

                        giveLike(mention_id) #give a like to the post/comment/reply

                        # message_tags is a list, hence needs to loop to get each value.
                        # if found the page name, get the name and quit the loop
                        for message_tags in changes_event["value"]["message_tags"]:
                            if message_tags["type"] == "page":
                                mention_bot = message_tags["name"]
                                log("mention_bot={msg1}".format(msg1=mention_bot))
                                pass

                        message_text = changes_event["value"]["message"]
                        log("message_text={msg1}".format(msg1=message_text))
                        # post_id = changes_event["value"]["post_id"]
                        # log("post_id={msg1}".format(msg1=post_id))


                        # appInfo=getAppInfo()
                        # appName=appInfo["name"]

                        # log("mention_bot={msg1} message_text={msg2} post_id={msg3}".format(msg1=mention_bot, msg2=message_text, msg3=post_id))


                        found_message_idx = message_text.find(RUN_COMMAND)
                        if found_message_idx > -1:
                            log("ok to run the job")
                            message_ack="ok to run the job"

                            #call function to execute batch update for all members

                        else:
                            log("cannot run the job")
                            message_ack = "cannot run the job"

                        createPost(message_ack, mention_id, COMMENT_EDGE)

    elif data["object"] == "workplace_security":
        for entry in data["entry"]:
            if "changes" in entry:
                for changes_event in entry["changes"]:
                    if "admin_activity" in changes_event["field"]:
                        newUserID = changes_event["value"]["target_id"]
                        log("new account has been created - newUserID={msg1}".format(msg1=newUserID))
                        message_ack = "new account has been created - newUserID={msg1}".format(msg1=newUserID)
                        createPost(message_ack, NOTIFY_GP_ID, FEED_EDGE)

    return "ok", 200

def getAppInfo():
    params = {
        "fields": "id,name",
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }

    r = requests.get(GRAPH_URL + "/me", params=params, headers=headers)
    result_json = json.loads(r.text, r.encoding)
    log("result_json={msg1}".format(msg1=result_json))

    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return ""
    else:
        return result_json

def giveLike(comment_id):
    log("like a post/comment/reply to {recipient}".format(recipient=comment_id))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post(GRAPH_URL + "/" + comment_id + "/likes", params=params, headers=headers)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def createPost(message_text, comment_id, edge):
    log("creating message to {recipient}: {text}".format(recipient=comment_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "message": message_text
    })
    # r = requests.post(GRAPH_URL + "/" + comment_id + "/comments", params=params, headers=headers, data=data)
    r = requests.post(GRAPH_URL + "/" + comment_id + edge, params=params, headers=headers, data=data)
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
    r = requests.post(GRAPH_URL + "/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()



if __name__ == '__main__':
    app.run(debug=True)
