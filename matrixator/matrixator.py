#!/usr/bin/python3 -tt

import re

from matrix_client.client import MatrixHttpApi


__all__ = ['Matrixator']


class Matrixator:
    def __init__(self, room='!rommId:example.com', server='https://matrix.org', matrix_token='reallyLongRandomToken'):
        self.room = room
        self.server = server
        self. matrix_token = matrix_token

    def send_message(self, message):
        try:
            matrix = MatrixHttpApi(self.server, self.matrix_token)
        except Exception as e:
            print(e)
        try:
            matrix.send_message_event(
                self.room, 'm.room.message', self.get_html_content(message))
        except Exception as e:
            print(e)

    def get_html_content(self, html, body=None, msgtype="m.text"):
        return {
            "body": body if body else re.sub('<[^<]+?>', '', html),
            "msgtype": msgtype,
            "format": "org.matrix.custom.html",
            "formatted_body": html
        }
