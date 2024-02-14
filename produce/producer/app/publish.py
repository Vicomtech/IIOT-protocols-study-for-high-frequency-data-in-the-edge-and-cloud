from config import get_config
import os
import pika
import paho.mqtt.client as mqtt 
import random
from csv import DictWriter
import orjson
import time
import random
from datetime import datetime
from confluent_kafka import Producer
import socket as sk
import zmq
import pandas as pd


def high_precision_sleep(duration):
    start_time = time.perf_counter()
    while True:
        elapsed_time = time.perf_counter() - start_time
        remaining_time = duration - elapsed_time
        if remaining_time <= 0:
            break
        if remaining_time > 0.02:  # Sleep for 5ms if remaining time is greater
            time.sleep(max(remaining_time/2, 0.0001))  # Sleep for the remaining time or minimum sleep interval
        else:
            pass


protocol = os.environ.get("PROTOCOL", "amqp") # por defecto coge ese PROTOCOL
cycles = int(os.environ.get("CYCLES", "30"))
cntion = os.environ.get("CONNECTION", 'WiFi')
broker = os.environ.get("BROKER", 'edge')

# data_type = os.environ.get("DATA_TYPE", "[int, float]") # por defecto coge ese DATA_TYPE
data_type = os.environ.get("DATA_TYPE", "[int]") # por defecto coge ese DATA_TYPE
data_type = data_type.strip('][').split(', ')

list_length = os.environ.get("LIST_LEN", "[25000, 12500, 6250, 100000, 50000, 25000, 200000, 100000, 50000]") # por defecto coge ese DATA_TYPE
list_length = list_length.strip('][').split(', ')

sampling_freq = os.environ.get("SAMPLING_FREQ", "[10, 20, 40, 10, 20, 40, 10, 20, 40]")
sampling_freq = sampling_freq.strip('][').split(', ')

runs =  os.environ.get("RUNS", "[1, 16]")
runs = runs.strip('][').split(', ')
print(runs)
    

# Configuración de conexión 
config = get_config(protocol, broker)


def create_data(data_type, id, list_length):
    # create data
    if list_length == 0:
        if data_type == 'int':
            msg = {'data': random.randint(1,100), 'id':id}
        elif data_type == 'float':
            msg = {'data': random.random(), 'id':id}
        elif data_type == 'str':
            msg = {'data': random.choice("abcde"), 'id':id}
    else:
        if data_type == 'int':
            d = [random.randint(1,100)] * list_length
            msg = {'data': d, 'id':id}
        elif data_type == 'float':
            d = [random.random()] * list_length
            msg = {'data': d, 'id':id}
        elif data_type == 'str':
            d = [random.choice("abcde")] * list_length
            msg = {'data': d, 'id':id}
    return msg

def on_send_data(dictionary, filename):
    # save time and id in csv
    # list of column names
    field_names = dictionary.keys()

    with open(filename, 'a') as f_object:
        # Pass the file object and a list
        # of column names to DictWriter()
        # You will get a object of DictWriter
        dictwriter_object = DictWriter(f_object, fieldnames=field_names)
        # Pass the dictionary as an argument to the Writerow()
        dictwriter_object.writerow(dictionary)
 
    # Close the file object
    f_object.close()      

def save_experiment_data(filename, experiment_res_list):
    experiment_res = pd.DataFrame(experiment_res_list)
    experiment_res.columns = ['ID', 'TIME1', 'location', 'metadata_id']
    experiment_res.to_csv(filename)  
        
def create_filename(run, broker, protocol, metadata_id):     
    return datetime.now().strftime('results/results_RUN{}_{}/send_{}_000{}.csv'.format(run, broker, protocol, metadata_id))
    
