# #!/usr/bin/env python
import pika
from confluent_kafka import Consumer,Producer, KafkaError, KafkaException
import socket as sk
import zmq

from datetime import datetime
from config import get_config
import time
import orjson
import paho.mqtt.client as mqtt
import sys
import os
import pandas as pd

def update_data(data):
    # create data
    if type(data) == int:
        data = data + 10
    elif type(data) == float:
        data = data + 10
    elif type(data) == str:
        data = data + '_hello'
    elif type(data) == list:
        data = 1 # here we should process the ML algorithm
    return data

def read_data(body):
    body = orjson.loads(body.decode('utf-8'))
    return  body['id'],  body['data']

def save(metadata_id, id, data, experiment_res_list1, experiment_res_list2, broker, protocol, channel):
    # SAVE EXPERIMENT DATA
    print('SAVING RESULTS')
    #UPDATE TO NEW EXPERIMENT
    msg = {'data': data, 'id': id}
    if protocol=='amqp':
        channel.basic_publish(exchange='', routing_key='q2', body=orjson.dumps(msg))
    elif protocol=='mqtt' or protocol == 'nanomq':
        channel.publish("q2", orjson.dumps(msg))
    elif protocol=='kafka':
        channel.produce("q2", value=orjson.dumps(msg))
    elif protocol=='zeromq':
        channel.send(orjson.dumps(msg))
        
    filename1 = datetime.now().strftime('results/results_RUN{}_{}/process_receive_{}_000{}.csv'.format(data, broker, protocol,metadata_id))
    filename2 = datetime.now().strftime('results/results_RUN{}_{}/process_send_{}_000{}.csv'.format(data, broker, protocol,metadata_id))
    os.makedirs(os.path.dirname(filename1), exist_ok=True)
    os.makedirs(os.path.dirname(filename2), exist_ok=True)
    save_experiment_data(filename1, experiment_res_list1)
    save_experiment_data2(filename2, experiment_res_list2)

    metadata_id = metadata_id + 1
    experiment_res_list1 = []
    experiment_res_list2 = []
    if metadata_id == number_of_combinations+1:
        metadata_id = 1
    return metadata_id, experiment_res_list1, experiment_res_list2

def save_experiment_data(filename, experiment_res_list):
    experiment_res = pd.DataFrame(experiment_res_list)
    experiment_res.columns = ['ID', 'TIME2', 'location', 'metadata_id']
    experiment_res.to_csv(filename)

def save_experiment_data2(filename, experiment_res_list):
    experiment_res = pd.DataFrame(experiment_res_list)
    experiment_res.columns = ['ID', 'TIME3', 'SCRIPT_TIME', 'location', 'metadata_id']
    experiment_res.to_csv(filename)

def process_data(id, metadata_id, data, t1, protocol, experiment_res_list1, experiment_res_list2, channel):
    l1 = [id, datetime.now(), 'host2_receive', metadata_id]
    experiment_res_list1.append(l1)
    # on_receive_data(dictionary, filename1)
    data = update_data(data)
    msg = {'data': data, 'id': id}
    body=orjson.dumps(msg)
    script_time = time.time()-t1
    l2 = [id, datetime.now(), script_time, 'host2_send', metadata_id]
    experiment_res_list2.append(l2)
    if protocol == 'amqp':
        channel.basic_publish(exchange='', routing_key='q2', body=body)
    elif protocol == 'mqtt' or protocol == 'nanomq': 
        channel.publish("q2",body)
    elif protocol=='kafka':
        channel.produce("q2", value=body)
    elif protocol=='zeromq':
        channel.send(body)
   
    return experiment_res_list1, experiment_res_list2

    # print(" [x] Sent back")

def connect_protocol(host, port, protocol):
    if protocol=='amqp':
        ############### CONNECTIONS ###############
        credentials = pika.PlainCredentials('user', 'pass')
        
        print(config.PARAMS['host'])
        print(config.PARAMS['port'])
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host,
                                                                    port=port,
                                                                    credentials=credentials))
        channel = connection.channel()

        ############## QUEUE DECLARATIONS ###################
        channel.queue_declare(queue='q1')
        channel.queue_declare(queue='q2')
        return channel
    elif protocol == 'mqtt' or protocol == 'nanomq':
        client = mqtt.Client("ertzean_experiment2")
        client.connect(host, port)
        client.subscribe("q1")
        return client
    elif protocol == 'kafka':
        server_broker = str(host) + ':' + str(port)
        conf_consumer = {'bootstrap.servers': server_broker,
                'group.id': "foo",
                'auto.offset.reset': 'smallest'}
        consumer = Consumer(conf_consumer)

        conf_producer = {'bootstrap.servers': server_broker,
                            'client.id': sk.gethostname()}
        producer = Producer(conf_producer)

        consumer.subscribe(["q1"])

        return producer, consumer
    elif protocol == 'zeromq':
        print('creating')
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        # socket.connect("tcp://"+server_broker)
        socket.bind("tcp://*:"+str(port[0]))
        socket.subscribe("q1")
        context1 = zmq.Context()
        socket_pub = context1.socket(zmq.PUB)
        socket_pub.bind("tcp://*:"+str(port[1]))
        return socket, socket_pub
