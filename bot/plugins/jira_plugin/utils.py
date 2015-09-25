__author__ = 'Matthew Tuusberg'

from bot.config import config


def error(message):
    return 'Error: {}'.format(message)


def not_valid_args(args, message=None):
    err = 'arguments not valid'

    if args:
        err += ': {}'.format(args)
    if message:
        err += '\n{}'.format(message)

    return error(err)


def get_transition(transitions, status):
    # O(n)
    for t in transitions:
        if unicode(status) == t.get('to', {}).get('name', ''):
            return t.get('id', None)

    return None


def check_project(jira, project_key):
    if project_key in [p.key for p in jira.projects()]:
        return True

    return False


def project_info(project):
    return '{}: {}'.format(project.key, project.name)


def issue_info(issue):
    issue_summary = issue.fields.summary
    issue_description = issue.fields.description or 'No description'
    issue_key = issue.key
    issue_labels = ','.join(issue.fields.labels or ['no labels', ])
    issue_type = issue.fields.issuetype
    issue_status = issue.fields.status
    issue_link = '{}/browse/{}'.format(config.get('jira_server'), issue_key)

    assignee = issue.fields.assignee

    if assignee:
        assignee = '@' + user_info(assignee)
    else:
        assignee = 'not assigned'

    return '{}\n{}\n{}|{}|{}|{}|{}\n{}'.format(issue_summary,
                                           issue_description,
                                           issue_key,
                                           issue_labels,
                                           issue_type,
                                           issue_status,
                                           assignee,
                                           issue_link)


def user_info(user):
    return '{}: {}'.format(user.key, user.displayName)
