import os
import json
import redis
import requests
# for getting environment variables
from dotenv import load_dotenv
# from utils import *
from logger import logger
from config_util import get_config_value
from language_util import language_init, get_languages, get_message
# for slack
from slack_bolt import App, Ack
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request 

# Initialize 
# load_dotenv()
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
app_handler = SlackRequestHandler(app)

# get environmnets
redis_host = os.getenv("REDIS_HOST", "172.17.0.1")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_index = int(os.getenv("REDIS_INDEX", "1"))

DEFAULT_CONTEXT = get_config_value('default', 'context', None)
DEFAULT_LANGUAGE = get_config_value('default', 'language', None)
CONVERSE_ENABLED = get_config_value('default', 'converse_enabled').lower() == "true"

# Connect to Redis - this is to store the user info, language and context
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_index) 

# initialize the support language
language_init()

# Define functions to store and retrieve data in Redis
def store_data(key, value):
    redis_client.set(key, value)

def retrieve_data(key):
    data_from_redis = redis_client.get(key)
    return data_from_redis.decode('utf-8') if data_from_redis is not None else None

def get_user_langauge(uid, default_lang=DEFAULT_LANGUAGE) -> str:
    user_id_lan = uid + '_language'
    selected_lang = retrieve_data(user_id_lan)
    if selected_lang:
        logger.info(selected_lang)
        return selected_lang
    else:
        logger.info(default_lang)
        return default_lang

def get_user_context(uid, default_context=DEFAULT_CONTEXT) -> str:
    user_context_id = uid + '_context'
    selected_context = retrieve_data(user_context_id)
    if selected_context:
        return selected_context
    else:
        return default_context            

def get_user_channel(uid, default_channel="null") -> str:
    user_channel_id = uid + '_channel'
    selected_channel = retrieve_data(user_channel_id)
    if selected_channel:
        return selected_channel
    else:
        return default_channel            


def get_bot_endpoint(contextName: str):
    if contextName == "story":
        return os.environ["STORY_API_BASE_URL"] + '/v1/query_rstory'
    else:
        activity_url = os.environ["ACTIVITY_API_BASE_URL"]
        url =  activity_url + '/v1/query'
        print(url)
        # if CONVERSE_ENABLED:
        #    url = activity_url + '/v1/chat'
        return url

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # some debug for testing
    userid=event["user"]
    dm_channel=event["channel"]
    # logger.info(redis_index)
    # logger.info(userid)
    logger.info(event)
    # get current user language
    selected_language = get_user_langauge(userid)
    selected_context = get_user_context(userid)
    logger.debug(selected_language)
    # store user dm channel id for later use
    user_id_channel = userid + '_channel'
    store_data(user_id_channel, dm_channel)
    # get welcome message from user language

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
              "text": "You can switch language and context (bot) with the below buttons."
            }
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "action_id": "select_language",
                "value": "en",
                "text": {
                  "type": "plain_text",
                  "text": "Select Language"
                }
              },
              {
                "type": "button",
                "action_id": "select_context",
                "value": "teacher",
                "text": {
                  "type": "plain_text",
                  "text": "Select Context"
                }
              }
            ]
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "Current Language: " + selected_language
            }
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "Current Context: " + selected_context
            }
          },

        ]
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

@app.action("select_language")
def action_handle(ack, body, client, logger):
   ack()
   logger.info(body)
   # retrieve the list of available language
   logger.info("getting all the languages")
   languages = get_languages()
   # create the list for language selection
   logger.info(languages)
   lang_list = []
   for language in languages:
      lang_list.append({"label": language["text"], "value": language["code"]})
     # lang_list["label"] = language["text"]
     # lang_list["value"] = language["code"] 
     # logger.info({"lang_list: ": lang_list["label"], "language: ":  language["text"]  })
   logger.info(lang_list)
   res = client.dialog_open(
        trigger_id=body["trigger_id"],
        dialog={
            "callback_id": "dialog-callback-language",
            "title": "Select Language",
            "submit_label": "Set",
            "notify_on_cancel": True,
            "state": "dummy",
            "elements": [
                {
                    "label": "Available languages",
                    "name": "language",
                    "type": "select",
                    "options": lang_list
                },
             ],
        },
    )   

@app.action("select_context")
def action_handle_context(ack, body, client, logger):
  ack()
  # debug and dump payload
  logger.info(body)

  uid = body["user"]["id"]
  current_language = get_user_langauge(uid)  
  logger.info({"userid": uid, "current language": current_language})
  
  loc_bot_list = get_message(language=current_language, key="context")
  logger.info(loc_bot_list)
  # build the localized bot list from loaded ini
  bot_list = []
  for loc_bot in loc_bot_list:
    bot_list.append({"label": loc_bot["label"], "value": loc_bot["value"]})
  res = client.dialog_open(
        trigger_id=body["trigger_id"],
        dialog={
            "callback_id": "dialog-callback-bot",
            "title": "Select Bot",
            "submit_label": "Set",
            "notify_on_cancel": True,
            "state": "dummy",
            "elements": [
                {
                    "label": "Available Bot",
                    "name": "bot",
                    "type": "select",
                    "options": bot_list
                },
             ],
        },
  )    

