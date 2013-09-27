#!/usr/bin/env python
import pika
import json
import uuid


class RPCClient(object):

    def __init__(self, host):
        self.connection = pika.BlockingConnection(pika.
                                                  ConnectionParameters
                                                  (host=host))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)
        self.resp_waiting = {}

    def on_response(self, ch, method, props, body):
        if props.correlation_id in self.resp_waiting:
            self.resp_waiting[props.correlation_id] = body

    def call(self, queue_name, method, **kwargs):
        self.response = None
        corr_id = str(uuid.uuid4())
        self.resp_waiting[corr_id] = None
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   properties=pika.
                                   BasicProperties(reply_to=self.
                                                   callback_queue,
                                                   correlation_id=corr_id,),
                                   body=json.dumps({'method': method,
                                                    'response_needed': True,
                                                    'args': kwargs}),)
        while self.resp_waiting[corr_id] is None:
            self.connection.process_data_events()
        resp = self.resp_waiting[corr_id]
        print resp
        return resp
