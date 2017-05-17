import tornado.ioloop
import tornado.web
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.httpclient import HTTPRequest
from tornado.web import RequestHandler, Application
from server.config import *
from server.db import RedisClient


class MainHandler(RequestHandler):
    redis = RedisClient()
    http_client = CurlAsyncHTTPClient(force_instance=True)

    def handle_proxy(self, response):
        request = response.request
        host = request.proxy_host
        port = request.proxy_port
        proxy = '{host}:{port}'.format(host=host, port=port)
        if response.error:
            print('Request failed Using', proxy, response.error)
            print('Invalid Proxy', proxy, 'Remove it')
            self.redis.remove(proxy)
        else:
            print('Valid Proxy', proxy)

    def test_proxies(self):
        proxies = self.redis.all()
        print(proxies)
        for proxy in proxies:
            self.test_proxy(proxy)

    def test_proxy(self, proxy):
        try:
            (proxy_host, proxy_port) = tuple(proxy.split(':'))
            print('Testing Proxy', proxy)
            request = HTTPRequest(url=TEST_URL, proxy_host=proxy_host, proxy_port=int(proxy_port))
            print(request)
            self.http_client.fetch(request, self.handle_proxy)
        except ValueError:
            print('Invalid Proxy', proxy)
            self.redis.remove(proxy)

    def post(self):
        token = self.get_body_argument('token', default=None, strip=False)
        port = self.get_body_argument('port', default=None, strip=False)
        if token == TOKEN and port:
            ip = self.request.remote_ip
            proxy = ip + ':' + port
            print('Receive proxy', proxy)
            self.redis.add(proxy)
            self.test_proxies()
        elif token != TOKEN:
            self.write('Wrong Token')
        elif not port:
            self.write('No Client Port')

    def get(self, api):
        if api == 'get':
            result = self.redis.get()
            if result:
                self.write(result)
        if api == 'count':
            self.write(str(self.redis.count()))


def run():
    application = Application([
        (r'/', MainHandler),
        (r'/(.*)', MainHandler),
    ])
    print('Listening on', RECEIVER_PORT)
    application.listen(RECEIVER_PORT)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    run()