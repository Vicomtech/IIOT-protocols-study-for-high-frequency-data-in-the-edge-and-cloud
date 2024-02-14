cloud_server = '18.199.54.222'
edge_server = '192.168.35.106'
class mqtt(object):
    # config for production environment

    PARAMS = {
        'host': edge_server,  # IP DEL SERVER DEL BROKER
        'port': 1883, 
    }
    
class mqtt_cloud(object):
    # config for production environment

    PARAMS = {
        'host': cloud_server,  # IP DEL SERVER DEL BROKER
        'port': 1883, 
    }

    
class zeromq(object):
    # config for production environment

    PARAMS = {
        'host': edge_server,  # IP DEL SERVER DEL "BROKER"
        'port': 5672, # 5556
    }
    
class zeromq_cloud(object):
    # config for production environment

    PARAMS = {
        'host': cloud_server,  # IP DEL SERVER DEL "BROKER"
        'port': 5672, # 5556
    }

class amqp(object):
    # config for production environment

    PARAMS = {
        'host': edge_server,  # IP DEL SERVER DEL BROKER
        'port': 5672, 
    }
    
class amqp_cloud(object):
    # config for production environment

    PARAMS = {
        'host': cloud_server,  # IP DEL SERVER DEL BROKER
        'port': 5672, 
    }
   

class kafka(object):
    # config for production environment

    PARAMS = {
        'host': edge_server,  # IP DEL SERVER DEL BROKER
        'port': 29092, 
    }

class kafka_cloud(object):
    # config for production environment

    PARAMS = {
        'host': cloud_server,  # IP DEL SERVER DEL BROKER
        'port': 29093, 
    }


def get_config(MODE, broker): # TO SELECT IN PRODUCER TO WHICH SERVER CONNECT AND HOW (make an if)
    if broker == 'edge':
        SWITCH = {
            'mqtt': mqtt,
            'amqp': amqp,
            'kafka': kafka,
            'zeromq': zeromq
        }
       
    elif broker == 'cloud':
        SWITCH = {
            'mqtt': mqtt_cloud,
            'amqp': amqp_cloud,
            'kafka': kafka_cloud,
            'zeromq': zeromq_cloud,
        }

    return SWITCH[MODE]
