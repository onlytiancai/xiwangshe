# -*- coding:utf-8 -*-

import re
from StringIO import StringIO
import logging
import gevent
from gevent import socket
from gevent.event import AsyncResult
import uuid
import string
from datetime import datetime, timedelta

__version__ = "0.1"
MAX_MSG_SIZE = 1024


class message(dict):
    REQUEST = 'request'
    RESPONSE = 'response'
    NOTIFY = 'notify'

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        return self.raw

    def send_response(self, status, body=''):
        to_send = '%s %s\r\n%s' % (status, self.seq, body)
        if len(to_send) > MAX_MSG_SIZE:
            raise ValueError('to send data overflow')
        self.socket.sendto(to_send, self.remote_url)


class parser(object):
    re_request = re.compile('([a-zA-Z]\w+) ([\w|\-]+)')
    re_response = re.compile('(\d{3}) ([\w|-]+)')

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
        return message(message_type=message.REQUEST,
                       method=result.group(1),
                       seq=result.group(2),
                       body=input.read(),
                       raw=result.group())

    @staticmethod
    def _make_response(result, input):
        return message(message_type=message.RESPONSE,
                       status=int(result.group(1)),
                       seq=result.group(2),
                       body=input.read(),
                       raw=result.group())

    @staticmethod
    def _make_notify(method, input):
        return message(message_type=message.NOTIFY,
                       method=method,
                       body=input.read(),
                       raw=method)


def _receive_msg(socket):
    data, remote_url = socket.recvfrom(MAX_MSG_SIZE)
    logging.debug('receive data:"%s" %s', data, remote_url)
    msg = parser.parse(data)
    msg.remote_url = remote_url
    msg.socket = socket
    return msg


class TimeoutException(Exception):
    pass


class client(object):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent_requests = {}

    def receive_msg_process():
        logging.info('receive_msg_process started')
        while True:
            try:
                msg = _receive_msg(client.client_socket)
                if msg.message_type == message.RESPONSE:
                    if msg.seq in client.sent_requests:
                        request = client.sent_requests.pop(msg.seq)
                        msg.request = request
                        request.result.set(msg)
            except:
                logging.exception('receive data error')

    gevent.spawn(receive_msg_process)

    def check_timeout_process():
        logging.info('check_timeout_process started')
        while True:
            try:
                now = datetime.now()
                to_removes = []
                logging.debug('check timeout:%s %s',
                              now,
                              len(client.sent_requests))
                for seq in client.sent_requests:
                    request = client.sent_requests[seq]
                    if now - request.senttime > request.timeout:
                        to_removes.append(seq)

                logging.debug('will remove:%s', to_removes)
                for seq in to_removes:
                    request = client.sent_requests[seq]
                    request.result.set_exception(TimeoutException())
            except:
                logging.exception('check_timeout_process error')
            finally:
                gevent.sleep(5)

    gevent.spawn(check_timeout_process)

    @staticmethod
    def async_send_request(url, method, body='', timeout=30):
        if not method[0] in string.ascii_letters:
            raise ValueError('method must letters prefix')
        seq = str(uuid.uuid1())
        to_send = '%s %s\r\n%s' % (method, seq, body)
        if len(to_send) > MAX_MSG_SIZE:
            raise ValueError('to send data overflow')

        msg = message(message_type=message.REQUEST,
                      method=method,
                      seq=seq,
                      body=body)
        msg.senttime = datetime.now()
        msg.timeout = timedelta(seconds=timeout)
        msg.result = AsyncResult()
        client.client_socket.sendto(to_send, url)
        logging.debug('client sendto:%s', url)
        client.sent_requests[seq] = msg
        return msg.result

    @staticmethod
    def send_request(url, method, body='', timeout=30):
        result = client.async_send_request(url, method, body, timeout)
        return result.get()

    @staticmethod
    def send_notify(url, method, body='', timeout=30):
        if not method[0] in string.ascii_letters:
            raise ValueError('method must letters prefix')
        to_send = '%s\r\n%s' % (method, body)
        if len(to_send) > MAX_MSG_SIZE:
            raise ValueError('to send data overflow')
        client.client_socket.sendto(to_send, url)
        logging.debug('client sendto:%s', url)


class Server(object):
    def __init__(self, url):
        self.url = url
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _start(self):
        self.server.bind(self.url)
        logging.info('server start')
        while True:
            try:
                msg = _receive_msg(self.server)
                if msg.message_type == message.REQUEST:
                    gevent.spawn(self.on_request, msg)
                elif msg.message_type == message.NOTIFY:
                    gevent.spawn(self.on_notify, msg)
                else:
                    logging.warn('unknow msg:%s', msg)
            except socket.error, err:
                logging.debug('receive data error:%s', err.errno)
                if err.errno == 9:
                    break
                raise

    def start(self):
        self.receive_process = gevent.spawn(self._start)

    def stop(self):
        try:
            self.server.close()
        except:
            pass
        try:
            self.receive_process.kill()
        except:
            pass

    def on_request(self, request):
        pass

    def on_notify(self, notify):
        pass
