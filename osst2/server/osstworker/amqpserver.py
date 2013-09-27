import pika
import json

success_code = 200


def on_request_builder(module_name):
    module = __import__(module_name, fromlist=[''])

    def on_request(ch, method, props, body):
        data = json.loads(body)
        print data
        if not (data['method'] or hasattr(module, data['method'])):
            resp = json.dumps({'error': {'code': 400}})
        else:
            try:
                resp = getattr(module, data['method'])(**data['args'])
            except Exception as e:
                resp = json.dumps({'error': {'code': 500, 'message': str(e)}})
        print resp
        if data.get('response_needed'):
            if resp is None:
                # make valid responce if rpc called function
                # works without errors and return None
                resp = success_code
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties
                             (correlation_id=props.correlation_id),
                             body=resp)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    return on_request


def start(host, queue_name, module_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_request_builder(module_name),
                          queue=queue_name, no_ack=True)
    print " [x] Awaiting RPC requests"
    channel.start_consuming()
