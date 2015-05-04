from email import message_from_file

__author__ = 'Aviad Rom'
from flask import Flask, url_for, request, redirect
from messageQueue import MessageQueue, Message, priority_dictionary
from datetime import datetime
from threading import Thread
import json
import logging

# filename='groundControl.log',
logging.basicConfig(level=logging.DEBUG, filemode='w',
                    format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)
###### Drone status information section ######
droneData = dict(lastUpdate=datetime.utcnow(), stats={'lat': 35.01574,
                                                      'long': 32.77849,
                                                      'height': 90,
                                                      'orientation': 0,
                                                      'battery': 95})
messagesQueue = None
droneIp = None
###### End of drone status information section######


def is_new_valid_ip(ip):
    # add more ip validation
    return ip and ip != droneIp


def destroy_queue(ip):
    """
    if a messageQueue is open to the given ip, close it and set the messageQueue to None
    :param ip: ipV4 address of target machine
    :return: None
    """
    global droneIp
    global messagesQueue
    if ip != droneIp or not messagesQueue:
        return
    messagesQueue.stop()
    messagesQueue = None
    droneIp = None


def create_queue(ip):
    """
    open a messageQueue to the given ip.
    if a current queue exists it will be destroyed and a warning logged.
    :param ip: target machine of message queue
    :return: None
    """
    global messagesQueue
    global droneIp
    if messagesQueue:
        logging.warning('A new queue is opened while current queue is still active, destroying current queue')
        destroy_queue(droneIp)
    droneIp = ip
    messagesQueue = MessageQueue(target=('http://' + ip + ':8080/receiveMessage'))
    messagesQueue.start()


def handle_hello(ip, message=None):
    """
    Handler for a hello message.
    checks if a messageQueue is open to the sender and if not
    destroys current queue and open a new one to the sender.
    :param ip: ip of sender
    :param message: irrelevant, for signature compatibility purposes.
    :return: None
    """
    if not is_new_valid_ip(ip):
        return
    destroy_queue(droneIp)
    create_queue(ip)


def handle_bye(ip, message=None):
    """
    Handler for bye message.
    tries to destroy the queue to the sender
    :param ip: sender's ip
    :param message: irrelevant, for signature compatibility purposes.
    :return:
    """
    destroy_queue(ip)


def log_message(message, ip):
    """
    Logs a message received by the web server.
    :param message: The message received
    :param ip: sender's ip
    :return: None
    """
    sent = message.timeStamp.strftime('%Y-%m-%d %H:%M:%S')
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    logging.info('Got "%s" from %s', message.kind, ip)
    logging.info('Sent: %s, received: %s', sent, now)
    logging.debug('Content: %s', message.content)

### Handlers dictionary with basic handlers. add handlers by calling 'register_handler(kind, handler)' ###
messagesHandlers = {
    'hello': handle_hello,
    'bye': handle_bye
}


@app.route("/")
def get_site():
    return redirect(url_for('static', filename='index.html'))


@app.route('/tiles/<tile_type>/<z>/<x>/<y>.jpg')
def get_tile(tile_type, x, y, z):
    import tileServer

    return tileServer.get_tile(tile_type, x, y, z)


@app.route('/changeDrone', methods=['GET'])
def change_drone():
    handle_hello(ip=request.args.get('ip', False))
    return 'ok'


@app.route('/receiveMessage', methods=['POST'])
def receive_message():
    """
    Handles a received message from another machine running a message queue.
    message is expected as json in request body. see messageQueue for message format.
    message is logged and then a matching handler is dispatched with sender's ip.
    if no matching handler is defined it is logged and an appropriate message is returned.
    :return: Status message
    """
    message = Message(json.loads(request.data))
    log_message(message, request.remote_addr)
    if message.kind in messagesHandlers:
        messagesHandlers[message.kind](ip=request.remote_addr, message=message)
        return "ok"
    logging.warning('Missing handler for message type: %s', message.kind)
    return "No handler found for message kind: " + message.kind


