# -*- coding:utf-8 -*-
'协议解析测试'

import sys
sys.path.append('../src/')

from xiwangshe import parser
from xiwangshe import message
from xiwangshe import pack_msg
import unittest


class DefaultTestCase(unittest.TestCase):
    def test_parse_request(self):
        input = 'POST 12345\r\n'
        body = 'aaaaaa'
        input += pack_msg(body)

        msg = parser.parse(input)
        self.assertEqual(msg.message_type, message.REQUEST)
        self.assertEqual(msg.method, 'POST')
        self.assertEqual(msg.seq, '12345')
        self.assertEqual(msg.body, body)

    def test_parse_response(self):
        input = '200 12345\r\n'
        body = 'bbbbbb'
        input += pack_msg(body)


        msg = parser.parse(input)
        self.assertEqual(msg.message_type, message.RESPONSE)
        self.assertEqual(msg.status, 200)
        self.assertEqual(msg.seq, '12345')
        self.assertEqual(msg.body, body)

    def test_parse_notify(self):
        input = 'NOTIFY\r\n'
        body = 'cccccc'
        input += pack_msg(body)

        msg = parser.parse(input)
        self.assertEqual(msg.message_type, message.NOTIFY)
        self.assertEqual(msg.method, 'NOTIFY')
        self.assertEqual(msg.body, body)


def suite():
    return unittest.makeSuite(DefaultTestCase, "test")

if __name__ == '__main__':
    unittest.main(defaultTest='suite', verbosity=2)
