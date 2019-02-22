#!/usr/bin/python3
# -*- coding: utf-8 -*-

__all__ = ['make_site']

from werkzeug.exceptions import Unauthorized

import flask
import os


def make_site(manager, debug=False):
    app = flask.Flask('.'.join(__name__.split('.')[:-1]))
    app.secret_key = os.urandom(16)
    app.debug = debug

    @app.errorhandler(Unauthorized.code)
    def unauthorized(e):
        return flask.Response('Invalid or missing token', Unauthorized.code, {'WWW-Authenticate': 'Bearer'})

    @app.route('/', methods=['GET'])
    def info():
        return flask.render_template('index.html', **locals())

    @app.route('/api/incoming', methods=['POST'])
    def msg():
        manager.process_msg(flask.request.get_json(),
                            flask.request.headers.get('Authorization'))

    return app
