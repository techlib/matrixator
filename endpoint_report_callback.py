#!/usr/bin/python3

from ansible.plugins.callback import CallbackBase
import uuid
import json
from requests import post
from functools import partial
from ansible.inventory.host import Host
import datetime

DOCUMENTATION = '''
    callback: NOTIFY_ENDPOINT
    callback_type: notification
    requirements:
      - whitelist in configuration
    short_description: Sends play report to endpoint
    version_added: "2.4"
    description:
        - This is an ansible callback plugin that sends play result to endpoint.
        - Before 2.4 only environment variables were available for configuring this plugin
    options:
     endpoint_url:
        required: True
        description: endpoint URL
        env:
          - name: ENDPOINT_URL
        ini:
          - section: callback_endpoint
            key: endpoint_url
      token:
        description: Authentication token.
        env:
          - name: ENDPOINT_TOKEN
        ini:
          - section: callback_endpoint
            key: token
'''


def current_time():
    return '%sZ' % datetime.datetime.utcnow().isoformat()

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
        self.results = []
        self.playbook_name = None
        # This is a 6 character identifier provided with each message
        # This makes it easier to correlate messages when there are more
        # than 1 simultaneous playbooks running
        self.guid = uuid.uuid4().hex[:6]

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct)

        self.url = self.get_option('endpoint_url')
        self.token = self.get_option('token')
        self.show_invocation = (self._display.verbosity > 1)

        if self.url is None:
            self.disabled = True
            self._display.warning('endpoint URL was not provided. The '
                                  'endpoint URL can be provided using '
                                  'the `ENDPOINT_URL` environment '
                                  'variable.')

    def send_msg(self, payload):
        try:
            req = post(self.url, headers={'Authentication': f'Bearer {self.token}'}, json=payload)
        except Exception as e:
            print(e)

        if req.status_code != 200:
            print(f'Failure to post JSON to endpoint. Status code: {req.status_code}')

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        payload = {'plays': self.results,}
        self.send_msg(payload)

    def _new_play(self, play):
        return {
            'play': {
                'name': play.get_name(),
                'id': str(play._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'tasks': []
        }

    def _new_task(self, task):
        return {
            'task': {
                'name': task.get_name(),
                'id': str(task._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'hosts': {}
        }

    def v2_playbook_on_play_start(self, play):
        self.results.append(self._new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.results[-1]['tasks'].append(self._new_task(task))

    def v2_playbook_on_handler_task_start(self, task):
        self.results[-1]['tasks'].append(self._new_task(task))

    def _convert_host_to_name(self, key):
        if isinstance(key, (Host,)):
            return key.get_name()
        return key

    def _record_task_result(self, on_info, result, **kwargs):
        """This function is used as a partial to add failed/skipped info in a single method"""
        host = result._host
        task = result._task
        task_result = result._result.copy()
        task_result.update(on_info)
        task_result['action'] = task.action
        self.results[-1]['tasks'][-1]['hosts'][host.name] = task_result
        end_time = current_time()
        self.results[-1]['tasks'][-1]['task']['duration']['end'] = end_time
        self.results[-1]['play']['duration']['end'] = end_time

    def __getattribute__(self, name):
        """Return ``_record_task_result`` partial with a dict containing skipped/failed if necessary"""
        if name not in ('v2_runner_on_ok', 'v2_runner_on_failed', 'v2_runner_on_unreachable', 'v2_runner_on_skipped'):
            return object.__getattribute__(self, name)

        on = name.rsplit('_', 1)[1]

        on_info = {}
        if on in ('failed', 'skipped'):
            on_info[on] = True

        return partial(self._record_task_result, on_info)
