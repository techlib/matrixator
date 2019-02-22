#!/usr/bin/python3

from ansible.plugins.callback import CallbackBase
import uuid
import json
import urllib.request
DOCUMENTATION = '''
    callback: MATRIX
    callback_type: notification
    requirements:
      - whitelist in configuration
    short_description: Sends play report on failure to a matrix room
    version_added: "2.4"
    description:
        - This is an ansible callback plugin that sends status to matrix room if playbook fails.
        - Before 2.4 only environment variables were available for configuring this plugin
    options:
      matrix_url:
        required: True
        description: matrix URL
        env:
          - name: MATRIX_URL
        ini:
          - section: callback_matrix
            key: matrix_url
      token:
        description: Authentication token.
        env:
          - name: matrix_token
        default: ansible
        ini:
          - section: callback_matrix
            key: token
'''


try:
    import prettytable
    from matrix_client.api import MatrixRequestError, MatrixHttpApi
    from requests.exceptions import MissingSchema
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


class CallbackModule(CallbackBase):
    """This is an ansible callback plugin that sends failure
    updates to a matrix room after playbook execution.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'matrix'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)

        if not HAS_DEPENDENCIES:
            self.disabled = True
            self._display.warning('One or more of dependencies is not '
                                  'installed. Disabling the matrix report callback '
                                  'plugin.')
        self.playbook_name = None
        # This is a 6 character identifier provided with each message
        # This makes it easier to correlate messages when there are more
        # than 1 simultaneous playbooks running
        self.guid = uuid.uuid4().hex[:6]

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct)

        self.url = self.get_option('matrix_url')
        self.token = self.get_option('matrix_token')
        self.room = self.get_option('matrix_room')
        self.show_invocation = (self._display.verbosity > 1)

        if self.url is None:
            self.disabled = True
            self._display.warning('matrix URL was not provided. The '
                                  'matrix URL can be provided using '
                                  'the `MATRIX_URL` environment '
                                  'variable.')

    def send_msg(self, attachments):
        try:
            matrix = MatrixHttpApi(self.url, self.token)
        except Exception as e:
            print(e)
        try:
            matrix.send_message(self.room, attachments)
        except Exception as e:
            print(e)

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        hosts = sorted(stats.processed.keys())

        t = prettytable.PrettyTable(['Host', 'Ok', 'Changed', 'Unreachable',
                                     'Failures'])

        failures = False
        unreachable = False

        for h in hosts:
            s = stats.summarize(h)

            failures = s['failures'] > 0
            unreachable = s['unreachable'] > 0

            t.add_row([h] + [s[k] for k in ['unreachable',
                                            'failures']])

        attachments = []
        msg_items = [
            '*Playbook Complete* (_%s_)' % self.guid
        ]
        if not (failures or unreachable):
          return
        if failures or unreachable:
            color = 'danger'
            msg_items.append('\n*Failed!*')

        msg_items.append('```\n%s\n```' % t)

        msg = '\n'.join(msg_items)

        attachments.append({
            'fallback': msg,
            'fields': [
                {
                    'value': msg
                }
            ],
            'color': color,
            'mrkdwn_in': ['text', 'fallback', 'fields']
        })

        self.send_msg(attachments=attachments)
