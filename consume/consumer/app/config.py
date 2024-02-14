class mqtt(object):
    PARAMS = {
        'host': 'mosquitto',  # IP DEL SERVER DEL CONSUMER, mosquitto
        'port': 1883, 
    }
    
class zeromq(object):
    PARAMS = {
        # 'host': '192.168.30.107',  # IP DEL SERVER DEL PRODUCER
        'port_consume': 1883, # 5555
        'port_produce': 5672, # 5556
    }

class amqp(object):
    PARAMS = {
        'host': 'rabbitmq3',  # SERVER DEL CONSUMER, rabbitmq3
        'port': 5672, 
    }

class kafka(object):
    PARAMS = {
        'host': 'kafkabroker',  # IP DEL SERVER DEL CONSUMER
        'port': 9092, 
    }


def get_config(MODE): # TO SELECT IN PRODUCER TO WHICH SERVER CONNECT AND HOW (make an if)
    SWITCH = {
        'mqtt': mqtt,
        'amqp': amqp,
        'kafka': kafka,
        'zeromq': zeromq
    }
    
    return SWITCH[MODE]
