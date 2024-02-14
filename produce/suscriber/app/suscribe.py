#!/usr/bin/env python
import pika
import sys
import os
from config import get_config
import paho.mqtt.client as mqtt
import time
from datetime import datetime
from confluent_kafka import Consumer, KafkaError, KafkaException
import zmq
import orjson
import pandas as pd



def save_experiment_data(filename, experiment_res_list):
    experiment_res = pd.DataFrame(experiment_res_list)
    experiment_res.columns = ['ID', 'TIME4', 'SCRIPT_TIME', 'location', 'metadata_id']
    experiment_res.to_csv(filename)
      
def create_filename(run, broker, protocol, metadata_id):     
    return datetime.now().strftime('results/results_RUN{}_{}/receive_{}_000{}.csv'.format(run, broker, protocol, metadata_id))


def process_data(id, metadata_id, t1, experiment_res_list):
    script_time = time.time()-t1
    l1 = [id, datetime.now(), script_time, 'host1_receive', metadata_id]
    experiment_res_list.append(l1)
    return experiment_res_list

def save(metadata_id, data, experiment_res_list, broker, protocol):
    # SAVE EXPERIMENT DATA
    print('SAVING RESULTS')
    filename = create_filename(data, broker, protocol, metadata_id)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    save_experiment_data(filename, experiment_res_list)
    metadata_id = metadata_id + 1
    
    experiment_res_list = []
    if metadata_id == number_of_combinations+1:
        metadata_id = 1
    return metadata_id, experiment_res_list

def connect_protocol(host, port, protocol):
    if protocol == 'amqp':
        ############### CONNECTIONS ###############
        credentials = pika.PlainCredentials('user', 'pass')
        print(host)
        print(port)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host,
                                                                    port=port,
                                                                    credentials=credentials))
        channel = connection.channel()

        ############## QUEUE DECLARATIONS ###################
        channel.queue_declare(queue='q2')
        return channel
    elif protocol == 'mqtt' or protocol=='nanomq':
                       
        client = mqtt.Client("ertzean_experiment3")
        client.connect(host, port)
        client.subscribe("q2")
        return client
    elif protocol == 'kafka':
        server_broker = str(host) + ':' + str(port)
        conf_consumer = {'bootstrap.servers': server_broker,
                'group.id': "foo",
                'auto.offset.reset': 'smallest'}
        consumer = Consumer(conf_consumer)
        topics = 'q2'
        consumer.subscribe([topics])
        return consumer
    elif protocol == 'zeromq':
        time.sleep(15)
        context = zmq.Context()
        #  Socket to talk to server
        #print("Connecting to server…")
        socket = context.socket(zmq.SUB)
        server_broker = str(host) + ':' + str(port)
        socket.connect("tcp://"+server_broker)
        socket.subscribe("")
        return socket


def read_data(body):
   
    body = orjson.loads(body.decode('utf-8'))
    return  body['id'],  body['data']


protocol = os.environ.get("PROTOCOL", "amqp") # por defecto coge ese PROTOCOL
broker = os.environ.get("BROKER", "edge") # por defecto coge ese PROTOCOL
list_length = int(os.environ.get("LIST_LEN", 5)) # por defecto coge ese DATA_TYPE
number_of_combinations = int(os.environ.get("NUMBER_OF_COMBINATIONS", "9"))

config = get_config(protocol, broker)
# Configuración de conexión 
server_broker = str(config.PARAMS['host']) + ':' + str(config.PARAMS['port'])
print(server_broker)


metadata_id = 1
filename = ''
experiment_res_list = []


if protocol == 'amqp':
    try: 
                    
        channel = connect_protocol(config.PARAMS['host'], config.PARAMS['port'], protocol)
       
        ################# CALLBACK ###################
        def callback(ch, method, properties, body):
            global metadata_id
            global experiment_res_list
            t1 = time.time()
            id, data = read_data(body)
            if id == -1:
                metadata_id, experiment_res_list = save(metadata_id, data, experiment_res_list, broker, protocol)
            else:
                experiment_res_list = process_data(id, metadata_id, t1, experiment_res_list)
                
        channel.basic_qos(0)
        channel.basic_consume(queue='q2', on_message_callback=callback, auto_ack=True)
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
        global filename
        global experiment_res_list
        t1 = time.time()
        id, data = read_data(message.payload)
        
        if id == -1:
            metadata_id, experiment_res_list = save(metadata_id, data, experiment_res_list, broker, protocol)
        else:
            experiment_res_list = process_data(id, metadata_id, t1, experiment_res_list)
      
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
    consumer = connect_protocol(config.PARAMS['host'], config.PARAMS['port'], protocol)
    
    def msg_process(msg):
        global metadata_id
        global filename
        global experiment_res_list
        t1 = time.time()
        id, data = read_data(msg.value())
       
        if id == -1:
            metadata_id, experiment_res_list = save(metadata_id, data, experiment_res_list, broker, protocol)
        else:
            experiment_res_list = process_data(id, metadata_id, t1, experiment_res_list)

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
    socket = connect_protocol(config.PARAMS['host'], config.PARAMS['port'], protocol)

    while True:
        #  Wait for next request from client
        message = socket.recv()
        t1 = time.time()
        id, data = read_data(message)
        if id == -1:
            metadata_id, experiment_res_list = save(metadata_id, data, experiment_res_list, broker, protocol)
        else:
            experiment_res_list = process_data(id, metadata_id, t1, experiment_res_list)
            
