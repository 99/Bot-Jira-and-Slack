__author__ = 'Matthew Tuusberg'

import re
from jira.utils import JIRAError
from bot.config import config
import utils


def usage():
    return '!jira help: shows this message \n' + \
           '!jira show issue <issue name>: shows issue info \n' + \
           '!jira show projects: shows list of all projects \n' + \
           '!jira show issues <project name>: shows all issues that belong to certain project  \n' + \
           '!jira show done <project name>: shows a list of resolved issues \n' + \
           '!jira show open <project name>: show a list of open issues \n' + \
           '!jira show fires <project name>: shows a list of issues with \'fire\' label \n' + \
           '!jira show statuses: shows a list of available statuses \n' + \
           '!jira show users <project name>: shows all user for specified project \n' + \
           '!jira create <project name> [@<assignee>] <summary>: creates an issue \n' + \
           '!jira close <issue name> <comment>: closes an issue \n' + \
           '!jira assign @<user> <issue name>: sets issue assignee \n' + \
           '!jira description <issue name>: sets issue description \n' + \
           '!jira comment <issue name> <comment>: sets issue comment \n' + \
           '!jira status <issue name> <status>: sets issue status \n'


def show(jira, args):
    values = ['projects', 'issues', 'open', 'done', 'fires', 'issue', 'users', 'statuses']
    m = re.match(r'({})*(?: (.*))?'.format('|'.join([v for v in values])), args, re.IGNORECASE)

    if not m:
        return utils.not_valid_args(args)

    type = m.group(1)
    args = m.group(2) or ''

    if not type:
        return utils.not_valid_args(args, message='valid commands are: {}'.format(', '.join(values)))

    if type == 'projects':
        return projects(jira, args)
    elif type == 'issues':
        return issues(jira, args)
    elif type == 'open':
        return open_issues(jira, args)
    elif type == 'done':
        return done_issues(jira, args)
    elif type == 'fires':
        return fires(jira, args)
    elif type == 'issue':
        return show_issue(jira, args)
    elif type == 'users':
        return users(jira, args)
    elif type == 'statuses':
        return statuses(jira, args)


def show_issue(jira, args):
    m = re.match(r'(\w+-\d+)', args)

    if not m:
        return utils.not_valid_args(args, message='')

    issue_key = m.group(1)
    try:
        issue = jira.issue(issue_key)
        return utils.issue_info(issue)
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def create(jira, args):
    m = re.match(r'(\w+)? ?(?:@(\w+))? (.*)', args)

    if not m:
        return utils.not_valid_args(args)

    project_key = m.group(1) or config.get('jira_default_project')

    if not project_key:
        return utils.error('Project name is required')

    assignee = m.group(2)
    summary = m.group(3)

    fields = {
        'project': {'key': project_key},
        'summary': summary,
        'issuetype': {'name': config.get('jira_default_issue_type')},
    }

    try:
        if assignee:
            jira.user(assignee)

        issue = jira.create_issue(fields=fields)

        issue.fields.labels = config.get('jira_default_labels')
        issue.update(fields={"labels": issue.fields.labels})

        # weird, but user cannot be assigned during creation
        if assignee:
            issue.update(assignee={'name': assignee})

        return utils.issue_info(issue)
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def close(jira, args):
    m = re.match(r'(\w+-\d+) ?(.*)', args)

    if not m:
        return utils.not_valid_args(args)

    issue_key = m.group(1)
    issue_status = 'Closed'
    comment = m.group(2)

    try:
        issue = jira.issue(issue_key)

        transitions = jira.transitions(issue)
        transition_id = utils.get_transition(transitions, issue_status)

        if issue_status == issue.fields.status.name:
            return utils.error('Issue already closed')

        if not transition_id:
            return utils.error('Operation not permitted')

        jira.transition_issue(issue, transition_id, comment=comment)
        issue = jira.issue(issue_key)

        return utils.issue_info(issue)
    except JIRAError as e:
        if e.status_code == 500:
            return utils.error('operation not permitted')

        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def status(jira, args):
    m = re.match(r'(\w+-\d+) (.*)', args)

    if not m:
        return utils.not_valid_args(args)

    issue_key = m.group(1)
    issue_status = m.group(2)

    try:
        issue = jira.issue(issue_key)
        statuses = jira.statuses()

        if issue_status not in [s.name for s in statuses]:
            return utils.error('Status {} does not exist'.format(issue_status))

        if issue_status == issue.fields.status.name:
            return utils.error('Status {} already set'.format(issue_status))

        transitions = jira.transitions(issue)
        transition_id = utils.get_transition(transitions, issue_status)

        if not transition_id:
            return utils.error('Operation not permitted')

        jira.transition_issue(issue, transition_id)
        issue = jira.issue(issue_key)

        return utils.issue_info(issue)
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def assign(jira, args):
    m = re.match(r"(?:@(\w+)) (\w+-\d+)", args)

    if not m:
        return utils.not_valid_args(args)

    user = m.group(1)
    issue_id = m.group(2)

    try:
        jira.assign_issue(issue_id, user)

        issue = jira.issue(issue_id)
        return utils.issue_info(issue)
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def description(jira, args):
    m = re.match(r"(\w+-\d+) (.*)", args)

    if not m:
        return utils.not_valid_args(args)

    issue_id = m.group(1)
    description = m.group(2) or ''

    try:
        issue = jira.issue(issue_id)
        issue.update(description=description)

        return utils.issue_info(issue)
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def comment(jira, args):
    m = re.match(r"(\w+-\d+) (.*)", args)

    if not m:
        return utils.not_valid_args(args)

    issue_id = m.group(1)
    comment = m.group(2)

    if not comment:
        return utils.error('Leave a comment')

    try:
        jira.add_comment(issue_id, comment)
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def projects(jira, args):
    projects = jira.projects()
    return '\n'.join([utils.project_info(project) for project in projects])


