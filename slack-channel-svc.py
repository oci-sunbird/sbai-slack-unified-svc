import os
import json
import redis
import requests
# Use the package we installed
from dotenv import load_dotenv
from slack_bolt import App

# Initialize your app with your bot token and signing secret
load_dotenv()
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

def get_bot_endpoint(contextName: str):
    if contextName == "story":
        return os.environ["STORY_API_BASE_URL"] + '/v1/query_rstory'
    else:
        activity_url = os.environ["ACTIVITY_API_BASE_URL"]
        url =  activity_url + '/v1/query'
        # if CONVERSE_ENABLED:
        #    url = activity_url + '/v1/chat'
        return url

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",

        # body of the view
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Welcome to your _App's Home tab_* :tada:"
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app."
            }
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Click me!"
                }
              }
            ]
          }
        ]
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

@app.message()
def chat_ai(message, say):
    user = message['user']
    # uncomment the print for debug
    # print(message)
    question=message['text']
    message_id=message['client_msg_id']
    # say(f"Hi there, <@{user}>! I am now Please wait, crafting response. It might take upto a minute.")
    say("Please wait, crafting response. It might take upto a minute.")
    selected_context="teacher"
    url = get_bot_endpoint(selected_context)
    reqBody: dict
    reqBody = {
        "input": {
            "language": "en",
            "audienceType": "teacher",
            "text": question
        },
        "output": {
            'format': 'text'
        }
    }
    headers = {
        "x-source": "slack",
        "x-request-id": str(message_id),
        "x-device-id": f"d{user}",
        "x-consumer-id": str(user)
    }
    response = requests.post(url, data=json.dumps(reqBody), headers=headers)
    response.raise_for_status()
    data = response.json()
    # uncomment the print to debug
    print(data)
    say(data['output']['text'])


# Ready? Start your app!
if __name__ == "__main__":

    print("Slack Bot listening port: " + os.environ.get("SLACK_PORT"))
    app.start(port=int(os.environ.get("SLACK_PORT", 3000)))