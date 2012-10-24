# xiwangshe

基于gevent的靠UDP通信。

项目名称来自我的老家"[西王舍村](http://j.map.baidu.com/xYztJ)", 正式名称待定。

## 与其它通信协议比较

1. [HTTP](http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol)
    1. 优点
        1. 通用性好，平台，语言支持广泛，被认知度高。
        1. 支持[Request-response](http://en.wikipedia.org/wiki/Request-response), 使用方便，直接能拿到请求处理结果。 
    1. 缺点
        1. 好多HTTP的Server和Client不支持[HTTP Persistent Connection](http://en.wikipedia.org/wiki/HTTP_persistent_connection)。
        1. 好多HTTP的Server和Client不支持[HTTP Pipeling](http://en.wikipedia.org/wiki/HTTP_pipelining)。
        1. 不支持[Full-duplex](http://en.wikipedia.org/wiki/Duplex_(telecommunications)#Full-duplex),服务端不能直接给客户端发通知。
        1. Response和Request都不支持sequence number,导致Server和Client不能纯异步的处理消息。
1. [WebSocket](http://en.wikipedia.org/wiki/WebSocket):
    1. 优点
        1. 支持持久连接，纯异步收发消息
        1. 有on_error,on_close等事件，方便处理连接断开等事件
    1. 缺点
        1. 不支持[Request-response](http://en.wikipedia.org/wiki/Request-response)，需要自己匹配应答。
1. [ZeroMQ](http://www.zeromq.org/)
    1. 优点
        1. 覆盖多种通信模式，request/response, sub/pub等
        1. 使用简单，性能好
    1. 缺点
        1. 功能太多，不够轻量级，据说高并发下有[丢失消息的问题](http://cn.bing.com/search?q=zeromq+lost+message&go=&qs=AS&form=QBRE&pq=zeromq+lo&sc=2-9&sp=2&sk=AS1)。
        1. 内部实现理解复杂，不利于将来排错。 
1. [xiwangshe](https://github.com/onlytiancai/xiwangshe)
    1. 优点
        1. 全双工，客户端和服务端都可以主动给对方发送request
        1. 每个message都有唯一的sequence number，客户端和服务端均可纯异步的处理消息
            1. client可以同时发起多个request，无需等待之前的request的response
            1. server收到response后可以在任何时候异步的返回response
        1. 得益于gevent，IO性能很好
        1. 得益于gevent, 收发消息都是同步的写法，异步的性能，不需要很多Callback，更直观
        1. 底层使用UDP协议，不需要进行连接管理，不需要处理连接异常断开等事件
        1. 代码简单，只有200多行代码，出错很容易排查故障
        1. 自带完善的单元测试，性能测试，性能剖析脚本
        1. 序列化组件默认使用msgpack，如果没有安装该模块会自动降级为SimpleJson或json
    1. 缺点
        1. 因为是UDP协议，所以不适合传输大数据，保险的话最好传输512字节以下的包

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

