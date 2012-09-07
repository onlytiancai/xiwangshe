# -*- coding:utf-8 -*-

import re
from StringIO import StringIO

__version__ = "0.1"

class message(dict):
    REQUEST = 'request'
    RESPONSE = 'response'
    NOTIFY = 'notify'

    def __getattr__(self, key): 
        try: return self[key]
        except KeyError, k: raise AttributeError, k
    
    def __setattr__(self, key, value): 
        self[key] = value
 

class parser(object):
    re_request = re.compile('([a-zA-Z]\w+) (\w+)')
    re_response = re.compile('(\d{3}) (\w+)')

    @staticmethod
    def parse(input):
        input = StringIO(input)
        status_line = input.readline().rstrip('\r\n')

        result = parser.re_request.match(status_line)
        if result:
            return parser._make_request(result, input)

        result = parser.re_response.match(status_line)
        if result:
            return parser._make_response(result, input)

        return parser._make_notify(status_line, input)

    @staticmethod
    def _make_request(result, input):
        return message(message_type=message.REQUEST, method=result.group(1), seq=result.group(2), body=input.read())

    @staticmethod
    def _make_response(result, input):
        return message(message_type=message.RESPONSE, status=int(result.group(1)), seq=result.group(2), body=input.read())

    @staticmethod
    def _make_notify(method, input):
        return message(message_type=message.NOTIFY, method=method, body=input.read())


class client(object):
    pass

class Server(object):
    pass

class TimeoutException(Exception):
    pass
