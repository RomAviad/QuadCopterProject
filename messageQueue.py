__author__ = 'Ohad'

from threading import Thread
from Queue import PriorityQueue
from datetime import datetime
import json
import urllib2

priority_dictionary = {
    'hello':        10,
    'heartBeat':    3,
    'flightPlan':  2,
    'Image':        1,
    'bye':          -2
}

last_sent = {
    'heartBeat': datetime.utcnow(),
    'targetFound': datetime.utcnow()
}


class BadParams(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Message():
    def __init__(self, message):
        if not 'kind' in message:
            raise BadParams('missing "kind" parameter')
        self.kind = message['kind']
        if not self.kind in priority_dictionary:
            raise BadParams('"' + self.kind + '" Is not a known message type')
        self.priority = priority_dictionary[self.kind]
        if not 'timeStamp' in message:
            raise BadParams('missing "timeStamp" parameter')
        try:
            self.timeStamp = datetime.strptime(message['timeStamp'], '%Y-%m-%d %H:%M:%S')
        except ValueError, e:
            print e
            raise BadParams('Bad timeStamp format')
        self.content = message

    def __cmp__(self, other):
        if self.priority > other.priority:
            return -1
        elif self.priority < other.priority:
            return 1
        elif self.timeStamp < other.timeStamp:
            return -1
        elif self.timeStamp > other.timeStamp:
            return 1
        return 0


class MessageQueue(Thread):
    __queue = PriorityQueue()
    # __target = 'http://127.0.0.1:8080/receiveMessage'

    def __init__(self, target):
        super(MessageQueue, self).__init__()
        self.__target = target

    def run(self):
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.enqueue({'kind': 'hello', 'timeStamp': now})
        while True:
            message = self.__queue.get(block=True)
            if message.kind in last_sent and message.timeStamp < last_sent[message.kind] and message.priority != -1:
                message.priority = -1
                self.__queue.put_nowait(item=message)
                continue
            if not self._send_message(message):
                print 'failed to send'
                self.__queue.put_nowait(item=message)
            elif message.kind == 'bye':
                break
            elif message.kind in last_sent:
                last_sent[message.kind] = max(message.timeStamp, last_sent[message.kind])

    def _send_message(self, message):
        request = urllib2.Request(self.__target)
        request.add_header('Content-Type', 'application/json')
        try:
            code = urllib2.urlopen(url=request, data=json.dumps(message.content), timeout=10).code
            return 200 <= code < 300
        except urllib2.URLError, e:
            print e
            return False

    def enqueue(self, message):
        self.__queue.put_nowait(item=Message(message))

    def stop(self):
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.enqueue({'kind': 'bye', 'timeStamp': now})

if __name__ == '__main__':
    # q = MessageQueue(target='http://postcatcher.in/catchers/54abdf8c31b05e0200000924')
    q = MessageQueue(target='http://127.0.0.1:8080/receiveMessage')
    q.enqueue({'kind': 'heartBeat', 'timeStamp': '2015-12-22 20:30:37', 'stats': {'lat': 35.01574, 'long': 32.77849,
                                                                                  'height': 90, 'orientation': 0,
                                                                                  'battery': 95}})
    q.start()
    q.stop()