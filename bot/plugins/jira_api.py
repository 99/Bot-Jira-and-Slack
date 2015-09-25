__author__ = 'Matthew Tuusberg'

import os
import sys
sys.path.append(os.path.dirname(__file__))

from jira_plugin.commands import *
from jira.client import JIRA
from bot.config import config

commands = {'help': usage,
            'issue': show_issue,
            'show': show,
            'create': create,
            'close': close,
            'assign': assign,
            'description': description,
            'status': status,
            'comment': comment,
            'sprints': sprints
            }


def on_message(msg, server):
    text = msg.get('text', '')
    user = msg.get('user_name', '')

    m = re.match(r'!jira', text)

    if not m:
        return

    m = re.match(r'!jira ({}) ?(.*)'.format('|'.join([cmd for cmd in commands.keys()])), text)

    if not m:
        return utils.error('command does not exist')

    action = m.group(1)
    args = m.group(2)
    return handle(action, args)


def handle(command, args):
    # we don't need api connection to show help :/
    if command == 'help':
        return usage()

    jira_username = config.get('jira_user')
    jira_password = config.get('jira_pass')

    options = {
        'server': config.get('jira_server'),
    }

    jira = JIRA(options, basic_auth=(jira_username, jira_password))

    if commands.get(command):
        return commands[command](jira, args)