@app.route('/flightData', methods=['GET'])
def flight_data():
    """
    return the latest known stats for the drone connected to this server.
    :return:
    """
    return json.dumps(droneData['stats'])


@app.route('/track', methods=['POST'])
def track():
    """
    receive a form containing a flight plan from the user web interface and
    queue an appropriate message to the connected drone message queue.
    If no drone is connected an error message is logged and returned
    :return: Status message
    """
    if not messagesQueue:
        logging.error('Cannot send flight plan, no drone connected')
        return "Internal error"
    messagesQueue.enqueue(
        {'kind': 'flightPlan', 'timeStamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
         'planType': request.form["drawType"], 'planData': json.loads(request.form["drawCoordinates"])})
    logging.info('Sent flight plan to drone: %s', droneIp)
    return "ok"


def start_server():
    """
    Start a groundControl flask based web server on an independent thread.
    only one server thread can be started to avoid port listening collision issues
    :return: Status message string
    """
    global serverThread
    if serverThread:
        logging.warning("Attempt to start server when already running")
        return "Server already running"
    serverThread = Thread(target=app.run,
                          kwargs={'port': 8080, 'host': '0.0.0.0', 'debug': False, 'threaded': True})
    serverThread.start()
    logging.info('Server successfully started')
    return "ok"


def connect(ip=None):
    """
    Opens a messageQueue connection to the given machine.
    server must be up for this to work.
    :param ip: The machine's ip.
    :return: Status message string
    """
    if not serverThread:
        logging.error("Cannot connect to drone when server is not running")
        return "Server not running"
    handle_hello(ip)
    logging.info("Now connected to drone: %s", ip)
    return "Hello sent"


def send_message(message_json):
    """
    Send a message to the currently connected machine.
    :param message_json: message to send. see messageQueue.py for format and examples.
    :return: Status message string
    """
    if not serverThread:
        logging.error("Cannot send message when server is not running")
        return "Server not running"
    if not messagesQueue:
        logging.error("Cannot send message when not connected to drone")
        return "Not connected"
    messagesQueue.enqueue(message_json)
    logging.info("Message queued")
    return "Message queued"


def register_handler(kind, handler):
    """
    register a new handler for a message kind.
    :param kind: kind of message to handle - see messageQueue.py for valid kinds
    :param handler: handler for messages - must take exactly 2 mandatory parameters 'ip', 'message'
    :return: Status message string
    """
    if not hasattr(handler, '__call__'):
        logging.error('Handler is not a function!')
        return "Bad handler"
    if not kind in priority_dictionary:
        logging.error('Kind "%s" is not a valid message kind', kind)
        return "Bad kind"
    if kind in messagesHandlers:
        logging.warning('A handler for %s already exists! replacing..', kind)
    messagesHandlers[kind] = handler
    return "Handler registered"


def handle_heartbeat(ip, message):
    """
    Handler for heartbeat message.
    saves heartbeat stats and ignores old heartbeats
    :param ip: sender's ip
    :param message: heartbeat message - see messageQueue.py for format example
    :return: None
    """
    if ip != droneIp:
        logging.warning('Got heartbeat from unknown drone: %s, current drone is: %s', ip, droneIp)
    elif message.timeStamp < droneData['lastUpdate']:
        logging.info('Got old heartbeat, Not updating')
    else:
        droneData['lastUpdate'] = message.timeStamp
        droneData['stats'] = message.content['stats']
        logging.info('Drone data updated')


serverThread = None
register_handler('heartBeat', handle_heartbeat)


if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0', debug=True, threaded=True)


# @app.route('/droneData', methods=['POST'])
# def drone_request():
# obj = request.get_json()
#     drone.update(obj)
#     #push object to "from_drone" queue
#     #return next mission (actual mission or NOP)