protocol = os.environ.get("PROTOCOL", "amqp") # por defecto coge ese PROTOCOL
broker = os.environ.get("broker", "edge") # por defecto coge ese PROTOCOL
list_length = int(os.environ.get("LIST_LEN", 5))
number_of_combinations = int(os.environ.get("NUMBER_OF_COMBINATIONS", "9"))

config = get_config(protocol)

# Configuración de conexión
if protocol == 'zeromq':
    server_broker=""
else:
    server_broker = str(config.PARAMS['host']) + ':' + str(config.PARAMS['port'])


metadata_id = 1
experiment_res1 = pd.DataFrame()
experiment_res_list1 = []
experiment_res2 = pd.DataFrame()
experiment_res_list2 = []

def start_consuming(protocol, config, server_broker):

    if protocol == 'amqp':
        try:
            ################# CONNECT ###################
            channel = connect_protocol(config.PARAMS['host'], config.PARAMS['port'], protocol)

            ################# CALLBACK ###################
            def callback(ch, method, properties, body):
                global metadata_id
                global experiment_res_list1
                global experiment_res_list2
                t1 = time.time()
                id, data = read_data(body)
                if id == -1:
                    # SAVE EXPERIMENT DATA
                    print('SAVING RESULTS')
                    metadata_id, experiment_res_list1, experiment_res_list2 = save(metadata_id, id, data, experiment_res_list1, experiment_res_list2, broker, protocol, channel)
                else:
                    experiment_res_list1, experiment_res_list2 = process_data(id, metadata_id, data, t1, protocol, experiment_res_list1, experiment_res_list2, channel)
                
            channel.basic_qos(0) # These levels correspond to increasing levels of reliability for message delivery. QoS 0 may lose messages, QoS 1 guarantees the message delivery but potentially exists duplicate messages, and QoS 2 ensures that messages are delivered exactly once without duplication
            channel.basic_consume(queue='q1', on_message_callback=callback, auto_ack=True)

            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()

        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    elif protocol == 'mqtt':

        def on_message(client, userdata, message):
            global metadata_id
            global experiment_res_list1
            global experiment_res_list2
            t1 = time.time()
            id, data = read_data(message.payload)
            if id == -1:
                # SAVE EXPERIMENT DATA
                metadata_id, experiment_res_list1, experiment_res_list2 = save(metadata_id, id, data, experiment_res_list1, experiment_res_list2, broker, protocol, client)
            else:
                experiment_res_list1, experiment_res_list2 = process_data(id, metadata_id, data, t1, protocol, experiment_res_list1, experiment_res_list2, client)
 
        try:
            client = connect_protocol(config.PARAMS['host'], config.PARAMS['port'], protocol)
            client.on_message=on_message
            client.loop_forever()

        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    
    elif protocol == 'kafka':
        producer, consumer = connect_protocol(config.PARAMS['host'], config.PARAMS['port'], protocol)
        

        def msg_process(msg):
            global metadata_id
            global experiment_res_list1
            global experiment_res_list2
            t1 = time.time()
            id, data = read_data(msg.value())
            if id == -1:
                # SAVE EXPERIMENT DATA
                metadata_id, experiment_res_list1, experiment_res_list2 = save(metadata_id, id, data, experiment_res_list1, experiment_res_list2, broker, protocol, producer)
            else:
                experiment_res_list1, experiment_res_list2 = process_data(id, metadata_id, data, t1, protocol, experiment_res_list1, experiment_res_list2, producer)
 
            
        def basic_consume_loop(consumer):
            try:
                
                while running:
                    msg = consumer.poll(timeout=1.0)
                    if msg is None: continue

                    if msg.error():

                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # End of partition event
                            sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                            (msg.topic(), msg.partition(), msg.offset()))
                        elif msg.error():
                            raise KafkaException(msg.error())
                            pass
                    else:
                        msg_process(msg)
            finally:
                # Close down consumer to commit final offsets.
                consumer.close()

        running = True
        basic_consume_loop(consumer)

    elif protocol == 'zeromq':
        socket, socket_pub = connect_protocol('', [config.PARAMS['port_consume'], config.PARAMS['port_produce']], protocol)
        
        #  Do 10 requests, waiting each time for a response
        while True:
            global metadata_id
            global experiment_res_list1
            global experiment_res_list2
            message = socket.recv_multipart()
            t1 = time.time()
            id, data = read_data(message[1])
            if id == -1:
                # SAVE EXPERIMENT DATA
                metadata_id, experiment_res_list1, experiment_res_list2 = save(metadata_id, id, data, experiment_res_list1, experiment_res_list2, broker, protocol, socket_pub)
            else:
                experiment_res_list1, experiment_res_list2 = process_data(id, metadata_id, data, t1, protocol, experiment_res_list1, experiment_res_list2, socket_pub)

 
if __name__ == "__main__":
    start_consuming(protocol, config, server_broker)






