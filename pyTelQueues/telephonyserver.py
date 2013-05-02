import threading, time, asyncore, Queue

from pyTelQueues.fastagi import FastAGIServer #move to telephony

#exposed entry point, start main telephony thread
CHANNELTYPE = 'fastagi'

class TelephonyServer():
    def __init__(self, pytelqueues):
        self._telephony_thread = TelephonyServerThread(pytelqueues)
        self._telephony_thread.daemon = True;
        self._telephony_thread.start()
        self._queue = Queue.Queue()
        self._threadhandles = {}

    def put(self, item):
        self._queue.put_nowait(item)

    def get(self):
        try:
            return self._queue.get_nowait()
        except (Queue.Empty, KeyError):
            return False

    def setthread(self, channeltype, handle):
        self._threadhandles[channeltype]=handle

    def getthread(self, channeltype):
        return self._threadhandles[channeltype]

#telephony thread, we are going to loop here.
class TelephonyServerThread(threading.Thread):
    def __init__(self, pytelqueues):
        threading.Thread.__init__(self)
        self._pytelqueues = pytelqueues

    def run(self):
        self._pytelqueues.logger().Message('Telephony Thread started', 'TELT')

        #fastagi
        self._fastagiserver = FastAGIServer(self._pytelqueues)
        self._pytelqueues.telephonyserver().setthread('fastagi', self._fastagiserver)

        while True:
            #poll here for event from queue to telephony backends
            event = self._pytelqueues.telephonyserver().get()
            if event != False:
                #fire the received event into the telephony core
                try:
                    self._pytelqueues.logger().Message('Fire event into %s' % event['channeltype'], 'TELT')
                    self._pytelqueues.telephonyserver().getthread(event['channeltype']).getclient(event['clientMD5']).handle_callcontroller_event(event)
                except KeyError:
                    self._pytelqueues.logger().Message("Received event for a non-existant channel or channeltype", 'CORE')

            #poll asyncore
            asyncore.loop(timeout=0.001, count=1)
