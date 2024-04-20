# Slack Bot Service for Sunbird AI Assistant
This repo provides the MVP implementation of a backend service for integration between Slack and Sunbird AI Assistant.

That is, to enable slack as a channel for Sunbird AI Assistant.

In the current MVP implementation, these are the assumption
- on English is being enabled.
- the service is hardcoded to points to activity API using teacher as context (that is the teacher bot)
- the source code is current running in development mode - run in box with python installed

## Installation
1. have a box (VM) with python installed
2. create a virtual environment (recommend) and activate the venv
3. clone the repo and cd to the repo folder
4. checkout the relavent branch, e.g. `git checkout -b slack-bot-0.0.1-beta`
6. create a .env file `cp env.sample.env .env`
7. create a App in Slack, assign the required scope and get the bot-token, signing secret
8. edit the .env and put the required information, you might need to change other values according to your environment
9. install the dependencies `pip install -r requirements.txt`
10. start the slack bot service with `python slack-channel-svc.py`

If you are fronting the service with API gateway, remember to create the corresponding deployment and routes


## To-Do

Here are the to-do list
- implement choosing language
- implement choosing the bot, aka context
- implement other functions, such as help, etc
- create the Dockerfile to enable the service to run as container
- create the Helm charts for deployment in K8S 