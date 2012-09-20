# -*- coding:utf-8 -*-
'通信测试'

import sys
sys.path.append('../src/')

import logging
logging.getLogger().setLevel(logging.WARN)
import unittest
import gevent
from xiwangshe import client
from xiwangshe import Server
from xiwangshe import TimeoutException

notify_received = False


class TestServer(Server):
    def __init__(self, url):
        Server.__init__(self, url)

    def on_request(self, request):
        if request.method == 'hi':
            request.send_response(200, request.body)
            return

        if request.method == 'sleep':
            interval = int(request.body)
            gevent.sleep(interval)
            request.send_response(200)
            return

    def on_notify(self, notify):
        if notify.method == 'hi':
            global notify_received
            notify_received = True
            return
        if notify.method == 'give_me_request':
            self.send_request(url=notify.remote_url, method='hehe')
            return
        if notify.method == 'give_me_notify':
            self.send_notify(url=notify.remote_url, method='haha')
            return


class DefaultTestCase(unittest.TestCase):
    def setUp(self):
        self.request_received = False
        self.notify_received = False
        client.on_request = self.on_request
        client.on_notify = self.on_notify

        self.url = ('localhost', 4446)
        self.server = TestServer(self.url)
        self.server.start()
        gevent.sleep(0.1)

    def tearDown(self):
        self.server.stop()

    def on_request(self, request):
        self.request_received = True

    def on_notify(self, notify):
        self.notify_received = True

    def test_client_receive_request(self):
        client.send_notify(url=self.url, method='give_me_request', body='wawa')
        gevent.sleep(0.1)
        self.assertTrue(self.request_received)

    def test_client_receive_notify(self):
        client.send_notify(url=self.url, method='give_me_notify', body='wawa')
        gevent.sleep(0.1)
        self.assertTrue(self.notify_received)

    def test_send_request(self):
        rsp = client.send_request(url=self.url, method='hi', body='wawa')
        self.assertIsNotNone(rsp, '应答为空')
        self.assertIsInstance(rsp.status, int, '应答码不为整数')
        self.assertIsNotNone(rsp.body, '应答码不为整数')
        self.assertIsNotNone(rsp.request, '应答里得不到请求')
        self.assertEqual(rsp.request.method, 'hi')
        self.assertEqual(rsp.request.body, 'wawa')

    #@unittest.skip('temp')
    def test_send_notify(self):
        rsp = client.send_notify(url=self.url, method='hi', body='wawa')
        self.assertIsNone(rsp, 'notify应答不为空')
        gevent.sleep(0.1)
        self.assertTrue(notify_received)

    #@unittest.skip('temp')
    def test_send_timeout(self):
        with self.assertRaises(TimeoutException):
            client.send_request(url=self.url,
                                method='sleep',
                                body='6',
                                timeout=1)


def suite():
    return unittest.makeSuite(DefaultTestCase, "test")

if __name__ == '__main__':
    unittest.main(defaultTest='suite', verbosity=2)
