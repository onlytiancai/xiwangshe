# xiwangshe

基于gevent的可靠UDP通信。

项目名称来自我的老家"西王舍村" http://j.map.baidu.com/xYztJ 

## Quick Start

Server

    from xiwangshe import Server


    class TestServer(Server):
        def __init__(self, url):
            Server.__init__(self, url)

        def on_request(self, request):
            if request.method == 'hi':
                request.send_response(200, request.body)
                return

    server = TestServer(('localhost', 4446))
    server.start()

Client

    from xiwangshe import client
    from xiwangshe import TimeoutException

    try:
        response = client.send_request(url=('localhost', 4446),
                                       method='hi',
                                       body='onlytiancai',
                                       timeout=5)
        print response.status
        print response.body
        print response.request
    except TimeoutException, ex:
        print ex

## feedback

[feadback](https://github.com/onlytiancai/xiwangshe/issues)
