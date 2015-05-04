__author__ = 'Ohad'

lat_long_delta = 0.0005

delta = {'lat':         0.0005,
         'long':        0.0005,
         'height':      5,
         'orientation': 10,
         'battery':     0.005}

data = {'lat':          35.01574,
        'long':         32.77849,
        'height':       90,
        'orientation':  0,
        'battery':      95}


def get_data():
    import random
    for key in data:
        data[key] = random.uniform(data[key]-delta[key], data[key]+delta[key])
    data['battery'] -= delta['battery']
    return data


if __name__ == '__main__':
    from time import sleep
    from datetime import datetime
    from messageQueue import MessageQueue
    q = MessageQueue(target='http://127.0.0.1:8080/receiveMessage')
    q.start()
    while True:
        sleep(0.5)
        q.enqueue({'kind': 'heartBeat', 'timeStamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'stats': get_data()})

