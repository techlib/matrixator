#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from werkzeug.exceptions import Unauthorized
from sqlalchemy import and_
from datetime import datetime
import os
from twisted.python import log
from flask import jsonify

__all__ = ['Manager']


class Manager(object):
    def __init__(self, token, db, matrixator):
        self.token = token
        self.db = db
        self. matrixator = matrixator

    def process_msg(self, msg, token):
        # if token != 'Bearer ' + self.token:
        #   raise Unauthorized()
        for play in msg['plays']:
            play_name = play['play']['name']
            play_ts = play['play']['duration']['start']
            for task in play['tasks']:
                for host in task['hosts']:
                    if self.db.play.filter(and_(self.db.play.host == host, self.db.play.name == play_name, self.db.play.ts == play_ts)).first():
                        play_db = self.db.play.filter(and_(
                            self.db.play.host == host, self.db.play.name == play_name, self.db.play.ts == play_ts)).first()
                    else:
                        play_db = self.db.play.insert(
                            status='temporary', host=host, name=play_name, ts=play_ts)
                    self.db.flush()
                    id_play = play_db.id
                    duration = f"[{task['hosts'][host]['start']},{task['hosts'][host]['end']}]"
                    task_stat = 'success'
                    play_stat = 'success'
                    if 'changed' in task['hosts'][host].keys() and task['hosts'][host]['changed']:
                        task_stat = 'changed'
                        play_stat = 'success'
                    if 'skipped' in task['hosts'][host].keys() and task['hosts'][host]['skipped']:
                        task_stat = 'skipped'
                        play_stat = 'success'
                    if 'failed' in task['hosts'][host].keys() and task['hosts'][host]['failed']:
                        task_stat = 'failed'
                        play_stat = 'failed'
                    if 'unreachable' in task['hosts'][host].keys() and task['hosts'][host]['unreachable']:
                        task_stat = 'unreachable'
                        play_stat = 'failed'
                    self.db.task.insert(
                        result=task['hosts'][host], status=task_stat, duration=duration, id_play=id_play)
                    play_db.status = play_stat
                    self.db.commit()
        return True

    def get_last_failed(self):
        retval = []
        for fail in self.db.play.filter_by(status='failed').all():
            retval.append({"name": f'{fail.name}', "time": datetime(
                fail.ts), "host": f'<a href="/host/{fail.host}">{fail.host}</a>'})
        return retval

    def get_host_history(self, hostname):
        retval = []
        for play in self.db.play.filter_by(host=hostname).all():
            retval.append(
                {"name": f'{play.name}', "status": f'{play.status}', "time": f'{play.ts}'})
        return retval

    def get_hosts(self):
        return [i[0] for i in self.db.execute('select distinct host from play where ts > now() - \'1 week\'::interval').fetchall()]
