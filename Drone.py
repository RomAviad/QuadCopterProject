import Queue
from datetime import datetime, date, time


# datetime.strptime('2014-12-22 20:30:37', '%Y-%m-%d %H:%M:%S')
class Drone:

    def __init__(self):
        self.lastConnection = datetime.utcnow()
        self.status = {'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

    def update(self, json):
        if self.__is_stale(json):
            print('stale, will not update')
            return
        self.status = json
        print self.status #ToDo - change to log

    @staticmethod
    def __string_to_date(str_date):
        return datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S')

    def __is_stale(self, json):
        return self.__string_to_date(self.status['timestamp']) >= self.__string_to_date(json['timestamp'])

if __name__ == '__main__':
    # d = Drone()
    # import time
    # time.sleep(2)
    # d.update({'timestamp': '2014-12-21 20:30:00'})
    # now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    # d.update({'timestamp': now})
    # d.update({'timestamp': now})
    # d.update({'timestamp': '2014-12-23 20:30:00'})
    import groundControl
    groundControl.start_server()