@app.shortcut("select_language")
def shortcut_action_handle(body, client, ack, logger):
   ack()
   logger.info(body)
   # retrieve the list of available language
   logger.info("getting all the languages")
   languages = get_languages()   
   lang_list = []
   for language in languages:
      lang_list.append({"label": language["text"], "value": language["code"]})
     # lang_list["label"] = language["text"]
     # lang_list["value"] = language["code"] 
     # logger.info({"lang_list: ": lang_list["label"], "language: ":  language["text"]  })
   logger.info(lang_list)
   res = client.dialog_open(
        trigger_id=body["trigger_id"],
        dialog={
            "callback_id": "dialog-callback-language",
            "title": "Select Language",
            "submit_label": "Set",
            "notify_on_cancel": True,
            "state": "dummy",
            "elements": [
                {
                    "label": "Available languages",
                    "name": "language",
                    "type": "select",
                    "options": lang_list
                },
             ],
        },
    )   

@app.shortcut("select_context")
def shortcut_handle_context(body, client, ack, logger):
  ack()
  # not implemented in this release
  uid = body["user"]["id"]
  current_language = get_user_langauge(uid)  
  logger.info({"userid": uid, "current language": current_language})
  
  loc_bot_list = get_message(language=current_language, key="context")
  logger.info(loc_bot_list)
  # build the localized bot list from loaded ini
  bot_list = []
  for loc_bot in loc_bot_list:
    bot_list.append({"label": loc_bot["label"], "value": loc_bot["value"]})
  res = client.dialog_open(
        trigger_id=body["trigger_id"],
        dialog={
            "callback_id": "dialog-callback-bot",
            "title": "Select Bot",
            "submit_label": "Set",
            "notify_on_cancel": True,
            "state": "dummy",
            "elements": [
                {
                    "label": "Available Bot",
                    "name": "bot",
                    "type": "select",
                    "options": bot_list
                },
             ],
        },
  )    




@app.action("dialog-callback-language")
def dialog_submission_or_cancellation(ack: Ack, body: dict, client):
    if body["type"] == "dialog_cancellation":
        # This can be sent only when notify_on_cancel is True
        ack()
        return

    errors = []
    submission = body["submission"]["language"]
    uid = body["user"]["id"]
    logger.info({"userid": uid, "language chosen": submission})
    # ack first
    ack()
    # get current language
    current_language = get_user_langauge(uid)
    if current_language == submission:
      # do nothing
      pass
    else:
      # implement set user language
      user_id_lan = uid + '_language'
      store_data(user_id_lan, submission)
      logger.info({"redis key": user_id_lan, "stored new language in redis": submission})
      # republish welcome message as language is now different
      # get user context and dm channel
      current_context = get_user_context(uid)
      dm_channel = get_user_channel(uid)
      # get welcome message 
      welcome_message = get_message(language=submission, key="context_selection")
      loc_welcome = welcome_message[current_context]
      # send DM
      client.chat_postMessage(
        channel=dm_channel,
        text=loc_welcome
      )     

@app.action("dialog-callback-bot")
def bot_submission_or_cancellation(ack: Ack, body: dict, client):
    if body["type"] == "dialog_cancellation":
        # This can be sent only when notify_on_cancel is True
        ack()
        return
    # to be implement later
    ack()
    # get selected context
    submission = body["submission"]["bot"]
    # get current user
    uid = body["user"]["id"]
    # get current context and language
    current_context = get_user_context(uid)
    current_language = get_user_langauge(uid)
    if current_context == submission:
      # do nothing
      pass
    else: 
      # implement set user context
      # update cache
      user_id_context = uid + '_context'
      store_data(user_id_context, submission)
      # get user DM channel to send 
      dm_channel = get_user_channel(uid)
      logger.info({"user dm channel: ": dm_channel})
      # dump the body to verify
      # logger.info(body)
      # get bot welcome message
      welcome_msg = get_message(language=current_language, key="context_selection")
      logger.info(welcome_msg)
      loc_welcome = welcome_msg[submission]
      logger.info(loc_welcome)
      # send DM to user so that she/he knows context changed and how to interact with new bot
      client.chat_postMessage(
        channel=dm_channel,
        text=loc_welcome
      )
    pass

# @app.action("select_context")
# def action_handle(ack, body, logger):
#   ack()
#   logger.info(body)


@app.message()
def chat_ai(message, say):
    user = message['user']
    # uncomment the print for debug
    print(message)
    question=message['text']
    message_id=message['client_msg_id']
    # get user current language
    current_language = get_user_langauge(user)
    selected_context = get_user_context(user)
    logger.info({"userid": user, "current language": current_language})
    # setup localized immediate respponse
    immediate_response = get_message(language=current_language, key="context_loading_msg")
    # say(f"Hi there, <@{user}>! I am now Please wait, crafting response. It might take upto a minute.")
    say(immediate_response)
    # selected_context="teacher"
    url = get_bot_endpoint(selected_context)
    reqBody: dict
    reqBody = {
        "input": {
            "language": current_language,
            "audienceType": selected_context,
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

# register fastapit to handle events
api = FastAPI(title="Sunbird Slack Channel Service",
    redoc_url=None,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    description='',
    version="1.0.0"    
)
@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)
    
@api.on_event("startup")
async def startup_event():
    logger.info('Invoking startup_event')
    # load environment variables
    load_dotenv()
    logger.info('startup_event : Engine created')


# Ready? Start your app!
# if __name__ == "__main__":
#
#    print("Slack Bot listening port: " + os.environ.get("SLACK_PORT"))
#    app.start(port=int(os.environ.get("SLACK_PORT", 3000)))