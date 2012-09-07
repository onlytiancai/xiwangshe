# -*- coding:utf-8 -*-
'协议解析测试'

import sys;sys.path.append('../src/')

import unittest
import gevent
from xiwangshe import client
from xiwangshe import Server
from xiwangshe import TimeoutException


notify_received = False
class TestServer(Server):
    def __init__(self, url):
        self.url = url
    def on_request(request):
        if request.method == 'hi' :
            request.send_response(200, request.body)
            return

        if request.method == 'sleep':
            interval = int(request.body)
            gevent.sleep(interval) 
            request.send_response(200)
            return

    def on_notify(notify):
        if notify.method == 'hi':
            global notify_received
            notify_received = True
            return

class DefaultTestCase(unittest.TestCase):
    def setUp(self):
        self.url = ('localhost',4446) 
        self.server = TestServer(self.url)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_send_request(self):
        rsp = client.send_request(url=self.url, method='hi', body='wawa')
        self.assertIsNotNone(rsp, '应答为空')
        self.assertIsInstance(rsp.status, int, '应答码不为整数')
        self.assertIsNotNone(rsp.body, '应答码不为整数')
        self.assertIsNotNone(rsp.request, '应答里得不到请求')
        self.assertEqual(rsp.request.method, 'hi')
        self.assertEqual(rsp.request.body, 'wawa')

    def test_send_notify(self):
        rsp = client.send_notify(url=self.url, method='hi', body='wawa')
        self.assertIsNone(rsp, 'notify应答不为空')
        gevent.sleep(1)
        self.assertTrue(notify_received)


    def test_send_timeout(self):
        with self.assertRaises(TimeoutException):
            client.send_request(url=self.url, method='sleep', body='5', timeout=3)



def suite():
    return unittest.makeSuite(DefaultTestCase, "test")

if __name__ == '__main__':
    unittest.main(defaultTest='suite',verbosity=2)
