# Slack Bot Service for Sunbird AI Assistant
This repo provides the MVP implementation of a backend service for integration between Slack and Sunbird AI Assistant.

That is, to enable slack as a channel for Sunbird AI Assistant.

## Versions: 

### Current Version: 0.1.0-beta

Changes:
1. implement and enabled user to choose different context (bot)
2. enhance language change, please see below
3. when either bot or language has been changed, a welcome DM will send to user
4. for both context and language, user can use either /commend or app home screen button to select context/language
5. original file of main.py, that is slack-channel-svc.py has been removed in the repository

### Previous version: 0.0.2-beta

Changes:
1. re-implemented the api with FastAPI, instead of using default bolt server
2. implemented and enabled user to choose different language
3. as language is now availabe, REDIS is a MUST
4. introduced a MANDATORY config value in env, i.e. SUPPORTED_LANGUAGES 
5. the filename of api/main has been renamed to main.py 

### Previous version: 0.0.1-beta

Initial MVP implementation, these are the assumption
- on English is being enabled.
- the service is hardcoded to points to activity API using teacher as context (that is the teacher bot)
- the source code is current running in development mode - run in box with python installed

## Installation
1. have a box (VM) with python installed
2. create a virtual environment (recommend) and activate the venv
3. clone the repo and cd to the repo folder
4. checkout the relavent branch, e.g. `git checkout -b slack-bot-0.0.2-beta`
6. create a .env file `cp env.sample.env .env`
7. create a App in Slack, assign the required scope and get the bot-token, signing secret
8. edit the .env and put the required information, you might need to change other values according to your environment
9. install the dependencies `pip install -r requirements.txt`
10. start the slack bot service with `uvicorn main:api --reload --port 8080 --host 0.0.0.0 --log-level info ` you can adjust the port, host, log-level accordingly

If you are fronting the service with API gateway, remember to create the corresponding deployment and routes

## To-Do

Here are the to-do list
- implement choosing language (partially completed in 0.0.2-beta)
- implement choosing the bot, aka context (partially completed in 0.1.0-beta)
- implement other functions, such as help, etc
- create the Dockerfile to enable the service to run as container
- create the Helm charts for deployment in K8S 