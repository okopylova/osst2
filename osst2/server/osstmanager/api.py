#!/usr/bin/env python
import pika
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

    def __init__(self, host):
        self.connection = pika.BlockingConnection(pika.
                                                  ConnectionParameters
                                                  (host=host))
        self.channel = self.connection.channel()
        #result = self.channel.queue_declare(exclusive=True) TODO: check work

    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = self.route_request(req)
        return resp(environ, start_response)

    def send_msg(self, queue_name, method, args):
        self.response = None
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   body=json.dumps({'method': method,
                                                    'args': args}),
                                   properties=pika.BasicProperties
                                   (delivery_mode=2,))
        #TODO: put to db, return info from from db
        return 'ok'

    def route_request(self, req):
        segments = req.path.strip('/').split('/')
        if len(segments) != 4 or segments[0] != 'api' or \
                segments[1] != 'v1' or segments[2] not in valid_methods or \
                segments[3] not in valid_methods[segments[2]] or \
                valid_methods[segments[2]][segments[3]] != req.method:
            resp = exc.HTTPBadRequest('Incorrect path or method')
        else:
            resp = Response(self.send_msg(segments[2], segments[3], req.json))
        return resp


def start_server():
    parser = ArgumentParser(description='Starts VM manager API server')
    parser.add_argument('-host', default='localhost')
    parser.add_argument('-port', type=int, default=8080)
    args = parser.parse_args()
    httpd = make_server(args.host, args.port, Manager(args.host))
    print 'Started on http://%s:%s' % (args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        exit()


if __name__ == '__main__':
    start_server()
