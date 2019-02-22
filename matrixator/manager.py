#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from werkzeug.exceptions import Unauthorized

__all__ = ['Manager']


class Manager(object):
    def __init__(self, token, db, matrixator):
        self.token = token
        self.db = db
        self. matrixator = matrixator

    def process_msg(self, msg, token):
        if token != 'Bearer ' + self.token:
            raise Unauthorized()
        hosts = sorted(msg.processed.keys())

        failures = False
        unreachable = False
        skipped = False

        for h in hosts:
            s = msg.summarize(h)

            failures = s['failures'] > 0
            unreachable = s['unreachable'] > 0
            skipped = s['skipped'] > 0
            if failures or unreachable:
                self.matrixator.send_message(msg)
                self.db.ansible_runs.insert(result=msg, status='failed', host=h)
            elif skipped:
                self.db.ansible_runs.insert(result=msg, status='skipped', host=h)
            else:
                self.db.ansible_runs.insert(result=msg, status='succeeded', host=h)

