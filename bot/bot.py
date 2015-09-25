#!/usr/bin/env python

import copy
import functools
from glob import glob
import importlib
import logging
import os
import re
import sys
import time
import traceback

from config import config
from .slackclient import SlackClient


CURDIR = os.path.abspath(os.path.dirname(__file__))
DIR = functools.partial(os.path.join, CURDIR)

logger = logging.getLogger(__name__)

class Server(object):
    def __init__(self, slack, config, hooks):
        self.slack = slack
        self.config = config
        self.hooks = hooks


class InvalidPluginDir(Exception):
    def __init__(self, plugindir):
        self.message = "Unable to find plugin dir {0}".format(plugindir)


def init_server(args, config):
    init_log(config)
    logger.debug("config: {0}".format(config))

    hooks = init_plugins(args.pluginpath)

    try:
        slack = SlackClient(config["slack_token"])
    except KeyError:
        logger.error("Unable to find a slack token.")
        raise
    server = Server(slack, config, hooks)
    return server


def init_log(cfg):
    loglevel = cfg.get("loglevel", logging.INFO)
    logformat = cfg.get("logformat", '%(asctime)s:%(levelname)s:%(name)s:%(message)s')

    if cfg.get("logfile"):
        logging.basicConfig(filename=cfg.get("logfile"), format=logformat, level=loglevel)
    else:
        logging.basicConfig(format=logformat, level=loglevel)


def init_plugins(plugindir):
    if not plugindir:
        plugindir = DIR("plugins")

    logger.debug("plugindir: {0}".format(plugindir))

    if not os.path.isdir(plugindir):
        raise InvalidPluginDir(plugindir)

    hooks = {}

    oldpath = copy.deepcopy(sys.path)
    sys.path.insert(0, plugindir)

    for plugin in glob(os.path.join(plugindir, "[!_]*.py")):
        logger.debug("plugin: {0}".format(plugin))
        try:
            mod = importlib.import_module(os.path.basename(plugin)[:-3])
            modname = mod.__name__

            for hook in re.findall("on_(\w+)", " ".join(dir(mod))):
                hookfun = getattr(mod, "on_" + hook)
                logger.debug("plugin: attaching %s hook for %s", hook, modname)
                hooks.setdefault(hook, []).append(hookfun)

            if mod.__doc__:
                firstline = mod.__doc__.split('\n')[0]
                hooks.setdefault('help', {})[modname] = firstline
                hooks.setdefault('extendedhelp', {})[modname] = mod.__doc__

        # bare except, because the modules could raise any number of errors
        # on import, and we want them not to kill our server
        except:
            logger.warning("import failed on module {0}, module not loaded".format(plugin))
            logger.warning("{0}".format(sys.exc_info()[0]))
            logger.warning("{0}".format(traceback.format_exc()))

    sys.path = oldpath
    return hooks


def run_hook(hooks, hook, *args):
    responses = []
    for hook in hooks.get(hook, []):
        try:
            h = hook(*args)
            if h:
                responses.append(h)
        except:
            logger.warning("Failed to run plugin {0}, module not loaded".format(hook))
            logger.warning("{0}".format(sys.exc_info()[0]))
            logger.warning("{0}".format(traceback.format_exc()))

    return responses


def handle_event(event, server):
    event_handlers = {
        "message": handle_message,
    }

    handler = event_handlers.get(event.get("type"))
    if handler:
        return handler(event, server)

    return None


def handle_message(event, server):
    # ignore bot messages and edits
    subtype = event.get("subtype", "")
    if subtype == "bot_message" or subtype == "message_changed":
        return

    # ignore regular messages
    message = event.get('text')
    if not message or not message.startswith('!'):
        return

    botname = server.slack.server.login_data["self"]["name"]
    msguser = server.slack.server.users.find(event["user"])

    # slack returns None if it can't find the user because it thinks it's ruby
    if not msguser:
        logger.debug("event {0} has no user".format(event))
        return

    # don't respond to ourself or slackbot
    if msguser.name == botname or msguser.name.lower() == "slackbot":
        return

    return '\n'.join(run_hook(server.hooks, "message", event, server))


def loop(server):
    try:
        while True:
            # This will cause a broken pipe to reveal itself
            server.slack.server.ping()

            events = server.slack.rtm_read()
            for event in events:
                logger.debug("got {0}".format(event.get("type", event)))
                response = handle_event(event, server)
                if response:
                    server.slack.rtm_send_message(event["channel"], response)

            time.sleep(1)
    except KeyboardInterrupt:
        if os.environ.get("LIMBO_DEBUG"):
            import ipdb

            ipdb.set_trace()
        raise


def main(args):
    server = init_server(args, config)

    if server.slack.rtm_connect():
        # run init hook. This hook doesn't send messages to the server (ought it?)
        run_hook(server.hooks, "init", server)

        loop(server)
    else:
        logger.warn("Connection Failed, invalid token <{0}>?".format(config["slack_token"]))
