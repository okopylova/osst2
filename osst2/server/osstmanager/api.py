import pika
#import uuid
import json
from webob import Request, Response
from webob import exc
from argparse import ArgumentParser
from wsgiref.simple_server import make_server

valid_methods = {
    'compute': {'list_all': 'GET', 'create': 'PUT', 'delete': 'DELETE',
                'reboot': 'POST', 'power_on': 'POST', 'power_off': 'POST'},
    'network': {'add_ip_range': 'PUT', 'del_ip_range': 'DELETE'}}


class Manager(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.
                                                  ConnectionParameters
                                                  (host='localhost'))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        #self.callback_queue = result.method.queue
        #self.channel.basic_consume(self.on_response, no_ack=True,
        #                           queue=self.callback_queue)
        #self.resp_waiting = {}

    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = self.route_request(req)
        return resp(environ, start_response)

    #def on_response(self, ch, method, props, body):
    #    if props.correlation_id in self.resp_waiting:
    #        self.resp_waiting[props.correlation_id] = body

    def rpc(self, queue_name, method, args):
        self.response = None
        #corr_id = str(uuid.uuid4())
        #self.resp_waiting[corr_id] = None
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   #properties=pika.
                                   #BasicProperties(reply_to=self.
                                   #                callback_queue,
                                   #                correlation_id=corr_id,),
                                   body=json.dumps({'method': method,
                                                    'args': args}),
                                   properties=
                                   pika.BasicProperties(delivery_mode = 2,))
        #while self.resp_waiting[corr_id] is None:
        #    self.connection.process_data_events()
        #resp = self.resp_waiting[corr_id]
        #return resp
        return 'ok'

    def route_request(self, req):
        segments = req.path.strip('/').split('/')
        if len(segments) != 4 or segments[0] != 'api' or \
                segments[1] != 'v1' or segments[2] not in valid_methods or \
                segments[3] not in valid_methods[segments[2]] or \
                valid_methods[segments[2]][segments[3]] != req.method:
            resp = exc.HTTPBadRequest('Incorrect path or method')
        else:
            resp = Response(self.rpc(segments[2], segments[3], req.json))
        return resp


def start_server():
    parser = ArgumentParser(description='Starts VM manager API server')
    parser.add_argument('-host', default='localhost')
    parser.add_argument('-port', type=int, default=8080)
    args = parser.parse_args()
    httpd = make_server(args.host, args.port, Manager())
    print 'Started on http://%s:%s' % (args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        exit()


if __name__ == '__main__':
    start_server()
