#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from werkzeug.exceptions import Unauthorized
from sqlalchemy import and_
from datetime import datetime
import os

__all__ = ['Manager']


class Manager(object):
    def __init__(self, token, db, matrixator):
        self.token = token
        self.db = db
        self. matrixator = matrixator

    def process_msg(self, msg, token):
        if token != 'Bearer ' + self.token:
            raise Unauthorized()
        for play in msg['plays']:
            play_name = play['play']['name']
            for task in play['tasks']:
                for host in task['hosts']:
                    if self.db.play.filter(and_(self.db.play.host == host, self.db.play.name == play_name)).first() == None:
                        play_db = self.db.play.insert(
                            host=host, name=play_name)
                    else:
                        play_db = self.db.play.filter(
                            self.db.play.host == host).one()
                    if 'changed' in host.keys() and host['changed'] == True:
                        play_db.append(self.db.task.insert(
                            result=msg, status='changed', host=host))
                        play_db.status = 'success'
                    elif 'skipped' in host.keys() and host['skipped'] == True:
                        play_db.append(self.db.task.insert(
                            result=msg, status='skipped', host=host))
                        play_db.status = 'success'
                    elif 'failed' in host.keys() and host['failed'] == True:
                        play_db.append(self.db.task.insert(
                            result=msg, status='failed', host=host))
                        play_db.status = 'failed'
                    elif 'unreachable' in host.keys() and host['unreachable'] == True:
                        play_db.append(self.db.task.insert(
                            result=msg, status='unreachable', host=host))
                        play_db.status = 'failed'
                    else:
                        play_db.append(self.db.task.insert(
                            result=msg, status='success', host=host))
                        play_db.status = 'success'

    def get_last_failed(self):
        retval = []
        for fail in self.db.play.filter_by(status='failed').all():
            retval.append({'name': f'{fail.name}', 'time': datetime(
                fail.ts), 'host': f'<a href="/host/{fail.host}">{fail.host}</a>'})
        return retval

    def get_host_history(self, hostname):
        retval = []
        for play in self.db.play.filter_by(host=hostname):
            retval.append(
                {'name': f'{play.name}', 'status': f'{play.status}', 'time': f'{play.ts}'})
        return retval

    def get_hosts(self):
        return str(self.db.execute('select distinct host from play where ts > now() - \'1 week\'::interval')).split()
