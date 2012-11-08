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

try:
    import msgpack
    pack_msg, unpack_msg = msgpack.packb, msgpack.unpackb
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json
    pack_msg, unpack_msg = json.dumps, json.loads


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
        body = pack_msg(body)
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
                       body=unpack_msg(input.read()),
                       raw=result.group())

    @staticmethod
    def _make_response(result, input):
        return message(message_type=message.RESPONSE,
                       status=int(result.group(1)),
                       seq=result.group(2),
                       body=unpack_msg(input.read()),
                       raw=result.group())

    @staticmethod
    def _make_notify(method, input):
        return message(message_type=message.NOTIFY,
                       method=method,
                       body=unpack_msg(input.read()),
                       raw=method)


class TimeoutException(Exception):
    pass


class EndPoint(object):
    def __init__(self, url=None):
        self.url = url
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sent_requests = {}

    def _receive_msg(self):
        data, remote_url = self.socket.recvfrom(MAX_MSG_SIZE)
        logging.debug('receive data:"%s" %s', data, remote_url)
        msg = parser.parse(data)
        msg.remote_url = remote_url
        msg.socket = self.socket
        return msg

    def async_send_request(self, url, method, body='', timeout=30):
        if not method[0] in string.ascii_letters:
            raise ValueError('method must letters prefix')
        seq = str(uuid.uuid1())
        to_send = '%s %s\r\n%s' % (method, seq, pack_msg(body))
        if len(to_send) > MAX_MSG_SIZE:
            raise ValueError('to send data overflow')

        msg = message(message_type=message.REQUEST,
                      method=method,
                      seq=seq,
                      body=body)
        msg.senttime = datetime.now()
        msg.timeout = timedelta(seconds=timeout)
        msg.result = AsyncResult()
        self.socket.sendto(to_send, url)
        logging.debug('client sendto:%s', url)
        self.sent_requests[seq] = msg
        return msg.result

    def send_request(self, url, method, body='', timeout=30):
        result = self.async_send_request(url, method, body, timeout)
        return result.get()

    def send_notify(self, url, method, body='', timeout=30):
        if not method[0] in string.ascii_letters:
            raise ValueError('method must letters prefix')
        to_send = '%s\r\n%s' % (method, pack_msg(body))
        if len(to_send) > MAX_MSG_SIZE:
            raise ValueError('to send data overflow')
        self.socket.sendto(to_send, url)
        logging.debug('client sendto:%s', url)

    def receive_msg_process(self):
        logging.info('receive_msg_process started')
        while True:
            try:
                msg = self._receive_msg()
                if msg.message_type == message.RESPONSE:
                    if msg.seq in self.sent_requests:
                        request = self.sent_requests.pop(msg.seq)
                        msg.request = request
                        request.result.set(msg)
                elif msg.message_type == message.REQUEST:
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
            except gevent.GreenletExit:
                break
            except:
                logging.exception('receive data error')

    def check_timeout_process(self):
        logging.info('check_timeout_process started')
        while True:
            try:
                now = datetime.now()
                to_removes = []
                logging.debug('check timeout:%s %s',
                              now,
                              len(self.sent_requests))
                for seq in self.sent_requests:
                    request = self.sent_requests[seq]
                    if now - request.senttime > request.timeout:
                        to_removes.append(seq)

                logging.debug('will remove:%s', to_removes)
                for seq in to_removes:
                    request = self.sent_requests[seq]
                    request.result.set_exception(TimeoutException())
            except:
                logging.exception('check_timeout_process error')
            finally:
                gevent.sleep(5)

    def start(self):
        logging.debug('server starting')
        if self.url:
            self.socket.bind(self.url)
        self.receive_msg_thread = gevent.spawn(self.receive_msg_process)
        self.check_timeout_thread = gevent.spawn(self.check_timeout_process)

    def stop(self):
        logging.debug('server stoping')
        try:
            self.socket.close()
        except:
            logging.debug('socket close error')
        try:
            self.receive_msg_thread.kill()
        except:
            logging.debug('kill receive_msg_thread error')
        try:
            self.check_timeout_thread.kill()
        except:
            logging.debug('kill check_timeout_thread error')

    def on_request(self, on_request):
        pass

    def on_notify(self, on_notify):
        pass

client = EndPoint()
client.start()


class Server(EndPoint):
    pass