def start_publishing(protocol, config,sampling_freq, id, runs):
    
    if protocol == 'zeromq':
        context = zmq.Context()
        #  Socket to talk to server
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        # socket.bind("tcp://*:"+str(config.PARAMS['port'])) 
        print(config.PARAMS['host']+str(config.PARAMS['port']))
        socket.connect("tcp://"+config.PARAMS['host']+":"+str(config.PARAMS['port']))
    
    
    for run in range(int(runs[0]), int(runs[1])):    
        metadata_id = 0
       
        for idx in range(len(list_length)):
            # for data_t in data_type:
            list_len = list_length[idx]
            sampl_f = sampling_freq[idx]
            data_t = data_type[0]
            id = 1
            sampl_f = int(sampl_f)
            list_len = int(list_len)
            metadata_id = metadata_id + 1
            
            metadata = protocol + ', '+  data_t  + ', ' + str(list_len) + ', ' + str(sampl_f) + ', ' + str(cycles) + ', ' + str(cntion)
            
            filename = datetime.now().strftime('results/results_RUN{}_{}/metadata_{}_000{}.txt'.format(run, broker, protocol, metadata_id))
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as file:
                file.write(metadata)
     
                                        
                        
            if protocol == 'amqp':
                time.sleep(10)
                ############### CONNECTIONS ###############
                
                credentials = pika.PlainCredentials('user', 'pass')
                connection = pika.BlockingConnection(pika.ConnectionParameters(config.PARAMS['host'],
                                                                                config.PARAMS['port'],
                                                                                '/',
                                                                                credentials))
               
                channel = connection.channel()
                
                ############## QUEUE DECLARATIONS ###################
                channel.queue_declare(queue='q1')
                #################### SEND DATA #####################
                msg = create_data(data_t, id, list_len)
                print(sampl_f)
                experiment_res_list = []
                eps = 0
                for c in range(cycles):
                    for i in range(sampl_f):
                        t1=time.time()
                        body = orjson.dumps(msg)
                        l1 = [msg['id'], datetime.now(), 'host1_send', metadata_id]
                        experiment_res_list.append(l1)
                        channel.basic_publish(exchange='', routing_key='q1', body=body, properties=pika.BasicProperties(delivery_mode=1))
                        msg['id'] = msg['id'] + 1
             
                        if (time.time()-t1+eps)>(1/sampl_f):
                            eps = eps + (time.time()-t1)-(1/sampl_f)
                        else: 
                            high_precision_sleep((1/sampl_f)+eps-(time.time()-t1))
                            eps = 0
                    
                
                filename = create_filename(run, broker, protocol, metadata_id)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                msg['id'] = -1
                msg['data'] = run
                body = orjson.dumps(msg)
                channel.basic_publish(exchange='', routing_key='q1', body=body)
                save_experiment_data(filename, experiment_res_list)
                connection.close()
                    
            elif protocol=='mqtt':
                time.sleep(10)
                server_broker = str(config.PARAMS['host']) + ':' + str(config.PARAMS['port'])
                client = mqtt.Client("Ertzean_experiment")
             
                client.connect(config.PARAMS['host'], config.PARAMS['port']) 
                msg = create_data(data_t, id, list_len)
                experiment_res_list = []
                eps = 0
                for c in range(cycles):
                    for i in range(sampl_f):
                        t1=time.time()
                        body = orjson.dumps(msg)
                        l1 = [msg['id'], datetime.now(), 'host1_send', metadata_id]
                        experiment_res_list.append(l1)
                        client.publish("q1", body)
                        msg['id'] = msg['id'] + 1
                        if (time.time()-t1+eps)>(1/sampl_f):
                            eps = eps + (time.time()-t1)-(1/sampl_f)
                        else: 
                            high_precision_sleep((1/sampl_f)+eps-(time.time()-t1))
                            eps = 0
                            
                filename = create_filename(run, broker, protocol, metadata_id)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                msg['id'] = -1
                msg['data'] = run
                body = orjson.dumps(msg)
                client.publish("q1", body)
                save_experiment_data(filename, experiment_res_list)
                client.disconnect()
                            
                
            elif protocol == 'kafka':
                time.sleep(10)
                server_broker = str(config.PARAMS['host']) + ':' + str(config.PARAMS['port'])
                conf = {'bootstrap.servers': server_broker,
                        'client.id': sk.gethostname()}

                producer = Producer(conf)
                topic = 'q1'
                
                #################### SEND DATA #####################
                msg = create_data(data_t, id, list_len)
                experiment_res_list = []
                eps = 0
                for c in range(cycles):
                    for i in range(sampl_f):
                        t1=time.time()
                        body = orjson.dumps(msg)
                        l1 = [msg['id'], datetime.now(), 'host1_send', metadata_id]
                        experiment_res_list.append(l1)
                        producer.produce(topic, value=body)
                        msg['id'] = msg['id'] + 1
                        if (time.time()-t1+eps)>(1/sampl_f):
                            eps = eps + (time.time()-t1)-(1/sampl_f)
                        else: 
                            high_precision_sleep((1/sampl_f)+eps-(time.time()-t1))
                            eps = 0
                filename = create_filename(run, broker, protocol, metadata_id)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                msg['id'] = -1
                msg['data'] = run
                body = orjson.dumps(msg)
                producer.produce(topic, value=body)
                producer.flush() # wait until all messages are delivered
                save_experiment_data(filename, experiment_res_list)
                    

            elif protocol == 'zeromq':
                
                time.sleep(20)
                msg = create_data(data_t, id, list_len)
                experiment_res_list = []
                eps = 0
                for c in range(cycles):
                    for i in range(sampl_f):
                        t1=time.time()
                        body = orjson.dumps(msg)
                        l1 = [msg['id'], datetime.now(), 'host1_send', metadata_id]
                        experiment_res_list.append(l1)
                        socket.send_multipart([b'q1', body])
                        msg['id'] = msg['id'] + 1
                        if (time.time()-t1+eps)>(1/sampl_f):
                            eps = eps + (time.time()-t1)-(1/sampl_f)
                        else: 
                            high_precision_sleep((1/sampl_f)+eps-(time.time()-t1))
                            eps = 0
                filename = create_filename(run, broker, protocol, metadata_id)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                msg['id'] = -1
                msg['data'] = run
                body = orjson.dumps(msg)
                socket.send_multipart([b'q1', body])
                save_experiment_data(filename, experiment_res_list)
                                
            print('exit')
                                                   

if __name__ == "__main__":
    start_publishing(protocol, config, sampling_freq, id, runs)

    
    
