# Slack

## Installation

1. Clone this repo.
2. [Create a bot](https://my.slack.com/services/new/bot) and copy the API token.
3. Fill `bot/config.py` with your credentials. This step is required.

## Running bot locally

1. cd into project folder.
2. `sudo chmod a+x bin/bot`
3. `make run`

## Deploying on heroku

1. cd into project folder.
2. `git push heroku master`
3. `heroku ps:scale worker=1`
4. `heroku ps` to check that bot is up and running.
