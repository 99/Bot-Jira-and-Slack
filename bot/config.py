__author__ = 'Matthew Tuusberg'

config = dict(jira_server=None,
              jira_user=None,
              jira_pass=None,
              jira_default_project=None,
              jira_default_issue_type='Bug',
              jira_default_labels=['fire', ],
              slack_token=None,
              loglevel=None,
              logformat=None,
              logfile=None
              )

if any([config.get(key) is None for key in ['jira_server', 'jira_user', 'jira_pass', 'slack_token']]):
    raise Exception('You should update config.py')