def issues(jira, args):
    m = re.match(r'(\w+)?', args)

    if not m:
        return utils.not_valid_args(args)

    project_key = m.group(1) or config.get('jira_default_project')

    if not project_key:
        return utils.error('Project name is required')

    if not utils.check_project(jira, project_key):
        return utils.error('Project {} does not exist'.format(project_key))

    query = 'project={}'.format(project_key)
    issues = jira.search_issues(query)

    if not issues:
        return 'No issues found'

    return '\n\n'.join([utils.issue_info(issue) for issue in issues])


def open_issues(jira, args):
    m = re.match(r'(\w+)?', args)

    if not m:
        return utils.not_valid_args(args)

    project_key = m.group(1) or config.get('jira_default_project')

    if not project_key:
        return utils.error('Project name is required')

    if not utils.check_project(jira, project_key):
        return utils.error('Project {} does not exist'.format(project_key))

    query = 'project={} and status not in (\'Done\', \'Closed\', \'Resolved\')'.format(project_key)
    issues = jira.search_issues(query)

    if not issues:
        return 'No issues found'

    return '\n\n'.join([utils.issue_info(issue) for issue in issues])


def done_issues(jira, args):  # todo
    m = re.match(r'(\w+)?', args)

    if not m:
        return utils.not_valid_args(args)

    project_key = m.group(1) or config.get('jira_default_project')

    if not project_key:
        return utils.error('Project name is required')

    if not utils.check_project(jira, project_key):
        return utils.error('Project {} does not exist'.format(project_key))

    query = 'project={} and status in (\'Done\', \'Closed\', \'Resolved\')'.format(project_key)
    issues = jira.search_issues(query)

    if not issues:
        return 'No issues found'

    return '\n\n'.join([utils.issue_info(issue) for issue in issues])


def fires(jira, args):
    m = re.match(r'(\w+)?', args)

    if not m:
        return utils.not_valid_args(args)

    project_key = m.group(1) or config.get('jira_default_project')

    if not project_key:
        return utils.error('Project name is required')

    if not utils.check_project(jira, project_key):
        return utils.error('Project {} does not exist'.format(project_key))

    try:
        query = 'project={0} and labels in (fire)'.format(project_key)
        issues = jira.search_issues(query)

        if not issues:
            return 'No issues found'

        return '\n'.join([utils.issue_info(issue) for issue in issues])
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def statuses(jira, args):
    try:
        statuses = jira.statuses()
        return ','.join([status.name for status in statuses])
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def users(jira, args):
    m = re.match(r'(\w+)?', args)

    if not m:
        return utils.not_valid_args(args)

    project_key = m.group(1) or config.get('jira_default_project')

    if not project_key:
        return utils.error('Project name is required')

    if not utils.check_project(jira, project_key):
        return utils.error('Project {} does not exist'.format(project_key))

    try:
        users = jira.search_assignable_users_for_projects('', project_key)
        return '\n'.join([utils.user_info(user) for user in users])
    except JIRAError as e:
        response = utils.error('{} {}'.format(str(e.status_code), str(e.text)))
        return response


def sprints(jira, args):
    return utils.error('Not implemented yet')
