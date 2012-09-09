# -*- coding:utf-8 -*-
'基准性能测试'

import sys;sys.path.append('../src/')

import logging;logging.getLogger().setLevel(logging.WARN) 
import gevent
from gevent.pool import Pool
from xiwangshe import client
from xiwangshe import Server
from xiwangshe import TimeoutException
from datetime import datetime

url = ('localhost', 4446)
test_count = 100
timeout_count = 0
pool = Pool(100)

import sys
if len(sys.argv) == 2:
    test_count = int(sys.argv[1])

class TestServer(Server):
    def __init__(self, url):
        Server.__init__(self, url)
    def on_request(self, request):
        request.send_response(200)

server = TestServer(url)
server.start()
gevent.sleep(0.1) 

def test_sync_one():
    try:
        client.send_request(url=url, method='hi', timeout=5)
    except TimeoutException:
        global timeout_count
        timeout_count += 1

def test_sync():
    test_start_time = datetime.now()
    jobs = [pool.spawn(test_sync_one) for i in xrange(test_count)]
    gevent.joinall(jobs)
    print 'test_sync:send %s request take %s, timeout_count=%s' % (test_count, datetime.now() - test_start_time, timeout_count)

def test_async():
    test_start_time = datetime.now()
    jobs = [gevent.spawn(client.async_send_request, url, 'hi') for i in xrange(test_count)]
    gevent.joinall(jobs)
    print 'send %s request take %s, timeout_count=%s' % (test_count, datetime.now() - test_start_time, timeout_count)

test_sync()
#1
